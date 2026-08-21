# Shared Python image for the AI-Driven Kubernetes Operator project.
#
# One image reused by:
#   Day 3  - metrics_client.py + capture_baseline.py + locust
#   Day 4  - kafka producer                   (add kafka-python)
#   Day 5  - faust stream processor           (add faust-streaming)
#   Day 7  - river training scripts           (add river)
#   Day 9  - decision engine                  (add shap)
#  Day 12 - kopf operator                     (add kopf + kubernetes)
#
# Run pattern (host port-forward active, container reaches it via host.docker.internal):
#   docker build -t k8-ai-ops:dev ops/docker/
#   docker run --rm -v ${PWD}:/code -w /code k8-ai-ops:dev python <script>
#   docker run --rm -v ${PWD}:/code -w /code --entrypoint locust k8-ai-ops:dev -f locustfile.py ...
#
# Python 3.11 chosen over 3.12 because:
#   - Locust + gevent have a known RecursionError on Python 3.12 Windows (SSL monkey-patch)
#   - Faust and Kopf officially target 3.10/3.11
#   - kafka-python 2.0.2 doesn't ship working wheels on 3.12 (vendored six import broken)
#   - All other libs work on 3.11 fine.
# River on 3.11 needs a 3-line source patch — see the RUN sed step below.
FROM python:3.11-slim

WORKDIR /app

# Pre-install build deps only if needed (we pin wheels-only deps, so usually none).
# Keep image small: --no-cache-dir + slim base.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Patch River for 3.11: cp311 wheels contain Python 3.12 typing syntax that fails
# to parse on 3.11. Strip the generic[] subscript on csv.DictReader so the module
# imports cleanly. Cost: lose the static type hint on one class; no runtime impact.
# See tasks/AMENDMENTS.md (2026-08-20 River 3.11-patch).
RUN sed -i 's|class DictReader(csv.DictReader\["FeatureName"\]):|class DictReader(csv.DictReader):|' \
        /usr/local/lib/python3.11/site-packages/river/stream/iter_csv.py

# Default entrypoint is python; override with --entrypoint locust when running Locust.
ENTRYPOINT ["python"]

# Volume mount expected at /code when running on a host project.
WORKDIR /code