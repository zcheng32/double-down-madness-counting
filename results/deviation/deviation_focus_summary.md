# DDM Deviation Batch Scan

- Rounds per action per TC: `200,000`
- True counts: `candidate-specific`
- Rules: Version 1, six decks, strict first-card Ace rule, H17, no Push 22 side bet.
- `clear` means the best action beat the runner-up by more than the combined 95% Monte Carlo interval.

| Candidate | TC | Best | Runner-up | Edge | Combined 95% CI | Clear |
|---|---:|---:|---:|---:|---:|---:|
| hard 16 vs 10 | 4 | H | S | 0.00769 | 0.00465 | True |
| hard 16 vs 10 | 5 | S | H | 0.00035 | 0.00460 | False |
| hard 16 vs 10 | 6 | S | H | 0.00375 | 0.00458 | False |
| hard 16 vs 10 | 7 | S | H | 0.00984 | 0.00453 | True |
| hard 12 vs 3 | 1 | H | S | 0.03806 | 0.00552 | True |
| hard 12 vs 3 | 2 | H | S | 0.01754 | 0.00554 | True |
| hard 12 vs 3 | 3 | H | S | 0.00491 | 0.00555 | False |
| hard 12 vs 3 | 4 | S | H | 0.00672 | 0.00555 | True |
| hard 12 vs 3 | 5 | S | H | 0.02413 | 0.00557 | True |
| hard 12 vs 4 | 0 | H | S | 0.02430 | 0.00558 | True |
| hard 12 vs 4 | 1 | H | S | 0.00675 | 0.00561 | True |
| hard 12 vs 4 | 2 | S | H | 0.01006 | 0.00562 | True |
| hard 12 vs 4 | 3 | S | H | 0.02044 | 0.00563 | True |
| hard 13 vs 2 | 2 | H | S | 0.01082 | 0.00508 | True |
| hard 13 vs 2 | 3 | S | H | 0.00313 | 0.00506 | False |
| hard 13 vs 2 | 4 | S | H | 0.00706 | 0.00505 | True |
| hard 13 vs 2 | 5 | S | H | 0.02613 | 0.00504 | True |
| single-card 8 vs 4 | -1 | H | D | 0.05077 | 0.01090 | True |
| single-card 8 vs 4 | 0 | H | D | 0.03564 | 0.01084 | True |
| single-card 8 vs 4 | 1 | H | D | 0.00243 | 0.01078 | False |
| single-card 8 vs 4 | 2 | D | H | 0.00651 | 0.01071 | False |
| single-card 8 vs 4 | 3 | D | H | 0.01591 | 0.01067 | True |
| single-card 10 vs 10 low TC | -4 | D | H | 0.02574 | 0.00942 | True |
| single-card 10 vs 10 low TC | -3 | D | H | 0.02737 | 0.00943 | True |
| single-card 10 vs 10 low TC | -2 | D | H | 0.03032 | 0.00942 | True |
| single-card 10 vs 10 low TC | -1 | D | H | 0.03502 | 0.00942 | True |
| single-card 10 vs 10 low TC | 0 | D | H | 0.03602 | 0.00942 | True |
| single-card 10 vs A low TC | -4 | H | D | 0.00364 | 0.00952 | False |
| single-card 10 vs A low TC | -3 | D | H | 0.00978 | 0.00954 | True |
| single-card 10 vs A low TC | -2 | D | H | 0.02333 | 0.00956 | True |
| single-card 10 vs A low TC | -1 | D | H | 0.03564 | 0.00956 | True |
| single-card 10 vs A low TC | 0 | D | H | 0.04784 | 0.00957 | True |
