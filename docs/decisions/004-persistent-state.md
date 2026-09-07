# NallPuter Decision 004 — Persistent Computer State (Canonical External Storage)

**Status:** LOCKED
**Date:** 2026-09-07
**Review gate:** Phase 2b — requires Decision 003 (Machine Contract) locked first
**Depends on:** `003-machine-contract.md` (`persistence.*`, `restart_behavior`, `capabilities`)
**Blocks:** Phase 3 (Machine & Execution API Contract), Phase 4 (Runtime), Phase 6 (MVP)

---

## Decision

**The NallPuter runtime is disposable; the external persistent store is the canonical source of truth.**

Render (Lab Rat #1) provides an *ephemeral machine* with an optional Persistent Disk mount. NallPuter does **not** equate that disk with the computer. Instead:

```
              NALLY
                │ API (Bearer, private network)
                ▼
           NALLPUTER
     ┌──────────────────┐
     │ Runtime          │
     │ ephemeral machine│
     │ /workspace       │  ← cache / execution view
     │ processes, tools │
     └────────┬─────────┘
              │ sync engine (debounced + flush + restore)
              ▼
     EXTERNAL PERSISTENT STORAGE  ← canonical
     ┌──────────────────┐
     │ files            │
     │ metadata         │
     │ snapshots/version│ (v0.2+)
     │ machine state    │
     │ environment spec │
     └──────────────────┘
```

**Persistence is not backup.** The external store is not a periodic dump; it is what the `computer_id` *is*. If the store says `computer_id=cmp_abc` has file `projects/foo/main.py@rev 42`, then after any restart — even total replacement of the underlying host — a new runtime that restores that `computer_id` must present the same workspace to NALLY.

**Three persistence axes are distinct** (fixing the earlier conflation):

| Axis | v0.1 `MachineProfile` value | Survives `instance` recreate? | Mechanism |
|------|-----------------------------|------------------------------|-----------|
| **Workspace** (`projects/`, `files/`, `artifacts/`, config) | `external_canonical` | ✅ Yes | Sync engine → external store → restore |
| **Package environment** (pip, npm, apt, toolchains) | `reconstructible` | ⚠️ Via reconstruction, not raw FS | Canonical *environment spec* + deterministic replay (see § Environment) |
| **Machine state** (RAM, running processes, open sockets) | `ephemeral` | ❌ No | v0.1: not promised. v0.2+ `pause/resume` via Firecracker/Kata |

A Render restart is therefore:

```
Before restart                  After restart
──────────────                  ─────────────
NallPuter (old instance)        New NallPuter instance
  │ workspace changes             │ restore/sync workspace
  │ env spec changes              │ replay environment spec
  └→ persistent store             └→ same computer_id, same workspace, same reconstructed packages
        ↑                              │
        └──────── canonical ────────────┘

From NALLY view: computer_id, workspace, files, and (reconstructed) packages are identical.
Only observable delta: GET /v1/health uptime_sec reset, possibly short cold-restore delay.
```

---

## What is synchronized vs. what is ephemeral

NALLY must not pay sync cost for caches, and NALLPUTER must not leak ephemeral state into the canonical store.

**Canonical layout on external store** (per `computer_id`):

```
/computers/cmp_<id>/
  manifest.json              # computer_id, revision, timestamps, checksums
  workspace/                 # mirrors /home/nally/workspace (persistent subset)
    projects/
    files/
    artifacts/
    .nallputer/
      state/
        environment.yaml     # ← the scrutiny item (see § Environment)
        environment.lock     # resolved, content-hashed
        sync-state.json      # last synced revision, dirty set
  snapshots/                 # v0.2+ only
  logs/                      # optional, bounded
```

**Runtime view inside ephemeral machine:**

| Path | Persistence | Synced? | Notes |
|------|-------------|---------|-------|
| `/home/nally/workspace/projects/**` | `persistent` | ✅ | User code, first-class durable |
| `/home/nally/workspace/files/**` | `persistent` | ✅ | Inputs/outputs |
| `/home/nally/workspace/artifacts/**` | `persistent` | ✅ | Build outputs |
| `/home/nally/workspace/.nallputer/state/**` | `persistent` | ✅ | Environment spec, machine state |
| `/home/nally/workspace/tmp/**` | `ephemeral` | ❌ | Scratch, safe to discard |
| `/tmp`, `/var/tmp` | `ephemeral` | ❌ | |
| `/workspace/.cache`, `**/__pycache__`, `**/node_modules/.cache`, `**/.pytest_cache` | `ephemeral` | ❌ | Excluded by default |
| `/home/nally/workspace/.cache/**` if NALLY creates it | `ephemeral` | ❌ | Explicit `ephemeral_paths` in MachineProfile |

The profile advertises `ephemeral_paths` and `persistent_paths` so NALLY can place data correctly without guessing provider behavior.

---

## Sync engine — debounced + flush + restore (locked for v0.1)

**Chosen:** `debounced continuous sync` + `pre-stop flush` + `on-start restore`. Not continuous byte-for-byte, not snapshot-only.

### Why this over alternatives

| Alternative | Verdict | Reason |
|-------------|---------|--------|
| Pure periodic full snapshot (e.g., every 5m) | Rejected | Loses up to 5m of work; NALLY cannot trust “restart and nothing happened” |
| Pure byte-for-byte streaming (FS watcher → immediate PUT per write) | Rejected | Chatty, expensive, amplifies tmp/cache churn; object-store PUT storms |
| Manual `POST /snapshot` only | Rejected | Requires NALLY to remember to snapshot; violates “computer” mental model |
| **Debounced + flush + restore** | **Selected** | Balances durability with cost; NALLY never explicitly manages persistence |

### Behavior (normative)

1. **Write coalescing:** FS watcher (inotify) + write buffer. On change to any `persistent_paths` file, debounce **2–5s** (configurable, default 3s), then upload deltas (content-addressed chunks or whole-file PUT if file < 5 MB). Multiple rapid writes to same file collapse to one PUT.
2. **Pre-stop flush:** SIGTERM handler: `fsync` + `sync dirty set` + write `manifest.json` with new revision. Blocks shutdown up to **10s** (Render graceful window). If flush fails, manifest stays at prior revision — NALLY sees last consistent state, not torn state.
3. **On-start restore:** New instance on boot: `fetch manifest.json` → `restore workspace/` → `replay environment spec` → `mark computer_id ready` → `GET /v1/health → ready`. If external store unreachable, NALLPUTER stays `recovering` (not `running`) and `GET /v1/health` returns `503` with `sync_state: degraded`.
4. **Consistency:** Strong eventual after flush. Mid-debounce crash loses at most **one debounce window** of unflushed deltas. This is acceptable for v0.1 because NALLY’s execs are synchronous and the API can return `sync_pending: true` in `POST /v1/exec` response when dirty set non-empty — NALLY may call `POST /v1/computer/{id}/sync` (optional, 202) if she needs a durability barrier.
5. **Atomicity:** Per-file atomic PUT + `manifest.json` commit last (two-phase). Partial workspace upload without manifest update is not visible to next restore. Old manifest always points to a consistent snapshot.
6. **Multi-writer:** Single writer per `computer_id` (one active runtime). External store uses `If-Match: etag(manifest)` to reject stale flushes — prevents split-brain if two runtimes briefly overlap during Render redeploy.

### Lab Rat #1 mapping (Render)

- External store **abstraction** is `external_canonical`. Lab Rat implementation: **Render Persistent Disk as local cache + background S3/R2 as canonical** OR **disk alone with abstraction shim** if object store not yet wired.
- Recommended for v0.1 speed: Use **Render Disk @ `/mnt/nallputer-cache`** as write-through cache for the abstraction, with the *same sync engine* code path as S3. Swapping to pure S3 later is a config change, not an API break. This keeps “provider-neutral” true while staying feasible on Render.
- If only disk is available and no object store is configured, the decision still holds: the disk is *accessed only via the sync engine interface*, never as “the computer is the disk”. The code path is identical; only `persistence.workspace_mechanism` in `MachineProfile` reports `persistent_disk` vs `object_store`.

---

## Environment representation & reconstruction — the scrutiny item (locked)

**Problem:** `pip install pandas` mutates the live FS. If `persistence.packages == "reconstructible"` and the runtime is `ephemeral`, a raw FS copy of `/usr/local/lib/python` is both expensive and non-portable, and loses the *intent* behind the install (which version? which extras? which index?).

**Principle:** Persist **declarative intent**, replay **deterministically**. The FS is a cache; the spec is canonical.

### v0.1 environment spec (canonical, lives in persistent store)

File: `/home/nally/workspace/.nallputer/state/environment.yaml` — NALLY and NALLPUTER both write here; NALLPUTER owns replay.

```yaml
# NallPuter Environment Spec v0.1 — declarative, deterministic, content-hashable
version: 1
computer_id: cmp_01j9f2...
base:
  image: "python:3.12-slim"          # Lab Rat base image; portable hint, not hard pin
  os: "debian-bookworm"
system:
  apt:                               # optional, ordered
    - { name: "ffmpeg", version: "6.*" }
    - { name: "build-essential" }    # version omitted → latest at reconstruct time, then lock pins it
python:
  manager: "pip"                     # v0.1: pip only. v0.2+: uv/poetry
  python_version: "3.12.*"
  packages:
    - "pandas==2.2.3"
    - "numpy==1.26.4"
    - "fastapi==0.115.*"
  index_url: "https://pypi.org/simple"  # optional
  extra_index_urls: []
  # Stores extras/markers exactly as requested:
  # - "requests[security]==2.32.* ; python_version >= '3.11'"
node:
  manager: "npm"                     # optional
  node_version: "20.*"
  packages: []
env:
  vars:                              # non-secret env only; secrets are injected, never stored in spec
    PYTHONPATH: "/home/nally/workspace/projects"
hooks:
  post_install:                      # optional, explicit, auditable
    - "pip check"
```

**Lock file:** `environment.lock` — generated by NALLPUTER after successful install, contains content hashes (`pip freeze` exact pins, `apt-cache policy` exact versions). On restore, NALLPUTER replays from `environment.lock` first (fast, exact), falls back to `environment.yaml` resolution if lock missing.

### How it works (normative, implements `package_persistence=reconstructible`)

1. **NALLY wants a package:** She has two durable paths:
   - **Preferred (declarative):** `POST /v1/files/write` to update `.nallputer/state/environment.yaml` (add `pandas==2.2.3`), then `POST /v1/exec` with `{"command": "nallputer env apply"}` (or auto-apply if NALLPUTER watches the spec). This is durable by definition — spec is in `persistent_paths`, so it is synced canonically before the install even starts.
   - **Ad-hoc (imperative):** `POST /v1/exec` → `pip install pandas==2.2.3`. The runtime intercepts via shim/wrapper (`pip` wrapper that logs to `environment.yaml` + runs real `pip`). If interception is missed, a periodic reconciler diffs `pip freeze` against `environment.yaml` and appends drift with a warning `policy_result: env_drift_detected`. Ad-hoc installs still mutate live FS immediately so NALLY sees the effect, but durability comes from the spec.

2. **Install outcome:** On success, NALLPUTER writes `environment.lock`, marks sync dirty, debounced sync → canonical store. `GET /v1/exec/{id}` observation includes `environment: { spec_rev, lock_rev, drift }` so NALLY can verify durability.

3. **Restore after restart:** New runtime boot sequence:
   ```
   fetch manifest + workspace + environment.yaml/lock from canonical store
     ↓
   if lock exists → pip install --no-deps --require-hashes -r environment.lock  (exact)
   else           → pip install -r <resolved from environment.yaml>             (resolve + lock)
     ↓
   pip check && write new lock if needed → mark ready
   ```
   Workspace files are already restored; packages are now reconstructed to the same effective state. From NALLY view: “nothing happened” except `GET /v1/health` shows new `uptime_sec`.

4. **Failure modes:** If `environment.lock` replay fails (e.g., yanked version, network), NALLPUTER stays `recovering`, exposes `GET /v1/machine` + `GET /v1/health` with `sync_state: env_replay_failed` and `GET /v1/exec/{id}` for the failed replay run. NALLY can then fix `environment.yaml` and retry `POST /v1/computer/{id}/start` (which re-attempts replay). No silent downgrade.

5. **Non-Python stacks:** Same shape — `node.packages`, `system.apt`. v0.1 locks `pip` + `apt` + `npm` only; adding `cargo`/`go` is additive YAML, no breaking change.

6. **What is NOT in the spec:** Secrets, tokens, private index creds, ephemeral caches, absolute paths outside `persistent_paths`. Credentials are injected per-exec via scoped env, never written to canonical store.

### Why not snapshot the whole FS

- FS snapshot is **non-portable** (kernel, arch, base-layer drift) and **bloated** (GBs of `__pycache__`). Declarative spec is KBs, auditable, diffable, and replays correctly even when the Lab Rat base image changes from `python:3.12-slim` to a future hardened image.
- Snapshot is a v0.2+ *capability* (`snapshots: true` in MachineProfile) for cases where a binary toolchain is truly not reconstructible — but it is **not** the v0.1 durability story.

---

## Sync API surface (minimal, v0.1)

No new NALLY-facing persistence verbs are required for durability, but two optional ops make the system observable:

```
POST /v1/computer/{id}/sync   → 202 { sync_rev, dirty_files }  (force flush, for tests/barriers)
GET  /v1/computer/{id}/sync   → 200 { last_sync_rev, last_sync_at, dirty_count, sync_state }
```

Both are optional; debounced sync works without them. They are useful for Phase 7 Evaluation (`recovery` metrics) and for NALLY to assert a durability barrier before a dependent step.

If omitted in v0.1, `GET /v1/health.sync_state` still exposes `synced|pending|degraded`.

---

## Eviction, retention, and cost controls

- External store is **retained** until `POST /v1/computer/{id}/destroy` (which deletes canonical prefix). `stop` does not delete; `destroy` is explicit and requires confirmation idempotency key.
- Per-computer quota: `resources.workspace_gb` (1 GB default) enforced at sync time — `write` that would exceed quota → `507 Insufficient Storage` with `policy_result: workspace_quota_exceeded`, not a silent truncation.
- Log retention: unbounded `logs/` is forbidden; `GET /v1/exec/{id}` retention is 24h / 100 KB per run (Decision 003), not the sync store.
- Auto-stop (Phase 4) interacts: `idle 900s → auto-stop` flushes, then runtime count drops to 0, but external store remains — next `start` restores.

---

## What this does NOT decide (deferred)

- Exact object-store provider or SDK (R2 vs S3 vs MinIO) — pick in Phase 6 MVP, behind abstraction.
- Chunking algorithm (whole-file PUT vs content-defined chunking) — choose in MVP based on measured object-storePUT cost; default whole-file < 5 MB is sufficient for v0.1.
- Snapshot format and lifecycle for v0.2+ — reserve `snapshots/` prefix now, define later.
- Encryption at rest for external store (customer-managed key) — v0.2+.

---

## Evidence trace

- Render docs: ephemeral FS vs Persistent Disk — motivates external canonical abstraction.
- Daytona: filesystem vs memory persistence distinction — motivates three-axis table.
- E2B/Modal: volume vs snapshot vs sandbox identity — motivates `manifest.json` + per-file atomic PUT + `computer_id` stability.
- Anthropic: env scrub / credential isolation — motivates secrets never in `environment.yaml`.
- Manus: persistent computer identity — motivates manifest as canonical pointer.
- OpenAI: bounded output vs durable files — motivates why exec output is short-lived while workspace/spec is canonical.

---

## Review gate outcome

Decision locked 2026-09-07. Next blockers unblocked:
- **Phase 3 (Machine & Execution API Contract):** can now define `GET /v1/machine` with `persistence.workspace=external_canonical` and `GET /v1/computer/{id}/sync`.
- **Phase 4 (Runtime):** implements watcher, debouncer, SIGTERM flush, restore+replay.
- **Scrutiny item resolved:** “restart and nothing happened” is true iff (a) workspace file PUTs are atomic+manifest-committed and (b) package state is captured declaratively in `environment.yaml/lock` and replayed deterministically. Both are specified above.
