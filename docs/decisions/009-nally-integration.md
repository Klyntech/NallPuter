# NallPuter Decision 009 — NALLY Integration (Computer Adapter)

**Status:** LOCKED
**Date:** 2026-09-07
**Review gate:** Phase 5 — NALLY-side integration (requires Phases 0–4 locked)
**Depends on:** `003-machine-contract.md` (MachineProfile + health), `004-persistent-state.md` (canonical + env reconstruct), `005-workspace-model.md` (jail/paths), `006-runtime-model.md` (cgroup/process groups), `007-security-model.md` (egress/credential gates), `008-lifecycle-model.md` (computer+run state machines), `docs/api/openapi.yaml` (v0.1 contract)
**Blocks:** Phase 6 MVP (validates client against real runtime), Phase 7 Evaluation (harness reuses same client)

---

## Decision

**NALLY integrates via a `Computer Adapter`, not a thin `POST /exec` client.**

The adapter owns four responsibilities that sit *outside* `nallputer/`:

```
NALLY (public Render service)
  │
  ├── NallPuterClient      → authenticated HTTP to private NALLPUTER (Bearer, constant-time)
  ├── Machine Preflight    → validates MachineProfile before any work
  ├── Execution Orchestrator → idempotency, polling, timeout, cancel, policy_denied
  └── Reconnection         → detects instance replacement via health/uptime, re-fetches profile, reconciles
```

No work is executed until preflight succeeds. No retry invents a new `computer_id`. All semantics are expressed in `MachineProfile` terms — never `if provider == "render"`.

This keeps the boundary clean: **Phase 4 built the computer; Phase 5 teaches NALLY how to operate it; Phase 6 builds the machine underneath the already-agreed contract.**

---

## 1. NallPuterClient — the only HTTP surface NALLY touches

### Transport

| Property | Normative |
|----------|-----------|
| **Base URL** | `NALLPUTER_URL` env (e.g., `https://nallputer.internal/v1` on Render private networking, `http://localhost:8000/v1` local). Never hard-coded. |
| **Auth** | `Authorization: Bearer <token>` from `NALLPUTER_TOKEN` env, forwarded verbatim. Client signs no other auth in v0.1. Verification is server-side constant-time; client does not interpret token. |
| **Private networking only** | NALLY’s public ingress never exposes NALLPUTER. The client is the bridge across Render private network; no browser/DNS fallback. |
| **Idempotency** | Every `POST /v1/exec` and `POST /v1/computer/{id}/destroy` is sent with `Idempotency-Key: <uuid v4>` generated once per logical operation and reused on retry (OpenAPI `Idempotency-Key` header). `GET`s are idempotent without key. |
| **Timeouts** | Client TCP connect 3s, TTFB 10s, overall `GET /v1/health` 5s. Exec creation is not execution — `POST /v1/exec` returns `201 {run_id}` quickly; long work is observed via `GET /v1/exec/{id}` polling. |

### Methods (normative — mirrors `openapi.yaml`)

```ts
interface NallPuterClient {
  // Machine Contract (003) — mandatory first calls
  getMachine(): Promise<MachineProfile>
  getHealth(): Promise<Health>

  // Computer lifecycle (008)
  createComputer(resources?: ResourcesInput): Promise<Computer>
  getComputer(computer_id: string): Promise<Computer>
  startComputer(computer_id: string): Promise<Computer>
  stopComputer(computer_id: string): Promise<Computer>
  destroyComputer(computer_id: string, idempotencyKey: string): Promise<void>
  getSync(computer_id: string): Promise<SyncState>
  forceSync(computer_id: string): Promise<SyncState>

  // Execution (006 + 008 run lifecycle)
  exec(req: ExecCreate, idempotencyKey: string): Promise<Run>              // POST /v1/exec → run_id
  getRun(run_id: string, cursor?: number, limit?: number): Promise<Run>    // GET /v1/exec/{id}?cursor=&limit=
  cancelRun(run_id: string): Promise<Run>                                   // DELETE /v1/exec/{id}
  streamRun?(run_id: string): never // 501 in v0.1 — calling returns CapabilityError, do not retry

  // Workspace (005)
  fileRead(computer_id: string, path: string, opts?: {offset?: number, limit?: number, encoding?: "utf8"|"base64"}): Promise<FileReadResponse>
  fileWrite(computer_id: string, path: string, content: string, opts?: {encoding?: "utf8"|"base64"}): Promise<{path: string, bytes_written: number, sync_state: SyncState}>
  fileList(computer_id: string, path: string, opts?: {recursive?: boolean, limit?: number}): Promise<FileListResponse>
}
```

All methods surface the union `Result<T> | {code, message, policy_result?}` — never throw raw `fetch` errors without a `code`.

### Error categories the client must distinguish (not collapse to “failed”)

| `status` / HTTP | Meaning | Client action |
|-----------------|---------|---------------|
| `policy_denied` (403) | Pre-spawn deny: `filesystem_denied`, `egress_blocked`, `workspace_quota_exceeded→507`, `concurrency_limited→429`, `credential_in_spec` | Fix input (path/allowlist/quota/env spec) then retry with a **new** idempotency key. Do not spin. |
| `timed_out` | Wall-time exceeded | Retry with larger `timeout_sec` only up to `MachineProfile.resources.wall_time_sec`; otherwise surface. |
| `cancelled` | Explicit `DELETE /exec/{id}` | Do not retry silently. |
| `failed` (non-zero exit) | Command error | Retry depends on command idempotency — caller decides; adapter does not auto-retry failed exits. |
| `410 Gone` | Run evicted (TTL 24h) | No retry of same `run_id`; re-exec with new idempotency key if still needed. |
| `501` | `streaming_not_supported` / `pause_not_supported` | Never retry; poll instead (003 `capabilities.*==false`). |
| `503` | `store_degraded` / `env_replay_failed` on `GET /health` or `GET /computer` | Backoff, do not mutate workspace, re-fetch preflight. See § 4. |

---

## 2. Machine Preflight — the mandatory handshake

No `exec` or `files/write` is issued until preflight passes.

```
connect
  ↓
GET /v1/machine
  ↓ validate: computer_id present, persistence instance/workspace/packages in expected set
  ↓ cache: MachineProfile (in NALLY memory, keyed by computer_id)
  ↓
GET /v1/health
  ↓ validate: status ∈ {ok,recovering}, computer_id matches machine, sync_state ∈ {synced,pending}
  ↓ if degraded/env_replay_failed → enter Reconnection (§ 4), not Execution
  ↓
ready → execute work
```

**Caching:** Cache `MachineProfile` for the lifetime of the `computer_id`. Invalidate only on `uptime_sec` reset or explicit `GET /v1/machine` mismatch. Unknown `provider` values are accepted — adapter branches on `persistence.*`/`capabilities`/`resources` + `restart_behavior`, never `provider`.

**Package-aware routing (004):**

| `persistence.packages` | Adapter behavior on `pip install` / `apt` intent |
|------------------------|--------------------------------------------------|
| `reconstructible` | Prefer **declarative** path: `fileWrite(environment.yaml, +pkg) → exec("nallputer env apply")`. If caller instead does imperative `exec("pip install pandas==2.2.3")`, adapter logs `env_drift_risk` — durability will depend on the server’s `environment.yaml` reconciler (004). Still poll `environment: {spec_rev, lock_rev, drift}` in the run response. |
| `persistent` | Direct `exec("pip install ...")` is durable; declarative path still valid but not required. |
| `ephemeral` | Warn: installs are valid but will vanish on next `instance_recreated`; force declarative path. |

**Readiness contract:** `GET /v1/computer/{id}.state == "running"` and `GET /v1/health.status == "ok"` together mean “safe to execute.” If `computer.state == "stopped"` and `exec` is requested, adapter calls `startComputer(computer_id)` first and waits for `running` + `synced` (004 restore+replay).

---

## 3. Execution Orchestrator — idempotency, polling, timeout, cancel, policy_denied

### Idempotency

- Adapter generates one `Idempotency-Key` per **logical** exec (same `computer_id+command+cwd+timeout_sec+env` intent) and reuses it across all retries of that logical exec. Server guarantees retries with same key return same `run_id` + status (OpenAPI `POST /v1/exec`).
- Different logical execs must have different keys. Destroy always requires a fresh key (never reuse an exec key).

### Polling (v0.1 transport — no streaming)

```
POST /v1/exec → 201 {run_id}
  ↓
poll GET /v1/exec/{run_id} every 500ms (jitter ±100ms) while status ∈ {queued,running}
  ↓ bounded output paging when truncated: GET /v1/exec/{run_id}?cursor=<bytes already read>&limit=100000
  ↓
terminal ∈ {succeeded,failed,timed_out,cancelled,policy_denied}
```

- Poll interval is fixed 500 ms for v0.1; no exponential backoff on runs (that would hide `health` changes). Backoff is only for `503` recovery (§ 4).
- `cursor`/`limit` paging is mandatory when `truncated: true`; adapter concatenates pages by `next_cursor` and returns unified `stdout` to caller.
- Caller may bound total wall time independently of server `wall_time_sec` — adapter’s `exec({timeout_sec})` is a per-run override capped by `MachineProfile.resources.wall_time_sec`; exceeding that cap is a client error before request.

### Timeout handling

- Server enforces `wall_time_sec` (006) as hard kill (`SIGTERM pgid` → `SIGKILL pgid`). Adapter surfaces that as `status: timed_out` with `policy_result: {reason: wall_time_exceeded}`.
- Adapter does **not** auto-retry `timed_out` — caller must bump `timeout_sec` (still ≤ machine max) or fix hang.

### Cancellation

- `cancelRun(run_id)` → `DELETE /v1/exec/{run_id}` → server kills pgid. Adapter treats cancel as success of the cancel operation (returns `cancelled`) and does not re-poll the original command.

### policy_denied

- Must be surfaced with `policy_result` (`decision: deny, reason: ..., destination?`). Never hidden as generic `failed`.
- Typical `policy_denied` reasons and NALLY fixes:

| Reason | Fix |
|--------|-----|
| `filesystem_denied` | Path outside workspace root or blocked symlink — change `path`/`cwd` to `persistent_paths` area. |
| `egress_blocked` | `dst_host` not in `NALLPUTER_EGRESS_ALLOWLIST` — operator adds host, adapter does not override. |
| `workspace_quota_exceeded` | Free `artifacts/`/`tmp/` or request larger `workspace_gb`. |
| `concurrency_limited` | Wait and retry; default cap 5 concurrent runs (006). |
| `credential_in_spec` | Remove secret literal from `environment.yaml`; use per-run `env` injection. |

---

## 4. Reconnection — detecting instance replacement without coupling to Render

### The signal (from 003 + 008)

```
GET /v1/health → {computer_id, uptime_sec, sync_state, last_sync_rev, ...}
```

- Same `computer_id`, reset `uptime_sec` → **possible runtime replacement** (new disposable instance after Render `SIGTERM`).
- Brief `503` (`recovering`, `sync_state: degraded|env_replay_failed`) → **do not** fire new execs; enter reconnect loop.

### Reconnect loop (normative)

```
uptime_sec reset  OR  503 on health/computer
  ↓
backoff: 1s → 2s → 5s → 10s (capped), jitter ±500ms   // lifecycle backoff (008 §4)
  ↓ on each iteration:
GET /v1/machine   // confirm same computer_id, re-cache profile
GET /v1/health    // wait for status: ok, sync_state: synced|pending
GET /v1/computer/{id} // confirm state: running|idle
  ↓ when ok+synced:
reconcile → continue using SAME computer_id
```

**Reconcile = verify, not re-create:**

1. Re-list expected durable state via `fileList(computer_id, "/home/nally/workspace/projects")` — same `computer_id` means same canonical workspace restored (004).
2. If `persistence.packages == "reconstructible"`, check `environment: {lock_rev}` via `getSync(computer_id)` — if replay failed, health `last_error` + the failed replay `run_id` are visible; adapter surfaces them and requires caller to fix `environment.yaml` then retry.
3. Never invent a new `computer_id` on reconnect — a new `computer_id` means a different computer, not a recovery.

### When reconnect is impossible

| Signal | Action |
|--------|--------|
| `GET /v1/computer/{id} → 404` | Computer was `destroyed` — `computer_id` retired. Caller must `createComputer` to get a new `computer_id`. |
| `GET /v1/health → 503` beyond backoff deadline (suggest 60s) | Surface `store_degraded` to caller; do not loop forever. |

---

## 5. Where NALLY runs this adapter

| Concern | v0.1 |
|---------|------|
| **Where** | NALLY process (public Render service). No agent code runs inside NALLPUTER except via `exec`/`files` API. |
| **Language** | TypeScript/JS in NALLY repo — `NallPuterClient` as a plain class with `fetch` (or `undici` / `axios`). No SDK publish required for MVP; import path `@klyntech/nallputer-client` is valid later. |
| **Config surface** | `NALLPUTER_URL`, `NALLPUTER_TOKEN` (Bearer), `NALLPUTER_STARTUP_GRACE_MS` (default 30s to cover cold restore+replay). No provider-specific flags. |
| **No Docker leakage** | NALLY never knows about `--memory`, `--pids-limit`, cgroup paths, or egress proxy `127.0.0.1:3128` — those are `MachineProfile` capability/resource fields. |

---

## 6. Example — preflight + exec + policy_denied + reconnect

```ts
// NALLY startup
const client = new NallPuterClient({ baseUrl: process.env.NALLPUTER_URL!, token: process.env.NALLPUTER_TOKEN! })

// 1. Preflight
const machine = await client.getMachine()             // {computer_id, persistence:{packages:"reconstructible"}, ...}
const health  = await client.getHealth()
if (health.sync_state === "degraded") await reconnect(client, machine.computer_id)
if (health.sync_state === "env_replay_failed") throw new Error(`fix environment.yaml: ${health.last_error}`)

// 2. Prefer declarative package install (004)
if (machine.persistence.packages === "reconstructible") {
  await client.fileWrite(machine.computer_id, "/home/nally/workspace/.nallputer/state/environment.yaml",
    "version: 1\npython:\n  packages: [\"pandas==2.2.3\"]\n")
  await execOrThrow(client, { computer_id: machine.computer_id, command: "nallputer env apply" })
}

// 3. Exec with idempotency + bounded output paging
const key = crypto.randomUUID()
const run = await client.exec({ computer_id: machine.computer_id, command: "pytest -q", cwd: "/home/nally/workspace/projects" }, key)
const final = await poll(client, run.run_id) // 500ms jitter while queued|running, handles cursor paging
if (final.status === "policy_denied") {
  // e.g., {reason: "egress_blocked", destination:"evil.com:443"} — do not retry with same allowlist
  throw new PolicyDenied(final.policy_result!)
}
if (final.sync_pending) await client.forceSync(machine.computer_id) // optional durability barrier

// 4. Reconnect on health change
async function reconnect(client: NallPuterClient, computer_id: string) {
  for (const delay of [1000, 2000, 5000, 10000, 10000, 10000]) { // capped, with jitter
    await sleep(delay + Math.random()*500)
    const m = await client.getMachine()
    const h = await client.getHealth()
    const c = await client.getComputer(m.computer_id)
    if (h.status === "ok" && h.sync_state !== "degraded" && c.state in ["running","idle"]) return
  }
  throw new Error("store_degraded — retry later")
}
```

---

## 7. What this does NOT decide (deferred to MVP / Evaluation)

- Concrete NALLY in-repo file path for `NallPuterClient` (e.g., `nally/src/computer/nallputerClient.ts`) — chosen when NALLY repo is wired; the interface above is the contract.
- Retry count for `store_degraded` vs user-visible deadline — MVP picks 60s capped backoff; Evaluation (Phase 7) measures reconnect latency vs cold-restore time.
- Batching / pipelining of multiple concurrent execs — v0.1 supports concurrent `run_id`s but evaluation will set the cap (default 5, 006).
- Snapshot/pausing flows — reserved, `501` in v0.1 (003).
- Encryption-at-rest policy for external store — v0.2+.

---

## Evidence trace

- Manus / E2B / Daytona / Modal: per-computer identity (`computer_id`) + distinct stop vs destroy — motivates “never invent a new `computer_id` on reconnect.”
- OpenAI (Responses container contract) + SWE-agent ACI: bounded observation, stable run IDs, explicit empty-output — motivates poll+cursor paging and `truncated` semantics.
- Anthropic (sandboxing): enforcement below agent, FS=net parity — motivates `policy_denied` before spawn and `MachineProfile` as single truth for all gates (007 → surfaced in adapter errors).
- OpenHands: client-server runtime — motivates preflight vs execution split.
- Render private networking docs: motivates private `baseUrl` and no public ingress assumption.

---

## Review gate outcome

Locked 2026-09-07. Closes Phase 5. Next: **Phase 6 MVP v0.1** — build the disposable runtime underneath the already-frozen contract (`003`–`009` + `openapi.yaml`). No implementation may change an interface locked here without a new decision and migration note.
