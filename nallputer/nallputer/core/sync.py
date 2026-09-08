from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

# 004 sync engine stub — debounced + flush + restore is the contract; MVP is local FS cache
# External store abstraction is behind env; MVP local FS acts as canonical.

@dataclass
class SyncStateData:
    sync_state: str = "synced"
    last_sync_rev: Optional[int] = 0
    last_sync_at: Optional[str] = None
    dirty_count: int = 0
    dirty_files: list[str] = field(default_factory=list)
    last_error: Optional[str] = None

sync_state = SyncStateData(last_sync_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), dirty_count=0)

def get_sync():
    return sync_state

def mark_dirty(path: str):
    if path not in sync_state.dirty_files:
        sync_state.dirty_files.append(path)
    sync_state.dirty_count = len(sync_state.dirty_files)
    sync_state.sync_state = "pending"

def flush():
    # MVP: pretend flush succeeded (would push to canonical store via abstraction)
    sync_state.last_sync_rev = (sync_state.last_sync_rev or 0) + 1
    sync_state.last_sync_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sync_state.dirty_files = []
    sync_state.dirty_count = 0
    sync_state.sync_state = "synced"
    return sync_state
