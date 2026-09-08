# Manus â€” Persistent Cloud Computer Research

> Phase 1 research document for NallPuter. Facts, observations, and NallPuter inferences are deliberately separated.

## Evidence discipline

- **Documented fact:** directly stated by the cited primary or vendor source.
- **Third-party observation:** interpretation, benchmark, implementation note, or repository documentation that is not itself a vendor product promise.
- **NallPuter inference:** a design conclusion proposed for NallPuter; it is not a claim about the researched system.

## Executive summary

Manus is useful as the reference model for a persistent, user-visible computer rather than a one-shot command sandbox. Its Cloud Computer is described as a persistent Ubuntu Server environment that can continue running services outside active Manus sessions. The research value for NallPuter is the explicit persistence concept, resource tiers, and the distinction between temporary sandboxing and a persistent computer.

## Documented facts

- Manus documents Cloud Computer as a persistent cloud server running Ubuntu Server 24.04 LTS.
- Manus says Cloud Computer instances can continuously run services outside active Manus sessions.
- The Cloud Computer offering includes a dedicated public IP address.
- Manus documents selectable resource tiers for different workloads.
- Manus documents monthly billing for Cloud Computer plans.
- Manus describes Cloud Computer as a separately purchased computer that can be mounted from the Manus interface.
- Manus also distinguishes Cloud Computer from temporary sandbox execution.
- The Help Center source states that the Cloud Computer is persistent rather than a disposable per-task runtime.

## Third-party / implementation observations

- The useful architectural distinction is between ephemeral task execution and a persistent computer that retains state.
- A persistent computer changes the agent contract: the agent can reconnect to an existing machine rather than recreate the environment for every task.
- A dedicated IP is an example of how a persistent computer may expose stable network identity, but NallPuter does not need to copy this.
- The tier model suggests resource profiles can be expressed as independent capacity choices instead of inventing a different computer product for every workload.

## NallPuter inferences

- NallPuter should model **computer identity** separately from an individual command execution.
- NallPuter should treat persistence as an explicit lifecycle property, not an accidental side effect of a long-lived process.
- Resource tiers may eventually become bundles of the independent NallPuter resource knobs, but the underlying knobs should remain measurable and independently enforceable.
- A stable computer identity is useful for reconnecting NALLY to the same workspace.
- NallPuter should not copy a public IP requirement because its intended topology is NALLY â†’ private network â†’ NallPuter.

## Resource model

- **CPU:** tiered capacity is useful for user-facing packaging; enforcement should still track actual CPU quota.
- **RAM:** should be an independently measurable limit.
- **Disk:** persistent storage is central to the computer model.
- **Processes:** persistent computers may keep services running while the computer exists.
- **Network:** stable network identity is possible but not a requirement for NallPuter v0.1.
- **Lifecycle:** computer lifetime is distinct from request lifetime.

## Lifecycle model

- Candidate states: `provisioning â†’ running â†’ idle â†’ stopped â†’ starting â†’ running â†’ error â†’ recovered/destroyed`.
- A persistent computer can remain available between agent sessions.
- An explicit stop/destroy operation is required to distinguish lifecycle events from task completion.
- Idle behavior must be designed explicitly so a persistent environment does not create uncontrolled cost.
- NallPuter should later decide whether an idle persistent computer stays running, auto-stops, or becomes a lower-cost retained state.

## Security boundary

- Persistence is valuable only if state boundaries are explicit.
- NallPuter must not rely on prompts to constrain access to the host environment.
- The persistent computer should be isolated from the public NALLY service and reached through authenticated private networking.
- Credentials should not be inherited blindly from the NALLY process.

## Pricing / infrastructure cost signals

- Manus publishes monthly Cloud Computer pricing rather than only per-second sandbox usage.
- The current Help Center shows a Basic plan at $10/month and states that plans are priced as persistent cloud servers.
- This provides a useful commercial signal: persistent environments have a meaningful idle-cost tradeoff.
- NallPuter should separate user-visible resource tiers from underlying runtime policy so economics can change without changing the API model.

## What to copy

- Persistent identity and filesystem continuity.
- A recognizable computer lifecycle.
- Resource tiers built from explicit capacity choices.
- A simple user mental model: NallPuter is the computer; NALLY is the brain.

## What to avoid

- Provider-specific public-IP behavior.
- Vendor-specific packaging that cannot be reproduced on Render.
- Treating 24/7 availability as automatic proof of process persistence across failures.
- Assuming persistence alone solves security.

## Open questions for NallPuter

- What exact storage mechanism backs a given persistent computer?
- What survives provider maintenance or forced redeploy?
- Which process failures are automatically recovered?
- How should NallPuter expose a persistent computer without leaking internal provider details?

## Sources

- **Manus Help Center â€” Understanding Cloud Computer Plans and Billing**
  https://help.manus.im/en/articles/15392078-understanding-cloud-computer-plans-and-billing
- **Manus Help Center â€” What is the Cloud Computer?**
  https://help.manus.im/en/articles/15392111-what-is-the-cloud-computer

