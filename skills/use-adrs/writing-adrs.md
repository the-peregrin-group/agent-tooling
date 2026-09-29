# How to format an ADR

This guide is canon and _supersedes any observed contradictory conventions in existing ADRs_. If in doubt, follow this guide, not the project conventions.

## Template

```md
---
date: [YYYY-MM-DD]
status: ["current" or "superseded by ADR-XXXX"]
---

# [decision title]

**Context:** [the problem statement, trigger for needing a decision; max 3 sentences]

**Decision:** [what was decided, concretely; max 1 sentence]

**Rationale:** [why was the decision made; max 1 sentence]

## [optional] Consequences

- [Consequence 1; max 1 sentence]
- ...

## [optional] Alternatives Considered

### [Name of option N]

**Description:** [concise description of alternative approach; max 1 sentence]
**Rejection rationale:** [concise description of rejection rationale; max 3 sentences]

[repeat ### sections as needed, one per option]
```

These sections should be as concise as possible while still meeting our "Why ADRs?" goal. There is no _minimum_ length per section; each can be a sentence fragment _if sufficient_.

If more than one sentence is required for `Rationale`, you should probably instead liste alternatives considered (see below)

## Consequences (optional)

If applicable, record _high-impact_ downstream consequences of this decision, one bullet, one sentence each.

## Alternatives considered (optional)

When the rejected alternatives are seemingly good solutions that required non-trivial exploration and reasoning to rule out; the goal is to prevent pointless relitigation. Focus the rejection rationale on the meaningful engineering trade-offs considered.
