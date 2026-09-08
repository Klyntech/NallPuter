import time
import uuid
from conftest import exec_and_poll, write_result, AUTH


def test_timeout(client, computer_id):
    """Timeout: wall-time 1s on sleep 3 → timed_out (006)."""
    res = exec_and_poll(client, computer_id, 'python -c "import time; time.sleep(3)"', timeout_sec=1)
    assert res["status"] == "timed_out", res
    assert res.get("policy_result", {}).get("reason") == "wall_time_exceeded"
    assert res.get("wall_time_ms") is not None
    write_result("timeout", {"status": res["status"], "wall_time_ms": res.get("wall_time_ms")})


def test_cancellation(client, computer_id):
    """Cancel: DELETE /v1/exec/{id} while running → cancelled (006 pgid)."""
    # create long run without polling
    key = str(uuid.uuid4())
    r = client.post("/v1/exec", headers={**AUTH, "Idempotency-Key": key}, json={"computer_id": computer_id, "command": 'python -c "import time; time.sleep(5)"'})
    assert r.status_code == 201, r.text
    rid = r.json()["run_id"]
    time.sleep(0.3)
    d = client.delete(f"/v1/exec/{rid}", headers=AUTH)
    assert d.status_code == 200, d.text
    assert d.json()["status"] == "cancelled", d.json()
    write_result("cancel", {"status": d.json()["status"]})


def test_stream_pause_snapshot_501(client, computer_id):
    """Streaming/pause/resume/snapshot are 501 when streaming false (003)."""
    # need a real run id for stream
    res = exec_and_poll(client, computer_id, "echo hi")
    rid = res.get("run_id")
    if not rid:
        # fallback: create one
        import uuid

        key = str(uuid.uuid4())
        r = client.post("/v1/exec", headers={**AUTH, "Idempotency-Key": key}, json={"computer_id": computer_id, "command": "echo hi"})
        rid = r.json()["run_id"]
    s = client.get(f"/v1/exec/{rid}/stream", headers=AUTH)
    assert s.status_code == 501, s.text
    assert s.json()["detail"]["capability"] == "streaming"

    p = client.post(f"/v1/computer/{computer_id}/pause", headers=AUTH)
    assert p.status_code == 501
    rs = client.post(f"/v1/computer/{computer_id}/resume", headers=AUTH)
    assert rs.status_code == 501
    sp = client.post(f"/v1/computer/{computer_id}/snapshot", headers=AUTH)
    assert sp.status_code == 501
    write_result("reserved_501", {"stream": s.status_code, "pause": p.status_code})
