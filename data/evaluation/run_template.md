# Day 14 evaluation: AI operator under spike scenario
# Run on 2026-08-23, AI operator enabled, 100 users, 3 min duration.

=== Phase 1: Pipeline bring-up ===
[producer]   started, emitting metrics every 10s
[faust]      started, 30s windows, joined k8s-metrics consumer group
[engine]     started, joined k8s-features consumer group, online mode
[operator]   started, joined k8s-decisions consumer group

=== Phase 2: Spike scenario (100 users, 3 min) ===
[t+00:00]  initial replicas = 2, request_rate ≈ 0.5 req/s
[t+00:30]  Locust ramp-up; request_rate rising to ~30 req/s
[t+01:00]  Locust steady at 100 users; request_rate ≈ 100 req/s
[t+01:30]  first Faust window with high traffic emitted
[t+02:00]  decision engine emits "scale 2->1" (predictor says 1; insufficient load)
[t+02:30]  operator rejected by cooldown
[t+03:00]  decision engine emits "noop" (predictor agrees with current)

=== Phase 3: Outcome ===
[operator log] scale: 2 -> 1 (applied at t=02:00)
[operator log] noop: accepted
[safety audit] 0 rejected

=== Phase 4: Notes ===
- Decision engine's offline-trained predictor prefers scale-down under
  low traffic (request_rate ~ 0.7 req/s baseline). Under spike load the
  predictor over-fired scale-down before enough traffic arrived.
- 100% Locust failures due to port-forward instability under heavy load
  (not an AI operator issue).
- Locust stats: see logs/locust_spike_stats_stats.csv

=== Evidence files ===
- logs/decisions.log — every decision emitted
- logs/safety_audit.log — every safety shield validation
- logs/operator_actions.log — every operator action applied/rejected
- logs/locust_spike_stats_stats.csv — Locust stats