"""8B — Sync engine tests (manifest-last, If-Match -> degraded, restore).

No real S3 bucket required — uses LocalFSPersistence via NALLPUTER_CANONICAL tmp.
Uses monkeypatch to override WORKSPACE_ROOT and CANONICAL_ROOT directly
instead of reloading config (cleaner for tmp isolation).
"""

import json
from pathlib import Path

import pytest


def _setup_ws_canon(tmp_path: Path, monkeypatch, ws_name: str, canon_name: str):
    ws = tmp_path / ws_name
    canon = tmp_path / canon_name
    ws.mkdir(parents=True, exist_ok=True)
    for sub in ("projects", "files"):
        (ws / sub).mkdir(parents=True, exist_ok=True)
    canon.mkdir(parents=True, exist_ok=True)

    # Override WORKSPACE_ROOT and CANONICAL_ROOT in all relevant modules
    import nallputer.app.config as cfg
    import nallputer.core.workspace as wsm
    import nallputer.core.sync_engine as se

    monkeypatch.setattr(cfg, "WORKSPACE_ROOT", ws)
    monkeypatch.setattr(cfg, "CANONICAL_ROOT", canon)
    monkeypatch.setattr(wsm, "WORKSPACE_ROOT", ws)
    monkeypatch.setattr(se, "WORKSPACE_ROOT", ws)
    # Also need to override CANONICAL_ROOT for factory local fallback
    monkeypatch.setattr(cfg, "CANONICAL_ROOT", canon)
    # Ensure factory will use new canon (it reads CANONICAL_ROOT at call time via config)
    # Reset singletons
    from nallputer.core.persistence.factory import reset_persistence
    from nallputer.core import sync_engine

    reset_persistence()
    sync_engine.reset_for_tests()
    # Re-ensure workspace dirs via new root
    for sub in ("projects", "files", "artifacts", "tmp", ".cache", ".nallputer/state"):
        (ws / sub).mkdir(parents=True, exist_ok=True)
    return ws, canon, sync_engine


def test_flush_manifest_last(tmp_path: Path, monkeypatch):
    ws, canon, sync_engine = _setup_ws_canon(tmp_path, monkeypatch, "ws", "canon")
    monkeypatch.setenv("NALLPUTER_S3_BUCKET", "")
    from nallputer.core.persistence.factory import reset_persistence

    reset_persistence()

    cid = "cmp_test_manifest"
    p = ws / "projects" / "hello.txt"
    p.write_text("hello")

    sync_engine.mark_dirty(cid, str(p))
    state = sync_engine.flush(cid)
    assert state.sync_state == "synced"
    assert state.last_sync_rev == 1
    assert state.dirty_count == 0

    from nallputer.core.persistence import get_persistence

    pers = get_persistence()
    data, etag = pers.get(f"computers/{cid}/manifest.json")
    assert data is not None
    manifest = json.loads(data)
    assert manifest["revision"] == 1
    assert "workspace/projects/hello.txt" in manifest["files"]
    fdata, _ = pers.get(f"computers/{cid}/workspace/projects/hello.txt")
    assert fdata == b"hello"

    # Second flush with no dirty should be no-op
    state2 = sync_engine.flush(cid)
    assert state2.last_sync_rev == 1

    # Modify and flush again -> rev 2
    p.write_text("hello2")
    sync_engine.mark_dirty(cid, str(p))
    state3 = sync_engine.flush(cid)
    assert state3.last_sync_rev == 2
    fdata2, _ = pers.get(f"computers/{cid}/workspace/projects/hello.txt")
    assert fdata2 == b"hello2"

    sync_engine.reset_for_tests()
    reset_persistence()


def test_if_match_conflict_degraded(tmp_path: Path, monkeypatch):
    ws, canon, sync_engine = _setup_ws_canon(tmp_path, monkeypatch, "ws2", "canon2")
    monkeypatch.setenv("NALLPUTER_S3_BUCKET", "")
    from nallputer.core.persistence.factory import reset_persistence

    reset_persistence()

    cid = "cmp_conflict"
    p = ws / "projects" / "a.txt"
    p.write_text("v1")
    sync_engine.mark_dirty(cid, str(p))
    s1 = sync_engine.flush(cid)
    assert s1.sync_state == "synced"
    assert s1.last_sync_rev == 1

    from nallputer.core.persistence import get_persistence

    pers = get_persistence()
    old_data, old_etag = pers.get(f"computers/{cid}/manifest.json")
    assert old_data is not None
    m = json.loads(old_data)
    m["revision"] = 999
    m["last_sync_at"] = "2099-01-01T00:00:00Z"
    pers.put(f"computers/{cid}/manifest.json", json.dumps(m).encode(), if_match=old_etag)

    p.write_text("v2")
    sync_engine.mark_dirty(cid, str(p))
    s2 = sync_engine.flush(cid)
    assert s2.sync_state == "degraded"
    assert "conflict" in (s2.last_error or "").lower()
    data, _ = pers.get(f"computers/{cid}/manifest.json")
    m2 = json.loads(data)
    assert m2["revision"] == 999

    sync_engine.reset_for_tests()
    reset_persistence()


def test_restore(tmp_path: Path, monkeypatch):
    ws, canon, sync_engine = _setup_ws_canon(tmp_path, monkeypatch, "ws3", "canon3")
    monkeypatch.setenv("NALLPUTER_S3_BUCKET", "")
    from nallputer.core.persistence.factory import reset_persistence

    reset_persistence()

    cid = "cmp_restore"
    p = ws / "projects" / "keep.txt"
    p.write_text("keep me")
    sync_engine.mark_dirty(cid, str(p))
    s = sync_engine.flush(cid)
    assert s.sync_state == "synced"

    # Simulate new runtime: clear workspace
    p.unlink()
    assert not p.exists()
    sync_engine._manifests.pop(cid, None)

    rs = sync_engine.restore(cid)
    assert rs.sync_state == "synced"
    assert p.exists()
    assert p.read_text() == "keep me"

    sync_engine.reset_for_tests()
    reset_persistence()
