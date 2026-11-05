---
date: 2026-10-27
status: current
---

# Delegation to agents is expressed as Permission rules on situation-split Verbs

**Context:** Permission rules grant an operation per repo, but the oversight an operation needs varies by situation (reparenting Issues under an approved design is routine; inferring a new project and reparenting existing Issues under it is scoping), so the skills had accumulated rules about who may act ("awaits human confirmation", "only when very confident") that no grant enforced and that would have to be rewritten for any repo that delegated more. The 2026-10-27 home-in on the Issue Tracker skill family ([proposal](../projects/use-issues/2026-11-05-proposal.md)) settled how delegation is expressed.

**Decision:** Verbs are split or augmented so that situations carrying different risk or trust can be given different Permission rules. To separate high-judgement from low-judgement situations within one Verb, the Verb offers a form that takes one more argument: the existing, approved decision (a design document, say) that justifies the action. The Wrapper records that source as provenance and does not verify it. A repo that trusts its agents grants the provenance-free form; a repo that trusts them less grants only the provenance-taking form for higher-risk operations, so the agent takes accountability up front and can be held to it afterwards.

**Rationale:** Grants are the one place policy is enforced, so delegating more to agents in one repo without rewriting skills or tools requires that every situation differing in required oversight be a different grantable invocation.

## Consequences

- bdw, a pass-through over bd, gets its own Verbs for the operations that need a situation or a source argument.
- Skills carry discipline (when an act is correct, what it must carry, what to check first) and never say who may act; a skill names situations only where no grant can separate them.
- The source argument buys accountability, not proof: a false claim of provenance is detectable and correctable afterwards, and having to make one is a deterrent; an operation whose policy must be foolproof is gated on the operation itself.
- Rule sets grow by one row per invocation, so a consumer generates them from a spec rather than writing them by hand.

## Alternatives Considered

### A per-repo delegation declaration that skills read

**Description:** A file per repo stating how much judgement agents hold, which skills consult before acting.
**Rejection rationale:** It puts policy in a file an agent could edit to loosen its own limits, and it states in a second place what the grants already say.

### `ask` on every judgement-laden operation

**Description:** Grant the routine operations and set `ask` on close, reparent, duplicate, and body rewrites everywhere.
**Rejection rationale:** A grant on the whole operation cannot tell the routine case from the judgement case, so a repo that delegates more must either accept prompts on routine work or allow the judgement case blind, and an unattended session cannot answer an `ask` at all.

### Keep "only when very confident" in skill text

**Description:** Leave the judgement rules as guidance in the skills, as they were.
**Rejection rationale:** Nothing enforces it, each agent reinterprets it a step further, and it names the actor in a procedure that should be actor-neutral.

### Verify the source in the Wrapper

**Description:** Have the Wrapper check that the cited design document or plan actually authorizes the change.
**Rejection rationale:** A tool cannot read a document's intent, and the aim is good judgement with accountability, which a recorded claim provides, not foolproof adherence, which belongs to operation-level gates.
