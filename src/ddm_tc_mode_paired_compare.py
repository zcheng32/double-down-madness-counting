#!/usr/bin/env python3
"""Paired comparison of true-count estimation modes.

Each sampled table round starts from one shared shoe state. The script clones
that state and evaluates exact/half/full from the same card order, which greatly
reduces Monte Carlo noise when comparing TC estimation modes.

If two-hand thresholds are enabled, modes may play a different number of spots.
In that case this is a paired opportunity comparison, not three independent
complete shoe histories.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
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
)


MODES = ("exact", "half", "full")


@dataclass
class RunningStats:
    n: int = 0
    total: float = 0.0
    total_sq: float = 0.0

    def add(self, value: float) -> None:
        self.n += 1
        self.total += value
        self.total_sq += value * value

    @property
    def mean(self) -> float:
        return self.total / self.n if self.n else 0.0

    @property
    def variance(self) -> float:
        if not self.n:
            return 0.0
        return max(0.0, self.total_sq / self.n - self.mean * self.mean)

    @property
    def sd(self) -> float:
        return math.sqrt(self.variance)

    @property
    def se(self) -> float:
        return self.sd / math.sqrt(self.n) if self.n else 0.0


@dataclass
class ModeStats:
    profit: RunningStats
    initial_bet: RunningStats
    final_wager: RunningStats

    @classmethod
    def make(cls) -> "ModeStats":
        return cls(RunningStats(), RunningStats(), RunningStats())


def clone_shoe(shoe: Shoe) -> Shoe:
    clone = object.__new__(Shoe)
    clone.decks = shoe.decks
    clone.rng = shoe.rng
    clone.cards = list(shoe.cards)
    clone.running_count = shoe.running_count
    return clone


def spots_for(tc: float, two_hands_from: str) -> int:
    if two_hands_from == "never":
        return 1
    if two_hands_from == "always":
        return 2
    return 2 if tc >= float(two_hands_from) else 1


def write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=20260709)
    parser.add_argument("--version", choices=["v1", "v2", "v3"], default="v1")
    parser.add_argument("--decks", type=int, default=6)
    parser.add_argument("--cut-decks", type=float, default=1.0)
    parser.add_argument("--ramp", default="-99:10,1:25,2:30,3:50,4:100,5:150,6:200,7:250")
    parser.add_argument("--two-hands-from", default="2", help="never, always, or numeric TC threshold")
    parser.add_argument("--other-spots", type=int, default=0)
    parser.add_argument("--strategy", choices=["basic", "tested-deviations"], default="basic")
    parser.add_argument("--out", default="outputs/tc_mode_paired_summary.csv")
    args = parser.parse_args()

    suited, unsuited = BJ_VERSIONS[args.version]
    rules = Rules(
        decks=args.decks,
        penetration=1.0 - args.cut_decks / args.decks,
        suited_bj_pay=suited,
        unsuited_bj_pay=unsuited,
        ace_one_card_rule="any",
    )
    ramp = parse_ramp(args.ramp)
    rng = random.Random(args.seed)
    master = Shoe(rules.decks, rng)
    max_user_spots = 2 if args.two_hands_from != "never" else 1
    spots_at_table = max_user_spots + args.other_spots
    round_reserve_cards = 12 * (spots_at_table + 1)
    cut_cards = max(20, round_reserve_cards, round(args.cut_decks * 52))

    mode_stats = {mode: ModeStats.make() for mode in MODES}
    pair_diff = {mode: RunningStats() for mode in MODES if mode != "exact"}

    for _ in range(args.rounds):
        if len(master.cards) <= cut_cards:
            master.shuffle()

        results: dict[str, float] = {}
        for mode in MODES:
            shoe = clone_shoe(master)
            tc = estimated_true_count(shoe, mode)
            wager = bet_units(tc, ramp)
            user_spots = spots_for(tc, args.two_hands_from)
            profit, initial, final = play_table_round(
                shoe,
                rules,
                args.version,
                wager,
                user_spots=user_spots,
                other_spots=args.other_spots,
                strategy=args.strategy,
            )
            mode_stats[mode].profit.add(profit)
            mode_stats[mode].initial_bet.add(initial)
            mode_stats[mode].final_wager.add(final)
            results[mode] = profit

        for mode in pair_diff:
            pair_diff[mode].add(results[mode] - results["exact"])

        # Advance the master shoe through a neutral one-spot exact round to
        # sample realistic pre-round shoe states without letting one TC mode
        # define the future states for every other mode.
        advance_tc = estimated_true_count(master, "exact")
        advance_wager = bet_units(advance_tc, ramp)
        play_table_round(
            master,
            rules,
            args.version,
            advance_wager,
            user_spots=1,
            other_spots=args.other_spots,
            strategy=args.strategy,
        )

    rows: list[dict[str, object]] = []
    exact_ev = mode_stats["exact"].profit.mean
    for mode in MODES:
        stats = mode_stats[mode]
        ev = stats.profit.mean
        avg_bet = stats.initial_bet.mean
        rows.append(
            {
                "row_type": "mode",
                "mode": mode,
                "rounds": stats.profit.n,
                "ev_per_round": ev,
                "ev_95ci": 1.96 * stats.profit.se,
                "sd_per_round": stats.profit.sd,
                "avg_initial_bet": avg_bet,
                "avg_final_wager": stats.final_wager.mean,
                "ev_per_initial_bet_pct": 100.0 * ev / avg_bet if avg_bet else 0.0,
                "paired_diff_vs_exact": "" if mode == "exact" else ev - exact_ev,
                "paired_diff_95ci": "",
            }
        )
    for mode, diff in pair_diff.items():
        rows.append(
            {
                "row_type": "paired_diff",
                "mode": f"{mode}-exact",
                "rounds": diff.n,
                "ev_per_round": "",
                "ev_95ci": "",
                "sd_per_round": diff.sd,
                "avg_initial_bet": "",
                "avg_final_wager": "",
                "ev_per_initial_bet_pct": "",
                "paired_diff_vs_exact": diff.mean,
                "paired_diff_95ci": 1.96 * diff.se,
            }
        )

    write_summary(Path(args.out), rows)

    print(f"Paired TC mode comparison: {args.rounds:,} rounds")
    print(f"  cut: {args.cut_decks:g} decks, two_hands_from: {args.two_hands_from}")
    print(f"  output: {args.out}")
    print()
    print("Mode results")
    for row in rows:
        if row["row_type"] != "mode":
            continue
        print(
            f"  {row['mode']:>5}: EV/round {float(row['ev_per_round']): .6f}, "
            f"95% CI +/- {float(row['ev_95ci']):.6f}, "
            f"avg bet {float(row['avg_initial_bet']):.3f}, "
            f"EV/bet {float(row['ev_per_initial_bet_pct']):.3f}%"
        )
    print()
    print("Paired differences")
    for row in rows:
        if row["row_type"] != "paired_diff":
            continue
        print(
            f"  {row['mode']:>10}: {float(row['paired_diff_vs_exact']): .6f} "
            f"+/- {float(row['paired_diff_95ci']):.6f} per round"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
