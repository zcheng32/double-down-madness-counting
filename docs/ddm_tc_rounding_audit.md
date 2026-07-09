# DDM TC Estimation Audit

This audit records an important correction to the true-count estimation modes.
The project now keeps only `exact`, `half`, and `full`, and all three modes use
integer truncation toward zero after the deck divisor is chosen.

The main calculator comparison below uses this ramp: no play at `<= -5`; $10
from TC -4 through TC 0; $25 at TC +1; $30 at TC +2; $50 at TC +3; $100 at
TC +4; $150 at TC +5; $200 at TC +6; $250 at TC +7 and above, with two hands
from TC +2.

## Code Findings

- `exact`: divide RC by exact decks remaining, then truncate toward zero.
- `half`: round decks remaining up to the next 0.5 deck, divide RC by that divisor, then truncate toward zero.
- `full`: round decks remaining up to the next 1.0 deck, divide RC by that divisor, then truncate toward zero.
- Example: if 3.25 decks remain, `half` uses 3.5 and `full` uses 4.0.

## Clean 2-Player 20M Rerun

The older cut-1, two-player calculator data was removed from the calculator
presentation and replaced with a clean rerun under the current `exact`, `half`,
and `full` definitions. Each mode uses 20M rounds for the one-spot bucket data
and 20M rounds for the two-spot support data.

Conditions:

- 6 decks.
- Cut 1 deck, about 83% penetration.
- 2 players at the table: the user plus one other basic-strategy player.
- Strict first-card Ace rule.
- Version 1 blackjack pays.
- Two hands from TC +2 in the calculator composition below.
- Ramp: no play at `<= -5`; $10 from TC -4 through TC 0; $25 at TC +1; $30 at
  TC +2; $50 at TC +3; $100 at TC +4; $150 at TC +5; $200 at TC +6; $250 at
  TC +7 and above.

| TC mode | Rounds | EV/round | 95% CI | Avg initial bet | EV/avg bet | SD/round |
|---|---:|---:|---:|---:|---:|---:|
| exact | 20,000,000 | $1.444 | +/-$0.053 | $37.53 | 3.846% | $120.64 |
| half | 20,000,000 | $1.214 | +/-$0.047 | $34.25 | 3.545% | $107.13 |
| full | 20,000,000 | $1.020 | +/-$0.040 | $30.30 | 3.367% | $92.35 |

## Same-Risk / Same-Bet Check

Because `exact`, `half`, and `full` do not place the same average bet under the
same displayed ramp, the project also compares them after scaling each ramp
shape to the same average initial bet or the same SD/round as `exact`.

This scaling does not optimize the ramp. It only answers: if we keep the same
ramp shape, is the `exact` advantage just coming from betting more or taking
more variance?

For the same 6D, cut-1, 2-player, 20M-round data above:

| Comparison | Mode | Scale | EV/round | SD/round | Avg initial bet | EV/avg bet | N0 rounds |
|---|---|---:|---:|---:|---:|---:|---:|
| raw | exact | 1.000 | $1.444 | $120.64 | $37.53 | 3.846% | 6,984 |
| raw | half | 1.000 | $1.214 | $107.13 | $34.25 | 3.545% | 7,786 |
| raw | full | 1.000 | $1.020 | $92.35 | $30.30 | 3.367% | 8,192 |
| equal avg bet | exact | 1.000 | $1.444 | $120.64 | $37.53 | 3.846% | 6,984 |
| equal avg bet | half | 1.096 | $1.331 | $117.41 | $37.53 | 3.545% | 7,786 |
| equal avg bet | full | 1.239 | $1.264 | $114.38 | $37.53 | 3.367% | 8,192 |
| equal SD | exact | 1.000 | $1.444 | $120.64 | $37.53 | 3.846% | 6,984 |
| equal SD | half | 1.126 | $1.367 | $120.64 | $38.56 | 3.545% | 7,786 |
| equal SD | full | 1.306 | $1.333 | $120.64 | $39.58 | 3.367% | 8,192 |

Interpretation: in this cut-1, 2-player dataset, `exact` remains ahead after
normalizing either average initial bet or per-round standard deviation. The
coarser modes are not merely lower-risk versions of the same edge; they lose
some betting information.

## Paired Same-Shoe Comparison

A separate paired-comparison script evaluates `exact`, `half`, and `full` from
the same pre-round shoe state. This greatly reduces noise when asking which TC
estimation mode performs better under the same ramp.

For 5M paired opportunities, 6 decks, cut 1 deck, heads-up opportunity sampling,
two hands from TC +2, and the same ramp:

| Mode | EV/round | 95% CI | Avg initial bet | EV/avg bet |
|---|---:|---:|---:|---:|
| exact | $1.459 | +/-$0.106 | $37.67 | 3.873% |
| half | $1.270 | +/-$0.094 | $34.47 | 3.684% |
| full | $1.038 | +/-$0.081 | $30.38 | 3.416% |

Paired differences:

| Difference | EV/round difference | 95% CI |
|---|---:|---:|
| half - exact | -$0.189 | +/-$0.022 |
| full - exact | -$0.421 | +/-$0.039 |

Interpretation: under this ramp, the coarser `half/full` estimates lower both
average bet and EV. Earlier observations where a coarser mode appeared better
were caused by a mix of old deck-estimation definitions, non-paired Monte Carlo
noise, and unequal sample sizes.

## Interpretation

- Current player-facing calculator work should compare only `exact`, `half`, and `full`.
- Cut-1, 2-player `exact/half/full` data has been rerun at equal 20M sample size.
- Additional penetration/player-count combinations should be rerun before being
  presented as publication-grade data.
- The first clean 2-player penetration extension is recorded in
  `docs/ddm_penetration_clean_2p_20m.md`.
