---
date: 2026-10-16
status: current
---

# Beads data syncs to a private Forgejo remote, never to the public GitHub origin

**Context:** [ADR 0001](0001-adopt-beads-for-the-tracker-trial.md) (adopt Beads as the sole work tracker for a local-only trial) kept the Beads database on the maintainer's machine with no remote, so this repo's whole Issue Tracker is a single copy, and [ADR 0011](0011-beads-for-swarmed-work-forge-issues-for-long-lived-work.md) (Beads tracks agent-swarmed work) made Beads permanent here. A Beads push goes through Dolt's own client rather than git, so the repo's pre-push content lint never sees it, and this repo's GitHub origin is public.

**Decision:** This repo's Beads database gets a Dolt remote in a private repository on the maintainer's self-hosted Forgejo, and never one on the public GitHub origin.

**Rationale:** Persistence costs only disk and setup, and a private, self-hosted remote keeps unlinted Issue content, with its full Dolt history, from ever being published.

## Consequences

- Dolt remotes are independent of git remotes, so the code stays on GitHub while the Issue data does not, and a fresh clone of the public repo gets no Issue data.
- The remote's address stays out of the tracked `.beads/config.yaml`, because this repo is public.
- A Beads push bypasses gitw, so the push path needs its own Permission rule, or a Verb, granting exactly the Beads data ref (`agent-tooling-cy3`).

## Alternatives Considered

### Stay local-only

**Description:** Keep the database on the maintainer's machine with no remote, as during the trial.
**Rejection rationale:** A lost disk, a lost machine, or a bd upgrade with a bad migration would lose the Issue Tracker outright, and a remote costs little.

### A remote on the public GitHub origin

**Description:** Sync to `refs/dolt/data` on the repo's own origin, which `bd init` defaults to and the dated [phase-two proposal](../projects/beads-trial/phase-two.md) planned once Issue content had a lint path.
**Rejection rationale:** Every Issue, note, and comment would be published along with its full history, outside the content lint; no lint path for Issue data exists, and a published history cannot be withdrawn.

### A private remote on GitHub

**Description:** Sync to a private GitHub repository.
**Rejection rationale:** The Issue data would still sit with a third party when a self-hosted forge is already at hand.

### Periodic snapshots to a NAS

**Description:** Archive a snapshot of the database to the maintainer's NAS every few days (`agent-tooling-mfs`).
**Rejection rationale:** A remote holds every Dolt commit as it is pushed and doubles as the path for sharing the data, while snapshots go stale between runs and need their own schedule.
