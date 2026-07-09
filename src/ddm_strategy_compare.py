#!/usr/bin/env python3
"""Compare basic strategy against tested DDM deviations with full-shoe simulation."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from ddm_bankroll_calculator import simulate_bankroll
from ddm_madness_counter_sim import BJ_VERSIONS, Rules, parse_ramp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds-per-seed", type=int, default=2_000_000)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=202607080)
    parser.add_argument("--version", choices=["v1", "v2", "v3"], default="v1")
    parser.add_argument("--decks", type=int, default=6)
    parser.add_argument("--penetration", type=float, default=5 / 6)
    parser.add_argument("--ace-one-card-rule", choices=["any", "double"], default="any")
    parser.add_argument("--tc-deck-estimate", choices=["exact", "exact-int", "1", "0.5"], default="exact-int")
    parser.add_argument("--ramp", default="-99:1,1:2,2:4,3:8,4:12,5:16")
    parser.add_argument("--user-spots", type=int, default=1)
    parser.add_argument("--other-spots", type=int, default=0)
    parser.add_argument("--out", default="outputs/ddm_strategy_compare.csv")
    return parser.parse_args()


def row_for(strategy: str, seed: int, args: argparse.Namespace) -> dict[str, object]:
    suited, unsuited = BJ_VERSIONS[args.version]
    rules = Rules(
        decks=args.decks,
        penetration=args.penetration,
        suited_bj_pay=suited,
        unsuited_bj_pay=unsuited,
        ace_one_card_rule=args.ace_one_card_rule,
    )
    total, _ = simulate_bankroll(
        rules=rules,
        version=args.version,
        rounds=args.rounds_per_seed,
        seed=seed,
        ramp=parse_ramp(args.ramp),
        user_spots=args.user_spots,
        other_spots=args.other_spots,
        tc_deck_estimate=args.tc_deck_estimate,
        strategy=strategy,
    )
    return {
        "strategy": strategy,
        "seed": seed,
        "rounds": args.rounds_per_seed,
        "profit_units": total.profit_units,
        "initial_bet_units": total.initial_bet_units,
        "final_wager_units": total.final_wager_units,
        "ev_units_per_round": total.mean_profit_per_round,
        "sd_units_per_round": total.sd_per_round,
        "ev_per_initial_bet_pct": 100.0 * total.profit_units / total.initial_bet_units,
        "ev_per_total_action_pct": 100.0 * total.profit_units / total.final_wager_units,
        "avg_initial_bet": total.avg_initial_bet,
        "avg_final_wager": total.avg_final_wager,
    }


def aggregate(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    for strategy in sorted({str(row["strategy"]) for row in rows}):
        group = [row for row in rows if row["strategy"] == strategy]
        rounds = sum(int(row["rounds"]) for row in group)
        profit = sum(float(row["profit_units"]) for row in group)
        initial = sum(float(row["initial_bet_units"]) for row in group)
        final = sum(float(row["final_wager_units"]) for row in group)
        # Average per-seed variances as a practical run-level uncertainty estimate.
        evs = [float(row["ev_units_per_round"]) for row in group]
        mean_ev = profit / rounds
        seed_sd = math.sqrt(sum((ev - sum(evs) / len(evs)) ** 2 for ev in evs) / (len(evs) - 1)) if len(evs) > 1 else 0.0
        output.append(
            {
                "strategy": strategy,
                "seeds": len(group),
                "rounds": rounds,
                "profit_units": profit,
                "initial_bet_units": initial,
                "final_wager_units": final,
                "ev_units_per_round": mean_ev,
                "seed_ev_sd": seed_sd,
                "seed_ev_se95": 1.96 * seed_sd / math.sqrt(len(evs)) if evs else 0.0,
                "ev_per_initial_bet_pct": 100.0 * profit / initial,
                "ev_per_total_action_pct": 100.0 * profit / final,
                "avg_initial_bet": initial / rounds,
                "avg_final_wager": final / rounds,
            }
        )
    return output


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    rows = []
    for index in range(args.seeds):
        seed = args.seed_start + index
        for strategy in ("basic", "tested-deviations"):
            print(f"{strategy} seed {seed} ({args.rounds_per_seed:,} rounds)", flush=True)
            rows.append(row_for(strategy, seed, args))

    out = Path(args.out)
    write_csv(out, rows)
    summary = aggregate(rows)
    summary_path = out.with_name(out.stem + "_summary.csv")
    write_csv(summary_path, summary)

    print()
    print("Summary")
    for row in summary:
        print(
            f"  {row['strategy']:>17}: EV/round {row['ev_units_per_round']:.6f}, "
            f"EV/bet {row['ev_per_initial_bet_pct']:.4f}%, "
            f"avg bet {row['avg_initial_bet']:.4f}, 95% seed SE {row['seed_ev_se95']:.6f}"
        )
    if len(summary) == 2:
        basic = next(row for row in summary if row["strategy"] == "basic")
        tested = next(row for row in summary if row["strategy"] == "tested-deviations")
        print(
            f"  delta tested-basic: {tested['ev_units_per_round'] - basic['ev_units_per_round']:.6f} units/round, "
            f"{tested['ev_per_initial_bet_pct'] - basic['ev_per_initial_bet_pct']:.4f} pct points EV/bet"
        )
    print()
    print(f"wrote {out}")
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
