from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Optional

from .base import Persistence, ConflictError


def _etag_for(data: bytes) -> str:
    # S3 ETag for single-part is md5 hex in quotes; we use bare hex for simplicity
    return hashlib.md5(data).hexdigest()


class LocalFSPersistence(Persistence):
    """Local-filesystem canonical store (fallback when S3 not configured).

    Maps key `computers/cmp_abc/manifest.json` to
    `CANONICAL_ROOT / key` on host FS.
    ETag is md5 of file content (or None if missing). Atomic via tmp+replace + fsync
    best-effort (same as 005 workspace atomic).
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Normalize: strip leading slash, prevent traversal
        k = key.lstrip("/")
        # Prevent `../` escape
        p = (self.root / k).resolve()
        r = self.root.resolve()
        try:
            p.relative_to(r)
        except ValueError:
            raise ValueError(f"key {key!r} escapes canonical root")
        return p

    def _etag(self, p: Path) -> Optional[str]:
        if not p.exists():
            return None
        try:
            data = p.read_bytes()
            return _etag_for(data)
        except OSError:
            return None

    def get(self, key: str) -> tuple[Optional[bytes], Optional[str]]:
        p = self._path(key)
        if not p.exists() or not p.is_file():
            return None, None
        try:
            data = p.read_bytes()
            return data, _etag_for(data)
        except OSError:
            return None, None

    def put(self, key: str, data: bytes, if_match: Optional[str] = None) -> str:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        # If-Match check
        cur_etag = self._etag(p)
        if if_match is not None:
            if cur_etag != if_match:
                raise ConflictError(key, if_match, cur_etag)
        # Atomic write
        tmp = p.with_suffix(p.suffix + ".tmp") if p.suffix else Path(str(p) + ".tmp")
        tmp.write_bytes(data)
        # fsync best-effort
        try:
            fd = os.open(str(tmp), os.O_RDWR)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        except Exception:
            pass
        try:
            tmp.replace(p)
        except OSError:
            # Windows fallback: unlink dest then replace
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
            tmp.replace(p)
        return _etag_for(data)

    def delete(self, key: str) -> None:
        p = self._path(key)
        try:
            if p.is_file():
                p.unlink()
            # Also try to prune empty parent dirs up to root (best-effort)
            cur = p.parent
            r = self.root.resolve()
            while cur.resolve() != r and cur != r:
                try:
                    cur.rmdir()
                except OSError:
                    break
                cur = cur.parent
        except OSError:
            pass

    def list(self, prefix: str) -> list[str]:
        pref = prefix.lstrip("/")
        base = self._path(pref) if pref else self.root
        # If prefix is file-like, list matching files
        root_resolved = self.root.resolve()
        out: list[str] = []
        # Determine search root: if prefix ends with / or is dir-like, use that dir
        search_root = base if base.is_dir() else base.parent
        if not search_root.exists():
            return []
        for p in search_root.rglob("*"):
            if p.is_file():
                try:
                    rel = p.resolve().relative_to(root_resolved).as_posix()
                    if rel.startswith(pref):
                        out.append(rel)
                except ValueError:
                    continue
        out.sort()
        return out

    def exists(self, key: str) -> bool:
        p = self._path(key)
        return p.exists() and p.is_file()
