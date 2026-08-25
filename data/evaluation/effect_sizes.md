# Effect sizes: AI vs HPA / KEDA

Source: `data/evaluation/comparison_results_N3.csv` (27 rows)

Cohen's d interpretation (positive = AI better than baseline):
- |d| < 0.2: negligible
- 0.2 <= |d| < 0.5: small
- 0.5 <= |d| < 0.8: medium
- |d| >= 0.8: large

## Scenario: idle

### Scaling lag (s)
- AI:   5.00 (n=3)
- HPA:  5.00 (n=3)
- KEDA: 5.00 (n=3)
- Cohen's d (AI vs HPA): **-0.00** (negligible)
- Cohen's d (AI vs KEDA): **-0.00** (negligible)

### p95 latency avg (ms)
- AI:   30000.00 (n=3)
- HPA:  3.33 (n=3)
- KEDA: 3.67 (n=3)
- Cohen's d (AI vs HPA): **-73476.53** (large)
- Cohen's d (AI vs KEDA): **-73475.71** (large)

### p95 latency max (ms)
- AI:   30000.00 (n=3)
- HPA:  13.00 (n=3)
- KEDA: 10.67 (n=3)
- Cohen's d (AI vs HPA): **-4896.86** (large)
- Cohen's d (AI vs KEDA): **-6230.67** (large)

### Error rate (%)
- AI:   100.00 (n=3)
- HPA:  0.00 (n=3)
- KEDA: 0.00 (n=3)
- Cohen's d (AI vs HPA): **-0.00** (negligible)
- Cohen's d (AI vs KEDA): **-0.00** (negligible)

### Total scale actions
- AI:   24.00 (n=3)
- HPA:  6.00 (n=3)
- KEDA: 0.00 (n=3)
- Cohen's d (AI vs HPA): **+8.49** (large)
- Cohen's d (AI vs KEDA): **+11.31** (large)

### Total heal actions
- AI:   1.00 (n=3)
- HPA:  0.00 (n=3)
- KEDA: 0.00 (n=3)
- Cohen's d (AI vs HPA): **+0.00** (negligible)
- Cohen's d (AI vs KEDA): **+0.00** (negligible)

## Scenario: spike

### Scaling lag (s)
- AI:   5.00 (n=3)
- HPA:  5.00 (n=3)
- KEDA: 5.00 (n=3)
- Cohen's d (AI vs HPA): **-0.00** (negligible)
- Cohen's d (AI vs KEDA): **-0.00** (negligible)

### p95 latency avg (ms)
- AI:   30000.00 (n=3)
- HPA:  3.33 (n=3)
- KEDA: 3.00 (n=3)
- Cohen's d (AI vs HPA): **-73476.53** (large)
- Cohen's d (AI vs KEDA): **-0.00** (negligible)

### p95 latency max (ms)
- AI:   30000.00 (n=3)
- HPA:  3.67 (n=3)
- KEDA: 4.00 (n=3)
- Cohen's d (AI vs HPA): **-73475.71** (large)
- Cohen's d (AI vs KEDA): **-0.00** (negligible)

### Error rate (%)
- AI:   100.00 (n=3)
- HPA:  0.00 (n=3)
- KEDA: 0.00 (n=3)
- Cohen's d (AI vs HPA): **-0.00** (negligible)
- Cohen's d (AI vs KEDA): **-0.00** (negligible)

### Total scale actions
- AI:   7.00 (n=3)
- HPA:  8.00 (n=3)
- KEDA: 0.00 (n=3)
- Cohen's d (AI vs HPA): **-0.47** (small)
- Cohen's d (AI vs KEDA): **+3.30** (large)

### Total heal actions
- AI:   1.00 (n=3)
- HPA:  0.00 (n=3)
- KEDA: 0.00 (n=3)
- Cohen's d (AI vs HPA): **+0.00** (negligible)
- Cohen's d (AI vs KEDA): **+0.00** (negligible)

## Scenario: steady

### Scaling lag (s)
- AI:   5.00 (n=3)
- HPA:  5.00 (n=3)
- KEDA: 5.00 (n=3)
- Cohen's d (AI vs HPA): **-0.00** (negligible)
- Cohen's d (AI vs KEDA): **-0.00** (negligible)

### p95 latency avg (ms)
- AI:   30000.00 (n=3)
- HPA:  3.33 (n=3)
- KEDA: 3.00 (n=3)
- Cohen's d (AI vs HPA): **-73476.53** (large)
- Cohen's d (AI vs KEDA): **-0.00** (negligible)

### p95 latency max (ms)
- AI:   30000.00 (n=3)
- HPA:  3.67 (n=3)
- KEDA: 8.67 (n=3)
- Cohen's d (AI vs HPA): **-73475.71** (large)
- Cohen's d (AI vs KEDA): **-4732.20** (large)

### Error rate (%)
- AI:   100.00 (n=3)
- HPA:  0.00 (n=3)
- KEDA: 0.00 (n=3)
- Cohen's d (AI vs HPA): **-0.00** (negligible)
- Cohen's d (AI vs KEDA): **-0.00** (negligible)

### Total scale actions
- AI:   15.33 (n=3)
- HPA:  8.00 (n=3)
- KEDA: 0.00 (n=3)
- Cohen's d (AI vs HPA): **+4.12** (large)
- Cohen's d (AI vs KEDA): **+8.62** (large)

### Total heal actions
- AI:   1.00 (n=3)
- HPA:  0.00 (n=3)
- KEDA: 0.00 (n=3)
- Cohen's d (AI vs HPA): **+0.00** (negligible)
- Cohen's d (AI vs KEDA): **+0.00** (negligible)
