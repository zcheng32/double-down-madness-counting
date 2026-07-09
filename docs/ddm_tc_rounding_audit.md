# DDM TC Rounding Audit

This audit separates legacy floating exact true count from integer-truncated playing true count.

Default calculator ramp used: $25 through TC +1, $100 at TC +2, $200 at TC +3, $300 at TC +4, $400 at TC +5 and above, with two hands from TC +2.

## Code Findings

- Legacy `exact` returns a floating true count and `tc_bucket()` floors it for bucket labels.
- Practical `1` and `0.5` estimate remaining decks and then use Python `int()`, truncating toward zero.
- New `exact-int` uses exact remaining decks but also truncates true count toward zero before betting/bucketing. This is the fairer comparison point for practical integer TC play.

## Calculator Comparison

| Cut cards | Mode | Rounds | EV/round | 95% CI | EV/hour | Avg bet | EV/avg bet |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 decks | Exact float legacy | 50,000,000 | $3.24 | ±$0.08 | $463.40 | $94.73 | 3.421% |
| 1 decks | Exact int | 20,000,000 | $3.15 | ±$0.12 | $450.24 | $94.62 | 3.328% |
| 1 decks | 1 deck int | 20,000,000 | $3.51 | ±$0.13 | $501.84 | $104.07 | 3.373% |
| 1 decks | 0.5 deck int | 5,000,000 | $3.48 | ±$0.25 | $497.79 | $101.63 | 3.426% |
| 1.25 decks | Exact float legacy | 50,000,000 | $2.71 | ±$0.07 | $367.46 | $88.78 | 3.057% |
| 1.25 decks | Exact int | 20,000,000 | $2.65 | ±$0.11 | $358.51 | $88.37 | 2.996% |
| 1.25 decks | 1 deck int | 20,000,000 | $2.95 | ±$0.12 | $399.91 | $96.91 | 3.047% |
| 1.25 decks | 0.5 deck int | 5,000,000 | $2.87 | ±$0.24 | $388.71 | $93.28 | 3.077% |
| 1.5 decks | Exact float legacy | 5,000,000 | $2.11 | ±$0.21 | $270.70 | $81.84 | 2.579% |
| 1.5 decks | Exact int | 20,000,000 | $2.34 | ±$0.11 | $300.62 | $81.93 | 2.860% |
| 1.5 decks | 1 deck int | 20,000,000 | $2.35 | ±$0.11 | $301.61 | $86.82 | 2.708% |
| 1.5 decks | 0.5 deck int | 5,000,000 | $2.30 | ±$0.22 | $295.08 | $87.15 | 2.639% |
| 1.75 decks | Exact float legacy | 5,000,000 | $1.70 | ±$0.20 | $206.27 | $76.10 | 2.236% |
| 1.75 decks | Exact int | 20,000,000 | $1.79 | ±$0.10 | $216.88 | $75.86 | 2.358% |
| 1.75 decks | 1 deck int | 20,000,000 | $1.98 | ±$0.11 | $239.62 | $82.32 | 2.401% |
| 1.75 decks | 0.5 deck int | 5,000,000 | $2.15 | ±$0.21 | $261.18 | $80.11 | 2.689% |
| 2 decks | Exact float legacy | 5,000,000 | $1.49 | ±$0.18 | $171.08 | $70.96 | 2.100% |
| 2 decks | Exact int | 20,000,000 | $1.57 | ±$0.09 | $180.69 | $70.48 | 2.234% |
| 2 decks | 1 deck int | 20,000,000 | $1.84 | ±$0.10 | $211.48 | $77.57 | 2.375% |
| 2 decks | 0.5 deck int | 5,000,000 | $1.65 | ±$0.19 | $189.87 | $75.36 | 2.195% |

## Why 1 Deck Can Appear Higher Than Exact Int

The calculator is applying one fixed ramp to different TC bucket definitions. A coarser bucket definition can produce a larger average bet under that same ramp. For cut 1 deck with the current default ramp, `Exact int` has EV/round about $3.15 with average bet $94.62, while `1 deck int` has EV/round about $3.51 with average bet $104.07. If the `1 deck int` ramp is scaled down to the same average bet as `Exact int`, its EV/round is about $3.19, only about $0.04 higher than `Exact int`, far inside the Monte Carlo uncertainty for this comparison.

So the current evidence does not show that estimating to 1 deck is truly stronger than exact integer TC. It shows that fixed bucket ramps must be compared either at equal average bet/risk or after separately optimizing each ramp.

## Interpretation

- EV/round can be higher for a coarser TC estimate because the same bucket ramp may create a larger average bet. Compare EV/avg bet too.
- The old Exact option was useful as a floating-TC diagnostic, but misleading as a player-facing integer TC comparison.
- For player-facing calculator work, compare `Exact int`, `1 deck int`, and `0.5 deck int`; treat `Exact float` as legacy/reference only.
