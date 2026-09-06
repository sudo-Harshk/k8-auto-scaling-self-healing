"""Phase 5 audit: every concrete number in main.tex (Abstract + main body)
must trace to evidence-freeze.md sections A-L.

Strategy:
  1. Extract all numeric literals (decimals, percentages, counts) from main.tex
     excluding the bibliography section.
  2. Read evidence-freeze.md and search for each number.
  3. Print a table: number, occurs in EF?, status.

Run from repo root: `python scripts/_phase5_audit.py`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "docs" / "paper" / "main.tex"
EF = ROOT / "evidence-freeze.md"


def extract_numbers(text: str) -> list[str]:
    """Extract all numbers from LaTeX text.

    Matches:
      - integers (0..9+)
      - decimals (1.234, 0.48, 273,702, 1,486,782, etc.)
      - percentages as standalone numbers preceding %
      - skipping LaTeX noise: section labels, citation numbers, bibitem indices
    """
    candidates = set()
    # decimal numbers with optional thousands separator
    for m in re.finditer(r"([\d]{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)", text):
        candidates.add(m.group(1))
    return sorted(candidates, key=lambda s: (-len(s), s))


def main() -> int:
    if not TEX.exists():
        print(f"ERROR: {TEX} missing")
        return 1
    if not EF.exists():
        print(f"ERROR: {EF} missing")
        return 1

    tex = TEX.read_text(encoding="utf-8")
    # Drop everything from \bibliography onwards (no claim numbers there)
    bib_idx = tex.find("\\bibliography{")
    main_body = tex[:bib_idx] if bib_idx > 0 else tex

    ef = EF.read_text(encoding="utf-8")

    print(f"main.tex size: {len(tex)} chars")
    print(f"main body (pre-bibliography): {len(main_body)} chars")
    print(f"evidence-freeze.md size: {len(ef)} chars")
    print()

    nums = extract_numbers(main_body)
    print(f"Distinct numbers in main body: {len(nums)}")
    print()

    # Filter out: cite-key years, structural numbers, derived values.
    STRUCTURAL_LITERALS = {
        "1", "2", "3", "4", "5", "6", "7", "8", "9",  # Section list
        "1994", "2001", "2010", "2011", "2015", "2016",
        "2018", "2020", "2023", "2024", "2025", "2026",  # cite years
        "262", "268", "283",  # line numbers in code citation
        "24", "04",  # Ubuntu version subcomponents
        "500", "1000",  # text examples (HTTP 500s, ms)
    }

    # Derived values that the reader can recompute and that we don't
    # need a direct evidence-freeze line for, because the components
    # are in evidence-freeze.md:
    DERIVED_OK = {
        "0.968":  "2 * 0.484 (anomaly threshold) -> heal gate; component 0.484 is in EF",
        "24.04":  "Ubuntu release version; documented in README.md:50, not a result",
        "500":    "HTTP 500 status code as a NAME for failures, not a measurement",
        "3.3":    "TLC fp probability 3.3E-8 from tlc_run_safety_shield.txt:26",
    }

    # For each number, check whether it appears literally in EF.
    # If a number appears in both main and EF, it's authoritative.
    # If it appears in main but NOT in EF, flag as UNSOURCED.
    # If it appears in both, flag as sourced.
    # Common citations numbers like "273,702" or "1,486,782" appear
    # both in `\$273{,}702\$` LaTeX format and in EF plain.
    unsourced: list[tuple[str, str]] = []
    sourced: list[tuple[str, str]] = []

    # Strip LaTeX formatting from a number for matching
    # `\num{273,702}` -> 273702 ; `273,702` -> 273702
    def normalize(s: str) -> str:
        s = s.replace("\\,", "")
        s = s.replace("{,}", "")
        s = s.replace(",", "")
        s = re.sub(r"[^0-9.\-]", "", s)
        return s.strip(".")

    # Find the surrounding context of each number in main for the table
    def context(s: str, text: str, ctx_chars: int = 60) -> str:
        idx = text.find(s)
        if idx < 0:
            return text[: ctx_chars].replace("\n", " ")
        a = max(0, idx - ctx_chars)
        b = min(len(text), idx + len(s) + ctx_chars)
        snippet = text[a:b].replace("\n", " ")
        return f"...{snippet}..."

    for n in nums:
        n_norm = normalize(n)
        if not n_norm or n_norm.lstrip("-") == "":
            continue
        if n_norm in STRUCTURAL_LITERALS:
            continue
        if n_norm in DERIVED_OK:
            continue

        present_in_ef = n_norm in ef.replace(",", "")
        ctx = context(n, main_body)

        if present_in_ef:
            sourced.append((n_norm, ctx))
        else:
            unsourced.append((n_norm, ctx))

    print(f"SOURCED (in both main + EF): {len(sourced)}")
    print(f"UNSOURCED (in main, NOT in EF): {len(unsourced)}")
    print()

    if unsourced:
        print("=" * 60)
        print("UNSOURCED NUMBERS (would be a fabrication flag)")
        print("=" * 60)
        for n, c in unsourced[:200]:
            note = " (DERIVED/component in EF)" if n in DERIVED_OK else ""
            print(f"  {n!r:>16s}{note}  in context: {c[:90]}")
        print()

    if sourced:
        print("=" * 60)
        print("SOURCED NUMBERS (sample, first 40)")
        print("=" * 60)
        for n, c in sourced[:40]:
            print(f"  {n!r:>16s}  context: {c[:90]}")

    return 1 if unsourced else 0


if __name__ == "__main__":
    sys.exit(main())
