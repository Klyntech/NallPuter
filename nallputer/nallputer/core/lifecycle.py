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

def get_or_create_default(machine_profile: dict) -> Computer:
    if default_computer_id not in computers:
        c = Computer(computer_id=default_computer_id, state="running", machine=machine_profile)
        computers[default_computer_id] = c
    return computers[default_computer_id]

def all_computers() -> list[Computer]:
    return list(computers.values())
