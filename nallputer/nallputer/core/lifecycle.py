from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Literal, Optional

from nallputer.app.config import BOOT_TS, BOOT_WALL

ComputerState = Literal["creating","running","idle","stopping","stopped","starting","error","recovering","destroyed","destroying"]
SyncStateLit = Literal["synced","pending","degraded","env_replay_failed"]

@dataclass
class SyncState:
    sync_state: SyncStateLit = "synced"
    last_sync_rev: Optional[int] = None
    last_sync_at: Optional[str] = None
    dirty_count: int = 0
    dirty_files: list[str] = field(default_factory=list)
    last_error: Optional[str] = None

@dataclass
class Computer:
    computer_id: str
    state: ComputerState = "running"
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(BOOT_WALL)))
    updated_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    machine: dict = field(default_factory=dict)
    sync_state: SyncState = field(default_factory=SyncState)
    idle_since: Optional[float] = None

# MVP: single-tenant in-memory computers (canonical store is 004 but local FS is the canonical for MVP)
computers: Dict[str, Computer] = {}
default_computer_id = f"cmp_{uuid.uuid4().hex[:8]}"

# 8E: auto-stop tracking
_last_activity: Dict[str, float] = {}
_auto_stop_thread = None
_auto_stop_stop = False


def touch_activity(cid: str) -> None:
    """Mark computer as active (called on exec/files). Resets idle timer."""
    import time as _t

    _last_activity[cid] = _t.monotonic()
    c = computers.get(cid)
    if c is not None and c.state in ("idle", "running"):
        c.idle_since = None
        if c.state == "idle":
            c.state = "running"


def get_idle_timeout() -> int:
    # 011 row 3: 900s default, configurable via env/MachineProfile
    try:
        import os

        return int(os.getenv("NALLPUTER_IDLE_TIMEOUT_SEC", "900"))
    except ValueError:
        return 900


def _auto_stop_loop() -> None:
    import time as _t

    while not _auto_stop_stop:
        try:
            # Check every 1s (fast for tests with short timeout)
            _t.sleep(1)
            now = _t.monotonic()
            timeout = get_idle_timeout()
            # Need to import here to avoid circular
            try:
                from nallputer.core.runtime import runs as _runs
            except Exception:
                _runs = {}  # type: ignore
            for cid, c in list(computers.items()):
                if c.state not in ("running", "idle"):
                    continue
                # Check active runs
                has_active = any(r.computer_id == cid and r.status in ("queued", "running") for r in _runs.values())
                if has_active:
                    c.idle_since = None
                    _last_activity[cid] = now
                    continue
                # No active runs -> idle
                if c.idle_since is None:
                    c.idle_since = now
                    if c.state == "running":
                        c.state = "idle"
                # Check timeout
                last = _last_activity.get(cid, now)
                # Use idle_since as start, but also consider last activity
                idle_start = c.idle_since or last
                if now - idle_start >= timeout:
                    # Transition idle -> stopping -> stopped (flush)
                    c.state = "stopping"
                    try:
                        from nallputer.core.sync import flush as _flush

                        s = _flush(cid)
                        if s.sync_state == "degraded":
                            c.state = "recovering"
                            c.sync_state.sync_state = "degraded"
                            c.sync_state.last_error = s.last_error
                        else:
                            c.state = "stopped"
                            c.sync_state.sync_state = "synced"
                            c.sync_state.last_sync_rev = s.last_sync_rev
                            c.sync_state.last_sync_at = s.last_sync_at
                    except Exception as e:
                        c.state = "recovering"
                        c.sync_state.last_error = str(e)[:500]
                    c.idle_since = None
        except Exception:
            continue


def start_auto_stop() -> None:
    global _auto_stop_thread, _auto_stop_stop
    if _auto_stop_thread is not None and _auto_stop_thread.is_alive():
        return
    _auto_stop_stop = False
    import threading

    _auto_stop_thread = threading.Thread(target=_auto_stop_loop, daemon=True)
    _auto_stop_thread.start()


def stop_auto_stop() -> None:
    global _auto_stop_stop
    _auto_stop_stop = True


def get_or_create_default(machine_profile: dict) -> Computer:
    if default_computer_id not in computers:
        c = Computer(computer_id=default_computer_id, state="running", machine=machine_profile)
        computers[default_computer_id] = c
        _last_activity[default_computer_id] = time.monotonic()
    return computers[default_computer_id]

def all_computers() -> list[Computer]:
    return list(computers.values())
