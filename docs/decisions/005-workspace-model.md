# NallPuter Decision 005 — Workspace Model

**Status:** LOCKED
**Date:** 2026-09-07
**Review gate:** Phase 4 — concrete models (requires 003 + 004 locked)
**Depends on:** `003-machine-contract.md` (MachineProfile paths/capabilities), `004-persistent-state.md` (canonical external store + sync engine + environment spec)
**Blocks:** Phase 6 MVP (NALLPUTER runtime implementation)

---

## Decision

**Single workspace per computer, with an explicit durable/ephemeral split and a canonical external layout that the runtime mirrors as a cache.**

NALLY never sees a host path. Every file op is jailed to the workspace root and subject to the same policy as `exec` (Anthropic gap fix). Quota is enforced at write + sync time, artifacts are durable, and temporary data has a defined eviction contract.

---

## Canonical layout (external store) vs Runtime view

### External canonical (per `computer_id`, Decision 004)

```
/computers/cmp_<id>/
  manifest.json                 # computer_id, revision, created_at, last_sync_rev, checksums
  workspace/
    projects/                   # user repos / cloned work — durable
    files/                      # inputs/outputs — durable
    artifacts/                  # build outputs, reports, bundles — durable
    .nallputer/
      state/
        environment.yaml        # declarative env intent (004)
        environment.lock        # pinned hashes
        sync-state.json         # last_sync_rev, dirty set
        machine.json            # snapshot of MachineProfile at create
  logs/                         # optional bounded run logs (not exec output store)
  snapshots/                    # v0.2+ only, reserved prefix
```

### Runtime inside disposable machine

```
HOME=/home/nally
WORKSPACE=/home/nally/workspace        # symlink → /workspace (compat)
  /home/nally/workspace/
    projects/          → persistent, synced ✅  (MachineProfile.persistent_paths)
    files/             → persistent, synced ✅
    artifacts/         → persistent, synced ✅
    .nallputer/state/  → persistent, synced ✅
    tmp/               → ephemeral, NOT synced ❌
    .cache/            → ephemeral, NOT synced ❌

  /tmp, /var/tmp                    → ephemeral ❌
  **/__pycache__, **/.pytest_cache, **/node_modules/.cache → excluded ❌
```

`GET /v1/machine` advertises `persistent_paths` / `ephemeral_paths` so NALLY places data correctly without provider sniffing. Anything under a persistent path is durable via the debounced+flush+restore engine (004). Anything under an ephemeral path is never uploaded — loss on `instance` recreate is expected and correct.

---

## Ownership, identity, and isolation

| Rule | Normative |
|------|-----------|
| **Per-computer ownership** | One workspace owns one `computer_id`. No cross-computer path access. `computer_id` in every `POST /v1/files/*` is mandatory and checked against the authenticated caller. |
| **No host escape** | All paths are resolved against the workspace root with `O_NOFOLLOW` + `realpath` + prefix check. `..`, absolute paths outside root, and symlink-follow-then-escape are rejected with `403 policy_denied` before any FS mutation. File ops and `exec` `cwd` share the same resolver (same policy object). |
| **Stable identity** | Workspace identity == `computer_id`. It survives `stop → start → restore` (004). `destroy` deletes the canonical prefix; the `computer_id` is retired and never reused. |
| **Single writer** | Exactly one active runtime per `computer_id`. External store `manifest.json` is written with `If-Match: etag` — stale flushes are rejected (004 multi-writer rule). |
| **CWD** | Initial `cwd` for execs is `/home/nally/workspace/projects`. `exec.cwd` if supplied must pass the same jail check; rejected `cwd` → `400` before spawn. The runtime tracks current cwd per exec (not a global shell session). |

---

## Quota and headroom (binds to 002 + 003 + 004)

| Knob | Source | v0.1 default | Enforcement points |
|------|--------|--------------|--------------------|
| `disk_gb` | `MachineProfile.resources.disk_gb` | 2 GB | Container disk (Render disk size) |
| `workspace_gb` | `MachineProfile.resources.workspace_gb` | 1 GB | `POST /v1/files/write` **and** sync-time check — exceeding → `507 Insufficient Storage` with `code: workspace_quota_exceeded` |
| Headroom | `disk_gb - workspace_gb` | 1 GB | Logs, tmp, package cache; not counted against workspace quota but still bounded by disk |
| Output cap | `max_output_bytes` | 100 KB | Per-run truncation in `GET /v1/exec/{id}` (003) — not workspace quota |

**Observability:** `GET /v1/computer/{id}` returns `resources_usage.{workspace_used_gb, disk_used_gb}`. `GET /v1/computer/{id}/sync` returns `dirty_count`. NALLY can call `POST /v1/computer/{id}/sync` as a durability barrier before a dependent step.

**Policy:** Exceeding workspace quota never truncates silently — write is refused atomically (no partial file visible to next restore). `manifest.json` is not updated for refused writes.

---

## File operation semantics (normative, matches OpenAPI)

| Operation | Contract | Notes |
|-----------|----------|-------|
| `POST /v1/files/write` | Atomic PUT per file + dirty-mark + debounced sync | `encoding: utf8|base64`, optional `mode`. Atomic at canonical layer: upload to `*.tmp` then rename. `bytes_written` + `sync_state` returned. Writing to `environment.yaml` triggers env reconcile (004). |
| `POST /v1/files/read` | Bounded (`limit` ≤ 100 KB), paginated (`offset`, `next_cursor`), `encoding` | `413` if caller requests an unbounded read on a large file — caller must page. |
| `POST /v1/files/list` | Bounded (`limit` ≤ 1000, `recursive: false` default) | No implicit recursive dump. Prevents “list `/` and blow context” failure mode (OpenHands ACI). |
| `POST /v1/exec` with `cwd` | Same jail as files | Generates run; exec may mutate persistent paths → debounced sync as above. |

All three share one policy object (Security model) — there is no “shell-can-write X but file API cannot” divergence.

---

## Artifact and lifecycle rules

| Concern | Rule |
|---------|------|
| **Artifacts** | `artifacts/` is durable and versioned via canonical revisions (manifest). NALLY should treat it as the publishable output area; it is synced and restored identically to `projects/`. |
| **Logs** | Run logs (`stdout/stderr`) are **not** workspace files — they live in the exec store with 24h TTL (003). `logs/` in canonical store is optional and bounded; it is not a replacement for exec output. |
| **Temp cleanup** | `tmp/` and `/tmp` are reaped on `start` (fresh disposable instance) and on `stop` flush they are explicitly excluded. Additionally, a background sweep deletes files in `tmp/` older than **24h** within a running instance (best-effort, never blocks sync). |
| **Cache** | `**/__pycache__`, `**/.pytest_cache`, `**/.cache`, `**/node_modules/.cache` are always excluded from sync (even if under a persistent parent) — deny-list lives in sync engine, not in NALLY logic. |
| **Restore** | On `start` / new instance boot: `fetch manifest.json → restore workspace/ persistent subset → replay environment.yaml/lock → ready`. Etag-checked, consistent-point-in-time view. If store unreachable: `recovering` + `GET /v1/health → 503 sync_state: degraded`. |

---

## What this does NOT decide (deferred)

- Chunking strategy for large files (whole-file < 5 MB vs content-defined chunking) — MVP measures PUT cost (004).
- Snapshot format/lifecycle for v0.2+ `snapshots/` prefix — reserved now.
- Per-file encryption — v0.2+.

---

## Evidence trace

- requirements.md Pillar 3 (Workspace): `projects/files/artifacts/tmp/logs` layout, quota, cleanup.
- OpenHands/SWE-agent ACI: targeted reads, bounded listings, explicit empty-output — prevents context blow-up.
- E2B/Daytona/Modal: volume vs snapshot vs RAM — motivates persistent subset not whole-FS.
- Anthropic gap: file ops must equal shell policy — motivates shared resolver.

---

## Review gate outcome

Locked 2026-09-07. Implements the workspace half of Phase 4; sync engine details in 004, security boundary in 007, lifecycle in 008.
