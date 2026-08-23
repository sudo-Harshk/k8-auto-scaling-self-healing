"""Day 12 Kubernetes Operator: consume shielded decisions and apply them.

This operator closes the AI scaling loop:
  Prometheus -> Kafka producer -> Faust (30s windows) -> k8s-features
    -> Decision Engine -> Safety Shield -> k8s-decisions topic
    -> OPERATOR (this module) -> Kubernetes API (patch Deployment / delete pod)

The operator:
  - polls Kafka topic `k8s-decisions` for new decisions
  - re-runs SafetyShield.validate() on each (defense in depth: even if the
    upstream pipeline forgot a check, the operator enforces invariants)
  - for `action=scale`: patches `podinfo` Deployment spec.replicas
  - for `action=heal`: deletes a pod (uses optional `target_pod` field;
    falls back to highest-restart pod or oldest pod)
  - for `action=noop`: logs only, no API call
  - for `rejected` decisions: logs and skips
  - logs every action to logs/operator_actions.log (append-only JSONL)

Usage (VM, --network host so the operator reaches the host's kubeconfig and
Kafka port-forward):

    docker run -d --rm --network host --name operator \\
        -v $HOME/.kube:/root/.kube:ro \\
        -v $HOME/k8-auto-scaling-self-healing:/code \\
        -w /code k8-ai-ops:dev src/kopf_operator/actuator.py

Smoke test (publish a decision directly to Kafka):

    docker run --rm --network host -v $PWD:/code -w /code k8-ai-ops:dev \\
        src/kopf_operator/publish_decision.py --action scale --target 4 --current 2
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kafka import KafkaConsumer  # noqa: E402
from kubernetes import client, config, watch  # noqa: E402
from kubernetes.client.rest import ApiException  # noqa: E402

from src.safety.safety_shield import (  # noqa: E402
    Decision,
    RejectedDecision,
    SafetyShield,
)

LOG = logging.getLogger("operator")

DEFAULT_NAMESPACE = "podinfo"
DEFAULT_DEPLOYMENT = "podinfo"
DEFAULT_KAFKA_BOOTSTRAP = "localhost:9094"
DEFAULT_KAFKA_TOPIC = "k8s-decisions"
DEFAULT_AUDIT_LOG = ROOT / "logs" / "operator_actions.log"

ALLOWED_ACTIONS = {"scale", "heal", "noop"}


@dataclass
class OperatorAction:
    """Audit-log record for one applied (or attempted) action."""

    timestamp: str
    service: str
    action: str
    target_replicas: int
    current_replicas_before: int
    current_replicas_after: int | None
    applied: bool
    rejected_reason: str | None
    safety_modifications: list[str]
    api_call: str
    pod_name: str | None

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


class K8sOperator:
    """Actuates decisions on a Kubernetes cluster via the official client."""

    def __init__(
        self,
        namespace: str = DEFAULT_NAMESPACE,
        deployment: str = DEFAULT_DEPLOYMENT,
    ) -> None:
        try:
            config.load_kube_config()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"failed to load kubeconfig: {exc}") from exc
        self.apps_api = client.AppsV1Api()
        self.core_api = client.CoreV1Api()
        self.namespace = namespace
        self.deployment = deployment

    # --------------------------------------------------------------- queries

    def get_current_replicas(self) -> int:
        dep = self.apps_api.read_namespaced_deployment(
            name=self.deployment, namespace=self.namespace
        )
        return int(dep.spec.replicas or 0)

    def list_pods(self) -> list[Any]:
        return self.core_api.list_namespaced_pod(self.namespace).items

    def pick_pod_to_heal(self, target_pod: str | None = None) -> str | None:
        """Pick a pod to delete for the heal action.

        Priority:
          1. explicit `target_pod` from the decision (Day 13 fault-injection)
          2. pod with highest restart count
          3. oldest pod (fallback)
        """
        pods = self.list_pods()
        if not pods:
            return None
        if target_pod:
            for p in pods:
                if p.metadata.name == target_pod:
                    return target_pod
        candidates = sorted(
            pods,
            key=lambda p: (
                -(sum(c.restart_count or 0 for c in (p.status.container_statuses or [])),
                 p.metadata.creation_timestamp),
            ),
        )
        return candidates[0].metadata.name if candidates else None

    # --------------------------------------------------------------- actions

    def apply_scale(self, target_replicas: int) -> tuple[int, int]:
        """Returns (replicas_before, replicas_after)."""
        before = self.get_current_replicas()
        if before == target_replicas:
            return before, before
        body = {"spec": {"replicas": target_replicas}}
        self.apps_api.patch_namespaced_deployment(
            name=self.deployment,
            namespace=self.namespace,
            body=body,
        )
        # Read back after a brief settle (k8s API is eventually consistent).
        time.sleep(0.5)
        after = self.get_current_replicas()
        return before, after

    def apply_heal(self, target_pod: str | None) -> tuple[int, str | None]:
        pod_name = self.pick_pod_to_heal(target_pod)
        if pod_name is None:
            return self.get_current_replicas(), None
        self.core_api.delete_namespaced_pod(
            name=pod_name, namespace=self.namespace
        )
        return self.get_current_replicas(), pod_name


def decision_from_kafka(raw: dict) -> Decision:
    """Build a Decision dataclass from a Kafka message payload."""
    return Decision(
        service=raw.get("service", "podinfo"),
        action=raw.get("action", "noop"),
        target_replicas=int(raw.get("target_replicas", 0)),
        current_replicas=int(raw.get("current_replicas", 0)),
        reason=raw.get("reason", ""),
        explanation=raw.get("explanation", []),
        anomaly_score=float(raw.get("anomaly_score", 0.0)),
        predicted_replicas_raw=float(raw.get("predicted_replicas_raw", 0.0)),
        timestamp=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
        features=raw.get("features", {}),
    )


def record_action(audit_path: Path, action: OperatorAction) -> None:
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(action.to_json() + "\n")


def run_operator(
    shield: SafetyShield,
    op: K8sOperator,
    kafka_bootstrap: str,
    kafka_topic: str,
    audit_path: Path,
    *,
    once: bool = False,
) -> int:
    LOG.info("starting operator: bootstrap=%s topic=%s", kafka_bootstrap, kafka_topic)
    consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers=kafka_bootstrap,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="k8-operator",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    def _stop(*_):
        LOG.info("stopping consumer")
        consumer.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    LOG.info("listening for decisions on %s", kafka_topic)
    for message in consumer:
        raw = message.value
        try:
            decision = decision_from_kafka(raw)
        except Exception as exc:  # noqa: BLE001
            LOG.warning("bad decision payload: %s | raw=%s", exc, raw)
            continue

        # Re-run the Safety Shield (defense-in-depth: every action is gated)
        outcome = shield.validate(decision)

        if isinstance(outcome, RejectedDecision):
            LOG.warning(
                "decision REJECTED by safety shield: action=%s reason=%s",
                decision.action,
                outcome.reason,
            )
            record_action(
                audit_path,
                OperatorAction(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    service=decision.service,
                    action=decision.action,
                    target_replicas=decision.target_replicas,
                    current_replicas_before=decision.current_replicas,
                    current_replicas_after=None,
                    applied=False,
                    rejected_reason=outcome.reason,
                    safety_modifications=[],
                    api_call="rejected",
                    pod_name=None,
                ),
            )
            if once:
                break
            continue

        # Apply the (possibly clamped) shielded decision.
        if outcome.action == "scale":
            try:
                before, after = op.apply_scale(outcome.target_replicas)
                LOG.info(
                    "scale applied: %d -> %d (target=%d)",
                    before, after, outcome.target_replicas,
                )
                record_action(
                    audit_path,
                    OperatorAction(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        service=decision.service,
                        action="scale",
                        target_replicas=outcome.target_replicas,
                        current_replicas_before=before,
                        current_replicas_after=after,
                        applied=True,
                        rejected_reason=None,
                        safety_modifications=_extract_mods(outcome.reason),
                        api_call="patch_namespaced_deployment",
                        pod_name=None,
                    ),
                )
            except ApiException as exc:
                LOG.error("scale failed: %s", exc)

        elif outcome.action == "heal":
            target_pod = decision.features.get("target_pod") if decision.features else None
            try:
                before, pod_name = op.apply_heal(target_pod)
                LOG.info(
                    "heal applied: pod=%s replicas=%d",
                    pod_name or "(none)", before,
                )
                record_action(
                    audit_path,
                    OperatorAction(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        service=decision.service,
                        action="heal",
                        target_replicas=outcome.target_replicas,
                        current_replicas_before=before,
                        current_replicas_after=None,
                        applied=True,
                        rejected_reason=None,
                        safety_modifications=_extract_mods(outcome.reason),
                        api_call="delete_namespaced_pod",
                        pod_name=pod_name,
                    ),
                )
            except ApiException as exc:
                LOG.error("heal failed: %s", exc)

        elif outcome.action == "noop":
            LOG.info("noop: %s", outcome.reason)
            record_action(
                audit_path,
                OperatorAction(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    service=decision.service,
                    action="noop",
                    target_replicas=outcome.target_replicas,
                    current_replicas_before=decision.current_replicas,
                    current_replicas_after=decision.current_replicas,
                    applied=False,
                    rejected_reason=None,
                    safety_modifications=[],
                    api_call="none",
                    pod_name=None,
                ),
            )

        else:
            LOG.warning("unknown action: %s", outcome.action)

        if once:
            break

    consumer.close()
    return 0


def _extract_mods(reason: str) -> list[str]:
    if "safety_mods=" not in reason:
        return []
    try:
        tail = reason.split("safety_mods=", 1)[1]
        end = tail.find("]")
        if end >= 0:
            return [tail[: end + 1]]
    except Exception:  # noqa: BLE001
        pass
    return []


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    p = argparse.ArgumentParser()
    p.add_argument("--bootstrap", default=os.environ.get("KAFKA_BOOTSTRAP", DEFAULT_KAFKA_BOOTSTRAP))
    p.add_argument("--topic", default=DEFAULT_KAFKA_TOPIC)
    p.add_argument("--namespace", default=DEFAULT_NAMESPACE)
    p.add_argument("--deployment", default=DEFAULT_DEPLOYMENT)
    p.add_argument("--once", action="store_true",
                   help="process one decision then exit (smoke test)")
    args = p.parse_args()

    shield = SafetyShield()
    op = K8sOperator(namespace=args.namespace, deployment=args.deployment)
    LOG.info(
        "k8s connected: namespace=%s deployment=%s current_replicas=%d",
        args.namespace,
        args.deployment,
        op.get_current_replicas(),
    )

    return run_operator(
        shield=shield,
        op=op,
        kafka_bootstrap=args.bootstrap,
        kafka_topic=args.topic,
        audit_path=DEFAULT_AUDIT_LOG,
        once=args.once,
    )


if __name__ == "__main__":
    raise SystemExit(main())