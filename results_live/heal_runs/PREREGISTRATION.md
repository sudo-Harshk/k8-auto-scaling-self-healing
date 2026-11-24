# Self-healing extension: analysis plan fixed before the runs

Written 2026-11-23 shortly before the extension started (first run logged 09:24:09 UTC by the VM clock). A copy is placed on VM B (`results_live/heal_runs/PREREGISTRATION.md`) at launch.

**Why.** The first 5 seeds (1–5) showed 5/5 correct heals but no significant recovery difference (n = 5, bimodal outcomes).

**Extension (fixed size, no early stopping, no further additions).**
- Arms: `shield-heal` and `shield-noheal`, fault runs only.
- Seeds 6–15 (10 more per arm). The analysis pools them with seeds 1–5, giving n = 15 per arm.
- Same code, image, cluster, VM, load (constant, 25 % of peak), fault (SIGSTOP at 60 s) and duration (300 s) as seeds 1–5.
- HPA and the gated arm are not extended. Their 5 seeds are reported as they are.

**Primary outcome.** Time to recover (`recovery_s`, censored at the end of the run). Heal vs no heal, two-sided Mann–Whitney U, α = 0.05, with Cliff's δ.

**Secondary outcome.** Whether the service was still degraded at the end of the run (recovery censored at ≥ 230 s): heal vs no heal, two-sided Fisher's exact test.

**Also reported.** Time over SLO, error %, detection time, correct-pod rate, false heals.

**Reporting.** All runs are reported whatever the result, including failed or anomalous runs, with a stated reason for any exclusion. The VM was rebooted before the extension. Kind's inotify limits were restored and the kube-proxy, kube-state-metrics and prometheus-operator pods restarted. This is disclosed.
