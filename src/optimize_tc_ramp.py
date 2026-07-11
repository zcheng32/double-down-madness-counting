#!/usr/bin/env python3
"""Optimize a TC betting ramp from bucket CSVs under a diffusion RoR target."""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import minimize


BUCKET_ORDER = ["<=-5", "-4", "-3", "-2", "-1", "0", "1", "2", "3", "4", "5", "6", "7", ">=8"]


@dataclass(frozen=True)
class Bucket:
    rounds: int
    ev_unit: float
    sd_unit: float


def tc_value(bucket: str) -> int:
    if bucket == "<=-5":
        return -5
    if bucket == ">=8":
        return 8
    return int(bucket)


def read_bucket_csv(path: Path) -> dict[str, Bucket]:
    rows: dict[str, Bucket] = {}
    with path.open() as f:
        for row in csv.DictReader(f):
            rows[row["true_count_bucket"]] = Bucket(
                rounds=int(row["rounds"]),
                ev_unit=float(row["ev_units_per_round"]),
                sd_unit=float(row["sd_units_per_round"]),
            )
    missing = [bucket for bucket in BUCKET_ORDER if bucket not in rows]
    if missing:
        raise SystemExit(f"{path} missing buckets: {missing}")
    return rows


def compose_arrays(one_csv: Path, two_csv: Path, two_hands_from: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    one = read_bucket_csv(one_csv)
    two = read_bucket_csv(two_csv)
    total_rounds = sum(one[bucket].rounds for bucket in BUCKET_ORDER)

    freqs = []
    mu_per_dollar = []
    sd_per_dollar = []
    spots = []
    for bucket in BUCKET_ORDER:
        use_two = tc_value(bucket) >= two_hands_from
        row = two[bucket] if use_two else one[bucket]
        freqs.append(one[bucket].rounds / total_rounds)
        mu_per_dollar.append(row.ev_unit)
        sd_per_dollar.append(row.sd_unit)
        spots.append(2.0 if use_two else 1.0)
    return np.array(freqs), np.array(mu_per_dollar), np.array(sd_per_dollar), np.array(spots)


def moments(bets: np.ndarray, freqs: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> tuple[float, float]:
    bucket_mean = mu * bets
    second = (sd * bets) ** 2 + bucket_mean**2
    ev = float(np.sum(freqs * bucket_mean))
    variance = float(np.sum(freqs * second) - ev * ev)
    return ev, max(variance, 0.0)


def risk_of_ruin(bankroll: float, ev_round: float, variance_round: float) -> float:
    if bankroll <= 0 or ev_round <= 0 or variance_round <= 0:
        return 1.0
    return math.exp(-2.0 * ev_round * bankroll / variance_round)


def optimize(args: argparse.Namespace) -> dict[str, object]:
    freqs, mu, sd, spots = compose_arrays(Path(args.one), Path(args.two), args.two_hands_from)
    target_log = math.log(1.0 / args.target_ror)

    # A conservative warm start: play only positive buckets, then scale to the RoR boundary.
    x0 = np.where(mu > 0, args.max_bet * 0.25, 0.0)
    for i in range(1, len(x0)):
        x0[i] = max(x0[i], x0[i - 1])
    ev0, var0 = moments(x0, freqs, mu, sd)
    if ev0 > 0 and var0 > 0:
        scale = min(1.0, (2.0 * ev0 * args.bankroll / (target_log * var0)))
        x0 *= max(scale, 0.05)

    bounds = [(0.0, args.max_bet) for _ in BUCKET_ORDER]

    constraints = []
    # RoR <= target means variance <= 2 * EV * bankroll / log(1/target).
    constraints.append(
        {
            "type": "ineq",
            "fun": lambda x: (2.0 * moments(x, freqs, mu, sd)[0] * args.bankroll / target_log)
            - moments(x, freqs, mu, sd)[1],
        }
    )
    # Monotone non-decreasing by TC bucket.
    for i in range(len(BUCKET_ORDER) - 1):
        constraints.append({"type": "ineq", "fun": lambda x, i=i: x[i + 1] - x[i]})
    # Avoid playing negative-EV buckets unless monotonicity forces it.
    for i, edge in enumerate(mu):
        if edge < 0:
            constraints.append({"type": "ineq", "fun": lambda x, i=i: args.negative_bucket_cap - x[i]})

    result = minimize(
        lambda x: -moments(x, freqs, mu, sd)[0],
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 2000, "ftol": 1e-10, "disp": False},
    )
    if not result.success:
        raise SystemExit(f"optimization failed: {result.message}")

    bets = result.x
    if args.round_to:
        bets = np.round(bets / args.round_to) * args.round_to
        # Rounded bets may slightly break the target. Scale down until RoR is under target again.
        for _ in range(100):
            ev, var = moments(bets, freqs, mu, sd)
            if risk_of_ruin(args.bankroll, ev, var) <= args.target_ror:
                break
            bets *= 0.99
            bets = np.floor(bets / args.round_to) * args.round_to

    ev, var = moments(bets, freqs, mu, sd)
    sd_round = math.sqrt(var)
    avg_bet = float(np.sum(freqs * bets * spots))
    return {
        "bets": bets,
        "freqs": freqs,
        "mu": mu,
        "spots": spots,
        "ev_round": ev,
        "sd_round": sd_round,
        "avg_bet": avg_bet,
        "ev_hour": ev * args.rph,
        "sd_hour": sd_round * math.sqrt(args.rph),
        "n0_rounds": var / (ev * ev) if ev > 0 else math.inf,
        "ror": risk_of_ruin(args.bankroll, ev, var),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--one", required=True)
    parser.add_argument("--two", required=True)
    parser.add_argument("--label", default="game")
    parser.add_argument("--bankroll", type=float, default=20_000.0)
    parser.add_argument("--target-ror", type=float, default=0.01)
    parser.add_argument("--rph", type=float, default=98.0)
    parser.add_argument("--two-hands-from", type=int, default=2)
    parser.add_argument("--max-bet", type=float, default=500.0)
    parser.add_argument("--negative-bucket-cap", type=float, default=0.0)
    parser.add_argument("--round-to", type=float, default=5.0)
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    opt = optimize(args)
    print(f"{args.label}")
    print(f"  EV/hour: ${opt['ev_hour']:.2f}")
    print(f"  SD/hour: ${opt['sd_hour']:.2f}")
    print(f"  avg initial bet: ${opt['avg_bet']:.2f}")
    print(f"  N0: {opt['n0_rounds']:.0f} rounds")
    print(f"  RoR: {100.0 * opt['ror']:.3f}%")
    print("  bets per spot:")
    for bucket, bet, edge, freq, spots in zip(BUCKET_ORDER, opt["bets"], opt["mu"], opt["freqs"], opt["spots"]):
        print(f"    {bucket:>4s}: ${bet:7.2f}  spots={int(spots)}  edge={100.0*edge:7.3f}%  freq={100.0*freq:6.3f}%")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with Path(args.out).open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "bucket",
                    "bet_per_spot",
                    "spots",
                    "freq",
                    "edge_pct",
                    "ev_hour",
                    "sd_hour",
                    "avg_initial_bet",
                    "n0_rounds",
                    "ror_pct",
                ],
            )
            writer.writeheader()
            for bucket, bet, edge, freq, spots in zip(BUCKET_ORDER, opt["bets"], opt["mu"], opt["freqs"], opt["spots"]):
                writer.writerow(
                    {
                        "bucket": bucket,
                        "bet_per_spot": bet,
                        "spots": int(spots),
                        "freq": freq,
                        "edge_pct": 100.0 * edge,
                        "ev_hour": opt["ev_hour"],
                        "sd_hour": opt["sd_hour"],
                        "avg_initial_bet": opt["avg_bet"],
                        "n0_rounds": opt["n0_rounds"],
                        "ror_pct": 100.0 * opt["ror"],
                    }
                )
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
