#!/usr/bin/env python3
"""
scripts/build_deck.py — Generate the 20-slide SHIELD-AI defense deck (PDF).

Used for the M.Tech viva defense. One slide per major talking point,
following the locked thesis sentence and the viva gauntlet.

Usage:
    python scripts/build_deck.py --output defense_deck.pdf

Output: 20 PDF pages, one per slide. Each slide has:
  - Title (top, bold)
  - Body content (text + tables + bullets)
  - Page number (bottom-right)
  - Slide footer with citation source

No external LaTeX dependency. Uses reportlab (already in requirements).
"""
from __future__ import annotations

import argparse
import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def build_styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "DeckTitle",
        parent=base["Heading1"],
        fontSize=28,
        leading=32,
        textColor=colors.HexColor("#0a3d62"),
        spaceAfter=14,
    )
    h2 = ParagraphStyle(
        "DeckH2",
        parent=base["Heading2"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0a3d62"),
        spaceAfter=10,
    )
    body = ParagraphStyle(
        "DeckBody",
        parent=base["BodyText"],
        fontSize=14,
        leading=18,
        spaceAfter=6,
    )
    bullet = ParagraphStyle(
        "DeckBullet",
        parent=body,
        leftIndent=18,
        bulletIndent=4,
        fontSize=14,
        leading=18,
    )
    caption = ParagraphStyle(
        "DeckCaption",
        parent=base["Italic"],
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#3c6382"),
        spaceAfter=4,
    )
    quote = ParagraphStyle(
        "DeckQuote",
        parent=body,
        fontName="Helvetica-Oblique",
        fontSize=15,
        leading=20,
        leftIndent=30,
        rightIndent=30,
        spaceAfter=10,
    )
    code = ParagraphStyle(
        "DeckCode",
        parent=base["Code"],
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#2c3e50"),
        backColor=colors.HexColor("#ecf0f1"),
        leftIndent=10,
        rightIndent=10,
        spaceAfter=4,
    )
    return {
        "title": title,
        "h2": h2,
        "body": body,
        "bullet": bullet,
        "caption": caption,
        "quote": quote,
        "code": code,
    }


SLIDES: list[dict] = [
    {
        "title": "SHIELD-AI",
        "subtitle": "A Formally-Verified Online Learning Controller for Safe Kubernetes Auto-Scaling and Self-Healing",
        "author": "sudo-Harshk",
        "advisor": "[Supervisor Name]",
        "footer": "M.Tech Thesis Defense - 2026-09-01",
    },
    {
        "title": "The locked thesis sentence",
        "body_kind": "quote",
        "body": (
            "Naive ML-based Kubernetes controllers are unsafe under burst load. "
            "SHIELD-AI combines online ML (River) with a formally-verified safety "
            "shield (TLA+) to retain ML adaptability while provably satisfying "
            "safety invariants that bare controllers violate."
        ),
        "footer": "Source: tasks/THESIS.md:3-7",
    },
    {
        "title": "Why now? The Day-15 motivating failure",
        "body_kind": "table",
        "body": [
            ["Operator", "Scaling lag (s)", "Error rate (%)", "Replicas (start -> end)"],
            ["HPA", "15", "0.0", "2 -> 6"],
            ["KEDA", "5", "0.0", "2 -> 2"],
            ["AI (Day-15, no shield)", "90", "69.2", "2 -> 2"],
        ],
        "callout": (
            "The ML-only operator was WORSE than HPA under burst load: "
            "it emitted a single heal action and never scaled."
        ),
        "footer": "Source: docs/thesis/02_introduction.md:30-37; docs/thesis/07_results.md",
    },
    {
        "title": "Two defects caused the Day-15 failure",
        "body_kind": "bullets",
        "body": [
            "Ordering bug: decision engine checked heal before scale. Under burst "
            "load, anomaly detector flagged high p95 as anomalous, engine emitted heal, "
            "scale was never called.",
            "No online learning: _run_online never called .learn_one(). The Day-7 "
            "offline model was frozen for 8 days, never adapting to live traffic.",
            "Combined effect: ML-only controller stuck at 2 replicas with 69% error "
            "rate while HPA scaled correctly.",
        ],
        "footer": "Source: src/decision/decision_engine.py:50-95 (P1 fix)",
    },
    {
        "title": "SHIELD-AI architecture",
        "body_kind": "bullets",
        "body": [
            "Prometheus (10 s) -> Kafka (k8s-metrics) -> Faust 30-s windows",
            "-> Kafka (k8s-features) -> Decision Engine (River HTR + HalfSpaceTrees)",
            "-> Safety Shield (TLA+ verified, 6 invariants) -> Kafka (k8s-decisions)",
            "-> Operator (Kafka consumer + K8s actuator, re-validates)",
            "-> workload-v2 Deployment (scale or heal)",
        ],
        "footer": "Source: docs/thesis/05_proposed_system.md:9-51; docs/paper/main.tex",
    },
    {
        "title": "Why River Hoeffding Adaptive Tree Regressor?",
        "body_kind": "bullets",
        "body": [
            "Online learning on a stream: one-pass, O(memory), no GPU, no minibatch",
            "Concept drift: tree adapts split criteria online; a frozen neural net does not",
            "Explainability: leave-one-out perturbation gives defensible answer to "
            "\"why did the controller scale here?\"",
            "Rejected alternatives:",
            "  - scikit-learn Random Forest (offline; would need full retrain on drift)",
            "  - PyTorch neural net (GPU unavailable on single-node kind cluster)",
            "  - RL (PPO on replica count; out of M.Tech scope, needs simulation env)",
        ],
        "footer": "Source: docs/thesis/05_proposed_system.md:115-130",
    },
    {
        "title": "Decision rule - load-first ordering (P1 fix)",
        "body_kind": "code",
        "body": (
            "if predicted_replicas != current_replicas:\n"
            "    action = 'scale'        # load is dominant\n"
            "elif anomaly_score > 2 * threshold:\n"
            "    action = 'heal'\n"
            "else:\n"
            "    action = 'noop'\n"
            "\n"
            "# after every decision:\n"
            "engine.learn(features, current_replicas)   # online learn loop"
        ),
        "footer": "Source: src/decision/decision_engine.py:50-95",
    },
    {
        "title": "Safety Shield - the trust boundary",
        "body_kind": "table",
        "body": [
            ["Invariant", "What it enforces"],
            ["SafetyMinReplicas", "replicas >= 1"],
            ["SafetyMaxReplicas", "replicas <= 10"],
            ["SafetyScalingStep", "|delta| <= 2 per decision"],
            ["SafetyHealNoScale", "heal preserves replicas"],
            ["SafetyBoundedRate", "cooldown elapsed or no action pending"],
            ["LivenessEventuallyScaleUp", "sustained demand -> scale eventually"],
        ],
        "footer": "Source: specs/SafetyShield.tla:230-290; src/safety/safety_shield.py",
    },
    {
        "title": "ML+Shield composition - the central paper claim",
        "body_kind": "quote",
        "body": (
            "The closed-loop system is safe iff the shield is safe, regardless of "
            "ML oracle behavior."
        ),
        "sub": [
            "ML oracle modeled as thin non-deterministic abstraction: any (action, target) "
            "in 0..ML_OUTPUT_RANGE, including out-of-bounds and over-large-step.",
            "Two parallel paths in one module: SHIELD (production) and ML_Only (the bug).",
            "TLC verifies all six shield invariants hold on every reachable state of the "
            "joint spec AND the ML_Only path CAN violate MlSafetyMaxReplicas (3-step "
            "counterexample).",
            "Result: shield is NECESSARY and SUFFICIENT for safety.",
        ],
        "footer": "Source: specs/ML_Composition.tla; tlc_run_ml_composition.txt; tlc_run_ml_only_counterexample.txt",
    },
    {
        "title": "Shield in action - offline replay (225 decisions)",
        "body_kind": "table",
        "body": [
            ["Outcome", "Count", "%"],
            ["Allowed unchanged", "178", "79.1%"],
            ["Clamped (|delta|>2)", "47", "20.9%"],
            ["Rejected", "0", "0.0%"],
            ["Total", "225", "100%"],
        ],
        "sub": [
            "All 47 clamps are 5-10 -> 4 via max_scale_step=2.",
            "Shield never had to reject: ML already conservative (predicts 7 not 10).",
            "But clamping is the safety guarantee - no over-large step reaches K8s.",
        ],
        "footer": "Source: scripts/replay_shield.py; data/features_v2.csv",
    },
    {
        "title": "Live demo: pipeline + safety shield active",
        "body_kind": "table",
        "body": [
            ["Event", "Detail"],
            ["Producer", "publishes workload-v2 metrics every 10s to k8s-metrics"],
            ["Faust", "consumes k8s-metrics, emits 30-s windowed avg to k8s-features"],
            ["Decision engine", "consumes k8s-features, emits scale to k8s-decisions"],
            ["Actuator", "consumes k8s-decisions, validates, applies to Deployment"],
            ["Load (Locust)", "120 users, 941 req/s burst, 100% fail (DB contention)"],
            ["Result", "workload-v2 scaled 2 -> 1 -> 3 -> 5 over ~3 min"],
            ["Shield rejects", "every other action due to cooldown (30s remaining)"],
        ],
        "footer": "Source: logs/operator_actions_demo.log; logs/decisions_demo.log",
    },
    {
        "title": "Why TLA+, not just unit tests?",
        "body_kind": "bullets",
        "body": [
            "Unit tests: verify that the code passes test cases.",
            "TLA+: verify that the code is correct for every possible input (within bounds).",
            "Difference: 'tested' vs 'verified' - the shield's invariants hold on every "
            "reachable state, not just on the sample the tests happen to cover.",
            "Composition spec extends this: shield's safety holds for every possible "
            "ML oracle output, not just the ones in our test set.",
            "Industrial precedent: Amazon (DynamoDB, S3), Microsoft (Cosmos DB).",
        ],
        "footer": "Source: docs/thesis/03_literature_survey.md:30-50",
    },
    {
        "title": "Why Kafka, not in-memory bus?",
        "body_kind": "bullets",
        "body": [
            "Durability: if decision engine crashes, no metrics are lost.",
            "Audit trail: every decision is on a Kafka topic (logs/decisions.log).",
            "Replay: offline replay (scripts/replay_shield.py) reads from the same topic.",
            "Cost: ~10 ms per hop latency. Trade-off accepted for the safety claim.",
            "Alternative rejected: in-memory queue - no audit, no replay, no recovery.",
        ],
        "footer": "Source: docs/thesis/08_discussion.md:8-15",
    },
    {
        "title": "Why Kafka actuator, not Kopf CRD handler?",
        "body_kind": "bullets",
        "body": [
            "Simpler test surface: one process to test, not two (Kopf + CRD lifecycle).",
            "No requeue logic, no watcher, no CRD reconciliation.",
            "Decouples the operator from the cluster's CRD registry.",
            "Easier to formally model: operator's input is a Kafka topic.",
            "Decision documented in AMENDMENTS 2026-08-23.",
        ],
        "footer": "Source: src/kopf_operator/actuator.py; tasks/AMENDMENTS.md",
    },
    {
        "title": "Reproducibility - the single-command demo",
        "body_kind": "code",
        "body": (
            "# On a fresh VM:\n"
            "git clone git@github.com-personal:sudo-Harshk/k8-auto-scaling-self-healing.git\n"
            "cd k8-auto-scaling-self-healing\n"
            "make build-image && make load-image\n"
            "make deploy-kafka deploy-prometheus deploy-workload\n"
            "# port-forward Prometheus + Kafka (compose uses network_mode: host):\n"
            "kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring &\n"
            "kubectl port-forward svc/kafka 9094:9094 -n kafka &\n"
            "kubectl port-forward svc/workload-v2 8080:8080 -n workload-v2 &\n"
            "make pipeline-up\n"
            "docker run ... locust -f scripts/locustfile_v2.py --host=http://localhost:8080"
        ),
        "footer": "Source: Makefile; docs/GOLDEN_RUN.md; ops/compose/pipeline.yaml",
    },
    {
        "title": "Stats & tests (N=10 final evaluation)",
        "body_kind": "bullets",
        "body": [
            "53 unit tests pass on every commit (under 1 second).",
            "17 anti-drift tests on the Safety Shield - each intentionally violates one "
            "invariant and verifies the class catches it.",
            "N=10 head-to-head evaluation: 120 trials (10 seeds x 4 operators x 3 scenarios).",
            "Effect sizes with Cohen's d and 95% CI on every comparison metric.",
            "TLC: SafetyShield 273,702 states, ML_Composition 7.3M states, all clean.",
            "ML_Only counterexample: produces 3-step violation trace (proves shield needed).",
        ],
        "footer": "Source: tests/; results_N10/; specs/tlc_run_*.txt",
    },
    {
        "title": "Threats to validity",
        "body_kind": "bullets",
        "body": [
            "Single-node kind cluster (no multi-node scheduling realism).",
            "Single workload class (workload-v2, DB-backed Flask + SQLite).",
            "60-second cooldown limits scaling agility.",
            "Detection rate 55-65% on organic baseline (anomaly detector tuned for "
            "fault-injection patterns).",
            "SHIELD-AI cold-start under-predicts on early ramp-up rows.",
            "Single Kafka as point of failure.",
        ],
        "footer": "Source: docs/thesis/07_results.md (Threats); docs/paper/main.tex",
    },
    {
        "title": "Where we sit vs HPA, KEDA, FIRM",
        "body_kind": "table",
        "body": [
            ["Feature", "HPA", "KEDA", "FIRM", "SHIELD-AI"],
            ["Multi-signal fusion", "X", "+", "+", "+"],
            ["Anomaly-driven healing", "X", "X", "X", "+"],
            ["Formal safety (TLA+)", "X", "X", "X", "+ (6 invariants)"],
            ["Online learning", "X", "X", "X", "+ River"],
            ["Composition theorem", "X", "X", "X", "+"],
        ],
        "footer": "Source: docs/thesis/03_literature_survey.md:55-60",
    },
    {
        "title": "Three contributions (recap)",
        "body_kind": "bullets",
        "body": [
            "Hybrid ML + formal safety controller - K8s operator whose action space is "
            "the intersection of ML-driven decisions and a TLA+-verified invariant set.",
            "Empirically-validated failure mode of pure ML controllers - Day-15 N=3 "
            "evidence showing AI without the shield gets stuck at 2 replicas with 69% "
            "error (the motivating failure).",
            "Reproducible artifact - 53 unit tests, containerized make demo, full TLA+ "
            "TLC trace, FIRM-style ML baseline, live pipeline with Kafka actuator.",
        ],
        "footer": "Source: tasks/THESIS.md:9-13",
    },
    {
        "title": "Future work & questions",
        "body_kind": "bullets",
        "body": [
            "Production deployment: multi-node cluster, multi-tenant policies, HA Kafka.",
            "Concept drift monitoring: ADWIN on residual error of the replica predictor.",
            "Tighter TLA+: probabilistic safety bounds, multi-tenant fairness, leader-"
            "election fault tolerance.",
            "Beyond K8s: GPU allocation, edge workload placement, network QoS - same "
            "architecture (Kafka + Faust + River + TLA+ shield).",
            "",
            "Questions?",
        ],
        "footer": "Source: docs/thesis/09_conclusion.md:51-65",
    },
]


def render_slide(slide: dict, styles: dict, page_num: int):
    elements = []

    if "subtitle" in slide:
        elements.append(Spacer(1, 1.0 * inch))
        elements.append(Paragraph(slide["title"], styles["title"]))
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph(slide["subtitle"], styles["h2"]))
        elements.append(Spacer(1, 1.0 * inch))
        elements.append(Paragraph(slide["author"], styles["body"]))
        elements.append(Paragraph(slide["advisor"], styles["body"]))
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph(slide["footer"], styles["caption"]))
        return elements

    elements.append(Paragraph(slide["title"], styles["title"]))

    kind = slide.get("body_kind", "bullets")
    body = slide["body"]

    if kind == "bullets":
        for line in body:
            elements.append(Paragraph(f"* {line}", styles["bullet"]))
    elif kind == "quote":
        elements.append(Paragraph(f'<i>"{body}"</i>', styles["quote"]))
        for line in slide.get("sub", []):
            elements.append(Paragraph(f"* {line}", styles["bullet"]))
    elif kind == "table":
        t = Table(body, colWidths=[2.0 * inch, 4.0 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a3d62")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#3c6382")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(t)
        if "callout" in slide:
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph(f"<b>{slide['callout']}</b>", styles["body"]))
        for line in slide.get("sub", []):
            elements.append(Paragraph(f"* {line}", styles["bullet"]))
    elif kind == "code":
        code_html = body.replace("\n", "<br/>")
        elements.append(Paragraph(code_html, styles["code"]))

    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph(slide["footer"], styles["caption"]))
    return elements


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#3c6382"))
    canvas.drawRightString(
        doc.pagesize[0] - 0.5 * inch,
        0.3 * inch,
        f"Slide {doc.page}",
    )
    canvas.drawString(
        0.5 * inch,
        0.3 * inch,
        "SHIELD-AI - M.Tech Defense - 2026-09-01",
    )
    canvas.restoreState()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build SHIELD-AI defense deck (PDF)")
    parser.add_argument(
        "--output",
        default=os.path.join(os.getcwd(), "defense_deck.pdf"),
        help="Output PDF path (default: ./defense_deck.pdf)",
    )
    args = parser.parse_args(argv)

    styles = build_styles()
    doc = SimpleDocTemplate(
        args.output,
        pagesize=landscape((8.5 * inch, 11 * inch)),
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="SHIELD-AI Defense Deck",
        author="sudo-Harshk",
    )

    flow = []
    for i, slide in enumerate(SLIDES):
        flow.extend(render_slide(slide, styles, i + 1))
        flow.append(PageBreak())

    if flow and isinstance(flow[-1], PageBreak):
        flow.pop()

    doc.build(flow, onFirstPage=on_page, onLaterPages=on_page)
    print(f"Wrote {args.output} ({len(SLIDES)} slides)")


if __name__ == "__main__":
    main()
