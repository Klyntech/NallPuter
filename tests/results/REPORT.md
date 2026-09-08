# Phase 7 Minimal Gate — Measure-Only Report

**Target:** `59d09ba` MVP v0.1 + 3 post-MVP fixes (egress default, Windows pgid, atomic write)
**Date:** 2026-09-08T18:30:39Z (`19 passed, 3 initial failures fixed`)
**Mode:** measure-only — no threshold failures; numbers are informational, not a production gate
**Env:** Windows local via `TestClient`, no Docker (Linux cgroup numbers stubbed, marked informational)
**Commit:** `59d09ba` + working-tree fixes (pending commit `nallputer/core/{security,runtime,files}` + `tests/` harness)

## Verdict (minimal gate)

**Is NallPuter good enough to be NALLY's computer?** — **YES for contract correctness.**

All 6 minimal dims return correct contract shapes with reasonable local latency. Full operational viability (RAM/CPU/PID, concurrency 5x, true cgroup enforcement) requires Docker Linux and is deferred to Phase 7-full.

| Dim | What we measured | Result | Evidence |
|-----|------------------|--------|----------|
| **Latency** | `echo latency-probe` via NALLPUTER vs `subprocess.run` baseline | `304.67ms` vs `87.38ms` delta `217ms` overhead `3.49x` | `latency.json` — Windows TestClient overhead includes FastAPI routing + thread spawn; Docker Linux will be lower (no shell cmd.exe) but overhead >1x is expected for API hop. |
| **Startup** | warm `GET /health+machine` vs cold (fresh import+lifespan) | warm `17.67ms` (`uptime 5s, synced`), cold `13.39ms` | `startup_warm.json`, `startup_cold.json` — cold on Windows is import only; real cold on Render includes container boot (seconds) not measured here. |
| **Timeout + Cancel** | `timeout_sec=1` on `sleep 3` → `timed_out`; `DELETE` on `sleep 5` → `cancelled` | `timed_out` wall `1234ms`, `cancelled` | `timeout.json`, `cancel.json` — pgid taskkill tree-kill on Windows now works (was `running` before fix). |
| **Isolation/Egress** | FS jail + egress deny + credential guard | `/etc/passwd` → `403 filesystem_denied`, `evil.com` → `403 policy_denied`, `pypi.org` → `succeeded` (allowlist hit), `environment.yaml` with `token:` → `403 credential_in_spec` | `jail.json`, `egress.json`, `credential.json` — egress allowlist default now `pypi.org,registry.npmjs.org,github.com` (was empty string before fix); FS jail now correctly denies absolute outside-workspace paths (was doubled prefix). |
| **Persistence/Sync** | `write → pending → flush → synced`, `read/list` round-trip, `base64`, `stop→start` keeps file | `write 17B`, `read 17B`, `pending 4 dirty → synced 0 dirty after flush`, `base64` ok, `stop→start` kept `keep.txt` | `files_basic.json`, `sync.json`, `base64.json`, `stop_start.json`, `env_spec.json` — sync stub `pending→synced` correct; full external canonical + env replay not exercised (needs stop→new runtime). |
| **Output Correctness** | empty, exact, truncation 200KB, pagination | empty `""` explicit (was `-n` before fix), `hello-nallputer` exact, `200001B` truncated `true`, `cursor` pagination 200B combined ok | `empty_output.json` (fixed to `python -c exit 0`), `output_exact.json`, `truncation.json`, `pagination.json` — Windows `echo -n` nuance fixed. |

## What was fixed to get to 19/19

| Failure (initial `3 failed`) | Root cause | Fix |
|------------------------------|------------|-----|
| `test_egress_policy` pypi blocked | `security.py` default `NALLPUTER_EGRESS_ALLOWLIST=""` vs `config.py` default `pypi.org,...` — mismatch caused `external:443` generic deny path | `security.py` default now `"pypi.org,registry.npmjs.org,github.com"` matching `config` + `render.yaml` (007). |
| `test_empty_output` got `-n` | Windows `cmd` `echo -n` prints literal `-n`, not empty | Test now uses `python -c "import sys; sys.exit(0)"` cross-platform empty. |
| `test_environment_spec` env `None` | `files.py` check `".nallputer/state/environment" in str(p)` fails on Windows backslashes `C:\...\.nallputer\...` | Normalize `str(p).replace("\\","/")` before check. |

Also: `runtime.py` Windows `taskkill /T /F` for `timed_out`/`cancel` tree-kill (previously `terminate` left `python` child alive → timeout never fired), `workspace.py` absolute workspace prefix handling (was doubling `C:\home\nally\workspace\home\nally\workspace`), `files.py` atomic write `O_RDWR + finally close + unlink fallback` for `WinError 32`, `computer.py` `POST /computer` now `201`.

## Windows informational caveats (not gates)

- `cgroup mode=none` (no `/sys/fs/cgroup/cgroup.controllers` on Windows) → `GET /health` still `ok` with `pids_used=0` stub (Linux will be `v2` + `pids.current`). No gate depends on this.
- `pids_used=0`, `memory_mb=0` in `GET /computer` — stubbed.
- Process-group kill uses `taskkill /T /F` instead of `killpg` — same contract (`cancelled`/`timed_out`), different syscall.
- Workspace path is `C:\home\nally\workspace` not `/home/nally/workspace` — jail semantics identical, just printed with backslashes.
- `startup cold` on Windows is `13ms` import, not Render container boot seconds.

## Artifacts

```
tests/results/
  latency.json, latency_poll.json
  startup_warm.json, startup_cold.json
  timeout.json, cancel.json, reserved_501.json
  jail.json, egress.json, credential.json
  files_basic.json, sync.json, base64.json, env_spec.json, stop_start.json
  empty_output.json, output_exact.json, truncation.json, pagination.json
```

All JSON include `ts` and are measure-only. No `PASS/FAIL` thresholds beyond contract `status`/`code` checks in `pytest`.

## Next — evidence-driven Phase 8

Do **not** modify runtime yet. This report is the evidence for Phase 8. Only Docker Linux `Phase 7-full` can measure:

- `RAM/CPU/PID` true cgroup enforcement (`memory.max` OOM, `pids.max=100`, `cpu.max`)
- Concurrency `5` (`min(cpu/100,pids/10)`) under load
- `environment.yaml/lock` full replay after `stop→new instance` (004)
- Large-file chunking vs `>5MB` trade-off, snapshot `501` future path
- Private networking latency (Render private `https://nallputer.internal` vs `http://localhost`)

Phase 7 minimal: **MEASURED, 19/19 PASS, informational deltas recorded.**
