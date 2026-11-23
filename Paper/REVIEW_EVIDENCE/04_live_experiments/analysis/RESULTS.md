# Live evaluation results

Runs: 75. Values: mean ± SD over seeds (n per cell shown).


## Scenario: bursty

| Operator | n | p95_ms | p99_ms | error_pct | slo_viol_pct | replica_min | underprov_pct | scale_events | oscillations | policy_viol |
|---|---|---|---|---|---|---|---|---|---|---|
| HPA | 5 | 2020.0 ± 44.7 | 2420.0 ± 349.3 | 19.0 ± 15.8 | 62.6 ± 13.1 | 33.1 ± 6.2 | 50.9 ± 1.2 | 3.8 ± 1.3 | 0.0 ± 0.0 | 0.2 ± 0.4 |
| KEDA | 5 | 1780.0 ± 408.7 | 2220.0 ± 204.9 | 8.8 ± 5.7 | 35.7 ± 19.0 | 70.5 ± 8.0 | 42.3 ± 2.2 | 8.8 ± 0.8 | 4.4 ± 0.9 | 1.6 ± 0.9 |
| MT (FIRM-inspired) | 5 | 2000.0 ± 0.0 | 2120.0 ± 109.5 | 8.0 ± 2.6 | 29.9 ± 10.7 | 81.2 ± 5.4 | 27.9 ± 7.8 | 5.8 ± 1.9 | 0.0 ± 0.0 | 0.4 ± 0.5 |
| ML-only | 5 | 1720.0 ± 626.1 | 2120.0 ± 164.3 | 5.9 ± 3.1 | 45.9 ± 12.0 | 63.1 ± 7.8 | 44.8 ± 6.8 | 15.0 ± 1.9 | 8.6 ± 1.8 | 15.4 ± 2.1 |
| SHIELD-AI | 5 | 1318.0 ± 936.3 | 1508.0 ± 912.6 | 5.5 ± 5.1 | 32.3 ± 14.5 | 74.7 ± 15.6 | 39.4 ± 12.4 | 7.6 ± 0.5 | 3.2 ± 1.1 | 0.2 ± 0.4 |

## Scenario: diurnal

| Operator | n | p95_ms | p99_ms | error_pct | slo_viol_pct | replica_min | underprov_pct | scale_events | oscillations | policy_viol |
|---|---|---|---|---|---|---|---|---|---|---|
| HPA | 5 | 906.0 ± 229.8 | 1580.0 ± 334.7 | 0.5 ± 0.4 | 49.6 ± 6.4 | 40.5 ± 11.7 | 65.6 ± 6.8 | 7.2 ± 0.8 | 1.0 ± 0.0 | 1.2 ± 0.8 |
| KEDA | 5 | 388.0 ± 199.8 | 772.0 ± 389.2 | 0.1 ± 0.1 | 33.1 ± 20.0 | 64.1 ± 1.1 | 45.4 ± 2.3 | 12.6 ± 0.9 | 1.0 ± 0.0 | 5.0 ± 0.7 |
| MT (FIRM-inspired) | 5 | 574.0 ± 317.3 | 982.0 ± 534.5 | 0.1 ± 0.1 | 41.0 ± 18.6 | 74.4 ± 3.2 | 47.6 ± 3.2 | 10.6 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| ML-only | 5 | 502.0 ± 320.7 | 962.0 ± 653.7 | 0.2 ± 0.3 | 31.5 ± 17.8 | 65.1 ± 9.1 | 32.4 ± 8.2 | 14.2 ± 2.0 | 4.2 ± 1.5 | 11.8 ± 1.6 |
| SHIELD-AI | 5 | 496.0 ± 678.3 | 700.0 ± 739.3 | 0.8 ± 1.7 | 19.5 ± 23.6 | 76.5 ± 10.3 | 24.4 ± 14.4 | 9.0 ± 1.2 | 2.4 ± 0.9 | 0.0 ± 0.0 |

## Scenario: spike

| Operator | n | p95_ms | p99_ms | error_pct | slo_viol_pct | replica_min | underprov_pct | scale_events | oscillations | policy_viol | reaction_s | recovery_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HPA | 5 | 2180.0 ± 164.3 | 2680.0 ± 576.2 | 34.0 ± 24.2 | 45.5 ± 12.5 | 23.6 ± 4.1 | 57.4 ± 1.3 | 3.6 ± 2.4 | 0.6 ± 0.5 | 0.6 ± 0.9 | 29.0 ± 8.7 | 136.4 ± 47.9 |
| KEDA | 5 | 1620.0 ± 571.8 | 2280.0 ± 676.0 | 10.7 ± 11.2 | 36.9 ± 14.4 | 53.3 ± 7.5 | 38.0 ± 5.6 | 7.8 ± 1.1 | 1.0 ± 0.0 | 3.6 ± 0.5 | 16.6 ± 7.1 | 123.0 ± 37.5 |
| MT (FIRM-inspired) | 5 | 1600.0 ± 565.7 | 2100.0 ± 424.3 | 7.4 ± 5.7 | 26.1 ± 11.8 | 80.8 ± 4.5 | 33.5 ± 6.4 | 6.2 ± 2.0 | 0.0 ± 0.0 | 0.6 ± 0.5 | 27.2 ± 8.1 | 82.6 ± 35.3 |
| ML-only | 5 | 1552.0 ± 765.8 | 1860.0 ± 712.7 | 15.8 ± 14.0 | 36.3 ± 9.5 | 47.8 ± 8.1 | 39.9 ± 2.1 | 13.6 ± 2.6 | 4.6 ± 2.1 | 8.6 ± 3.4 | 44.0 ± 33.2 | 133.6 ± 31.6 |
| SHIELD-AI | 5 | 612.0 ± 835.9 | 882.0 ± 975.9 | 8.3 ± 18.5 | 24.3 ± 18.5 | 79.6 ± 24.4 | 21.6 ± 11.1 | 8.0 ± 1.0 | 2.4 ± 0.9 | 0.0 ± 0.0 | 32.6 ± 17.8 | 86.0 ± 59.0 |

## SHIELD-AI vs. each baseline (two-sided Mann–Whitney U, Holm-corrected per scenario×metric family; Cliff's δ, negative = SHIELD-AI lower)

| Scenario | Metric | vs | SHIELD median | other median | δ | p (Holm) |
|---|---|---|---|---|---|---|
| bursty | p95_ms | HPA | 2000.0 | 2000.0 | -0.52 | 0.492 |
| bursty | p95_ms | KEDA | 2000.0 | 2000.0 | -0.28 | 0.881 |
| bursty | p95_ms | MT (FIRM-inspired) | 2000.0 | 2000.0 | -0.40 | 0.539 |
| bursty | p95_ms | ML-only | 2000.0 | 2000.0 | -0.28 | 0.881 |
| bursty | p99_ms | HPA | 2100.0 | 2400.0 | -0.76 | 0.225 |
| bursty | p99_ms | KEDA | 2100.0 | 2300.0 | -0.48 | 0.734 |
| bursty | p99_ms | MT (FIRM-inspired) | 2100.0 | 2200.0 | -0.28 | 1.000 |
| bursty | p99_ms | ML-only | 2100.0 | 2100.0 | -0.20 | 1.000 |
| bursty | error_pct | HPA | 9.0 | 17.1 | -0.52 | 0.835 |
| bursty | error_pct | KEDA | 9.0 | 10.8 | -0.52 | 0.835 |
| bursty | error_pct | MT (FIRM-inspired) | 9.0 | 9.2 | -0.44 | 0.835 |
| bursty | error_pct | ML-only | 9.0 | 5.7 | -0.04 | 1.000 |
| bursty | slo_viol_pct | HPA | 31.9 | 60.1 | -0.92 | 0.063 |
| bursty | slo_viol_pct | KEDA | 31.9 | 39.3 | -0.04 | 1.000 |
| bursty | slo_viol_pct | MT (FIRM-inspired) | 31.9 | 36.8 | +0.08 | 1.000 |
| bursty | slo_viol_pct | ML-only | 31.9 | 45.3 | -0.44 | 0.929 |
| bursty | replica_min | HPA | 83.3 | 32.7 | +1.00 | 0.032 |
| bursty | replica_min | KEDA | 83.3 | 68.5 | +0.20 | 1.000 |
| bursty | replica_min | MT (FIRM-inspired) | 83.3 | 81.2 | -0.04 | 1.000 |
| bursty | replica_min | ML-only | 83.3 | 64.2 | +0.52 | 0.667 |
| bursty | underprov_pct | HPA | 39.8 | 50.9 | -0.68 | 0.381 |
| bursty | underprov_pct | KEDA | 39.8 | 42.0 | -0.12 | 1.000 |
| bursty | underprov_pct | MT (FIRM-inspired) | 39.8 | 25.8 | +0.52 | 0.667 |
| bursty | underprov_pct | ML-only | 39.8 | 43.2 | -0.28 | 1.000 |
| bursty | scale_events | HPA | 8.0 | 4.0 | +1.00 | 0.043 |
| bursty | scale_events | KEDA | 8.0 | 9.0 | -0.76 | 0.087 |
| bursty | scale_events | MT (FIRM-inspired) | 8.0 | 6.0 | +0.64 | 0.101 |
| bursty | scale_events | ML-only | 8.0 | 15.0 | -1.00 | 0.043 |
| bursty | oscillations | HPA | 4.0 | 0.0 | +1.00 | 0.026 |
| bursty | oscillations | KEDA | 4.0 | 4.0 | -0.52 | 0.121 |
| bursty | oscillations | MT (FIRM-inspired) | 4.0 | 0.0 | +1.00 | 0.026 |
| bursty | oscillations | ML-only | 4.0 | 9.0 | -1.00 | 0.026 |
| bursty | policy_viol | HPA | 0.0 | 0.0 | +0.00 | 1.000 |
| bursty | policy_viol | KEDA | 0.0 | 1.0 | -0.88 | 0.058 |
| bursty | policy_viol | MT (FIRM-inspired) | 0.0 | 0.0 | -0.20 | 1.000 |
| bursty | policy_viol | ML-only | 0.0 | 15.0 | -1.00 | 0.039 |
| diurnal | p95_ms | HPA | 150.0 | 970.0 | -0.60 | 0.570 |
| diurnal | p95_ms | KEDA | 150.0 | 480.0 | -0.20 | 1.000 |
| diurnal | p95_ms | MT (FIRM-inspired) | 150.0 | 700.0 | -0.44 | 0.884 |
| diurnal | p95_ms | ML-only | 150.0 | 380.0 | -0.28 | 1.000 |
| diurnal | p99_ms | HPA | 300.0 | 1600.0 | -0.64 | 0.460 |
| diurnal | p99_ms | KEDA | 300.0 | 930.0 | -0.20 | 1.000 |
| diurnal | p99_ms | MT (FIRM-inspired) | 300.0 | 1300.0 | -0.24 | 1.000 |
| diurnal | p99_ms | ML-only | 300.0 | 700.0 | -0.20 | 1.000 |
| diurnal | error_pct | HPA | 0.0 | 0.4 | -0.60 | 0.555 |
| diurnal | error_pct | KEDA | 0.0 | 0.1 | -0.20 | 1.000 |
| diurnal | error_pct | MT (FIRM-inspired) | 0.0 | 0.1 | -0.20 | 1.000 |
| diurnal | error_pct | ML-only | 0.0 | 0.0 | +0.00 | 1.000 |
| diurnal | slo_viol_pct | HPA | 3.4 | 51.9 | -0.76 | 0.222 |
| diurnal | slo_viol_pct | KEDA | 3.4 | 39.6 | -0.20 | 1.000 |
| diurnal | slo_viol_pct | MT (FIRM-inspired) | 3.4 | 47.6 | -0.60 | 0.452 |
| diurnal | slo_viol_pct | ML-only | 3.4 | 37.6 | -0.12 | 1.000 |
| diurnal | replica_min | HPA | 76.8 | 46.6 | +1.00 | 0.032 |
| diurnal | replica_min | KEDA | 76.8 | 64.7 | +0.76 | 0.167 |
| diurnal | replica_min | MT (FIRM-inspired) | 76.8 | 74.1 | +0.04 | 1.000 |
| diurnal | replica_min | ML-only | 76.8 | 62.2 | +0.76 | 0.167 |
| diurnal | underprov_pct | HPA | 23.2 | 61.5 | -1.00 | 0.032 |
| diurnal | underprov_pct | KEDA | 23.2 | 46.6 | -1.00 | 0.032 |
| diurnal | underprov_pct | MT (FIRM-inspired) | 23.2 | 46.9 | -1.00 | 0.032 |
| diurnal | underprov_pct | ML-only | 23.2 | 35.8 | -0.12 | 0.841 |
| diurnal | scale_events | HPA | 9.0 | 7.0 | +0.76 | 0.057 |
| diurnal | scale_events | KEDA | 9.0 | 12.0 | -1.00 | 0.043 |
| diurnal | scale_events | MT (FIRM-inspired) | 9.0 | 11.0 | -0.84 | 0.057 |
| diurnal | scale_events | ML-only | 9.0 | 15.0 | -1.00 | 0.043 |
| diurnal | oscillations | HPA | 3.0 | 1.0 | +0.80 | 0.069 |
| diurnal | oscillations | KEDA | 3.0 | 1.0 | +0.80 | 0.069 |
| diurnal | oscillations | MT (FIRM-inspired) | 3.0 | 0.0 | +1.00 | 0.027 |
| diurnal | oscillations | ML-only | 3.0 | 4.0 | -0.72 | 0.070 |
| diurnal | policy_viol | HPA | 0.0 | 1.0 | -0.80 | 0.049 |
| diurnal | policy_viol | KEDA | 0.0 | 5.0 | -1.00 | 0.027 |
| diurnal | policy_viol | MT (FIRM-inspired) | 0.0 | 0.0 | +0.00 | 1.000 |
| diurnal | policy_viol | ML-only | 0.0 | 11.0 | -1.00 | 0.027 |
| spike | p95_ms | HPA | 320.0 | 2300.0 | -0.84 | 0.133 |
| spike | p95_ms | KEDA | 320.0 | 2000.0 | -0.64 | 0.269 |
| spike | p95_ms | MT (FIRM-inspired) | 320.0 | 2000.0 | -0.60 | 0.269 |
| spike | p95_ms | ML-only | 320.0 | 2000.0 | -0.68 | 0.269 |
| spike | p99_ms | HPA | 520.0 | 3100.0 | -0.84 | 0.138 |
| spike | p99_ms | KEDA | 520.0 | 2100.0 | -0.76 | 0.167 |
| spike | p99_ms | MT (FIRM-inspired) | 520.0 | 2300.0 | -0.60 | 0.285 |
| spike | p99_ms | ML-only | 520.0 | 2200.0 | -0.52 | 0.285 |
| spike | error_pct | HPA | 0.0 | 50.8 | -0.84 | 0.138 |
| spike | error_pct | KEDA | 0.0 | 7.1 | -0.60 | 0.416 |
| spike | error_pct | MT (FIRM-inspired) | 0.0 | 10.2 | -0.60 | 0.416 |
| spike | error_pct | ML-only | 0.0 | 24.2 | -0.40 | 0.416 |
| spike | slo_viol_pct | HPA | 21.4 | 47.6 | -0.68 | 0.381 |
| spike | slo_viol_pct | KEDA | 21.4 | 36.5 | -0.28 | 1.000 |
| spike | slo_viol_pct | MT (FIRM-inspired) | 21.4 | 27.1 | -0.12 | 1.000 |
| spike | slo_viol_pct | ML-only | 21.4 | 39.6 | -0.28 | 1.000 |
| spike | replica_min | HPA | 90.8 | 21.1 | +1.00 | 0.032 |
| spike | replica_min | KEDA | 90.8 | 54.3 | +0.60 | 0.452 |
| spike | replica_min | MT (FIRM-inspired) | 90.8 | 79.2 | +0.52 | 0.452 |
| spike | replica_min | ML-only | 90.8 | 47.1 | +0.60 | 0.452 |
| spike | underprov_pct | HPA | 17.0 | 56.8 | -1.00 | 0.032 |
| spike | underprov_pct | KEDA | 17.0 | 37.4 | -0.68 | 0.190 |
| spike | underprov_pct | MT (FIRM-inspired) | 17.0 | 34.9 | -0.60 | 0.190 |
| spike | underprov_pct | ML-only | 17.0 | 41.3 | -0.84 | 0.108 |
| spike | scale_events | HPA | 8.0 | 3.0 | +0.92 | 0.059 |
| spike | scale_events | KEDA | 8.0 | 8.0 | +0.08 | 0.913 |
| spike | scale_events | MT (FIRM-inspired) | 8.0 | 7.0 | +0.52 | 0.392 |
| spike | scale_events | ML-only | 8.0 | 14.0 | -1.00 | 0.046 |
| spike | oscillations | HPA | 3.0 | 1.0 | +0.88 | 0.064 |
| spike | oscillations | KEDA | 3.0 | 1.0 | +0.80 | 0.064 |
| spike | oscillations | MT (FIRM-inspired) | 3.0 | 0.0 | +1.00 | 0.027 |
| spike | oscillations | ML-only | 3.0 | 5.0 | -0.60 | 0.130 |
| spike | policy_viol | HPA | 0.0 | 0.0 | -0.40 | 0.180 |
| spike | policy_viol | KEDA | 0.0 | 4.0 | -1.00 | 0.026 |
| spike | policy_viol | MT (FIRM-inspired) | 0.0 | 1.0 | -0.60 | 0.134 |
| spike | policy_viol | ML-only | 0.0 | 8.0 | -1.00 | 0.026 |
| spike | reaction_s | HPA | 25.0 | 34.0 | +0.00 | 1.000 |
| spike | reaction_s | KEDA | 25.0 | 19.0 | +0.88 | 0.107 |
| spike | reaction_s | MT (FIRM-inspired) | 25.0 | 26.0 | +0.08 | 1.000 |
| spike | reaction_s | ML-only | 25.0 | 35.0 | -0.40 | 1.000 |
| spike | recovery_s | HPA | 80.0 | 169.0 | -0.60 | 0.570 |
| spike | recovery_s | KEDA | 80.0 | 136.0 | -0.44 | 0.747 |
| spike | recovery_s | MT (FIRM-inspired) | 80.0 | 79.0 | +0.04 | 1.000 |
| spike | recovery_s | ML-only | 80.0 | 141.0 | -0.48 | 0.747 |

## Shield accounting (SHIELD-AI runs)

| scenario   |   shield_validated |   shield_modified |   shield_rejected |
|:-----------|-------------------:|------------------:|------------------:|
| bursty     |                148 |                19 |               103 |
| diurnal    |                128 |                15 |                81 |
| spike      |                105 |                21 |                61 |