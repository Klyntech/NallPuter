import time
import subprocess
from conftest import exec_and_poll, baseline_subprocess, write_result, AUTH


def test_latency_exec_vs_subprocess(client, computer_id):
    """Latency: NALLPUTER exec vs local subprocess baseline (measure-only)."""
    cmd = "echo latency-probe"
    # baseline
    _, base_ms = baseline_subprocess(cmd)
    # NALLPUTER
    t0 = time.perf_counter()
    res = exec_and_poll(client, computer_id, cmd)
    dt = (time.perf_counter() - t0) * 1000

    assert res["status"] == "succeeded", res
    assert "latency-probe" in res.get("stdout", "")

    write_result("latency", {
        "measure": "exec_latency_ms",
        "nallputer_ms": round(dt, 2),
        "baseline_subprocess_ms": round(base_ms, 2),
        "delta_ms": round(dt - base_ms, 2),
        "overhead_x": round(dt / max(base_ms, 1), 2),
        "command": cmd,
        "note": "Windows TestClient baseline; Docker Linux will differ. Informational only.",
    })


def test_latency_polling_overhead(client, computer_id):
    """Ensure poll loop itself is not unexpectedly slow (sanity)."""
    t0 = time.perf_counter()
    r = client.get("/v1/machine", headers=AUTH)
    dt = (time.perf_counter() - t0) * 1000
    assert r.status_code == 200
    write_result("latency_poll", {"get_machine_ms": round(dt, 2)})
