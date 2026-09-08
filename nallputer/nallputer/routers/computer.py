from __future__ import annotations

import uuid
import time
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from nallputer.core.security import verify_bearer
from nallputer.core.lifecycle import computers, default_computer_id, Computer, SyncState, get_or_create_default
from nallputer.routers.machine import machine_profile, require_auth
from nallputer.core.sync import get_sync, flush
from nallputer.app.config import NALLPUTER_RAM_MB, NALLPUTER_WORKSPACE_GB

router = APIRouter(tags=["computer"])

class ResourcesInput(BaseModel):
    cpu_millicores: Optional[int] = None
    memory_mb: Optional[int] = None
    disk_gb: Optional[int] = None
    pids: Optional[int] = None
    wall_time_sec: Optional[int] = None
    max_output_bytes: Optional[int] = None
    workspace_gb: Optional[int] = None

class CreateComputerBody(BaseModel):
    resources: Optional[ResourcesInput] = None

def _computer_to_dict(c: Computer) -> dict:
    from nallputer.core.workspace import workspace_usage_gb, disk_usage_gb
    try:
        w_used = workspace_usage_gb()
    except Exception:
        w_used = 0
    return {
        "computer_id": c.computer_id,
        "state": c.state,
        "machine": c.machine or machine_profile(),
        "resources_usage": {
            "workspace_used_gb": round(w_used, 4),
            "disk_used_gb": round(disk_usage_gb(), 4),
            "pids_used": 0,  # MVP: not wiring pids.current yet; stub
            "memory_mb": 0,
            "cpu_millicores": 0,
        },
        "sync_state": {
            "sync_state": c.sync_state.sync_state,
            "last_sync_rev": c.sync_state.last_sync_rev,
            "last_sync_at": c.sync_state.last_sync_at,
            "dirty_count": c.sync_state.dirty_count,
            "dirty_files": c.sync_state.dirty_files,
            "last_error": c.sync_state.last_error,
        },
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }

@router.post("/computer")
def create_computer(body: CreateComputerBody | None = None, _auth=Depends(require_auth)):
    profile = machine_profile()
    if body and body.resources:
        # apply overrides to profile resources (002 scaling is config, not new product)
        for k,v in body.resources.model_dump(exclude_none=True).items():
            if k in profile["resources"]:
                profile["resources"][k] = v
    cid = f"cmp_{uuid.uuid4().hex[:8]}"
    sync = SyncState(sync_state="synced", last_sync_rev=0, last_sync_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    c = Computer(computer_id=cid, state="running", machine=profile, sync_state=sync)
    computers[cid] = c
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=201, content={"computer_id": cid, "machine": profile})

@router.get("/computer")
def list_computers(_auth=Depends(require_auth)):
    # ensure default exists
    get_or_create_default(machine_profile())
    return {"computers": [_computer_to_dict(c) for c in computers.values()]}

@router.get("/computer/{computer_id}")
def get_computer(computer_id: str, _auth=Depends(require_auth)):
    c = computers.get(computer_id)
    if not c:
        # also check default alias
        if computer_id == default_computer_id:
            c = get_or_create_default(machine_profile())
        else:
            raise HTTPException(status_code=404, detail={"code":"not_found","message":"computer not found"})
    return _computer_to_dict(c)

@router.post("/computer/{computer_id}/start")
def start_computer(computer_id: str, _auth=Depends(require_auth)):
    c = computers.get(computer_id)
    if not c:
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"computer not found"})
    if c.state in ("running","idle"):
        raise HTTPException(status_code=409, detail={"code":"already_running","message":"computer already running"})
    # 008: re-fetch manifest + restore workspace + replay env -> running (MVP: just flip)
    c.state = "running"
    c.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # simulate restore flush
    s = get_sync()
    c.sync_state.sync_state = s.sync_state
    return _computer_to_dict(c)

@router.post("/computer/{computer_id}/stop")
def stop_computer(computer_id: str, _auth=Depends(require_auth)):
    c = computers.get(computer_id)
    if not c:
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"computer not found"})
    if c.state == "stopped":
        return _computer_to_dict(c)
    # 008: SIGTERM flush up to 10s
    flush()
    c.state = "stopped"
    c.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    c.sync_state.sync_state = "synced"
    return _computer_to_dict(c)

@router.post("/computer/{computer_id}/destroy")
def destroy_computer(computer_id: str, authorization: str | None = Header(default=None), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    if not verify_bearer(authorization):
        raise HTTPException(status_code=401, detail={"code":"unauthorized","message":"invalid bearer token"})
    if not idempotency_key:
        raise HTTPException(status_code=400, detail={"code":"idempotency_required","message":"Idempotency-Key required for destroy"})
    c = computers.get(computer_id)
    if not c:
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"computer not found"})
    # idempotent destroy: delete canonical prefix (MVP: delete in-memory + workspace files? keep workspace for safety but mark destroyed)
    c.state = "destroyed"
    # remove from map after marking
    computers.pop(computer_id, None)
    return {"status":"destroying","computer_id":computer_id}

@router.get("/computer/{computer_id}/sync")
def get_computer_sync(computer_id: str, _auth=Depends(require_auth)):
    c = computers.get(computer_id) or (get_or_create_default(machine_profile()) if computer_id==default_computer_id else None)
    if not c:
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"computer not found"})
    s = get_sync()
    return {"sync_state": s.sync_state, "last_sync_rev": s.last_sync_rev, "last_sync_at": s.last_sync_at, "dirty_count": s.dirty_count, "dirty_files": s.dirty_files, "last_error": s.last_error}

@router.post("/computer/{computer_id}/sync")
def post_computer_sync(computer_id: str, _auth=Depends(require_auth)):
    c = computers.get(computer_id) or (get_or_create_default(machine_profile()) if computer_id==default_computer_id else None)
    if not c:
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"computer not found"})
    s = flush()
    return {"sync_state": s.sync_state, "last_sync_rev": s.last_sync_rev, "last_sync_at": s.last_sync_at, "dirty_count": s.dirty_count, "dirty_files": s.dirty_files, "last_error": s.last_error}

@router.post("/computer/{computer_id}/pause")
def pause_computer(computer_id: str, _auth=Depends(require_auth)):
    raise HTTPException(status_code=501, detail={"code":"pause_not_supported","capability":"pause_resume","supported":False})

@router.post("/computer/{computer_id}/resume")
def resume_computer(computer_id: str, _auth=Depends(require_auth)):
    raise HTTPException(status_code=501, detail={"code":"resume_not_supported","capability":"pause_resume","supported":False})

@router.post("/computer/{computer_id}/snapshot")
def snapshot_computer(computer_id: str, _auth=Depends(require_auth)):
    raise HTTPException(status_code=501, detail={"code":"snapshot_not_supported","capability":"snapshot_restore","supported":False})
