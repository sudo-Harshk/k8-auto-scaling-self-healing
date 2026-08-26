"""Locust test for workload-v2 (DB-backed Flask + SQLite).

Run from repo root with the v2 port-forward active:
    docker run --rm --network host -v $PWD:/code -w /code \
        --entrypoint locust k8-ai-ops:dev -f scripts/locustfile_v2.py \
        --headless -u N -r 20 -t Ts --host=http://localhost:8080
"""
from locust import HttpUser, task, between


class V2User(HttpUser):
    """User behavior for the v2 DB-backed workload."""
    wait_time = between(0.05, 0.2)

    @task(5)
    def query_count(self):
        self.client.get("/api/query?type=count")

    @task(5)
    def query_stats(self):
        self.client.get("/api/query?type=stats")

    @task(3)
    def query_top(self):
        self.client.get("/api/query?type=top")

    @task(2)
    def write(self):
        self.client.post(
            "/api/write",
            json={"kind": "scale", "value": 42.5},
        )

    @task(1)
    def index(self):
        self.client.get("/")
