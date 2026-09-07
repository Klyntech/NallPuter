# NallPuter Decision 003 — Machine Contract (Provider-Neutral Machine Profile)

**Status:** LOCKED
**Date:** 2026-09-07
**Review gate:** Phase 2a — inserts before persistence/recovery and API contract
**Supersedes / amends:** Clarifies `001-computer-model.md` and `002-resource-model.md` without breaking them — Render is demoted from architecture to *Lab Rat #1* implementation.

---

## Decision

**NallPuter exposes a provider-neutral Machine Contract before NALLY may treat it as a computer.**

Before any `exec`/`files` call, NALLY must be able to call:

```
GET /v1/machine  → MachineProfile
GET /v1/health   → liveness + computer_id binding
```

The profile answers *“what kind of computer am I connected to?”* not *“what provider am I on?”*. Provider identity (`render`, `aws`, `gcp`, `hetzner`, `local`, …) is a field inside the profile, never the contract itself.

This is **Phase 2a**. It blocks Phase 2b (Persistent State) and Phase 3 (Machine & Execution API Contract).

---

## Rationale

1. **NALLY must adapt reasoning to the machine, not the provider.** An ephemeral 512 MB container with no package persistence requires a fundamentally different strategy than a persistent 16 GB VM with snapshot. If NALLY has to infer this from `provider == "render"`, the contract leaks and every new provider needs a new prompt.

2. **Persistence, packages, and lifecycle are not one knob.** Research convergence was wrong to conflate them. Evidence:
   - Daytona: *filesystem persistence* ≠ *memory/process persistence* (explicit docs).
   - E2B: *sandbox identity* + *pause/resume* is separate from *volume/storage*.
   - Manus: *persistent computer identity* is separate from *resource tier*.
   A single `provider: render` label hides those three independent axes.

3. **Render is Lab Rat #1, not architecture.** Render’s own docs state the default filesystem is ephemeral across restarts/redeploys; only paid services with an attached Persistent Disk preserve files under the mount path. A NallPuter that *is* a Render Disk cannot port to S3, R2, or a local Docker host. The canonical store (Decision 004) must be abstract.

4. **Security & resource enforcement piggybacks on the profile.** PIDs, wall-time, output cap, network policy, and `package_persistence` all change the policy engine path before a process is spawned (`NALLY decision → NallPuter policy → OS enforcement`).

---

## MachineProfile — canonical schema (v0.1)

This is the exact shape returned by `GET /v1/machine`. All fields are required unless marked `optional`. Unknown `provider` values must be accepted — NALLY reasons over capabilities, not provider names.

```json
{
  "computer_id": "cmp_01j9f2...",
  "provider": "render",
  "runtime": "nallputer-0.1.0",
  "revision": "58dc6db",
  "created_at": "2026-09-07T00:00:00Z",
  "persistence": {
    "instance": "ephemeral",
    "workspace": "persistent",
    "workspace_mechanism": "external_canonical",
    "packages": "reconstructible",
    "snapshots": false
  },
  "resources": {
    "cpu_millicores": 500,
    "memory_mb": 512,
    "disk_gb": 2,
    "pids": 100,
    "wall_time_sec": 300,
    "max_output_bytes": 100000,
    "workspace_gb": 1
  },
  "capabilities": {
    "shell": true,
    "files": true,
    "package_install": true,
    "network": true,
    "egress_policy": "deny-by-default",
    "streaming": false,
    "pause_resume": false,
    "snapshot_restore": false
  },
  "restart_behavior": "instance_recreated",
  "ephemeral_paths": ["/tmp", "/workspace/.cache", "/workspace/tmp"],
  "persistent_paths": ["/home/nally/workspace", "/home/nally/workspace/projects", "/home/nally/workspace/.nallputer/state"]
}
```

### Field semantics

| Field | Values | Meaning |
|-------|--------|---------|
| `persistence.instance` | `ephemeral` \| `persistent` | Does the *runtime process* survive restart? v0.1: `ephemeral`. v0.2+ VM: `persistent`. |
| `persistence.workspace` | `ephemeral` \| `persistent` \| `external_canonical` | Is the *user-visible* workspace durable? v0.1: `external_canonical` — runtime is disposable, canonical store is truth (Decision 004). |
| `persistence.workspace_mechanism` | `external_canonical` \| `persistent_disk` \| `object_store` \| `volume` | How workspace durability is achieved. NALLY should not branch on this, but it is auditable. Render Disk is `persistent_disk` behind `external_canonical` abstraction. |
| `persistence.packages` | `ephemeral` \| `persistent` \| `reconstructible` | v0.1: `reconstructible` — `pip install` mutates current FS but may vanish on recreate; canonical *environment spec* in persistent store must be able to recreate it. See Decision 004 § Environment. |
| `persistence.snapshots` | `bool` | Point-in-time images distinct from workspace persistence (E2B/Daytona/Modal signal). v0.1: `false`. |
| `restart_behavior` | `instance_recreated` \| `state_preserved` | What happens on provider restart. Lab Rat Render: `instance_recreated` + restore via sync engine. |
| `capabilities.streaming` / `pause_resume` / `snapshot_restore` | `bool` | Advertised; `GET /v1/exec/{id}/stream` and `POST /v1/computer/{id}/pause` return `501 Not Implemented` when `false`. Prevents NALLY from guessing. |
| `ephemeral_paths` / `persistent_paths` | `string[]` | Explicit so NALLY knows where to put caches vs. durable work. |

### Example profiles

**Machine A — Lab Rat (current v0.1, ephemeral runtime, canonical workspace):**
```json
{
  "computer_id": "cmp_lab_001",
  "provider": "render",
  "persistence": { "instance": "ephemeral", "workspace": "external_canonical", "packages": "reconstructible" },
  "resources": { "cpu_millicores": 500, "memory_mb": 512, "disk_gb": 2 },
  "capabilities": { "streaming": false, "pause_resume": false },
  "restart_behavior": "instance_recreated"
}
```

**Machine B — Future persistent VM:**
```json
{
  "computer_id": "cmp_prod_042",
  "provider": "aws",
  "persistence": { "instance": "persistent", "workspace": "persistent", "packages": "persistent", "snapshots": true },
  "resources": { "cpu_millicores": 8000, "memory_mb": 32768, "disk_gb": 200 },
  "capabilities": { "streaming": true, "pause_resume": true, "snapshot_restore": true },
  "restart_behavior": "state_preserved"
}
```

NALLY’s logic is identical: read profile → choose strategy. No `if provider == "render"` branch.

---

## API implications (feeds Phase 3)

```
GET /v1/machine
  → 200 { MachineProfile }  (no auth? No — requires same Bearer as exec; unauth → 401)
  → Must be callable before any exec; should be cheap, cached, no side effects.

GET /v1/health
  → 200 { status: "ok", computer_id, uptime_sec, sync_state }
  → Liveness for Render private networking; also binds health to the same computer_id so NALLY can detect
     instance recreation (new startup time, same computer_id).

GET /v1/exec/{run_id}/stream  (v0.1)
  → 501 Not Implemented, body: { code: "streaming_not_supported", machine_capability: "streaming=false" }
  → Keeps contract forward-compatible without pretending.

POST /v1/computer/{id}/pause , /resume , /snapshot (v0.1)
  → 501 with machine_capability hint
```

Polling remains v0.1 transport (`POST /v1/exec → run_id`, `GET /v1/exec/{run_id}`).

---

## Auth & transport decisions (locked here)

| Decision | Choice | Why | Future path |
|----------|--------|-----|-------------|
| **Auth** | **Bearer token** for v0.1, constant-time compare, single NALLY→NallPuter trust relationship | Simplest, matches README deployment target, one private network hop | Auth interface must be pluggable — header `Authorization: Bearer <token>` isolated in middleware so mTLS / signed JWT can be added without changing endpoint shapes |
| **Egress policy** | **Lock policy contract only, not implementation** (`deny-by-default`, allowlist semantics, auditable decisions) | Implementation depends on isolation model (iptables vs sidecar vs userspace proxy chosen in Phase 4) | Policy language stable; enforcement swapped under it |
| **Output retention** | **Persist execution metadata + bounded output** with explicit TTL, not unbounded log store | Prevents `/exec/{id}` becoming accidental log store; E2B per-sec cost signal | Propose TTL 24h + max 100 KB per run (002 knob), pagination via `?cursor=&limit=`; server may evict with `410 Gone` |
| **Streaming** | **Include endpoint, mark unsupported/501** | Forward-compatible contract — NALLY can probe `capabilities.streaming` | v0.2+: SSE/WebSocket when pause/resume or long runs justify it |
| **Provider neutrality** | **No Render-Disk assumption in API** | Storage mechanism is Decision 004 abstraction | Lab Rat uses Render Disk *behind* `external_canonical`; swap to S3/R2 without breaking NALLY |

---

## What NALLY does with the profile (normative)

1. On connect, `GET /v1/machine`. Cache `computer_id` + `persistence.*` + `capabilities`.
2. If `persistence.packages == "reconstructible"` → any `pip install` / `apt` must also write to the persisted environment spec (Decision 004) so a recreate can `reconstruct`. If `persistent`, a direct install is durable.
3. If `capabilities.streaming == false` → poll `GET /v1/exec/{id}`; do not retry stream with backoff.
4. If `restart_behavior == "instance_recreated"` → expect possible cold restore delay after `health` reports new `uptime_sec`; do not treat `computer_id` disappearance as new computer.

---

## What this does NOT decide (deferred to 004 / Phase 3 / Phase 4)

- Exact persistence backend (S3 vs R2 vs volume plugin) — 004.
- Sync engine internals (inotify vs periodic vs flush hook) — 004.
- Snapshot scope and lifecycle — 004.
- Exact cgroup v1 vs v2 flags, or sidecar vs iptables — Phase 4.
- CPU burst vs hard limit — Phase 4.

---

## Evidence trace

- Anthropic: dual FS+net boundary, child inheritance — informs `capabilities.egress_policy` + `persistence` split.
- Manus: persistent computer identity, tiered resources — informs `computer_id` stability, `resources.*` knobs.
- OpenAI: bounded output, orchestration/execution split — informs `max_output_bytes`, `streaming=false` in v0.1.
- OpenHands/SWE-agent: client-server runtime, ACI — informs profile-first design, explicit empty-output.
- E2B/Daytona/Modal: FS vs RAM vs snapshot, pause/resume, per-knob resources — informs `instance` vs `workspace` vs `packages` vs `snapshots`.
- requirements.md Pillars 1–3 — informs isolation/lifecycle/workspace axes mapped to profile fields.

---

## Review gate outcome

Decision locked 2026-09-07. Proceed to Decision 004 (Persistent Computer State) — the only blocker that can interpret `persistence.workspace=external_canonical` correctly.

## Addendum to prior decisions

- `001-computer-model.md`: “Render private service + persistent disk” is now understood as **one implementation of the Machine Contract with `persistence.instance=ephemeral`, `workspace=external_canonical`, `restart_behavior=instance_recreated`** — not the definition of a NallPuter.
- `002-resource-model.md`: The 8 knobs and Docker flag table remain accurate for Lab Rat, but are now **resource fields of `MachineProfile`**, not the profile itself.
