# Deviation Research Plan

## Goal

Find count-conditioned deviations for Double Down Madness Blackjack under Version 1 strict-Ace rules.

The first objective is not to publish a final index table. The first objective is to build a repeatable pipeline that can:

1. Reproduce off-the-top basic strategy decisions.
2. Compare H/S/D action EV at specific true-count buckets.
3. Identify candidate deviations with meaningful EV gain.
4. Validate high-value deviations with larger samples or exact combinatorial methods.

## Why Ordinary Blackjack Indexes Are Only Candidates

Ordinary blackjack indexes are useful as a candidate list, but Double Down Madness changes the EV surface:

- Dealer 22 pushes active main wagers, reducing the value of standing and waiting for dealer busts.
- Players may hit after doubling and may double after later cards.
- First-card Ace handling is special under the strict-Ace interpretation.
- Blackjack payouts differ by suited/unsuited Version 1 rules.

Therefore every ordinary blackjack deviation must be recalculated.

## Initial Candidate List

Hard totals:

- 16 vs 10
- 16 vs A
- 15 vs 10
- 12 vs 2
- 12 vs 3
- 12 vs 4
- 10 vs 10
- 10 vs A
- 9 vs 2
- 9 vs 7
- 8 vs 6
- 8 vs 7

DDM-specific starts:

- First-card 10 vs all dealer upcards
- First-card Ace vs all dealer upcards
- 11 vs A
- Soft 18 vs 9/10/A

## Current Scanner

`src/ddm_deviation_scan.py` estimates action EV for a fixed state:

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

It forces the first action and then returns to DDM basic strategy for subsequent decisions.

## Early Observation

The preliminary `T,6 vs 10` scan did not reproduce the ordinary blackjack `stand at TC 0+` behavior. In DDM, hitting stayed competitive through TC +2 in the initial scan.

This is plausible because:

- Standing loses value when dealer 22 pushes instead of paying.
- Hitting can lead to future double opportunities.

## Next Engineering Step

Improve condition sampling and add a batch scanner:

- Cache conditioned shoe states per true-count bucket.
- Run multiple candidate hands from the same sampled states.
- Report action EV, confidence interval, and EV gain over basic strategy.
- Add a filter for deviations where EV gain exceeds sampling noise.

## Next Math Step

For final publication, replace or supplement Monte Carlo with a composition-dependent recursive EV solver for the most important states.

