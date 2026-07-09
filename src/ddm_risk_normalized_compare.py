#!/usr/bin/env python3
"""Risk-normalized comparison of DDM TC estimation modes.

This reads one-spot and two-spot bucket CSVs produced by
ddm_bankroll_calculator.py and composes a calculator-style bet ramp. It then
compares TC modes under:

- raw displayed bets,
- equal average initial bet, and
- equal standard deviation per round.

The scaling keeps each mode's ramp shape unchanged. It answers a narrower
question than ramp optimization: if I use the same spread shape, how much EV is
lost when I normalize the modes to comparable risk?
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path


BUCKET_ORDER = ["<=-5", "-4", "-3", "-2", "-1", "0", "1", "2", "3", "4", "5", "6", "7", ">=8"]


@dataclass(frozen=True)
class ComposedStats:
    rounds: int
    ev_per_round: float
    sd_per_round: float
    avg_initial_bet: float
    ev_per_avg_bet_pct: float
    n0_rounds: float

    def scaled(self, factor: float) -> "ComposedStats":
        ev = self.ev_per_round * factor
        sd = self.sd_per_round * factor
        avg = self.avg_initial_bet * factor
        variance = sd * sd
        n0 = variance / (ev * ev) if ev > 0 else math.inf
        return ComposedStats(
            rounds=self.rounds,
            ev_per_round=ev,
            sd_per_round=sd,
            avg_initial_bet=avg,
            ev_per_avg_bet_pct=100.0 * ev / avg if avg else 0.0,
            n0_rounds=n0,
        )


def tc_value(bucket: str) -> int:
    if bucket == "<=-5":
        return -5
    if bucket == ">=8":
        return 8
    return int(bucket)


def parse_bets(text: str) -> dict[str, float]:
    values = [float(item.strip()) for item in text.split(",") if item.strip()]
    if len(values) != len(BUCKET_ORDER):
        raise SystemExit(f"--bets must provide {len(BUCKET_ORDER)} comma-separated values")
    return dict(zip(BUCKET_ORDER, values))


def read_bucket_csv(path: Path) -> dict[str, dict[str, float]]:
    rows = {}
    with path.open() as f:
        for row in csv.DictReader(f):
            rows[row["true_count_bucket"]] = {
                "rounds": int(row["rounds"]),
                "ev": float(row["ev_units_per_round"]),
                "sd": float(row["sd_units_per_round"]),
            }
    missing = [bucket for bucket in BUCKET_ORDER if bucket not in rows]
    if missing:
        raise SystemExit(f"{path} missing buckets: {', '.join(missing)}")
    return rows


def compose(one_spot_csv: Path, two_spot_csv: Path, bets: dict[str, float], two_hands_from: str) -> ComposedStats:
    one = read_bucket_csv(one_spot_csv)
    two = read_bucket_csv(two_spot_csv)
    rounds = sum(int(one[bucket]["rounds"]) for bucket in BUCKET_ORDER)
    ev = 0.0
    second = 0.0
    avg_bet = 0.0

    for bucket in BUCKET_ORDER:
        use_two = two_hands_from == "always" or (
            two_hands_from != "never" and tc_value(bucket) >= float(two_hands_from)
        )
        row = two[bucket] if use_two else one[bucket]
        spots = 2 if use_two else 1
        freq = one[bucket]["rounds"] / rounds
        bet = bets[bucket]
        # CSV EV/SD are for a $1/unit bet per spot. Convert to displayed bet.
        bucket_ev = row["ev"] * bet
        bucket_sd = row["sd"] * bet
        ev += freq * bucket_ev
        second += freq * (bucket_sd * bucket_sd + bucket_ev * bucket_ev)
        avg_bet += freq * bet * spots

    variance = max(0.0, second - ev * ev)
    sd = math.sqrt(variance)
    n0 = variance / (ev * ev) if ev > 0 else math.inf
    return ComposedStats(
        rounds=rounds,
        ev_per_round=ev,
        sd_per_round=sd,
        avg_initial_bet=avg_bet,
        ev_per_avg_bet_pct=100.0 * ev / avg_bet if avg_bet else 0.0,
        n0_rounds=n0,
    )


def cut_tag(cut_decks: float | None) -> str:
    if cut_decks is None:
        return ""
    return f"cut{cut_decks:.2f}".rstrip("0").rstrip(".").replace(".", "p")


def mode_paths(data_dir: Path, mode: str, cut_decks: float | None) -> tuple[Path, Path]:
    cut_filter = f"*{cut_tag(cut_decks)}" if cut_decks is not None else "*"
    matches_one = sorted(data_dir.glob(f"{cut_filter}*u1_o1*tc{mode}_clean.csv"))
    matches_two = sorted(data_dir.glob(f"{cut_filter}*u2_o1*tc{mode}_clean.csv"))
    if mode == "exact":
        matches_one = sorted(data_dir.glob(f"{cut_filter}*u1_o1*tcexact_clean.csv"))
        matches_two = sorted(data_dir.glob(f"{cut_filter}*u2_o1*tcexact_clean.csv"))
    if len(matches_one) != 1 or len(matches_two) != 1:
        label = f" cut {cut_decks:g}" if cut_decks is not None else ""
        raise SystemExit(f"expected one u1 and one u2 CSV for {mode}{label} in {data_dir}")
    return matches_one[0], matches_two[0]


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--decks", type=float, default=6.0)
    parser.add_argument("--cut-decks", type=float, default=None)
    parser.add_argument("--two-hands-from", default="2")
    parser.add_argument(
        "--bets",
        default="0,10,10,10,10,10,25,30,50,100,150,200,250,250",
        help="bets for <=-5,-4,-3,-2,-1,0,1,2,3,4,5,6,7,>=8",
    )
    parser.add_argument("--target-mode", choices=["exact", "half", "full"], default="exact")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    bets = parse_bets(args.bets)
    raw = {}
    for mode in ["exact", "half", "full"]:
        one, two = mode_paths(data_dir, mode, args.cut_decks)
        raw[mode] = compose(one, two, bets, args.two_hands_from)

    target_avg = raw[args.target_mode].avg_initial_bet
    target_sd = raw[args.target_mode].sd_per_round

    rows: list[dict[str, object]] = []
    for mode, stats in raw.items():
        variants = {
            "raw": stats,
            f"equal_avg_bet_to_{args.target_mode}": stats.scaled(target_avg / stats.avg_initial_bet),
            f"equal_sd_to_{args.target_mode}": stats.scaled(target_sd / stats.sd_per_round),
        }
        for comparison, value in variants.items():
            rows.append(
                {
                    "comparison": comparison,
                    "cut_decks": args.cut_decks if args.cut_decks is not None else "",
                    "penetration_pct": (
                        100.0 * (1.0 - args.cut_decks / args.decks) if args.cut_decks is not None else ""
                    ),
                    "mode": mode,
                    "rounds": value.rounds,
                    "scale_factor": value.ev_per_round / stats.ev_per_round if stats.ev_per_round else 0.0,
                    "ev_per_round": value.ev_per_round,
                    "ci95_ev_per_round": 1.96 * value.sd_per_round / math.sqrt(value.rounds),
                    "sd_per_round": value.sd_per_round,
                    "avg_initial_bet": value.avg_initial_bet,
                    "ev_per_avg_bet_pct": value.ev_per_avg_bet_pct,
                    "n0_rounds": value.n0_rounds,
                }
            )

    write_rows(Path(args.out), rows)
    print(f"wrote {args.out}")
    for row in rows:
        if row["comparison"] == "raw":
            print(
                f"{row['mode']:>5} raw: EV {float(row['ev_per_round']):.3f}, "
                f"SD {float(row['sd_per_round']):.2f}, avg bet {float(row['avg_initial_bet']):.2f}, "
                f"EV/bet {float(row['ev_per_avg_bet_pct']):.3f}%"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
