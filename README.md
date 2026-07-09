# Double Down Madness Blackjack Counting Research

Monte Carlo tools and early results for researching whether Double Down Madness Blackjack can be beaten with card counting.

The current model targets Version 1 rules:

- 6-deck shoe by default
- Dealer hits soft 17
- No split, no surrender
- Dealer 22 pushes active main-game wagers
- Strict first-card Ace rule: if the player's first card is an Ace, hit or double receives one card only
- Version 1 blackjack pays suited 2:1 and unsuited 3:2

This project is research-grade, not gambling advice. Results should be independently checked before being treated as final.

## What Is Included

- `src/ddm_madness_counter_sim.py`  
  Core Double Down Madness simulator and basic strategy implementation.

- `src/ddm_bankroll_calculator.py`  
  True-count bucket simulator and bankroll/ramp calculator.

- `src/ddm_run_scenario_grid.py`  
  Batch runner for penetration/player/TC-estimation grids.

- `src/ddm_deviation_scan.py`  
  Early action-EV scanner for count-conditioned deviation research.

- `src/ddm_deviation_batch.py` and `src/ddm_deviation_focus.py`  
  Batch runners for first-pass and focused deviation scans.

- `src/ddm_strategy_compare.py`  
  Full-shoe comparison of basic strategy vs the current tested-deviation strategy.

- `web/index.html`  
  Static bankroll calculator UI.

- `docs/ddm_deviation_research_notes.md`  
  Current deviation findings and next-run priorities.

- `docs/ddm_strategy_compare_notes.md`  
  Current full-shoe EV impact of adding the tested deviations.

- `docs/ddm_tc_rounding_audit.md`  
  Audit explaining floating exact TC vs integer TC comparisons.

- `results/`  
  Lightweight manifests and starter deviation CSVs. Large raw simulation outputs are intentionally excluded.

## Quick Start

Run a basic bankroll bucket simulation:

```bash
python3 src/ddm_bankroll_calculator.py \
  --rounds 1000000 \
  --version v1 \
  --decks 6 \
  --penetration 0.83333333 \
  --ace-one-card-rule any \
  --tc-deck-estimate exact-int \
  --bucket-csv results/sample_exact_int.csv
```

Run a deviation scan for `16 vs 10`:

```bash
python3 src/ddm_deviation_scan.py \
  --player T,6 \
  --dealer T \
  --true-counts=-1,0,1,2,3,4 \
  --rounds 10000 \
  --actions H,S \
  --decks-remaining 4.5 \
  --csv results/deviation/t6_vs_t.csv
```

Run the first-pass deviation batch:

```bash
python3 src/ddm_deviation_batch.py \
  --rounds 50000 \
  --out-dir results/deviation/batch_local
```

Run the focused higher-sample deviation batch:

```bash
python3 src/ddm_deviation_focus.py \
  --rounds 200000 \
  --out-dir results/deviation/focus_local
```

Compare basic strategy against the current tested-deviation strategy:

```bash
python3 src/ddm_strategy_compare.py \
  --rounds-per-seed 2000000 \
  --seeds 5 \
  --out results/deviation/strategy_compare_local.csv \
  --ramp=-99:1,1:2,2:4,3:8,4:12,5:16
```

Open the calculator:

```bash
open web/index.html
```

## TC Definitions

The project separates these modes:

- `Exact float (legacy)`: exact decks remaining, floating true count, then bucketed for reporting.
- `Exact int`: exact decks remaining, true count truncated toward zero before betting/bucketing.
- `1 deck int`: remaining decks rounded to the nearest full deck, then true count truncated toward zero.
- `0.5 deck int`: remaining decks rounded to the nearest half deck, then true count truncated toward zero.

For player-facing comparisons, use `Exact int`, `1 deck int`, and `0.5 deck int`.

## Early Deviation Note

Early Monte Carlo scans suggest Double Down Madness does not copy ordinary blackjack index numbers directly. In this game, hitting often remains better longer on stiff hands, likely because:

- Dealer 22 pushes instead of paying standing hands.
- After hitting, the player can still enter profitable future double opportunities.

Examples from the current focused scan:

- `16 vs 10`: stand appears much later than ordinary blackjack, around TC +6/+7.
- `12 vs 3`: stand around TC +4.
- `12 vs 4`: stand around TC +2.
- `13 vs 2`: stand around TC +4.
- single-card `8 vs 4`: hit at TC 0 and below; double around TC +3.

The current tested-deviation strategy improved a 50M-round-per-strategy full-shoe comparison by about `0.0029` units/round, or `0.116` percentage points of EV per initial bet, under the included 1-2-4-8-12-16 ramp. This is promising but still preliminary.

See `docs/ddm_deviation_research_notes.md` for the current notes and caveats.

## Reproducibility

The current scripts use Python standard library only. Simulations are seed-controlled, but Monte Carlo error remains material, especially in high true-count tails.

For publication-quality claims, include:

- ruleset
- TC estimation mode
- penetration
- rounds per scenario
- random seed range
- confidence interval or standard error
- whether results are bucket-composed or directly simulated with the full ramp
