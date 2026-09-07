# NallPuter Phase 1 Synthesis — Requirements

> Purpose: translate prior-art research into candidate requirements for the NallPuter architecture. This document is a synthesis, not an implementation specification.

## Evidence discipline

- A requirement is a NallPuter design inference unless explicitly marked otherwise.
- Vendor claims are not treated as proof that the same implementation is suitable for NallPuter.
- Third-party observations inform interface design but do not become product guarantees.
- Any unresolved item remains an architecture decision for Phase 2–6.

## Mission

NallPuter is the computer/runtime for NALLY.

NALLY is the brain/orchestrator.

NallPuter is the isolated environment that owns execution, workspace state, processes, resource limits, lifecycle, and runtime enforcement.

The first interface is `NALLY → authenticated API → NallPuter`.

The first deployment target is a private Render service with persistent storage.

Docker is an implementation candidate, not the definition of NallPuter's security boundary.

## Cross-system convergence

Across the researched systems, the repeated primitives are:

- isolated execution environment
- workspace/filesystem
- shell or command execution
- explicit process identity
- bounded observations
- resource controls
- network policy
- credential isolation
- lifecycle state
- persistence semantics
- reconnect/recovery
- structured agent/computer interface

The systems differ mainly in how much persistence and lifecycle sophistication they provide.

## Pillar 1 — Isolation

### Filesystem isolation

- The agent must not directly access the host filesystem.
- Workspace paths must be resolved inside an explicit runtime boundary.
- Reads and writes need one policy model.
- Temporary files must have defined retention semantics.
- External volumes must be treated as privileged resources.
- File operations and shell commands must not bypass one another's security assumptions.

### Network isolation

- Network policy is separate from filesystem policy.
- Default egress should be deny-by-default or narrowly allowlisted.
- Domain-level policy should be expressible without exposing credentials to arbitrary processes.
- Network policy decisions should be auditable.
- A future proxy should permit centrally observable egress.

### Process isolation

- Every execution must have a stable run/process identity.
- Child processes inherit resource and security restrictions.
- Cancellation must terminate the relevant process tree.
- Orphan processes must be detected and reaped.
- PID limits should be measurable and enforceable.

### Credential isolation

- NallPuter should not inherit NALLY's broad environment by default.
- Secret injection should be scoped to an approved operation or destination.
- `.ssh`, cloud credentials, and host-level secrets should not become ambient sandbox files.
- Credential use should be visible in audit data without logging secret values.

## Pillar 2 — Lifecycle

### Computer lifecycle

Candidate state model:

`creating → running → idle → stopping → stopped → starting → running`

Failure path:

`running → error → recovering → running | stopped | destroyed`

Future VM path:

`running → pausing → paused → resuming → running`

### Run lifecycle

Candidate state model:

`queued → running → succeeded`

Alternative terminal paths:

`succeeded | failed | timed_out | cancelled | policy_denied`

The run lifecycle is intentionally separate from the computer lifecycle.

### Persistence layers

NallPuter should distinguish:

1. filesystem persistence
2. installed package/environment persistence
3. external storage persistence
4. process/memory persistence

v0.1 promises the first two.

v0.2+ may add process/memory persistence through pause/resume or memory snapshots.

## Pillar 3 — Workspace

Candidate layout:

`/home/nally/workspace/`

Subdirectories:

- `projects/`
- `files/`
- `artifacts/`
- `tmp/`
- `logs/`

Requirements:

- stable workspace identity
- per-computer ownership
- quota visibility
- artifact persistence
- cleanup policy for temporary data
- no implicit direct host-path access from NALLY

## Resource model

NallPuter should expose independent resource knobs:

| Resource | v0.1 role | Measurement |
|---|---|---|
| RAM | hard runtime ceiling | peak/current memory |
| CPU | reservation/limit where supported | CPU time/utilization |
| Disk | persistent workspace quota | used/remaining bytes |
| PIDs | process ceiling | active process count |
| Wall time | run timeout | elapsed time |
| Output | model-facing observation cap | bytes returned/stored |
| Workspace | logical disk quota | bytes/files |
| Network | egress policy and limits | requests/bytes/destinations |

“Bigger NallPuter” means increasing one or more of these knobs; it does not require a new product architecture.

## API contract requirements

The computer API must:

- authenticate NALLY
- return stable computer IDs
- return stable run IDs
- support idempotency for retried requests
- support polling
- define cancellation
- define bounded output
- support output pagination
- define file operations
- expose lifecycle state
- expose resource status
- carry audit identifiers
- support a future stream transport
- avoid leaking host implementation details

Candidate v0.1 endpoints:

- `POST /v1/exec`
- `GET /v1/exec/{run_id}`
- `DELETE /v1/exec/{run_id}`
- `GET /v1/exec/{run_id}/stream` as a contract-only future/optional transport
- `POST /v1/files/read`
- `POST /v1/files/write`
- `POST /v1/files/list`
- `GET /v1/computer`
- `POST /v1/computer/start`
- `POST /v1/computer/stop`

## Security trust split

NALLY has its normal permission/preflight decision.

NallPuter independently enforces runtime policy.

Therefore:

`NALLY decision → authenticated request → NallPuter policy engine → OS/runtime enforcement → execution`

Neither layer is allowed to silently weaken the other.

A denied operation should stop before the process is started.

An allowed operation still passes through NallPuter enforcement.

## Observation requirements

Observations should be structured:

- run ID
- command status
- exit code
- stdout
- stderr
- truncation marker
- byte counts
- timestamps
- resource metrics where available
- policy result
- error category

Empty successful output must be explicit.

Large output must never be returned without a cap.

## Package/environment requirements

NallPuter should allow controlled package installation because its purpose includes becoming a real developer computer.

Package behavior is part of the workspace state.

The runtime must still enforce:

- network policy
- disk quota
- process/PID limits
- execution timeout
- credential isolation

Installing a package must not imply unrestricted host access.

## Phase 9 evaluation requirements

The API must make these measurable:

- command latency
- startup latency
- peak RAM
- CPU usage
- disk usage
- process count
- command success
- timeout behavior
- cancellation reliability
- orphan-process cleanup
- workspace persistence
- package persistence
- recovery
- isolation violations
- network-policy violations
- output correctness
- workspace integrity

Comparison should eventually include:

`local NALLY subprocess execution` vs `NALLY → NallPuter`.

## What the research changes

The prior art changes the target from:

“remote run_command”

to:

“isolated computer runtime with an agent-facing contract.”

That means the API, lifecycle, resource model, and security boundary all matter as much as command execution.

## What remains unresolved for Phase 2

- container implementation details
- exact runtime isolation mechanism
- exact Render resource ceiling
- default RAM/CPU/disk/PID quotas
- storage backing
- authentication mechanism
- egress proxy shape
- process recovery guarantees
- auto-stop policy
- snapshot scope
- multi-user ownership model
- Research note 1: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 2: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 3: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 4: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 5: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 6: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 7: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 8: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 9: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 10: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 11: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 12: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 13: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 14: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 15: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 16: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 17: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 18: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 19: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 20: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 21: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 22: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 23: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 24: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 25: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 26: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 27: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 28: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 29: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 30: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 31: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 32: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 33: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 34: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 35: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 36: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 37: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 38: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 39: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 40: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 41: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 42: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 43: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 44: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 45: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 46: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 47: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 48: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 49: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 50: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 51: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 52: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 53: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 54: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 55: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 56: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 57: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 58: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 59: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 60: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 61: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 62: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 63: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 64: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 65: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 66: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 67: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 68: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 69: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 70: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 71: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 72: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 73: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 74: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 75: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 76: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 77: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 78: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 79: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 80: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 81: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 82: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 83: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 84: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 85: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 86: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 87: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 88: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 89: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 90: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 91: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 92: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 93: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 94: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 95: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 96: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 97: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 98: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 99: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 100: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 101: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 102: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 103: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 104: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 105: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 106: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 107: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 108: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 109: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 110: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 111: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 112: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 113: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 114: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 115: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 116: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 117: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 118: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 119: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 120: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 121: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 122: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 123: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 124: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 125: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 126: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 127: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 128: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 129: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 130: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 131: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 132: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 133: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 134: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 135: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 136: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 137: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 138: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 139: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 140: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 141: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 142: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 143: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 144: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 145: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 146: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 147: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 148: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 149: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 150: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 151: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 152: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 153: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 154: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 155: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 156: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 157: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 158: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 159: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 160: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 161: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 162: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 163: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 164: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 165: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 166: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 167: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 168: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 169: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 170: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 171: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 172: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 173: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 174: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 175: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 176: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 177: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 178: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 179: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 180: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 181: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 182: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 183: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 184: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 185: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 186: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 187: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 188: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 189: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 190: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 191: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 192: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 193: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 194: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 195: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 196: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 197: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 198: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 199: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 200: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 201: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 202: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 203: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 204: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 205: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 206: requirements synthesis: retain evidence, label inference, and defer provider-specific choices to the formal Phase 2 decisions. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
