#!/usr/bin/env python3
"""Monte Carlo action EV scanner for Double Down Madness deviation research."""

from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

from ddm_madness_counter_sim import (
    BJ_VERSIONS,
    HI_LO,
    RANKS,
    SUITS,
    Card,
    Hand,
    Rules,
    basic_action,
    blackjack_profit,
    dealer_play,
    settle_active_hand,
    upcard_value,
)


TEN_RANKS = ("T", "J", "Q", "K")


@dataclass
class ActionStats:
    rounds: int = 0
    profit: float = 0.0
    profit_sq: float = 0.0

    def add(self, value: float) -> None:
        self.rounds += 1
        self.profit += value
        self.profit_sq += value * value

    @property
    def mean(self) -> float:
        return self.profit / self.rounds if self.rounds else 0.0

    @property
    def sd(self) -> float:
        if not self.rounds:
            return 0.0
        return math.sqrt(max(0.0, self.profit_sq / self.rounds - self.mean * self.mean))

    @property
    def se95(self) -> float:
        return 1.96 * self.sd / math.sqrt(self.rounds) if self.rounds else 0.0


class DrawPile:
    def __init__(self, cards: list[Card]):
        self.cards = cards

    def draw(self) -> Card:
        return self.cards.pop()


def parse_rank(text: str) -> str:
    text = text.strip().upper()
    if text == "10":
        return "T"
    if text not in RANKS:
        raise argparse.ArgumentTypeError(f"invalid rank: {text}")
    return text


def card_value(rank: str) -> int:
    return 11 if rank == "A" else 10 if rank in TEN_RANKS else int(rank)


def remove_rank(cards: list[Card], rank: str, rng: random.Random) -> Card:
    candidates = [i for i, card in enumerate(cards) if card.rank == rank]
    if not candidates:
        raise RuntimeError(f"no {rank} left in shoe")
    index = rng.choice(candidates)
    return cards.pop(index)


def full_shoe(decks: int) -> list[Card]:
    return [Card(rank, suit) for _ in range(decks) for rank in RANKS for suit in SUITS]


def count_cards(cards: list[Card]) -> int:
    return sum(HI_LO[card.rank] for card in cards)


def log_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def weighted_choice(items: list[tuple[tuple[int, int, int], float]], rng: random.Random) -> tuple[int, int, int]:
    max_log = max(weight for _, weight in items)
    weights = [math.exp(weight - max_log) for _, weight in items]
    total = sum(weights)
    pick = rng.random() * total
    running = 0.0
    for (item, _), weight in zip(items, weights):
        running += weight
        if running >= pick:
            return item
    return items[-1][0]


def truncate_tc(running_count: int, cards_remaining: int) -> int:
    decks_remaining = max(cards_remaining / 52.0, 0.25)
    return int(running_count / decks_remaining)


def tc_matches(tc: int, target: str) -> bool:
    if target == "<=-5":
        return tc <= -5
    if target == ">=8":
        return tc >= 8
    return tc == int(target)


def target_running_counts(target: str, cards_remaining: int, min_count: int, max_count: int) -> list[int]:
    return [rc for rc in range(min_count, max_count + 1) if tc_matches(truncate_tc(rc, cards_remaining), target)]


def sample_burn_with_count(
    cards: list[Card],
    burn_count: int,
    target_count: int,
    rng: random.Random,
) -> list[Card] | None:
    low = [card for card in cards if HI_LO[card.rank] == 1]
    neutral = [card for card in cards if HI_LO[card.rank] == 0]
    high = [card for card in cards if HI_LO[card.rank] == -1]
    feasible: list[tuple[tuple[int, int, int], float]] = []
    for low_count in range(max(0, target_count), min(len(low), burn_count) + 1):
        high_count = low_count - target_count
        neutral_count = burn_count - low_count - high_count
        if high_count < 0 or high_count > len(high) or neutral_count < 0 or neutral_count > len(neutral):
            continue
        weight = (
            log_choose(len(low), low_count)
            + log_choose(len(high), high_count)
            + log_choose(len(neutral), neutral_count)
        )
        feasible.append(((low_count, high_count, neutral_count), weight))
    if not feasible:
        return None

    low_count, high_count, neutral_count = weighted_choice(feasible, rng)
    burn = rng.sample(low, low_count) + rng.sample(high, high_count) + rng.sample(neutral, neutral_count)
    burn_ids = {id(card) for card in burn}
    cards[:] = [card for card in cards if id(card) not in burn_ids]
    rng.shuffle(burn)
    return burn


def make_conditioned_state_constructed(
    rng: random.Random,
    decks: int,
    player_ranks: list[str],
    dealer_rank: str,
    target_tc: str,
    decks_remaining: float,
    max_attempts: int,
) -> tuple[list[Card], Hand, Card, int]:
    burn_count = int(round(decks * 52 - decks_remaining * 52 - len(player_ranks) - 1))
    if burn_count < 0:
        raise ValueError("decks_remaining leaves no room for exposed cards")

    for _ in range(max_attempts):
        cards = full_shoe(decks)
        rng.shuffle(cards)
        player_cards = [remove_rank(cards, rank, rng) for rank in player_ranks]
        dealer_up = remove_rank(cards, dealer_rank, rng)
        exposed_count = count_cards(player_cards) + HI_LO[dealer_up.rank]
        remaining_cards = len(cards) - burn_count
        min_running = exposed_count - min(burn_count, sum(1 for card in cards if HI_LO[card.rank] == -1))
        max_running = exposed_count + min(burn_count, sum(1 for card in cards if HI_LO[card.rank] == 1))
        running_options = target_running_counts(target_tc, remaining_cards, min_running, max_running)
        rng.shuffle(running_options)
        for target_running in running_options:
            burn = sample_burn_with_count(cards, burn_count, target_running - exposed_count, rng)
            if burn is None:
                continue
            running_count = exposed_count + count_cards(burn)
            rng.shuffle(cards)
            return cards, Hand(player_cards[:]), dealer_up, running_count
    raise RuntimeError(f"could not construct state for TC {target_tc} after {max_attempts:,} attempts")


def make_conditioned_state(
    rng: random.Random,
    decks: int,
    player_ranks: list[str],
    dealer_rank: str,
    target_tc: str,
    decks_remaining: float,
    max_attempts: int,
) -> tuple[list[Card], Hand, Card, int]:
    burn_count = int(round(decks * 52 - decks_remaining * 52 - len(player_ranks) - 1))
    if burn_count < 0:
        raise ValueError("decks_remaining leaves no room for exposed cards")

    for _ in range(max_attempts):
        cards = full_shoe(decks)
        rng.shuffle(cards)
        player_cards = [remove_rank(cards, rank, rng) for rank in player_ranks]
        dealer_up = remove_rank(cards, dealer_rank, rng)
        burn = [cards.pop() for _ in range(burn_count)]
        running_count = count_cards(burn) + count_cards(player_cards) + HI_LO[dealer_up.rank]
        tc = truncate_tc(running_count, len(cards))
        if tc_matches(tc, target_tc):
            rng.shuffle(cards)
            return cards, Hand(player_cards[:]), dealer_up, running_count
    raise RuntimeError(f"could not condition state for TC {target_tc} after {max_attempts:,} attempts")


def draw_dealer_hole(cards: list[Card], dealer_up: Card, rng: random.Random, rules: Rules) -> Card:
    disallowed: set[str] = set()
    dealer_value = upcard_value(dealer_up)
    if dealer_value == 11:
        disallowed.update(TEN_RANKS)
    elif rules.peek_ten_blackjack and dealer_value == 10:
        disallowed.add("A")
    candidates = [i for i, card in enumerate(cards) if card.rank not in disallowed]
    if not candidates:
        raise RuntimeError("no valid dealer hole cards under peek condition")
    return cards.pop(rng.choice(candidates))


def continue_player(
    player: Hand,
    pile: DrawPile,
    rules: Rules,
    version: str,
    dealer_up_value: int,
    wager: float,
) -> tuple[Hand, float, float | None]:
    while True:
        action = basic_action(player, dealer_up_value, version, rules.ace_one_card_rule)
        if action == "S":
            return player, wager, None
        one_card_ace_double = len(player.cards) == 1 and player.cards[0].rank == "A" and action == "D"
        one_card_ace_any = rules.ace_one_card_rule == "any" and len(player.cards) == 1 and player.cards[0].rank == "A"
        if action == "D":
            wager *= 2.0
        player.add(pile.draw())
        if player.busted:
            return player, wager, -wager
        if player.blackjack:
            return player, wager, None
        if one_card_ace_double or one_card_ace_any:
            return player, wager, None


def force_action_ev(
    cards: list[Card],
    player: Hand,
    dealer_up: Card,
    action: str,
    rules: Rules,
    version: str,
    rng: random.Random,
) -> float:
    cards = cards[:]
    rng.shuffle(cards)
    dealer = Hand([dealer_up, draw_dealer_hole(cards, dealer_up, rng, rules)])
    pile = DrawPile(cards)
    dealer_up_value = upcard_value(dealer_up)
    wager = 1.0

    if action == "S":
        dealer_play(dealer, pile)
        return settle_active_hand(player, dealer, wager, rules)

    if action == "D":
        wager *= 2.0
    elif action != "H":
        raise ValueError(f"unsupported action {action}")

    one_card_ace_double = len(player.cards) == 1 and player.cards[0].rank == "A" and action == "D"
    one_card_ace_any = rules.ace_one_card_rule == "any" and len(player.cards) == 1 and player.cards[0].rank == "A"
    player.add(pile.draw())
    if player.busted:
        return -wager
    if player.blackjack:
        dealer_play(dealer, pile)
        return blackjack_profit(player, dealer, wager, rules)
    if not (one_card_ace_double or one_card_ace_any):
        player, wager, resolved = continue_player(player, pile, rules, version, dealer_up_value, wager)
        if resolved is not None:
            return resolved

    dealer_play(dealer, pile)
    return settle_active_hand(player, dealer, wager, rules)


def scan(args: argparse.Namespace) -> list[dict[str, object]]:
    rng = random.Random(args.seed)
    suited, unsuited = BJ_VERSIONS[args.version]
    rules = Rules(
        decks=args.decks,
        penetration=1.0 - args.cut_decks / args.decks,
        suited_bj_pay=suited,
        unsuited_bj_pay=unsuited,
        ace_one_card_rule=args.ace_one_card_rule,
        dealer_completes_hand=args.dealer_completes_hand,
    )
    player_ranks = [parse_rank(part) for part in args.player.split(",")]
    dealer_rank = parse_rank(args.dealer)
    actions = [action.strip().upper() for action in args.actions.split(",") if action.strip()]
    rows: list[dict[str, object]] = []

    for target_tc in [item.strip() for item in args.true_counts.split(",") if item.strip()]:
        stats = {action: ActionStats() for action in actions}
        accepted = 0
        attempts = 0
        while accepted < args.rounds:
            attempts += 1
            if args.conditioning == "constructed":
                cards, player, dealer_up, running_count = make_conditioned_state_constructed(
                    rng,
                    args.decks,
                    player_ranks,
                    dealer_rank,
                    target_tc,
                    args.decks_remaining,
                    args.max_condition_attempts,
                )
            else:
                cards, player, dealer_up, running_count = make_conditioned_state(
                    rng,
                    args.decks,
                    player_ranks,
                    dealer_rank,
                    target_tc,
                    args.decks_remaining,
                    args.max_condition_attempts,
                )
            accepted += 1
            for action in actions:
                profit = force_action_ev(cards, Hand(player.cards[:]), dealer_up, action, rules, args.version, rng)
                stats[action].add(profit)
        best_action = max(actions, key=lambda action: stats[action].mean)
        for action in actions:
            stat = stats[action]
            rows.append(
                {
                    "player": args.player,
                    "dealer": args.dealer,
                    "tc": target_tc,
                    "decks_remaining": args.decks_remaining,
                    "action": action,
                    "rounds": stat.rounds,
                    "ev": stat.mean,
                    "sd": stat.sd,
                    "ci95": stat.se95,
                    "best_action": best_action,
                    "delta_vs_best": stat.mean - stats[best_action].mean,
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--player", default="T,6", help="comma-separated player ranks, e.g. T,6")
    parser.add_argument("--dealer", default="T", type=parse_rank)
    parser.add_argument("--true-counts", default="-2,-1,0,1,2,3,4")
    parser.add_argument("--decks-remaining", type=float, default=4.5)
    parser.add_argument("--rounds", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260708)
    parser.add_argument("--actions", default="H,S,D")
    parser.add_argument("--version", choices=["v1", "v2", "v3"], default="v1")
    parser.add_argument("--decks", type=int, default=6)
    parser.add_argument("--cut-decks", type=float, default=1.5)
    parser.add_argument("--ace-one-card-rule", choices=["any", "double"], default="any")
    parser.add_argument("--dealer-completes-hand", action="store_true")
    parser.add_argument("--conditioning", choices=["constructed", "rejection"], default="constructed")
    parser.add_argument("--max-condition-attempts", type=int, default=100_000)
    parser.add_argument("--csv", default="")
    args = parser.parse_args()

    rows = scan(args)
    print("DDM deviation scan")
    print(f"  player {args.player} vs dealer {args.dealer}")
    print(f"  decks_remaining: {args.decks_remaining}")
    print(f"  rounds/action/tc: {args.rounds:,}")
    print()
    print("TC  action       EV       95% CI   best   delta")
    for row in rows:
        print(
            f"{row['tc']:>3} {row['action']:>6}"
            f" {row['ev']:>9.5f} {row['ci95']:>9.5f}"
            f" {row['best_action']:>6} {row['delta_vs_best']:>9.5f}"
        )

    if args.csv:
        path = Path(args.csv)
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print()
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
