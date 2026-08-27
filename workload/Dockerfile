# Dockerfile for Day 16 workload (Flask + SQLite)
#
# Build:
#   docker build -t workload-v2:dev -f workload/Dockerfile .
#
# Run:
#   docker run --rm -p 8080:8080 workload-v2:dev

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    flask==3.1.3 \
    gunicorn==23.0.0 \
    prometheus_client==0.21.0

COPY app.py /app/app.py

ENV DB_PATH=/data/workload.db
ENV INIT_ROWS=100000
ENV ARTIFICIAL_LATENCY_MS=0

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD wget -qO- http://localhost:8080/healthz || exit 1

# gunicorn: 4 workers, threaded, 30s timeout
CMD ["gunicorn", "--workers", "4", "--threads", "2", "--bind", "0.0.0.0:8080", "--timeout", "30", "--access-logfile", "-", "app:app"]
