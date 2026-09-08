"""8F — Observability: real resources_usage behind existing shape.

No endpoint redesign. Linux acceptance: pids.max=100, pids.current real non-zero,
concurrency 5->429 already proven in test_linux_cgroup, but here we check that
GET /computer/{id} resources_usage is not stub 0 on Linux.
"""

import os

import pytest


def test_resources_usage_real(client, computer_id):
    """GET /computer/{id} should return real pids_used/memory_mb, not stub 0 on Linux."""
    r = client.get(f"/v1/computer/{computer_id}", headers={"Authorization": "Bearer dev-token"})
    assert r.status_code == 200, r.text
    j = r.json()
    usage = j.get("resources_usage", {})
    # On Windows, pids_used may still be 0 (informational stub) — allow 0 there
    # On Linux/Docker, it must be real non-zero from cgroup
    if os.name == "nt":
        # Windows: stub is okay, but if psutil provides memory, it may be >0
        assert "pids_used" in usage
        assert "memory_mb" in usage
        # Don't hard-code 0 vs non-zero on Windows
    else:
        # Linux: should be real from cgroup, not stub 0
        assert usage.get("pids_used") is not None
        # pids_used should be >0 and comes from cgroup (not stub 0)
        # Don't hard-code 3, just ensure >0 and < pids_max (100)
        assert usage["pids_used"] > 0, f"pids_used should be >0 on Linux, got {usage['pids_used']}"
        assert usage["pids_used"] < 100, f"pids_used should be < max 100, got {usage['pids_used']}"
        # memory should be >0
        assert usage["memory_mb"] > 0, f"memory_mb should be >0 on Linux, got {usage['memory_mb']}"


def test_cgroup_files_exist_on_linux():
    """Direct cgroup check — informational, not a gate failure if not on Windows."""
    if os.name == "nt":
        pytest.skip("Linux/Docker only")
    from pathlib import Path

    # Check cgroup v2 exists
    has_v2 = Path("/sys/fs/cgroup/cgroup.controllers").exists()
    has_pids = Path("/sys/fs/cgroup/pids.current").exists() or Path("/sys/fs/cgroup/system.slice/pids.current").exists()
    # On Docker with pids limit, both should be true
    # This is the same check as collect.py
    assert has_v2 or has_pids, "cgroup files should exist on Linux"
