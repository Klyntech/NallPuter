# NallPuter

**The computer for NALLY.**

NallPuter is the isolated, persistent execution environment that gives NALLY a real computer to operate — files, processes, shell, network, packages, and workspace state — with an agent-facing API contract and runtime-enforced security boundaries.

## Architecture

```text
NALLY (brain)
     │
     │ authenticated API (private network)
     ▼
NallPuter (computer)
     │
     ├─ Workspace    → persistent filesystem, packages, artifacts
     ├─ Runtime      → shell, processes, resource limits
     ├─ Network      → egress policy, credential isolation
     └─ Lifecycle    → create/start/stop/pause/resume/destroy
```

## Phase status

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 0 | Mission lock | ✅ |
| 1 | Prior-art research (6 docs + synthesis) | ✅ `docs/research/` |
| 2 | Computer model + Resource model decisions | ✅ `docs/decisions/001+002` |
| 2a | Machine Contract — provider-neutral `GET /v1/machine` profile | ✅ `docs/decisions/003-machine-contract.md` |
| 2b | Persistent Computer State — external canonical + sync + env reconstruct | ✅ `docs/decisions/004-persistent-state.md` |
| 3 | Machine & Execution API contract + OpenAPI | ✅ `docs/api/openapi.yaml` |
| 4 | Workspace / Runtime / Security / Lifecycle models | ⬜ |
| 5 | NALLY integration | ⬜ |
| 6 | MVP v0.1 — disposable runtime + sync engine | ⬜ `nallputer/` |
| 7 | Evaluation | ⬜ `tests/` |
| 8 | Production architecture | ⬜ |

Execution sequence: `2a ─┐ → 3 → 4 → 5 → 6 → 7 → 8` and `2b ─┘` (both block 3). Render is Lab Rat #1; external store is canonical (004).

## Repository structure

```
NallPuter/
├── docs/
│   ├── research/          # Phase 1: six research docs + synthesis
│   │   ├── manus.md
│   │   ├── openai.md
│   │   ├── anthropic.md
│   │   ├── openhands-swe.md
│   │   ├── e2b-daytona-modal.md
│   │   ├── requirements.md
│   │   └── _evidence-index.md
│   ├── decisions/         # Phases 2 + 2a + 2b: locked decisions
│   │   ├── 001-computer-model.md        # + addendum 2026-09-07 (003/004)
│   │   ├── 002-resource-model.md        # + addendum 2026-09-07 (003/004)
│   │   ├── 003-machine-contract.md      # 2a: provider-neutral MachineProfile
│   │   └── 004-persistent-state.md      # 2b: canonical external store + env reconstruct
│   └── api/
│       └── openapi.yaml               # Phase 3: Machine & Execution contract (Bearer, 501 stubs)
├── nallputer/             # Implementation (Phase 6+)
├── tests/                 # Phase 7 evaluation harness
└── README.md
```

## Key design principles (from Phase 1)

1. **Computer ≠ shell command** — NallPuter is a runtime contract (execution + workspace + network + lifecycle + policy), not a `run_command` replacement
2. **Security below the agent** — NALLY decides intent; NallPuter independently enforces filesystem, network, process, and credential boundaries at the OS/runtime layer
3. **Persistence has layers** — v0.1: filesystem + packages; v0.2+: process/memory via pause/resume
4. **Agent-Computer Interface matters** — Structured observations, targeted file access, explicit empty-output semantics, stable run/computer IDs
5. **Lifecycle is first-class** — Explicit state machine, auto-stop policy, recovery, snapshot boundary
6. **Trust split** — `NALLY decision → NallPuter policy → OS enforcement` — neither layer silently weakens the other

## v0.1 scope (locked)

| Included | Excluded |
|----------|----------|
| Linux container (Docker) | Desktop GUI |
| Persistent workspace volume | Browser automation |
| Shell execution + file ops | Multi-user platform |
| Process management (start/stop/kill) | Marketplace |
| Resource quotas (8 knobs) | GPU (v0.3+) |
| Network egress policy (deny-by-default) | Full VM isolation (v0.2+) |
| Computer lifecycle (create/start/stop/destroy) | Pause/resume (v0.2+) |
| API: exec, files, computer status | Snapshot/restore (v0.2+) |
| Render private service deployment | |

## Deployment target (v0.1 — Lab Rat #1)

- **NALLY**: public Render web service
- **NallPuter**: private Render service (ephemeral runtime) + external canonical storage (sync engine), same region
- **Lab Rat impl**: Render Persistent Disk used as write-through cache behind the `external_canonical` abstraction (004) — swappable to S3/R2/volume without API break
- **Network**: Render private networking (no public ingress to NallPuter)
- **Auth**: Bearer token v0.1 (constant-time compare, pluggable to mTLS/JWT — 003)
- **Persistence**: runtime disposable; `GET /v1/machine` reports `persistence.*` and `restart_behavior`; `GET /v1/health.sync_state` exposes `synced|pending|degraded`

## Research evidence discipline

All Phase 1 documents separate three evidence tiers:
- **Documented fact** — vendor primary source
- **Third-party observation** — benchmarks, implementations, community analysis
- **NallPuter inference** — our design conclusion, not a claim about the source system

This makes architecture decisions traceable and defensible.

## Next: Phase 4 — Workspace / Runtime / Security / Lifecycle Models

Builds on the now-locked Machine Contract (003) + Persistent State (004) + OpenAPI (Phase 3 `docs/api/openapi.yaml`):

- `GET /v1/machine` → provider-neutral profile (persistence, resources, capabilities, `ephemeral_paths`/`persistent_paths`)
- `GET /v1/health` → liveness + `computer_id` binding + `sync_state`
- `POST /v1/exec` → `run_id`, `GET /v1/exec/{run_id}` polling, `DELETE` cancel (process-tree kill), `GET /stream` → `501` when `capabilities.streaming=false`
- `POST /v1/files/{read,write,list}` — same policy model as exec, quota-checked, atomic; env spec at `.nallputer/state/environment.yaml` + `environment.lock` for `reconstructible` packages
- `GET/POST /v1/computer/{id}/{start,stop,destroy}` + `GET/POST /v1/computer/{id}/sync` (debounced+flush+restore engine, 004)
- Reserved 501s: `/computer/{id}/{pause,resume,snapshot}`

## License

Proprietary — Klyntech / Clinton (Klyntech/Klynvybz)