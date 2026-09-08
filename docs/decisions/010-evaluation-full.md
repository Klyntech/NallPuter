# NallPuter Decision 010 — Evaluation Full (Linux/Docker) Plan

**Status:** LOCKED (plan only — no runtime changes)
**Date:** 2026-09-08
**Review gate:** Phase 7-full — *executable experiment, not architecture*
**Depends on:** `5a44765` (Phase 7 minimal 19/19), `59d09ba` MVP (`003`–`009` + `openapi.yaml`), `tests/results/REPORT.md` (Windows informational)
**Blocks:** Phase 8 Production — Phase 8 must not be drafted until this plan's Linux numbers exist

---

## Decision

**Phase 7-full is a locked measurement plan that re-uses the 19-test semantics against the actual Linux/Docker runtime.**

No contract changes (`003`–`009`), no runtime changes, no Phase 8 architecture. The plan is executable (`make eval-linux`) when Docker becomes available and produces a `tests/results/linux/REPORT.md` that is directly comparable to the `5a44765` Windows `tests/results/REPORT.md`.

The comparison is the gate: **evidence table must have two columns, not one.**

---

## Scope — extremely tight

| In | Out |
|----|-----|
| `tests/docker/` harness (Dockerfile/compose + runner) | Any change to `nallputer/` |
| `Makefile` target `eval-linux` | Any change to `003`–`009` or `openapi.yaml` |
| `docs/decisions/010-evaluation-full.md` (this file) | Any Phase 8 production decision |
| Re-use of the existing 19 tests (same `exec_and_poll`, same assertions) | New feature tests |
| Linux measurements written to `tests/results/linux/*.json` + `tests/results/linux/REPORT.md` | Threshold gate failures — still measure-only |

**Reuse rule:** The 19 tests in `tests/test_*.py` are the semantics. The Linux harness does not fork them; it runs the *same* `pytest tests/` inside the container (plus a small Linux-only supplemental check for cgroup/pids). Any test that is inherently Windows-specific is parameterized, not duplicated.

---

## What must be measured on Linux (the full 13-dim view where possible without Render)

From `requirements.md` Phase 9 evaluation requirements; minimal gate covered 6, full adds the 7 that require Linux:

| Dim | Windows minimal (`5a44765`) | Linux full (this plan) | How |
|-----|------------------------------|------------------------|-----|
| **Latency** | `304ms` / `87ms` (3.49x) | ⏳ | Same `echo latency-probe` via `TestClient` inside container vs `bash -c "echo"` baseline inside same container (no `cmd.exe` overhead). |
| **Startup** | warm `17ms`, cold `13ms*` | ⏳ | Warm: `GET /health+machine`. Cold: `docker run` cold boot → `GET /health` polls until `ok` (real `tini` + `cgroup` probe + restore). |
| **Timeout + Cancel** | `timed_out`/`cancelled` via `taskkill` | ⏳ | Same commands, but verifies Linux `setsid`+`killpg` path (pgid tree-kill, not `taskkill`). |
| **Isolation/Egress** | jail `403`, `evil` `403`, `pypi` `succeeded` | ⏳ | Same assertions; additionally checks `HTTP_PROXY=127.0.0.1:3128` is present in `exec` env. |
| **Persistence/Sync** | `pending→synced`, `stop→start` keep | ⏳ | Same plus `environment.yaml/lock` replay check (write spec → `stop`→`start`→ verify replay log). |
| **Output** | empty/trunc/pagination correct | ⏳ | Same (Linux `echo -n` now truly empty vs Windows `-n` nuance). |
| **RAM** | N/A (stub `0`) | ⏳ | `GET /v1/computer/{id}` `resources_usage.memory_mb` + `docker stats` peak during `stress --vm 1` (if available) or `python -c "bytearray(80*1024*1024)"`. Verifies `memory.max=512M` OOM path (not a gate, just measurement). |
| **CPU** | N/A | ⏳ | `cpu.max` throttling observable via `time python -c "for i in range(10000000): pass"` vs baseline. |
| **PIDs** | `pids_used=0` stub | ⏳ | `cat /sys/fs/cgroup/pids.current` vs `GET /v1/computer` `pids_used`; verifies `pids.max=100` is `v2` with `pids.current` incrementing under `stress --fork`. |
| **Concurrency** | Not exercised (informational) | ⏳ | 5-way: fire 5 concurrent `sleep 1` execs, measure 6th → `429 concurrency_limited` (006 `min(cpu/100,pids/10)`). |
| **Recovery** | `health` `ok` only | ⏳ | Kill container (`docker stop` 10s) → `docker start` → poll `health` `recovering→ok`, verify same `computer_id` + `uptime_sec` reset + workspace file still `keep`. |
| **Env reconstruct** | write/read of spec only | ⏳ | Full: write `environment.yaml` → `stop`→`start` → assert `pip list` shows replayed package (004). |
| **Orphan cleanup** | `taskkill` | ⏳ | Linux: spawn `bash -c "sleep 10 & sleep 10 & wait"` then `DELETE` → verify `pids.current` drops + no zombies (`tini` reaps). |

`*` Windows cold `13ms` is import-only; Linux cold is container boot seconds — explicitly not comparable beyond shape.

---

## Harness shape (runnable when Docker exists)

```
tests/docker/
  Dockerfile.eval      # FROM python:3.12-slim → tini + nallputer + pytest
  docker-compose.eval.yml  # single service: nallputer-eval (no private net needed locally)
  run.sh               # sh -e: docker compose -f docker-compose.eval.yml run --rm nallputer-eval
tests/results/linux/
  REPORT.md            # same shape as tests/results/REPORT.md but Linux column filled
  *.json               # same filenames as tests/results/*.json but Linux values
Makefile:
  eval-linux           # builds image, runs harness, writes linux/REPORT.md
```

**`make eval-linux` (at repo root):**

```make
eval-linux:
	docker build -f tests/docker/Dockerfile.eval -t nallputer:eval .
	docker compose -f tests/docker/docker-compose.eval.yml up --build --abort-on-container-exit
	# container writes to mounted ./tests/results/linux/ which is .gitignored except REPORT.md/json
```

Inside the container:

```sh
pytest tests -v --junitxml=tests/results/linux/junit.xml
python tests/docker/collect.py  # reads tests/results/linux/*.json + Windows JSON, writes evidence table
```

**Reuse:** `tests/conftest.py` already uses `TestClient`; inside Docker it still uses `TestClient` (no HTTP server needed). The same 19 tests run unmodified. A tiny Linux-only supplement `tests/test_linux_cgroup.py` (skipped on Windows via `pytest.mark.skipif os.name=="nt"`) adds `v2`/`pids.current`/`concurrency` checks.

---

## Evidence table (must be produced)

The Linux run must produce this table with both columns populated, directly comparable to `5a44765`:

| Metric                  | Windows/TestClient (`5a44765`) | Linux/Docker (`tests/results/linux/*`) |
| ----------------------- | ------------------------------: | -------------------------------------: |
| Exec latency            |                         304 ms |                                   ⏳ |
| Local baseline          |                          87 ms |                                   ⏳ |
| Overhead                |                          3.49× |                                   ⏳ |
| Warm startup            |                          17 ms |                                   ⏳ |
| Cold startup            |                         13 ms* |                                   ⏳ |
| cgroup v2 enforcement   |                            N/A |                                   ⏳ |
| `pids.current`          |                            N/A |                                   ⏳ |
| 5-way concurrency       |                              ⏳ |                                   ⏳ |
| Process-group kill      |               Windows `taskkill` |                    Linux `setsid`/`killpg` |
| Environment replay      |                        partial |                                   ⏳ |
| Private-network latency |                              ⏳ |                                   ⏳ |

`*` not representative of Render cold boot.

**Gate:** Phase 7-full is **measure-only**. No `PASS/FAIL` threshold on latency or overhead. The gate is: **does the Linux run produce the same contract `status`/`code` shapes as Windows (19/19), plus cgroup `v2` and concurrency `429` where applicable?** If yes, evidence is sufficient for Phase 8.

---

## What this does NOT decide

- No change to `003`–`009`, `openapi.yaml`, or `nallputer/` — this file is a plan, not a migration.
- No Phase 8 production choice (Firecracker/Kata vs VM, snapshot scope, GPU, multi-user) — those wait for Linux numbers.
- No Docker-in-Docker on Render — local Docker only.
- No new allowlist entries — `pypi.org,registry.npmjs.org,github.com` remains.

---

## Review gate outcome

Locked 2026-09-08 as the **executable definition of Phase 7-full**. Implement the scaffold (`tests/docker/` + `Makefile`) now; execution (`make eval-linux`) waits for Docker. Phase 8 remains blocked until `tests/results/linux/REPORT.md` exists.

## Evidence trace

- `requirements.md` Phase 9 evaluation requirements: 13 dims, `local subprocess` vs `NALLPUTER`.
- `006-runtime-model.md`: cgroup v2 `v2` vs `v1` probe, `pids.max=100`, `cpu.max`, `concurrency min(cpu/100,pids/10)`.
- `004-persistent-state.md`: `environment.yaml/lock` replay, `manifest.json` + restore.
- `007-security-model.md`: `127.0.0.1:3128` + `HTTP_PROXY` injection, deny-by-default.
- `008-lifecycle-model.md`: `uptime_sec` reset → recovery, `stop→start` restore.
- `tests/results/REPORT.md` (`5a44765`): Windows informational baseline this plan compares against.
