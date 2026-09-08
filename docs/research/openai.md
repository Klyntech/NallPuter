# OpenAI â€” Hosted Computer Environment Research

> Phase 1 research document for NallPuter. Facts, observations, and NallPuter inferences are deliberately separated.

## Evidence discipline

- **Documented fact:** directly stated by the cited primary or vendor source.
- **Third-party observation:** interpretation, benchmark, implementation note, or repository documentation that is not itself a vendor product promise.
- **NallPuter inference:** a design conclusion proposed for NallPuter; it is not a claim about the researched system.

## Executive summary

OpenAI provides the clearest model for a modern agent-facing computer contract: the model proposes actions, a hosted container executes them, results are returned into the agent loop, and the environment supplies files, networking controls, skills, and bounded shell output. The strongest NallPuter lesson is that the computer is a runtime contract, not merely an operating-system shell.

## Documented facts

- OpenAI describes the Responses API, shell tool, and hosted container workspace as coordinated components for agent execution.
- The hosted container provides a filesystem used for inputs, outputs, and intermediate state.
- The shell tool supports command execution and returns output to the model.
- The API forwards commands to a container runtime and feeds resulting output into the next model step.
- Multiple shell commands can be executed concurrently in separate container sessions.
- Shell output can be bounded so large command output does not consume excessive context.
- OpenAI describes restricted network access as part of the computer environment.
- OpenAI describes skills as versioned bundles that can be copied into the container when needed.
- OpenAI describes compaction as a mechanism for long-running agent context.

## Third-party / implementation observations

- The design is deliberately layered: orchestration outside, execution inside a hosted environment.
- Bounded output is presented as an agent-quality feature as well as a resource-control feature.
- The container filesystem is used to stage resources instead of copying all data into prompts.
- Concurrent sessions provide a useful model for multiplexing multiple commands without requiring a user-facing terminal.
- The shell contract is non-interactive at the agent level; the platform manages the execution lifecycle around it.

## NallPuter inferences

- NallPuter should expose a structured execution contract rather than raw host subprocess handles.
- `run_id`, status, output cursors, cancellation, and bounded output should be first-class concepts.
- Workspace storage should be a real execution resource, not prompt text.
- Skills are a useful future capability, but NallPuter should keep the v0.1 runtime focused on computer primitives.
- NallPuter should allow concurrent executions while keeping each run separately observable.

## Resource model

- **RAM / CPU:** enforce at the computer or process boundary.
- **Disk:** workspace is a first-class state store.
- **Processes:** execution runs need stable IDs.
- **Wall time:** each run needs a timeout/cancel path.
- **Output:** each run needs a byte budget and pagination/cursor semantics.
- **Network:** policy should be independently enforceable from agent text.

## Lifecycle model

- Candidate command lifecycle: `queued â†’ running â†’ succeeded/failed/timed_out/cancelled`.
- A computer lifecycle should be separate: `created â†’ ready â†’ idle â†’ stopped â†’ deleted`.
- A long-running process should not force the API into a single blocking request.
- NallPuter can support polling in v0.1 while defining a streaming route in the contract.

## Security boundary

- OpenAI's model strongly supports the idea that the runtime, not the model, is responsible for enforcing execution and network boundaries.
- Credential access should be scoped and not be equivalent to inheriting the NALLY host environment.
- The NallPuter API should expose observations, not raw internal runtime details.
- Large filesystem state should stay in the workspace rather than being repeatedly injected into LLM context.

## Pricing / infrastructure cost signals

- The source describes a hosted computer environment, shell execution, network controls, skills, and compaction as platform components.
- NallPuter cost should be evaluated across persistent base cost, transient execution cost, and storage.
- Output and storage caps are potential cost controls as well as context controls.

## What to copy

- Structured shell observations.
- Explicit workspace state.
- Output caps and pagination.
- Separation between orchestration and execution.
- Concurrent run identity.

## What to avoid

- Tight coupling to a proprietary API shape.
- Treating hosted-container expiry as a complete persistence model.
- Building skill management into the first NallPuter runtime before shell/files/processes are solid.

## Open questions for NallPuter

- What should NallPuter's canonical observation schema contain?
- Should binary output use the same run channel or artifact storage?
- How much output should be retained server-side?
- What is the right concurrency policy for one persistent computer?

## Sources

- **OpenAI Engineering â€” From model to agent: Equipping the Responses API with a computer environment**
  https://openai.com/index/equip-responses-api-computer-environment/

