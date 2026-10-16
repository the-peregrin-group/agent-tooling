---
date: 2026-10-16
status: current
---

# Beads tracks agent-swarmed work; long-lived work belongs in forge issues

**Context:** [ADR 0001](0001-adopt-beads-for-the-tracker-trial.md) (adopt Beads as the sole work tracker for a local-only trial) made Beads this repo's only Issue Tracker until a go/no-go, with GitHub Issues frozen. By 2026-10-16 the trial had run across many sessions and one agent workjam that landed 36 Leaf Issues without a `bdw` refusal, and nearly all the friction it logged was fixable in our own layer (see the [Beads trial](../projects/beads-trial/index.md)). The live question had shifted from whether Beads works to which tracker suits which kind of work.

**Decision:** The trial ends with Beads kept for work that agents swarm, while long-lived, low-churn, or human-driven work belongs in forge issues (GitHub or Forgejo Issues), and this repo stays on Beads alone until its long tail can move back to forge issues.

**Rationale:** Beads' one real advantage over forge issues is agent-native operation (a computed ready queue, single-owner claims, a per-session Actor, no forge round-trip), whereas ownership and self-hosting argue for Forgejo just as well, so the choice follows who drives the work.

## Consequences

- GitHub Issues stays enabled for this repo, and the issues imported on 2026-09-24 stay open there as stale copies; agents file and change nothing there until the long tail moves back.
- A project with both kinds of work needs Beads and forge issues together, each Issue with one writable home at a time, checked out to Beads for a swarm and back afterwards; that pattern is not built (`agent-tooling-ze3`).
- The go/no-go criteria, the phase-two entry criteria, and per-criterion tagging of the friction log are dropped.

## Alternatives Considered

### The planned "go": close every GitHub issue and disable GitHub Issues

**Description:** Close each open GitHub issue with a pointer to its Beads replacement and turn GitHub Issues off, as the dated [phase-two proposal](../projects/beads-trial/phase-two.md) planned for a go.
**Rejection rationale:** Long-lived work belongs in forge issues, so disabling them would remove the home this repo's long tail is meant to return to.

### No-go: back to GitHub Issues for everything

**Description:** Refile the open Beads Issues to GitHub by hand and retire Beads.
**Rejection rationale:** Forge issues have no ready queue, no single-owner claims, and one identity for every agent, which is what the workjam relied on.

### Beads for everything

**Description:** Make Beads every project's only tracker, long-lived work included.
**Rejection rationale:** For work agents do not swarm, Beads adds nothing over forge issues and offers a human reader less.

### Formal go/no-go criteria first

**Description:** Write a checkable decision rule, then grade the friction log and the trial's evidence against the use-bd success criteria before ruling.
**Rejection rationale:** Which tracker to use is a judgment of fit and preference that the evidence had already settled, and grading machinery would have cost more than the decision is worth in a trial about reducing friction.

### Keep the trial running, or run phase two on a second repo first

**Description:** Extend phase one, or repeat the trial with sync on a second repo before ruling.
**Rejection rationale:** Phase one had stopped producing new findings, and the one open risk, a remote for the Issue data, is tested more cheaply on this repo ([ADR 0012](0012-beads-data-syncs-to-private-forgejo-remote.md)).
