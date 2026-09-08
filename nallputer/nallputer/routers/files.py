from __future__ import annotations

import base64
import os
from pathlib import Path
from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from nallputer.core.security import verify_bearer, credential_in_spec, audit
from nallputer.core.workspace import resolve_jail, is_ephemeral, workspace_usage_gb
from nallputer.core.sync import get_sync, mark_dirty
from nallputer.routers.machine import machine_profile, require_auth
from nallputer.core.lifecycle import computers, default_computer_id, get_or_create_default

router = APIRouter(tags=["files"])

class FileReadRequest(BaseModel):
    computer_id: str
    path: str
    offset: Optional[int] = 0
    limit: Optional[int] = None
    encoding: Optional[str] = "utf8"

class FileWriteRequest(BaseModel):
    computer_id: str
    path: str
    content: str
    encoding: Optional[str] = "utf8"
    mode: Optional[str] = None

class FileListRequest(BaseModel):
    computer_id: str
    path: str
    recursive: Optional[bool] = False
    limit: Optional[int] = 100
    cursor: Optional[str] = None

def _ensure_computer(computer_id: str):
    profile = machine_profile()
    c = computers.get(computer_id)
    if not c:
        if computer_id == default_computer_id:
            c = get_or_create_default(profile)
        else:
            raise HTTPException(status_code=404, detail={"code":"not_found","message":"computer not found"})
    if c.state == "stopped":
        c.state = "running"
    return c

@router.post("/files/read")
def file_read(body: FileReadRequest, authorization: str | None = Header(default=None)):
    if not verify_bearer(authorization):
        raise HTTPException(status_code=401, detail={"code":"unauthorized","message":"invalid bearer token"})
    _ensure_computer(body.computer_id)
    try:
        p = resolve_jail(body.path)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail={"code":"filesystem_denied","message":str(e)})
    if not p.exists():
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"file not found"})
    if p.is_dir():
        raise HTTPException(status_code=400, detail={"code":"is_directory","message":"path is directory"})
    # read bounded
    limit = body.limit or 100000
    offset = body.offset or 0
    try:
        data = p.read_bytes()
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code":"read_failed","message":str(e)})
    total = len(data)
    if total > 100000 and body.limit is None:
        raise HTTPException(status_code=413, detail={"code":"too_large","message":"file too large for single read — use range"})
    sliced = data[offset: offset+limit]
    # encoding
    if body.encoding == "base64":
        content = base64.b64encode(sliced).decode()
    else:
        try:
            content = sliced.decode("utf-8")
        except UnicodeDecodeError:
            content = base64.b64encode(sliced).decode()
            return {"path": str(p), "content": content, "encoding": "base64", "truncated": len(data) > offset+limit, "total_bytes": total, "offset": offset, "next_cursor": offset+limit if len(data) > offset+limit else None}
    truncated = len(data) > offset+limit
    next_cursor = offset+limit if truncated else None
    return {"path": str(p), "content": content, "encoding": body.encoding or "utf8", "truncated": truncated, "total_bytes": total, "offset": offset, "next_cursor": next_cursor}

@router.post("/files/write")
def file_write(body: FileWriteRequest, authorization: str | None = Header(default=None)):
    if not verify_bearer(authorization):
        raise HTTPException(status_code=401, detail={"code":"unauthorized","message":"invalid bearer token"})
    c = _ensure_computer(body.computer_id)
    # credential_in_spec check for environment.yaml
    if "environment.yaml" in body.path or "environment.lock" in body.path:
        if credential_in_spec(body.content):
            audit({"computer_id": body.computer_id, "path": body.path, "decision":"deny","reason":"credential_in_spec"})
            raise HTTPException(status_code=403, detail={"code":"credential_in_spec","message":"environment spec must not contain secrets"})
    try:
        p = resolve_jail(body.path)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail={"code":"filesystem_denied","message":str(e)})
    # quota check 005: would write exceed workspace_gb?
    profile = machine_profile()
    quota_gb = profile["resources"]["workspace_gb"]
    quota_bytes = int(quota_gb * 1024**3)
    # estimate new file size
    if body.encoding == "base64":
        try:
            new_bytes = len(base64.b64decode(body.content))
        except Exception:
            raise HTTPException(status_code=400, detail={"code":"bad_encoding","message":"invalid base64"})
        content_bytes = base64.b64decode(body.content)
    else:
        content_bytes = body.content.encode("utf-8")
        new_bytes = len(content_bytes)
    # check existing size to compute delta
    existing = 0
    if p.exists() and p.is_file():
        try:
            existing = p.stat().st_size
        except Exception:
            existing = 0
    # workspace usage + delta
    try:
        used = workspace_usage_gb() * 1024**3
        if used - existing + new_bytes > quota_bytes:
            raise HTTPException(status_code=507, detail={"code":"workspace_quota_exceeded","message":"workspace_gb limit reached"})
    except HTTPException:
        raise
    except Exception:
        pass
    # atomic write: *.tmp + rename (005)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        # Use unique tmp to avoid collision; suffix handling for files without extension
        tmp = p.with_suffix(p.suffix + ".tmp") if p.suffix else Path(str(p)+".tmp")
        # Windows fsync: handle descriptor leak correctly; best-effort only on POSIX
        tmp.write_bytes(content_bytes)
        # fsync for durability (004) — best-effort, never leak fd
        try:
            import os as _os
            fd = _os.open(str(tmp), _os.O_RDWR)
            try:
                _os.fsync(fd)
            finally:
                _os.close(fd)
        except Exception:
            pass
        # On Windows, replace fails if target exists and is open; ensure we handle
        try:
            tmp.replace(p)
        except OSError:
            # Fallback: unlink dest then replace (handles WinError 32 stale handle case)
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
            tmp.replace(p)
        if body.mode:
            try:
                os.chmod(p, int(body.mode, 8))
            except Exception:
                pass
    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(status_code=403, detail={"code":"filesystem_denied","message":str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code":"write_failed","message":str(e)})
    # sync dirty tracking: only if persistent path
    from nallputer.core.workspace import is_ephemeral
    if not is_ephemeral(p):
        mark_dirty(str(p))
    sync = get_sync()
    audit({"computer_id":body.computer_id,"path":str(p),"decision":"allow","bytes":new_bytes})
    # environment spec hint — Windows uses backslashes, so normalize to forward slashes for check
    env_info = None
    norm = str(p).replace("\\", "/")
    if ".nallputer/state/environment" in norm:
        env_info = {"spec_rev": sync.last_sync_rev or 0, "lock_rev": 0, "drift": None}
    return {"path": str(p), "bytes_written": new_bytes, "sync_state": {"sync_state": sync.sync_state, "last_sync_rev": sync.last_sync_rev, "last_sync_at": sync.last_sync_at, "dirty_count": sync.dirty_count, "dirty_files": sync.dirty_files, "last_error": sync.last_error}, "environment": env_info}

@router.post("/files/list")
def file_list(body: FileListRequest, authorization: str | None = Header(default=None)):
    if not verify_bearer(authorization):
        raise HTTPException(status_code=401, detail={"code":"unauthorized","message":"invalid bearer token"})
    _ensure_computer(body.computer_id)
    try:
        p = resolve_jail(body.path)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail={"code":"filesystem_denied","message":str(e)})
    if not p.exists():
        raise HTTPException(status_code=404, detail={"code":"not_found","message":"path not found"})
    if not p.is_dir():
        raise HTTPException(status_code=400, detail={"code":"not_directory","message":"path is not directory"})
    limit = body.limit or 100
    if limit > 1000:
        limit = 1000
    entries = []
    # no recursive by default (005)
    items = sorted(p.iterdir(), key=lambda x: x.name)
    # cursor is opaque string: we use name offset
    start = 0
    if body.cursor:
        try:
            start = int(body.cursor)
        except ValueError:
            start = 0
    sliced = items[start:start+limit]
    truncated = len(items) > start+limit
    for child in sliced:
        try:
            stat = child.stat()
            typ = "dir" if child.is_dir() else "symlink" if child.is_symlink() else "file"
            entries.append({"name": child.name, "path": str(child), "type": typ, "size": stat.st_size if typ=="file" else None, "mtime": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(stat.st_mtime))})
        except OSError:
            entries.append({"name": child.name, "path": str(child), "type": "file", "size": None, "mtime": None})
    next_cursor = str(start+limit) if truncated else None
    return {"path": str(p), "entries": entries, "truncated": truncated, "next_cursor": next_cursor}
