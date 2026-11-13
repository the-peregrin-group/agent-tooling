---
date: 2026-11-03
status: current
---

# Issue lifecycle semantics live in the repo's Issue State Diagram, not in the skills

**Context:** The lifecycle guidance was spread across skills as fixed state lists with exit rules, which only fit software projects, drifted as each skill restated them, and could not be customized per repo without rewriting skill text. The maintainer's test case was that "ready" and "closed" are not properties of a state but of who is asking: a scoping agent's ready queue is a different state from an implementer's. The 2026-11-03 home-in on the Issue Tracker skill family ([proposal](../projects/use-issues/2026-11-13-proposal.md)) settled where lifecycle logic lives.

**Decision:** Every state meaning and every transition condition is written in natural language in the repo's Issue State Diagram, part of its Tracker Schema. Each Issue State carries one structural attribute, open or closed, and nothing else is encoded. The skills say one thing about states: judge every move against the repo's Issue State Diagram. The ready queue is defined by the agent, as the unclaimed, unblocked Issues in the states it works.

**Rationale:** Agents judge prose conditions well and the maintainer's aim is good judgement with accountability rather than enforced logic, so a prose diagram per repo gives each project its own lifecycle without any skill knowing the states, while the one hard fact every tracker enforces, open or closed, stays structural.

## Consequences

- Scoping and design requirements (R31a, R31b) move out of the skills into the default diagram's transition conditions.
- Tooling that needs to reason about states (a lint, a triage pass) reads the diagram and the open-or-closed attribute, and nothing more.
- A repo whose diagram is unclear gets unclear transitions; the diagram is the agents' only context, and keeping it self-explanatory is the repo owner's job.
- Stage-aware blocking (a dependency blocks only at the state its blocker stops) is possible later but not built now; a blocking dependency blocks in every state.

## Alternatives Considered

### One universal state set in the skills

**Description:** Keep the triage skill's eight states and their exit rules as the lifecycle for every repo.
**Rejection rationale:** "Needs Eng Design" is an attention kind only a software project has, and every restatement across skills drifted.

### A fixed category layer with per-repo states mapped onto it

**Description:** The generic layer defines a few categories (intake, definition, ready, active, review, closed), skills reason about categories, and each repo maps its states onto them.
**Rejection rationale:** The categories freeze one agent's view into the schema, when "ready" for a scoping agent is "definition" for an implementer; the only category every tracker agrees on is open or closed, so that is the only one kept.

### Machine-checked exit requirements

**Description:** Encode each state's exit requirements as structured checks a lint can run.
**Rejection rationale:** Most requirements ("an implementer could proceed without further design input") are judgements no check can express, and a structured subset would push repos toward the checkable rather than the right.
