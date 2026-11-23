"""Load scenarios for the live evaluation (paper revision).

Runs INSIDE the cluster (namespace loadgen) against the podinfo Service, so
kube-proxy spreads requests over all ready replicas. (The previous harness
used `kubectl port-forward svc/podinfo`, which pins every connection to a
single pod and makes extra replicas useless.)

Each simulated user issues ~1 request/s (constant_pacing), so the number of
users equals the offered request rate. Every request has a 2 s timeout;
timeouts and non-2xx responses count as failures.

Environment:
    SCENARIO   spike | diurnal | bursty | constant | calibrate | train
    PEAK_RPS   offered load at the scenario peak (req/s)
    SEED       RNG seed for the per-run multiplicative noise (+-15 %, 10 s steps)
    DURATION   total seconds (default 360)
"""
from __future__ import annotations

import math
import os
import random

from locust import FastHttpUser, LoadTestShape, constant_pacing, task

SCENARIO = os.environ.get("SCENARIO", "spike")
PEAK = float(os.environ.get("PEAK_RPS", "200"))
SEED = int(os.environ.get("SEED", "1"))
DURATION = int(os.environ.get("DURATION", "360"))
NOISE = float(os.environ.get("NOISE", "0.15"))


class PodinfoUser(FastHttpUser):
    network_timeout = 2.0
    connection_timeout = 2.0
    wait_time = constant_pacing(1.0)

    @task(6)
    def home(self):
        self.client.get("/", name="GET /")

    @task(3)
    def info(self):
        self.client.get("/api/info", name="GET /api/info")

    @task(1)
    def echo(self):
        self.client.post("/api/echo", json={"msg": "x" * 256},
                         name="POST /api/echo")


def base_profile(t: float) -> float:
    """Fraction of PEAK offered at second t (before noise)."""
    if SCENARIO == "spike":
        # 60 s low, sudden jump to peak for 150 s, back to low for 150 s.
        return 0.15 if t < 60 or t >= 210 else 1.0
    if SCENARIO == "diurnal":
        # One smooth day-like cycle: 0.1 -> 1.0 -> 0.1 over DURATION.
        return 0.1 + 0.9 * 0.5 * (1 - math.cos(2 * math.pi * t / DURATION))
    if SCENARIO == "bursty":
        # Flash crowds: 45 s bursts every 90 s (oscillation stress test).
        return 1.0 if (t % 90) < 45 else 0.2
    if SCENARIO == "train":
        # Training trace (disjoint from the test scenarios): slow random walk.
        rng = random.Random(10_000 + int(t // 30))
        return 0.1 + 0.9 * rng.random()
    if SCENARIO == "constant":
        # Self-healing study: steady load (~4 replicas at r*); faults are injected separately.
        return 0.25
    if SCENARIO == "calibrate":
        # Staircase: +PEAK/10 every 30 s (used against a fixed replica count).
        return min(1.0, 0.1 * (1 + int(t // 30)))
    raise ValueError(SCENARIO)


class ScenarioShape(LoadTestShape):
    def __init__(self):
        super().__init__()
        self._rng = random.Random(SEED)
        self._noise = {}

    def _noise_at(self, t: float) -> float:
        if SCENARIO in ("calibrate",):
            return 1.0
        k = int(t // 10)
        if k not in self._noise:
            self._noise[k] = 1.0 + self._rng.uniform(-NOISE, NOISE)
        return self._noise[k]

    def tick(self):
        t = self.get_run_time()
        if t >= DURATION:
            return None
        users = max(1, int(round(PEAK * base_profile(t) * self._noise_at(t))))
        return users, max(50, users)  # spawn fast so steps are sharp
