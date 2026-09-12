from __future__ import annotations

import os
import sys
import time
import subprocess
import uuid
from pathlib import Path

import pytest

# Ensure nallputer is importable (local Windows dev) without Docker
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "nallputer"))
os.environ.setdefault("NALLPUTER_TOKEN", "dev-token")
os.environ.setdefault("NALLPUTER_PROVIDER", "local")
os.environ.setdefault("NALLPUTER_RUNTIME", "nallputer-0.1.0")

from fastapi.testclient import TestClient  # noqa: E402
from nallputer.app.main import app  # noqa: E402

AUTH = {"Authorization": "Bearer dev-token"}
BAD_AUTH = {"Authorization": "Bearer wrong"}


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def computer_id(client: TestClient) -> str:
    r = client.get("/v1/machine", headers=AUTH)
    assert r.status_code == 200, r.text
    return r.json()["computer_id"]


@pytest.fixture(scope="session")
def baseline_env():
    return {}


def timed(fn):
    t0 = time.perf_counter()
    res = fn()
    t1 = time.perf_counter()
    return res, (t1 - t0) * 1000


def baseline_subprocess(command: str, cwd: str | None = None) -> tuple[subprocess.CompletedProcess, float]:
    """Measure local subprocess baseline (shell=True for Windows parity)."""
    t0 = time.perf_counter()
    proc = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)
    dt = (time.perf_counter() - t0) * 1000
    return proc, dt


def exec_and_poll(client: TestClient, cid: str, command: str, timeout_sec: int | None = None, poll_interval: float = 0.2, max_wait: float = 8.0) -> dict:
    key = str(uuid.uuid4())
    body: dict = {"computer_id": cid, "command": command}
    if timeout_sec is not None:
        body["timeout_sec"] = timeout_sec
    r = client.post("/v1/exec", headers={**AUTH, "Idempotency-Key": key}, json=body)
    assert r.status_code in (201, 403), f"exec create failed {r.status_code} {r.text}"
    if r.status_code == 403:
        return r.json()
    rid = r.json()["run_id"]
    deadline = time.time() + max_wait
    while time.time() < deadline:
        rr = client.get(f"/v1/exec/{rid}", headers=AUTH)
        assert rr.status_code == 200, rr.text
        j = rr.json()
        if j["status"] not in ("queued", "running"):
            return j
        time.sleep(poll_interval)
    # return last poll even if still running
    return client.get(f"/v1/exec/{rid}", headers=AUTH).json()

# Results writer — measure-only, not a gate
# When running inside Docker (NALLPUTER_PROVIDER=docker), write to linux subdir so host's Windows baseline is preserved
RESULTS_DIR = ROOT / "tests" / "results"
LINUX_RESULTS_DIR = RESULTS_DIR / "linux"
if os.getenv("NALLPUTER_PROVIDER") == "docker":
    LINUX_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    _active_results_dir = LINUX_RESULTS_DIR
else:
    RESULTS_DIR.mkdir(exist_ok=True)
    _active_results_dir = RESULTS_DIR

def write_result(name: str, payload: dict):
    # Write to active dir; on Docker this is linux/, on host this is results/
    path = _active_results_dir / f"{name}.json"
    payload["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path.write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")
    # Also mirror to legacy path for backwards compat when not docker?
    # No — keep Windows baseline untouched when in Docker


# 8B/8C isolation: each test gets clean persistence + sync state + computer state + workspace env (prevents leakage)
@pytest.fixture(autouse=True)
def _isolate_8b():
    # Before each test, ensure clean state from previous test's S3 mock, degraded sync, or yanked env
    try:
        from nallputer.core.persistence.factory import reset_persistence
        from nallputer.core import sync_engine
        from nallputer.core.lifecycle import computers

        reset_persistence()
        sync_engine.reset_for_tests()
        # Reset Computer sync_states (per-computer) that may be degraded from previous bad env test
        for c in list(computers.values()):
            try:
                c.sync_state.sync_state = "synced"
                c.sync_state.last_error = None
                # Also ensure state is not recovering unless test expects it
                if c.state == "recovering":
                    c.state = "running"
            except Exception:
                pass
        # 8E: lifecycle cleanup — clear _last_activity and idle_since, reset idle/stopped->running
        try:
            from nallputer.core.lifecycle import _last_activity

            _last_activity.clear()
            for c in list(computers.values()):
                try:
                    c.idle_since = None
                    if c.state in ("idle", "stopped"):
                        c.state = "running"
                except Exception:
                    pass
        except Exception:
            pass
        # Ensure global workspace env is valid (not yanked) — previous integration test may have left yanked
        for p in [Path("/home/nally/workspace/.nallputer/state/environment.yaml"), Path(os.getenv("NALLPUTER_WORKSPACE", "/home/nally/workspace")) / ".nallputer/state/environment.yaml"]:
            try:
                if p.exists() and "yanked" in p.read_text(encoding="utf-8", errors="ignore").lower():
                    p.write_text("version: 1\npython:\n  packages: [\"requests==2.32.0\"]\n", encoding="utf-8")
                    # Also remove lock if yanked
                    lp = p.parent / "environment.lock"
                    if lp.exists() and "yanked" in lp.read_text(encoding="utf-8", errors="ignore").lower():
                        lp.unlink()
            except Exception:
                pass
    except Exception:
        pass
    yield
    try:
        from nallputer.core.persistence.factory import reset_persistence
        from nallputer.core import sync_engine
        from nallputer.core.lifecycle import computers

        reset_persistence()
        sync_engine.reset_for_tests()
        for c in list(computers.values()):
            try:
                if c.sync_state.sync_state in ("degraded", "env_replay_failed"):
                    c.sync_state.sync_state = "synced"
                    c.sync_state.last_error = None
                if c.state == "recovering":
                    c.state = "running"
            except Exception:
                pass
        # 8E: lifecycle cleanup — clear _last_activity and idle_since, reset idle/stopped->running
        try:
            from nallputer.core.lifecycle import _last_activity

            _last_activity.clear()
            for c in list(computers.values()):
                try:
                    c.idle_since = None
                    if c.state in ("idle", "stopped"):
                        c.state = "running"
                except Exception:
                    pass
        except Exception:
            pass
        for k in list(os.environ.keys()):
            if k.startswith("NALLPUTER_S3_"):
                if k == "NALLPUTER_S3_BUCKET" and os.getenv(k) == "test-bucket-8a":
                    os.environ.pop(k, None)
                if k == "NALLPUTER_S3_ENDPOINT" and os.getenv(k) == "mock":
                    os.environ.pop(k, None)
        from nallputer.core.persistence.factory import reset_persistence as _rp

        _rp()
        # Clean global workspace again after test
        for p in [Path("/home/nally/workspace/.nallputer/state/environment.yaml"), Path(os.getenv("NALLPUTER_WORKSPACE", "/home/nally/workspace")) / ".nallputer/state/environment.yaml"]:
            try:
                if p.exists() and "yanked" in p.read_text(encoding="utf-8", errors="ignore").lower():
                    p.write_text("version: 1\npython:\n  packages: [\"requests==2.32.0\"]\n", encoding="utf-8")
                    lp = p.parent / "environment.lock"
                    if lp.exists() and "yanked" in lp.read_text(encoding="utf-8", errors="ignore").lower():
                        lp.unlink()
            except Exception:
                pass
    except Exception:
        pass
