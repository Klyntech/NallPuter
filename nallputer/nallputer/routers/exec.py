from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
import math

from nallputer.core.security import verify_bearer, egress_check, audit
from nallputer.core.runtime import create_run, get_run, cancel_run, runs
from nallputer.core.workspace import resolve_jail
from nallputer.core.lifecycle import computers, default_computer_id, get_or_create_default
from nallputer.routers.machine import machine_profile, require_auth
from nallputer.core.sync import get_sync, mark_dirty
from nallputer.app.config import NALLPUTER_IDLE_TIMEOUT_SEC, NALLPUTER_MAX_OUTPUT_BYTES

router = APIRouter(tags=["exec"])

class ExecCreate(BaseModel):
    computer_id: str
    command: str
    cwd: Optional[str] = None
    timeout_sec: Optional[int] = None
    env: Optional[dict] = None

def _run_to_dict(r, cursor: int = 0, limit: int = NALLPUTER_MAX_OUTPUT_BYTES):
    # pagination: cursor is byte offset into stdout
    stdout = r.stdout or ""
    total = r.bytes or len(stdout.encode("utf-8"))
    # slice
    b = stdout.encode("utf-8")
    sliced = b[cursor: cursor+limit].decode("utf-8", errors="ignore")
    truncated_slice = (cursor+limit) < len(b) or r.truncated
    return {
        "run_id": r.run_id,
        "computer_id": r.computer_id,
        "status": r.status,
        "command": r.command,
        "cwd": r.cwd,
        "exit_code": r.exit_code,
        "stdout": sliced,
        "stderr": r.stderr,
        "truncated": truncated_slice if total>limit or r.truncated else False,
        "bytes": total,
        "started_at": r.started_at,
        "finished_at": r.finished_at,
        "wall_time_ms": r.wall_time_ms,
        "policy_result": r.policy_result,
        "error": r.error,
        "environment": r.environment,
        "sync_pending": r.sync_pending,
    }

@router.post("/exec")
def create_exec(body: ExecCreate, authorization: str | None = Header(default=None), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    if not verify_bearer(authorization):
        raise HTTPException(status_code=401, detail={"code":"unauthorized","message":"invalid bearer token"})
    # 008: computer must exist or be startable; if stopped -> implicit start
    profile = machine_profile()
    c = computers.get(body.computer_id)
    if not c:
        if body.computer_id == default_computer_id:
            c = get_or_create_default(profile)
        else:
            raise HTTPException(status_code=404, detail={"code":"not_found","message":"computer not found"})
    if c.state == "stopped":
        # implicit start
        c.state = "running"
    if c.state not in ("running","idle","creating","starting"):
        raise HTTPException(status_code=409, detail={"code":"computer_not_running","message": f"computer state {c.state}"})
    # quota check: workspace quota 007/005 -> 507 if would exceed (MVP: check usage)
    from nallputer.core.workspace import workspace_usage_gb
    try:
        if workspace_usage_gb() > profile["resources"]["workspace_gb"] * 0.99:
            raise HTTPException(status_code=507, detail={"code":"workspace_quota_exceeded","message":"workspace_gb limit reached"})
    except HTTPException:
        raise
    except Exception:
        pass
    # concurrency cap 006: min(cpu/100, pids/10)=5
    max_concurrent = min(profile["resources"]["cpu_millicores"]//100, profile["resources"]["pids"]//10)
    running = sum(1 for r in runs.values() if r.computer_id==body.computer_id and r.status in ("queued","running"))
    if running >= max_concurrent:
        raise HTTPException(status_code=429, detail={"code":"concurrency_limited","message":f"max concurrent runs {max_concurrent}"})
    # 007 egress preflight before spawn
    policy = egress_check(body.command)
    if policy and policy.get("decision")=="deny":
        # policy_denied: no spawn, return run with that status (403 body is Run)
        # we still create a run to satisfy contract's 403 Run shape; but spec says 403 with Run body
        from nallputer.core.runtime import new_run_id, Run
        import uuid, time
        rid = new_run_id()
        r = Run(run_id=rid, computer_id=body.computer_id, status="policy_denied", command=body.command, cwd=body.cwd, policy_result=policy)
        runs[rid] = r
        audit({"computer_id":body.computer_id,"run_id":rid,"decision":"deny","reason":policy.get("reason"),"dst":policy.get("destination")})
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=403, content=_run_to_dict(r))
    # cwd jail check
    cwd_resolved = None
    if body.cwd:
        try:
            p = resolve_jail(body.cwd)
            cwd_resolved = str(p)
            # ensure cwd is inside workspace persistent or tmp allowed
        except PermissionError as e:
            raise HTTPException(status_code=400, detail={"code":"invalid_cwd","message":str(e)})
        except Exception as e:
            raise HTTPException(status_code=400, detail={"code":"invalid_cwd","message":str(e)})
    else:
        cwd_resolved = str(resolve_jail("projects"))

    # wall_time cap
    if body.timeout_sec and body.timeout_sec > profile["resources"]["wall_time_sec"]:
        raise HTTPException(status_code=400, detail={"code":"timeout_exceeds_machine","message":f"timeout {body.timeout_sec} > machine wall_time {profile['resources']['wall_time_sec']}"})

    r = create_run(body.computer_id, body.command, cwd_resolved, body.timeout_sec, body.env, idempotency_key)
    audit({"computer_id": body.computer_id, "run_id": r.run_id, "decision":"allow","command": body.command[:200]})
    # mark possible dirty pending: exec may mutate workspace; optimistic
    sync = get_sync()
    r.sync_pending = sync.dirty_count > 0
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=201, content=_run_to_dict(r))

@router.get("/exec/{run_id}")
def get_exec(run_id: str, authorization: str | None = Header(default=None), cursor: int = Query(0, ge=0), limit: int = Query(NALLPUTER_MAX_OUTPUT_BYTES, ge=1, le=100000)):
    if not verify_bearer(authorization):
        raise HTTPException(status_code=401, detail={"code":"unauthorized","message":"invalid bearer token"})
    r = get_run(run_id)
    if not r:
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"run not found"})
    # TTL 24h eviction check would go here (MVP: no eviction)
    sync = get_sync()
    r.sync_pending = sync.dirty_count > 0
    return _run_to_dict(r, cursor=cursor, limit=limit)

@router.delete("/exec/{run_id}")
def delete_exec(run_id: str, authorization: str | None = Header(default=None)):
    if not verify_bearer(authorization):
        raise HTTPException(status_code=401, detail={"code":"unauthorized","message":"invalid bearer token"})
    r = get_run(run_id)
    if not r:
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"run not found"})
    if r.status in ("succeeded","failed","timed_out","cancelled","policy_denied"):
        raise HTTPException(status_code=409, detail={"code":"already_terminal","message":f"run already {r.status}"})
    cr = cancel_run(run_id)
    audit({"run_id":run_id,"decision":"cancel"})
    return _run_to_dict(cr)

@router.get("/exec/{run_id}/stream")
def stream_exec(run_id: str, authorization: str | None = Header(default=None)):
    if not verify_bearer(authorization):
        raise HTTPException(status_code=401, detail={"code":"unauthorized","message":"invalid bearer token"})
    raise HTTPException(status_code=501, detail={"code":"streaming_not_supported","capability":"streaming","supported":False,"hint":"poll GET /v1/exec/{run_id} with ?cursor=&limit="})
