# NallPuter Decision 007 — Security Model (Filesystem, Network, Credential, and Audit Boundaries)

**Status:** LOCKED
**Date:** 2026-09-07
**Review gate:** Phase 4 — concrete models
**Depends on:** `003-machine-contract.md` (auth + `MachineProfile.capabilities.egress_policy`), `004-persistent-state.md` (canonical store trust boundary), `005-workspace-model.md` (jail + quota), `006-runtime-model.md` (cgroup v2 + process groups)
**Blocks:** Phase 6 MVP (NALLPUTER policy engine + egress proxy + credential handling)

---

## Decision

**Security is enforced below the agent, at the runtime boundary, in two orthogonal gates: filesystem and network. Credentials never become ambient files, and every privileged or denied operation is auditable without logging secrets.**

Enforcement flow (non-bypassable):

```
NALLY intent
  ↓
Authenticated request (Bearer, constant-time, private network)
  ↓
NallPuter policy engine (workspace jail + egress allowlist + credential rules + quota + PID/wall-time)
  ↓  policy_denied → no process spawned, structured error + audit event
OS/runtime enforcement (cgroup v2 limits, process-group isolation, jail, proxy)
  ↓
Execution (observed, bounded, paginated)
```

Anthropic’s central lesson: `Security below the agent` — a prompt or permission flag may not silently widen the boundary. The policy engine and the OS enforcement are **independent**; neither may weaken the other.

---

## 1. Filesystem boundary

| Property | Normative |
|----------|-----------|
| **Root jail** | All FS ops (`POST /v1/files/{read,write,list}` + `POST /v1/exec.cwd`) are resolved against a single workspace root (`/home/nally/workspace`) via `realpath` + `O_NOFOLLOW` + prefix check. `..` traversal, absolute paths outside root, and symlink-follow-then-escape are rejected **before** any mutation with `403` + `code: filesystem_denied`. |
| **Single policy object** | File APIs and shell APIs share one resolver and one policy module (Anthropic gap fix). There is no “Bash is jailed but `files/write` is not” path. |
| **External volumes privileged** | Anything that would mount outside the workspace root (volumes, extra persistent disks) is a privileged configuration, not an agent action. Agent cannot create mounts. |
| **Atomic writes** | `files/write` is atomic at canonical layer (`*.tmp` + rename) plus `If-Match` on `manifest.json` at sync (004). Torn manifests are not committed; old manifest remains the consistent view. |
| **Operation metadata vs content** | `list` never returns content; `read` is bounded (100 KB per page) and requires `offset`/`limit` for large files. Prevents whole-project dump amplification (SWE-agent ACI). |

**Deny set (v0.1):** Writes outside workspace root, writes to `/etc`, `/proc`, `/sys`, `/root`, `/home/nally/.ssh` (credential isolation), and any `NALLPUTER_*` internal state except via explicit sync. Reads outside workspace are denied except for a tiny allowlist needed for toolchain introspection (e.g., `/etc/os-release` via shell is allowed — direct file API read outside root is still denied).

---

## 2. Network boundary — userspace egress proxy (locked)

### Choice (settles deferred decision in 003)

| Option | Verdict | Reason |
|--------|---------|--------|
| **iptables / nftables with NET_ADMIN** | Rejected for v0.1 | Requires `--privileged` / `--cap-add=NET_ADMIN`. Render does not grant this on private services; even if it did, it couples enforcement to host capabilities and is not portable to other providers. |
| Sidecar container per computer | Rejected for v0.1 | Cost/complexity linear in computers; Render model is one container per service, not a pod with sidecars. Adds interconnect policy of its own. |
| **Userspace forward proxy (in-container) + HTTP_PROXY injection + deny-by-default API policy** | **Locked for v0.1** | Works with no privileged caps, is provider-portable, is fully auditable, and covers the important allowlist case (`pip`, `npm`, `apt`, `curl` to approved destinations). |

### How it works (normative)

1. **Default is deny.** `MachineProfile.capabilities.egress_policy == "deny-by-default"` until an explicit allowlist exists. With an empty allowlist, only Render private-network traffic to the canonical store (and DNS for that store if needed) is permitted — all agent-initiated egress is `policy_denied`.
2. **Forward proxy process:** `nallputer-egress-proxy` (tiny Go or `tinyproxy`-based forward proxy, ~5 MB) listens on `127.0.0.1:3128` inside the same container. It holds the allowlist (see below) and logs `{run_id, dst_host, dst_port, decision, reason}` — never request/response bodies or credential values.
3. **Injection, not advisory:** On every `POST /v1/exec`, NALLPUTER injects `HTTP_PROXY=http://127.0.0.1:3128`, `HTTPS_PROXY=http://127.0.0.1:3128`, `http_proxy/…`, `NO_PROXY=127.0.0.1,localhost,169.254.169.254,nallputer.internal` into the spawned process group’s env (scoped overlay, not host inheritance). `NO_PROXY` ensures liveness/health and private-network store fetches bypass the proxy when appropriate.
4. **Non-HTTP egress:** The proxy handles HTTP(S) (covers `pip`/`npm`/`apt`/`curl`/`git https` — 95% of agent egress). Raw TCP/UDP outside HTTP (e.g., `nc`, custom binary) that bypasses `HTTP_PROXY` is caught by **API-layer preflight**: if `command` parsing or an out-of-band connect is attempted to a non-allowlisted host:port, policy denies before spawn. In v0.1 this is best-effort allowlist matching on the command’s literal hosts + a post-exec audit warning `policy_result: egress_bypass_attempted`. Full per-process `connect` syscall interposition (eBPF/Seatbelt/bubblewrap `--unshare-net`) is deferred to v0.2 VM path (Firecracker/Kata).
5. **Allowlist shape (config, not agent-writable):**

```yaml
# NALLPUTER_EGRESS_ALLOWLIST — operator config, loaded at boot, hash in machine.json
allowlist:
  - host: "pypi.org"        # exact or suffix "*.pypi.org"
    ports: [443]
    reason: "python packages"
  - host: "registry.npmjs.org"
    ports: [443]
  - host: "github.com"
    ports: [443]
  - host: "*.render.com"
    ports: [443]
  deny: "*"                  # default — everything else denied
```

`*` host rules are rejected at config load — deny-by-default is not combinable with a wildcard allow.

6. **DNS:** Proxy does DNS; allowlist is checked on the requested host string, not just resolved IP — prevents DNS-rebinding style bypass. DNS for non-allowlisted hosts still resolves but proxy returns `403` before connecting.
7. **Audit:** Every proxy decision → append-only audit line `{ts, computer_id, run_id, src_pgid, dst_host, dst_port, decision: allow|deny, reason, allowlist_rev}` — exposed read-only via operator logs, never via agent API bodies.

**Future path:** v0.2 VM with its own netns can add `nftables` deny-by-default + proxy pass-through for complete TCP coverage while keeping the same allowlist language. API does not change; `capabilities.egress_policy` stays `deny-by-default` and `MachineProfile` just reports a tighter enforcement.

---

## 3. Credential isolation

| Property | Normative |
|----------|-----------|
| **No ambient inheritance** | NALLPUTER does not inherit NALLY’s broad env. Base env is minimal (`PATH`, `HOME`, `WORKSPACE`, proxy vars). Extra vars for a run come only from the per-request `ExecCreate.env` overlay (003) and are scrubbed. |
| **Scrub rules** | On every exec, the policy engine strips `AWS_*`, `GCP_*`, `AZURE_*`, `RENDER_*`, `*_TOKEN`, `*_SECRET`, `SSH_AUTH_SOCK`, etc., unless the key is in an explicit `NALLPUTER_ALLOWED_ENV` list. Silently inheriting `.ssh` or cloud creds is a violation. |
| **Scoped injection** | Secrets needed for egress (e.g., private PyPI token, GitHub token for allowlisted host) are injected **only** for `dst_host` matches in the allowlist and only for that run’s pgid. They are not written to `environment.yaml` or the canonical store (004). |
| **No secret persistence** | `environment.yaml` / `environment.lock` and the canonical `workspace/` must never contain token values. Reconciler rejects specs that contain `token`, `secret`, `password` literals with `policy_denied: credential_in_spec`. |
| **SSH / host creds** | `/home/nally/.ssh` does not exist by default. Creating it via `files/write` is denied; only `ExecCreate.env` scoped injection can provide `GIT_SSH_COMMAND` material ephemerally per run. |

**Observability without leakage:** Audit events record `{key_name, destination_host}` but never the value (e.g., `injected: GITHUB_TOKEN → github.com:443` without value).

---

## 4. Process & resource isolation (binds to 006)

All runs inherit the container’s cgroup v2 limits (`memory.max`, `cpu.max`, `pids.max`). Children cannot escape the cgroup; PID ceiling is per-computer. Wall-time and output caps are enforced by NALLPUTER timers/truncators before the kernel would need to intervene. Orphans are reaped by `tini` (006 § 3).

---

## 5. Trust split and audit

| Principle | Enforced by |
|-----------|-------------|
| `NALLY decision → NallPuter policy → OS enforcement` | NALLY may call anything; NALLPUTER decides `allow|deny` before `fork`; kernel decision is final. Neither layer may silently widen the other. |
| Denied-before-spawn | Any `policy_denied` (FS escape, egress not in allowlist, quota, credential-in-spec, concurrency cap) stops before `fork` and returns `status: policy_denied` with `policy_result` + audit event. |
| **Audit** | Append-only, operator-visible: `{ts, computer_id, run_id, decision, reason, policy_rev, allowlist_rev, egress{dst}, fs{path}, quota{used}}`. No secrets, no full file content, no proxy bodies. `GET /v1/computer/{id}/sync` and `GET /v1/health` may surface summary counters but not raw audit log (agent API is not the audit channel). |
| **Public vs agent paths** | NALLPUTER has no public ingress (Render private networking). Operator-owned bridge from NALLY (public service) to NALLPUTER (private service) is the only entry point. A compromised agent credential cannot directly reach the host — only through the authenticated API. |

---

## 6. What this does NOT decide (deferred)

- eBPF/syscall-interposition for raw-TCP egress capture — v0.2 VM path (007 § 2 handles HTTP(S) sufficiently for v0.1).
- PIDs includes-init accounting for `pids.max` — already locked in 006 (yes, includes init).
- GPU isolation — v0.3+.

---

## Evidence trace

- Anthropic: bubblewrap/Seatbelt, dual FS+net gates, child inheritance, credential scrub, gap that file ops must equal shell (fixed here with single resolver).
- Manus/OpenAI: isolated environment whose network policy is not the same as FS policy — motivates deny-by-default + allowlist.
- E2B/Daytona/Modal: explicit lifecycle vs policy — motivates auditable allowlist + single-writer per computer.
- OpenHands/SWE-agent: narrow capability surface, structured observations — motivates no raw TTY / no full file dump.

---

## Review gate outcome

Locked 2026-09-07. Implements the security/isolation half of Phase 4. Lifecycle transitions, auto-stop, and recovery semantics in 008.
