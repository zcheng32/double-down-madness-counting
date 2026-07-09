# DDM 2-Player Penetration Clean Run

This note records the clean 6-deck, 2-player penetration rerun completed after
the TC-estimation cleanup.

Conditions:

- Double Down Madness Version 1.
- Strict first-card Ace rule.
- 6 decks.
- 2 players at the table: the user plus one other basic-strategy player.
- Dealer hits soft 17.
- Dealer 22 pushes active main-game wagers.
- Push 22 side bet is not played.
- TC modes: `exact`, `half`, and `full`, all integer-truncated toward zero.
- 20M table rounds for each one-spot bucket file and 20M table rounds for each
  two-spot support file.
- Ramp: no play at `<= -5`; $10 from TC -4 through TC 0; $25 at TC +1; $30 at
  TC +2; $50 at TC +3; $100 at TC +4; $150 at TC +5; $200 at TC +6; $250 at
  TC +7 and above.
- Two hands from TC +2.

Raw files:

- `results/bankroll/tc_modes/clean_6d_pen_2p_20m/`
- `results/bankroll/tc_modes/risk_normalized_6d_2p_penetration_summary_20m.csv`

## Raw Calculator Composition

| Cut decks | TC mode | EV/round | 95% CI | SD/round | Avg initial bet | EV/avg bet | N0 rounds |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1.00 | exact | $1.444 | +/-$0.053 | $120.64 | $37.53 | 3.846% | 6,984 |
| 1.00 | half | $1.214 | +/-$0.047 | $107.13 | $34.25 | 3.545% | 7,786 |
| 1.00 | full | $1.020 | +/-$0.040 | $92.35 | $30.30 | 3.367% | 8,192 |
| 1.25 | exact | $1.176 | +/-$0.048 | $110.40 | $34.56 | 3.402% | 8,816 |
| 1.25 | half | $1.078 | +/-$0.044 | $100.87 | $32.35 | 3.332% | 8,760 |
| 1.25 | full | $0.925 | +/-$0.039 | $89.21 | $29.26 | 3.163% | 9,296 |
| 1.50 | exact | $0.968 | +/-$0.043 | $99.17 | $31.39 | 3.085% | 10,490 |
| 1.50 | half | $0.818 | +/-$0.039 | $89.44 | $29.33 | 2.790% | 11,949 |
| 1.50 | full | $0.717 | +/-$0.036 | $83.02 | $27.44 | 2.613% | 13,407 |
| 1.75 | exact | $0.739 | +/-$0.039 | $89.53 | $28.85 | 2.560% | 14,694 |
| 1.75 | half | $0.655 | +/-$0.036 | $82.41 | $27.38 | 2.392% | 15,835 |
| 1.75 | full | $0.576 | +/-$0.033 | $75.06 | $25.45 | 2.265% | 16,956 |
| 2.00 | exact | $0.604 | +/-$0.035 | $80.74 | $26.57 | 2.275% | 17,845 |
| 2.00 | half | $0.551 | +/-$0.032 | $73.46 | $25.15 | 2.193% | 17,750 |
| 2.00 | full | $0.456 | +/-$0.028 | $64.60 | $23.10 | 1.974% | 20,073 |

## Same-SD Check

The same-SD comparison scales each mode's whole ramp shape to match the
SD/round of `exact` at the same cut depth. This is not ramp optimization; it is
a check for whether a lower-EV mode is simply taking less risk.

| Cut decks | TC mode | EV/round | 95% CI | SD/round | Avg initial bet | EV/avg bet | N0 rounds |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1.00 | exact | $1.444 | +/-$0.053 | $120.64 | $37.53 | 3.846% | 6,984 |
| 1.00 | half | $1.367 | +/-$0.053 | $120.64 | $38.56 | 3.545% | 7,786 |
| 1.00 | full | $1.333 | +/-$0.053 | $120.64 | $39.58 | 3.367% | 8,192 |
| 1.25 | exact | $1.176 | +/-$0.048 | $110.40 | $34.56 | 3.402% | 8,816 |
| 1.25 | half | $1.180 | +/-$0.048 | $110.40 | $35.40 | 3.332% | 8,760 |
| 1.25 | full | $1.145 | +/-$0.048 | $110.40 | $36.21 | 3.163% | 9,296 |
| 1.50 | exact | $0.968 | +/-$0.043 | $99.17 | $31.39 | 3.085% | 10,490 |
| 1.50 | half | $0.907 | +/-$0.043 | $99.17 | $32.52 | 2.790% | 11,949 |
| 1.50 | full | $0.856 | +/-$0.043 | $99.17 | $32.78 | 2.613% | 13,407 |
| 1.75 | exact | $0.739 | +/-$0.039 | $89.53 | $28.85 | 2.560% | 14,694 |
| 1.75 | half | $0.711 | +/-$0.039 | $89.53 | $29.75 | 2.392% | 15,835 |
| 1.75 | full | $0.688 | +/-$0.039 | $89.53 | $30.36 | 2.265% | 16,956 |
| 2.00 | exact | $0.604 | +/-$0.035 | $80.74 | $26.57 | 2.275% | 17,845 |
| 2.00 | half | $0.606 | +/-$0.035 | $80.74 | $27.64 | 2.193% | 17,750 |
| 2.00 | full | $0.570 | +/-$0.035 | $80.74 | $28.87 | 1.974% | 20,073 |

## Interpretation

- Penetration matters a lot. With this ramp and two-player model, raw exact-mode
  EV falls from about $1.44/round at cut 1 deck to about $0.60/round at cut 2
  decks.
- Coarser TC estimation usually lowers both EV and variance because it places
  fewer or smaller high-count bets.
- At equal SD, `exact` remains clearly ahead at cut 1 and cut 1.5. At cut 1.25
  and cut 2, `exact` and `half` are close enough that the point-estimate
  difference should not be overinterpreted without paired comparison or more
  rounds.
- `full` is consistently worse on EV/avg bet and N0 in this run.

