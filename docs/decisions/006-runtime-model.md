# NallPuter Decision 006 — Runtime Model (Process, Resource, and Isolation Implementation)

**Status:** LOCKED
**Date:** 2026-09-07
**Review gate:** Phase 4 — concrete models
**Depends on:** `002-resource-model.md` (8 knobs), `003-machine-contract.md` (MachineProfile), `004-persistent-state.md` (disposable runtime), `005-workspace-model.md` (layout/quotas)
**Blocks:** Phase 6 MVP (`nallputer/`), Phase 7 Evaluation

---

## Decision

**cgroup v2 unified hierarchy for all hard limits, `tini` as PID 1, per-run process groups for tree-kill, and application-layer wall-time/output enforcement.**

NallPuter’s runtime is a single Linux container (Lab Rat: Docker on Render) with explicit hard-limit flags and in-container runtime daemons. Every `POST /v1/exec` spawns a process group that inherits the container’s cgroup, is bounded by wall-time and output caps, and is killed atomically on timeout/cancel. Orphans are reaped by the init.

---

## 1. cgroup v2 (locked)

| Choice | Locked | Rationale |
|--------|--------|-----------|
| **cgroup v2 unified hierarchy** | ✅ Locked | Modern kernels (≥5.4) and Docker Engine ≥20.10 default to v2 when host supports it. Render’s current fleet is on v2-compatible hosts. v2 gives one unified tree, `pids.max` + `memory.max` + `cpu.max` under `cpu.weight`, and correct `io.max`/`memory.swap.max` semantics. v1 is legacy/compat only. |
| cgroup v1 | Rejected | Hybrid v1 (`memory`, `cpu`, `pids` as separate controllers) is maintenance burden; E2B/Daytona/Modal all document unified reservations. |
| Fallback | Detection at boot: if `/sys/fs/cgroup/cgroup.controllers` missing → refuse to start with `recovering` + `last_error: cgroup_v2_required` and emit `GET /v1/health → 503`. No silent v1 fallback — v1 flag mappings differ enough to break quota auditing. |

**Enforcement is at the cgroup, not advisory.** The API can lie; the kernel cannot.

---

## 2. Docker / container configuration (Lab Rat #1)

Base image is a **policy decision**, not just convenience. The same image tag is recorded in `environment.yaml` (`base.image`) for replay portability (004).

```dockerfile
# Dockerfile — illustrative (MVP may pin digest)
FROM python:3.12-slim-bookworm

# Init
RUN apt-get update && apt-get install -y --no-install-recommends tini curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["/usr/bin/tini", "--"]

# Workspace
RUN useradd -m -u 1000 nally && mkdir -p /home/nally/workspace /workspace \
 && chown -R nally:nally /home/nally /workspace
USER nally
WORKDIR /home/nally/workspace/projects

# Env
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_INPUT=1 \
    HOME=/home/nally

EXPOSE 8000
CMD ["uvicorn", "nallputer.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Run flags (mapped from `MachineProfile.resources`, bounds in 002):**

| Knob | Lab Rat flag (cgroup v2) | Default | Notes |
|------|--------------------------|---------|-------|
| RAM | `--memory=512m --memory-swap=512m` (== no swap) | 512 MB | `memory.max=512M`, `memory.swap.max=0` under v2 |
| CPU | `--cpus=0.5` (`cpu.max="50000 100000"` → 0.5 core) | 500m | `cpu.weight` + `cpu.max`; no `--cpu-shares` (v1). |
| Disk | Render Persistent Disk 2 GB mounted at `/mnt/nallputer-cache` **and** canonical abstraction (004) | 2 GB | Not `--storage-opt`; quota is at sync + `workspace_gb` policy layer (005). |
| PIDs | `--pids-limit=100` | 100 | `pids.max=100` — includes NALLPUTER server + sync watcher + exec trees. |
| Network | `--network` left to Render; **no** `--privileged` / `--cap-add=NET_ADMIN` | — | Egress is enforced via egress proxy + API policy (007), not iptables (see § 4). |
| Init | `ENTRYPOINT ["/usr/bin/tini","--"]`, `STOPSIGNAL SIGTERM` | — | PID 1 reaps zombies; handles SIGTERM → flush (004). |
| Security | `--read-only` rootfs if feasible + tmpfs at `/tmp`, `--cap-drop=ALL` + `--cap-add=CHOWN,DAC_OVERRIDE,FOWNER` minimal, `--security-opt=no-new-privileges:true` | — | App writes only to `/home/nally/workspace` + `/tmp`. Evaluate in MVP; if Render requires writable rootfs, keep rootfs writable but keep cap-drop. |

**Render specifics:** No Docker-in-Docker, no `--privileged`. Private networking only; no public ingress to NALLPUTER. `STOPSIGNAL SIGTERM` + 10s graceful window honored by Render → triggers sync flush (004).

---

## 3. Process model — runs as process groups

Each `POST /v1/exec` creates exactly one **run** with a stable `run_id`. Implementation:

```
NALLPUTER (PID 1: tini → uvicorn)
  ├─ sync engine (watcher)
  └─ run_id=run_abc (pgid=run_abc)
       └─ bash -c "<command>"   (setsid / new process group)
            ├─ child …
            └─ grandchild …
```

| Rule | Normative |
|------|-----------|
| **Stable identity** | `run_id` is returned immediately (201) and is the only handle for `GET /exec/{id}` / `DELETE /exec/{id}`. `run_id` ≠ `computer_id`. |
| **Process-group kill** | `DELETE /v1/exec/{run_id}` and timeout paths send `SIGTERM` to `-pgid`, wait `5s`, then `SIGKILL` to `-pgid`. Orphans outside the pgid are caught by reaping. |
| **Inheritance** | Children inherit the container cgroup, `pids.max`, `memory.max`, `cpu.max`, and the scrubbed env (007). No escalation path. |
| **Orphan reaping** | `tini --` as PID 1 reaps zombies at `waitpid` rate. NALLPUTER additionally on `GET /v1/computer/{id}` reports `resources_usage.pids_used`; sweeper kills runs in `running` whose pgid no longer exists but were not transitioned → marks `failed` with `last_error: orphan_reaped`. |
| **Max concurrent runs** | `min(cpu_millicores/100, pids/10)` (derived in 002) → default 5. Admission control: `POST /v1/exec` when at cap → `429 Too Many Requests` with `code: concurrency_limited`. Prevents fork bombs without tuning pids per provider. |

---

## 4. Resource enforcement — split hard vs policy (locked with 002)

| Class | Knobs | Enforced by | On violation |
|-------|-------|-------------|--------------|
| **Hard (kernel)** | `RAM`, `CPU`, `PIDs`, `Disk` | cgroup `memory.max`, `cpu.max`/`cpu.weight`, `pids.max` + container disk | OOMKilled / throttle / `fork: Resource temporarily unavailable` — surfaced as `status: failed` + `error.code: oom_killed|pids_exhausted` |
| **Policy (NALLPUTER)** | `Wall time`, `Output`, `Workspace`, `Network` | API/runtime timers, truncators, quota checks, egress proxy+policy | Before spawn (policy_denied) or during (timed_out/cancelled/truncated/507) |

**Wall time:** Per-run timer (`MachineProfile.resources.wall_time_sec` default 300s, overridable per-run down-only). On expiry: `SIGTERM` to pgid → grace 5s → `SIGKILL` → `status: timed_out`. Distinct from `cancelled` (explicit delete) so NALLY can distinguish automation vs user intent.

**Output:** `max_output_bytes` (100 KB) is a per-run observation cap. Stdout+stderr are captured to bounded buffers; on overflow `truncated: true`, slice returned via `?cursor=&limit=` pagination. Original total `bytes` is still reported. TTL 24h then `410 Gone`. This is a context-control, not a workspace quota.

**Concurrency + PIDs:** Admission check uses live `resources_usage.pids_used` from cgroup `pids.current`. This prevents a single `exec` that forks wildly from starving the API server itself.

---

## 5. What was deferred to here is now locked

| Earlier deferred | Decision |
|------------------|----------|
| cgroup v1 vs v2 | **v2 unified** (above). |
| `--pids-limit` includes init? | Yes — `pids.max=100` includes init + server. Admission math accounts for it (~5 headroom). `pids.current` is what we report. |
| CPU burst vs hard limit | `cpu.max` is a **hard ceiling** (`0.5` means 50 ms per 100 ms period, not burst). No `--cpu-shares` soft reservation in v0.1; fairness is via `cpu.weight` proportional only if multiple cgroups contend (single-computer v0.1: weight is a no-op). Burst knob deferred to v0.2+. |
| Bandwidth / connection rate | Deferred to Security model (007) — quota is not a policy limit in v0.1; egress `allowlist` + `concurrency` are the controls. |

---

## 6. Local dev equivalence

`docker run` with identical flags must be used for local `http://localhost:8000` NALLPUTER so NALLY integration tests against the same kernel enforcement. The only difference is `provider: local` vs `render` in `GET /v1/machine` — NALLY must not branch on it.

---

## Evidence trace

- Anthropic: cgroup/process inheritance, PID controls, memory enforcement at runtime layer.
- OpenAI/E2B/Modal: per-second resource pricing, independent CPU/RAM/disk knobs → validates split of 8 knobs.
- Manus: tiered plans as resource bundles → validates preset bundles (002 scaling section).

---

## Review gate outcome

Locked 2026-09-07. Implements the runtime/isolation half of Phase 4. Egress enforcement specifics in 007, lifecycle transitions in 008.
