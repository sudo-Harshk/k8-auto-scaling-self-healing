"""Day 16 - DB-backed workload to replace podinfo.

A minimal Flask app backed by SQLite, exposing three endpoints that
exhibit varying p95 latency under load:

  GET  /            - render index template (in-memory, fast ~2ms)
  GET  /api/query   - run a SQL SELECT against a 100k-row table (~5-30ms)
  POST /api/write   - INSERT a new row (~10-50ms, contention under load)

The /api/query endpoint is the primary load-bearing one: p95 latency
scales with concurrent queries because SQLite serializes writes.

Used to:
  - generate p95-varying training data for v2 models (Day 16)
  - replace podinfo as the K8s workload for the AI operator

Run locally:
    docker run --rm -p 8080:8080 workload-v2:dev
    curl http://localhost:8080/api/query?type=count

Run on K8s:
    kubectl apply -f ops/manifests/workload-v2.yaml
"""
from __future__ import annotations

import logging
import os
import random
import sqlite3
import time
from flask import Flask, jsonify, request, render_template_string

LOG = logging.getLogger("workload_v2")

DB_PATH = os.environ.get("DB_PATH", "/tmp/workload.db")
INIT_ROWS = int(os.environ.get("INIT_ROWS", "100000"))
ARTIFICIAL_LATENCY_MS = int(os.environ.get("ARTIFICIAL_LATENCY_MS", "0"))

app = Flask(__name__)


def _conn():
    """Open a SQLite connection with WAL mode + connection-per-thread."""
    c = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")
    return c


def _maybe_init_db():
    """Create schema and seed rows if the DB is fresh."""
    c = _conn()
    c.execute(
        """CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            kind TEXT NOT NULL,
            value REAL NOT NULL,
            payload TEXT
        )"""
    )
    c.execute("SELECT COUNT(*) FROM events")
    count = c.fetchone()[0]
    if count < INIT_ROWS:
        LOG.info("seeding %d rows (current=%d)", INIT_ROWS, count)
        rows = [
            (
                time.time(),
                random.choice(["scale", "heal", "noop"]),
                random.gauss(50.0, 15.0),
                "seed",
            )
            for _ in range(INIT_ROWS - count)
        ]
        c.executemany(
            "INSERT INTO events (ts, kind, value, payload) VALUES (?, ?, ?, ?)",
            rows,
        )
        c.commit()
    c.close()


INDEX_HTML = """<!doctype html>
<html><head><title>Workload v2</title></head>
<body>
<h1>Workload v2 — Day 16</h1>
<p>DB-backed Flask microservice with variable p95 latency.</p>
<ul>
<li>GET <a href="/api/query?type=count">/api/query?type=count</a></li>
<li>GET <a href="/api/query?type=top">/api/query?type=top</a></li>
<li>POST /api/write (JSON: {kind, value})</li>
</ul>
</body></html>
"""


def _artificial_latency():
    """Optional sleep to ensure p95 variance even under no DB contention."""
    if ARTIFICIAL_LATENCY_MS > 0:
        time.sleep(random.uniform(0, ARTIFICIAL_LATENCY_MS / 1000.0))


@app.route("/")
def index():
    _artificial_latency()
    return INDEX_HTML


@app.route("/api/query")
def query():
    _artificial_latency()
    qtype = request.args.get("type", "count")
    c = _conn()
    if qtype == "count":
        cur = c.execute("SELECT COUNT(*) FROM events")
        n = cur.fetchone()[0]
        c.close()
        return jsonify({"type": "count", "count": n})
    elif qtype == "top":
        cur = c.execute(
            "SELECT id, ts, kind, value FROM events ORDER BY value DESC LIMIT 10"
        )
        rows = [
            {"id": r[0], "ts": r[1], "kind": r[2], "value": r[3]}
            for r in cur.fetchall()
        ]
        c.close()
        return jsonify({"type": "top", "rows": rows})
    elif qtype == "stats":
        cur = c.execute(
            "SELECT kind, COUNT(*), AVG(value), MIN(value), MAX(value) "
            "FROM events GROUP BY kind"
        )
        rows = [
            {
                "kind": r[0],
                "count": r[1],
                "avg_value": r[2],
                "min_value": r[3],
                "max_value": r[4],
            }
            for r in cur.fetchall()
        ]
        c.close()
        return jsonify({"type": "stats", "rows": rows})
    else:
        c.close()
        return jsonify({"error": f"unknown type: {qtype}"}), 400


@app.route("/api/write", methods=["POST"])
def write():
    _artificial_latency()
    body = request.get_json(silent=True) or {}
    kind = body.get("kind", "scale")
    value = float(body.get("value", random.gauss(50.0, 15.0)))
    c = _conn()
    c.execute(
        "INSERT INTO events (ts, kind, value, payload) VALUES (?, ?, ?, ?)",
        (time.time(), kind, value, "api"),
    )
    c.commit()
    c.close()
    return jsonify({"status": "ok", "kind": kind, "value": value})


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    _maybe_init_db()
    LOG.info("starting workload_v2 on :8080 (db=%s, init_rows=%d, latency_ms=%d)",
             DB_PATH, INIT_ROWS, ARTIFICIAL_LATENCY_MS)
    app.run(host="0.0.0.0", port=8080, threaded=True)
