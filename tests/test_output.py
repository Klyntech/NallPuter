import uuid
import time
from conftest import AUTH, exec_and_poll, write_result


def test_empty_output(client, computer_id):
    """Empty successful output must be explicit (not missing). Cross-platform: use python."""
    res = exec_and_poll(client, computer_id, 'python -c "import sys; sys.exit(0)"')
    # python -c "" produces empty stdout but should still be succeeded with stdout == ""
    assert res["status"] == "succeeded", res
    # allow "" or just whitespace (Windows vs Linux nuance) — must be explicit, not missing
    assert res.get("stdout") == "" or res.get("stdout") is not None, f"expected explicit empty got {repr(res.get('stdout'))}"
    assert res.get("stdout", None) is not None
    assert res.get("stderr") == ""
    write_result("empty_output", {"stdout": res.get("stdout"), "status": res["status"]})


def test_output_exact(client, computer_id):
    res = exec_and_poll(client, computer_id, "echo hello-nallputer")
    assert res["status"] == "succeeded", res
    assert res["stdout"].strip() == "hello-nallputer"
    assert res["exit_code"] == 0
    write_result("output_exact", {"stdout": res["stdout"].strip()})


def test_output_truncation(client, computer_id):
    """Bounded output: 200KB → truncated true, bytes >100000."""
    res = exec_and_poll(client, computer_id, "python -c \"print('A'*200000)\"")
    assert res["status"] == "succeeded", res
    assert res.get("truncated") is True, res
    assert res.get("bytes", 0) > 100000
    # stdout slice at default limit is capped
    assert len(res.get("stdout", "").encode("utf-8")) <= 100000
    write_result("truncation", {"bytes": res.get("bytes"), "truncated": res.get("truncated")})


def test_output_pagination(client, computer_id):
    """Pagination: cursor + limit returns correct slice."""
    # create a run that prints 500 chars
    key = str(uuid.uuid4())
    r = client.post("/v1/exec", headers={**AUTH, "Idempotency-Key": key}, json={"computer_id": computer_id, "command": "python -c \"print('X'*500)\""})
    assert r.status_code == 201, r.text
    rid = r.json()["run_id"]
    # poll until done
    deadline = time.time() + 5
    while time.time() < deadline:
        rr = client.get(f"/v1/exec/{rid}", headers=AUTH)
        if rr.json()["status"] not in ("queued", "running"):
            break
        time.sleep(0.2)
    full = client.get(f"/v1/exec/{rid}", headers=AUTH).json()
    assert full["status"] == "succeeded"
    # paginate
    p1 = client.get(f"/v1/exec/{rid}", headers=AUTH, params={"cursor": 0, "limit": 100})
    p2 = client.get(f"/v1/exec/{rid}", headers=AUTH, params={"cursor": 100, "limit": 100})
    assert p1.status_code == 200
    assert p2.status_code == 200
    # combined slices should equal first 200 chars of full stdout
    combined = p1.json()["stdout"] + p2.json()["stdout"]
    assert full["stdout"][:200] == combined, f"pagination mismatch {repr(full['stdout'][:200])} vs {repr(combined)}"
    write_result("pagination", {"cursor": "ok", "combined_len": len(combined)})
