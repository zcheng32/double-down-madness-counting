# Double Down Madness Blackjack Counting Research

Monte Carlo tools, early results, and a bankroll calculator for researching whether
Double Down Madness Blackjack can be beaten with card counting.

This project is a research notebook, not gambling advice. The results are
preliminary and should be independently checked before being treated as final.

## Current Findings

Under the current strict-Ace Version 1 model, the Monte Carlo evidence suggests
Double Down Madness is countable and may be beatable with a risk-controlled
true-count ramp.

The strongest evidence so far is:

- Hi-Lo true count has a strong relationship with player edge.
- Neutral and negative counts remain bad for the player.
- Positive counts, especially TC +2 and above, become strongly positive.
- A simple one-hand 1-2-4-8-16 ramp produces positive EV/hour in the current
  clean six-deck, cut-one-deck, two-player dataset.

Preview fixed-ramp results for six decks, cut one deck, two players, one hand
only, $10 unit size, and the following ramp:

| TC bucket | Bet |
|---:|---:|
| <= 0 | 1 unit |
| +1 | 2 units |
| +2 | 4 units |
| +3 | 8 units |
| >= +4 | 16 units |

| TC estimation | EV/hour | SD/hour | Avg initial bet | N0 rounds | RoR |
|---|---:|---:|---:|---:|---:|
| Full-deck round-up | $48.80 | $652.09 | $22.37 | 17,496 | 1.014% |
| Half-deck round-up | $54.60 | $714.33 | $24.09 | 16,773 | 1.384% |
| Exact decks remaining | $59.83 | $751.48 | $25.14 | 15,460 | 1.444% |

These are preliminary bucket-composed results, not casino-ready betting advice.
See `docs/ddm_beatability_evidence.md` for assumptions and limitations.

## Current Ruleset

The current model targets Double Down Madness Version 1:

- 6-deck shoe by default.
- Dealer hits soft 17.
- No split, no surrender.
- Dealer 22 pushes active main-game wagers.
- Strict first-card Ace rule: if the player's first card is an Ace, hit or double receives one card only.
- Version 1 blackjack pays suited BJ 2:1 and unsuited BJ 3:2.
- Push 22 side bet is not played.

## Storyline

This repository follows the research path below.

### 1. Wizard Basic Strategy And Rules Discussion

The starting point is the
[Wizard of Odds Double Down Madness page](https://wizardofodds.com/games/blackjack/double-down-madness/)
and its published basic strategy. The most important rule ambiguity is the
first-card Ace rule.

This project currently uses the stricter interpretation:

> If the player's first card is an Ace, the player receives only one additional
> card after either hit or double.

This differs from Wizard's published strategy note that says first-card Ace
should double except that Version 1 `A vs A` should hit. The project treats
that point as an open rules/strategy question:

- If only an Ace double is restricted to one card, `A vs A` hit may be correct.
- If any action after a first-card Ace receives only one card, `A vs A` hit loses
  its continuing-action value, and our simulations support double instead.

Under the current strict-Ace model, Version 1 `A vs A` is modeled as double, not
hit.

The first-pass deviation scan supports that choice. With 50,000 simulated
rounds per action per true-count bucket, double beat hit for `A vs A` across the
tested range:

| TC | Double EV | Hit EV | Double edge | Combined 95% CI |
|---:|---:|---:|---:|---:|
| -3 | 0.35136 | 0.17502 | 0.17634 | 0.02290 |
| 0 | 0.50698 | 0.24855 | 0.25843 | 0.02297 |
| +3 | 0.66196 | 0.33153 | 0.33043 | 0.02305 |
| +6 | 0.78450 | 0.38652 | 0.39798 | 0.02297 |

Full table: `results/deviation/deviation_batch_summary.md`.

### 2. House Edge Replication

Before studying counting, the simulator is checked against published or
expected house-edge behavior. The goal is not just to get a number, but to make
sure the dealing order, blackjack payouts, Dealer 22 push, H17 behavior, cut
card handling, and Ace handling are all explicit.

Relevant files:

- `src/ddm_madness_counter_sim.py`
- `results/bankroll/tc_modes/clean_6d_cut1_2p_20m/`

### 3. Counting EV Results

After the base game is modeled, the next question is whether Hi-Lo true count
correlates with player edge strongly enough to support a bet ramp.

The current bankroll calculator and simulation tools estimate:

- EV by true-count bucket.
- EV per round.
- EV per initial bet.
- EV per total action.
- Standard deviation.
- Risk-of-ruin approximation.

Relevant files:

- `src/ddm_bankroll_calculator.py`
- `src/ddm_run_scenario_grid.py`
- `web/index.html`

### 4. True Count Estimation Impact

A real player does not know exact fractional decks remaining. The project now
uses three player-facing true-count modes, all integer-truncated toward zero:

- `exact`: exact decks remaining, then truncate the true count.
- `half`: remaining decks rounded up to the next half deck, then truncate the true count.
- `full`: remaining decks rounded up to the next full deck, then truncate the true count.

Example: if 3.25 decks remain and RC is +9, `exact`, `half`, and `full` all
produce TC +2. If RC is +13, `exact` produces +4, while `half` and `full`
produce +3 because they divide by 3.5 and 4.0 decks respectively.

Earlier deck-estimation datasets were removed from the calculator presentation.
Publication-grade comparisons should use datasets rerun under the current
`exact/half/full` definitions.

Relevant file:

- `docs/ddm_tc_rounding_audit.md`
- `docs/ddm_penetration_clean_2p_20m.md`

### 5. Deviation Findings

Early Monte Carlo scans suggest Double Down Madness does not copy ordinary
blackjack index numbers directly. Hitting often remains better longer on stiff
hands, likely because Dealer 22 pushes standing hands and hitting can still lead
to future profitable double opportunities.

Current focused findings:

- `16 vs 10`: stand appears much later than ordinary blackjack, around TC +6/+7.
- `12 vs 3`: stand around TC +4.
- `12 vs 4`: stand around TC +2.
- `13 vs 2`: stand around TC +4.
- single-card `8 vs 4`: hit at TC 0 and below; double around TC +3.

The current tested-deviation strategy improved a 50M-round-per-strategy
full-shoe comparison by about `0.0029` units/round, or `0.116` percentage points
of EV per initial bet, under the included 1-2-4-8-12-16 ramp. This is promising
but still preliminary.

Relevant files:

- `src/ddm_deviation_scan.py`
- `src/ddm_deviation_batch.py`
- `src/ddm_deviation_focus.py`
- `src/ddm_strategy_compare.py`
- `docs/ddm_deviation_research_notes.md`
- `docs/ddm_strategy_compare_notes.md`
- `results/deviation/deviation_batch_summary.md`
- `results/deviation/deviation_focus_summary.md`

### 6. Bankroll Calculator

The static calculator estimates the value and risk of custom bet ramps:

- Bankroll.
- Bets by true count.
- Penetration.
- Number of players.
- One-hand vs two-hand thresholds.
- EV/hour.
- SD/hour.
- Risk of ruin.

Local file:

- `web/index.html`

GitHub Pages file:

- `docs/index.html`

### 7. Beatability Evidence

The current DDM-only beatability argument is summarized in:

- `docs/ddm_beatability_evidence.md`

This page focuses on whether DDM itself can be beaten under the modeled rules.
It does not require a comparison to ordinary blackjack.

## What Is Included

- `src/ddm_madness_counter_sim.py`  
  Core Double Down Madness simulator and basic strategy implementation.

- `src/ddm_bankroll_calculator.py`  
  True-count bucket simulator and bankroll/ramp calculator.

- `src/ddm_run_scenario_grid.py`  
  Batch runner for penetration/player/TC-estimation grids.

- `src/ddm_deviation_scan.py`  
  Action-EV scanner for count-conditioned deviation research.

- `src/ddm_deviation_batch.py` and `src/ddm_deviation_focus.py`  
  Batch runners for first-pass and focused deviation scans.

- `src/ddm_strategy_compare.py`  
  Full-shoe comparison of basic strategy vs the current tested-deviation strategy.

- `src/ddm_tc_mode_paired_compare.py`  
  Same-shoe paired comparison of `exact`, `half`, and `full` TC estimation modes.

- `src/ddm_risk_normalized_compare.py`  
  Same-ramp comparison after scaling to equal average bet or equal SD/round.

- `web/index.html`  
  Static bankroll calculator UI.

- `docs/index.html`
  GitHub Pages copy of the calculator.

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
  --tc-deck-estimate exact \
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

Compare basic strategy against the current tested-deviation strategy:

```bash
python3 src/ddm_strategy_compare.py \
  --rounds-per-seed 2000000 \
  --seeds 5 \
  --out results/deviation/strategy_compare_local.csv \
  --ramp=-99:1,1:2,2:4,3:8,4:12,5:16
```

Open the calculator locally:

```bash
open web/index.html
```

## Reproducibility

The current scripts use Python standard library only. Simulations are
seed-controlled, but Monte Carlo error remains material, especially in high
true-count tails.

For publication-quality claims, include:

- Ruleset.
- TC estimation mode.
- Penetration.
- Rounds per scenario.
- Random seed range.
- Confidence interval or standard error.
- Whether results are bucket-composed or directly simulated with the full ramp.
