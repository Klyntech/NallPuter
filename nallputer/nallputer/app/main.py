from __future__ import annotations

import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from nallputer.app.config import BOOT_TS, probe_cgroup, CGroupState
from nallputer.routers import machine as machine_router
from nallputer.routers import computer as computer_router
from nallputer.routers import exec as exec_router
from nallputer.routers import files as files_router
from nallputer.core.lifecycle import default_computer_id, get_or_create_default
from nallputer.core.workspace import WORKSPACE_ROOT


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 8B: on-start restore (manifest + workspace) per 004 + 011 row 2
    probe_cgroup()
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    for sub in ("projects","files","artifacts","tmp",".cache",".nallputer/state"):
        (WORKSPACE_ROOT / sub).mkdir(parents=True, exist_ok=True)
    # init default computer
    from nallputer.routers.machine import machine_profile

    get_or_create_default(machine_profile())
    # 8B restore for default computer (best-effort, degraded on failure per 004)
    # 8C env replay after restore (011 row 4) — never mutate yaml, 503 on failure
    try:
        from nallputer.core.sync import restore

        restore(default_computer_id)
        try:
            from nallputer.core.env_reconstruct import replay, EnvReplayError
            from nallputer.core.sync_engine import get_sync_state as _get_ss

            replay()
        except EnvReplayError as e:
            # Mark degraded per 004/008: env_replay_failed
            from nallputer.core.sync_engine import _sync_states as _ss_map
            from nallputer.core.sync_engine import SyncState as _SS

            ss = _ss_map.get(default_computer_id)
            if ss is not None:
                ss.sync_state = "env_replay_failed"
                ss.last_error = str(e)[:500]
            print(f"[env_reconstruct] replay failed for {default_computer_id}: {e}", flush=True)
        except Exception as e:
            print(f"[env_reconstruct] unexpected replay error: {e}", flush=True)
    except Exception:
        pass
    # launch egress proxy stub (007) — binds 127.0.0.1:3128 and enforces allowlist; MVP is no-op but logs
    # we don't actually start a proxy process to keep MVP light; env HTTP_PROXY still injected per run
    yield
    # 8B pre-stop flush (manifest-last, 10s SIGTERM window per 004) for default computer
    try:
        from nallputer.core.sync import flush

        flush(default_computer_id)
    except Exception:
        pass

app = FastAPI(
    title="NallPuter",
    version="0.1.0",
    description="NallPuter disposable runtime — provider-neutral Machine Contract",
    lifespan=lifespan,
)

# Routers under /v1
app.include_router(machine_router.router, prefix="/v1")
app.include_router(computer_router.router, prefix="/v1")
app.include_router(exec_router.router, prefix="/v1")
app.include_router(files_router.router, prefix="/v1")

@app.get("/")
def root():
    return {"name":"nallputer","version":"0.1.0","computer_id": default_computer_id, "uptime_sec": int(time.monotonic()-BOOT_TS)}

@app.get("/health")
def plain_health():
    # plain health without auth for load balancer probe; v1/health is auth-guarded
    return {"status":"ok","computer_id": default_computer_id, "uptime_sec": int(time.monotonic()-BOOT_TS), "cgroup": CGroupState.get("mode")}

# Global error wrapper to ensure Error shape
@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    # don't leak stack
    return JSONResponse(status_code=500, content={"code":"internal_error","message":str(exc)[:500]})
