from __future__ import annotations

import time
from fastapi import APIRouter, Depends, Header

from nallputer.app.config import (
    NALLPUTER_RAM_MB, NALLPUTER_CPU_MILLICORES, NALLPUTER_DISK_GB, NALLPUTER_MAX_PIDS,
    NALLPUTER_WALL_TIME_SEC, NALLPUTER_MAX_OUTPUT_BYTES, NALLPUTER_WORKSPACE_GB,
    NALLPUTER_EGRESS_POLICY, NALLPUTER_PROVIDER, NALLPUTER_RUNTIME, NALLPUTER_REVISION,
    BOOT_TS, BOOT_WALL, CGroupState, WORKSPACE_ROOT
)
from nallputer.core.lifecycle import default_computer_id, get_or_create_default
from nallputer.core.security import verify_bearer

router = APIRouter(tags=["machine"])

def require_auth(authorization: str | None = Header(default=None)):
    if not verify_bearer(authorization):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail={"code":"unauthorized","message":"invalid bearer token"})
    return True

def machine_profile() -> dict:
    # create/get default computer to anchor computer_id
    # ensure workspace paths from spec
    profile = {
        "computer_id": default_computer_id,
        "provider": NALLPUTER_PROVIDER,
        "runtime": NALLPUTER_RUNTIME,
        "revision": NALLPUTER_REVISION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(BOOT_WALL)),
        "persistence": {
            "instance": "ephemeral",
            "workspace": "external_canonical",
            "workspace_mechanism": "persistent_disk",
            "packages": "reconstructible",
            "snapshots": False,
        },
        "resources": {
            "cpu_millicores": NALLPUTER_CPU_MILLICORES,
            "memory_mb": NALLPUTER_RAM_MB,
            "disk_gb": NALLPUTER_DISK_GB,
            "pids": NALLPUTER_MAX_PIDS,
            "wall_time_sec": NALLPUTER_WALL_TIME_SEC,
            "max_output_bytes": NALLPUTER_MAX_OUTPUT_BYTES,
            "workspace_gb": NALLPUTER_WORKSPACE_GB,
        },
        "capabilities": {
            "shell": True,
            "files": True,
            "package_install": True,
            "network": True,
            "egress_policy": NALLPUTER_EGRESS_POLICY,
            "streaming": False,
            "pause_resume": False,
            "snapshot_restore": False,
        },
        "restart_behavior": "instance_recreated",
        "ephemeral_paths": ["/tmp", "/workspace/.cache", "/workspace/tmp", str(WORKSPACE_ROOT / "tmp"), str(WORKSPACE_ROOT / ".cache")],
        "persistent_paths": [str(WORKSPACE_ROOT), str(WORKSPACE_ROOT / "projects"), str(WORKSPACE_ROOT / "files"), str(WORKSPACE_ROOT / "artifacts"), str(WORKSPACE_ROOT / ".nallputer/state")],
    }
    return profile


@router.get("/machine")
def get_machine(_auth=Depends(require_auth)):
    return machine_profile()

@router.get("/health")
def get_health(authorization: str | None = Header(default=None)):
    # health is also auth-guarded per 003 (same Bearer as exec)
    if not verify_bearer(authorization):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail={"code":"unauthorized","message":"invalid bearer token"})
    # cgroup probe: if v1, return 503 degraded
    if CGroupState.get("mode") == "v1":
        return {
            "status": "degraded",
            "computer_id": default_computer_id,
            "uptime_sec": int(time.monotonic() - BOOT_TS),
            "sync_state": "degraded",
            "last_error": "cgroup_v2_required",
        }
    # sync_state from stub
    from nallputer.core.sync import get_sync
    s = get_sync()
    status = "ok" if s.sync_state in ("synced","pending") else "degraded"
    # 008: if degraded due to env replay etc: 503
    code = 200 if status == "ok" else 503
    body = {
        "status": status,
        "computer_id": default_computer_id,
        "uptime_sec": int(time.monotonic() - BOOT_TS),
        "sync_state": s.sync_state,
        "last_sync_rev": s.last_sync_rev,
        "last_sync_at": s.last_sync_at,
        "last_error": s.last_error,
    }
    # FastAPI will return 200 by default; to emit 503 we raise Response? Use JSONResponse
    if code == 503:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=body)
    return body
