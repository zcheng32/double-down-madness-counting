#!/usr/bin/env python3
"""
Monte Carlo simulator for Double Down Madness Blackjack.

Implemented from the supplied rule sheet/screenshots:
- 6/8 deck shoe, no splits, no surrender.
- Dealer is dealt the first up card, then the player receives one card, then
  the dealer receives a hole card.
- Dealer hits soft 17.
- Player may hit or double after every received card.
- A full double matches the amount already in play, so the wager doubles.
- If the player's first card is an ace, the default rule gives the player
  exactly one more card after hit or double. Use --ace-one-card-rule double to
  reproduce the Wizard of Odds wording where only an ace double is restricted.
- Dealer bust total 22 pushes active main-game wagers.
- Because the Push 22 side bet must resolve, the dealer completes the hand
  even when all main-game player hands have already busted or resolved.
- Dealer blackjack is checked before player action on ace and ten up cards.
- Three configurable blackjack payout versions.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from dataclasses import dataclass


RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K")
SUITS = ("S", "H", "D", "C")
UPCARDS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
HI_LO = {
    "2": 1,
    "3": 1,
    "4": 1,
    "5": 1,
    "6": 1,
    "7": 0,
    "8": 0,
    "9": 0,
    "T": -1,
    "J": -1,
    "Q": -1,
    "K": -1,
    "A": -1,
}


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    @property
    def value(self) -> int:
        if self.rank == "A":
            return 11
        if self.rank in {"T", "J", "Q", "K"}:
            return 10
        return int(self.rank)


class Shoe:
    def __init__(self, decks: int, rng: random.Random):
        self.decks = decks
        self.rng = rng
        self.cards: list[Card] = []
        self.running_count = 0
        self.shuffle()

    def shuffle(self) -> None:
        self.cards = [Card(rank, suit) for _ in range(self.decks) for rank in RANKS for suit in SUITS]
        self.rng.shuffle(self.cards)
        self.running_count = 0

    def draw(self) -> Card:
        card = self.cards.pop()
        self.running_count += HI_LO[card.rank]
        return card

    @property
    def true_count(self) -> float:
        return self.running_count / max(len(self.cards) / 52.0, 0.25)


def estimated_true_count(shoe: Shoe, deck_estimate: str) -> float:
    exact_decks = len(shoe.cards) / 52.0
    if deck_estimate == "exact":
        return float(int(shoe.running_count / max(exact_decks, 0.25)))
    increments = {
        "full": 1.0,
        "half": 0.5,
    }
    if deck_estimate not in increments:
        raise ValueError(f"unknown true-count deck estimate mode: {deck_estimate}")
    increment = increments[deck_estimate]
    if increment == 0.0:
        decks_remaining = exact_decks
    else:
        decks_remaining = math.ceil(exact_decks / increment) * increment
    return float(int(shoe.running_count / max(decks_remaining, 0.25)))


@dataclass
class Hand:
    cards: list[Card]

    def add(self, card: Card) -> None:
        self.cards.append(card)

    @property
    def raw_total(self) -> int:
        return sum(card.value for card in self.cards)

    @property
    def total(self) -> int:
        total = self.raw_total
        aces = sum(card.rank == "A" for card in self.cards)
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    @property
    def soft(self) -> bool:
        total = self.raw_total
        aces = sum(card.rank == "A" for card in self.cards)
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return aces > 0 and total <= 21

    @property
    def busted(self) -> bool:
        return self.total > 21

    @property
    def blackjack(self) -> bool:
        return len(self.cards) == 2 and self.total == 21

    @property
    def suited_blackjack(self) -> bool:
        return self.blackjack and self.cards[0].suit == self.cards[1].suit


@dataclass(frozen=True)
class Rules:
    decks: int = 6
    penetration: float = 0.75
    suited_bj_pay: float = 2.0
    unsuited_bj_pay: float = 1.5
    peek_ten_blackjack: bool = True
    dealer_blackjack_pushes_player_blackjack: bool = False
    ace_one_card_rule: str = "any"
    dealer_completes_hand: bool = False


BJ_VERSIONS = {
    "v1": (2.0, 1.5),
    "v2": (1.5, 1.5),
    "v3": (3.0, 1.0),
}


HARD_TABLE = {
    2: "HHHHDDHHHH",
    3: "HHHHDHHHHH",
    4: "HHHHHHHHHH",
    5: "HHHHHHHHHH",
    6: "HHHHHHHHHH",
    7: "HHHHHHHHHH",
    8: "HHHDDDHHHH",
    9: "HDDDDDDHHH",
    10: "DDDDDDDDHH",
    11: "DDDDDDDDDD",
    12: "HHHSSHHHHH",
    13: "HSSSSHHHHH",
    14: "SSSSSHHHHH",
    15: "SSSSSHHHHH",
    16: "SSSSSHHHHH",
}

SOFT_TABLE = {
    12: "HDDDDDDHHH",
    13: "HHDDDDDHHH",
    14: "HHHDDDHHHH",
    15: "HHHHDHHHHH",
    16: "HHHHDHHHHH",
    17: "HHHHDDHHHH",
    18: "SSSDDSSHHH",
}


def upcard_value(card: Card) -> int:
    return 11 if card.rank == "A" else card.value


def table_lookup(row: str, dealer_up: int) -> str:
    return row[UPCARDS.index(dealer_up)]


def basic_action(hand: Hand, dealer_up: int, version: str, ace_one_card_rule: str = "any") -> str:
    first = hand.cards[0]
    if len(hand.cards) == 1:
        if first.value == 10:
            return "D"
        if first.rank == "A":
            if version == "v1" and dealer_up == 11 and ace_one_card_rule == "double":
                return "H"
            return "D"

    total = hand.total
    if total >= 19 and hand.soft:
        return "S"
    if total >= 17 and not hand.soft:
        return "S"
    if hand.soft:
        return table_lookup(SOFT_TABLE.get(total, "HHHHHHHHHH"), dealer_up)
    return table_lookup(HARD_TABLE.get(total, "HHHHHHHHHH"), dealer_up)


def count_cards(cards: list[Card]) -> int:
    return sum(HI_LO[card.rank] for card in cards)


def visible_true_count(visible_running_count: int, cards_remaining: int) -> int:
    return int(visible_running_count / max(cards_remaining / 52.0, 0.25))


def strategy_action(
    hand: Hand,
    dealer_up: int,
    version: str,
    ace_one_card_rule: str,
    strategy: str = "basic",
    true_count: int | None = None,
) -> str:
    action = basic_action(hand, dealer_up, version, ace_one_card_rule)
    if strategy != "tested-deviations" or true_count is None:
        return action

    total = hand.total
    if not hand.soft:
        if total == 16 and dealer_up == 10 and true_count >= 7:
            return "S"
        if total == 12 and dealer_up == 3 and true_count >= 4:
            return "S"
        if total == 12 and dealer_up == 4 and true_count >= 2:
            return "S"
        if total == 13 and dealer_up == 2 and true_count >= 4:
            return "S"

    if len(hand.cards) == 1 and hand.cards[0].rank == "8" and dealer_up == 4:
        if true_count <= 0:
            return "H"
        if true_count >= 3:
            return "D"

    return action


def dealer_play(dealer: Hand, shoe: Shoe) -> None:
    while dealer.total < 17 or (dealer.total == 17 and dealer.soft):
        dealer.add(shoe.draw())


def bet_units(true_count: float, ramp: list[tuple[float, float]]) -> float:
    amount = ramp[0][1]
    for threshold, units in ramp:
        if true_count >= threshold:
            amount = units
    return amount


def parse_ramp(text: str) -> list[tuple[float, float]]:
    ramp = []
    for item in text.split(","):
        threshold, units = item.split(":")
        ramp.append((float(threshold), float(units)))
    return sorted(ramp)


def tc_bucket(tc: float) -> str:
    floored = math.floor(tc)
    if floored <= -5:
        return "<=-5"
    if floored >= 8:
        return ">=8"
    return str(floored)


def blackjack_profit(player: Hand, dealer: Hand, wager: float, rules: Rules) -> float:
    if dealer.blackjack and rules.dealer_blackjack_pushes_player_blackjack:
        return 0.0
    pay = rules.suited_bj_pay if player.suited_blackjack else rules.unsuited_bj_pay
    return wager * pay


def play_spot_until_done(
    shoe: Shoe,
    rules: Rules,
    version: str,
    dealer_up: int,
    base_wager: float,
    strategy: str = "basic",
    visible_running_count: int | None = None,
) -> tuple[Hand, float, float | None]:
    player = Hand([shoe.draw()])
    if visible_running_count is not None:
        visible_running_count += HI_LO[player.cards[-1].rank]
    wager = base_wager
    while True:
        decision_tc = (
            visible_true_count(visible_running_count, len(shoe.cards)) if visible_running_count is not None else None
        )
        action = strategy_action(player, dealer_up, version, rules.ace_one_card_rule, strategy, decision_tc)
        if action == "S":
            return player, wager, None
        one_card_ace_double = len(player.cards) == 1 and player.cards[0].rank == "A" and action == "D"
        one_card_ace_any = rules.ace_one_card_rule == "any" and len(player.cards) == 1 and player.cards[0].rank == "A"
        if action == "D":
            wager *= 2.0
        player.add(shoe.draw())
        if visible_running_count is not None:
            visible_running_count += HI_LO[player.cards[-1].rank]

        if player.busted:
            return player, wager, -wager
        if player.blackjack:
            return player, wager, None
        if one_card_ace_double or one_card_ace_any:
            return player, wager, None


def settle_active_hand(player: Hand, dealer: Hand, wager: float, rules: Rules) -> float:
    if player.blackjack:
        return blackjack_profit(player, dealer, wager, rules)
    if dealer.blackjack:
        return -wager
    if dealer.busted:
        if dealer.total == 22:
            return 0.0
        return wager
    if player.total > dealer.total:
        return wager
    if player.total < dealer.total:
        return -wager
    return 0.0


def play_table_round(
    shoe: Shoe,
    rules: Rules,
    version: str,
    base_wager: float,
    user_spots: int = 1,
    other_spots: int = 0,
    strategy: str = "basic",
) -> tuple[float, float, float]:
    round_start_running_count = shoe.running_count
    dealer = Hand([shoe.draw()])
    dealer_up_card = dealer.cards[0]
    user_hands = [Hand([shoe.draw()]) for _ in range(user_spots)]
    other_hands = [Hand([shoe.draw()]) for _ in range(other_spots)]
    dealer.add(shoe.draw())
    dealer_up = upcard_value(dealer.cards[0])
    visible_running_count = (
        round_start_running_count
        + HI_LO[dealer_up_card.rank]
        + sum(count_cards(hand.cards) for hand in user_hands)
        + sum(count_cards(hand.cards) for hand in other_hands)
    )

    if dealer_up == 11 and dealer.blackjack:
        initial = base_wager * user_spots
        return -initial, initial, initial
    if rules.peek_ten_blackjack and dealer_up == 10 and dealer.blackjack:
        initial = base_wager * user_spots
        return -initial, initial, initial

    profit = 0.0
    initial_bet = base_wager * user_spots
    final_bet = 0.0
    active_user: list[tuple[Hand, float]] = []
    active_other = False
    dealer_needs_to_play = False

    for player in user_hands:
        wager = base_wager
        while True:
            decision_tc = visible_true_count(visible_running_count, len(shoe.cards))
            action = strategy_action(player, dealer_up, version, rules.ace_one_card_rule, strategy, decision_tc)
            if action == "S":
                active_user.append((player, wager))
                dealer_needs_to_play = True
                final_bet += wager
                break
            one_card_ace_double = len(player.cards) == 1 and player.cards[0].rank == "A" and action == "D"
            one_card_ace_any = rules.ace_one_card_rule == "any" and len(player.cards) == 1 and player.cards[0].rank == "A"
            if action == "D":
                wager *= 2.0
            player.add(shoe.draw())
            visible_running_count += HI_LO[player.cards[-1].rank]

            if player.busted:
                profit -= wager
                final_bet += wager
                break
            if player.blackjack:
                active_user.append((player, wager))
                final_bet += wager
                break
            if one_card_ace_double or one_card_ace_any:
                active_user.append((player, wager))
                dealer_needs_to_play = True
                final_bet += wager
                break

    for other in other_hands:
        while True:
            action = basic_action(other, dealer_up, version, rules.ace_one_card_rule)
            if action == "S":
                active_other = True
                break
            one_card_ace_double = len(other.cards) == 1 and other.cards[0].rank == "A" and action == "D"
            one_card_ace_any = rules.ace_one_card_rule == "any" and len(other.cards) == 1 and other.cards[0].rank == "A"
            other.add(shoe.draw())
            visible_running_count += HI_LO[other.cards[-1].rank]
            if other.busted or other.blackjack:
                break
            if one_card_ace_double or one_card_ace_any:
                active_other = True
                break

    if rules.dealer_completes_hand or dealer_needs_to_play or active_other:
        dealer_play(dealer, shoe)

    for player, wager in active_user:
        profit += settle_active_hand(player, dealer, wager, rules)
    return profit, initial_bet, final_bet


def play_round(
    shoe: Shoe,
    rules: Rules,
    version: str,
    base_wager: float,
    strategy: str = "basic",
) -> tuple[float, float, float]:
    return play_table_round(shoe, rules, version, base_wager, user_spots=1, other_spots=0, strategy=strategy)


def simulate(
    rules: Rules,
    version: str,
    rounds: int,
    seed: int,
    ramp: list[tuple[float, float]],
    user_spots: int = 1,
    other_spots: int = 0,
    strategy: str = "basic",
) -> dict:
    rng = random.Random(seed)
    shoe = Shoe(rules.decks, rng)
    spots_at_table = user_spots + other_spots
    round_reserve_cards = 12 * (spots_at_table + 1)
    cut_cards = max(20, round_reserve_cards, int(rules.decks * 52 * (1.0 - rules.penetration)))

    profit = 0.0
    initial_bet = 0.0
    final_bet = 0.0
    buckets: dict[str, list[float]] = {}

    for _ in range(rounds):
        if len(shoe.cards) <= cut_cards:
            shoe.shuffle()
        start_tc = shoe.true_count
        wager = bet_units(start_tc, ramp)
        round_profit, round_initial, round_final = play_table_round(
            shoe,
            rules,
            version,
            wager,
            user_spots=user_spots,
            other_spots=other_spots,
            strategy=strategy,
        )
        profit += round_profit
        initial_bet += round_initial
        final_bet += round_final
        buckets.setdefault(tc_bucket(start_tc), []).append(round_profit / round_initial)

    bucket_rows = []
    for bucket, values in sorted(buckets.items(), key=lambda kv: -99 if kv[0] == "<=-5" else 99 if kv[0] == ">=8" else int(kv[0])):
        bucket_rows.append(
            {
                "true_count_bucket": bucket,
                "rounds": len(values),
                "ev_per_initial_unit": sum(values) / len(values),
            }
        )
    return {
        "version": version,
        "rounds": rounds,
        "profit_units": profit,
        "avg_final_wager": final_bet / initial_bet,
        "ev_per_round": profit / rounds,
        "ev_per_initial_unit": profit / initial_bet,
        "ev_per_total_action": profit / final_bet,
        "buckets": bucket_rows,
    }


def make_rules(args: argparse.Namespace, version: str) -> Rules:
    suited, unsuited = BJ_VERSIONS[version]
    return Rules(
        decks=args.decks,
        penetration=args.penetration,
        suited_bj_pay=suited,
        unsuited_bj_pay=unsuited,
        peek_ten_blackjack=not args.no_peek_ten_blackjack,
        dealer_blackjack_pushes_player_blackjack=args.dealer_blackjack_pushes_player_blackjack,
        ace_one_card_rule=args.ace_one_card_rule,
        dealer_completes_hand=args.dealer_completes_hand,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=500_000)
    parser.add_argument("--seed", type=int, default=20260705)
    parser.add_argument("--decks", type=int, default=6)
    parser.add_argument("--penetration", type=float, default=0.75)
    parser.add_argument("--versions", default="v1,v2,v3")
    parser.add_argument("--ramp", default="-99:1", help="true-count threshold:units, e.g. -99:1,1:2,2:4")
    parser.add_argument("--user-spots", type=int, default=1)
    parser.add_argument("--other-spots", type=int, default=0)
    parser.add_argument("--bucket-csv", default="")
    parser.add_argument("--no-peek-ten-blackjack", action="store_true")
    parser.add_argument("--dealer-blackjack-pushes-player-blackjack", action="store_true")
    parser.add_argument("--ace-one-card-rule", choices=["any", "double"], default="any")
    parser.add_argument("--dealer-completes-hand", action="store_true")
    args = parser.parse_args()

    ramp = parse_ramp(args.ramp)
    csv_rows = []
    for version in [v.strip() for v in args.versions.split(",") if v.strip()]:
        result = simulate(
            make_rules(args, version),
            version,
            args.rounds,
            args.seed,
            ramp,
            user_spots=args.user_spots,
            other_spots=args.other_spots,
        )
        print(f"{version}:")
        print(f"  profit_units: {result['profit_units']:.2f}")
        print(f"  avg_final_wager: {result['avg_final_wager']:.4f}")
        print(f"  ev_per_initial_unit: {100 * result['ev_per_initial_unit']:.4f}%")
        print(f"  ev_per_total_action: {100 * result['ev_per_total_action']:.4f}%")
        print()
        csv_rows.extend({"version": version, **row} for row in result["buckets"])

    if args.bucket_csv:
        with open(args.bucket_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["version", "true_count_bucket", "rounds", "ev_per_initial_unit_pct"])
            writer.writeheader()
            writer.writerows(
                {
                    "version": row["version"],
                    "true_count_bucket": row["true_count_bucket"],
                    "rounds": row["rounds"],
                    "ev_per_initial_unit_pct": 100 * row["ev_per_initial_unit"],
                }
                for row in csv_rows
            )
        print(f"wrote {args.bucket_csv}")


if __name__ == "__main__":
    main()
