# scripts/ — Reproducibility bundle

These scripts reproduce the project from a fresh VM in ~30 minutes.

## Quick start (from a fresh Azure `Standard_D4as_v5` VM)

```bash
git clone https://github.com/sudo-Harshk/k8-auto-scaling-self-healing.git
cd k8-auto-scaling-self-healing
./scripts/bootstrap_vm.sh    # install Docker, kind, Helm, Java, tla2tools
./scripts/build_image.sh     # build k8-ai-ops:dev
./scripts/deploy_infra.sh    # create kind cluster, deploy podinfo, monitoring, kafka
./scripts/run_pipeline.sh    # start producer, Faust, engine, operator
./scripts/run_comparison.sh  # Day-14 evaluation harness
```

## Script catalogue

| Script | Purpose | Time |
|--------|---------|------|
| `bootstrap_vm.sh` | Install all host dependencies | ~5 min |
| `build_image.sh` | Rebuild `k8-ai-ops:dev` | ~3 min cold |
| `deploy_infra.sh` | Create kind cluster + deploy everything | ~10 min |
| `run_pipeline.sh` | Start the 4 AI services + port-forwards | ~30 s |
| `stop_all.sh` | Stop containers + port-forwards | ~5 s |
| `swap_operator.sh` | Switch between HPA / KEDA / AI | ~30 s |
| `run_comparison.sh` | Run Day-14 evaluation harness | variable |

## Order of operations

1. `bootstrap_vm.sh` once on a fresh VM
2. `build_image.sh` once after any `requirements.txt` change
3. `deploy_infra.sh` once after any manifest change
4. `run_pipeline.sh` + `swap_operator.sh` repeatedly during evaluation
5. `stop_all.sh` to clean up

## Outputs

`run_comparison.sh` writes:
- `data/evaluation/comparison_results.csv` — one row per (operator, scenario, run)
- `data/evaluation/run_<timestamp>_<op>_<scenario>.log` — per-run logs

## Verification commands

After bootstrap:

```bash
docker --version
kubectl version --client
kind version
helm version
java -jar ~/tla/tla2tools.jar -help | head -1
```

After deploy:

```bash
kubectl get nodes
kubectl get pods -A
docker run --rm k8-ai-ops:dev --entrypoint python -c "import river; print(river.__version__)"
```

After run_comparison:

```bash
cat data/evaluation/comparison_results.csv
```

## TLA+ verification

```bash
java -jar ~/tla/tla2tools.jar -config specs/SafetyShield.cfg specs/SafetyShield
```

Expected output (Day-10 verification):
```
264330 distinct states found, 0 states left on queue.
Finished in 03s
No error has been found.
```

## Python tests

```bash
docker run --rm --entrypoint python \
  -v "$PWD":/code -w /code \
  k8-ai-ops:dev \
  -m pytest tests/ -v
```

Expected: 24 passed (16 safety_shield + 8 actuator).