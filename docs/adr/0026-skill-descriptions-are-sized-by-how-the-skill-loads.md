---
date: 2026-11-24
status: current
---

# A Skill's description is sized by how the Skill loads, and its trigger text starts terse

**Context:** Every Skill's description sits in the Skill listing that every session and sub-agent pays for before it does anything, and a measured multi-agent run showed most listed Skills never loaded at all. This repo's 17 model-visible descriptions had grown to about 12.7k characters (roughly 3.2k tokens) of summaries, trigger-phrase lists, and EXCLUDE clauses, with no evidence that the extra text changed what loaded. `agent-tooling-6zll` holds the measurements.

**Decision:** A Skill's description takes the shape of the route it loads by (hidden when only the user invokes it; very short when something else cues it; a short, absolute trigger for a clear-cut condition; short to start for a judgement call; a distillation plus a short trigger for a Knowledge Skill), and its trigger text grows only to fix an observed trigger miss.

**Rationale:** The listing is paid in every session while extra trigger text has no observed benefit, so only a miss someone saw can justify paying for more.

## Consequences

- Trigger-phrase lists and EXCLUDE clauses leave the descriptions; telling neighbouring Skills apart is the bodies' job.
- A Skill hidden from the model (`disable-model-invocation: true`) can only be started by the user typing its name, so a Skill any agent or automation may need to start stays visible, however short its description.
- The Knowledge Skills keep a heavy description, and its cost is measured so that whether it pays can be judged later.

## Alternatives Considered

### Rich descriptions with trigger-phrase lists and EXCLUDE clauses

**Description:** Keep each description as a summary of the Skill plus every phrase that should fire it and every neighbour it should not be confused with.
**Rejection rationale:** The cost is paid in every session for a benefit nobody observed, and the lists overlapped across Skills (use-bd and work-issue both claimed "what's ready", create-issue and use-github both claimed "file an issue"), so they blurred the routing they were meant to sharpen.

### Hide every Skill the user mostly invokes by name

**Description:** Set `disable-model-invocation: true` on every Skill the user usually starts with a slash command.
**Rejection rationale:** It breaks natural-language triggers (home-in on "home in on"), agent-initiated use (handoff when an agent hands work to another agent), and automation (setup-github-issues when a new project is set up unattended).

### One terse rule for every description, Knowledge Skills included

**Description:** Cut the Knowledge Skills' descriptions to a short trigger like every other Skill's.
**Rejection rationale:** A Knowledge Skill's description is how its knowledge reaches every session unloaded ([ADR 0021 (the issue skills are split by moment of need)](0021-issue-skills-are-split-by-moment-of-need.md)), so cutting it would silently undo that decision; whether that approach is worth its cost is a separate judgement, left to the measurement.
