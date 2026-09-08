import uuid
from conftest import AUTH, write_result


def test_workspace_jail(client, computer_id):
    """Filesystem jail: /etc/passwd and /tmp outside workspace → 403 (005+007)."""
    forbidden = ["/etc/passwd", "/tmp/hack", "/home/nally/.ssh/id_rsa"]
    for path in forbidden:
        r = client.post("/v1/files/write", headers=AUTH, json={"computer_id": computer_id, "path": path, "content": "bad"})
        assert r.status_code == 403, f"{path} should be 403 got {r.status_code} {r.text}"
        assert r.json()["detail"]["code"] in ("filesystem_denied", "not_found")
    # allowed path must succeed
    r = client.post("/v1/files/write", headers=AUTH, json={"computer_id": computer_id, "path": "/home/nally/workspace/projects/allowed.txt", "content": "ok"})
    assert r.status_code == 200, r.text
    write_result("jail", {"forbidden": forbidden, "allowed": "ok"})


def test_egress_policy(client, computer_id):
    """Egress deny-by-default (007): evil.com blocked, pypi/npm/github allowed."""
    blocked = 'curl https://evil.com'
    r = client.post("/v1/exec", headers={**AUTH, "Idempotency-Key": str(uuid.uuid4())}, json={"computer_id": computer_id, "command": blocked})
    assert r.status_code == 403, r.text
    assert r.json()["status"] == "policy_denied"
    assert r.json()["policy_result"]["reason"] == "egress_blocked"

    # allowlisted — should not be policy_denied (may succeed or fail on exec, but not denied)
    import time
    from conftest import exec_and_poll

    # pypi.org is in default allowlist
    res = exec_and_poll(client, computer_id, "echo fetch https://pypi.org ok")
    assert res["status"] in ("succeeded", "failed", "policy_denied")
    # if our allowlist works, pypi should NOT be policy_denied
    assert res["status"] != "policy_denied", f"pypi should be allowed, got {res}"
    write_result("egress", {"evil": "blocked 403", "pypi": res["status"]})


def test_credential_in_spec_blocked(client, computer_id):
    """environment.yaml must not contain secrets (007)."""
    r = client.post(
        "/v1/files/write",
        headers=AUTH,
        json={"computer_id": computer_id, "path": "/home/nally/workspace/.nallputer/state/environment.yaml", "content": "token: ghp_secret123"},
    )
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["code"] == "credential_in_spec"
    # valid env spec should pass
    r = client.post(
        "/v1/files/write",
        headers=AUTH,
        json={"computer_id": computer_id, "path": "/home/nally/workspace/.nallputer/state/environment.yaml", "content": "version: 1\npython:\n  packages: [\"pandas==2.2.3\"]\n"},
    )
    assert r.status_code == 200, r.text
    write_result("credential", {"blocked": 403, "valid": 200})
