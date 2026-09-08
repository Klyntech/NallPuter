import time
import importlib
from conftest import write_result, AUTH


def test_startup_warm(client):
    """Warm: consecutive GET /v1/health + GET /v1/machine (measure-only)."""
    t0 = time.perf_counter()
    h = client.get("/v1/health", headers=AUTH)
    m = client.get("/v1/machine", headers=AUTH)
    dt = (time.perf_counter() - t0) * 1000
    assert h.status_code == 200, h.text
    assert m.status_code == 200, m.text
    assert m.json()["computer_id"] == h.json()["computer_id"]
    write_result("startup_warm", {
        "warm_ms": round(dt, 2),
        "uptime_sec": h.json().get("uptime_sec"),
        "sync_state": h.json().get("sync_state"),
    })


def test_startup_cold():
    """Cold: fresh TestClient import + lifespan (measure-only, Windows)."""
    t0 = time.perf_counter()
    import nallputer.app.main as main
    importlib.reload(main)
    from fastapi.testclient import TestClient

    c = TestClient(main.app)
    r = c.get("/v1/health", headers=AUTH)
    dt = (time.perf_counter() - t0) * 1000
    assert r.status_code in (200, 503), r.text
    write_result("startup_cold", {
        "cold_ms": round(dt, 2),
        "health": r.json(),
        "note": "Cold includes import+lifespan; Windows; real cold on Render includes container boot.",
    })
