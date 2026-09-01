# SHIELD-AI — Makefile
#
# One-command golden path for reviewers, viva defense, and CI.
# Each target is idempotent where possible; `make reset` returns to clean state.

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

CLUSTER       := k8-ai
IMAGE         := k8-ai-ops:dev
KAFKA_NS      := kafka
MON_NS        := monitoring
WORKLOAD_NS   := workload
KIND_CONFIG   := ops/kind/kind-cluster.yaml
RESULTS_DIR   := results_N10

# Detect host platform
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
  PLATFORM := linux
endif
ifeq ($(UNAME_S),Darwin)
  PLATFORM := darwin
endif

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Targets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# --------------------------------------------------------------- cluster

.PHONY: kind-up
kind-up: ## Create kind cluster
	kind create cluster --name $(CLUSTER) --config $(KIND_CONFIG)
	kubectl cluster-info

.PHONY: kind-down
kind-down: ## Delete kind cluster
	kind delete cluster --name $(CLUSTER)

.PHONY: reset
reset: kind-down ## Full reset: cluster + images + volumes
	docker rmi -f $(IMAGE) || true
	docker volume prune -f

# --------------------------------------------------------------- image

.PHONY: build-image
build-image: ## Build the shared Python image (3.11-slim)
	docker build -t $(IMAGE) -f ops/docker/Dockerfile .

.PHONY: load-image
load-image: build-image ## Load image into kind
	kind load docker-image $(IMAGE) --name $(CLUSTER)

# --------------------------------------------------------------- infra

.PHONY: deploy-kafka
deploy-kafka: ## Deploy Kafka (KRaft mode)
	kubectl apply -f ops/manifests/kafka/ -n $(KAFKA_NS) --validate=false
	kubectl wait --for=condition=ready pod -l app=kafka -n $(KAFKA_NS) --timeout=120s

.PHONY: deploy-prometheus
deploy-prometheus: ## Deploy Prometheus + Grafana via kube-prometheus-stack
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	helm repo update
	helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
	  --namespace $(MON_NS) --create-namespace -f ops/manifests/prometheus/values.yaml

.PHONY: deploy-workload
deploy-workload: ## Deploy podinfo (default) and workload-v2
	kubectl apply -f ops/manifests/workload/podinfo.yaml
	kubectl apply -f ops/manifests/workload/v2/

.PHONY: deploy-all
deploy-all: deploy-kafka deploy-prometheus deploy-workload ## Deploy all infra + workloads

# --------------------------------------------------------------- pipeline

.PHONY: pipeline-up
pipeline-up: ## Start the four pipeline processes
	docker compose -f ops/compose/pipeline.yaml up -d
	@echo "Pipeline started. Tail logs with: make pipeline-logs"

.PHONY: pipeline-down
pipeline-down: ## Stop the pipeline
	docker compose -f ops/compose/pipeline.yaml down

.PHONY: pipeline-logs
pipeline-logs: ## Tail pipeline logs
	docker compose -f ops/compose/pipeline.yaml logs -f --tail=100

# --------------------------------------------------------------- demo

.PHONY: load-baseline
load-baseline: ## Send baseline traffic (50 RPS, 5 min)
	locust -f scripts/locustfile.py --headless -u 50 -r 10 -t 300s --host http://localhost:9898

.PHONY: load-burst
load-burst: ## Send burst traffic (200 RPS, 5 min)
	locust -f scripts/locustfile.py --headless -u 200 -r 50 -t 300s --host http://localhost:9898

.PHONY: load-rampdown
load-rampdown: ## Send rampdown traffic (20 RPS, 3 min)
	locust -f scripts/locustfile.py --headless -u 20 -r 5 -t 180s --host http://localhost:9898

.PHONY: inject-fault
inject-fault: ## Inject podinfo fault (5xx)
	curl -X POST http://podinfo.$(WORKLOAD_NS):9898/fault_injection/enable

.PHONY: inject-unsafe
inject-unsafe: ## Force a deliberately unsafe ML output (test hook)
	python scripts/eval/inject_unsafe_decision.py

.PHONY: export-graphs
export-graphs: ## Export latency/replicas/decisions figures to $(RESULTS_DIR)/
	mkdir -p $(RESULTS_DIR)
	python scripts/eval/export_graphs.py --output $(RESULTS_DIR)

# --------------------------------------------------------------- end-to-end

.PHONY: demo
demo: ## Run the 12-step golden run end-to-end
	./scripts/demo/run_all.sh

.PHONY: eval
eval: ## Run N>=10 statistical evaluation (~3 hours)
	./scripts/eval/run_N10.sh

.PHONY: stats
stats: ## Generate statistical report from $(RESULTS_DIR)
	python scripts/eval/stats_report.py --input $(RESULTS_DIR)

# --------------------------------------------------------------- formal

.PHONY: tla
tla: ## Run TLC on the safety shield spec
	cd specs && tlc SafetyShield.tla -config SafetyShield.cfg

.PHONY: tla-composition
tla-composition: ## Run TLC on ML+shield composition spec
	cd specs && tlc ML_Composition.tla -config ML_Composition.cfg

# --------------------------------------------------------------- paper

.PHONY: paper
paper: ## Build IEEE paper PDF
	cd docs/paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex

.PHONY: thesis
thesis: ## Build M.Tech thesis PDF (pandoc from docs/thesis/)
	pandoc docs/thesis/*.md -o thesis.pdf --pdf-engine=xelatex -V geometry:margin=1in

.PHONY: deck
deck: ## Build 20-slide defense deck
	python scripts/build_deck.py --output defense_deck.pdf
