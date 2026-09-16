#!/usr/bin/env python3
"""
scripts/eval/export_graphs.py — STUB

Generates paper figures (latency/replicas/decisions) from the live pipeline
output. The full implementation reads from Kafka topics populated by the
decision engine during a live demo run.

For the golden-run demo (which uses pre-recorded evidence), this stub
ensures the output directory exists so `make stats` can proceed.
"""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Export graphs from live pipeline.")
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for generated figures",
    )
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    print(
        "[export_graphs] stub: output dir created at "
        f"{out} — real figures require a live pipeline run",
        file=sys.stdout,
    )
    print(
        "For the golden-run demo, `make stats` (step 12) reads directly "
        "from results_N10/ which is pre-populated.",
        file=sys.stdout,
    )


if __name__ == "__main__":
    main()
