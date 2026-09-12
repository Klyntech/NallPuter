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
| 7-full | Evaluation — Linux CI harness | ✅ LOCKED — 20/20 PASS at `2195f2b` (`tests/results/linux/` 20 JSON + `junit.xml`/`pytest.log`/`REPORT.md`, `cgroup v2` `100`/`3`, `concurrency 5→429`, `setsid`/`killpg`) — CI green |
| 8 | Production architecture | ✅ LOCKED `011` (`e82f9e4`→`5863dbc`) |
| 8A–8F | Production NallPuter — persistence, sync, env, security, lifecycle, observability | ✅ `5a72833` (8E) + `d5d841b` (8C verification) on top of `7af639a`/`ada54d1`/`7400b68`/`428a2ad`/`91b0628` — **39 passed, 3 skipped, 0 failures** Windows gate (`-k "not linux"` 39/3), combined `8A+8B+8C+8D+8E+8F` — `tests/results/linux/REPORT.md` production gate (Windows 39, Linux Lab Rat 20/20 preserved, Docker re-run pending CI) |

Execution sequence: `2a ─┐ → 3 → 4 → 5 → 6 → 7 → 8 (8A→8F)` and `2b ─┘` (both block 3). Render is Lab Rat #1; external store is canonical (004). `7` + `7-full` + `8` are locked; `011` is the authority for Phase 8 (no `003–009` reopen without `Exception`). Production gate Windows PASS, Linux PENDING CI re-run (`make eval-linux` on `5a72833`).

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
│   ├── decisions/         # Phases 2 + 2a + 2b + 4 + 5 + 8: locked decisions
│   │   ├── 001-computer-model.md        # + addendum 2026-09-07 (003/004)
│   │   ├── 002-resource-model.md        # + addendum 2026-09-07 (003/004)
│   │   ├── 003-machine-contract.md      # 2a: provider-neutral MachineProfile
│   │   ├── 004-persistent-state.md      # 2b: canonical external store + env reconstruct
│   │   ├── 005-workspace-model.md       # Phase 4: workspace layout, quota, sync
│   │   ├── 006-runtime-model.md         # Phase 4: cgroup v2, Docker, process groups
│   │   ├── 007-security-model.md        # Phase 4: FS+net, credential isolation, audit
│   │   ├── 008-lifecycle-model.md       # Phase 4: computer+run state machines, auto-stop
│   │   ├── 009-nally-integration.md     # Phase 5: Computer Adapter (NALLY side)
│   │   ├── 010-evaluation-full.md       # Phase 7-full: Linux/Docker plan (LOCKED)
│   │   └── 011-production-architecture.md # Phase 8: Lab Rat → production (LOCKED 2026-09-08)
│   └── api/
│       └── openapi.yaml               # Phase 3: Machine & Execution contract (Bearer, 501 stubs)
├── nallputer/             # Phase 6: MVP runtime (FastAPI + workspace jail + pgid + sync stub)
│   ├── Dockerfile               # tini + cgroup v2 + workspace
│   ├── pyproject.toml
│   └── nallputer/app,core,routers
├── tests/                 # Phase 7: minimal ✅ 19/19 + Linux ✅ 20/20 + Phase 8 ✅ 39/39
│   ├── conftest.py              # TestClient + computer_id + exec_and_poll + 8C/8E isolation (yanked scrub, lifecycle _last_activity)
│   ├── test_latency.py, test_startup.py, test_lifecycle.py
│   ├── test_isolation.py, test_persistence.py, test_output.py
│   ├── test_persistence_adapter.py # 8A S3-compatible (local/moto)
│   ├── test_sync_engine.py      # 8B manifest-last, If-Match degraded
│   ├── test_env_reconstruct.py  # 8C yaml never-mutate, 503
│   ├── test_security_proxy.py   # 8D 127.0.0.1:3128 allowlist audit
│   ├── test_lifecycle_8e.py     # 8E stop/start, 503, auto-stop 2s, same cid
│   ├── test_observability.py    # 8F pids/memory real
│   ├── test_linux_cgroup.py     # Linux-only (v2 + 429)
│   ├── docker/                  # Phase 7-full + Phase 8 harness
│   │   ├── Dockerfile.eval
│   │   ├── docker-compose.eval.yml # cpus 0.5/mem 512m/pids 100, user 0:0
│   │   ├── collect.py           # Windows + Linux evidence table
│   │   └── run.sh
│   └── results/
│       ├── REPORT.md            # Windows minimal baseline (5a44765) — 19/19
│       ├── *.json               # Windows measure-only
│       └── linux/               # Phase 8 production gate (5a72833) — Windows 39, Linux 20/20 preserved + Docker re-run pending
│           ├── REPORT.md        # production gate (8A–8F combined, not Lab Rat repeat)
│           ├── *.json, junit.xml, pytest.log
│           └── (was .gitkeep)
├── .github/
│   └── workflows/ci.yml         # eval-minimal + eval-linux (push master+PR+dispatch, pip cache, 14d, informational, green 34274399240)
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

## Next: Phase 8 closure → NALLY integration (009)

Phase 7 is **LOCKED** (`5a44765` 19/19 + `2195f2b` 20/20). **011** is **LOCKED** (S3-compatible canonical, hard `5→429`, `900s` default, no `003–009` reopen). **Phase 8 is implemented** — `8A` `91b0628`, `8B` `428a2ad`, `8C` `7400b68`+`d5d841b`, `8D` `7af639a`, `8F` `ada54d1`, `8E` `5a72833` — combined Windows gate **39 passed, 3 skipped, 0 failures** (`~37s`, within 180s), `tests/results/linux/REPORT.md` production gate (Windows 39, Linux Lab Rat 20/20 preserved, Docker `make eval-linux` pending CI). **No `idle_since` in API, no queue/012, no openapi change; auto-stop `1s` poll + `flush parity` (degraded→`recovering` never falsely `stopped`).**

**Locked sequence:**
```text
8A–8F → combined Linux/production gate → REPORT.md + evidence → README + baseline → Phase 8 = ✅ → ONLY THEN full read-only NALLY mapping
```

**NALLY mapping (next, read-only, no Phase 9 lock yet):**
* **A. NallPuter boundary** — `NallPuterClient`, `NALLPUTER_URL/TOKEN`, preflight `machine→health`, `computer_id` lifecycle, `exec`/`poll 500ms`/`cancel`/`paging`, `429/503/policy_denied`, `sync_state/lock_rev`, reconnect `uptime_sec` `1s→10s` backoff.
* **B. NALLY control plane** — `TaskRouter/RouteDecision`, planner, ReAct, tool registry/executor, MCP, sub-agents, memory, skills, tracing, receipts/verification, streaming.
* **C. Execution-path map** — `RouteDecision → planner/reasoner → Computer Adapter → NallPuterClient → preflight → computer_id → exec/files/env → observation → reasoning loop`.
* **D. Gap classification** — `✅ exists | 🔧 small addition | 🧩 new NALLY component | ⚠️ contract gap→Exception | ❌ duplicate`.

That map defines minimal integration work before `9B` e2e and `9D` real consumer. **No 9B/9D implementation before mapping.** `NALLY's contract does not change` — `openapi.yaml` frozen.

## License

Proprietary — Klyntech / Clinton (Klyntech/Klynvybz)