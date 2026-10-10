---
date: 2026-10-08
status: current
---

# Branch Issues are worked in passes, triggered by having no open children

**Context:** A Branch Issue's work is management (scoping, setting success criteria, breaking down, verifying completion), but nothing in Beads schedules it: excluded from ready-work queries it becomes invisible, and closed automatically once its children close it skips verification. No agent stays available across the days or weeks a Branch Issue can live, so that work cannot belong to a standing owner. The analysis is in the [use-bd v1 proposal](../projects/use-bd/v1-proposal.md).

**Decision:** A Branch Issue is ready work exactly when it has no open children, and each claim on it is one session-sized pass that ends either by adding children or by verifying completion and closing it.

**Rationale:** The state of the tree then says when management work is due, so it needs neither a long-lived owner nor special tasks to stand in for one.

## Consequences

- A new Branch Issue is ready work at once, and its first pass breaks it down.
- A Branch Issue is never closed merely because its children closed; a pass verifies it first.
- Children added in a pass become ready work as soon as they exist, so a pass drafts its whole breakdown before submitting it.

## Alternatives Considered

### Branch Issues as passive containers

**Description:** Exclude Branch Issues from ready work and close them once their children are done.
**Rejection rationale:** An unbroken-down Branch Issue is invisible, and nobody verifies that the whole met its goal.

### Breakdown and acceptance child tasks

**Description:** File a breakdown task first and an acceptance task, blocked by every sibling, last.
**Rejection rationale:** The acceptance task's dependencies must be kept current as children are added, which works against the grain and is easily misunderstood or skipped.

### A long-lived lead who owns the Branch Issue

**Description:** One agent claims the Branch Issue for its whole life and manages it throughout.
**Rejection rationale:** No agent stays available and up to speed across many sessions and days, and a claim cannot outlive its session.

### Hide children while the Branch Issue is claimed

**Description:** Children stay out of ready work until the pass releases its claim, so a breakdown can be restructured privately.
**Rejection rationale:** A session that dies mid-pass hides the whole subtree until its lease expires, whereas building the breakdown in one atomic batch gives the same privacy without a lock.
