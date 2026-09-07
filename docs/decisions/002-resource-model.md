# NallPuter Decision 002 — Resource Model

**Status:** LOCKED
**Date:** 2026-09-06
**Review gate:** Post-Phase-1 synthesis review

## Decision

**Eight independent resource knobs with v0.1 defaults sized for Render private service (512 MB RAM baseline).** "Bigger NallPuter" = increasing one or more knobs; no new product architecture required.

## Resource knobs

| Knob | Env var | v0.1 Default | Unit | Enforcement | Notes |
|------|---------|--------------|------|-------------|-------|
| RAM | `NALLPUTER_RAM_MB` | 512 | MB | cgroup / container limit | Matches Render baseline; hard ceiling |
| CPU | `NALLPUTER_CPU_MILLICORES` | 500 | millicores | cgroup cpu.shares / quota | 0.5 core baseline; reservation + limit |
| Disk | `NALLPUTER_DISK_GB` | 2 | GB | persistent disk quota | Workspace + logs + temp; volume size |
| PIDs | `NALLPUTER_MAX_PIDS` | 100 | count | cgroup pids.max | Process tree ceiling per computer |
| Wall time | `NALLPUTER_WALL_TIME_SEC` | 300 | seconds | per-run timeout | Max single execution lifetime |
| Output | `NALLPUTER_MAX_OUTPUT_BYTES` | 100000 | bytes | per-run truncation | Observation cap returned to NALLY |
| Workspace | `NALLPUTER_WORKSPACE_GB` | 1 | GB | logical quota check | Subset of disk; user-visible quota |
| Network | `NALLPUTER_EGRESS_POLICY` | `deny-by-default` | policy | egress proxy / iptables | Allowlist only; no ambient net |

## Derived / composite limits

| Composite | Formula | v0.1 Value | Purpose |
|-----------|---------|------------|---------|
| Max concurrent runs | `min(CPU_MILLICORES/100, MAX_PIDS/10)` | 5 | Prevent fork bombs |
| Temp disk headroom | `DISK_GB - WORKSPACE_GB` | 1 GB | Logs, temp, package cache |
| Idle timeout | `NALLPUTER_IDLE_TIMEOUT_SEC` | 900 (15 min) | Auto-stop trigger |

## Enforcement model

- **Hard limits** (RAM, CPU, PIDs, Disk): enforced by container runtime (cgroups) — process cannot exceed
- **Policy limits** (Wall time, Output, Workspace, Network): enforced by NallPuter API/runtime — request rejected or terminated
- **Observability**: all knobs exposed via `GET /v1/computer/{id}` for NALLY to read current usage

## v0.1 implementation mapping (Docker on Render)

| Knob | Docker / Render mechanism |
|------|---------------------------|
| RAM | `--memory=512m --memory-swap=512m` |
| CPU | `--cpus=0.5` |
| Disk | Render persistent disk (2 GB) mounted at `/workspace` |
| PIDs | `--pids-limit=100` |
| Wall time | NallPuter runtime kills process tree at timeout |
| Output | NallPuter truncates stdout/stderr at 100 KB |
| Workspace | Application-level quota check on writes |
| Network | `--network=none` + explicit egress proxy (v0.1: allowlist only) |

## "Bigger NallPuter" scaling

Increasing any knob is a configuration change, not a new computer type:

```text
Small (default)     → 512 MB RAM, 0.5 CPU, 2 GB disk, 100 PIDs
Medium (dev)        → 2 GB RAM, 2 CPU, 10 GB disk, 500 PIDs
Large (build/CI)    → 8 GB RAM, 4 CPU, 50 GB disk, 2000 PIDs
XLarge (ML/train)   → 32 GB RAM, 8 CPU, 200 GB disk, 4000 PIDs + GPU (v0.3+)
```

Each tier is a preset bundle of the same eight knobs. Users can also set knobs individually.

## What this does NOT decide (deferred)

- Exact cgroup v1 vs v2 configuration
- Whether Render persistent disk or S3/volume plugin for workspace storage
- Network egress proxy implementation (sidecar, iptables, userspace proxy)
- CPU burst vs hard limit behavior
- Whether PIDs limit includes the container init process
- GPU resource knob (v0.3+)
- Bandwidth/connection rate limits under Network

## Evidence trace

- Manus: tiered plans (Basic/Standard/Advanced) as resource bundles
- OpenAI: hosted container with workspace, output caps, network policy
- Anthropic: OS-level resource controls as part of security boundary
- OpenHands: Docker runtime with resource constraints
- E2B/Daytona/Modal: per-second resource pricing, independent CPU/RAM/disk config
- NallPuter requirements.md: Resource model table, "Bigger NallPuter" concept

## Addendum — 2026-09-07 (Decisions 003/004)

The 8 knobs remain the scaling mechanism (“Bigger NallPuter” = bump knobs, no new product), but they are now **fields of `MachineProfile.resources`** (Decision 003), not the profile itself. The Docker/Render mapping table is the **Lab Rat #1 implementation** of those fields; the canonical persistence backing is `external_canonical` (Decision 004) and the Render Disk is accessed only via the sync-engine abstraction (not as “the computer is the disk”). `Disk` vs `Workspace` quota is enforced at sync time (`507 workspace_quota_exceeded`) as well as at write time. `Network` remains policy-contract-only here; enforcement choice (sidecar vs iptables vs userspace) is Phase 4.

## Review gate outcome

Synchronous review completed. Decision locked 2026-09-06; addendum locked 2026-09-07. Proceed to Phase 2a/2b (Machine Contract + Persistent State) → Phase 3 (Machine & Execution API Contract).