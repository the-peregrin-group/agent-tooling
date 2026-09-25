# Architecture decision records

Design decisions for this repo, one file per decision, named
`NNNN-short-title.md`. Numbering starts at 0001; scan the directory for the
highest number and add one.

Record a decision only when all three hold: it is hard to reverse, it would
surprise a reader without context, and it came out of a real trade-off. The
point is to preserve why, so that later decisions stay consistent, settled
questions are not relitigated, and an obsolete decision can be recognized.

## Format

```md
---
date: YYYY-MM-DD
---

# Short title of the decision

**Context:** problem statement and trigger; three sentences at most.
**Decision:** what was decided; one sentence.
**Rationale:** why; one sentence.
```

Optional, only when they add value: a `status` line in the frontmatter
(`current` or `superseded by ADR-NNNN`) once a decision is revisited;
**Gotchas:** for non-obvious downstream effects; and an
`## Alternatives Considered` section at the end, one `### Option` per
rejected alternative with **Description:** and **Rejection rationale:**
lines, only for alternatives that took real reasoning to rule out.

## Index

- [0001](0001-adopt-beads-for-the-tracker-trial.md): Adopt Beads as the sole
  work tracker for a local-only trial
