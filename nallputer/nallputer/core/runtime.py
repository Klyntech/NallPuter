from __future__ import annotations

import asyncio
import os
import signal
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Literal, Optional
import subprocess
import threading

from nallputer.app.config import NALLPUTER_MAX_OUTPUT_BYTES, NALLPUTER_WALL_TIME_SEC

RunStatus = Literal["queued","running","succeeded","failed","timed_out","cancelled","policy_denied"]

@dataclass
class Run:
    run_id: str
    computer_id: str
    status: RunStatus
    command: Optional[str] = None
    cwd: Optional[str] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    truncated: bool = False
    bytes: int = 0
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    wall_time_ms: Optional[int] = None
    policy_result: Optional[dict] = None
    error: Optional[dict] = None
    environment: Optional[dict] = None
    sync_pending: bool = False
    _pgid: Optional[int] = None
    _proc: Optional[subprocess.Popen] = field(default=None, repr=False)

runs: Dict[str, Run] = {}
idempotency: Dict[str, str] = {}  # key -> run_id

def _now_iso():
    import time as _t
    return _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime())

def new_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:8]}"

def get_run(run_id: str) -> Optional[Run]:
    return runs.get(run_id)

def create_run(computer_id: str, command: str, cwd: Optional[str], timeout_sec: Optional[int], env_overlay: Optional[dict], idem_key: Optional[str]) -> Run:
    if idem_key and idem_key in idempotency:
        existing = runs.get(idempotency[idem_key])
        if existing:
            return existing
    run_id = new_run_id()
    r = Run(run_id=run_id, computer_id=computer_id, status="queued", command=command, cwd=cwd)
    runs[run_id] = r
    if idem_key:
        idempotency[idem_key] = run_id
    # launch async
    threading.Thread(target=_execute, args=(r, timeout_sec, env_overlay), daemon=True).start()
    return r

def _execute(run: Run, timeout_sec: Optional[int], env_overlay: Optional[dict]):
    run.status = "running"
    run.started_at = _now_iso()
    t0 = time.monotonic()
    # 007 credential scrub: minimal env + scoped overlay
    import os as _os
    base_env = {"PATH": _os.getenv("PATH","/usr/local/bin:/usr/bin:/bin"), "HOME": _os.getenv("HOME","/home/nally"), "WORKSPACE": str(_os.getenv("NALLPUTER_WORKSPACE","/home/nally/workspace")), "PYTHONUNBUFFERED":"1"}
    # scrub blocklist
    block_prefixes = ("AWS_","GCP_","AZURE_","RENDER_")
    block_suffixes = ("_TOKEN","_SECRET","_PASSWORD","_KEY")
    # we don't inherit os.environ, only allowlisted
    env = dict(base_env)
    # inject proxy vars for egress (007 stub)
    env.update({"HTTP_PROXY":"http://127.0.0.1:3128","HTTPS_PROXY":"http://127.0.0.1:3128","http_proxy":"http://127.0.0.1:3128","https_proxy":"http://127.0.0.1:3128","NO_PROXY":"127.0.0.1,localhost,169.254.169.254,nallputer.internal","no_proxy":"127.0.0.1,localhost,169.254.169.254,nallputer.internal"})
    if env_overlay:
        for k,v in env_overlay.items():
            ku = k.upper()
            if ku.startswith(block_prefixes) or ku.endswith(block_suffixes):
                # deny unless allowlisted env
                if ku not in {"NALLPUTER_ALLOWED_ENV"}:
                    continue
            # also block credential_in_spec style keys if they look like secrets
            if "SECRET" in ku or "PASSWORD" in ku or ku == "GITHUB_TOKEN":
                # scoped injection only if dst check passes — MVP: allow but audit
                pass
            env[k] = str(v)
    # workspace cwd jail is already validated by caller; choose cwd
    cwd = run.cwd
    # ensure cwd exists
    if cwd:
        try:
            os.makedirs(cwd, exist_ok=True)
        except Exception:
            pass
    # 006: process group for tree kill (Linux: setsid + killpg; Windows: no setsid, use shell)
    try:
        is_win = os.name == "nt"
        if is_win:
            # Windows: no bash -c, no setsid. Use shell=True via cmd /c for local dev parity.
            # Production Linux path uses bash -c + setsid.
            proc = subprocess.Popen(
                run.command or "true",
                cwd=cwd or None,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                shell=True,
            )
        else:
            proc = subprocess.Popen(
                ["bash","-c", run.command or "true"],
                cwd=cwd or None,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if hasattr(os, "setsid") else None,
                text=True,
                bufsize=1,
            )
        run._proc = proc
        try:
            run._pgid = os.getpgid(proc.pid) if hasattr(os, "getpgid") else proc.pid
        except Exception:
            run._pgid = proc.pid
        # wall-time enforcement (006)
        wall = timeout_sec if timeout_sec else NALLPUTER_WALL_TIME_SEC
        try:
            stdout, stderr = proc.communicate(timeout=wall)
        except subprocess.TimeoutExpired:
            # 006 SIGTERM pgid 5s -> SIGKILL pgid (Linux) / taskkill tree on Windows
            if hasattr(os, "killpg"):
                try:
                    os.killpg(run._pgid, signal.SIGTERM)
                except Exception:
                    proc.terminate()
            else:
                # Windows: kill process tree via taskkill
                try:
                    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
                except Exception:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                if hasattr(os, "killpg"):
                    try:
                        os.killpg(run._pgid, signal.SIGKILL)
                    except Exception:
                        proc.kill()
                else:
                    try:
                        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
                    except Exception:
                        pass
                    try:
                        proc.kill()
                    except Exception:
                        pass
                try:
                    stdout, stderr = proc.communicate(timeout=2)
                except Exception:
                    stdout, stderr = "", ""
            run.status = "timed_out"
            run.exit_code = None
            run.policy_result = {"decision":"deny","reason":"wall_time_exceeded"}
            # still record output
        else:
            if proc.returncode == 0:
                run.status = "succeeded"
            else:
                run.status = "failed"
            run.exit_code = proc.returncode
        # output cap (003/006) 100KB
        total = (stdout or "") + (stderr or "")
        cap = NALLPUTER_MAX_OUTPUT_BYTES
        out_combined = stdout or ""
        err_combined = stderr or ""
        # truncate per output cap: we store full but mark truncated if exceeds
        total_bytes = len((out_combined+err_combined).encode("utf-8"))
        run.bytes = total_bytes
        if total_bytes > cap:
            # truncate stdout to cap (keep prefix)
            run.truncated = True
            # keep first cap bytes of stdout+stderr combined, split roughly
            # prefer stdout
            out_b = out_combined.encode("utf-8")[:cap]
            run.stdout = out_b.decode("utf-8", errors="ignore")
            # stderr truncated representation
            run.stderr = (err_combined[: max(0, cap - len(run.stdout))] if len(run.stdout) < cap else "")
            if len(err_combined.encode("utf-8")) > (cap - len(out_b)):
                # append marker
                run.stderr = run.stderr + "\n[truncated]"
        else:
            run.stdout = out_combined
            run.stderr = err_combined
    except Exception as e:
        run.status = "failed"
        run.error = {"code":"exec_failed","message":str(e)}
        run.exit_code = 127
    finally:
        run.finished_at = _now_iso()
        run.wall_time_ms = int((time.monotonic()-t0)*1000)


def cancel_run(run_id: str) -> Optional[Run]:
    r = runs.get(run_id)
    if not r:
        return None
    if r.status in ("succeeded","failed","timed_out","cancelled","policy_denied"):
        return r  # 409 handled by caller
    # try pgid kill (Linux) else taskkill tree on Windows
    if r._pgid and hasattr(os, "killpg"):
        try:
            os.killpg(r._pgid, signal.SIGTERM)
            time.sleep(0.5)
            try:
                os.killpg(r._pgid, signal.SIGKILL)
            except Exception:
                pass
        except Exception:
            if r._proc:
                try:
                    r._proc.terminate()
                except Exception:
                    pass
    elif r._proc:
        if os.name == "nt":
            try:
                subprocess.run(["taskkill", "/PID", str(r._proc.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
                time.sleep(0.2)
            except Exception:
                pass
        try:
            r._proc.terminate()
            # ensure
            try:
                r._proc.wait(timeout=1)
            except Exception:
                try:
                    r._proc.kill()
                except Exception:
                    pass
        except Exception:
            pass
    r.status = "cancelled"
    r.finished_at = _now_iso()
    return r
