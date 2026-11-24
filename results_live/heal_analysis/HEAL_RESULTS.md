# Self-healing study

Runs: 55 (pilot seed 99 excluded).


## Fault injected

|                                 |   n | slo_viol_pct   | error_pct     | p95_mean_ms      | recovery_s     | heals       | correct_heal   | detect_s      | false_heals   |
|:--------------------------------|----:|:---------------|:--------------|:-----------------|:---------------|:------------|:---------------|:--------------|:--------------|
| HPA                             |   5 | 93.5 ± 10.51   | 57.58 ± 52.43 | 1400.38 ± 847.66 | 230.0 ± 17.55  | 0.0 ± 0.0   | 0.0 ± 0.0      | nan ± nan     | 0.0 ± 0.0     |
| SHIELD-AI (heal)                |  15 | 28.02 ± 27.89  | 1.61 ± 4.87   | 229.64 ± 270.51  | 70.13 ± 78.58  | 0.67 ± 0.49 | 0.67 ± 0.49    | 44.08 ± 17.32 | 0.0 ± 0.0     |
| SHIELD-AI (heal, anomaly-gated) |   5 | 57.13 ± 46.08  | 0.91 ± 0.66   | 366.48 ± 249.09  | 144.6 ± 128.41 | 0.0 ± 0.0   | 0.0 ± 0.0      | nan ± nan     | 0.0 ± 0.0     |
| SHIELD-AI (no heal)             |  15 | 30.15 ± 34.94  | 0.52 ± 0.65   | 216.79 ± 189.62  | 83.93 ± 101.86 | 0.0 ± 0.0   | 0.0 ± 0.0      | nan ± nan     | 0.0 ± 0.0     |

## No fault (false-heal control)

|                     |   n | slo_viol_pct   | error_pct   | p95_mean_ms     | recovery_s     | heals     | correct_heal   | detect_s   | false_heals   |
|:--------------------|----:|:---------------|:------------|:----------------|:---------------|:----------|:---------------|:-----------|:--------------|
| HPA                 |   5 | 50.46 ± 46.07  | 0.43 ± 0.4  | 322.78 ± 200.61 | 135.4 ± 124.63 | 0.0 ± 0.0 | 0.0 ± 0.0      | nan ± nan  | 0.0 ± 0.0     |
| SHIELD-AI (heal)    |   5 | 18.13 ± 9.21   | 0.47 ± 0.15 | 118.15 ± 19.19  | 12.8 ± 17.17   | 0.0 ± 0.0 | 0.0 ± 0.0      | nan ± nan  | 0.0 ± 0.0     |
| SHIELD-AI (no heal) |   5 | 22.57 ± 9.19   | 0.51 ± 0.14 | 125.19 ± 45.43  | 42.4 ± 50.95   | 0.0 ± 0.0 | 0.0 ± 0.0      | nan ± nan  | 0.0 ± 0.0     |

## Pairwise tests (fault runs; two-sided Mann–Whitney U, Holm within metric)

| metric       | a                               | b                               |   median_a |   median_b |   cliffs_delta |      p |   p_holm |
|:-------------|:--------------------------------|:--------------------------------|-----------:|-----------:|---------------:|-------:|---------:|
| slo_viol_pct | SHIELD-AI (heal)                | SHIELD-AI (heal, anomaly-gated) |    19.1667 |    89.3617 |          -0.45 | 0.1493 |   0.3628 |
| error_pct    | SHIELD-AI (heal)                | SHIELD-AI (heal, anomaly-gated) |     0.22   |     1.142  |          -0.44 | 0.168  |   0.8506 |
| p95_mean_ms  | SHIELD-AI (heal)                | SHIELD-AI (heal, anomaly-gated) |   135.383  |   516.913  |          -0.36 | 0.2661 |   0.8889 |
| recovery_s   | SHIELD-AI (heal)                | SHIELD-AI (heal, anomaly-gated) |    18      |   234      |          -0.28 | 0.3813 |   1      |
| slo_viol_pct | SHIELD-AI (heal)                | SHIELD-AI (no heal)             |    19.1667 |     7.5314 |          -0    | 1      |   1      |
| error_pct    | SHIELD-AI (heal)                | SHIELD-AI (no heal)             |     0.22   |     0.2312 |           0.04 | 0.8682 |   0.8682 |
| p95_mean_ms  | SHIELD-AI (heal)                | SHIELD-AI (no heal)             |   135.383  |   147.754  |          -0    | 1      |   1      |
| recovery_s   | SHIELD-AI (heal)                | SHIELD-AI (no heal)             |    18      |    17      |           0.02 | 0.9501 |   1      |
| slo_viol_pct | SHIELD-AI (heal)                | HPA                             |    19.1667 |   100      |          -0.95 | 0.0022 |   0.0132 |
| error_pct    | SHIELD-AI (heal)                | HPA                             |     0.22   |    93.9429 |          -0.47 | 0.1418 |   0.8506 |
| p95_mean_ms  | SHIELD-AI (heal)                | HPA                             |   135.383  |  2009.36   |          -0.95 | 0.0005 |   0.0031 |
| recovery_s   | SHIELD-AI (heal)                | HPA                             |    18      |   235      |          -0.92 | 0.0029 |   0.0176 |
| slo_viol_pct | SHIELD-AI (heal, anomaly-gated) | SHIELD-AI (no heal)             |    89.3617 |     7.5314 |           0.51 | 0.106  |   0.3628 |
| error_pct    | SHIELD-AI (heal, anomaly-gated) | SHIELD-AI (no heal)             |     1.142  |     0.2312 |           0.36 | 0.2661 |   0.8506 |
| p95_mean_ms  | SHIELD-AI (heal, anomaly-gated) | SHIELD-AI (no heal)             |   516.913  |   147.754  |           0.36 | 0.2661 |   0.8889 |
| recovery_s   | SHIELD-AI (heal, anomaly-gated) | SHIELD-AI (no heal)             |   234      |    17      |           0.17 | 0.596  |   1      |
| slo_viol_pct | SHIELD-AI (heal, anomaly-gated) | HPA                             |    89.3617 |   100      |          -0.68 | 0.0907 |   0.3628 |
| error_pct    | SHIELD-AI (heal, anomaly-gated) | HPA                             |     1.142  |    93.9429 |          -0.36 | 0.4206 |   0.8506 |
| p95_mean_ms  | SHIELD-AI (heal, anomaly-gated) | HPA                             |   516.913  |  2009.36   |          -0.52 | 0.2222 |   0.8889 |
| recovery_s   | SHIELD-AI (heal, anomaly-gated) | HPA                             |   234      |   235      |          -0.28 | 0.5271 |   1      |
| slo_viol_pct | SHIELD-AI (no heal)             | HPA                             |     7.5314 |   100      |          -0.92 | 0.0029 |   0.0147 |
| error_pct    | SHIELD-AI (no heal)             | HPA                             |     0.2312 |    93.9429 |          -0.47 | 0.1418 |   0.8506 |
| p95_mean_ms  | SHIELD-AI (no heal)             | HPA                             |   147.754  |  2009.36   |          -0.84 | 0.0037 |   0.0187 |
| recovery_s   | SHIELD-AI (no heal)             | HPA                             |    17      |   235      |          -0.6  | 0.0527 |   0.2636 |

## Pre-registered test: heal vs no heal (fault runs, all seeds)

n = 15 vs 15
- Primary, time to recover: median 18 s vs 17 s, Mann–Whitney p = 0.9501, Cliff's δ = 0.02
- Secondary, still degraded at end (recovery ≥ 230 s): 1/15 vs 4/15, Fisher exact p = 0.3295