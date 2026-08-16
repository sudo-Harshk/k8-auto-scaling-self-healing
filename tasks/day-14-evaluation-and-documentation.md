# Day 14 — Evaluation, Dashboards & Final Documentation

## Task
Measure system performance, build an audit dashboard, and finalize the thesis report and presentation.

## Aim
Quantify the value of the AI-driven operator and produce the final M.Tech deliverables.

## Requirements

- Results from Day 13 testing
- Grafana access
- Locust reports
- Thesis template (Word/LaTeX/Google Docs)
- Original PPT file

## Steps

1. **Define evaluation metrics and SLOs**
   - Example SLOs:
     - p95 latency < 500 ms
     - Availability > 99%
     - CPU utilization between 40% and 80%
   - Define comparison scenarios:
     - Baseline: default HPA only
     - Proposed: your AI-driven operator

2. **Run comparison experiments**
   - Run the same Locust load profile twice:
     - Once with default HPA
     - Once with your AI operator active
   - Record p95 latency, availability, replica counts, and CPU usage.

3. **Analyze results**
   - Compute SLO compliance for both scenarios.
   - Show that your system adapts faster or maintains better SLOs.

4. **Build an audit dashboard**
   - Create a simple web page or Grafana dashboard showing:
     - Recent decisions
     - Approved vs rejected actions
     - Current replica counts
     - Anomaly scores

5. **Write final thesis sections**
   - Include:
     - Abstract
     - Introduction
     - Literature Survey
     - Existing System
     - Proposed System
     - System Architecture
     - Implementation
     - Results and Discussion
     - Conclusion and Future Work
     - References

6. **Update the PPT**
   - Add results, screenshots, and evaluation graphs.
   - Add a demo video or screenshots.

7. **Prepare a short demo script**
   - 5-minute walkthrough of the system.

## Outcome

- Evaluation table/graphs comparing default HPA vs AI operator.
- Audit dashboard showing decisions and system state.
- Completed thesis report.
- Updated project presentation.
- Demo script ready.

## Verification

Check that you can answer these questions with data:

- How much faster does your system scale compared to HPA?
- How quickly does it detect and heal a faulty pod?
- What percentage of decisions were approved by the Safety Shield?
- Did SLO compliance improve?
