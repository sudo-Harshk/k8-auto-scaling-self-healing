#!/usr/bin/env bash
# Measure the capacity of ONE podinfo replica (25m CPU), then derive the
# shared configuration written to calibration.env:
#   CAPACITY_RPS     highest offered rate with p95 < SLO and errors < 1 %
#   REQ_PER_REPLICA  0.6 * CAPACITY_RPS  (same 60 % headroom as the HPA CPU target)
#   PEAK_RPS         load that needs ~16 replicas at REQ_PER_REPLICA (exercises >10 replicas)
source "$(dirname "$0")/lib.sh"
OUT="$ROOT/results_live/calibration"; mkdir -p "$OUT"
STAIR_PEAK="${STAIR_PEAK:-150}"   # staircase goes 10 %..100 % of this, 30 s per step

stop_all_ops
kubectl -n $NS scale deploy podinfo --replicas=1
kubectl -n $NS rollout status deploy/podinfo --timeout=120s
sleep 10
LOG "staircase to $STAIR_PEAK rps against 1 replica (5 min)"
run_load calibrate 0 300 "$OUT" "$STAIR_PEAK"
wait_load_and_collect "$OUT"

python3 - "$OUT/run_stats_history.csv" "$STAIR_PEAK" "$SLO_MS" > "$L/calibration.env" <<'EOF'
import sys, pandas as pd
h = pd.read_csv(sys.argv[1]); peak = float(sys.argv[2]); slo = float(sys.argv[3])
h = h[(h["Name"] == "Aggregated") & (h["Timestamp"] > 1e9)].copy()
h["t"] = h["Timestamp"] - h["Timestamp"].min()
h["step"] = (h["t"] // 30).astype(int)
best = 0.0
for step, g in h.groupby("step"):
    g = g[g["t"] >= step * 30 + 10]          # skip 10 s transient per step
    if g.empty: continue
    rps = g["Requests/s"].mean(); fail = g["Failures/s"].mean()
    p95 = g["95%"].median()
    ok = p95 < slo and (fail / max(rps, 1e-9)) < 0.01
    print(f"# step {step}: offered={(step+1)*peak/10:.0f} served={rps:.1f} p95={p95:.0f}ms fail={fail:.2f}/s ok={ok}", file=sys.stderr)
    if ok: best = max(best, rps)
cap = round(best, 1)
rpr = round(0.6 * cap, 1)
print(f"CAPACITY_RPS={cap}")
print(f"REQ_PER_REPLICA={rpr}")
print(f"PEAK_RPS={int(16 * rpr)}")
print(f"SLO_MS={int(slo)}")
EOF
cat "$L/calibration.env"
cp "$L/calibration.env" "$OUT/"
kubectl -n $NS scale deploy podinfo --replicas=$MIN_R
