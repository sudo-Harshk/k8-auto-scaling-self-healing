# Day 16 — p95 Variability Rework, IEEE Paper Draft, Dashboard JSON

## Task
Fix the largest paper weakness (p95 latency zero-variance), produce a 6-page IEEE-format paper draft, and ship a reproducible Grafana dashboard JSON.

## Aim
Convert a workshop-quality paper into an IEEE-conference-submission-ready package.

## Why this day exists

`p95_latency_ms` is 4.75 ms in every row of the Day-6 dataset because podinfo is a trivial Go HTTP server with no backend dependency. Reviewers will flag this. Day 16 replaces podinfo with a DB-backed microservice so p95 varies under load, then re-runs the Day-6 → Day-13 → Day-14 chain. Also writes the actual IEEE-format paper (vs Day-14's M.Tech thesis chapters).

## Steps

1. **Pick a DB-backed workload**
   - Candidate: a Python Flask app backed by SQLite, exposing `GET /` (renders template), `GET /api/query` (runs an SQL query), `POST /api/write` (DB insert)
   - Build image, push to local registry or load into kind
   - Add `ops/manifests/workload-v2.yaml`

2. **Re-capture Day-6 dataset on new workload**
   - 3 scenarios (spike / steady-high / idle) × 30 min each
   - New `data/features_v2.csv` with p95 varying meaningfully
   - Compare `data/features.csv` (old, constant p95) vs `data/features_v2.csv` (new, variable p95)

3. **Retrain models on new dataset**
   - Replica predictor retrain
   - Anomaly detector retrain
   - Save as `data/replica_model_v2.pkl` and `data/anomaly_model_v2.pkl`
   - Update Day-9 decision engine to load v2 models by default

4. **Re-run Day-13 E2E on new workload**
   - Restart producer + Faust + engine + operator
   - Run scaling test (100 users) + healing test (fault injection)
   - Capture evidence in `data/evaluation/v2_*.log`

5. **Re-run Day-15 N=3 with v2 models**
   - Run the 27 evaluations again with v2 models
   - Update `comparison_results_N3.csv` (or save as v2)

6. **IEEE-format paper draft**
   - `docs/ieee_paper.tex` (or `.docx`) — 6-page IEEE conference template:
     - Abstract (150 words)
     - Introduction (1 page)
     - Related Work (1 page: HPA, KEDA, online ML, TLA+, formal verification in k8s)
     - Method (1.5 pages: architecture + algorithms + safety/liveness properties)
     - Evaluation (1 page: comparison + ablation + p95 evidence from v2 workload)
     - Discussion + Conclusion (0.5 page)
     - References (0.5 page, IEEE format)
   - Convert thesis chapters → IEEE-style with figure references

7. **Grafana dashboard JSON**
   - Use Grafana HTTP API with admin/admin auth
   - Build dashboard with panels:
     - Recent decisions (table from logs/decisions.log)
     - Approved vs rejected actions (stat from logs/safety_audit.log)
     - Current replica count (Prometheus query)
     - Anomaly score over time (Prometheus query)
     - Scaling action timeline (from logs/operator_actions.log)
   - Export via `GET /api/dashboards/uid/<id>` to `docs/dashboard.json`

8. **Final polish**
   - `README.md` — add Results section linking to thesis + paper + dashboard
   - `AMENDMENTS.md` — Day 16 entries
   - `MILESTONES.md` — Day 16 entries + project wrap-up

## Outcome

- New DB-backed workload deployed, dataset regenerated
- Models retrained on variable-p95 dataset
- 6-page IEEE paper draft
- Reproducible Grafana dashboard JSON
- All artifacts committed, VM synced

## Verification

- [ ] p95 latency varies across new dataset (>5× range)
- [ ] Models retrained; smoke test predicts on spike data
- [ ] IEEE paper draft is 6 pages, all sections filled
- [ ] `docs/dashboard.json` is valid Grafana export (can be re-imported)
- [ ] Final commit + tag `day-16`

## Time estimate: 8 hours

## Risk register

| Risk | Mitigation |
|------|-----------|
| New workload p95 still doesn't vary enough | Add artificial latency (random sleep 0–50 ms) to the workload to ensure variance |
| IEEE template not installed | Use `docs/ieee_paper.md` as markdown; convert to LaTeX later |
| Grafana auth fails | Use environment variable substitution; document in `scripts/export_grafana_dashboard.sh` |
| Retrained models regress on existing scenarios | Keep v1 models as fallback; only switch to v2 if MAE improves |