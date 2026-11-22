#!/usr/bin/env bash
# Shared helpers for the live evaluation harness. Source, do not execute.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
L="$ROOT/scripts/eval/live"
IMG=k8-ai-ops:dev
NS=podinfo
LOG() { printf '\033[1;34m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }

# ---- shared configuration (written by calibrate.sh) ----
[[ -f "$L/calibration.env" ]] && source "$L/calibration.env"
REQ_PER_REPLICA="${REQ_PER_REPLICA:-15}"
PEAK_RPS="${PEAK_RPS:-200}"
SLO_MS="${SLO_MS:-250}"
MIN_R=2
MAX_R=20

port_forwards() {
  pkill -f "port-forward.*9090:9090" 2>/dev/null || true
  pkill -f "port-forward.*9094:9094" 2>/dev/null || true
  nohup kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090 >/tmp/pf-prom.log 2>&1 &
  nohup kubectl -n kafka port-forward svc/kafka 9094:9094 >/tmp/pf-kafka.log 2>&1 &
  sleep 4
}

# ---------------- operators ----------------
stop_all_ops() {
  kubectl -n $NS delete hpa --all --ignore-not-found >/dev/null
  kubectl -n $NS delete scaledobject --all --ignore-not-found >/dev/null 2>&1 || true
  docker rm -f ev-producer ev-faust ev-engine ev-actuator ev-mt >/dev/null 2>&1 || true
}

reset_workload() {
  kubectl -n $NS scale deploy podinfo --replicas=$MIN_R >/dev/null
  kubectl -n $NS rollout status deploy/podinfo --timeout=180s >/dev/null
  # wait until surplus pods are gone
  for _ in $(seq 60); do
    n=$(kubectl -n $NS get pods -l app=podinfo --no-headers 2>/dev/null | wc -l)
    [[ "$n" -le $MIN_R ]] && break; sleep 2
  done
}

_pipe_env() {
  echo -e "-e KAFKA_BOOTSTRAP=localhost:9094 -e PROMETHEUS_URL=http://localhost:9090 \
 -e WORKLOAD_NAMESPACE=$NS -e WORKLOAD_DEPLOYMENT=podinfo \
 -e MIN_REPLICAS=$MIN_R -e MAX_REPLICAS=$MAX_R -e REQ_PER_REPLICA=$REQ_PER_REPLICA \
 -e CPU_TARGET_PCT=60 -e CPU_LIMIT_CORES=0.025 -e PYTHONUNBUFFERED=1"
}

start_feature_pipeline() {   # producer + Faust (shared by MT, ML-only, SHIELD-AI)
  docker run -d --rm --network host --name ev-producer $(_pipe_env) \
    -e KAFKA_TOPIC=k8s-metrics -e POLL_INTERVAL=5 -e RATE_WINDOW=30s \
    -v "$ROOT":/code -w /code $IMG src/kafka/producer.py >/dev/null
  docker run -d --rm --network host --name ev-faust $(_pipe_env) -e WINDOW_SECONDS=15 \
    -v "$ROOT":/code -w /code --entrypoint faust $IMG \
    -A src.streaming.stream_processor worker -l warn >/dev/null
}

# $1 = run dir, $2 = replica model snapshot, $3 = NO_SHIELD (0/1), $4 = learn-out (optional)
start_ml() {
  local rd=$1 model=$2 noshield=$3 out=${4:-}
  cp "$model" "$rd/replica_model_start.pkl"
  docker run -d --rm --network host --name ev-engine $(_pipe_env) \
    -e REPLICA_MODEL_PATH=/code/${rd#$ROOT/}/replica_model_start.pkl \
    -e ANOMALY_MODEL_PATH=/code/data/anomaly_model_eval.pkl \
    -e DECISIONS_LOG=/code/${rd#$ROOT/}/decisions.log \
    ${out:+-e REPLICA_MODEL_OUT=/code/${out#$ROOT/}} \
    -v "$ROOT":/code -w /code $IMG src/decision/decision_engine.py >/dev/null
  if [[ "$noshield" != "skip" ]]; then
    docker run -d --rm --network host --name ev-actuator $(_pipe_env) \
      -e NO_SHIELD=$noshield -e SHIELD_POLICY=/code/specs/safety_policy_v2.yaml \
      -e OPERATOR_ACTIONS_LOG=/code/${rd#$ROOT/}/operator_actions.log \
      -e SHIELD_AUDIT_LOG=/code/${rd#$ROOT/}/safety_audit.log \
      -e CONSUMER_GROUP=act-$(basename "$rd") \
      -v "$HOME/.kube":/root/.kube:ro -v "$ROOT":/code -w /code $IMG \
      src/kopf_operator/actuator.py >/dev/null
  fi
}

start_mt() {
  local rd=$1
  docker run -d --rm --network host --name ev-mt $(_pipe_env) \
    -e MT_ACTIONS_LOG=/code/${rd#$ROOT/}/mt_actions.log -e CONSUMER_GROUP=mt-$(basename "$rd") \
    -v "$HOME/.kube":/root/.kube:ro -v "$ROOT":/code -w /code $IMG \
    src/baselines/rule_controller_live.py >/dev/null
}

start_op() {   # $1 op, $2 run dir
  local op=$1 rd=$2
  case $op in
    hpa)  kubectl apply -f "$L/manifests/hpa-eval.yaml" >/dev/null ;;
    keda) sed "s/__REQ_PER_REPLICA__/$REQ_PER_REPLICA/" "$L/manifests/keda-eval.yaml.tpl" | kubectl apply -f - >/dev/null ;;
    mt)        start_feature_pipeline; start_mt "$rd" ;;
    ml-only)   start_feature_pipeline; start_ml "$rd" "$ROOT/data/replica_model_eval.pkl" 1 ;;
    shield-ai) start_feature_pipeline; start_ml "$rd" "$ROOT/data/replica_model_eval.pkl" 0 ;;
    *) echo "unknown op $op"; return 1 ;;
  esac
}

# ---------------- load generator (in-cluster) ----------------
# $1 scenario, $2 seed, $3 duration, $4 out dir, $5 peak rps
run_load() {
  local sc=$1 seed=$2 dur=$3 out=$4 peak=${5:-$PEAK_RPS}
  kubectl -n loadgen create configmap locustfile --from-file="$L/locust_scenarios.py" \
    --dry-run=client -o yaml | kubectl apply -f - >/dev/null
  kubectl -n loadgen delete pod locust --ignore-not-found --wait=true >/dev/null
  cat <<EOF | kubectl apply -f - >/dev/null
apiVersion: v1
kind: Pod
metadata: { name: locust, namespace: loadgen }
spec:
  restartPolicy: Never
  nodeSelector: { tier: infra }
  containers:
    - name: locust
      image: $IMG
      imagePullPolicy: Never
      command: ["sh","-c"]
      args: ["locust -f /lf/locust_scenarios.py --headless --host http://podinfo.podinfo.svc:9898 --csv /out/run --csv-full-history --only-summary > /out/locust.log 2>&1; touch /out/DONE; sleep 900"]
      env:
        - { name: SCENARIO, value: "$sc" }
        - { name: SEED, value: "$seed" }
        - { name: DURATION, value: "$dur" }
        - { name: PEAK_RPS, value: "$peak" }
      resources: { requests: { cpu: "1" } }
      volumeMounts: [{ name: lf, mountPath: /lf }, { name: out, mountPath: /out }]
  volumes:
    - { name: lf, configMap: { name: locustfile } }
    - { name: out, emptyDir: {} }
EOF
  kubectl -n loadgen wait --for=condition=Ready pod/locust --timeout=120s >/dev/null
  echo "$(date +%s)" > "$out/load_start_epoch"
}

wait_load_and_collect() {   # $1 out dir
  local out=$1
  until kubectl -n loadgen exec locust -- test -f /out/DONE 2>/dev/null; do sleep 5; done
  for f in run_stats.csv run_stats_history.csv run_failures.csv locust.log; do
    kubectl -n loadgen cp locust:/out/$f "$out/$f" >/dev/null 2>&1 || true
  done
  kubectl -n loadgen delete pod locust --wait=false >/dev/null
}

# ---------------- replica sampler ----------------
start_sampler() {   # $1 out dir ; samples spec/ready replicas every 2 s
  local out=$1
  ( echo "epoch,spec_replicas,ready_replicas" > "$out/replicas.csv"
    while true; do
      r=$(kubectl -n $NS get deploy podinfo -o jsonpath='{.spec.replicas},{.status.readyReplicas}' 2>/dev/null || echo ",")
      echo "$(date +%s),$r" >> "$out/replicas.csv"; sleep 2
    done ) &
  echo $! > "$out/.sampler.pid"
}
stop_sampler() { kill "$(cat "$1/.sampler.pid")" 2>/dev/null || true; rm -f "$1/.sampler.pid"; }
