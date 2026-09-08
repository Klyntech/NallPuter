# NallPuter Decision 011 — Production Architecture (Lab Rat → Production)

**Status:** LOCKED
**Date:** 2026-09-08
**Review gate:** Phase 8 — production architecture (requires 003–010 locked + 2195f2b Linux baseline committed) — **REVIEW PASSED 2026-09-08**
**Depends on:** `003-machine-contract.md`, `004-persistent-state.md`, `005-workspace-model.md`, `006-runtime-model.md`, `007-security-model.md`, `008-lifecycle-model.md`, `009-nally-integration.md`, `010-evaluation-full.md`, `59d09ba` MVP, `5a44765` Windows minimal (19/19), `2195f2b` Linux baseline (20/20)
**Blocks:** Phase 8 implementation (canonical store wiring, sync_engine real flush/restore, prod lifecycle wiring)

---

## Decision

**NallPuter production is the same provider-neutral contract already frozen in 003–009, now run on production primitives that honor that contract.**

The disposable Lab Rat (`render`, `instance_recreated`, single container, local-FS stub sync) becomes a **production computer that still presents the identical `MachineProfile` + `openapi.yaml` surface to NALLY**. The 14 rows below are the production interpretations of the already-locked models, with the three choices you just locked:

1. **Canonical persistence is an S3-compatible object store; the provider is deployment configuration.**
2. **Concurrency stays hard `5 running → 429`. No queue in 011.**
3. **Idle timeout stays `900s` as the production default, but remains configurable via MachineProfile/config — not a hard-coded universal constant.**

If any row requires changing a locked contract (`003`–`009` or `openapi.yaml`), it **must** be recorded as an explicit `Exception to 00X` with migration (see § Exception template) — not silent scope creep.

---

## 1. Canonical persistence

**Decision:** **An S3-compatible object store is the canonical persistence layer; the provider is deployment configuration.** R2, S3, or any S3-compatible endpoint are *deployments* of the same `external_canonical` abstraction. Render Disk remains the Lab Rat / write-through cache behind that abstraction (`workspace_mechanism: persistent_disk` → `object_store` is a config swap).

**Rationale:** `004` already demoted Render Disk from architecture to Lab Rat. `010` proves the sync contract (`pending→synced`, `If-Match` etag, per-file atomic PUT, `manifest.json` last) works against a real store. Object storage is provider-neutral (`009` → NALLY never branches on `provider`), cost-proportional to retained `workspace_gb`, and swappable without breaking `computer_id` stability.

**Evidence:** `004` canonical store diagram + three-axis table (`workspace` `external_canonical` vs `packages` `reconstructible` vs `machine` `ephemeral`), `005` canonical layout `/computers/cmp_<id>/workspace/...`, `010` Linux `pending 4 dirty → synced 0` + `stop_start.json` `kept:true`, `2195f2b` Linux `sync.json` same shape.

**v0.2:** Chunked sync (`>5MB` content-defined), cross-region replication, KMS encryption — all *behind* `S3-compatible` interface, no new endpoint shape.

## 2. Runtime lifecycle

**Decision:** Production lifecycle is the already-locked `008` machine: `creating→running→idle→stopping→stopped→starting→recovering→destroyed` with `starting` = **fetch `manifest.json` + restore `workspace/` + replay `environment.lock` (exists → `pip --require-hashes`, else resolve `environment.yaml`)**. `stopped` retains canonical prefix; `destroy` deletes prefix with `Idempotency-Key`. Render stays `instance_recreated` (disposable); `starting` hides it.

**Rationale:** `008` + `004` restore+replay already passed Windows+Linux; `010` proves `stop→start` keep. No new state; production just wires `starting` to the object store.

**Evidence:** `008` state diagram + `recovering` `env_replay_failed→503`, `010` `stop_start.json` `kept:true`, `2195f2b` same.

**v0.2:** `paused→resuming` via Firecracker/Kata (005/006 defer) — new states, not a change to `stopped`.

## 3. Workspace durability / sync

**Decision:** Same `005` split: `persistent {projects,files,artifacts,.nallputer/state}` vs `ephemeral {tmp,.cache,__pycache__,node_modules/.cache}`; `workspace_gb 1/2` quota `507`; large-file chunking deferred (whole-file `<5MB` PUT now). Conflict = **`If-Match` reject stale `manifest` flush**, not last-write-wins; no merge.

**Rationale:** `005` + `004` debounced `3s` + pre-stop `10s` + on-start restore already proven `pending→synced`. Chunking is a cost optimization, not a contract fix.

**Evidence:** `005` `ephemeral_paths`/`persistent_paths`, `004` `debounced→flush→restore`, `010` `sync.json` `dirty_count 4→0`, `2195f2b` same with Linux paths.

**v0.2:** Content-defined chunking, delta PUT, snapshot `snapshots/` prefix reserved in `005`.

## 4. Environment reconstruction

**Decision:** `004` deterministic replay stays: `environment.yaml` (intent, `version:1`, `base.image`, `system.apt`, `python.packages`, `node.packages`) + `environment.lock` (hashes) → `pip check` → new `lock`. `credential_in_spec 403` enforced; failure → `recovering` `503 env_replay_failed` + failed replay `run_id` (no silent downgrade).

**Rationale:** Windows `pandas==2.2.3` and Linux `requests==2.32.0` both pass `env_spec.json`; `004` scrutiny item ("restart and nothing happened" iff declarative+lock) is satisfied.

**Evidence:** `004` § Environment, `007` `credential_in_spec`, `009` `reconstructible` vs `persistent`, `010` `env_spec.json` `spec:ok`.

**v0.2:** `uv`/`poetry` managers, `system.apt` version pins, `hooks.post_install` — additive `yaml` keys.

## 5. Security / egress enforcement

**Decision:** `007` `deny-by-default` stays; production enforces via the **same** `127.0.0.1:3128` userspace proxy + `HTTP_PROXY`/`NO_PROXY` injection per-run + `allowlist pypi.org,registry.npmjs.org,github.com` + API preflight `egress_blocked 403` before spawn + audit `{run_id,dst,decision}` without bodies/secrets.

**Rationale:** `010` `egress.json` `evil 403/pypi succeeded` + `jail.json` + `credential.json` all PASS on Linux with `setsid`/`killpg` (not `taskkill`). Proxy is provider-portable, unlike `iptables` `NET_ADMIN` (rejected in `007`).

**Evidence:** `007` + `003` `egress_policy`, `010` `egress.json`, `2195f2b` `pids.max 100` + `jail`.

**v0.2:** `nftables` deny-by-default inside netns for raw TCP, same allowlist language.

## 6. Isolation boundaries

**Decision:** **Container-level remains for v0.1 production** (`tini` PID1, `no-new-privileges`, `cap-drop ALL`, `read-only` rootfs where Render allows, `tmpfs /tmp`). Stronger VM (`Firecracker`/`Kata`) is `v0.2` as a *different* `persistence.instance` value, not a `v0.1` production change.

**Rationale:** `006` `cgroup v2` `memory.max`/`cpu.max`/`pids.max` already verified `v2` on Linux (`010` `v2 (cpuset cpu io…)`). Container is the Lab Rat's isolation that passed 20/20; VM changes cost/latency, not contract.

**Evidence:** `006` + `010` `cgroup v2` `v2` + `pids.max 100`, `2195f2b` same + `pids.current 3`.

**v0.2:** `Firecracker` microVM / `Kata` with own netns, same `openapi.yaml`.

## 7. Resource enforcement

**Decision:** The 8 knobs stay (`500m/512M/2G/100/300s/100KB/1G/deny`) with `006` `v2` `memory.max` hard ceiling (`swap 0`), `cpu.max` hard (`0.5`), `pids.max 100` (`pids.current` observable), derived `concurrency 5` (`min(cpu/100,pids/10)` → `429`), `wall_time 300s→timed_out` + per-run override, `output 100KB→truncated` paged `?cursor&limit`.

**Rationale:** `002` bundles (`Small…XLarge` as knob presets, not product) + `006` + `010` `concurrency 5 →429` proof (`test_concurrency_5` PASS).

**Evidence:** `002` + `006` + `010` `pids.max 100/current 3`, `timeout.json` `timed_out`, `truncation.json` `200001B→truncated`.

**v0.2:** `cpu burst` vs hard, `io.max`, `GPU` — new knobs, not changes.

## 8. Observability / audit

**Decision:** No new endpoint shape: `GET /health` (`computer_id/uptime/sync_state`), `GET /computer/{id}` (`resources_usage` now includes true `pids.current`/`memory` — was stub `0` on Windows), `GET /exec/{id}?cursor&limit` paged, `GET /sync` `dirty_count`, `POST /sync` flush `202`, `append-only` audit `{ts,computer_id,run_id,decision,reason}` without secrets, `exec` `policy_result` on deny.

**Rationale:** `003` + `008` + `009` already expose these; `010` Windows `uptime 5s` vs Linux `uptime 4s` shows `health` works.

**Evidence:** `003` `health`, `008` `sync_state`, `009` `policy_denied` taxonomy, `010` `startup_warm/cold`.

**v0.2:** Host `pids`/`memory`/`cpu` time series, not new endpoint.

## 9. Concurrency and queuing

**Decision:** **Hard `5 running → 429` stays; no queue in 011.** `6th →429 concurrency_limited` is the `008` `429` already proven on Linux (`test_concurrency_5` → `201*5 + 429*1`). This continues `006+009` cleanly.

**Rationale:** Queue changes execution semantics (ordering, head-of-line) and deserves its own future decision. `010` validates `5`.

**Evidence:** `006` derived limit, `010` `concurrency 5` PASS (`junit.xml` `20 tests`), `009` client backoff on `429`.

**v0.2:** Queue (`5 running + 5 queued`) is a *new* `012`, not an amendment.

## 10. Failure / reconnection semantics

**Decision:** Instance replacement preserves `computer_id`, resets `uptime_sec`, exposes `recovering`+`degraded` via `health` (`sync_state: degraded` / `env_replay_failed`); `009` adapter does `GET /machine`+`health`+`computer` backoff `1s→10s`, re-fetches `machine`, reconciles same `computer_id` (not new).

**Rationale:** `008` + `009` + `004` `instance_recreated` already specify this; `010` `stop_start.json` proves `keep`.

**Evidence:** `008` `recovering`, `009` `uptime_sec` reset → reconnect, `010` `health` `ok` with `sync_state`.

**v0.2:** `paused` recovery uses same `health` shape.

## 11. Secrets / credentials

**Decision:** Scoped per-run `env` overlay, `AWS_/*_TOKEN/*_SECRET` scrub, private index creds via `dst_host`-scoped injection (only for allowlisted host), **never persisted** to `environment.yaml`/`workspace/`/canonical. `credential_in_spec 403` stays.

**Rationale:** `007` + `004` non-secret `env.vars` in `environment.yaml` already enforce this; `010` `credential.json` `403/200` PASS.

**Evidence:** `007` + `010` `credential`.

**v0.2:** `mTLS`/`signed JWT` pluggability already in `003`.

## 12. Provider abstraction

**Decision:** `provider` stays **field** in `MachineProfile`, never a branch (`009`: `if provider == "render"` is anti-pattern). Render is an `external_canonical` via `persistent_disk` cache; `object_store` swap is deployment configuration.

**Rationale:** `003` provider-neutral `GET /v1/machine` (`instance`/`workspace`/`packages` triples, not `render` flag) + `004` `workspace_mechanism` are the architecture.

**Evidence:** `003` `provider: render` vs `docker` vs `ci` all `external_canonical`, `009` `machine: docker` `v2` `100` still `external_canonical`.

**v0.2:** `aws`/`gcp`/`hetzner` are new `provider` values, no code branch.

## 13. Cost / scaling model

**Decision:** `stop` retains `1G` canonical (`2G` disk) with no compute; `destroy` deletes prefix (`Idempotency-Key`); `auto-stop 900s` `idle→stopping→stopped` flushes; `Small/Med/Large/XLarge` bundles from `002` scale knobs (not product). Cost = retained `workspace_gb` + active `cpu/memory` time, not new computer type.

**Rationale:** `002` `Bigger NallPuter = bump knobs`, `008` `idle_since` `900s` + `stopping` flush `10s`, `010` `warm 17ms` vs cold container boot (not import) is the cost knob.

**Evidence:** `002` + `008` + `010` `startup_*`.

**v0.2:** Per-second billing vs retained storage split (Manus `10$/mo` vs E2B per-sec) stays pricing, not architecture.

## 14. Migration path

**Decision:** v0.1 state (`/home/nally/workspace`, `.nallputer/state/environment.yaml`, local `sync` pending) moves into canonical `workspace/` prefix via **one-time `manifest.json` import** (copy local `projects/files/artifacts/.nallputer` into `workspace/` under new `computer_id`, write `manifest` rev `1`). `computer_id` stays stable thereafter; `NALLY` contract (`003` `openapi.yaml`) does not change.

**Rationale:** `004` `manifest` is the canonical pointer; `005` persistent split already defines what migrates; `010` `linux/REPORT.md` is the evidence that `copy` is sufficient (no `pids`/`memory` state moves).

**Evidence:** `004` `manifest.json` + `workspace/` mirror, `005` `persistent` set, `010` `stop_start`.

**v0.2:** No migration change — `paused` state is new scope, not a migration of `v0.1` state.

---

## What 011 does NOT decide (deferred)

- Exact object-store provider (R2 vs S3 vs Ceph) — deployment config, not architecture.
- Exact S3 bucket naming / IAM / KMS — `render.yaml` + `NALLPUTER_CANONICAL` env in Phase 8 wiring.
- Chunking algorithm (`>5MB` content-defined), cross-region, snapshot `501→200` — `012+`.
- Docker-in-Docker on Render, multi-user, GPU (`v0.3+`), human approval gates — out of `v0.1` prod.

---

## Exception template — for any attempted 003–009 change

> **Exception to 00X:** `Title`
> **Affected contract:** `003` / `004` / `005` / `006` / `007` / `008` / `009` / `openapi.yaml`
> **Production requirement:** one paragraph why `011` cannot be satisfied without the change
> **Evidence:** cite `010` `2195f2b` number that forces the change (e.g., `pids.current 3` vs expected `5`)
> **Migration:** how existing `computer_id`/`workspace`/`runs` move without breaking `NALLY` client (`009` `reconnect`)
> **Review gate:** must be approved before code — not after

If no exception is filed, `003–009` are **closed**.

---

## Evidence trace

- `003-machine-contract.md` — provider-neutral `MachineProfile` (`instance`/`workspace`/`packages`) → rows 1,12
- `004-persistent-state.md` — canonical `external_canonical`, `debounced+flush+restore`, `environment.yaml/lock` → rows 1-4,14
- `005-workspace-model.md` — `persistent` vs `ephemeral` + `507` → rows 3,14
- `006-runtime-model.md` — `v2` `memory/cpu/pids` + `concurrency 5` + `wall-time` + `tini` → rows 6,7,9
- `007-security-model.md` — `deny-by-default` + `HTTP_PROXY` + `credential_in_spec` → rows 5,11
- `008-lifecycle-model.md` — `creating→…→destroyed`, `auto-stop 900s`, `recovering` → rows 2,8,10,13
- `009-nally-integration.md` — `GET /machine` first + `uptime_sec` reconnect → rows 10,12
- `010-evaluation-full.md` — lockdown vs measure-only, evidence table → this file's gate
- `5a44765` Windows `REPORT.md` — `19/19`, `304ms/87ms` baseline
- `2195f2b` Linux `REPORT.md` — `20/20`, `213ms/0.92ms`, `v2` `100/3`, `concurrency 5→429`, `setsid`/`killpg`
- `59d09ba` MVP — `33` contract checks on which `010` builds

---

## Review gate outcome

**REVIEW — 2026-09-08 — PASSED. No contradictions with 003–010.**

- **Contradictions with 003–010:** none. All 14 rows are interpretations of locked models behind the same `MachineProfile` + `openapi.yaml` surface. No `003` provider branch, no `004` contract change (S3-compatible is the `external_canonical` abstraction already in `004`), no `005` split change, no `006` v2/concurrency change, no `007` egress change, no `008` state change, no `009` adapter change.
- **Accidental endpoint changes:** none. Row 8 explicitly *fills* `pids.current`/`memory` stubs with real values behind existing `GET /computer/{id}` shape — not a new endpoint. No new path/method.
- **Assumptions vs Linux evidence:** all cited numbers are in `2195f2b` (`213ms/0.92ms`, `3.8ms` warm, `v2`, `100/3`, `concurrency 5→429`, `setsid/killpg`, `pending→synced`). Overhead `213×` correctly labeled container-internal, not host.
- **S3 failure semantics:** covered — `If-Match` reject stale flush (row 1) + `health` `degraded`/`recovering` on unreachable store per `008` (rows 2,8,10). No silent last-write-wins.
- **Sync/conflict:** `If-Match` reject, no merge (row 3) — matches `004`.
- **Env replay failure:** `recovering` `503 env_replay_failed` + failed `run_id`, no downgrade (row 4) — matches `004`/`008`.
- **Secret leakage:** scoped per-run, never persisted, `credential_in_spec 403` (rows 4,11) — matches `007`, no new path.
- **Lifecycle/recovery:** `instance_recreated` hidden by `starting` restore+replay, `uptime_sec` reset → `009` backoff (rows 2,10) — matches `008`/`009` and `010` `stop_start`.

**No `Exception to 00X` required. Status flips DRAFT → LOCKED. Implementation may now wire the production primitives; still no new endpoint shape until a new decision says so.**

## Addendum

- `001`/`002` addenda (`003/004` reinterpretation) remain accurate; `011` now adds the `010` interpretation: Windows `13ms*` cold is not production cold, Linux `3.8ms` warm is not Render cold — both are `measure-only`.
