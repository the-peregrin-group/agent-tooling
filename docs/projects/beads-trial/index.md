# Beads trial

This repo tracks its own work in [Beads](https://github.com/gastownhall/beads)
(`bd`) as its only Issue Tracker, for a trial whose verdict decides whether
Beads stays. The trial asks whether the agent loop on Beads becomes routine
across sessions, and whether per-session identity shows up in claims and
history. The freeze has held since 2026-09-24:

- **Local-only.** Beads 1.3.0 keeps its database in an embedded Dolt store on
  the maintainer's machine. It has no Dolt remote and syncs nowhere. git
  tracks only three config files under `.beads/`: `.gitignore`,
  `config.yaml`, and `metadata.json`. `config.yaml` keeps `sync.remote`
  commented out as a record and pins `backup.git-push: false`, so backups
  stay on the machine in every clone.
- **GitHub Issues frozen.** The open GitHub issues were imported once, one
  way; each carries its GitHub URL as its external reference. No GitHub
  issue is filed, edited, relabeled, reprioritized, or closed while the
  freeze holds, and there is no sync in either direction. Pinned issue #18
  says so for anyone arriving from the web.
- **Agents go through [`bdw`](../bdw/index.md).** Reads may use `bd` or
  `bdw`; writes go through `bdw`, and a raw `bd` write prompts.
- **Permission rules** in `.claude/settings.json` decide which Beads calls
  run, prompt, or are refused. `cli/repo_policy_test.py` is their spec: its
  tuples generate the expected rules, and the test requires the JSON to
  equal them.
- **The loop**, written in `CLAUDE.md`: prime, ready, claim, file
  discovered work with a `discovered-from` dependency, close, and land the
  plane (close or unclaim everything held before the session ends). A
  `TODO` comment cites the Issue ID; a PR body names the Issue it lands
  (`Lands agent-tooling-xyz`).
- **Another repo** can repeat the setup with the maintainer's post-init
  checklist, [`docs/beads-init.md`](../../beads-init.md).

Why the trial has this shape, and the alternatives it rules out, is in
[design.md](design.md). How it closes and what follows is the ratified
[phase-two proposal](phase-two.md).

## Status

| Capability | State | Where |
|---|---|---|
| Beads as the sole, local-only Issue Tracker, with only its config committed | shipped | `.beads/`; [design.md](design.md) |
| One-way import of the open GitHub issues, then the freeze | shipped | `CLAUDE.md`; pinned issue #18 |
| Permission rules for `bd`, `bdw`, and `beads`, with a spec test that requires the JSON to equal its generated set | shipped | `.claude/settings.json`; `cli/repo_policy_test.py` |
| The agent loop through `bdw` | shipped | `CLAUDE.md`; [`bdw`](../bdw/index.md) |
| Post-init checklist for another repo | shipped | [`docs/beads-init.md`](../../beads-init.md) |
| Go/no-go verdict as an ADR, with the GitHub Issues wind-down or refile | planned | [phase-two.md](phase-two.md) (Issue to be filed) |
| Phase two: a second repo syncing Issues to its git remote | planned | [phase-two.md](phase-two.md) (Issue to be filed) |

### Known gaps

- Prefix rules cannot see a verb hidden inside a nested shell string, so
  the Permission rules are not safe in auto mode until a parsed-command deny
  hook lands (`agent-tooling-1790288522490-13-6d52b051`).
- A denied verb's `--help` is denied too, so agents cannot read the flags of
  the commands they document (Issue to be filed).
- A deny rule also matches a write whose Issue text names a denied verb or
  flag, so Issue text spells those in words (Issue to be filed).
- The Permission rules' spec docstring still calls the bare-call match of
  a trailing space-star unobserved (`agent-tooling-na2`).

## Beads 1.3.0 known behavior

Observed during the trial on Beads 1.3.0 (Homebrew), or documented by
Beads for that release; re-check on any upgrade. Behavior of the agent
harness is out of scope here.

**Install and init**

- Homebrew links the binary as both `bd` and `beads`.
- `bd init` configures a Dolt remote from the git origin. Unsetting
  `sync.remote` in `config.yaml` does not touch the Dolt repo state, which
  keeps its own copy of the remote.
- `bd init` turns on auto-backup when a git remote exists, writing the
  first backup to `.beads/backup/` inside the repo, and turns on usage
  metrics.
- `bd init` commits straight to the current branch: `.beads/README.md`, the
  three config files, and five root `.gitignore` patterns.
- The gate lock, `.beads.gate.lock`, lives at the repo root beside
  `.beads/`, not inside it.
- `.beads/dolt-backup.json` records the backup destination as an absolute
  path, and the shipped `.beads/.gitignore` does not ignore it.
- `metadata.json` names the Dolt database after the Issue prefix with
  underscores (`agent_tooling` here).
- The metrics opt-out is stored per user (`~/.config/bd/config.yaml`), not
  per repo.

**Database and data**

- With `metadata.json` missing, bd warns, falls back to a database named
  `beads`, creates it empty on the first read, and later writes miss the
  real database.
- Nothing deletes on its own under default config. The forgetting commands
  (`admin cleanup`, `prune`, `gc`, `admin compact`) are lossy; closed
  Issues are already hidden from the default views. `bd compact --dolt` is
  Dolt garbage collection and lossless.
- `bd config show` and `bd config get` disagree on the effective
  `backup.enabled`; `get` is right.
- Created and updated dates render in UTC.
- Imported Issues get long timestamp-and-hash Issue IDs and carry no
  history events from GitHub.

**Identity and workflow**

- Beads honors `BD_ACTOR` (it shows in `created_by`) although its help
  names only `BEADS_ACTOR`; bd's `--actor` flag overrides both.
- A claim carries a lease that expires unless heartbeated
  (`bd heartbeat`); `bd reclaim` reverts every claim with an expired lease
  to open.
- There is no "in review" status, and an unclaimed Issue reads as ready.
- `bd prime` tells agents to store memory with `bd remember` and not to
  push.

**Integrations and sync**

- `bd github sync` can push selected Issues (named Issue IDs, or one
  epic's subtree) but has no roots-only or label-gated publish filter. It
  resolves conflicts per whole issue, not per field, and does not embed the
  Issue ID in the GitHub issue body.
- Dolt pushes through its own git-protocol client, so a Beads push never
  passes through git: neither git's pre-push hooks nor gitw sees it.
