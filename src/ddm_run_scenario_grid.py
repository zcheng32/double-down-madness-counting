#!/usr/bin/env python3
"""Batch runner for Double Down Madness scenario bucket data.

This script runs the existing bankroll simulator across a grid of table
conditions and writes one bucket CSV per scenario. By default it prints the
commands without running them; pass --execute to actually run the grid.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_CUT_DECKS = "0.5,0.75,1,1.25,1.5,1.75,2,2.25,2.5"
DEFAULT_PLAYERS = "1,3,5"


@dataclass(frozen=True)
class Scenario:
    decks: int
    cut_decks: float
    players: int
    user_spots: int
    seed: int
    rounds: int
    output: str
    tc_deck_estimate: str = "exact"
    dealer_completes_hand: bool = False

    @property
    def other_spots(self) -> int:
        return max(0, self.players - 1)

    @property
    def penetration(self) -> float:
        return 1.0 - self.cut_decks / self.decks

    @property
    def cut_cards(self) -> int:
        return round(self.cut_decks * 52)

    @property
    def dealt_decks(self) -> float:
        return self.decks - self.cut_decks

    @property
    def label(self) -> str:
        return (
            f"{self.decks}D, cut {self.cut_decks:g} decks"
            f" ({self.cut_cards} cards, ~{100 * self.penetration:.1f}%),"
            f" {self.players} players, user {self.user_spots} spot(s)"
            f", tc {self.tc_deck_estimate}"
        )


def parse_csv_numbers(text: str, cast) -> list:
    return [cast(item.strip()) for item in text.split(",") if item.strip()]


def tag_float(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", "p")


def scenario_output_name(scenario: Scenario, suffix: str) -> str:
    millions = scenario.rounds / 1_000_000
    if millions.is_integer():
        round_tag = f"{int(millions)}m"
    else:
        round_tag = f"{scenario.rounds}"
    return (
        f"ddm_scenario_d{scenario.decks}_cut{tag_float(scenario.cut_decks)}"
        f"_u{scenario.user_spots}_o{scenario.other_spots}_{round_tag}{suffix}.csv"
    )


def build_scenarios(args: argparse.Namespace) -> list[Scenario]:
    decks_values = parse_csv_numbers(args.decks, int)
    cut_values = parse_csv_numbers(args.cut_decks, float)
    player_values = parse_csv_numbers(args.players, int)
    spot_values = [1, 2] if args.spots == "both" else [int(args.spots)]

    scenarios = []
    seed = args.seed_base
    for decks in decks_values:
        for cut_decks in cut_values:
            if cut_decks >= decks:
                continue
            for players in player_values:
                for user_spots in spot_values:
                    scenario = Scenario(
                        decks=decks,
                        cut_decks=cut_decks,
                        players=players,
                        user_spots=user_spots,
                        seed=seed,
                        rounds=args.rounds,
                        output="",
                        tc_deck_estimate=args.tc_deck_estimate,
                        dealer_completes_hand=args.dealer_completes_hand,
                    )
                    output = scenario_output_name(scenario, args.suffix)
                    scenarios.append(
                        Scenario(
                            decks=scenario.decks,
                            cut_decks=scenario.cut_decks,
                            players=scenario.players,
                            user_spots=scenario.user_spots,
                            seed=scenario.seed,
                            rounds=scenario.rounds,
                            output=str(Path(args.output_dir) / output),
                            tc_deck_estimate=scenario.tc_deck_estimate,
                            dealer_completes_hand=scenario.dealer_completes_hand,
                        )
                    )
                    seed += 1
    return scenarios


def command_for(scenario: Scenario) -> list[str]:
    cmd = [
        sys.executable,
        "outputs/ddm_bankroll_calculator.py",
        "--rounds",
        str(scenario.rounds),
        "--version",
        "v1",
        "--seed",
        str(scenario.seed),
        "--decks",
        str(scenario.decks),
        "--penetration",
        f"{scenario.penetration:.8f}",
        "--ramp=-99:1",
        "--ace-one-card-rule",
        "any",
        "--tc-deck-estimate",
        scenario.tc_deck_estimate,
        "--user-spots",
        str(scenario.user_spots),
        "--other-spots",
        str(scenario.other_spots),
        "--bucket-csv",
        scenario.output,
    ]
    if scenario.dealer_completes_hand:
        cmd.append("--dealer-completes-hand")
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=1_000_000)
    parser.add_argument("--decks", default="6", help="comma list, e.g. 6 or 6,8")
    parser.add_argument("--cut-decks", default=DEFAULT_CUT_DECKS)
    parser.add_argument("--players", default=DEFAULT_PLAYERS, help="total players at table, including you")
    parser.add_argument("--spots", choices=["1", "2", "both"], default="both")
    parser.add_argument("--seed-base", type=int, default=8000)
    parser.add_argument("--output-dir", default="outputs/scenario_grid")
    parser.add_argument("--suffix", default="")
    parser.add_argument("--tc-deck-estimate", choices=["exact", "half", "full"], default="exact")
    parser.add_argument("--dealer-completes-hand", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--manifest", default="")
    parser.add_argument("--task-index", type=int, default=0, help="1-based scenario index for cluster array jobs")
    parser.add_argument("--print-count", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scenarios = build_scenarios(args)

    if args.print_count:
        print(len(scenarios))
        return 0

    print(f"Scenarios: {len(scenarios)}")
    print(f"Rounds each: {args.rounds:,}")
    print(f"Total simulated table rounds if executed: {len(scenarios) * args.rounds:,}")
    print()

    manifest_rows = []
    indexed_scenarios = list(enumerate(scenarios, start=1))
    if args.task_index:
        if args.task_index < 1 or args.task_index > len(scenarios):
            raise SystemExit(f"--task-index must be 1..{len(scenarios)}")
        indexed_scenarios = [indexed_scenarios[args.task_index - 1]]

    for i, scenario in indexed_scenarios:
        manifest_rows.append({**asdict(scenario), "penetration": scenario.penetration, "label": scenario.label})
        if args.skip_existing and Path(scenario.output).exists():
            print(f"[{i}/{len(scenarios)}] skip existing {scenario.output}")
            continue
        cmd = command_for(scenario)
        print(f"[{i}/{len(scenarios)}] {scenario.label}")
        print("  " + " ".join(cmd))
        if args.execute:
            subprocess.run(cmd, check=True)

    manifest_path = args.manifest or str(output_dir / "manifest.json")
    with Path(manifest_path).open("w") as f:
        json.dump(manifest_rows, f, indent=2)
    print()
    print(f"wrote manifest: {manifest_path}")
    if not args.execute:
        print("dry run only; pass --execute to run these simulations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
