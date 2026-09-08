# NallPuter Phase 1 Synthesis â€” Requirements

> Purpose: translate prior-art research into candidate requirements for the NallPuter architecture. This document is a synthesis, not an implementation specification.

## Evidence discipline

- A requirement is a NallPuter design inference unless explicitly marked otherwise.
- Vendor claims are not treated as proof that the same implementation is suitable for NallPuter.
- Third-party observations inform interface design but do not become product guarantees.
- Any unresolved item remains an architecture decision for Phase 2â€“6.

## Mission

NallPuter is the computer/runtime for NALLY.

NALLY is the brain/orchestrator.

NallPuter is the isolated environment that owns execution, workspace state, processes, resource limits, lifecycle, and runtime enforcement.

The first interface is `NALLY â†’ authenticated API â†’ NallPuter`.

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

## Pillar 1 â€” Isolation

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

## Pillar 2 â€” Lifecycle

### Computer lifecycle

Candidate state model:

`creating â†’ running â†’ idle â†’ stopping â†’ stopped â†’ starting â†’ running`

Failure path:

`running â†’ error â†’ recovering â†’ running | stopped | destroyed`

Future VM path:

`running â†’ pausing â†’ paused â†’ resuming â†’ running`

### Run lifecycle

Candidate state model:

`queued â†’ running â†’ succeeded`

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

## Pillar 3 â€” Workspace

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

â€œBigger NallPuterâ€ means increasing one or more of these knobs; it does not require a new product architecture.

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

`NALLY decision â†’ authenticated request â†’ NallPuter policy engine â†’ OS/runtime enforcement â†’ execution`

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

`local NALLY subprocess execution` vs `NALLY â†’ NallPuter`.

## What the research changes

The prior art changes the target from:

â€œremote run_commandâ€

to:

â€œisolated computer runtime with an agent-facing contract.â€

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
