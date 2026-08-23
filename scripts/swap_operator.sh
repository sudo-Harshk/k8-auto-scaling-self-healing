#!/usr/bin/env bash
# scripts/swap_operator.sh
#
# Disable one operator (HPA, KEDA, or AI) and enable another. Used by the
# Day-14 evaluation harness to run the same scenarios under each operator.
#
# Usage:
#   ./scripts/swap_operator.sh hpa    # disable everything else, enable HPA
#   ./scripts/swap_operator.sh keda   # disable HPA + AI, enable KEDA
#   ./scripts/swap_operator.sh ai     # disable HPA + KEDA, enable AI
#   ./scripts/swap_operator.sh status # show current operator state
#
# The AI operator = producer + Faust + decision engine + Safety Shield +
# operator running as Docker containers. To enable AI, start them with
# run_pipeline.sh; to disable, stop them with stop_all.sh.
#
# HPA = ops/manifests/podinfo-hpa.yaml. KEDA = kedacore/keda + ScaledObject.

set -euo pipefail

LOG() { printf '\033[1;34m[swap]\033[0m %s\n' "$*"; }
DIE() { printf '\033[1;31m[swap][FATAL]\033[0m %s\n' "$*" >&2; exit 1; }

CMD="${1:-status}"

show_status() {
  echo "== Current operator state =="
  HPA_ENAB=$([ "$(kubectl -n podinfo get hpa podinfo -o jsonpath='{.spec.minReplicas}' 2>/dev/null)" != "" ] && echo "ON" || echo "OFF")
  KEDA_DEPLOY=$(kubectl -n keda get deploy keda-operator 2>/dev/null | wc -l)
  AI_RUNNING=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -c -E '(ai-producer|faust-e2e|engine-e2e|operator-e2e)' || true)
  echo "  HPA:      $HPA_ENAB"
  echo "  KEDA:     $([[ "$KEDA_DEPLOY" -gt 0 ]] && echo "INSTALLED" || echo "NOT INSTALLED")"
  echo "  AI:       $AI_RUNNING container(s) running"
}

enable_hpa() {
  LOG "enabling HPA"
  kubectl -n podinfo scale deploy podinfo --replicas=2 || true
  kubectl apply -f ops/manifests/podinfo-hpa.yaml || true
  KEDA_ENABLED=$(kubectl -n keda get scaledobject -o name 2>/dev/null | wc -l)
  if [[ "$KEDA_ENABLED" -gt 0 ]]; then
    kubectl -n keda delete scaledobject --all 2>/dev/null || true
    LOG "  deleted KEDA ScaledObject(s)"
  fi
  ./scripts/stop_all.sh >/dev/null 2>&1 || true
}

enable_keda() {
  LOG "enabling KEDA"
  kubectl -n podinfo delete -f ops/manifests/podinfo-hpa.yaml 2>/dev/null || true
  if [[ ! "$(kubectl -n keda get deploy keda-operator 2>/dev/null)" ]]; then
    DIE "KEDA not installed. Run: helm install keda kedacore/keda -n keda --create-namespace"
  fi
  # Apply ScaledObject (defined in scripts/eval/keda-scaledobject.yaml)
  kubectl apply -f scripts/eval/keda-scaledobject.yaml 2>/dev/null || \
    DIE "scripts/eval/keda-scaledobject.yaml not found"
  ./scripts/stop_all.sh >/dev/null 2>&1 || true
}

enable_ai() {
  LOG "enabling AI operator"
  kubectl -n podinfo delete -f ops/manifests/podinfo-hpa.yaml 2>/dev/null || true
  KEDA_ENABLED=$(kubectl -n keda get scaledobject -o name 2>/dev/null | wc -l)
  if [[ "$KEDA_ENABLED" -gt 0 ]]; then
    kubectl -n keda delete scaledobject --all 2>/dev/null || true
  fi
  ./scripts/run_pipeline.sh
}

case "$CMD" in
  hpa)        enable_hpa ;;
  keda)       enable_keda ;;
  ai)         enable_ai ;;
  status|*)   show_status ;;
esac