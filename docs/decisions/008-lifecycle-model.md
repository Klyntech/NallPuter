# NallPuter Decision 008 — Lifecycle Model (Computer + Run, Auto-Stop, Recovery, Health)

**Status:** LOCKED
**Date:** 2026-09-07
**Review gate:** Phase 4 — concrete models
**Depends on:** `003-machine-contract.md` (MachineProfile + health sync_state), `004-persistent-state.md` (restore+replay, sync engine), `005-workspace-model.md` (tmp cleanup), `006-runtime-model.md` (process groups + cgroup), `007-security-model.md` (policy-before-spawn)
**Blocks:** Phase 5 NALLY integration (client retry/reconnect semantics), Phase 6 MVP, Phase 7 Evaluation

---

## Decision

**Lifecycle is two independent state machines: one for the computer, one for each run. Only the computer’s lifecycle is durable — run state is bounded and evictable.**

The computer survives process death, stop, and instance recreation (004 external canonical). Runs do not — after 24h they may be evicted (`410 Gone`). `health` and `machine` are the NALLY-visible truth for both.

---

## 1. Computer lifecycle (durable, canonical)

```
                        ┌────── error (panic/OOM/unrecoverable) ──────┐
                        │                                              │
creating ──→ running ──→ idle ──→ stopping ──→ stopped ──→ starting ──┘
              │  ↑         │  │        │                  │
              │  │         │  └  ──→   │   auto-stop 900s │
              │  │         │           │   (idle→stopping)│
              │  └───  recover  ←──────┘                  │
              │        (retry)                            │
              └──→ recovering ──→ (running | stopped | destroyed)
                        │
                        └─ env_replay_failed, store_degraded → recovering stays, health 503
destroyed ←─────────────────────────────────────────────────────────────── destroying
  (terminal, computer_id retired; canonical prefix deleted via destroy 202 + Idempotency-Key)
```

**States:**

| State | Meaning | `GET /v1/computer/{id}.state` | Durable? | Compute consumed? |
|-------|---------|-------------------------------|----------|-------------------|
| `creating` | Allocated, fetching manifest, restoring workspace (004 restore) | transient | manifest not yet committed | yes (boot) |
| `running` | Executing runs, handling `exec/files/computer` | steady | yes | yes |
| `idle` | No active runs, still warm, ready to accept work | steady | yes | yes (low) |
| `stopping` | SIGTERM flush up to 10s (004 pre-stop), draining | transient | flush in progress | yes |
| `stopped` | Compute released, canonical store retained, no process | steady | yes (canonical only) | **no** |
| `starting` | `start` requested → re-fetch manifest → restore workspace + replay env → `running` | transient | restore in progress | yes |
| `recovering` | Error recovery in progress (OOM, store degraded, env replay failed) | transient | retry loop | yes |
| `error` | Short-lived internal error state before `recovering` | transient | no | yes |
| `destroyed` | Terminal — prefix deleted from external store, `computer_id` retired | terminal | **no** (deleted) | no |
| `destroying` | In-flight `destroy` (async) | transient | deleting | no |

**Transitions (normative):**

| From → To | Trigger | Precondition | Effect |
|-----------|---------|--------------|--------|
| `creating → running` | restore+env replay succeeds | manifest fetch + env lock replay ok | `GET /v1/health → 200 ok, sync_state: synced` |
| `running → idle` | `active_runs == 0` | none | start `idle_since` timer (RFC3339) |
| `idle → running` | `POST /v1/exec` or `POST /v1/files/write` | `health: ok` | reset idle timer |
| `idle → stopping` | `idle 900s` auto-stop **or** `POST /computer/{id}/stop` | — | `GET /v1/computer/{id}.state == stopping` |
| `running → stopping` | `POST /computer/{id}/stop` | — | drain active runs (best-effort kill with grace), then `stopped` |
| `stopping → stopped` | flush succeeds (≤10s) | dirty flush committed + `manifest.json` written | `GET /v1/health` may be briefly `503 recovering` during Render redeploy, then `stopped` — `GET /v1/computer/{id}` is source of truth while instance is gone |
| `stopped → starting` | `POST /computer/{id}/start` or implicit on first `exec`/`files` against stopped computer | canonical store reachable | re-create Runtime (new disposable instance), restore + replay |
| `* → recovering` | `oom_killed`, `pids_exhausted`, `store_degraded`, `env_replay_failed` | — | `GET /v1/health → 503 sync_state: degraded|env_replay_failed`, `GET /v1/computer/{id} → recovering` |
| `recovering → running` | retry succeeds (backoff, bounded) | transient error resolved | ready |
| `recovering → stopped` | recovery gives up but data intact | after N retries, external store still intact | can retry `start` later |
| `recovering → destroyed` | unrecoverable canonical corruption | manifest checksum failure that cannot be repaired | `computer_id` retired, prefix quarantined for operator review |
| `* → destroying → destroyed` | `POST /computer/{id}/destroy` + `Idempotency-Key` | caller holds key; active runs killed | delete canonical prefix `/computers/cmp_<id>/` with `If-Match`; key reuse returns same result (idempotent) |

**Auto-stop (locked):**
- `NALLPUTER_IDLE_TIMEOUT_SEC=900` (15 min) from `002` derived limits.
- Timer starts on `idle` entry; reset on any `POST /v1/exec` or `POST /v1/files/write`.
- On fire: log audit `auto_stop`, transition `idle→stopping→stopped`, flush (004). No data loss — canonical store remains. Next `exec` implicitly `starting` again (or caller may call `POST /start` explicitly).
- Backoff: if NALLY immediately re-creates work, NALLPUTER honors `start` right away — thrash is cost, not correctness. Evaluation (Phase 7) will measure auto-stop churn.

**Render restart mapping:**
- Render sends `SIGTERM` → `stopping` → flush (≤10s) → instance gone → `stopped` in canonical world.
- New instance booted by Render → `starting` → restore+replay → `running`. NALLY observes same `computer_id`, new `uptime_sec` in `GET /v1/health`, brief `recovering/503` window.

---

## 2. Run lifecycle (ephemeral, bounded, per `run_id`)

```
queued ──→ running ──→ succeeded
   │          │           failed          (exit_code ≠ 0)
   │          ├────────── timed_out      (wall-time exceeded → SIGTERM→SIGKILL pgid)
   │          ├────────── cancelled      (DELETE /exec/{id} → SIGTERM→SIGKILL pgid)
   │          └────────── policy_denied  (never spawned; policy_before_spawn in 007)
   └────────── policy_denied (admission: concurrency|quota|egress|FS denied)
```

| State | Terminal? | Spawned? | `exit_code` | `truncated` | Evictable? |
|-------|-----------|----------|-------------|-------------|------------|
| `queued` | no | maybe (admission) | null | false | no |
| `running` | no | yes | null | false | no |
| `succeeded` | yes | yes | 0 | maybe | yes (TTL 24h) |
| `failed` | yes | yes | ≠0 | maybe | yes |
| `timed_out` | yes | yes | null (killed) | maybe | yes |
| `cancelled` | yes | yes | null | maybe | yes |
| `policy_denied` | yes | **no** | null | false | yes (policy_result carries reason) |

**Guarantees:**

- `run_id` is stable and required for all observations (`GET /exec/{id}` is the only read path; polling transport in v0.1).
- Bounded output: `max_output_bytes` (100 KB) pagination via `?cursor=&limit=`; `truncated: true` when cap hit. TTL **24h**, then `410 Gone` (003).
- `sync_pending: true` in `POST /v1/exec` / `GET /v1/exec/{id}` when the run dirtied `persistent_paths` and debounce hasn’t flushed yet.
- Cancel/timeout kills the **process group** (`-pgid`, 006 § 3: SIGTERM 5s → SIGKILL), not just the parent. Orphans are reaped by `tini`.
- `policy_denied` never spawns — NALLPUTER rejects before `fork` and emits an audit event (007).

---

## 3. Health and sync observability (binds 003 + 004)

| Endpoint | Steady `running` | `recovering` (store degraded) | `recovering` (env replay failed) | `stopped` |
|----------|------------------|-------------------------------|----------------------------------|-----------|
| `GET /v1/health` | `200 ok, sync_state: synced, uptime_sec: N, computer_id: cmp_*` | `503 degraded|recovering, sync_state: degraded, last_error: store_unreachable` | `503 sync_state: env_replay_failed` | May be `503` briefly while no instance; `GET /v1/computer/{id}.state: stopped` is canonical |
| `GET /v1/computer/{id}` | `state: running|idle, resources_usage, sync_state` | `state: recovering` | `state: recovering, sync_state: env_replay_failed, last_error: <replay run_id>` | `state: stopped` |
| `GET /v1/computer/{id}/sync` | `{sync_state: synced|pending, last_sync_rev, dirty_count}` | `dirty_count` may grow until retry | — | last known `sync_state` at time of `stopping` flush |

NALLY’s reconnect path after a suspected restart: `GET /v1/health` → if `computer_id` same but `uptime_sec` reset → expect brief `recovering` → wait with backoff → `GET /v1/machine` to confirm `restart_behavior` → resume with same workspace.

---

## 4. Error and retry taxonomy

| Class | Example `policy_result` / `error.code` | Retryable by NALLY? | Who fixes |
|-------|----------------------------------------|---------------------|-----------|
| `policy_denied` (pre-spawn) | `filesystem_denied`, `egress_blocked`, `workspace_quota_exceeded → 507`, `concurrency_limited → 429`, `credential_in_spec` | Fix allowlist/path/quota/concurrency then retry | NALLY or operator config |
| `timed_out` / `cancelled` | `wall_time_exceeded`, `cancelled_by_delete` | Retry after raising `timeout_sec` or fixing hang | NALLY |
| `failed` (exec error) | non-zero exit | Depends on command | NALLY |
| `oom_killed` / `pids_exhausted` | `oom_killed`, `pids_exhausted` (hard cgroup) | Retry after bumping `MachineProfile.resources` or lowering concurrency | NALLY or operator |
| `store_degraded` | `store_unreachable` (503) | Backoff retry, no mutation | NALLPUTER (or provider) — NALLY waits |
| `env_replay_failed` | `yanked_package`, `index_unreachable` | Fix `environment.yaml` then `POST /start` | NALLY |

No silent downgrade: a failed env replay keeps the computer `recovering` — it does not boot with a reduced env and claim `running`.

---

## 5. What this does NOT decide (deferred)

- `paused`/`resumed` VM states — reserved, `501` in v0.1 (003).
- Snapshot/restore semantics beyond reserved `snapshots/` prefix — v0.2+.
- Exact retry backoff constants for `recovering` → `running` — MVP picks `1s,2s,5s,10s` capped, observable in logs.

---

## Evidence trace

- E2B/Daytona/Modal: distinct stop vs pause vs snapshot, compute vs storage retention — motivates `stopped`≠`destroyed` and `idle→auto-stop`.
- Manus: persistent identity distinct from task — motivates `computer_id` survives runs.
- Anthropic: orphan reaping, inherited limits — motivates `tini` + pgid kill + cgroup inheritance (006).
- OpenAI: bounded transport — motivates output TTL + pagination.

---

## Review gate outcome

Locked 2026-09-07. Completes Phase 4’s four concrete models (005 workspace, 006 runtime, 007 security, 008 lifecycle). Next: Phase 5 NALLY integration, then Phase 6 MVP, then Phase 7 Evaluation.
