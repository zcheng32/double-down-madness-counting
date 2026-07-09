#!/usr/bin/env python3
"""Focused higher-sample scans for likely DDM deviation index points."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from ddm_deviation_batch import summarize, write_csv, write_markdown
from ddm_deviation_scan import scan


FOCUS_CANDIDATES = [
    ("T,6", "T", "H,S", "4,5,6,7", "hard 16 vs 10"),
    ("T,2", "3", "H,S", "1,2,3,4,5", "hard 12 vs 3"),
    ("T,2", "4", "H,S", "0,1,2,3", "hard 12 vs 4"),
    ("T,3", "2", "H,S", "2,3,4,5", "hard 13 vs 2"),
    ("8", "4", "H,D", "-1,0,1,2,3", "single-card 8 vs 4"),
    ("T", "T", "H,D", "-4,-3,-2,-1,0", "single-card 10 vs 10 low TC"),
    ("T", "A", "H,D", "-4,-3,-2,-1,0", "single-card 10 vs A low TC"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=200_000)
    parser.add_argument("--decks-remaining", type=float, default=4.5)
    parser.add_argument("--seed", type=int, default=2026070802)
    parser.add_argument("--out-dir", default="outputs/deviation_focus_v1_200k")
    return parser.parse_args()


def make_namespace(args: argparse.Namespace, player: str, dealer: str, actions: str, true_counts: str, seed: int) -> argparse.Namespace:
    return argparse.Namespace(
        player=player,
        dealer=dealer,
        true_counts=true_counts,
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


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, object]] = []
    all_summaries: list[dict[str, object]] = []
    for index, (player, dealer, actions, true_counts, label) in enumerate(FOCUS_CANDIDATES, start=1):
        print(
            f"[{index}/{len(FOCUS_CANDIDATES)}] {label}: player {player} vs dealer {dealer}, "
            f"TC {true_counts}, actions {actions}",
            flush=True,
        )
        rows = scan(make_namespace(args, player, dealer, actions, true_counts, args.seed + index * 997))
        for row in rows:
            row["label"] = label
        all_rows.extend(rows)
        all_summaries.extend(summarize(rows, label))
        write_csv(out_dir / "deviation_focus_rows_partial.csv", all_rows)
        write_csv(out_dir / "deviation_focus_summary_partial.csv", all_summaries)

    write_csv(out_dir / "deviation_focus_rows.csv", all_rows)
    write_csv(out_dir / "deviation_focus_summary.csv", all_summaries)
    write_markdown(out_dir / "deviation_focus_summary.md", all_summaries, args.rounds, "candidate-specific")
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
