#!/bin/sh
set -e
# Phase 7-full runner — usable when Docker becomes available
# Usage: sh tests/docker/run.sh  or  make eval-linux
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
echo "Building nallputer:eval ..."
docker build -f tests/docker/Dockerfile.eval -t nallputer:eval .
echo "Running harness (same 19 tests + Linux supplement) ..."
mkdir -p tests/results/linux
# Compose handles cpus/mem_limit/pids_limit as per 006
docker compose -f tests/docker/docker-compose.eval.yml up --build --abort-on-container-exit || true
# Even if compose fails, collect evidence table from whatever JSON was written
python tests/docker/collect.py || echo "collect failed — check tests/results/linux/pytest.log"
echo "Done. See tests/results/linux/REPORT.md and compare to tests/results/REPORT.md (Windows 5a44765)"
