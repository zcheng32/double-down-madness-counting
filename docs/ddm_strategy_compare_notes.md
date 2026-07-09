# DDM Basic vs Tested Deviations: Full-Shoe EV Impact

Date: 2026-07-08

Rules:
- Version 1.
- Six decks.
- Cut card: 1 deck cut off, about 83.33% penetration.
- Strict first-card Ace rule: first-card Ace receives one card only after hit or double.
- H17.
- No splits, no surrender.
- Dealer 22 pushes active main-game wagers.
- Push 22 side bet not played.
- True count mode: exact integer true count.

Bet ramp used:

| TC threshold | Bet units |
|---:|---:|
| -99 | 1 |
| +1 | 2 |
| +2 | 4 |
| +3 | 8 |
| +4 | 12 |
| +5 | 16 |

Tested deviations included:

| Hand | Dealer | Deviation |
|---|---:|---|
| hard 16 | 10 | stand at TC >= +7 |
| hard 12 | 3 | stand at TC >= +4 |
| hard 12 | 4 | stand at TC >= +2 |
| hard 13 | 2 | stand at TC >= +4 |
| single-card 8 | 4 | hit at TC <= 0; double at TC >= +3 |

## 10M Rounds Per Strategy

This was the first quick full-shoe comparison.

| Strategy | Rounds | EV / round | EV / initial bet | Avg initial bet | Avg final wager |
|---|---:|---:|---:|---:|---:|
| Basic | 10,000,000 | 0.0551669 | 2.2735% | 2.4265 | 3.8232 |
| Tested deviations | 10,000,000 | 0.0587291 | 2.4170% | 2.4299 | 3.8367 |

Delta:
- +0.003562 units/round.
- +0.1435 percentage points EV / initial bet.

## 50M Rounds Per Strategy

This is the stronger current result.

| Strategy | Rounds | EV / round | EV / initial bet | EV / total action | Avg initial bet | Avg final wager |
|---|---:|---:|---:|---:|---:|---:|
| Basic | 50,000,000 | 0.0556677 | 2.2978% | 1.4581% | 2.4227 | 3.8177 |
| Tested deviations | 50,000,000 | 0.0585596 | 2.4138% | 1.5287% | 2.4260 | 3.8306 |

Delta:
- +0.002892 units/round.
- +0.1160 percentage points EV / initial bet.
- +0.0706 percentage points EV / total action.

All five paired seed comparisons were positive for the tested-deviation strategy.

## Interpretation

The early tested deviations appear to improve full-shoe EV, but the effect is modest. That makes sense:

- Only five deviations are included.
- Most deviations trigger in relatively narrow TC/hand states.
- Some improvements reduce bad doubles rather than creating large new win rates.

This is enough to justify continuing deviation research. It is not enough to call the index table final.

## Next Step

The next improvement should be a trigger-frequency and paired-action EV report:

1. Count how often each tested deviation actually triggers in full-shoe play.
2. Estimate each deviation's isolated EV contribution.
3. Keep only deviations that produce meaningful full-game value.
4. Add the result to the calculator as `Basic` vs `Basic + tested deviations`.

