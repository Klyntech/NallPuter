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
    from nallputer.core.metrics import get_pids, get_memory_mb, get_cpu_millicores

    try:
        w_used = workspace_usage_gb()
    except Exception:
        w_used = 0
    # 8F: real cgroup metrics behind existing shape (no new endpoint)
    pids_current, pids_max = get_pids()
    # On Windows, pids_current is None -> keep 0 as informational stub (was 0 before 8F)
    pids_used = pids_current if pids_current is not None else 0
    mem_mb = get_memory_mb()
    if mem_mb is None:
        mem_mb = 0
    cpu_m = get_cpu_millicores()
    if cpu_m is None:
        cpu_m = 0
    return {
        "computer_id": c.computer_id,
        "state": c.state,
        "machine": c.machine or machine_profile(),
        "resources_usage": {
            "workspace_used_gb": round(w_used, 4),
            "disk_used_gb": round(disk_usage_gb(), 4),
            "pids_used": pids_used,
            "memory_mb": mem_mb,
            "cpu_millicores": cpu_m,
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
    # 8E: mark activity for auto-stop
    try:
        from nallputer.core.lifecycle import touch_activity

        touch_activity(cid)
    except Exception:
        pass
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
    # 008 + 8B: restore from canonical (manifest + workspace) via sync_engine
    from nallputer.core.sync import restore as sync_restore

    s = sync_restore(computer_id)
    if s.sync_state in ("degraded", "env_replay_failed"):
        # Keep recovering semantics per 008: if restore fails, mark recovering
        c.state = "recovering"
        c.sync_state.sync_state = s.sync_state
        c.sync_state.last_error = s.last_error
        c.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content=_computer_to_dict(c))
    # 8C: env replay after restore (never mutate yaml, 503 on failure)
    try:
        from nallputer.core.env_reconstruct import replay, EnvReplayError
        from nallputer.core.sync_engine import get_sync_state as _get_ss

        replay()
        # Replay success: sync state may have been updated via file writes, but ensure computer reflects it
        ss = _get_ss(computer_id)
        c.sync_state.sync_state = ss.sync_state
        c.sync_state.last_sync_rev = ss.last_sync_rev
        c.sync_state.last_sync_at = ss.last_sync_at
        c.sync_state.last_error = ss.last_error
    except EnvReplayError as e:
        c.state = "recovering"
        c.sync_state.sync_state = "env_replay_failed"
        c.sync_state.last_error = str(e)[:500]
        c.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        # Also mark sync_engine state
        try:
            from nallputer.core.sync_engine import _sync_states as _ss_map

            ss = _ss_map.get(computer_id)
            if ss is not None:
                ss.sync_state = "env_replay_failed"
                ss.last_error = str(e)[:500]
        except Exception:
            pass
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content=_computer_to_dict(c))
    except Exception as e:
        # Unexpected replay error -> degraded
        c.state = "recovering"
        c.sync_state.sync_state = "degraded"
        c.sync_state.last_error = str(e)[:500]
        c.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content=_computer_to_dict(c))
    c.state = "running"
    c.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    c.sync_state.sync_state = s.sync_state
    c.sync_state.last_sync_rev = s.last_sync_rev
    c.sync_state.last_sync_at = s.last_sync_at
    c.sync_state.last_error = s.last_error
    return _computer_to_dict(c)

@router.post("/computer/{computer_id}/stop")
def stop_computer(computer_id: str, _auth=Depends(require_auth)):
    c = computers.get(computer_id)
    if not c:
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"computer not found"})
    if c.state == "stopped":
        return _computer_to_dict(c)
    # 008 + 8B: SIGTERM flush up to 10s — manifest-last via persistence adapter
    s = flush(computer_id)
    c.state = "stopped"
    c.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # If flush degraded (If-Match conflict), mark recovering not synced
    if s.sync_state == "degraded":
        c.state = "recovering"
        c.sync_state.sync_state = "degraded"
        c.sync_state.last_error = s.last_error
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content=_computer_to_dict(c))
    c.sync_state.sync_state = "synced"
    c.sync_state.last_sync_rev = s.last_sync_rev
    c.sync_state.last_sync_at = s.last_sync_at
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
    s = get_sync(computer_id)
    return {"sync_state": s.sync_state, "last_sync_rev": s.last_sync_rev, "last_sync_at": s.last_sync_at, "dirty_count": s.dirty_count, "dirty_files": s.dirty_files, "last_error": s.last_error}

@router.post("/computer/{computer_id}/sync")
def post_computer_sync(computer_id: str, _auth=Depends(require_auth)):
    c = computers.get(computer_id) or (get_or_create_default(machine_profile()) if computer_id==default_computer_id else None)
    if not c:
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"computer not found"})
    s = flush(computer_id)
    # Keep computer's sync_state in sync with engine
    c.sync_state.sync_state = s.sync_state
    c.sync_state.last_sync_rev = s.last_sync_rev
    c.sync_state.last_sync_at = s.last_sync_at
    c.sync_state.last_error = s.last_error
    c.sync_state.dirty_count = s.dirty_count
    c.sync_state.dirty_files = s.dirty_files
    if s.sync_state == "degraded":
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"sync_state": s.sync_state, "last_sync_rev": s.last_sync_rev, "last_sync_at": s.last_sync_at, "dirty_count": s.dirty_count, "dirty_files": s.dirty_files, "last_error": s.last_error})
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
