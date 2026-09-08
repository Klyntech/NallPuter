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
RESULTS_DIR = ROOT / "tests" / "results"
RESULTS_DIR.mkdir(exist_ok=True)

def write_result(name: str, payload: dict):
    path = RESULTS_DIR / f"{name}.json"
    payload["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path.write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")
