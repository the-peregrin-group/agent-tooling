# Beads trial: design

How Beads is set up in this repo and why. What is in place and what is
planned is in [index.md](index.md). The setup began as a trial whose
founding decision made Beads the repo's sole Issue Tracker, local-only,
without hooks, with GitHub Issues imported once and frozen (see
[ADR 0001](../../adr/0001-adopt-beads-for-the-tracker-trial.md), adopt
Beads as the sole work tracker for a local-only trial). The trial ended
with Beads kept for agent-swarmed work and long-lived work bound for forge
issues (see
[ADR 0011](../../adr/0011-beads-for-swarmed-work-forge-issues-for-long-lived-work.md),
Beads tracks agent-swarmed work).

## Principles

- **One writable home per Issue.** Today that means one Issue Tracker for
  the repo, Beads. When the long tail moves back to forge issues, Beads and
  forge issues will both hold Issues, but each Issue is writable in exactly
  one of them at a time.
- **No sync, in either direction.** Any cross-repo view of Issues is
  read-only aggregation on top of each repo's Issue Tracker. None is
  built.
- **Issue data stays private.** The database's one remote is a private
  repository on the maintainer's self-hosted Forgejo, never the public
  GitHub origin (see
  [ADR 0012](../../adr/0012-beads-data-syncs-to-private-forgejo-remote.md),
  Beads data syncs to a private Forgejo remote).

## The shape, and why

- **A private Dolt remote, configured outside tracked config.** A Beads
  push never passes through git (see
  [known behavior](index.md#beads-130-known-behavior)): neither git's
  pre-push hooks nor any gitw Verb sees it. This repo's pushes pass a
  pre-push content lint, and Issue content pushed through Dolt to the
  public origin would escape it. The remote is therefore a private Forgejo
  repository, which keeps Issue content off any public host so that it
  needs no lint path. Its address lives only in Dolt's own remote state, not
  in the tracked `config.yaml`, because this repo is public. `bdw` carries
  the push (see [`bdw`](../bdw/index.md)): after every write, and only to a
  host on its push-host allowlist. Backups go to a local directory outside
  the repo, and `backup.git-push: false` is pinned in the tracked config.
- **Tracked config, not a stealth init.** The three config files under
  `.beads/` are committed, beside the repo's `PRIME.md`: worktrees and
  fresh clones need the Issue prefix, and removing the trial is the
  deletion of those four files.
- **Hooks off.** Of Beads' git hooks only the `Executed-By:` commit trailer
  has value, and `gitw-commit` writes it instead (see
  [bdw](../bdw/index.md)).
- **Forgetting off.** Closed Issues are hidden from agents' default views,
  so the lossy forgetting commands buy nothing; they are denied, and
  nothing else in Beads deletes.
- **Import once, then leave GitHub idle.** The open GitHub issues were
  pulled into Beads one way (`bd github sync --pull-only`, token from the
  environment, never stored). GitHub has taken no Issue writes since, and
  takes none until the long tail moves back to forge issues
  (`agent-tooling-ze3`); GitHub Issues stays enabled so it can.

## Permission rules

`.claude/settings.json` holds the repo's Permission rules for Beads, in
deny, ask, and allow lists. They are use-bd's canonical Beads rule set
(`skills/use-bd/rules.json`, shipped with the Skill as data) plus a local
layer. `cli/repo_policy_test.py` is their spec: it expands the canonical
groups, adds the local layer, and requires the JSON to equal the result,
sorted. A hand-edited row with a typo would fail a deny open silently, so
equality with a generated set is the control.

- **Raw names denied.** Beads installs under two names (see
  [known behavior](index.md#beads-130-known-behavior)). Both, `bd` and
  `beads`, are denied outright, reads included: agents touch Beads only
  through `bdw`, as the [use-bd](../use-bd/index.md) Skill teaches, so the
  habit of typing `bd` fails at once. The rows below are all on `bdw`.
- **Denied** (every spelling: verb first, flag first, and a bare row for
  verbs that act with no arguments). The canonical set's deny groups are
  the full list; they cover the forgetting verbs (all of `compact`
  included, so even lossless Dolt garbage collection is a maintainer
  act), `delete` and the
  other destructive edits, every `dolt` subcommand, `init`, the tracker
  integrations (`github`, `gitlab`, `jira`, `linear`, `ado`, `notion`),
  `sync`, `remember`, `memories`, `recall`, `reclaim`, `metrics on`,
  `epic close-eligible` (it closes epics because their children closed),
  and `link` and the aliases `new`, `done`, and `hb`, so each operation
  has one spelling. The flags that claim the next Issue on the agent's
  behalf (`ready --claim`, `close --claim-next`, `close --continue`) are
  denied too. bd's `--actor` flag is denied in any position, and so is
  invocation by install path.
- **`reclaim` is denied, not asked for.** It reverts every claim with an
  expired lease to open. Sessions here can sit for hours waiting on a
  human, so a reclaim would take live work from them.
- **Asked for:** flags that delete, override another Actor's claim
  (`unclaim --force`, `update --assignee`), close Issues on the agent's
  behalf (`orphans --fix`, `human respond`), write files, or send data off
  the machine (`backup sync`); configuration and backup changes. The local
  layer adds shell indirections (`exec`, `env`, `sh -c`, `xargs`, `eval`,
  and similar) in this checkout, because they would hide a verb from
  prefix matching, and shell `rm` and `mv`.
- **Allowed:** reads and reversible writes on `bdw` (`create`, `update`,
  `close`, `note`, `heartbeat`, `dep`, `gate create`, `duplicate`,
  `supersede`, `defer`, and similar). `gate resolve` has no rule, so it
  prompts: resolving a human gate is the human's act.
- **Limits.** Prefix rules cannot see a verb inside a nested shell string,
  and the indirection list cannot be complete; the resulting auto-mode gap
  is listed under [Known gaps](index.md#known-gaps). The project file
  governs only sessions launched from a checkout whose checked-out branch
  contains it.

## Alternatives considered

### Beads beside GitHub Issues with a sync

**Description:** Keep GitHub Issues live and let `bd github sync`
reconcile the two.
**Rejection rationale:** Two writable sources of truth for one repo make
the trial's outcome unreadable and add an outbound write path. The freeze
costs one round of hand work at the trial's end, which is cheaper than any
conflict rule.

### A push-only sync at the trial's end

**Description:** At the trial's end, run one push-only `bd github sync`,
limited to the imported issues, so GitHub shows whatever Beads closed.
**Rejection rationale:** It would be the one outbound write outside the
Wrappers, and the Permission rules deny the `github` verb. With a small
number of imported issues, closing or refiling them by hand costs little and
keeps the no-sync rule whole.

### A roots-only bridge (parked, not rejected)

**Description:** GitHub owns parentless Issues and Beads owns everything
below them, with per-field ownership: content flows down, status flows up.
**Why parked:** The model is coherent but too rough-edged to reason about
with today's Beads. It needs three upstream changes: a roots-only publish
filter for `bd github sync`, per-field conflict ownership (Beads resolves
conflicts per whole issue), and the Beads Issue ID embedded in the GitHub
issue body. It can be reopened if Beads ships all three.

### Beads git hooks

**Description:** Let `bd init` install its git hooks, including the
`Executed-By:` commit trailer.
**Rejection rationale:** Only the trailer has value, and it conflicts with
`gitw-commit` owning the commit message. The hooks' install location would
also displace the repo's pre-push lint hook unless chained.

### Stealth init

**Description:** Keep the `.beads/` config out of git through
`.git/info/exclude`.
**Rejection rationale:** Worktrees and fresh clones could not resolve the
Issue prefix from per-checkout invisible state, and `bdw` and the
Permission rules make the trial visible in the tree anyway.
