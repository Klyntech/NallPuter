from __future__ import annotations

import os
import time
from functools import lru_cache
from pathlib import Path


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


# 002 + 003 + 006
NALLPUTER_RAM_MB = _int("NALLPUTER_RAM_MB", 512)
NALLPUTER_CPU_MILLICORES = _int("NALLPUTER_CPU_MILLICORES", 500)
NALLPUTER_DISK_GB = _int("NALLPUTER_DISK_GB", 2)
NALLPUTER_MAX_PIDS = _int("NALLPUTER_MAX_PIDS", 100)
NALLPUTER_WALL_TIME_SEC = _int("NALLPUTER_WALL_TIME_SEC", 300)
NALLPUTER_MAX_OUTPUT_BYTES = _int("NALLPUTER_MAX_OUTPUT_BYTES", 100000)
NALLPUTER_WORKSPACE_GB = _int("NALLPUTER_WORKSPACE_GB", 1)
NALLPUTER_EGRESS_POLICY = os.getenv("NALLPUTER_EGRESS_POLICY", "deny-by-default")
NALLPUTER_IDLE_TIMEOUT_SEC = _int("NALLPUTER_IDLE_TIMEOUT_SEC", 900)
# default allowlist for lab: pip/npm/github — matches render.yaml and 007
NALLPUTER_EGRESS_ALLOWLIST = os.getenv("NALLPUTER_EGRESS_ALLOWLIST", "pypi.org,registry.npmjs.org,github.com")  # comma host:port or host

NALLPUTER_TOKEN = os.getenv("NALLPUTER_TOKEN", "dev-token")
NALLPUTER_PROVIDER = os.getenv("NALLPUTER_PROVIDER", "render" if os.getenv("RENDER") else "local")
NALLPUTER_RUNTIME = os.getenv("NALLPUTER_RUNTIME", "nallputer-0.1.0")
NALLPUTER_REVISION = os.getenv("NALLPUTER_REVISION", "cf8834e")
WORKSPACE_ROOT = Path(os.getenv("NALLPUTER_WORKSPACE", "/home/nally/workspace"))
CANONICAL_ROOT = Path(os.getenv("NALLPUTER_CANONICAL", str(WORKSPACE_ROOT.parent / ".nallputer-canonical")))
# 004 Lab Rat cache mount
CACHE_MOUNT = Path(os.getenv("NALLPUTER_CACHE_MOUNT", "/mnt/nallputer-cache"))

# 011 8A — S3-compatible canonical (provider is deployment config, not architecture)
NALLPUTER_S3_BUCKET = os.getenv("NALLPUTER_S3_BUCKET", "").strip()
NALLPUTER_S3_ENDPOINT = os.getenv("NALLPUTER_S3_ENDPOINT", "").strip()
NALLPUTER_S3_REGION = os.getenv("NALLPUTER_S3_REGION", "").strip()
NALLPUTER_S3_ACCESS_KEY = os.getenv("NALLPUTER_S3_ACCESS_KEY", "").strip()
NALLPUTER_S3_SECRET_KEY = os.getenv("NALLPUTER_S3_SECRET_KEY", "").strip()
NALLPUTER_S3_PREFIX = os.getenv("NALLPUTER_S3_PREFIX", "").strip()
# When S3_BUCKET is set and ENDPOINT is "mock", factory will use moto in tests (no real creds)

BOOT_TS = time.monotonic()
BOOT_WALL = time.time()

CGroupState = {"mode": "unknown", "error": None}


def probe_cgroup() -> dict:
    # 006: cgroup v2 unified required, no silent v1 fallback
    ctrl = Path("/sys/fs/cgroup/cgroup.controllers")
    if ctrl.exists():
        CGroupState["mode"] = "v2"
        try:
            CGroupState["controllers"] = ctrl.read_text().strip()
        except Exception:
            CGroupState["controllers"] = ""
        return {"mode": "v2", "controllers": CGroupState.get("controllers","")}
    # check for v1 hybrid
    if Path("/sys/fs/cgroup/memory").exists():
        CGroupState["mode"] = "v1"
        CGroupState["error"] = "cgroup_v2_required"
        return {"mode": "v1", "error": "cgroup_v2_required"}
    CGroupState["mode"] = "none"
    return {"mode": "none"}


# prime at import
probe_cgroup()
