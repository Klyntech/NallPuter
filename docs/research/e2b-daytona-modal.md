# E2B + Daytona + Modal â€” Sandbox, Persistence, and Lifecycle Research

> Phase 1 research document for NallPuter. Facts, observations, and NallPuter inferences are deliberately separated.

## Evidence discipline

- **Documented fact:** directly stated by the cited primary or vendor source.
- **Third-party observation:** interpretation, benchmark, implementation note, or repository documentation that is not itself a vendor product promise.
- **NallPuter inference:** a design conclusion proposed for NallPuter; it is not a claim about the researched system.

## Executive summary

E2B, Daytona, and Modal provide the strongest comparative evidence for lifecycle and resource design. The most important finding is that filesystem persistence, process/memory persistence, and external storage are different capabilities. Daytona makes this separation especially explicit; E2B makes pause/resume and sandbox identity first-class; Modal demonstrates detailed execution/resource controls and filesystem or memory snapshot capabilities.

## Documented facts

- E2B documents sandboxes as isolated Linux environments supporting files, commands, code, and internet access.
- E2B exposes sandbox identity, connection, timeout, and kill operations.
- E2B documents beta pause and reconnect semantics.
- E2B pricing separates a plan fee from usage costs and publishes resource-based usage rates.
- Daytona documents filesystem persistence across stop/start for persistent sandboxes.
- Daytona distinguishes filesystem persistence from memory persistence.
- Daytona documents pause/resume for VM sandboxes to preserve memory and running processes.
- Daytona documents snapshots and volumes as separate persistence mechanisms.
- Daytona documents auto-stop, auto-pause, auto-archive, and auto-delete lifecycle controls.
- Modal documents configurable CPU and memory reservations/limits.
- Modal documents sandbox timeouts, idle timeouts, volumes, region placement, proxies, and snapshot functionality.

## Third-party / implementation observations

- The most useful shared abstraction is a sandbox/computer identity with explicit lifecycle state.
- Persistent storage should not be conflated with RAM state.
- Auto-stop and auto-pause are economic controls as much as technical controls.
- Resource limits are best represented as independent knobs so different workloads can be composed.
- Snapshotting creates a boundary between a live computer and a reusable point-in-time image.

## NallPuter inferences

- NallPuter v0.1 should persist filesystem/workspace state but should not promise RAM/process survival across stop/start.
- The API should reserve a place for pause/resume semantics even if containers are used initially.
- A computer ID should outlive an individual command.
- Resource knobs should be explicit: RAM, CPU, disk, PIDs, wall time, output bytes, workspace quota, network/egress.
- Lifecycle should distinguish stop, destroy, recover, and later pause/resume.

## Resource model

- **RAM:** configurable hard limit when runtime supports it.
- **CPU:** reservation and/or hard ceiling.
- **Disk:** persistent workspace quota.
- **PIDs:** process-count ceiling.
- **Wall time:** maximum run lifetime.
- **Output bytes:** per-run observation cap.
- **Workspace:** total disk/file quota.
- **Network:** egress policy and possibly bandwidth/connection ceilings.

## Lifecycle model

- Candidate states: `creating â†’ running â†’ idle â†’ stopping â†’ stopped â†’ starting â†’ running`.
- Error states should be recoverable where possible.
- A later VM implementation may add `paused â†’ resuming` while preserving the same computer identity.
- Snapshot operations should be explicit and should not be confused with ordinary filesystem persistence.
- Auto-stop/pause policy should be configured independently from task cancellation.

## Security boundary

- Sandboxes are expected to be isolated from the host and from other sandboxes.
- Network access can be separately controlled from compute isolation.
- Volumes and snapshots change the persistence trust boundary and must be included in security review.
- NallPuter should treat external storage mounts as privileged configuration rather than ordinary agent actions.

## Pricing / infrastructure cost signals

- E2B publishes per-second resource pricing and plan tiers.
- Daytona explicitly documents retention/lifecycle states that have different resource consequences.
- Modal exposes resource configuration directly as part of sandbox creation.
- NallPuter should measure both active compute cost and retained storage cost in Phase 9.

## What to copy

- Separate filesystem persistence from memory persistence.
- Explicit lifecycle state machine.
- Resource knobs as independent controls.
- Auto-stop/auto-pause as policy.
- Snapshot/restore as a future capability.

## What to avoid

- Pretending container stop/start preserves running processes.
- Mixing snapshot state with ordinary workspace persistence.
- Hiding idle-cost behavior behind a vague 'persistent' label.
- Adding GPU/browser complexity to v0.1.

## Open questions for NallPuter

- Which resource knobs are enforceable on the chosen Render runtime?
- What storage mechanism should back the persistent workspace?
- What is the minimum viable recovery behavior for v0.1?
- What conditions trigger auto-stop versus retaining the computer?

## Sources

- **E2B Docs â€” Sandbox**
  https://e2b.dev/docs/sdk-reference/js-sdk/v2.10.5/sandbox
- **E2B Pricing**
  https://e2b.dev/pricing
- **Daytona Docs â€” Persistence**
  https://www.daytona.io/docs/en/persistence/
- **Daytona Docs â€” Sandboxes**
  https://www.daytona.io/docs/sandboxes
- **Modal Docs â€” Sandbox**
  https://modal.com/docs/sdk/js/latest/Sandbox
- **Modal Docs â€” Sandbox V2**
  https://modal.com/docs/guide/sandbox-v2

