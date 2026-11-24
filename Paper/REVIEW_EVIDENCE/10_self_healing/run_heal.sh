#!/usr/bin/env bash
# Self-healing study: gray-failure injection under constant load.
#
# Fault (hung process): at FAULT_AT s after load start, the podinfo process of
# one pod (chosen with the seed) is frozen with SIGSTOP, sent from the kind node
# (a container's PID 1 ignores SIGSTOP from inside its own namespace). Requests
# to the pod hang, its readiness probe fails and Kubernetes removes it from the
# Service; with no liveness probe it is never replaced, so the lost capacity
# persists until the pod is deleted.
# (Two pilot runs with an in-pod CPU hog did not degrade service and were not
#  visible in podinfo's handler-time histogram; see heal_pilot_v1 / pilot seed 98.)
#
# Arms:  shield-heal   SHIELD-AI, heal on pod localisation (HEAL_GATE=none)
#        shield-heal-gated SHIELD-AI, heal also gated by the anomaly score
#        shield-noheal SHIELD-AI with HEAL_MODE=off   (ablation)
#        hpa           Kubernetes HPA                 (baseline)
# Each arm runs with FAULT=1 and FAULT=0 (false-heal control).
#
#   SEEDS="1 2 3 4 5" bash scripts/eval/live/run_heal.sh
source "$(dirname "$0")/lib.sh"
ARMS="${ARMS:-shield-heal shield-heal-gated shield-noheal hpa}"
FAULTS="${FAULTS:-1 0}"
SEEDS="${SEEDS:-1 2 3 4 5}"
DUR="${DURATION:-300}"
FAULT_AT="${FAULT_AT:-60}"
START_R="${START_R:-4}"
RES="$ROOT/results_live/heal_runs"; mkdir -p "$RES"

LOG "self-healing study: arms=[$ARMS] faults=[$FAULTS] seeds=[$SEEDS] dur=${DUR}s fault_at=${FAULT_AT}s"
port_forwards

inject_fault() {   # $1 run dir, $2 seed
  local rd=$1 seed=$2
  sleep "$FAULT_AT"
  # Running pods that are not terminating (a terminating pod has no container to freeze)
  mapfile -t pods < <(kubectl -n $NS get pods -l app=podinfo --field-selector=status.phase=Running \
                        -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.metadata.deletionTimestamp}{"\n"}{end}' \
                      | awk 'NF==1{print $1}' | sort)
  local n=${#pods[@]} i pod node cid pid
  for (( i=0; i<n; i++ )); do              # seed picks the first candidate; skip any without a container
    pod=${pods[$(( (seed + i) % n ))]}
    node=$(kubectl -n $NS get pod "$pod" -o jsonpath='{.spec.nodeName}')
    cid=$(docker exec "$node" crictl ps -q --name podinfo --pod "$(docker exec "$node" crictl pods -q --name "$pod")")
    [[ -n $cid ]] && break
  done
  if [[ -z $cid ]]; then LOG "fault injection FAILED (no running container); run is invalid"; return 1; fi
  pid=$(docker exec "$node" crictl inspect --output go-template --template '{{.info.pid}}' "$cid")
  docker exec "$node" kill -STOP "$pid" || { LOG "fault injection FAILED (kill)"; return 1; }
  printf '{"epoch": %s, "pod": "%s", "pods_at_injection": %s}\n' \
    "$(date +%s)" "$pod" "${#pods[@]}" > "$rd/fault.json"
}

for seed in $SEEDS; do
  combos=()
  for a in $ARMS; do for f in $FAULTS; do
    [[ $a == shield-heal-gated && $f == 0 ]] && continue   # gated arm: fault runs only
    combos+=("$a:$f"); done; done
  mapfile -t combos < <(printf '%s\n' "${combos[@]}" | shuf --random-source=<(yes $seed))
  for c in "${combos[@]}"; do
    arm=${c%%:*}; fault=${c##*:}
    rd="$RES/${arm}__f${fault}__s${seed}"
    [[ -f "$rd/DONE" ]] && { LOG "skip $rd"; continue; }
    rm -rf "$rd"; mkdir -p "$rd"
    LOG "=== arm=$arm fault=$fault seed=$seed"
    pgrep -f "port-forward.*9094" >/dev/null || port_forwards
    stop_all_ops
    # remove pods left frozen (unready) by a previous run so every run starts healthy
    kubectl -n $NS get pods -l app=podinfo --no-headers \
      | awk '$2!="1/1"{print $1}' | xargs -r kubectl -n $NS delete pod --wait=true >/dev/null 2>&1 || true
    reset_workload
    kubectl -n $NS scale deploy podinfo --replicas=$START_R >/dev/null
    kubectl -n $NS rollout status deploy/podinfo --timeout=180s >/dev/null
    sleep 20
    case $arm in
      shield-heal)   HEAL_MODE=outlier HEAL_GATE=none    start_op shield-ai "$rd" ;;
      shield-heal-gated) HEAL_MODE=outlier HEAL_GATE=anomaly start_op shield-ai "$rd" ;;
      shield-noheal) HEAL_MODE=off     start_op shield-ai "$rd" ;;
      hpa)           start_op hpa "$rd" ;;
    esac
    sleep 25
    start_sampler "$rd"
    run_load constant "$seed" "$DUR" "$rd"
    fpid=""
    if [[ "$fault" == 1 ]]; then inject_fault "$rd" "$seed" & fpid=$!; fi
    wait_load_and_collect "$rd"
    [[ -n "$fpid" ]] && wait "$fpid" 2>/dev/null || true
    sleep 5; stop_sampler "$rd"
    kubectl -n $NS get pods -l app=podinfo -o json > "$rd/pods_end.json"
    kubectl -n $NS get events --sort-by=.lastTimestamp -o custom-columns=T:.lastTimestamp,R:.reason,O:.involvedObject.name,M:.message > "$rd/events.txt" 2>/dev/null || true
    stop_all_ops
    printf 'arm=%s\nfault=%s\nseed=%s\nduration=%s\nfault_at=%s\nstart_replicas=%s\nslo_ms=%s\n' \
      "$arm" "$fault" "$seed" "$DUR" "$FAULT_AT" "$START_R" "$SLO_MS" > "$rd/meta.env"
    touch "$rd/DONE"
  done
done
# remove any pod still carrying a fault
kubectl -n $NS rollout restart deploy/podinfo >/dev/null; reset_workload
LOG "self-healing study finished -> $RES"
