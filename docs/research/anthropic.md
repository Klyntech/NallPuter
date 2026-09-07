# Anthropic — Claude Code Sandbox Research

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

- **Anthropic Engineering — Beyond permission prompts: making Claude Code more secure and autonomous with sandboxing**
  https://www.anthropic.com/engineering/claude-code-sandboxing
- **Anthropic Engineering — How we contain Claude**
  https://www.anthropic.com/engineering/how-we-contain-claude

- Research note 1: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 2: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 3: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 4: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 5: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 6: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 7: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 8: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 9: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 10: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 11: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 12: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 13: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 14: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 15: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 16: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 17: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 18: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 19: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 20: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 21: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 22: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 23: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 24: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 25: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 26: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 27: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 28: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 29: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 30: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 31: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 32: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 33: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 34: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 35: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 36: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 37: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 38: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 39: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 40: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 41: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 42: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 43: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 44: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 45: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 46: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 47: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 48: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 49: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 50: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 51: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 52: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 53: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 54: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 55: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 56: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 57: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 58: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 59: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 60: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 61: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 62: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 63: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 64: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 65: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 66: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 67: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 68: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 69: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 70: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 71: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 72: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 73: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 74: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 75: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 76: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 77: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 78: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 79: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 80: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 81: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 82: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 83: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 84: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 85: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 86: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 87: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 88: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 89: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 90: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 91: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 92: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 93: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 94: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 95: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 96: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 97: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 98: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 99: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 100: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 101: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 102: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 103: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 104: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 105: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 106: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 107: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 108: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 109: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 110: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 111: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 112: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 113: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 114: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 115: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 116: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 117: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 118: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 119: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 120: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 121: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 122: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 123: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 124: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 125: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 126: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 127: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 128: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 129: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 130: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 131: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 132: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 133: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 134: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 135: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 136: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 137: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 138: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 139: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 140: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 141: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 142: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 143: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 144: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 145: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 146: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 147: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 148: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 149: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 150: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 151: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 152: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 153: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 154: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 155: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 156: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 157: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 158: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 159: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 160: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 161: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 162: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 163: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 164: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 165: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 166: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 167: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 168: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 169: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 170: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 171: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 172: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 173: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 174: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 175: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 176: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 177: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 178: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 179: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 180: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 181: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 182: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 183: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 184: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 185: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 186: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 187: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 188: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 189: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 190: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 191: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 192: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 193: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 194: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 195: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 196: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 197: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 198: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 199: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 200: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 201: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 202: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 203: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 204: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 205: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 206: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 207: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 208: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 209: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 210: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 211: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 212: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 213: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 214: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 215: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 216: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 217: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 218: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 219: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 220: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 221: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 222: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 223: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 224: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 225: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 226: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 227: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 228: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 229: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 230: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 231: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 232: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 233: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 234: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 235: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 236: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 237: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 238: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 239: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 240: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 241: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 242: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 243: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 244: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 245: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 246: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 247: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 248: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 249: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 250: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 251: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 252: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 253: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 254: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 255: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 256: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 257: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 258: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 259: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 260: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 261: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 262: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 263: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 264: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 265: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 266: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 267: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 268: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 269: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 270: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 271: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 272: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 273: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 274: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 275: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 276: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 277: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 278: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 279: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 280: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 281: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 282: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 283: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 284: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 285: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 286: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 287: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 288: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 289: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 290: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 291: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 292: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 293: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 294: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 295: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 296: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 297: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 298: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 299: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 300: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 301: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 302: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 303: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 304: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 305: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 306: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 307: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 308: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 309: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 310: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 311: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 312: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 313: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 314: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 315: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 316: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 317: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 318: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 319: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 320: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 321: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 322: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 323: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 324: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 325: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 326: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 327: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 328: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 329: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 330: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 331: Anthropic — Claude Code Sandbox Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
