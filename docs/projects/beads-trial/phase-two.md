# Beads trial: the verdict and phase two

Proposal, ratified 2026-10-01. A point-in-time capture of the plan at
ratification; [index.md](index.md) tracks its state.

The trial runs in two phases. Phase one is this repo, local-only, as
described in [index.md](index.md) and [design.md](design.md). Phase two
repeats the trial on a second repo with sync turned on, to test what phase
one deliberately leaves out: a remote for Issue data, and several worktrees
sharing it.

## The phase-one verdict

- **Recorded as an ADR.** The go/no-go verdict is a new ADR in this repo.
  ADR 0001, which made Beads the sole Issue Tracker for the trial, is
  marked superseded in part, with a Superseded-by line naming the verdict
  ADR.
- **Announced on pinned issue #18.** The maintainer comments on the pinned
  issue, announcing the verdict and linking the ADR. That comment is the
  maintainer's deliberate act of unfreezing, and the one sanctioned write
  to the frozen Issue Tracker.
- **`CLAUDE.md` reworded to match.** Its freeze paragraph, which today ends
  the freeze at "the go/no-go recorded on pinned issue #18", is reworded so
  that the verdict lives in the ADR and the #18 comment is the maintainer's
  unfreeze act announcing it.
- **On go,** GitHub Issues is wound down completely. The maintainer closes
  every open GitHub issue with a pointer to its Beads replacement, through
  `ghw-issue-close`, and then disables GitHub Issues in the repo settings.
- **On no-go,** the maintainer refiles the still-open Beads Issues to
  GitHub by hand.
- **Either way, `bd github sync` is never run.** The no-sync rule of
  [design.md](design.md) holds through the boundary.

## Phase two

- **A second repo, with sync.** Its open GitHub issues are imported once,
  one way, and frozen, as in phase one. Unlike phase one, its Issue data
  syncs to the git remote through Dolt, on the dedicated ref
  `refs/dolt/data`, so it travels with the repo without touching any
  branch. Phase two also observes how several worktrees of one repo share
  that data.
- **A Wrapper Verb for the one remote write.** A Beads push bypasses the
  gitw Verbs and git's pre-push hooks (see
  [known behavior](index.md#beads-130-known-behavior)). The push is
  therefore a named exception: a Verb carries it, and the Permission rules
  grant exactly the Beads data ref and nothing else.
- **A lint path for Issue content.** A repo whose pushes must pass a
  content lint cannot sync Issue content the lint never sees. Issue content
  needs its own lint path before such a repo syncs; until then that repo,
  this one included, stays local-only.
- **A pinned Beads version.** Both repos run one pinned Beads release, so
  findings stay comparable. An upgrade is deliberate, and the
  [known-behavior list](index.md#beads-130-known-behavior) is re-checked
  against it.
- **Entry criteria.** What makes phase one routine enough to start phase two
  is not yet written down (Issue to be filed).
