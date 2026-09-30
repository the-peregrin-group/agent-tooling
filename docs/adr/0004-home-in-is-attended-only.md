---
date: 2026-09-30
status: current
---

# home-in is attended-only

**Context:** Every other Skill in this repo has an unattended branch (lexicon proposals, draft ADRs for a reviewer, guess-and-note autonomy), and home-in's value lies entirely in a live exchange with the user. The design is [home-in: design](../skills/home-in/design.md).

**Decision:** home-in has no unattended form: its frontmatter sets `disable-model-invocation: true` and its body states attended-only.

**Rationale:** An interrogation with no one to answer it produces the agent's opinion dressed as the user's, and dropping the unattended branches removes a shadow procedure for a case that does not exist.

## Consequences

- The frontmatter flag stops only the model's auto-invocation; a user who types `/home-in` into an unattended job is outside the skill's contract, and the body says so.

## Alternatives Considered

### Unattended home-in over a written brief

**Description:** Interrogate a brief instead of a person and emit lexicon proposals and draft ADRs.
**Rejection rationale:** The questions have no one to answer them, so nothing distinguishes the result from the agent's own analysis.
