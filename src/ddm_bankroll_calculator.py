#!/usr/bin/env python3
"""Bankroll and ramp calculator for Double Down Madness Blackjack."""

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
    Rules,
    Shoe,
    bet_units,
    estimated_true_count,
    parse_ramp,
    play_table_round,
    tc_bucket,
)


@dataclass
class BucketStats:
    rounds: int = 0
    initial_bet_units: float = 0.0
    final_wager_units: float = 0.0
    profit_units: float = 0.0
    profit_sq_units: float = 0.0

    def add(self, profit: float, initial_bet: float, final_wager: float) -> None:
        self.rounds += 1
        self.initial_bet_units += initial_bet
        self.final_wager_units += final_wager
        self.profit_units += profit
        self.profit_sq_units += profit * profit

    @property
    def mean_profit_per_round(self) -> float:
        return self.profit_units / self.rounds if self.rounds else 0.0

    @property
    def variance_per_round(self) -> float:
        if not self.rounds:
            return 0.0
        mean = self.mean_profit_per_round
        return max(0.0, self.profit_sq_units / self.rounds - mean * mean)

    @property
    def sd_per_round(self) -> float:
        return math.sqrt(self.variance_per_round)

    @property
    def avg_initial_bet(self) -> float:
        return self.initial_bet_units / self.rounds if self.rounds else 0.0

    @property
    def avg_final_wager(self) -> float:
        return self.final_wager_units / self.rounds if self.rounds else 0.0


def sort_bucket_key(bucket: str) -> int:
    if bucket == "<=-5":
        return -99
    if bucket == ">=8":
        return 99
    return int(bucket)


def risk_of_ruin_approx(bankroll_units: float, mean_per_round: float, variance_per_round: float) -> float:
    if bankroll_units <= 0:
        return 1.0
    if mean_per_round <= 0 or variance_per_round <= 0:
        return 1.0
    return math.exp(-2.0 * mean_per_round * bankroll_units / variance_per_round)


def simulate_bankroll(
    rules: Rules,
    version: str,
    rounds: int,
    seed: int,
    ramp: list[tuple[float, float]],
    user_spots: int = 1,
    other_spots: int = 0,
    tc_deck_estimate: str = "exact",
    strategy: str = "basic",
) -> tuple[BucketStats, dict[str, BucketStats]]:
    rng = random.Random(seed)
    shoe = Shoe(rules.decks, rng)
    spots_at_table = user_spots + other_spots
    round_reserve_cards = 12 * (spots_at_table + 1)
    cut_cards = max(20, round_reserve_cards, int(rules.decks * 52 * (1.0 - rules.penetration)))
    total = BucketStats()
    buckets: dict[str, BucketStats] = {}

    for _ in range(rounds):
        if len(shoe.cards) <= cut_cards:
            shoe.shuffle()
        start_tc = estimated_true_count(shoe, tc_deck_estimate)
        initial_bet = bet_units(start_tc, ramp)
        profit, round_initial, final_wager = play_table_round(
            shoe,
            rules,
            version,
            initial_bet,
            user_spots=user_spots,
            other_spots=other_spots,
            strategy=strategy,
        )
        total.add(profit, round_initial, final_wager)
        bucket = tc_bucket(start_tc)
        buckets.setdefault(bucket, BucketStats()).add(profit, round_initial, final_wager)

    return total, buckets


def write_bucket_csv(path: Path, buckets: dict[str, BucketStats], unit_size: float) -> None:
    rows = []
    for bucket in sorted(buckets, key=sort_bucket_key):
        stats = buckets[bucket]
        rows.append(
            {
                "true_count_bucket": bucket,
                "rounds": stats.rounds,
                "avg_initial_bet_units": stats.avg_initial_bet,
                "avg_final_wager_units": stats.avg_final_wager,
                "ev_units_per_round": stats.mean_profit_per_round,
                "ev_dollars_per_round": stats.mean_profit_per_round * unit_size,
                "sd_units_per_round": stats.sd_per_round,
                "ev_per_initial_bet_pct": 100.0 * stats.profit_units / stats.initial_bet_units
                if stats.initial_bet_units
                else 0.0,
                "profit_units": stats.profit_units,
            }
        )
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=2_000_000)
    parser.add_argument("--seed", type=int, default=20260707)
    parser.add_argument("--version", choices=["v1", "v2", "v3"], default="v1")
    parser.add_argument("--decks", type=int, default=6)
    parser.add_argument("--penetration", type=float, default=0.75)
    parser.add_argument("--ace-one-card-rule", choices=["any", "double"], default="any")
    parser.add_argument("--ramp", default="-99:1,2:4,3:8,4:12,5:16")
    parser.add_argument("--user-spots", type=int, default=1)
    parser.add_argument("--other-spots", type=int, default=0)
    parser.add_argument("--bankroll", type=float, default=10_000.0)
    parser.add_argument("--unit-size", type=float, default=25.0)
    parser.add_argument("--hands-per-hour", type=float, default=60.0)
    parser.add_argument("--tc-deck-estimate", choices=["exact", "exact-int", "1", "0.5"], default="exact")
    parser.add_argument("--strategy", choices=["basic", "tested-deviations"], default="basic")
    parser.add_argument("--dealer-completes-hand", action="store_true")
    parser.add_argument("--bucket-csv", default="")
    args = parser.parse_args()

    suited, unsuited = BJ_VERSIONS[args.version]
    rules = Rules(
        decks=args.decks,
        penetration=args.penetration,
        suited_bj_pay=suited,
        unsuited_bj_pay=unsuited,
        ace_one_card_rule=args.ace_one_card_rule,
        dealer_completes_hand=args.dealer_completes_hand,
    )
    ramp = parse_ramp(args.ramp)
    total, buckets = simulate_bankroll(
        rules,
        args.version,
        args.rounds,
        args.seed,
        ramp,
        user_spots=args.user_spots,
        other_spots=args.other_spots,
        tc_deck_estimate=args.tc_deck_estimate,
        strategy=args.strategy,
    )

    bankroll_units = args.bankroll / args.unit_size
    mean = total.mean_profit_per_round
    variance = total.variance_per_round
    sd = total.sd_per_round
    ror = risk_of_ruin_approx(bankroll_units, mean, variance)
    n0 = variance / (mean * mean) if mean > 0 else math.inf

    print("Double Down Madness bankroll calculator")
    print(f"  version: {args.version}")
    print(f"  ace_one_card_rule: {args.ace_one_card_rule}")
    print(f"  decks / penetration: {args.decks} / {args.penetration:.2f}")
    print(f"  tc_deck_estimate: {args.tc_deck_estimate}")
    print(f"  strategy: {args.strategy}")
    print(f"  dealer_completes_hand: {args.dealer_completes_hand}")
    print(f"  user_spots / other_spots: {args.user_spots} / {args.other_spots}")
    print(f"  rounds: {args.rounds:,}")
    print(f"  ramp: {args.ramp}")
    print(f"  bankroll: ${args.bankroll:,.2f} ({bankroll_units:.2f} units)")
    print(f"  unit_size: ${args.unit_size:,.2f}")
    print()
    print("Results")
    print(f"  EV per hand: {mean:.6f} units (${mean * args.unit_size:.4f})")
    print(f"  EV per 100 hands: {100.0 * mean:.4f} units (${100.0 * mean * args.unit_size:.2f})")
    print(f"  EV per hour: {args.hands_per_hour * mean:.4f} units (${args.hands_per_hour * mean * args.unit_size:.2f})")
    print(f"  SD per hand: {sd:.4f} units (${sd * args.unit_size:.2f})")
    print(f"  average initial bet: {total.avg_initial_bet:.4f} units")
    print(f"  average final wager/action: {total.avg_final_wager:.4f} units")
    print(f"  EV / initial bet: {100.0 * total.profit_units / total.initial_bet_units:.4f}%")
    print(f"  EV / total action: {100.0 * total.profit_units / total.final_wager_units:.4f}%")
    print(f"  N0: {n0:,.0f} hands" if math.isfinite(n0) else "  N0: not favorable")
    print(f"  approximate risk of ruin: {100.0 * ror:.4f}%")
    print()
    print("Bucket summary")
    print("  TC       rounds       bet     EV/hand      EV/bet")
    for bucket in sorted(buckets, key=sort_bucket_key):
        stats = buckets[bucket]
        ev_bet = 100.0 * stats.profit_units / stats.initial_bet_units if stats.initial_bet_units else 0.0
        print(
            f"  {bucket:>4} {stats.rounds:>10,} {stats.avg_initial_bet:>8.2f}"
            f" {stats.mean_profit_per_round:>11.5f} {ev_bet:>10.4f}%"
        )

    if args.bucket_csv:
        write_bucket_csv(Path(args.bucket_csv), buckets, args.unit_size)
        print()
        print(f"wrote {args.bucket_csv}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
