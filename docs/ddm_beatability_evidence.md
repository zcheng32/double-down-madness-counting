# Double Down Madness Beatability Evidence

This note summarizes the current evidence that Double Down Madness Version 1
may be beatable with card counting under the model used in this repository.

The claim is intentionally narrow:

- Version 1 only.
- Six-deck shoe.
- Dealer hits soft 17.
- No split and no surrender.
- Dealer 22 pushes active main-game wagers.
- Strict first-card Ace rule: a first-card Ace receives only one additional
  card after either hit or double.
- Push 22 side bet is not played.
- Hi-Lo count with true-count betting.

This is not a final mathematical proof. It is Monte Carlo evidence and a
reproducible research path.

## Why The Game Appears Countable

The key result is that player edge rises strongly with true count. Off the top,
the game has a house edge. At positive counts, especially TC +2 and above, the
simulated player edge becomes positive enough to support a bet ramp.

For the clean six-deck, cut-one-deck, two-player dataset using full-deck
round-up true-count estimation, the simulated DDM edge by bucket includes:

| TC bucket | Edge per initial bet | Frequency |
|---:|---:|---:|
| 0 | -0.908% | 43.086% |
| +1 | +1.069% | 12.760% |
| +2 | +4.548% | 7.001% |
| +3 | +7.695% | 3.829% |
| +4 | +10.637% | 2.070% |
| +5 | +12.897% | 1.089% |
| +6 | +16.576% | 0.558% |
| +7 | +20.305% | 0.269% |
| >= +8 | +24.392% | 0.221% |

The practical interpretation is simple: the game is poor at neutral or negative
counts, but high counts are valuable enough that a player who can sit out or bet
very small in bad buckets and press in good buckets can create a positive EV
profile.

## Risk-Constrained Ramp Preview

The current optimization script solves for a monotone true-count ramp under a
risk-of-ruin target. The preview below uses:

- Bankroll: $20,000.
- Target risk of ruin: about 1%.
- Two hands from TC +2.
- Maximum bet per spot: $500.
- Negative-EV buckets capped at $0.
- Bets rounded to $5.
- 3 shoes/hour speed model.
- Six decks, cut one deck, two players.

| TC estimation | EV/hour | SD/hour | Avg initial bet | N0 rounds | RoR |
|---|---:|---:|---:|---:|---:|
| Full-deck round-up | $145.90 | $1,124.27 | $33.14 | 5,819 | 0.988% |
| Half-deck round-up | $146.05 | $1,123.83 | $32.53 | 5,803 | 0.980% |
| Exact decks remaining | $147.48 | $1,109.30 | $31.26 | 5,544 | 0.828% |

These numbers are not presented as final casino-ready betting advice. They show
that, under the model and constraints above, the optimizer can find positive-EV
ramps with controlled risk.

## Example Full-Deck Round-Up Ramp

This is the optimized full-deck round-up ramp from the preview run.

| TC bucket | Bet / spot | Spots | Simulated edge |
|---:|---:|---:|---:|
| <= -5 | $0 | 1 | -10.763% |
| -4 | $0 | 1 | -7.258% |
| -3 | $0 | 1 | -5.611% |
| -2 | $0 | 1 | -4.030% |
| -1 | $0 | 1 | -2.765% |
| 0 | $0 | 1 | -0.908% |
| +1 | $35 | 1 | +1.069% |
| +2 | $55 | 2 | +4.548% |
| +3 | $95 | 2 | +7.695% |
| +4 | $130 | 2 | +10.637% |
| +5 | $160 | 2 | +12.897% |
| +6 | $200 | 2 | +16.576% |
| +7 | $245 | 2 | +20.305% |
| >= +8 | $290 | 2 | +24.392% |

## Why This Does Not Contradict The House Edge

The off-the-top house edge answers the flat-bet question:

> What happens if the player plays every round with the same bet?

Counting answers a different question:

> Does the remaining shoe composition create buckets where the player has a
> positive enough edge to bet more?

Double Down Madness appears to have a worse neutral game but a steep true-count
response. The high-count value is likely amplified by repeated double-down
opportunities and blackjack payouts on the current wager. This makes the game
more volatile, but it also gives the count more leverage.

## Limitations

- The optimized ramps are bucket-composed from simulations, not yet direct
  end-to-end trip simulations.
- The risk-of-ruin estimate uses a diffusion approximation.
- High-count buckets are rare and need very large samples for publication-grade
  precision.
- The first-card Ace rule remains an important real-world rules question.
- Casino speed, table crowding, heat, and the ability to wong out are practical
  constraints not fully modeled here.

## Reproducibility

The optimization script is:

- `src/optimize_tc_ramp.py`

The included preview outputs are:

- `results/optimized_ramps/ddm_full_bankroll20k_ror1_max500.csv`
- `results/optimized_ramps/ddm_half_bankroll20k_ror1_max500.csv`
- `results/optimized_ramps/ddm_exact_bankroll20k_ror1_max500.csv`

The underlying clean penetration dataset is documented in:

- `docs/ddm_penetration_clean_2p_20m.md`
