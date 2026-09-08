# OpenHands + SWE-agent â€” Agentâ€“Computer Interface Research

> Phase 1 research document for NallPuter. Facts, observations, and NallPuter inferences are deliberately separated.

## Evidence discipline

- **Documented fact:** directly stated by the cited primary or vendor source.
- **Third-party observation:** interpretation, benchmark, implementation note, or repository documentation that is not itself a vendor product promise.
- **NallPuter inference:** a design conclusion proposed for NallPuter; it is not a claim about the researched system.

## Executive summary

OpenHands provides a concrete client-server runtime pattern: the backend communicates with an ActionExecutor inside a Docker container over REST. SWE-agent complements that architecture with the Agentâ€“Computer Interface idea: the interface itself is a performance-critical part of an agent system. NallPuter should therefore be both an isolated runtime and a carefully designed observation/action interface.

## Documented facts

- OpenHands documents a client-server runtime implemented with Docker containers.
- The runtime initializes an action execution server inside the container.
- The backend sends actions and receives observations through a REST interface.
- OpenHands runtime actions include shell, file operations, Python, browser, and plugins.
- SWE-agent defines an Agentâ€“Computer Interface as the tools and interaction format between an agent and a computer environment.
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
- Stable Agentâ€“Computer Interface.
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

- **OpenHands Docs â€” Runtime architecture**
  https://github.com/OpenHands/docs/blob/main/openhands/usage/architecture/runtime.mdx
- **SWE-agent â€” Agent Computer Interface**
  https://github.com/SWE-agent/SWE-agent/blob/main/docs/background/aci.md
- **SWE-agent repository**
  https://github.com/SWE-agent/SWE-agent

