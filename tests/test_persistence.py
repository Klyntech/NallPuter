import base64
import time
from conftest import AUTH, write_result, exec_and_poll


def test_files_write_read_list(client, computer_id):
    path = "/home/nally/workspace/projects/persist.txt"
    content = "hello persistence"
    w = client.post("/v1/files/write", headers=AUTH, json={"computer_id": computer_id, "path": path, "content": content})
    assert w.status_code == 200, w.text
    assert w.json()["sync_state"]["sync_state"] in ("pending", "synced")
    r = client.post("/v1/files/read", headers=AUTH, json={"computer_id": computer_id, "path": path})
    assert r.status_code == 200, r.text
    assert r.json()["content"] == content
    l = client.post("/v1/files/list", headers=AUTH, json={"computer_id": computer_id, "path": "/home/nally/workspace/projects"})
    assert l.status_code == 200, l.text
    assert any(e["name"] == "persist.txt" for e in l.json()["entries"])
    write_result("files_basic", {"write": w.json()["bytes_written"], "read": r.json()["total_bytes"]})


def test_sync_pending_to_synced(client, computer_id):
    # write creates pending
    w = client.post("/v1/files/write", headers=AUTH, json={"computer_id": computer_id, "path": "/home/nally/workspace/projects/syncme.txt", "content": "dirty"})
    assert w.status_code == 200
    s1 = client.get(f"/v1/computer/{computer_id}/sync", headers=AUTH).json()
    # either pending or synced (if auto-flushed)
    assert s1["sync_state"] in ("pending", "synced")
    # force flush
    f = client.post(f"/v1/computer/{computer_id}/sync", headers=AUTH)
    assert f.status_code == 200
    s2 = f.json()
    assert s2["sync_state"] == "synced"
    assert s2["dirty_count"] == 0
    write_result("sync", {"before": s1, "after": s2})


def test_base64_roundtrip(client, computer_id):
    payload = base64.b64encode(b"binary \x00\x01 data").decode()
    p = "/home/nally/workspace/files/binary.dat"
    w = client.post("/v1/files/write", headers=AUTH, json={"computer_id": computer_id, "path": p, "content": payload, "encoding": "base64"})
    assert w.status_code == 200, w.text
    r = client.post("/v1/files/read", headers=AUTH, json={"computer_id": computer_id, "path": p, "encoding": "base64"})
    assert r.status_code == 200, r.text
    assert r.json()["content"] == payload
    write_result("base64", {"path": p})


def test_environment_spec(client, computer_id):
    # valid spec already tested in isolation, but check sync hint + persistence
    p = "/home/nally/workspace/.nallputer/state/environment.yaml"
    content = "version: 1\npython:\n  packages: [\"requests==2.32.0\"]\n"
    w = client.post("/v1/files/write", headers=AUTH, json={"computer_id": computer_id, "path": p, "content": content})
    assert w.status_code == 200, w.text
    assert w.json().get("environment") is not None
    # read back
    r = client.post("/v1/files/read", headers=AUTH, json={"computer_id": computer_id, "path": p})
    assert "requests" in r.json()["content"]
    write_result("env_spec", {"spec": "ok"})


def test_stop_start_persistence(client):
    """Minimal stop/start still presents same workspace (recovery semantics)."""
    # create a dedicated computer for this test
    rc = client.post("/v1/computer", headers=AUTH, json={})
    assert rc.status_code == 201, rc.text
    cid = rc.json()["computer_id"]
    # write file
    w = client.post("/v1/files/write", headers=AUTH, json={"computer_id": cid, "path": "/home/nally/workspace/projects/keep.txt", "content": "keep me"})
    assert w.status_code == 200
    # stop
    st = client.post(f"/v1/computer/{cid}/stop", headers=AUTH)
    assert st.status_code == 200
    assert st.json()["state"] == "stopped"
    # write after stopped should implicitly start (file write triggers running)
    # or explicit start
    s = client.post(f"/v1/computer/{cid}/start", headers=AUTH)
    assert s.status_code == 200
    assert s.json()["state"] == "running"
    # file still there (local FS canonical — informational)
    r = client.post("/v1/files/read", headers=AUTH, json={"computer_id": cid, "path": "/home/nally/workspace/projects/keep.txt"})
    assert r.status_code == 200
    assert r.json()["content"] == "keep me"
    # cleanup
    import uuid

    client.post(f"/v1/computer/{cid}/destroy", headers={**AUTH, "Idempotency-Key": str(uuid.uuid4())})
    write_result("stop_start", {"cid": cid, "kept": True})
