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
| 2 | Computer model + Resource model decisions | ✅ `docs/decisions/` |
| 3 | API contract + OpenAPI | ⬜ |
| 4 | Workspace model | ⬜ |
| 5 | Security model | ⬜ |
| 6 | Lifecycle model | ⬜ |
| 7 | NALLY integration | ⬜ |
| 8 | MVP v0.1 | ⬜ |
| 9 | Evaluation | ⬜ |
| 10 | Production architecture | ⬜ |

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
│   └── decisions/         # Phase 2: locked decisions
│       ├── 001-computer-model.md
│       └── 002-resource-model.md
├── nallputer/             # Implementation (Phase 8+)
├── tests/                 # Phase 9 evaluation harness
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

## Deployment target (v0.1)

- **NALLY**: public Render web service
- **NallPuter**: private Render service + persistent disk, same region
- **Network**: Render private networking (no public ingress to NallPuter)
- **Auth**: Bearer token (NALLY → NallPuter), constant-time comparison

## Research evidence discipline

All Phase 1 documents separate three evidence tiers:
- **Documented fact** — vendor primary source
- **Third-party observation** — benchmarks, implementations, community analysis
- **NallPuter inference** — our design conclusion, not a claim about the source system

This makes architecture decisions traceable and defensible.

## Next: Phase 3 — API Contract

Design the OpenAPI specification for:
- `POST /v1/exec` → `run_id`
- `GET /v1/exec/{run_id}` → output/status/exit (polling v0.1)
- `DELETE /v1/exec/{run_id}` → cancel
- `GET /v1/exec/{run_id}/stream` — contract-only (SSE/WebSocket future)
- `POST /v1/files/{read,write,list}`
- `GET/POST /v1/computer/{id}/{start,stop,destroy,status}`

## License

Proprietary — Klyntech / Clinton (Klyntech/Klynvybz)