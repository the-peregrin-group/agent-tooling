---
date: 2026-11-03
status: current
---

# The issue skills are split by moment of need, with the fundamentals as a Knowledge Skill

**Context:** The issue guidance lived in long per-platform operating manuals that every session loaded whole and that drifted as each restated the others; the maintainer's sketch for the family had a generic `use-issues` skill as both fundamentals and table of contents, which other skills would tell agents to load. This family is the pilot for restructuring every skill for progressive disclosure (`agent-tooling-jat`). The 2026-11-03 home-in on the Issue Tracker skill family ([proposal](../projects/use-issues/2026-11-13-proposal.md)) settled the shape.

**Decision:** The generic issue skills are split by moment of need (filing, working an Issue, breaking down a Branch Issue, triage, setup), one skill per moment and none per platform. The fundamentals are a Knowledge Skill, `know-issues`, whose description carries the distillation into every session. There is no table-of-contents skill: the graph's edges are the skill descriptions in the session listing, pointers in skill text at the moment of need, and the wrappers' help and refusals.

**Rationale:** An agent loads a skill whole and loses hops, so a document that exists to point at other documents is a hop that costs loads and makes the leaf feel already read, while the harness's listing of descriptions is a table of contents that is already in context for free.

## Consequences

- A session pays for the moments it is in, plus one description per skill; the manuals' cost per session goes away.
- A platform skill is entered when the platform is what the agent can see (a `.beads/` directory, a GitHub remote); it must stay a pointer, or it becomes the manual again.
- `agent-tooling-jat` inherits the split rule and the no-table-of-contents rule as the pilot's lesson.

## Alternatives Considered

### A `use-issues` skill as fundamentals and table of contents

**Description:** One generic skill that teaches the mental model and lists the moment skills, which platform skills tell agents to load.
**Rejection rationale:** The fundamentals belong in a Knowledge Skill's description, where they reach every session unloaded, and the listing part would be a second copy of the session listing that goes stale; the hop it adds is the one agents skip.

### Split by topic

**Description:** Skills per subject (filing, relationships, lifecycle, closing), loaded as reference.
**Rejection rationale:** An agent at a moment of need would have to load several topics to act once, so it would load one and guess the rest.

### One moment skill per platform

**Description:** `create-issue` for Beads, for GitHub, and for Forgejo, each complete in itself.
**Rejection rationale:** Three copies of the same discipline, which is the drift this design exists to remove; the discipline is generic and only the Verb differs.
