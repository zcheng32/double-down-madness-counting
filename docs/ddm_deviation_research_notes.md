# Double Down Madness Deviation Research Notes

Date: 2026-07-08

Rules used:
- Version 1 blackjack pays: suited BJ 2:1, unsuited BJ 3:2.
- Six decks, H17, no splits, no surrender.
- Strict first-card Ace rule: first-card Ace gets one card only after either hit or double.
- Dealer 22 pushes active main-game wagers.
- Push 22 side bet is not played.

Simulation setup:
- First pass: 19 candidate decisions, 50,000 rounds per action per true count.
- Focus pass: likely index areas, 200,000 rounds per action per true count.
- True count conditioning: exact integer true count at about 4.5 decks remaining.
- These are exploratory Monte Carlo results, not final publication-grade indices.

## Strong Early Findings

### Hard 16 vs dealer 10

Ordinary blackjack often uses a much lower stand index, but DDM shifts this strongly upward.

Focused scan:

| TC | Best | Edge over runner-up | Combined 95% CI |
|---:|---:|---:|---:|
| +4 | Hit | 0.00769 | 0.00465 |
| +5 | Stand | 0.00035 | 0.00460 |
| +6 | Stand | 0.00375 | 0.00458 |
| +7 | Stand | 0.00984 | 0.00453 |

Working conclusion: stand is not clearly justified until about TC +6/+7. TC +5 and +6 need larger samples.

### Hard 12 vs dealer 3

Focused scan:

| TC | Best | Edge over runner-up | Combined 95% CI |
|---:|---:|---:|---:|
| +1 | Hit | 0.03806 | 0.00552 |
| +2 | Hit | 0.01754 | 0.00554 |
| +3 | Hit | 0.00491 | 0.00555 |
| +4 | Stand | 0.00672 | 0.00555 |
| +5 | Stand | 0.02413 | 0.00557 |

Working conclusion: stand around TC +4. TC +3/+4 is the transition zone.

### Hard 12 vs dealer 4

Focused scan:

| TC | Best | Edge over runner-up | Combined 95% CI |
|---:|---:|---:|---:|
| 0 | Hit | 0.02430 | 0.00558 |
| +1 | Hit | 0.00675 | 0.00561 |
| +2 | Stand | 0.01006 | 0.00562 |
| +3 | Stand | 0.02044 | 0.00563 |

Working conclusion: stand at about TC +2.

### Hard 13 vs dealer 2

Focused scan:

| TC | Best | Edge over runner-up | Combined 95% CI |
|---:|---:|---:|---:|
| +2 | Hit | 0.01082 | 0.00508 |
| +3 | Stand | 0.00313 | 0.00506 |
| +4 | Stand | 0.00706 | 0.00505 |
| +5 | Stand | 0.02613 | 0.00504 |

Working conclusion: stand around TC +4. TC +3/+4 is the transition zone.

### Single-card 8 vs dealer 4

This is a DDM-specific-looking result because the basic strategy says double.

Focused scan:

| TC | Best | Edge over runner-up | Combined 95% CI |
|---:|---:|---:|---:|
| -1 | Hit | 0.05077 | 0.01090 |
| 0 | Hit | 0.03564 | 0.01084 |
| +1 | Hit | 0.00243 | 0.01078 |
| +2 | Double | 0.00651 | 0.01071 |
| +3 | Double | 0.01591 | 0.01067 |

Working conclusion: hit at TC 0 and below; double around TC +3. TC +1/+2 is the transition zone.

## Mostly Confirmed Basic Strategy Points

### Single-card 9 vs dealer 2

The user flagged this as a plausible deviation. First pass did not support double through TC +6. Hit remained best.

Working conclusion: not a priority unless we later test very high TC or a different remaining-decks point.

### Single-card 9 vs dealer 7/8

Double was clearly best across the tested range.

Working conclusion: basic strategy double appears stable.

### Single-card 10 vs dealer 10

Focused low-count scan showed double is still best from TC -4 through 0.

Working conclusion: first-card 10 always double is strongly supported for dealer 10.

### Single-card 10 vs dealer Ace

Focused low-count scan:
- TC -4 was effectively unclear: hit slightly ahead, but far inside the confidence interval.
- TC -3 and above favored double.

Working conclusion: first-card 10 always double is broadly supported. TC -4 vs Ace is too marginal to matter much for betting EV, but it can be retested later.

### Soft 18 vs dealer 9/10/A

Hit was clearly best across the tested range.

Working conclusion: no obvious soft 18 deviation in this first pass.

### Single-card Ace vs dealer Ace

Double was clearly best across the tested range under the strict Ace rule.

Working conclusion: this supports using double for Version 1 A vs A under the strict first-card Ace rule.

## Next Runs

Recommended next high-sample runs:

1. Hard 16 vs 10 at TC +5, +6, +7 with 1M+ rounds/action.
2. Hard 12 vs 3 at TC +3, +4 with 1M+ rounds/action.
3. Hard 13 vs 2 at TC +3, +4 with 1M+ rounds/action.
4. Single-card 8 vs 4 at TC +1, +2, +3 with 1M+ rounds/action.
5. Repeat the strongest findings at different decks remaining, such as 5.0, 4.0, 3.0, to test whether the index is stable through the shoe.

