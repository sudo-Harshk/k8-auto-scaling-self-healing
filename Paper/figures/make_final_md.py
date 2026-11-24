"""Derive SHIELD_AI_final.md (single-column, numbered-section layout of the
reference paper) from SHIELD_AI_revised.md. Content is unchanged except for
section numbering, caption style and an added pseudo procedure.
usage: python figures/make_final_md.py   (run from Paper/)
"""
import re
from pathlib import Path

src = Path("SHIELD_AI_revised.md").read_text(encoding="utf-8")
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
TITLES = {"Related Work": "Literature Review", "System Design": "Proposed Approach"}
LET = "ABCDEFGH"

PSEUDO = """
**Pseudo procedure.** The control loop of SHIELD-AI for one decision window is as follows:

```
Pseudo_Procedure SHIELD_AI_Window(features x_t, replicas R, policy P):
Input:  feature record x_t of the closed 15 s window, live replica count R
Output: applied action (scale / heal / noop) and an audit record
Step 1: Forecast
    1.1 y = HATR.predict(x_t)                      # replicas needed next window
    1.2 s = HST.score(x_t)                         # anomaly score in [0, 1]
Step 2: Localise a faulty pod (HEAL_MODE = outlier)
    2.1 for each pod p: read p95(p) and Ready(p) from Prometheus
    2.2 c = pod with p95(p) >= 3 * median(siblings) and p95(p) > SLO,
            or pod Running but not Ready while a sibling is Ready
    2.3 if c holds for 2 consecutive windows (and s > threshold when HEAL_GATE = anomaly):
            propose (heal, target = R, pod = c); go to Step 4
Step 3: Scale
    3.1 if y != R: propose (scale, target = y) else propose (noop)
Step 4: Shield (rules in TLA+ order; Listing 3)
    4.1 reject unknown actions; reject a change inside its cooldown (15 s up, 60 s down/heal)
    4.2 heal: force target = R
    4.3 scale: clamp the step (up <= max(4, R), down <= 2), then clamp to [2, 20]
Step 5: Actuate
    5.1 actuator re-reads the live R and re-validates the decision (defence in depth)
    5.2 patch spec.replicas (scale) or delete pod c (heal); append to the audit log
Step 6: Learn
    6.1 HATR.learn(x_{t-1}, demand(t)); HST.learn(x_t)
```
"""


def sec_ref(m):
    n = ROMAN[m.group(1)]
    return f"Section {n}" + (f".{LET.index(m.group(2)) + 1}" if m.group(2) else "")


out, major, minor = [], 0, 0
for ln in src.splitlines():
    if ln.startswith("> "):                      # editorial note, not part of the paper
        continue
    m = re.match(r"^## ([IVX]+)\. (.+)$", ln)
    if m:
        major = ROMAN[m.group(1)]; minor = 0
        out.append(f"## {major}. {TITLES.get(m.group(2), m.group(2))}"); continue
    m = re.match(r"^### ([A-H])\. (.+)$", ln)
    if m:
        minor += 1
        if major == 3 and m.group(1) == "C":     # pseudo procedure after the decision engine
            out.append(PSEUDO)
        out.append(f"### {major}.{minor} {m.group(2)}"); continue
    ln = re.sub(r"Section ([IVX]+)(?:-([A-H]))?\b", sec_ref, ln)
    ln = re.sub(r"Sections ([IVX]+)–([IVX]+)", lambda m: f"Sections {ROMAN[m.group(1)]}–{ROMAN[m.group(2)]}", ln)
    ln = re.sub(r"§([IVX]+)-([A-H])", lambda m: f"Section {ROMAN[m.group(1)]}.{LET.index(m.group(2)) + 1}", ln)
    ln = re.sub(r"^\*Fig\. (\d+) — (.+)\*$", r"*Fig \1. \2*", ln)
    ln = re.sub(r"^\*\*Table ([IVX]+) — (.+?)\*\*", r"**Table \1. \2**", ln)
    ln = re.sub(r"^\*\*Listing (\d+) — (.+?)\*\*", r"**Listing \1. \2**", ln)
    out.append(ln)

text = "\n".join(out) + "\n"
text = text.replace("**Index Terms** —", "**Keywords:**").replace("**Abstract** —", "**Abstract -**")
left = re.findall(r"Section [IVX]+\b", text)
assert not left, left
Path("SHIELD_AI_final.md").write_text(text, encoding="utf-8", newline="")
print("written SHIELD_AI_final.md")
