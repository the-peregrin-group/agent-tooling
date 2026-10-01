# `gitw-trunk-sync`: proposal

Proposal, ratified 2026-10-01. A point-in-time capture of the plan for
the one remaining planned gitw Verb; it is not built. Status and Issue:
[index.md](index.md) (`agent-tooling-1790288521317-5-34a5f7c2`). Current
design: [design.md](design.md).

## Purpose

Keep the human's local default branch current without an agent ever
owning it. Under universal worktree isolation, every agent works in its
own worktree on its own branch and affects trunk only by pushing for a PR
or through `gitw-integrate`. The primary checkout's local default branch
belongs to the human, and the one thing an agent may do to it is
fast-forward it. Typical use: after a `gitw-integrate` or a forge merge,
so the human's next look at the primary checkout is current.

Agents do not depend on it: `gitw-branch-start` branches from the
remote-tracking ref, so a fresh worktree never needs local trunk current.
The Verb is a convenience and gates nothing.

## Specification

`gitw-trunk-sync <repo>`

1. Verify identity like every other Verb (Roster label, cwd inside the
   repo's primary checkout or one of its worktrees), then fetch the
   authoritative remote.
2. Find where the local default branch is checked out, and act without
   ever switching any worktree's branch:
   - **Checked out in the primary checkout, worktree clean:**
     fast-forward it in place to the fetched tip.
   - **Checked out nowhere:** move the ref directly (`update-ref`,
     guarded by its old value).
   - **Checked out in the primary checkout, worktree dirty:** exit 4.
     The dirt is the human's; the agent reports it and stops.
   - **Local default diverged from the fetched tip** (it has commits the
     remote lacks): exit 4. Unpushed local trunk commits are the human's
     parked work, never an agent's to reconcile.
3. Already at the fetched tip: exit 0, converged no-op. A machine-local
   repo has nothing to fetch: converged no-op.

Exit codes follow the shared Exit-code contract (see
[design.md](design.md#exit-codes)). Output is the usual JSON plan with
`"action"`.

The Verb creates nothing, deletes nothing, never moves the branch
backwards, and cannot lose commits by construction. That makes it safe
for a plain `allow` Permission rule, granted per repo in exact form
(`Bash(gitw-trunk-sync <label>)`), where an agent is expected to keep the
human's local trunk current.

**Unspecified, to settle before build:** what the Verb does when the
local default branch is checked out in a linked worktree rather than the
primary checkout.

## Why never switch

The alternative spec, switch the current checkout to the default branch
and then fast-forward, breaks under universal isolation. The Verb runs
from an agent's worktree. Switching that worktree to the default branch
fails whenever the primary checkout holds it (git allows one checkout per
branch), and switching the primary checkout instead is exactly the
mutation of the human's copy the design forbids. That spec assumed agents
working in the primary checkout, which no longer happens. The Issue's
switch-then-fast-forward text is to be rewritten to match this proposal.

## Build bar

An agent-tooling PR: `cli/` implementation plus offline tests green under
Apple Python 3.9; adversarial-correctness and style/test review passes
before the maintainer merges; `use-git`'s The Verbs section gains the Verb and
the `index.md` Status row flips to `shipped` in the same PR; install with
`tooling-install` after merge.
