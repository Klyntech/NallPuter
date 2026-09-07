# NallPuter Decision 001 — Computer Model

**Status:** LOCKED
**Date:** 2026-09-06
**Review gate:** Post-Phase-1 synthesis review

## Decision

**Hybrid model: persistent container for v0.1, VM path for v0.2+**

- v0.1: Linux container (Docker) with persistent workspace volume, running as a private Render service behind private networking
- v0.2+: evaluate Firecracker microVM or Kata Containers for stronger isolation and process/memory pause-resume
- Computer identity is explicit and outlives individual command executions
- The container/VM is a single computer, not a per-request sandbox

## Options evaluated

| Option | Description | Pros | Cons | Verdict |
|--------|-------------|------|------|---------|
| **A. Ephemeral container** | Fresh container per task, destroyed after | Simple, reproducible, no idle cost | No persistence, no long-running processes, high cold-start per task | Rejected — violates core persistence requirement |
| **B. Persistent container** | Container stop/start preserves filesystem volume | Fast (Docker on Render), persistent workspace, packages survive | No process/RAM survival across restart; container != security boundary | **Selected for v0.1** |
| **C. VM** | Full virtual machine | Stronger isolation, kernel separation | Heavier, slower boot, overkill for v0.1 | Deferred to v0.2+ |
| **D. Persistent VM** | Always-on VM with process persistence (Manus model) | True 24/7, processes survive | Cost, complexity, no Docker-in-Docker on Render | Deferred to v0.2+ |
| **E. Hybrid (selected)** | Container v0.1, VM path later | Iterates fast, matches Render, defers isolation depth | Must design API so VM swap is non-breaking | **Locked** |

## Rationale

1. **Render deployment reality**: NallPuter v0.1 deploys as a private Render service with a persistent disk. Docker containers on Render start fast (~seconds), fit the 512MB RAM constraint, and work over private networking. No Docker-in-Docker requirement.

2. **Persistence split (from Phase 1)**: v0.1 guarantees filesystem + package persistence. Process/RAM persistence requires pause/resume which containers don't provide — this is explicitly v0.2+.

3. **API stability**: The NallPuter API exposes computer identity, run identity, workspace, and lifecycle operations. The implementation (container vs VM) is encapsulated. Swapping container → VM in v0.2+ must not break the API contract.

4. **Security boundary**: Docker is the *runtime*, not the *security boundary*. NallPuter enforces filesystem, network, process, and credential policy at the API/runtime layer regardless of underlying isolation mechanism. This matches the Anthropic finding that enforcement must be below the agent.

## Computer identity

- `computer_id`: stable UUID assigned at creation
- Survives stop/start/restart
- Used for reconnection, policy attachment, quota accounting
- Distinct from `run_id` (per-execution)

## Lifecycle states (v0.1)

```
creating → running → idle → stopping → stopped → starting → running
                │
                └── error → recovering → (running | stopped | destroyed)
```

- `idle`: no active runs, computer kept alive
- `stopped`: filesystem persisted, compute released
- `destroyed`: volume deleted, computer_id retired

## API implications (feeds Phase 3)

- `POST /v1/computer` — create computer (returns computer_id)
- `GET /v1/computer/{computer_id}` — status, resource usage, workspace info
- `POST /v1/computer/{computer_id}/start`
- `POST /v1/computer/{computer_id}/stop`
- `POST /v1/computer/{computer_id}/destroy`
- `POST /v1/exec` — runs inside a computer (requires computer_id)
- Future v0.2+: `POST /v1/computer/{computer_id}/pause`, `POST /v1/computer/{computer_id}/resume`

## What this does NOT decide (deferred)

- Exact isolation mechanism inside container (bubblewrap, gVisor, nsjail, plain Docker)
- Whether Render persistent disk or S3-backed volume for workspace
- Authentication mechanism between NALLY and NallPuter (Bearer token, mTLS, etc.)
- Multi-user vs single-user computer ownership
- Snapshot/restore semantics (v0.2+)

## Evidence trace

- Manus: persistent computer identity, tiered resources, lifecycle distinct from task
- OpenAI: hosted container as computer contract, separation of orchestration/execution
- Anthropic: enforcement at runtime layer, not prompt layer
- OpenHands/SWE-agent: client-server runtime, stable computer interface
- E2B/Daytona/Modal: pause/resume as distinct from stop/start, snapshots ≠ workspace persistence
- NallPuter requirements.md: Pillar 1 (Isolation), Pillar 2 (Lifecycle), Pillar 3 (Workspace)

## Review gate outcome

Synchronous review completed. Decision locked. Proceed to 002-resource-model.md.