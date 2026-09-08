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
| 4 | Workspace + Runtime + Security + Lifecycle models | ✅ `docs/decisions/005` `006` `007` `008` |
| 5 | NALLY integration — Computer Adapter | ✅ `docs/decisions/009-nally-integration.md` |
| 6 | MVP v0.1 — disposable runtime + sync engine | ✅ `nallputer/` (FastAPI, cgroup v2, pgid, egress proxy, sync stub) |
| 7 | Evaluation — minimal gate | ✅ LOCKED — 19/19 PASS at `5a44765` (`tests/results/REPORT.md`, Windows/TestClient, measure-only) |
| 7-full | Evaluation — Linux CI harness | 🟡 scaffolded at `e3d3891` (`tests/docker/`, `Makefile eval-linux`, `010`) → CI green `34272443007` (19/19 on ubuntu-latest) · Linux baseline `tests/results/linux/REPORT.md` ⏳ not yet committed |
| 8 | Production architecture | ⬜ **BLOCKED** (awaiting Linux baseline per 010) |

Execution sequence: `2a ─┐ → 3 → 4 → 5 → 6 → 7 → 8` and `2b ─┘` (both block 3). Render is Lab Rat #1; external store is canonical (004). `7` is locked; `7-full` is scaffolded (010) and running in CI; `8` is blocked until Linux baseline is committed.

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
│   ├── decisions/         # Phases 2 + 2a + 2b + 4 + 5: locked decisions
│   │   ├── 001-computer-model.md        # + addendum 2026-09-07 (003/004)
│   │   ├── 002-resource-model.md        # + addendum 2026-09-07 (003/004)
│   │   ├── 003-machine-contract.md      # 2a: provider-neutral MachineProfile
│   │   ├── 004-persistent-state.md      # 2b: canonical external store + env reconstruct
│   │   ├── 005-workspace-model.md       # Phase 4: workspace layout, quota, sync
│   │   ├── 006-runtime-model.md         # Phase 4: cgroup v2, Docker, process groups
│   │   ├── 007-security-model.md        # Phase 4: FS+net, credential isolation, audit
│   │   ├── 008-lifecycle-model.md       # Phase 4: computer+run state machines, auto-stop
│   │   └── 009-nally-integration.md     # Phase 5: Computer Adapter (NALLY side)
│   └── api/
│       └── openapi.yaml               # Phase 3: Machine & Execution contract (Bearer, 501 stubs)
├── nallputer/             # Phase 6: MVP runtime (FastAPI + workspace jail + pgid + sync stub)
│   ├── Dockerfile               # tini + cgroup v2 + workspace
│   ├── pyproject.toml
│   └── nallputer/app,core,routers
├── tests/                 # Phase 7: minimal ✅ 19/19 + Linux CI harness 🟡
│   ├── conftest.py              # TestClient + computer_id + exec_and_poll
│   ├── test_latency.py, test_startup.py, test_lifecycle.py
│   ├── test_isolation.py, test_persistence.py, test_output.py
│   ├── test_linux_cgroup.py     # Linux-only (skipped on Windows)
│   ├── docker/                  # Phase 7-full scaffold (e3d3891)
│   │   ├── Dockerfile.eval
│   │   ├── docker-compose.eval.yml
│   │   ├── collect.py
│   │   └── run.sh
│   └── results/
│       ├── REPORT.md            # Windows minimal baseline (5a44765) — committed
│       ├── *.json               # measure-only artifacts (14d CI retention)
│       └── linux/
│           ├── .gitkeep         # awaiting first committed Linux REPORT
│           └── REPORT.md        # ⏳ not yet committed (CI green 34272443007)
├── .github/
│   └── workflows/ci.yml         # eval-minimal + eval-linux (push master+PR+dispatch, pip cache, 14d, informational)
├── render.yaml            # Render private service (ephemeral) + token
├── Makefile               # eval / eval-linux / docker-eval
├── .env.example
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

## Next: Phase 7-full → Phase 8 (BLOCKED)

Phase 7 minimal is **LOCKED 19/19 PASS** at `5a44765` (`tests/results/REPORT.md`, Windows/TestClient, measure-only). Phase 7-full is **scaffolded** at `e3d3891` (`tests/docker/`, `Makefile eval-linux`, `010`) and **CI is green** (`34272443007` — 19/19 on ubuntu-latest, Docker `cgroup v2`). **Linux baseline `tests/results/linux/REPORT.md` is not yet committed** — that separate evidence commit will unlock Phase 8 per `010`. `pids.max` path discovery remains a harness refinement (`collect.py`), not a runtime failure. **Do not modify runtime, contracts 003–009, 010, or the harness before that baseline.** Next full gate (Docker Linux) will measure true `cgroup v2`, `pids.current`, 5-way concurrency `429`, `setsid`/`killpg` vs `taskkill`, env replay, private-network latency, then drive Phase 8.

## License

Proprietary — Klyntech / Clinton (Klyntech/Klynvybz)