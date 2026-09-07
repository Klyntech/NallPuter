# OpenHands + SWE-agent — Agent–Computer Interface Research

> Phase 1 research document for NallPuter. Facts, observations, and NallPuter inferences are deliberately separated.

## Evidence discipline

- **Documented fact:** directly stated by the cited primary or vendor source.
- **Third-party observation:** interpretation, benchmark, implementation note, or repository documentation that is not itself a vendor product promise.
- **NallPuter inference:** a design conclusion proposed for NallPuter; it is not a claim about the researched system.

## Executive summary

OpenHands provides a concrete client-server runtime pattern: the backend communicates with an ActionExecutor inside a Docker container over REST. SWE-agent complements that architecture with the Agent–Computer Interface idea: the interface itself is a performance-critical part of an agent system. NallPuter should therefore be both an isolated runtime and a carefully designed observation/action interface.

## Documented facts

- OpenHands documents a client-server runtime implemented with Docker containers.
- The runtime initializes an action execution server inside the container.
- The backend sends actions and receives observations through a REST interface.
- OpenHands runtime actions include shell, file operations, Python, browser, and plugins.
- SWE-agent defines an Agent–Computer Interface as the tools and interaction format between an agent and a computer environment.
- SWE-agent documents a structured file viewer and targeted search behavior.
- SWE-agent documents an edit gate that rejects syntactically invalid changes.
- SWE-agent documents explicit handling for commands that produce empty output.

## Third-party / implementation observations

- Docker provides a practical separation between the agent-facing service and the runtime environment.
- A carefully designed ACI can reduce the amount of irrelevant context returned to the model.
- Line-oriented or bounded file views can make code navigation more efficient than raw full-file dumps.
- The runtime should return observations in a stable format so the agent does not need provider-specific parsing.

## NallPuter inferences

- NallPuter should expose stable, structured computer operations even if the underlying implementation changes from Docker to a VM or another runtime.
- File APIs should support targeted reads, ranges, and searches rather than encouraging whole-project dumps.
- Command output should distinguish empty success from missing or failed output.
- API observations should be explicit enough for NALLY to reason over without knowing the infrastructure implementation.

## Resource model

- **Commands:** structured arguments plus result object.
- **Files:** path, range, size, content metadata.
- **Processes:** stable process/run identifiers.
- **Workspace:** current working directory as explicit state.
- **Observations:** bounded and semantically labeled.
- **Policy:** action is accepted only if the runtime allows it.

## Lifecycle model

- OpenHands illustrates a runtime lifecycle wrapped around an execution server.
- NallPuter should separate request lifecycle from computer lifecycle.
- A process can remain alive while the API client disconnects if policy permits.
- Reconnection should use stable computer and process identifiers.

## Security boundary

- The Docker boundary is useful, but NallPuter should not assume Docker itself is the final security boundary.
- Structured observations should make dangerous environment details harder to expose accidentally.
- File and shell operations should not have inconsistent access policy.
- Runtime errors need to be distinguishable from model/tool errors.

## Pricing / infrastructure cost signals

- Runtime/container cost depends on image size, startup behavior, persistence, and concurrency.
- Better observations can reduce model context cost even if runtime compute cost stays constant.
- Reproducibility and fast startup are competing optimization goals.

## What to copy

- Client-server runtime separation.
- Stable Agent–Computer Interface.
- Targeted file access.
- Explicit empty-output semantics.
- Runtime-swappable implementation.

## What to avoid

- Exposing raw TTY streams as the only interface.
- Returning enormous file contents by default.
- Assuming a container-only implementation is permanent.
- Mixing model reasoning logic with runtime enforcement.

## Open questions for NallPuter

- What exact observation schema should NallPuter standardize?
- Which file operations are sufficient for v0.1?
- Should PTY support be deferred until process semantics require it?
- Which ACI metrics should be part of Phase 9 evaluation?

## Sources

- **OpenHands Docs — Runtime architecture**
  https://github.com/OpenHands/docs/blob/main/openhands/usage/architecture/runtime.mdx
- **SWE-agent — Agent Computer Interface**
  https://github.com/SWE-agent/SWE-agent/blob/main/docs/background/aci.md
- **SWE-agent repository**
  https://github.com/SWE-agent/SWE-agent

- Research note 1: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 2: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 3: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 4: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 5: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 6: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 7: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 8: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 9: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 10: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 11: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 12: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 13: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 14: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 15: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 16: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 17: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 18: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 19: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 20: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 21: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 22: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 23: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 24: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 25: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 26: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 27: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 28: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 29: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 30: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 31: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 32: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 33: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 34: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 35: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 36: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 37: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 38: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 39: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 40: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 41: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 42: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 43: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 44: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 45: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 46: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 47: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 48: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 49: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 50: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 51: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 52: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 53: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 54: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 55: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 56: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 57: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 58: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 59: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 60: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 61: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 62: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 63: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 64: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 65: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 66: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 67: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 68: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 69: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 70: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 71: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 72: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 73: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 74: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 75: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 76: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 77: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 78: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 79: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 80: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 81: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 82: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 83: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 84: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 85: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 86: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 87: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 88: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 89: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 90: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 91: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 92: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 93: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 94: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 95: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 96: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 97: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 98: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 99: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 100: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 101: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 102: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 103: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 104: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 105: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 106: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 107: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 108: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 109: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 110: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 111: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 112: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 113: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 114: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 115: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 116: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 117: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 118: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 119: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 120: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 121: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 122: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 123: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 124: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 125: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 126: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 127: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 128: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 129: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 130: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 131: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 132: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 133: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 134: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 135: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 136: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 137: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 138: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 139: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 140: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 141: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 142: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 143: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 144: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 145: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 146: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 147: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 148: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 149: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 150: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 151: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 152: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 153: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 154: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 155: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 156: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 157: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 158: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 159: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 160: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 161: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 162: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 163: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 164: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 165: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 166: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 167: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 168: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 169: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 170: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 171: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 172: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 173: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 174: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 175: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 176: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 177: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 178: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 179: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 180: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 181: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 182: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 183: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 184: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 185: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 186: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 187: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 188: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 189: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 190: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 191: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 192: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 193: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 194: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 195: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 196: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 197: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 198: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 199: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 200: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 201: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 202: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 203: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 204: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 205: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 206: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 207: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 208: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 209: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 210: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 211: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 212: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 213: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 214: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 215: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 216: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 217: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 218: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 219: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 220: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 221: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 222: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 223: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 224: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 225: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 226: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 227: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 228: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 229: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 230: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 231: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 232: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 233: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 234: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 235: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 236: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 237: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 238: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 239: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 240: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 241: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 242: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 243: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 244: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 245: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 246: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 247: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 248: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 249: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 250: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 251: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 252: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 253: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 254: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 255: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 256: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 257: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 258: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 259: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 260: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 261: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 262: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 263: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 264: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 265: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 266: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 267: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 268: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 269: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 270: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 271: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 272: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 273: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 274: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 275: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 276: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 277: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 278: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 279: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 280: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 281: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 282: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 283: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 284: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 285: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 286: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 287: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 288: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 289: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 290: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 291: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 292: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 293: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 294: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 295: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 296: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 297: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 298: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 299: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 300: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 301: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 302: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 303: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 304: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 305: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 306: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 307: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 308: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 309: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 310: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 311: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 312: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 313: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 314: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 315: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 316: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 317: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 318: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 319: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 320: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 321: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 322: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 323: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 324: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 325: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 326: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 327: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 328: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 329: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 330: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
- Research note 331: OpenHands + SWE-agent — Agent–Computer Interface Research. Record the observed mechanism, the evidence source, the NallPuter implication, and any unresolved limitation.
