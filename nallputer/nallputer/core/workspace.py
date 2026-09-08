from __future__ import annotations

from pathlib import Path
import os
import base64

from nallputer.app.config import WORKSPACE_ROOT

# 005 + 007: single workspace jail, shared by files + exec cwd

PERSISTENT_SUBS = {"projects", "files", "artifacts", ".nallputer"}
EPHEMERAL_SUBS = {"tmp", ".cache"}
DENY_CACHE_SUFFIXES = {"__pycache__", ".pytest_cache", "node_modules/.cache", ".cache"}

def _ensure_workspace():
    # 005: ensure workspace exists, but do not crash on permission errors (CI uses RUNNER_TEMP)
    try:
        WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
        for sub in ("projects","files","artifacts","tmp",".cache",".nallputer/state",".nallputer/logs"):
            (WORKSPACE_ROOT / sub).mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        # Fall back to tmp if /home/nally not writable (e.g., GitHub Actions host)
        import tempfile

        fb = Path(tempfile.gettempdir()) / "nallputer-workspace"
        try:
            fb.mkdir(parents=True, exist_ok=True)
            for sub in ("projects","files","artifacts","tmp",".cache",".nallputer/state",".nallputer/logs"):
                (fb / sub).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        # do not raise — caller may use NALLPUTER_WORKSPACE override
        print(f"[workspace] warning: could not create {WORKSPACE_ROOT}: {e} — using fallback {fb}", flush=True)

_ensure_workspace()

def resolve_jail(requested: str) -> Path:
    """
    005 + 007: resolve against workspace root with realpath + O_NOFOLLOW + prefix check.
    Rejects .. traversal, absolute outside root, symlink escape.
    Handles both:
      - absolute workspace paths: /home/nally/workspace/projects/x -> WORKSPACE_ROOT/projects/x
      - relative paths: projects/x -> WORKSPACE_ROOT/projects/x
      - bare /etc/passwd -> denied (not under workspace prefix)
    """
    if not requested or requested == "/":
        return WORKSPACE_ROOT.resolve()
    # Normalize slashes
    req = requested.replace("\\", "/")
    # Absolute workspace path: strip prefix
    workspace_prefix = "/home/nally/workspace"
    # Also handle WORKSPACE_ROOT as prefix (for Windows, translate)
    if req.startswith(workspace_prefix):
        rel = req[len(workspace_prefix):].lstrip("/")
        if not rel:
            rel = "."
        candidate = WORKSPACE_ROOT / rel
    elif req.startswith("/"):
        # any other absolute path is outside workspace -> deny
        raise PermissionError(f"filesystem_denied: {requested!r} outside workspace")
    else:
        # relative path
        rel = req.lstrip("/")
        if not rel:
            rel = "."
        candidate = WORKSPACE_ROOT / rel
    # Resolve + prefix check (also catches .. traversal and symlink escape)
    try:
        resolved = candidate.resolve()
    except Exception:
        resolved = (candidate).absolute()
    root_resolved = WORKSPACE_ROOT.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError:
        raise PermissionError(f"filesystem_denied: {requested!r} outside workspace (traversal)")
    return resolved


def is_ephemeral(path: Path) -> bool:
    """005: tmp/.cache and cache suffixes are ephemeral and excluded from sync."""
    try:
        rel = path.resolve().relative_to(WORKSPACE_ROOT.resolve())
    except ValueError:
        return True  # outside root treated as ephemeral/denied
    parts = set(rel.parts)
    if "tmp" in parts or ".cache" in parts:
        return True
    for suffix in DENY_CACHE_SUFFIXES:
        if suffix in str(rel):
            return True
    # explicit sub tmp/.cache
    if rel.parts and rel.parts[0] in EPHEMERAL_SUBS:
        return True
    return False


def workspace_usage_gb() -> float:
    total = 0
    root = WORKSPACE_ROOT.resolve()
    for p in root.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                continue
    return total / (1024**3)

def disk_usage_gb() -> float:
    # 002/005: disk is container FS; use workspace dir's filesystem stats
    try:
        import shutil
        total, used, free = shutil.disk_usage(str(WORKSPACE_ROOT.resolve()))
        return used / (1024**3)
    except Exception:
        return workspace_usage_gb()

def is_within_persistent(path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(WORKSPACE_ROOT.resolve())
    except ValueError:
        return False
    if not rel.parts:
        return False
    return rel.parts[0] in PERSISTENT_SUBS and rel.parts[0] not in EPHEMERAL_SUBS and not is_ephemeral(path)
