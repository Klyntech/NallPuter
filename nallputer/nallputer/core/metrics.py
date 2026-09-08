from __future__ import annotations

import os
from pathlib import Path


def _read_int(path: Path) -> int | None:
    try:
        if path.exists():
            txt = path.read_text(encoding="utf-8").strip()
            # Handle "max" for pids.max
            if txt == "max":
                return 999999
            return int(txt.split()[0])
    except (OSError, ValueError):
        pass
    return None


def _read_first_existing(paths: list[Path]) -> int | None:
    for p in paths:
        v = _read_int(p)
        if v is not None:
            return v
    return None


def get_pids() -> tuple[int | None, int | None]:
    """Return (pids_current, pids_max). None if not on cgroup v2 or not available."""
    # cgroup v2 unified paths
    # On Docker with --pids-limit=100, files are at /sys/fs/cgroup/pids.current / pids.max
    # On systemd, they may be at /sys/fs/cgroup/system.slice/... but for container it's still /sys/fs/cgroup/...
    current = _read_first_existing(
        [
            Path("/sys/fs/cgroup/pids.current"),
            Path("/sys/fs/cgroup/system.slice/pids.current"),
        ]
    )
    max_val = _read_first_existing(
        [
            Path("/sys/fs/cgroup/pids.max"),
            Path("/sys/fs/cgroup/system.slice/pids.max"),
        ]
    )
    return current, max_val


def get_memory_mb() -> int | None:
    """Return current memory usage in MB, or None if not available."""
    # cgroup v2: /sys/fs/cgroup/memory.current (bytes)
    # cgroup v1: /sys/fs/cgroup/memory/memory.usage_in_bytes
    # Also check systemd path
    for p in [
        Path("/sys/fs/cgroup/memory.current"),
        Path("/sys/fs/cgroup/system.slice/memory.current"),
        Path("/sys/fs/cgroup/memory/memory.usage_in_bytes"),
    ]:
        v = _read_int(p)
        if v is not None:
            return int(v / (1024 * 1024))
    # Fallback: try psutil if available
    try:
        import psutil  # type: ignore

        return int(psutil.Process().memory_info().rss / (1024 * 1024))
    except Exception:
        pass
    return None


def get_cpu_millicores() -> int | None:
    """Return CPU usage in millicores (1000 = 1 core), or None if not available."""
    # cgroup v2: cpu.stat has usage_usec
    # For now return None and let caller handle
    try:
        p = Path("/sys/fs/cgroup/cpu.stat")
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            for line in txt.splitlines():
                if line.startswith("usage_usec"):
                    usec = int(line.split()[1])
                    # Convert to millicores not trivial without time; return None for now
                    return None
    except Exception:
        pass
    return None
