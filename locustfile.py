# Locust load profile for the podinfo workload.
#
# Tasks (chosen to exercise HTTP request-rate, CPU, and error signals for the model):
#   - GET /            : podinfo home page (JS + JSON render; light CPU + 1 request)
#   - GET /api/info    : JSON metadata endpoint (small JSON, easy on CPU)
#   - POST /echo       : echo a small JSON body back (drives CPU on the server side)
#
# Run (via shared Docker image so we sidestep Locust+Python 3.12 Windows issues):
#   docker run --rm -v ${PWD}:/code -w /code \
#       --entrypoint locust k8-ai-ops:dev \
#       -f /code/locustfile.py \
#       --host http://host.docker.internal:8070 \
#       --headless -u 10 -r 1 -t 300s
#
# Or interactive (web UI on http://localhost:8089):
#   docker run --rm -p 8089:8089 -v ${PWD}:/code -w /code \
#       --entrypoint locust k8-ai-ops:dev \
#       -f /code/locustfile.py --host http://host.docker.internal:8070
from __future__ import annotations

import json
import random
import string

from locust import HttpUser, between, task


def _random_tag() -> str:
    """Random 8-char tag used in the /echo body; keeps Locust requests distinct."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


class PodinfoUser(HttpUser):
    """Simulated user hitting the podinfo web app."""

    # Brief pause between requests (1-3s) keeps request rate stable and humane.
    wait_time = between(1, 3)

    @task(5)
    def home(self) -> None:
        """Hit the home page (most-common user action -> high weight)."""
        self.client.get("/", name="GET /")

    @task(3)
    def api_info(self) -> None:
        """Fetch JSON metadata - drives request-rate with little CPU."""
        self.client.get("/api/info", name="GET /api/info")

    @task(2)
    def echo(self) -> None:
        """POST a small JSON body to /api/echo - drives a bit of server CPU."""
        body = {"msg": "hello from locust", "tag": _random_tag()}
        with self.client.post(
            "/api/echo",
            data=json.dumps(body),
            headers={"Content-Type": "application/json"},
            name="POST /api/echo",
            catch_response=True,
        ) as resp:
            # podinfo's /api/echo returns 2xx (typically 202 Accepted) and echoes
            # the body; flag any non-2xx as an anomaly.
            if not (200 <= resp.status_code < 300):
                resp.failure(f"unexpected status {resp.status_code}")