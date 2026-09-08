# Phase 8 Implementation Plan — 011 into 8A–8F

**Status:** DRAFT — planning only, no `nallputer/` code changed here
**Date:** 2026-09-08
**Authority:** `011-production-architecture.md` LOCKED (`e82f9e4` → `5863dbc` review passed), `010-evaluation-full.md`, `5a44765` Windows 19/19, `2195f2b` Linux 20/20 (`213ms/0.92ms`, `v2`, `100/3`, `5→429`)
**Invariant:** **NALLY's contract does not change** — `GET /v1/machine`/`health`/`computer`/`exec`/`files` stay identical (`openapi.yaml` frozen). Phase 8 makes internals durable underneath.

---

## Execution order — `011 REVIEW → LOCKED → README sync → 8A→8F → production evaluation`

```
011 DRAFT (e82f9e4)
  ↓ REVIEW (this doc) → LOCKED (5863dbc)
  ↓ README sync (8 🟡)
  ↓ 8A Persistence adapter
  ↓ 8B Sync engine
  ↓ 8C Env reconstruct
  ↓ 8D Security
  ↓ 8E Lifecycle/recovery
  ↓ 8F Observability
  ↓ production evaluation (new gate, not 20/20 Lab Rat)
  ↓ production baseline
```

Each slice is **independently reviewable**; 8B needs 8A's store, 8C needs 8B's flush, 8E needs 8A+8B+8C, 8F is parallel.

---

## 8A — Persistence adapter (S3-compatible)

**Goal:** Replace local-FS stub `nallputer/core/sync.py` with `S3-compatible object store` canonical behind `external_canonical` abstraction (011 row 1). `An S3-compatible object store is the canonical persistence layer; the provider is deployment configuration.`

**Files**

- New `nallputer/core/persistence/` package:
  - `__init__.py` (interface `Persistence` with `get/put/delete/list + get_etag/put_if_match`)
  - `s3.py` (boto3 `S3Client` with `If-Match` via `IfMatch` header, `x-amz` + `ETag`, env `NALLPUTER_S3_ENDPOINT/BUCKET/REGION/ACCESS_KEY/SECRET`)
  - `local_fs.py` (existing local stub, now implements same interface for `NALLPUTER_S3_ENDPOINT=""` fallback → keeps `make eval-minimal` working without creds)
  - `factory.py` (`get_persistence()` reads env, returns S3 or local)
- Config `nallputer/app/config.py`: add `NALLPUTER_S3_*` vars + `NALLPUTER_CANONICAL` (`s3://bucket/computers` vs `file://...`)
- `tests/docker/Dockerfile.eval`: add `boto3 moto` for mocked S3 harness (no real creds in CI)

**Acceptance**

- `Persistence.put_if_match(manifest, etag)` succeeds with fresh etag, fails with stale etag → `409` mapped to `sync_state: degraded` retry (row 1,3).
- `tests/test_persistence.py` extended: write → `pending` → `flush` → `synced` works against `moto` S3 when `NALLPUTER_S3_ENDPOINT=mock`.
- No new endpoint shape; `POST /computer/{id}/sync` still `202`.

**Risks**

- S3 `503`/`NoSuchKey` on fresh boot → `health` `degraded` per `008` (row 2). Mitigate via `factory` fallback to `local` when env not set.

---

## 8B — Sync engine (dirty, debounce, flush, restore)

**Goal:** Turn `sync.py` stub (`pending→synced` in-memory) into real `debounced 3s + pre-stop flush 10s + on-start restore` (011 rows 2,3,8).

**Files**

- `nallputer/core/sync_engine.py` (new):
  - `DirtyTracker` (`add/mark_dirty`, `get_dirty`)
  - `debounce` (async `inotify`/`watchdog` or poll `inotify` fallback, `3s` coalesce, per-file atomic `*.tmp` → `put` → `manifest` last)
  - `flush()` (write all dirty + `manifest.json` with new `rev`, `If-Match`, `fsync` best-effort)
  - `restore(computer_id)` (fetch `manifest` → list `workspace/` prefix → download)
- `nallputer/app/main.py` lifespan: `startup` calls `restore`, `shutdown` calls `flush` within `10s` `SIGTERM` window (`tini` → `STOPSIGNAL SIGTERM` already in `006`).
- `nallputer/core/workspace.py`: keep `_ensure_workspace` fallback to `/tmp` for CI, but add `is_dirty` hook.

**Acceptance**

- `test_sync_pending_to_synced` passes with real store (dirty `4` → `synced 0` after `POST /sync`).
- `test_stop_start_persistence` writes `keep.txt` → `stop` (flush) → `start` (restore) → `read` `keep me` works against S3 (currently local FS stub already does, but now via object store).
- `GET /health` `sync_state` transitions `pending` → `synced` observable; `degraded` on S3 unreachable (simulate by bad endpoint).

---

## 8C — Environment reconstruction

**Goal:** Wire `environment.yaml` → `environment.lock` deterministic replay (011 row 4) behind `starting` restore.

**Files**

- `nallputer/core/env_reconstruct.py`:
  - `parse_environment_yaml(path)` → `spec` dict
  - `replay(spec, lock)` → `subprocess` `pip install --require-hashes` if `lock` exists else `pip install` from `yaml`, then `pip freeze > lock`, `pip check`
  - `write_lock(lock_path, content)`
- `nallputer/core/workspace.py`: `files/write` for `environment.yaml` already does `credential_in_spec 403` (007) — keep, add `spec_rev` bump → triggers `dirty` → `flush`.
- `nallputer/app/main.py` `startup` restore calls `replay` after `workspace` restore; failure → `recovering` + `health 503 env_replay_failed` + failed replay `run_id`.

**Acceptance**

- `test_environment_spec` write → `spec_rev` bump; after `stop→start` with mocked `environment.lock` containing `requests==2.32.0`, `pip list` shows it.
- `credential_in_spec` (`token: ghp_`) still `403`.
- Failure path: yanked version → `health` `env_replay_failed` (simulate by bad `index_url`).

---

## 8D — Production security enforcement

**Goal:** Turn `007` policy model into production enforcement (011 rows 5,11) without new endpoint shape.

**Files**

- `nallputer/core/security.py`: keep `verify_bearer` constant-time, `egress_check` allowlist `pypi.org...` (already `deny-by-default`), add `proxy` config `NALLPUTER_EGRESS_PROXY=127.0.0.1:3128`.
- New `nallputer/core/egress_proxy.py` (tiny forward proxy, ~100 lines, `http.server` or `tinyproxy` wrapper): allowlist `host:port` + `NO_PROXY` bypass for `nallputer.internal` + private-store, audit `{run_id,dst,decision}` without bodies.
- `nallputer/core/runtime.py`: keep `HTTP_PROXY` injection per-run + `NO_PROXY`, add `audit` append for `egress` decisions (already does `egress_blocked`).
- `nallputer/app/main.py`: start proxy thread on `startup` if `NALLPUTER_EGRESS_POLICY=deny-by-default`.

**Acceptance**

- `test_egress_policy` `evil 403` / `pypi succeeded` passes on Linux with proxy running (already passes via API preflight, but now also via proxy log).
- `test_credential_in_spec_blocked` still `403`.
- Proxy not required for `eval-minimal` (API preflight suffices), but must be present for prod `NALLPUTER_EGRESS_PROXY` env.

---

## 8E — Lifecycle / recovery

**Goal:** Wire `008` machine to real `starting`/`stopping`/`recovering` (011 rows 2,10).

**Files**

- `nallputer/core/lifecycle.py`: expand `Computer.state` transitions to call `sync_engine.flush` on `stopping` (≤10s), `sync_engine.restore`+`env_reconstruct.replay` on `starting`, `health` `degraded` on failure.
- `nallputer/routers/computer.py`: `POST /computer/{id}/stop` → `stopping→stopped` with `If-Match` flush; `POST /start` → `starting→running` with `uptime_sec` reset detection.
- `tests/docker/collect.py` `pids.max` refinement already noted — no runtime change, just harness.

**Acceptance**

- `test_stop_start_persistence` still `kept:true`.
- New `test_recovery` (not in 19, for prod): kill `sync_engine` S3 mock → `health` `degraded`, then restore → `ok`, same `computer_id`, `uptime_sec` reset observed, `009` reconnect backoff would succeed.

---

## 8F — Observability

**Goal:** Fill stubs with real `resources_usage` behind existing `GET /computer/{id}` shape (011 row 8).

**Files**

- `nallputer/core/metrics.py` (new): `pids_current` (`/sys/fs/cgroup/pids.current`), `memory.current` (`/sys/fs/cgroup/memory.current` or `memory.stat`), `cpu.stat`, `workspace_used_gb` (already), `sync_state`.
- `nallputer/routers/computer.py`: `resources_usage` now returns real `pids_used`, `memory_mb`, `cpu_millicores` instead of `0` stubs (Windows `0` remains informational).
- `nallputer/core/audit.py` (already append-only) + expose via `GET /health` `last_error`.

**Acceptance**

- Linux `GET /computer/{id}` shows `pids_used` ≈ `3` (as in `2195f2b` `pids.current 3`) not `0`.
- `pytest` minimal still `19/19` on Windows (stubs `0` acceptable) and `20/20` on Linux (real numbers).

---

## What remains blocked

- **No new endpoint shape** until a new decision says so — `openapi.yaml` stays frozen at `59d09ba` version.
- **No `003–009` reopen** — any needed change requires `Exception to 00X` per `011` template.
- **README** stays at `58b589a` until `011` lock → implementation → production evaluation adds the next `REPORT.md`.

---

## Sequencing & review

```
8A (store) ─┐
            ├→ 8B (sync) ─┬→ 8C (env) ─┬→ 8E (lifecycle) ─┬→ prod eval (new gate, not 20/20 Lab Rat)
8D (security) ┘             └→ 8F (observability) ────────┘
```

Each slice gets its own `feat: 8X — …` commit, `pytest tests -k "not linux"` must stay `19/19` after each, `make eval-linux` must stay `20/20` after `8A–8C`.

---

## Review gate

This plan itself is a `DRAFT`. Lock it by approving the 6 slices and the `no new endpoint` invariant, then `8A` can branch from `011 LOCKED` (`5863dbc`).
