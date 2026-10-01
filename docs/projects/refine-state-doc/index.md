# refine-state-doc: the State doc Skill

The `refine-state-doc` Skill is the guide for writing and refining State
docs, as distinct from Stream docs. It defines what makes a State doc good
(clarity and concision, one point in time, one owning place per fact,
progressive disclosure from summary to detail) and how to refine one toward
that. Agents load it when working on a known State doc, or when told to
refine one; home-in loads it at its opening move, because its default
artifact is a State doc.

## Status

| Capability | State | Where |
|---|---|---|
| The properties of a good State doc | shipped | `skills/refine-state-doc/SKILL.md` |
| A three-step refinement process: plan the organization, settle each fact's current value, rewrite into the plan without past states | shipped | `skills/refine-state-doc/SKILL.md` |
| Guardrails: embedded streams may be rewritten, keeping their event statements; currency stamps are left alone, and staleness is mentioned in one sentence rather than fixed | shipped | `skills/refine-state-doc/SKILL.md` |
| Exceptions that look like history but are state (alternatives considered, major reversals, root causes), and where each goes | shipped | `skills/refine-state-doc/SKILL.md` |
| Rules for Stream sections embedded in a State doc, including TODO lists that track rather than define | shipped | `skills/refine-state-doc/SKILL.md` |
| Loading the use-privacy Skill, when listed, before writing anything bound outward | planned | `agent-tooling-n0p` |
