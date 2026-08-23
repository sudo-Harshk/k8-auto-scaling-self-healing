#!/usr/bin/env bash
# scripts/build_image.sh
#
# Build the shared Docker image `k8-ai-ops:dev` that holds every Python
# dependency for the project (Days 3, 4, 5, 7, 8, 9, 11, 12).
#
# Usage (from repo root):
#   ./scripts/build_image.sh
#
# Run-time: ~3 min cold, ~30 s incremental.

set -euo pipefail

LOG() { printf '\033[1;34m[build]\033[0m %s\n' "$*"; }
DIE() { printf '\033[1;31m[build][FATAL]\033[0m %s\n' "$*" >&2; exit 1; }

cd "$(dirname "$0")/.."   # repo root

LOG "building k8-ai-ops:dev"
docker build \
  -t k8-ai-ops:dev \
  -f ops/docker/Dockerfile \
  ops/docker/

LOG "image ready:"
docker images k8-ai-ops:dev --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}"