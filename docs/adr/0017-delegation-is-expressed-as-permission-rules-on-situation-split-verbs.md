---
date: 2026-10-27
status: current
---

# Delegation to agents is expressed as Permission rules on situation-split Verbs

**Context:** Permission rules grant an operation per repo, but the oversight an operation needs varies by situation (reparenting Issues under an approved design is routine; inferring a new project and reparenting existing Issues under it is scoping), so the skills had accumulated rules about who may act ("awaits human confirmation", "only when very confident") that no grant enforced and that would have to be rewritten for any repo that delegated more. The 2026-10-27 home-in on the Issue Tracker skill family ([proposal](../projects/use-issues/2026-11-13-proposal.md)) settled how delegation is expressed.

**Decision:** Verbs are split or augmented so that situations carrying different risk or trust can be given different Permission rules, and policy about who may act leaves the skills wherever a grant can express it.

**Rationale:** Grants are the one place policy is enforced, so delegating more to agents in one repo without rewriting skills or tools requires that every situation differing in required oversight be a different grantable invocation.

## Consequences

- bdw, a pass-through over bd, gets its own Verbs for the operations that need a situation argument.
- Skills carry discipline (when an act is correct, what it must carry, what to check first) and never say who may act.
- Rule sets grow by one row per invocation, so a consumer generates them from a spec rather than writing them by hand.
- Not every situation can be split yet.

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
