.PHONY: eval eval-linux eval-minimal docker-eval clean

# Default: minimal gate (no Docker needed)
eval: eval-minimal

eval-minimal:
	pytest tests -v

# Phase 7-full — requires Docker (runnable when available, measure-only)
eval-linux:
	@echo "Building nallputer:eval and running Linux harness..."
	docker build -f tests/docker/Dockerfile.eval -t nallputer:eval .
	docker compose -f tests/docker/docker-compose.eval.yml up --build --abort-on-container-exit || true
	python tests/docker/collect.py || echo "collect failed — see tests/results/linux/pytest.log"
	@echo "Windows: tests/results/REPORT.md (5a44765)  |  Linux: tests/results/linux/REPORT.md"

docker-eval:
	sh tests/docker/run.sh

clean:
	rm -rf tests/results/linux/__pycache__ tests/results/linux/junit.xml tests/results/linux/pytest.log
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
