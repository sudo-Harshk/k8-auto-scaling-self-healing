# Live evaluation results

Runs: 45. Values: mean ± SD over seeds (n per cell shown).


## Scenario: bursty

| Operator | n | p95_ms | p99_ms | error_pct | slo_viol_pct | replica_min | underprov_pct | scale_events | oscillations | policy_viol |
|---|---|---|---|---|---|---|---|---|---|---|
| HPA | 3 | 2033.3 ± 57.7 | 2600.0 ± 346.4 | 26.9 ± 16.3 | 70.5 ± 10.1 | 33.6 ± 8.7 | 50.7 ± 1.7 | 4.0 ± 1.7 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| KEDA | 3 | 2033.3 ± 57.7 | 2366.7 ± 57.7 | 12.8 ± 1.8 | 48.1 ± 11.6 | 65.1 ± 3.9 | 42.6 ± 3.0 | 8.7 ± 0.6 | 4.7 ± 1.2 | 1.0 ± 0.0 |
| MT (FIRM-inspired) | 3 | 2000.0 ± 0.0 | 2200.0 ± 0.0 | 9.8 ± 0.6 | 37.7 ± 1.0 | 82.5 ± 5.9 | 22.4 ± 3.0 | 6.7 ± 1.5 | 0.0 ± 0.0 | 0.3 ± 0.6 |
| ML-only | 3 | 2000.0 ± 0.0 | 2200.0 ± 173.2 | 7.4 ± 2.5 | 52.6 ± 9.6 | 65.4 ± 9.0 | 42.7 ± 7.3 | 15.0 ± 2.6 | 9.3 ± 1.5 | 16.3 ± 2.1 |
| SHIELD-AI | 3 | 2000.0 ± 0.0 | 2166.7 ± 115.5 | 9.2 ± 0.3 | 41.9 ± 8.7 | 67.9 ± 17.5 | 40.8 ± 17.1 | 8.0 ± 0.0 | 3.3 ± 1.2 | 0.3 ± 0.6 |

## Scenario: diurnal

| Operator | n | p95_ms | p99_ms | error_pct | slo_viol_pct | replica_min | underprov_pct | scale_events | oscillations | policy_viol |
|---|---|---|---|---|---|---|---|---|---|---|
| HPA | 3 | 1056.7 ± 125.0 | 1800.0 ± 200.0 | 0.7 ± 0.4 | 51.6 ± 2.2 | 49.0 ± 2.4 | 60.7 ± 0.9 | 7.3 ± 1.2 | 1.0 ± 0.0 | 1.3 ± 1.2 |
| KEDA | 3 | 526.7 ± 64.3 | 1043.3 ± 140.1 | 0.1 ± 0.0 | 45.1 ± 5.3 | 64.4 ± 1.0 | 44.3 ± 2.3 | 12.7 ± 1.2 | 1.0 ± 0.0 | 5.0 ± 0.0 |
| MT (FIRM-inspired) | 3 | 796.7 ± 95.0 | 1366.7 ± 57.7 | 0.2 ± 0.0 | 49.8 ± 4.0 | 76.4 ± 2.1 | 48.4 ± 4.2 | 10.7 ± 0.6 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| ML-only | 3 | 583.3 ± 425.2 | 1173.3 ± 827.1 | 0.4 ± 0.4 | 26.2 ± 22.8 | 67.2 ± 12.2 | 30.5 ± 11.0 | 13.0 ± 1.7 | 3.3 ± 1.2 | 11.3 ± 1.5 |
| SHIELD-AI | 3 | 730.0 ± 845.4 | 970.0 ± 905.4 | 1.3 ± 2.2 | 31.1 ± 24.7 | 80.5 ± 10.5 | 19.9 ± 16.7 | 9.7 ± 0.6 | 2.3 ± 1.2 | 0.0 ± 0.0 |

## Scenario: spike

| Operator | n | p95_ms | p99_ms | error_pct | slo_viol_pct | replica_min | underprov_pct | scale_events | oscillations | policy_viol | reaction_s | recovery_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HPA | 3 | 2300.0 ± 0.0 | 3100.0 ± 0.0 | 51.6 ± 1.3 | 54.1 ± 6.0 | 20.6 ± 0.6 | 56.6 ± 0.3 | 2.0 ± 1.0 | 0.3 ± 0.6 | 0.0 ± 0.0 | 24.3 ± 8.4 | 169.3 ± 0.6 |
| KEDA | 3 | 2033.3 ± 57.7 | 2666.7 ± 513.2 | 17.3 ± 9.3 | 44.1 ± 11.5 | 48.6 ± 5.4 | 40.9 ± 5.6 | 8.3 ± 0.6 | 1.0 ± 0.0 | 3.7 ± 0.6 | 19.3 ± 0.6 | 138.0 ± 18.1 |
| MT (FIRM-inspired) | 3 | 2000.0 ± 0.0 | 2366.7 ± 57.7 | 11.5 ± 1.1 | 33.6 ± 7.6 | 82.0 ± 5.9 | 33.2 ± 7.0 | 6.7 ± 2.3 | 0.0 ± 0.0 | 0.3 ± 0.6 | 32.3 ± 5.7 | 103.0 ± 28.8 |
| ML-only | 3 | 2066.7 ± 57.7 | 2233.3 ± 57.7 | 25.9 ± 2.2 | 42.2 ± 3.3 | 42.7 ± 3.9 | 41.4 ± 0.2 | 13.0 ± 3.5 | 4.7 ± 2.5 | 7.7 ± 4.0 | 52.0 ± 44.2 | 150.3 ± 11.4 |
| SHIELD-AI | 3 | 913.3 ± 1027.7 | 1270.0 ± 1154.9 | 13.8 ± 23.8 | 35.8 ± 12.9 | 73.6 ± 32.1 | 25.0 ± 14.2 | 8.3 ± 1.2 | 2.7 ± 0.6 | 0.0 ± 0.0 | 36.3 ± 24.1 | 121.0 ± 42.6 |

## SHIELD-AI vs. each baseline (two-sided Mann–Whitney U, Holm-corrected per scenario×metric family; Cliff's δ, negative = SHIELD-AI lower)

| Scenario | Metric | vs | SHIELD median | other median | δ | p (Holm) |
|---|---|---|---|---|---|---|
| bursty | p95_ms | HPA | 2000.0 | 2000.0 | -0.33 | 1.000 |
| bursty | p95_ms | KEDA | 2000.0 | 2000.0 | -0.33 | 1.000 |
| bursty | p95_ms | MT (FIRM-inspired) | 2000.0 | 2000.0 | +0.00 | 1.000 |
| bursty | p95_ms | ML-only | 2000.0 | 2000.0 | +0.00 | 1.000 |
| bursty | p99_ms | HPA | 2100.0 | 2400.0 | -1.00 | 0.289 |
| bursty | p99_ms | KEDA | 2100.0 | 2400.0 | -0.89 | 0.330 |
| bursty | p99_ms | MT (FIRM-inspired) | 2100.0 | 2200.0 | -0.33 | 1.000 |
| bursty | p99_ms | ML-only | 2100.0 | 2100.0 | -0.11 | 1.000 |
| bursty | error_pct | HPA | 9.1 | 17.9 | -1.00 | 0.400 |
| bursty | error_pct | KEDA | 9.1 | 13.3 | -1.00 | 0.400 |
| bursty | error_pct | MT (FIRM-inspired) | 9.1 | 10.1 | -0.78 | 0.400 |
| bursty | error_pct | ML-only | 9.1 | 7.0 | +0.33 | 0.700 |
| bursty | slo_viol_pct | HPA | 45.6 | 70.9 | -1.00 | 0.400 |
| bursty | slo_viol_pct | KEDA | 45.6 | 43.6 | -0.11 | 1.000 |
| bursty | slo_viol_pct | MT (FIRM-inspired) | 45.6 | 37.6 | +0.33 | 1.000 |
| bursty | slo_viol_pct | ML-only | 45.6 | 49.0 | -0.56 | 1.000 |
| bursty | replica_min | HPA | 59.0 | 36.2 | +1.00 | 0.400 |
| bursty | replica_min | KEDA | 59.0 | 66.0 | -0.33 | 1.000 |
| bursty | replica_min | MT (FIRM-inspired) | 59.0 | 81.2 | -0.56 | 1.000 |
| bursty | replica_min | ML-only | 59.0 | 67.8 | +0.11 | 1.000 |
| bursty | underprov_pct | HPA | 50.3 | 50.6 | -0.33 | 1.000 |
| bursty | underprov_pct | KEDA | 50.3 | 43.6 | +0.33 | 1.000 |
| bursty | underprov_pct | MT (FIRM-inspired) | 50.3 | 21.3 | +0.56 | 1.000 |
| bursty | underprov_pct | ML-only | 50.3 | 39.3 | +0.11 | 1.000 |
| bursty | scale_events | HPA | 8.0 | 5.0 | +1.00 | 0.237 |
| bursty | scale_events | KEDA | 8.0 | 9.0 | -0.67 | 0.375 |
| bursty | scale_events | MT (FIRM-inspired) | 8.0 | 7.0 | +0.67 | 0.375 |
| bursty | scale_events | ML-only | 8.0 | 14.0 | -1.00 | 0.237 |
| bursty | oscillations | HPA | 4.0 | 0.0 | +1.00 | 0.237 |
| bursty | oscillations | KEDA | 4.0 | 4.0 | -0.56 | 0.302 |
| bursty | oscillations | MT (FIRM-inspired) | 4.0 | 0.0 | +1.00 | 0.237 |
| bursty | oscillations | ML-only | 4.0 | 9.0 | -1.00 | 0.237 |
| bursty | policy_viol | HPA | 0.0 | 0.0 | +0.33 | 1.000 |
| bursty | policy_viol | KEDA | 0.0 | 1.0 | -0.67 | 0.563 |
| bursty | policy_viol | MT (FIRM-inspired) | 0.0 | 0.0 | +0.00 | 1.000 |
| bursty | policy_viol | ML-only | 0.0 | 17.0 | -1.00 | 0.306 |
| diurnal | p95_ms | HPA | 340.0 | 1000.0 | -0.33 | 1.000 |
| diurnal | p95_ms | KEDA | 340.0 | 500.0 | -0.33 | 1.000 |
| diurnal | p95_ms | MT (FIRM-inspired) | 340.0 | 800.0 | -0.33 | 1.000 |
| diurnal | p95_ms | ML-only | 340.0 | 750.0 | +0.11 | 1.000 |
| diurnal | p99_ms | HPA | 610.0 | 1800.0 | -0.44 | 1.000 |
| diurnal | p99_ms | KEDA | 610.0 | 1000.0 | -0.33 | 1.000 |
| diurnal | p99_ms | MT (FIRM-inspired) | 610.0 | 1400.0 | -0.33 | 1.000 |
| diurnal | p99_ms | ML-only | 610.0 | 1600.0 | +0.11 | 1.000 |
| diurnal | error_pct | HPA | 0.0 | 0.6 | -0.33 | 1.000 |
| diurnal | error_pct | KEDA | 0.0 | 0.1 | -0.33 | 1.000 |
| diurnal | error_pct | MT (FIRM-inspired) | 0.0 | 0.2 | -0.33 | 1.000 |
| diurnal | error_pct | ML-only | 0.0 | 0.3 | +0.00 | 1.000 |
| diurnal | slo_viol_pct | HPA | 39.3 | 51.9 | -0.78 | 0.800 |
| diurnal | slo_viol_pct | KEDA | 39.3 | 45.6 | -0.33 | 1.000 |
| diurnal | slo_viol_pct | MT (FIRM-inspired) | 39.3 | 49.6 | -0.56 | 1.000 |
| diurnal | slo_viol_pct | ML-only | 39.3 | 37.6 | +0.33 | 1.000 |
| diurnal | replica_min | HPA | 86.5 | 48.9 | +1.00 | 0.400 |
| diurnal | replica_min | KEDA | 86.5 | 64.9 | +1.00 | 0.400 |
| diurnal | replica_min | MT (FIRM-inspired) | 86.5 | 76.9 | +0.33 | 0.700 |
| diurnal | replica_min | ML-only | 86.5 | 62.2 | +0.78 | 0.400 |
| diurnal | underprov_pct | HPA | 12.7 | 60.9 | -1.00 | 0.400 |
| diurnal | underprov_pct | KEDA | 12.7 | 44.3 | -1.00 | 0.400 |
| diurnal | underprov_pct | MT (FIRM-inspired) | 12.7 | 48.3 | -1.00 | 0.400 |
| diurnal | underprov_pct | ML-only | 12.7 | 36.2 | -0.33 | 0.700 |
| diurnal | scale_events | HPA | 10.0 | 8.0 | +1.00 | 0.289 |
| diurnal | scale_events | KEDA | 10.0 | 12.0 | -1.00 | 0.289 |
| diurnal | scale_events | MT (FIRM-inspired) | 10.0 | 11.0 | -0.78 | 0.289 |
| diurnal | scale_events | ML-only | 10.0 | 12.0 | -1.00 | 0.289 |
| diurnal | oscillations | HPA | 3.0 | 1.0 | +0.67 | 0.563 |
| diurnal | oscillations | KEDA | 3.0 | 1.0 | +0.67 | 0.563 |
| diurnal | oscillations | MT (FIRM-inspired) | 3.0 | 0.0 | +1.00 | 0.237 |
| diurnal | oscillations | ML-only | 3.0 | 4.0 | -0.56 | 0.563 |
| diurnal | policy_viol | HPA | 0.0 | 2.0 | -0.67 | 0.375 |
| diurnal | policy_viol | KEDA | 0.0 | 5.0 | -1.00 | 0.187 |
| diurnal | policy_viol | MT (FIRM-inspired) | 0.0 | 0.0 | +0.00 | 1.000 |
| diurnal | policy_viol | ML-only | 0.0 | 11.0 | -1.00 | 0.191 |
| spike | p95_ms | HPA | 320.0 | 2300.0 | -1.00 | 0.237 |
| spike | p95_ms | KEDA | 320.0 | 2000.0 | -0.44 | 1.000 |
| spike | p95_ms | MT (FIRM-inspired) | 320.0 | 2000.0 | -0.33 | 1.000 |
| spike | p95_ms | ML-only | 320.0 | 2100.0 | -0.56 | 1.000 |
| spike | p99_ms | HPA | 690.0 | 3100.0 | -1.00 | 0.254 |
| spike | p99_ms | KEDA | 690.0 | 2800.0 | -0.78 | 0.600 |
| spike | p99_ms | MT (FIRM-inspired) | 690.0 | 2400.0 | -0.33 | 1.000 |
| spike | p99_ms | ML-only | 690.0 | 2200.0 | -0.33 | 1.000 |
| spike | error_pct | HPA | 0.0 | 51.0 | -1.00 | 0.400 |
| spike | error_pct | KEDA | 0.0 | 19.6 | -0.33 | 1.000 |
| spike | error_pct | MT (FIRM-inspired) | 0.0 | 11.9 | -0.33 | 1.000 |
| spike | error_pct | ML-only | 0.0 | 25.3 | -0.33 | 1.000 |
| spike | slo_viol_pct | HPA | 39.9 | 55.3 | -1.00 | 0.400 |
| spike | slo_viol_pct | KEDA | 39.9 | 38.5 | -0.11 | 1.000 |
| spike | slo_viol_pct | MT (FIRM-inspired) | 39.9 | 31.9 | +0.11 | 1.000 |
| spike | slo_viol_pct | ML-only | 39.9 | 41.0 | -0.11 | 1.000 |
| spike | replica_min | HPA | 90.8 | 20.9 | +1.00 | 0.400 |
| spike | replica_min | KEDA | 90.8 | 47.8 | +0.33 | 1.000 |
| spike | replica_min | MT (FIRM-inspired) | 90.8 | 80.0 | +0.33 | 1.000 |
| spike | replica_min | ML-only | 90.8 | 40.8 | +0.33 | 1.000 |
| spike | underprov_pct | HPA | 19.5 | 56.7 | -1.00 | 0.306 |
| spike | underprov_pct | KEDA | 19.5 | 37.8 | -0.56 | 0.800 |
| spike | underprov_pct | MT (FIRM-inspired) | 19.5 | 34.9 | -0.33 | 0.800 |
| spike | underprov_pct | ML-only | 19.5 | 41.3 | -1.00 | 0.306 |
| spike | scale_events | HPA | 9.0 | 2.0 | +1.00 | 0.289 |
| spike | scale_events | KEDA | 9.0 | 8.0 | +0.11 | 1.000 |
| spike | scale_events | MT (FIRM-inspired) | 9.0 | 8.0 | +0.56 | 0.737 |
| spike | scale_events | ML-only | 9.0 | 11.0 | -1.00 | 0.289 |
| spike | oscillations | HPA | 3.0 | 0.0 | +1.00 | 0.237 |
| spike | oscillations | KEDA | 3.0 | 1.0 | +1.00 | 0.237 |
| spike | oscillations | MT (FIRM-inspired) | 3.0 | 0.0 | +1.00 | 0.237 |
| spike | oscillations | ML-only | 3.0 | 5.0 | -0.44 | 0.500 |
| spike | policy_viol | HPA | 0.0 | 0.0 | +0.00 | 1.000 |
| spike | policy_viol | KEDA | 0.0 | 4.0 | -1.00 | 0.237 |
| spike | policy_viol | MT (FIRM-inspired) | 0.0 | 0.0 | -0.33 | 1.000 |
| spike | policy_viol | ML-only | 0.0 | 7.0 | -1.00 | 0.237 |
| spike | reaction_s | HPA | 25.0 | 20.0 | +0.44 | 1.000 |
| spike | reaction_s | KEDA | 25.0 | 19.0 | +0.89 | 0.463 |
| spike | reaction_s | MT (FIRM-inspired) | 25.0 | 34.0 | -0.33 | 1.000 |
| spike | reaction_s | ML-only | 25.0 | 75.0 | -0.33 | 1.000 |
| spike | recovery_s | HPA | 118.0 | 169.0 | -1.00 | 0.306 |
| spike | recovery_s | KEDA | 118.0 | 136.0 | -0.33 | 1.000 |
| spike | recovery_s | MT (FIRM-inspired) | 118.0 | 95.0 | +0.33 | 1.000 |
| spike | recovery_s | ML-only | 118.0 | 147.0 | -0.33 | 1.000 |

## Shield accounting (SHIELD-AI runs)

| scenario   |   shield_validated |   shield_modified |   shield_rejected |
|:-----------|-------------------:|------------------:|------------------:|
| bursty     |                 85 |                 9 |                58 |
| diurnal    |                 59 |                 7 |                30 |
| spike      |                 62 |                12 |                34 |