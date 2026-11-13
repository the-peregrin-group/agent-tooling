---
date: 2026-11-03
status: current
---

# Every repo carries its own copy of the Tracker Schema, bootstrapped from the shipped default

**Context:** With lifecycle semantics in a per-repo Issue State Diagram ([ADR 0019](0019-issue-lifecycle-semantics-live-in-the-issue-state-diagram.md), lifecycle semantics live in the Issue State Diagram), each repo needs a Tracker Schema, yet most of the maintainer's projects will use the shipped default untouched, which invites keeping the default implicit and letting a repo override pieces of it. The 2026-11-03 home-in on the Issue Tracker skill family ([proposal](../projects/use-issues/2026-11-13-proposal.md)) settled how a repo gets and keeps its schema.

**Decision:** Setup writes a full copy of the shipped default Tracker Schema into every repo, recording the revision of this repo it was copied from. Any edit to that copy is the repo's customization. No repo relies on an implicit default or a reference to the shipped one.

**Rationale:** The file is the agents' only context for the repo's lifecycle, so it must read whole and self-explanatory in place, and a recorded source revision lets setup or triage show the owner what the default has changed since, which a copy without provenance could not.

## Consequences

- Improvements to the shipped default reach existing repos only when their owner is shown the difference and takes it; the provenance line is what makes that possible.
- The generic skills name none of a repo's states and are read beside its schema; a repo that customizes keeps its copy self-explanatory, since no skill text describes its states.
- The same file is the one home for the rest of the schema (kinds, priorities, labels), which is what `agent-tooling-wx5` (one canonical per-repo config home) asked for.

## Alternatives Considered

### An implicit default with per-repo overrides

**Description:** The skills carry the default lifecycle, and a repo writes a file only for what it changes.
**Rejection rationale:** An agent would read a default in the skill and then a partial override in the repo and reconcile the two, which is the drift mechanism this design exists to remove.

### A reference to the shipped default

**Description:** The repo's file names a default by version, and the tooling resolves it from the installed copy.
**Rejection rationale:** The file would not read whole in place, and a repo's lifecycle would change under it when the installed tooling updated.
