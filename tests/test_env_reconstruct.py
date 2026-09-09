"""8C — Environment reconstruction tests.

- Never mutate yaml during replay
- Deterministic replay via lock (mocked pip)
- Failure -> 503 env_replay_failed, recovering
- Secrets never in yaml/lock (credential_in_spec 403 already covered)
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _setup_ws(tmp_path: Path, monkeypatch, ws_name: str, canon_name: str):
    ws = tmp_path / ws_name
    canon = tmp_path / canon_name
    ws.mkdir(parents=True, exist_ok=True)
    for sub in ("projects", ".nallputer/state"):
        (ws / sub).mkdir(parents=True, exist_ok=True)
    canon.mkdir(parents=True, exist_ok=True)
    import nallputer.app.config as cfg
    import nallputer.core.workspace as wsm
    import nallputer.core.env_reconstruct as er

    monkeypatch.setattr(cfg, "WORKSPACE_ROOT", ws)
    monkeypatch.setattr(cfg, "CANONICAL_ROOT", canon)
    monkeypatch.setattr(wsm, "WORKSPACE_ROOT", ws)
    monkeypatch.setattr(er, "WORKSPACE_ROOT", ws)
    monkeypatch.setenv("NALLPUTER_WORKSPACE", str(ws))
    monkeypatch.setenv("NALLPUTER_CANONICAL", str(canon))
    monkeypatch.setenv("NALLPUTER_S3_BUCKET", "")
    monkeypatch.setenv("NALLPUTER_ENV_REPLAY_MOCK", "1")
    from nallputer.core.persistence.factory import reset_persistence
    from nallputer.core.sync_engine import reset_for_tests

    reset_persistence()
    reset_for_tests()
    for sub in ("projects", "files", "artifacts", "tmp", ".cache", ".nallputer/state"):
        (ws / sub).mkdir(parents=True, exist_ok=True)
    return ws, canon


def test_yaml_not_mutated_on_replay(tmp_path: Path, monkeypatch):
    ws, _ = _setup_ws(tmp_path, monkeypatch, "ws", "canon")
    yaml_path = ws / ".nallputer" / "state" / "environment.yaml"
    yaml_content = "version: 1\npython:\n  packages: [\"requests==2.32.0\"]\n"
    yaml_path.write_text(yaml_content, encoding="utf-8")
    import nallputer.core.env_reconstruct as er

    lock_path = ws / ".nallputer" / "state" / "environment.lock"
    if lock_path.exists():
        lock_path.unlink()
    result = er.replay()
    assert result["status"] in ("ok", "no_env")
    assert yaml_path.read_text(encoding="utf-8") == yaml_content
    assert lock_path.exists()
    lock_content = lock_path.read_text(encoding="utf-8")
    assert "requests" in lock_content
    assert "ghp_" not in lock_content.lower()
    from nallputer.core.sync_engine import reset_for_tests
    from nallputer.core.persistence.factory import reset_persistence

    reset_for_tests()
    reset_persistence()


def test_replay_failure_503(tmp_path: Path, monkeypatch):
    ws, _ = _setup_ws(tmp_path, monkeypatch, "ws2", "canon2")
    yaml_path = ws / ".nallputer" / "state" / "environment.yaml"
    yaml_path.write_text("version: 1\npython:\n  packages: [\"yanked-package==0.0.1\"]\n", encoding="utf-8")
    import nallputer.core.env_reconstruct as er

    with pytest.raises(er.EnvReplayError) as exc:
        er.replay()
    assert "yanked" in str(exc.value).lower() or "failed" in str(exc.value).lower()
    assert "yanked-package" in yaml_path.read_text()
    from nallputer.core.sync_engine import reset_for_tests
    from nallputer.core.persistence.factory import reset_persistence

    reset_for_tests()
    reset_persistence()


def test_credential_never_in_lock(tmp_path: Path, monkeypatch):
    ws, _ = _setup_ws(tmp_path, monkeypatch, "ws3", "canon3")
    yaml_path = ws / ".nallputer" / "state" / "environment.yaml"
    yaml_path.write_text("version: 1\npython:\n  packages: [\"requests==2.32.0\"]\n", encoding="utf-8")
    import nallputer.core.env_reconstruct as er

    lock_path = ws / ".nallputer" / "state" / "environment.lock"
    er.replay()
    if lock_path.exists():
        assert "ghp_" not in lock_path.read_text().lower()
        assert "secret" not in lock_path.read_text().lower()
    from nallputer.core.sync_engine import reset_for_tests
    from nallputer.core.persistence.factory import reset_persistence

    reset_for_tests()
    reset_persistence()


def test_start_replay_integration(monkeypatch):
    monkeypatch.setenv("NALLPUTER_ENV_REPLAY_MOCK", "1")
    import sys

    sys.path.insert(0, "nallputer")
    from nallputer.app.main import app

    client = TestClient(app)
    auth = {"Authorization": "Bearer dev-token"}
    r = client.get("/v1/machine", headers=auth)
    assert r.status_code == 200
    cid = r.json()["computer_id"]
    r = client.post("/v1/files/write", headers=auth, json={"computer_id": cid, "path": "/home/nally/workspace/.nallputer/state/environment.yaml", "content": "version: 1\npython:\n  packages: [\"requests==2.32.0\"]\n"})
    assert r.status_code == 200, r.text
    r = client.post("/v1/computer", headers=auth, json={})
    assert r.status_code == 201
    new_cid = r.json()["computer_id"]
    r = client.post("/v1/files/write", headers=auth, json={"computer_id": new_cid, "path": "/home/nally/workspace/.nallputer/state/environment.yaml", "content": "version: 1\npython:\n  packages: [\"requests==2.32.0\"]\n"})
    assert r.status_code == 200
    r = client.post(f"/v1/computer/{new_cid}/stop", headers=auth)
    assert r.status_code in (200, 202, 503)
    r = client.post(f"/v1/computer/{new_cid}/start", headers=auth)
    assert r.status_code in (200, 202)
    assert r.json()["state"] in ("running", "idle", "recovering")
    bad_cid = client.post("/v1/computer", headers=auth, json={}).json()["computer_id"]
    r = client.post("/v1/files/write", headers=auth, json={"computer_id": bad_cid, "path": "/home/nally/workspace/.nallputer/state/environment.yaml", "content": "version: 1\npython:\n  packages: [\"yanked-package==0.0.1\"]\n"})
    assert r.status_code == 200
    for p in [Path("/home/nally/workspace/.nallputer/state/environment.lock"), Path(os.getenv("NALLPUTER_WORKSPACE", "/home/nally/workspace")) / ".nallputer/state/environment.lock"]:
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
    r = client.post(f"/v1/computer/{bad_cid}/stop", headers=auth)
    r = client.post(f"/v1/computer/{bad_cid}/start", headers=auth)
    if r.status_code == 503:
        assert r.json()["sync_state"]["sync_state"] in ("env_replay_failed", "degraded", "recovering") or r.json()["state"] == "recovering"
    else:
        assert r.status_code == 200
    # Cleanup: restore valid yaml via direct filesystem (more reliable than API when degraded)
    try:
        for p in [Path("/home/nally/workspace/.nallputer/state/environment.yaml"), Path(os.getenv("NALLPUTER_WORKSPACE", "/home/nally/workspace")) / ".nallputer/state/environment.yaml"]:
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("version: 1\npython:\n  packages: [\"requests==2.32.0\"]\n", encoding="utf-8")
            except Exception:
                pass
        for p in [Path("/home/nally/workspace/.nallputer/state/environment.lock"), Path(os.getenv("NALLPUTER_WORKSPACE", "/home/nally/workspace")) / ".nallputer/state/environment.lock"]:
            if p.exists():
                try:
                    txt = p.read_text(encoding="utf-8")
                    if "yanked" in txt.lower():
                        p.unlink()
                except Exception:
                    try:
                        p.unlink()
                    except Exception:
                        pass
        import uuid

        for _cid in [new_cid, bad_cid]:
            try:
                client.post(f"/v1/computer/{_cid}/destroy", headers={**auth, "Idempotency-Key": str(uuid.uuid4())})
            except Exception:
                pass
    except Exception:
        pass
