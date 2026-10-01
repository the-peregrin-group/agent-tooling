---
date: 2026-09-30
status: current
---

# home-in is attended-only

**Context:** Every other Skill in this repo has an unattended branch (lexicon proposals, draft ADRs for a reviewer, guess-and-note autonomy), and home-in's value lies entirely in a live exchange with the user. The design is [home-in: design](../projects/understanding/home-in-design.md).

**Decision:** home-in has no unattended form: its body declares attended-only, and the declaration is not enforced, because no enforcement exists; a narrow trigger description limits accidental invocation and `disable-model-invocation` is not set.

**Rationale:** An interrogation with no one to answer it produces the agent's opinion dressed as the user's, and dropping the unattended branches removes a shadow procedure for a case that does not exist.

## Consequences

- The skill stays model-invocable, because Claude Code parses a slash command only as a message's first token (per the skills documentation at code.claude.com/docs/en/skills, verified 2026-09-30) and the natural invocation is mid-sentence ("help me /home-in on..."), which only the model path can honor.
- A user who invokes home-in from an unattended job is outside the skill's contract, and the body says so.

## Alternatives Considered

### Unattended home-in over a written brief

**Description:** Interrogate a brief instead of a person and emit lexicon proposals and draft ADRs.
**Rejection rationale:** The questions have no one to answer them, so nothing distinguishes the result from the agent's own analysis.

### Enforce with `disable-model-invocation: true`

**Description:** Set the frontmatter flag so only a leading `/home-in` can start the skill.
**Rejection rationale:** It makes the mid-sentence invocation silently inert, and the flag never stopped an unattended user from typing the command anyway.
