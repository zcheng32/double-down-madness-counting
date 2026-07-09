#!/usr/bin/env python3
"""Batch runner for first-pass Double Down Madness deviation scans."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

from ddm_deviation_scan import scan


CANDIDATES = [
    # Hard hit/stand pivots.
    ("T,6", "T", "H,S", "hard 16 vs 10"),
    ("T,5", "T", "H,S", "hard 15 vs 10"),
    ("T,6", "9", "H,S", "hard 16 vs 9"),
    ("T,5", "A", "H,S", "hard 15 vs A"),
    ("T,2", "2", "H,S", "hard 12 vs 2"),
    ("T,2", "3", "H,S", "hard 12 vs 3"),
    ("T,2", "4", "H,S", "hard 12 vs 4"),
    ("T,3", "2", "H,S", "hard 13 vs 2"),
    # Hard hit/double pivots that may matter more in DDM.
    ("9", "2", "H,D", "single-card 9 vs 2"),
    ("9", "7", "H,D", "single-card 9 vs 7"),
    ("9", "8", "H,D", "single-card 9 vs 8"),
    ("T", "T", "H,D", "single-card 10 vs 10"),
    ("T", "A", "H,D", "single-card 10 vs A"),
    ("8", "4", "H,D", "single-card 8 vs 4"),
    ("8", "7", "H,D", "single-card 8 vs 7"),
    # Soft totals and first-card Ace edge cases.
    ("A,7", "9", "H,S,D", "soft 18 vs 9"),
    ("A,7", "T", "H,S,D", "soft 18 vs 10"),
    ("A,7", "A", "H,S,D", "soft 18 vs A"),
    ("A", "A", "H,D", "single-card A vs A"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=50_000)
    parser.add_argument("--true-counts", default="-3,-2,-1,0,1,2,3,4,5,6")
    parser.add_argument("--decks-remaining", type=float, default=4.5)
    parser.add_argument("--seed", type=int, default=20260708)
    parser.add_argument("--out-dir", default="outputs/deviation_batch_v1")
    parser.add_argument("--limit", type=int, default=0, help="optional first N candidates for smoke tests")
    return parser.parse_args()


def make_namespace(args: argparse.Namespace, player: str, dealer: str, actions: str, seed: int) -> argparse.Namespace:
    return argparse.Namespace(
        player=player,
        dealer=dealer,
        true_counts=args.true_counts,
        decks_remaining=args.decks_remaining,
        rounds=args.rounds,
        seed=seed,
        actions=actions,
        version="v1",
        decks=6,
        cut_decks=1.5,
        ace_one_card_rule="any",
        dealer_completes_hand=False,
        conditioning="constructed",
        max_condition_attempts=100_000,
        csv="",
    )


def tc_sort_key(text: str) -> float:
    if text == "<=-5":
        return -99
    if text == ">=8":
        return 99
    return float(text)


def summarize(rows: list[dict[str, object]], label: str) -> list[dict[str, object]]:
    by_tc: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_tc.setdefault(str(row["tc"]), []).append(row)
    summary = []
    for tc in sorted(by_tc, key=tc_sort_key):
        tc_rows = by_tc[tc]
        best = max(tc_rows, key=lambda row: float(row["ev"]))
        second = sorted(tc_rows, key=lambda row: float(row["ev"]), reverse=True)[1]
        combined_ci = math.sqrt(float(best["ci95"]) ** 2 + float(second["ci95"]) ** 2)
        summary.append(
            {
                "label": label,
                "player": best["player"],
                "dealer": best["dealer"],
                "tc": tc,
                "best_action": best["action"],
                "best_ev": best["ev"],
                "runner_up": second["action"],
                "runner_up_ev": second["ev"],
                "edge": float(best["ev"]) - float(second["ev"]),
                "combined_ci95": combined_ci,
                "clear": abs(float(best["ev"]) - float(second["ev"])) > combined_ci,
            }
        )
    return summary


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, summaries: list[dict[str, object]], rounds: int, true_counts: str) -> None:
    lines = [
        "# DDM Deviation Batch Scan",
        "",
        f"- Rounds per action per TC: `{rounds:,}`",
        f"- True counts: `{true_counts}`",
        "- Rules: Version 1, six decks, strict first-card Ace rule, H17, no Push 22 side bet.",
        "- `clear` means the best action beat the runner-up by more than the combined 95% Monte Carlo interval.",
        "",
        "| Candidate | TC | Best | Runner-up | Edge | Combined 95% CI | Clear |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            "| {label} | {tc} | {best_action} | {runner_up} | {edge:.5f} | {combined_ci95:.5f} | {clear} |".format(
                **row
            )
        )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = CANDIDATES[: args.limit] if args.limit else CANDIDATES

    all_rows: list[dict[str, object]] = []
    all_summaries: list[dict[str, object]] = []
    for index, (player, dealer, actions, label) in enumerate(candidates, start=1):
        print(f"[{index}/{len(candidates)}] {label}: player {player} vs dealer {dealer}, actions {actions}", flush=True)
        rows = scan(make_namespace(args, player, dealer, actions, args.seed + index * 997))
        for row in rows:
            row["label"] = label
        all_rows.extend(rows)
        all_summaries.extend(summarize(rows, label))
        write_csv(out_dir / "deviation_batch_rows_partial.csv", all_rows)
        write_csv(out_dir / "deviation_batch_summary_partial.csv", all_summaries)

    write_csv(out_dir / "deviation_batch_rows.csv", all_rows)
    write_csv(out_dir / "deviation_batch_summary.csv", all_summaries)
    write_markdown(out_dir / "deviation_batch_summary.md", all_summaries, args.rounds, args.true_counts)
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
