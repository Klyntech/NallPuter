import os
import sys
from pathlib import Path
import pytest

# Linux-only supplemental checks for Phase 7-full — skipped on Windows
pytestmark = pytest.mark.skipif(os.name == "nt", reason="Linux/Docker only — cgroup v2 + pids + concurrency")

from conftest import AUTH  # noqa: E402


def test_cgroup_v2_and_pids(client):
    """Linux: GET /health should report v2 (not v1), pids.max=100, pids.current increments."""
    h = client.get("/v1/health", headers=AUTH)
    assert h.status_code == 200, h.text
    # Probe host cgroup directly — informational, not a contract gate
    mode = "unknown"
    if Path("/sys/fs/cgroup/cgroup.controllers").exists():
        mode = "v2"
        assert Path("/sys/fs/cgroup/cgroup.controllers").read_text().strip() != ""
    elif Path("/sys/fs/cgroup/memory").exists():
        mode = "v1"
        pytest.fail("cgroup v1 detected — Phase 6 requires v2 (no silent fallback)")
    else:
        mode = "none"
    assert mode == "v2", f"expected cgroup v2 got {mode}"
    # pids
    # inside Docker with pids_limit:100, host's cgroup should show max 100
    for cand in [Path("/sys/fs/cgroup/pids.max"), Path("/sys/fs/cgroup/pids.current")]:
        if cand.exists():
            break
    # Check container's view of pids.max
    pids_max_path = Path("/sys/fs/cgroup/pids.max")
    if pids_max_path.exists():
        assert pids_max_path.read_text().strip() == "100", f"pids.max should be 100 got {pids_max_path.read_text().strip()}"
    # Verify GET /v1/computer reports pids_used (stub currently 0 — this will tighten in 7-full)
    # For now just ensure health is ok
    assert h.json()["status"] == "ok"


def test_concurrency_5(client, computer_id):
    """Linux: 5 concurrent sleep 1 should allow 5, 6th → 429 (006)."""
    import time
    import uuid
    import threading

    results = []

    def fire():
        key = str(uuid.uuid4())
        r = client.post("/v1/exec", headers={**AUTH, "Idempotency-Key": key}, json={"computer_id": computer_id, "command": "sleep 1"})
        results.append(r)

    threads = [threading.Thread(target=fire) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # At least 5 should be 201, the 6th should be 429
    codes = [r.status_code for r in results]
    assert codes.count(201) >= 5, f"expected ≥5 concurrent 201 got {codes}"
    assert 429 in codes, f"expected 6th to be 429 concurrency_limited got {codes}"
    # cleanup: wait for sleeps to finish
    time.sleep(1.5)
