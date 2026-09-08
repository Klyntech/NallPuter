from __future__ import annotations

import json
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set

from nallputer.app.config import WORKSPACE_ROOT
from nallputer.core.persistence import get_persistence
from nallputer.core.persistence.base import ConflictError
from nallputer.core.workspace import is_ephemeral


# 8B — Sync engine: dirty → debounce 3s → flush (workspace files → manifest LAST) → restore
# Invariant: manifest LAST via If-Match. If workspace files succeed but manifest fails (Conflict),
# canonical state is NOT committed — old manifest remains consistent snapshot (004).


@dataclass
class Manifest:
    computer_id: str
    revision: int = 0
    created_at: str = ""
    last_sync_at: Optional[str] = None
    files: Dict[str, dict] = field(default_factory=dict)  # key -> {etag, size}
    etag: Optional[str] = None  # current manifest etag (not persisted, for If-Match)

    def to_dict(self) -> dict:
        return {
            "computer_id": self.computer_id,
            "revision": self.revision,
            "created_at": self.created_at,
            "last_sync_at": self.last_sync_at,
            "files": self.files,
        }

    @classmethod
    def from_bytes(cls, computer_id: str, data: bytes, etag: Optional[str]) -> "Manifest":
        try:
            d = json.loads(data.decode("utf-8"))
            return cls(
                computer_id=d.get("computer_id", computer_id),
                revision=d.get("revision", 0),
                created_at=d.get("created_at", ""),
                last_sync_at=d.get("last_sync_at"),
                files=d.get("files", {}),
                etag=etag,
            )
        except Exception:
            return cls(computer_id=computer_id, revision=0, etag=etag)


@dataclass
class SyncState:
    sync_state: str = "synced"  # synced | pending | degraded | env_replay_failed
    last_sync_rev: Optional[int] = 0
    last_sync_at: Optional[str] = None
    dirty_count: int = 0
    dirty_files: list[str] = field(default_factory=list)
    last_error: Optional[str] = None
    manifest_etag: Optional[str] = None


# Per-computer state
_sync_states: Dict[str, SyncState] = {}
_dirty: Dict[str, Set[str]] = {}
_manifests: Dict[str, Manifest] = {}
_locks: Dict[str, threading.Lock] = {}
_debounce_timers: Dict[str, threading.Timer] = {}

DEBOUNCE_SEC = 3.0


def _lock_for(cid: str) -> threading.Lock:
    if cid not in _locks:
        _locks[cid] = threading.Lock()
    return _locks[cid]


def _sync_state_for(cid: str) -> SyncState:
    if cid not in _sync_states:
        _sync_states[cid] = SyncState(last_sync_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), dirty_count=0)
    return _sync_states[cid]


def _manifest_key(cid: str) -> str:
    return f"computers/{cid}/manifest.json"


def _workspace_key(cid: str, rel_posix: str) -> str:
    # rel_posix is posix relative to WORKSPACE_ROOT, e.g. projects/foo.txt
    return f"computers/{cid}/workspace/{rel_posix}"


def _rel_for_path(p: Path) -> Optional[str]:
    try:
        rel = p.resolve().relative_to(WORKSPACE_ROOT.resolve()).as_posix()
        return rel
    except ValueError:
        return None


def _ensure_manifest(cid: str) -> Manifest:
    if cid in _manifests:
        return _manifests[cid]
    # Try to load from persistence
    pers = get_persistence()
    data, etag = pers.get(_manifest_key(cid))
    if data is not None:
        m = Manifest.from_bytes(cid, data, etag)
        _manifests[cid] = m
        ss = _sync_state_for(cid)
        ss.manifest_etag = etag
        ss.last_sync_rev = m.revision
        ss.last_sync_at = m.last_sync_at
        return m
    # New manifest
    m = Manifest(computer_id=cid, revision=0, created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), etag=None)
    _manifests[cid] = m
    return m


def mark_dirty(cid: str, path_str: str) -> None:
    """Called by files/write or exec mutating workspace. Coalesces via debounce."""
    # Only persistent files
    try:
        p = Path(path_str)
        if is_ephemeral(p):
            return
        rel = _rel_for_path(p)
        if rel is None:
            return
        # Only workspace persistent subset (but is_ephemeral already checks)
        # Track dirty
        with _lock_for(cid):
            if cid not in _dirty:
                _dirty[cid] = set()
            _dirty[cid].add(str(p.resolve()))
            ss = _sync_state_for(cid)
            ss.dirty_files = sorted(_dirty[cid])
            ss.dirty_count = len(ss.dirty_files)
            ss.sync_state = "pending"
        # Debounce
        _schedule_debounce(cid)
    except Exception:
        # Never fail the write because sync failed
        pass


def _schedule_debounce(cid: str) -> None:
    # Cancel existing timer
    t = _debounce_timers.get(cid)
    if t is not None:
        try:
            t.cancel()
        except Exception:
            pass
    timer = threading.Timer(DEBOUNCE_SEC, lambda: _debounced_flush(cid))
    timer.daemon = True
    _debounce_timers[cid] = timer
    timer.start()


def _debounced_flush(cid: str) -> None:
    try:
        flush(cid)
    except Exception as e:
        ss = _sync_state_for(cid)
        ss.sync_state = "degraded"
        ss.last_error = str(e)[:500]


def flush(cid: Optional[str] = None) -> SyncState:
    """Flush dirty files + manifest LAST with If-Match.

    If `cid` is None, flush all dirty computers (used by global POST /sync without cid? but spec is per-cid).
    Returns SyncState for cid (or first if multiple).
    """
    # Determine which cids to flush
    cids = [cid] if cid is not None else list(_dirty.keys())
    # If no dirty, ensure at least default cid's manifest is not stale? No-op
    last_state: Optional[SyncState] = None
    for target in cids:
        if not target:
            continue
        with _lock_for(target):
            dirty_set = _dirty.get(target, set())
            if not dirty_set:
                # No dirty, but still ensure sync_state is synced unless degraded
                ss = _sync_state_for(target)
                if ss.sync_state not in ("degraded", "env_replay_failed"):
                    ss.sync_state = "synced"
                last_state = ss
                continue
            pers = get_persistence()
            manifest = _ensure_manifest(target)
            old_etag = manifest.etag
            # Upload each dirty file
            new_files = dict(manifest.files)  # copy
            failed = False
            for abs_path_str in list(dirty_set):
                p = Path(abs_path_str)
                rel = _rel_for_path(p)
                if rel is None:
                    continue
                if not p.exists() or not p.is_file():
                    # File deleted locally -> delete from canonical? For v0.1, skip deletes (no tombstone)
                    # To be explicit, we could delete key, but not required for minimal
                    # Just remove from manifest and delete canonical key if exists
                    key = _workspace_key(target, rel)
                    try:
                        pers.delete(key)
                    except Exception:
                        pass
                    new_files.pop(f"workspace/{rel}", None)
                    continue
                try:
                    data = p.read_bytes()
                    key = _workspace_key(target, rel)
                    # No If-Match for file puts (idempotent)
                    etag = pers.put(key, data)
                    new_files[f"workspace/{rel}"] = {"etag": etag, "size": len(data)}
                except Exception as e:
                    ss = _sync_state_for(target)
                    ss.sync_state = "degraded"
                    ss.last_error = f"put failed {rel}: {e}"[:500]
                    failed = True
                    break
            if failed:
                last_state = _sync_state_for(target)
                continue
            # Prepare new manifest
            new_rev = manifest.revision + 1
            new_manifest_dict = {
                "computer_id": target,
                "revision": new_rev,
                "created_at": manifest.created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "last_sync_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "files": new_files,
            }
            data = json.dumps(new_manifest_dict, indent=2).encode("utf-8")
            try:
                new_etag = pers.put(_manifest_key(target), data, if_match=old_etag)
            except ConflictError as ce:
                # Manifest-last invariant: do NOT commit partial state, mark degraded
                ss = _sync_state_for(target)
                ss.sync_state = "degraded"
                ss.last_error = f"manifest If-Match conflict: expected {ce.expected!r} got {ce.actual!r}"
                last_state = ss
                continue
            except Exception as e:
                ss = _sync_state_for(target)
                ss.sync_state = "degraded"
                ss.last_error = str(e)[:500]
                last_state = ss
                continue
            # Success: update in-memory manifest and clear dirty
            manifest.revision = new_rev
            manifest.last_sync_at = new_manifest_dict["last_sync_at"]
            manifest.files = new_files
            manifest.etag = new_etag
            _manifests[target] = manifest
            # Clear dirty
            _dirty[target] = set()
            ss = _sync_state_for(target)
            ss.dirty_count = 0
            ss.dirty_files = []
            ss.sync_state = "synced"
            ss.last_sync_rev = new_rev
            ss.last_sync_at = manifest.last_sync_at
            ss.manifest_etag = new_etag
            ss.last_error = None
            last_state = ss
    # If cid was None and we flushed multiple, return first; if no cid supplied and no dirty, return default
    if last_state is not None:
        return last_state
    # Fallback: return state for requested cid or default
    if cid is not None:
        return _sync_state_for(cid)
    # No cid and no dirty -> return generic synced
    return SyncState(sync_state="synced", last_sync_rev=0)


def restore(cid: str) -> SyncState:
    """On-start restore: fetch manifest -> restore workspace files -> synced.

    If store unreachable, mark degraded/recovering per 004.
    """
    with _lock_for(cid):
        pers = get_persistence()
        ss = _sync_state_for(cid)
        try:
            data, etag = pers.get(_manifest_key(cid))
        except Exception as e:
            ss.sync_state = "degraded"
            ss.last_error = f"manifest fetch failed: {e}"[:500]
            return ss
        if data is None:
            # No manifest yet -> fresh computer, nothing to restore
            ss.sync_state = "synced"
            ss.last_sync_rev = 0
            _manifests[cid] = Manifest(computer_id=cid, revision=0, created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), etag=None)
            return ss
        manifest = Manifest.from_bytes(cid, data, etag)
        _manifests[cid] = manifest
        ss.manifest_etag = etag
        ss.last_sync_rev = manifest.revision
        ss.last_sync_at = manifest.last_sync_at
        # Restore each file in manifest
        for rel_key, meta in manifest.files.items():
            # rel_key is workspace/... e.g. workspace/projects/foo.txt
            # Map to local path: WORKSPACE_ROOT / rel without workspace prefix?
            # Our key is computers/cmp/workspace/... -> rel_key is workspace/...
            # Strip workspace/ prefix for local path
            local_rel = rel_key
            if local_rel.startswith("workspace/"):
                local_rel = local_rel[len("workspace/") :]
            local_path = WORKSPACE_ROOT / local_rel
            try:
                key = f"computers/{cid}/{rel_key}"
                fdata, _ = pers.get(key)
                if fdata is not None:
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    # Atomic write
                    tmp = local_path.with_suffix(local_path.suffix + ".tmp") if local_path.suffix else Path(str(local_path) + ".tmp")
                    tmp.write_bytes(fdata)
                    try:
                        import os

                        fd = os.open(str(tmp), os.O_RDWR)
                        try:
                            os.fsync(fd)
                        finally:
                            os.close(fd)
                    except Exception:
                        pass
                    try:
                        tmp.replace(local_path)
                    except OSError:
                        try:
                            if local_path.exists():
                                local_path.unlink()
                        except Exception:
                            pass
                        tmp.replace(local_path)
            except Exception as e:
                ss.sync_state = "degraded"
                ss.last_error = f"restore failed {rel_key}: {e}"[:500]
                return ss
        # Clear dirty after successful restore (local is now canonical)
        _dirty[cid] = set()
        ss.dirty_count = 0
        ss.dirty_files = []
        ss.sync_state = "synced"
        ss.last_error = None
        return ss


def get_sync_state(cid: str) -> SyncState:
    return _sync_state_for(cid)


def reset_for_tests() -> None:
    """For tests only — clear all in-memory state."""
    _sync_states.clear()
    _dirty.clear()
    _manifests.clear()
    for t in list(_debounce_timers.values()):
        try:
            t.cancel()
        except Exception:
            pass
    _debounce_timers.clear()
    _locks.clear()
