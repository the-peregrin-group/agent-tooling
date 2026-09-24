---
date: 2026-09-24
---

# Adopt Beads as the sole work tracker for a local-only trial

**Context:** Agent-driven work needs a tracker that agents can read and write from any session without a forge round-trip, and running a second tracker beside GitHub Issues, or syncing between them, would make the trial's question unanswerable. Beads 1.3.0 keeps its database in an embedded Dolt store under `.beads/`, ships git hooks and a Dolt remote by default, and with default config deletes nothing on its own.
**Decision:** Beads is this repo's only tracker, local-only and without hooks, until a go/no-go is recorded on pinned issue #18, with the open GitHub issues imported once and then frozen and no sync in either direction.
**Rationale:** One tracker per repo with nothing leaving the machine keeps the trial readable and its perimeter trivially safe, and closed beads are hidden from agents by default so forgetting buys nothing.

**Gotchas:**

- The forgetting commands (`admin cleanup`, `prune`, `gc`, `admin compact`) never run; the command policy denies them and nothing else deletes.
- `bd init` on 1.3.0 also configures a Dolt remote from the git origin, turns on auto-backup and usage metrics, commits `.beads/` files to the current branch, and keeps `.beads.gate.lock` beside `.beads/` rather than inside it. Each was reversed or ignored deliberately; the init commit lists them. Unsetting `sync.remote` in `config.yaml` does not touch the Dolt repo state, which keeps its own copy of the remote; that copy is a hand step, `bd dolt remote remove origin`, run by the maintainer in the primary checkout because agents are denied every `dolt` subcommand.
- The command policy is a `.claude/settings.json` deny, ask, and allow list, with `cli/repo_policy_test.py` as its spec, because no parsed-command hook exists yet; that hook (imported issue #16) is the planned tightening. Prefix rules cannot see a verb hidden inside a nested shell string, and the ask rows on `exec`, `env`, `sh -c`, `xargs`, and friends are enumerative, so the policy is not safe in auto mode until the hook lands. Those ask rows prompt for every such wrapper in this checkout, not only Beads calls; that is deliberate. The project file applies only to sessions launched from a checkout whose checked-out branch contains it.
- The `Executed-By` commit trailer is ported into `gitw-commit` by the shim PR, not by this one; until that lands, commits carry no actor.
- On no-go, beads closed during the trial have diverged from GitHub, and the beads that still matter are refiled by hand.

## Alternatives Considered

### Beads beside GitHub Issues with a sync

**Description:** Keep GitHub Issues live and let `bd github sync` reconcile the two.
**Rejection rationale:** Two writable sources of truth for one repo make the trial's outcome unreadable and the perimeter non-trivial; the freeze costs one hand refile on no-go, which is cheaper than any conflict rule.

### Beads git hooks

**Description:** Let `bd init` install its five git hooks, including the `Executed-By` commit trailer.
**Rejection rationale:** Only the trailer has value, it conflicts with `gitw-commit` owning the commit message, and the hook install location would displace the outbound-lint pre-push hook unless chained; the trailer is ported into `gitw-commit` by the shim PR instead.

### Stealth init

**Description:** Keep the `.beads/` config out of git via `.git/info/exclude`.
**Rejection rationale:** Per-checkout invisible state that worktrees and fresh clones cannot resolve the prefix from, and the shim and policy make the trial visible in the tree anyway; the committed footprint is three config files and a rip-out is their deletion.
