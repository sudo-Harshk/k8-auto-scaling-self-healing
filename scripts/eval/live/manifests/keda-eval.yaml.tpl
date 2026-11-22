# Baseline 2: KEDA, Prometheus request-rate trigger (target REQ_PER_REPLICA
# req/s per replica, the same capacity figure SHIELD-AI and MT use).
# __REQ_PER_REPLICA__ is substituted by run_matrix.sh after calibration.
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: { name: podinfo-keda, namespace: podinfo }
spec:
  scaleTargetRef: { name: podinfo }
  pollingInterval: 5
  cooldownPeriod: 60
  minReplicaCount: 2
  maxReplicaCount: 20
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleUp:
          stabilizationWindowSeconds: 0
          policies:
            - { type: Percent, value: 100, periodSeconds: 15 }
            - { type: Pods, value: 4, periodSeconds: 15 }
          selectPolicy: Max
        scaleDown:
          stabilizationWindowSeconds: 60
  triggers:
    - type: prometheus
      metadata:
        serverAddress: http://kube-prometheus-stack-prometheus.monitoring.svc.cluster.local:9090
        query: sum(rate(http_requests_total{namespace="podinfo"}[30s]))
        threshold: "__REQ_PER_REPLICA__"
