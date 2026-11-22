"""Micro-benchmark: latency added by SafetyShield.validate() (v2 policy).

Random untrusted proposals (action mix 80 % scale / 10 % heal / 10 % noop,
targets 0..25, current 2..20). Audit logging ON (as in production).
"""
import json, random, statistics, sys, tempfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
from src.safety.safety_shield import Decision, SafetyShield

def main(n=20000):
    tmp = Path(tempfile.mkdtemp()) / "audit.log"
    sh = SafetyShield(policy_path=ROOT / "specs/safety_policy_v2.yaml", audit_log_path=tmp)
    rng = random.Random(42); lat = []
    for _ in range(n):
        a = rng.choices(["scale", "heal", "noop"], [8, 1, 1])[0]
        c = rng.randint(2, 20)
        d = Decision(service="podinfo", action=a, target_replicas=rng.randint(0, 25) if a == "scale" else c,
                     current_replicas=c, reason="bench")
        t = time.perf_counter_ns(); sh.validate(d, bypass_cooldown=(rng.random() < 0.5)); lat.append((time.perf_counter_ns() - t) / 1000)
    lat.sort()
    res = {"n": n, "mean_us": statistics.mean(lat), "p50_us": lat[n // 2], "p95_us": lat[int(n * .95)],
           "p99_us": lat[int(n * .99)], "max_us": lat[-1], "audit_logging": True}
    print(json.dumps(res, indent=2)); return res

if __name__ == "__main__":
    r = main(); Path(sys.argv[1] if len(sys.argv) > 1 else "results_live/shield_overhead.json").write_text(json.dumps(r, indent=2))
