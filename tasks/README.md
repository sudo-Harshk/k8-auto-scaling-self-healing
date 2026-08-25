# AI-Driven Kubernetes Operator — 2-Week Build Plan

This folder contains day-by-day tasks to build the M.Tech project **"AI-Driven Kubernetes Operator for Unified Online Auto-Scaling and Auto-Healing"** in exactly two weeks.

## Locked-in Choices

| Decision | Choice |
|---|---|
| Team size | 1 person |
| Kubernetes cluster | kind (local, free) |
| Microservice benchmark | podinfo (stefanprodan/podinfo v6.14.1) |
| Stream processor | Faust |
| Operator framework | Python (kafka-python + kubernetes client; Kafka-driven actuator) |
| Online ML library | River-ML |
| Safety verification | TLA+ / PlusCal |
| Fault injection | podinfo built-in `/fault_injection/enable` (+ LitmusChaos fallback) |
| Final deliverable | Working prototype + thesis documentation |

## How to Use These Tasks

1. Open the file for the current day.
2. Read the **Aim**, **Requirements**, **Steps**, and **Outcome**.
3. Complete the steps in order.
4. Check off the day in the tracker below once the outcome is verified.

## Daily Checklist

- [x] Day 1 — Cluster & Workload Deployment
- [x] Day 2 — Monitoring Stack
- [x] Day 3 — Metrics API & Baseline Load Test
- [x] Day 4 — Kafka Streaming Pipeline
- [x] Day 5 — Faust Stream Processor
- [x] Day 6 — Feature Engineering & Dataset
- [x] Day 7 — Replica Prediction Model
- [x] Day 8 — Anomaly Detection Model
- [x] Day 9 — Decision Engine & SHAP Explainability
- [x] Day 10 — TLA+ Safety Shield Specification
- [x] Day 11 — Safety Shield Implementation
- [x] Day 12 — Kubernetes Operator (Kafka actuator)
- [x] Day 13 — End-to-End Integration & Chaos Testing
- [x] Day 14 — Evaluation, Dashboards & Final Documentation
- [x] Day 15 — Statistical Rigor, Liveness & Reproducibility
- [ ] Day 16 — p95 Variability Rework, IEEE Paper Draft, Dashboard

## Goal at the End of Week 2

A fully integrated pipeline that:

1. Collects real-time metrics from a podinfo deployment running on a local kind cluster.
2. Streams metrics through Kafka.
3. Processes them with Faust.
4. Predicts optimal replicas and detects anomalies using River-ML.
5. Generates explainable scaling/healing decisions with SHAP.
6. Validates every decision through a TLA+-verified Safety Shield.
7. Executes safe decisions via a Kopf-based Kubernetes Operator.
8. Demonstrates auto-scaling under load and auto-healing under chaos.
9. Produces evaluation metrics and updated thesis documentation.

Do not over-engineer. Each task is scoped to deliver exactly what the project needs.
