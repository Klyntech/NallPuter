# Anthropic â€” Claude Code Sandbox Research

> Phase 1 research document for NallPuter. Facts, observations, and NallPuter inferences are deliberately separated.

## Evidence discipline

- **Documented fact:** directly stated by the cited primary or vendor source.
- **Third-party observation:** interpretation, benchmark, implementation note, or repository documentation that is not itself a vendor product promise.
- **NallPuter inference:** a design conclusion proposed for NallPuter; it is not a claim about the researched system.

## Executive summary

Anthropic's sandboxing work is the strongest security reference for NallPuter. The central idea is that filesystem and network boundaries must be enforced below the model, using OS-level mechanisms, and inherited by subprocesses. This research also exposes an important scope trap: securing Bash alone does not automatically secure every in-process file or code operation.

## Documented facts

- Anthropic describes two sandbox boundaries: filesystem isolation and network isolation.
- Linux uses bubblewrap and macOS uses Seatbelt as OS-level enforcement mechanisms in Claude Code.
- Sandboxed Bash and the subprocesses it launches inherit the sandbox restrictions.
- The documented filesystem policy allows work inside the workspace while blocking writes outside it.
- Network access is denied by default in the described sandbox and can be routed through a proxy with an allowlist.
- Anthropic describes environment scrubbing and credential-handling measures.
- Anthropic states that sandboxing substantially reduced permission prompts in internal usage.
- Anthropic also documents a known gap in which some non-Bash file operations can run outside the Bash sandbox in certain versions.

## Third-party / implementation observations

- Security is treated as a runtime boundary rather than a prompt convention.
- Child-process inheritance matters because shell commands routinely launch other programs.
- Network policy is materially different from filesystem policy; both need explicit enforcement.
- Credential exposure is a distinct problem from filesystem access.
- The documented gap is useful because it demonstrates that a secure shell boundary does not automatically protect all execution paths.

## NallPuter inferences

- NallPuter must enforce filesystem and network controls at the runtime boundary.
- Every process spawned by a run must inherit the relevant restrictions.
- Environment inheritance should be treated as a security decision, not a default.
- File operations must use the same policy model as command execution; the sandbox cannot protect Bash while leaving file APIs unrestricted.
- NallPuter should maintain a narrow internal capability surface and audit privileged operations.

## Resource model

- **Filesystem:** workspace write boundary plus explicit read policy.
- **Network:** deny-by-default with an egress policy.
- **Processes:** child inheritance and PID/resource controls.
- **Credentials:** environment scrub and scoped injection.
- **CPU/RAM:** OS/runtime enforcement, not application-level advisory checks.
- **Disk:** workspace quota and artifact quota.

## Lifecycle model

- Security state should attach to a computer/workspace and be inherited by run processes.
- Cancellation must stop the process tree, not only the parent process.
- Recovery must account for orphaned processes and stale runtime state.
- Security policy changes should be auditable and should not silently broaden access.

## Security boundary

- NallPuter should make the runtime its second independent policy enforcement point after NALLY's preflight policy.
- Secrets should ideally be injected only for an explicitly permitted destination or operation.
- The sandbox should not inherit NALLY's broad host environment.
- Public-facing NallPuter administration and agent-facing execution paths should be separate.

## Pricing / infrastructure cost signals

- OS-level isolation can reduce the need for repeated user approval prompts, but it does not eliminate the need for auditability.
- Proxying egress can make domain policy measurable and enforceable.
- Resource controls are part of the same defense-in-depth story as filesystem and network controls.

## What to copy

- Dual filesystem + network boundary.
- Child-process inheritance.
- Credential scrubbing.
- Security at the runtime layer.
- Explicit audit of policy exceptions.

## What to avoid

- Bash-only isolation.
- Prompt-only permission controls.
- Implicitly inheriting all host credentials.
- Assuming application-level path checks are equivalent to an OS boundary.

## Open questions for NallPuter

- Which Linux isolation mechanism will NallPuter use in v0.1?
- How will file APIs and shell APIs share the same policy decision?
- How should scoped network credentials be represented in the API?
- What exact evidence proves that a child process inherited the sandbox?

## Sources

- **Anthropic Engineering â€” Beyond permission prompts: making Claude Code more secure and autonomous with sandboxing**
  https://www.anthropic.com/engineering/claude-code-sandboxing
- **Anthropic Engineering â€” How we contain Claude**
  https://www.anthropic.com/engineering/how-we-contain-claude

