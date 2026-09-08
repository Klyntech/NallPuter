from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

# 8B — Sync engine now real (manifest-last via persistence adapter).
# This module is the public facade used by routers; actual logic lives in sync_engine.py
# Keeps backward compat for callers that used global sync_state.

from nallputer.core import sync_engine as _engine
from nallputer.core.sync_engine import SyncState as EngineSyncState


@dataclass
class SyncStateData:
    sync_state: str = "synced"
    last_sync_rev: Optional[int] = 0
    last_sync_at: Optional[str] = None
    dirty_count: int = 0
    dirty_files: list[str] = field(default_factory=list)
    last_error: Optional[str] = None
    manifest_etag: Optional[str] = None

# Global singleton for default computer (backward compat)
sync_state = SyncStateData(last_sync_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), dirty_count=0)

# Keep default computer id lazy to avoid circular import
def _default_cid() -> str:
    try:
        from nallputer.core.lifecycle import default_computer_id

        return default_computer_id
    except Exception:
        return "cmp_default"


def _map_state(s: EngineSyncState) -> SyncStateData:
    return SyncStateData(
        sync_state=s.sync_state,
        last_sync_rev=s.last_sync_rev,
        last_sync_at=s.last_sync_at,
        dirty_count=s.dirty_count,
        dirty_files=list(s.dirty_files),
        last_error=s.last_error,
        manifest_etag=s.manifest_etag,
    )


def get_sync(cid: Optional[str] = None):
    """Get sync state for cid (or default). Keeps global sync_state in sync for legacy callers."""
    target = cid or _default_cid()
    s = _engine.get_sync_state(target)
    mapped = _map_state(s)
    # Keep global for backward compat when called without cid
    if cid is None or cid == _default_cid():
        sync_state.sync_state = mapped.sync_state
        sync_state.last_sync_rev = mapped.last_sync_rev
        sync_state.last_sync_at = mapped.last_sync_at
        sync_state.dirty_count = mapped.dirty_count
        sync_state.dirty_files = mapped.dirty_files
        sync_state.last_error = mapped.last_error
        sync_state.manifest_etag = mapped.manifest_etag
        return sync_state
    return mapped


def get_sync_for(cid: str):
    return _map_state(_engine.get_sync_state(cid))


def mark_dirty(path: str, cid: Optional[str] = None):
    target = cid or _default_cid()
    _engine.mark_dirty(target, path)
    # Update global mirror
    s = _engine.get_sync_state(target)
    if target == _default_cid():
        sync_state.sync_state = s.sync_state
        sync_state.dirty_count = s.dirty_count
        sync_state.dirty_files = list(s.dirty_files)
        sync_state.last_error = s.last_error


def flush(cid: Optional[str] = None):
    target = cid or _default_cid()
    # Flush via engine (manifest-last, If-Match)
    s = _engine.flush(target)
    mapped = _map_state(s)
    if target == _default_cid():
        sync_state.sync_state = mapped.sync_state
        sync_state.last_sync_rev = mapped.last_sync_rev
        sync_state.last_sync_at = mapped.last_sync_at
        sync_state.dirty_count = mapped.dirty_count
        sync_state.dirty_files = mapped.dirty_files
        sync_state.last_error = mapped.last_error
        sync_state.manifest_etag = mapped.manifest_etag
        return sync_state
    return mapped


def restore(cid: str):
    s = _engine.restore(cid)
    # Mirror to global if default
    if cid == _default_cid():
        sync_state.sync_state = s.sync_state
        sync_state.last_sync_rev = s.last_sync_rev
        sync_state.last_sync_at = s.last_sync_at
        sync_state.dirty_count = s.dirty_count
        sync_state.dirty_files = list(s.dirty_files)
        sync_state.last_error = s.last_error
        sync_state.manifest_etag = s.manifest_etag
    return _map_state(s)
