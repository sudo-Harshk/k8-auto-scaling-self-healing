"""Recount the 28-proposal stress audit (lines 1-28 of logs/safety_audit.log)."""
import json, sys
p = sys.argv[1] if len(sys.argv) > 1 else "safety_audit_first28.log"
rows = [json.loads(l) for l in open(p, encoding="utf-8")][:28]
mod = rej = ok = 0; reasons = {}
for i, r in enumerate(rows, 1):
    if r["rejected"]:
        rej += 1; why = " ".join(r["modifications"]) or r["outcome"].get("reason", "")
        k = "cooldown" if "cooldown" in why.lower() else r["input"]["action"]
        reasons[k] = reasons.get(k, 0) + 1; tag = f"REJECTED ({k})"
    elif r["modifications"]:
        mod += 1; tag = "MODIFIED " + ",".join(r["modifications"])
    else:
        ok += 1; tag = "passed unchanged"
    print(f"{i:2d} {r['input']['action']:9s} target={r['input']['target_replicas']}: {tag}")
print(f"\nmodified={mod} rejected={rej} {reasons} passed={ok}  -> corrected {mod+rej}/28")

# Per-rule breakdown (a proposal can trigger more than one rule)
import re
rule = {}
for r in rows:
    names = set()
    for m in r["modifications"]:
        names.add(re.match(r"[a-z_]+", m).group(0))
    if r["rejected"]:
        why = (" ".join(r["modifications"]) + " " + r["outcome"].get("reason", "")).lower()
        names = {"cooldown"} if "cooldown" in why else {"unknown_action:" + r["input"]["action"]}
    for n in names:
        rule[n] = rule.get(n, 0) + 1
print("per-rule:", dict(sorted(rule.items())))
