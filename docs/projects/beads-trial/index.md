# Beads trial

This repo tracks its own work in [Beads](https://github.com/gastownhall/beads)
(`bd`) as its only Issue Tracker. That began on 2026-09-24 as a trial, and
the trial ended on 2026-10-16 with Beads kept: Beads tracks the work agents
swarm, and long-lived, low-churn, or human-driven work belongs in forge
issues (GitHub or Forgejo Issues). This repo stays on Beads alone until its
long tail can move back to forge issues (see
[ADR 0011](../../adr/0011-beads-for-swarmed-work-forge-issues-for-long-lived-work.md),
Beads tracks agent-swarmed work). What makes Beads work here is the layer
that lets agents cooperate on it: the [use-bd](../use-bd/index.md) Skill,
[`bdw`](../bdw/index.md), and the Permission rules.

- **Local-only, for now.** Beads 1.3.0 keeps its database in an embedded
  Dolt store on the maintainer's machine. It has no Dolt remote and syncs
  nowhere; a private remote on the maintainer's self-hosted Forgejo is
  planned (see
  [ADR 0012](../../adr/0012-beads-data-syncs-to-private-forgejo-remote.md),
  Beads data syncs to a private Forgejo remote). git tracks only four files
  under `.beads/`: the config files `.gitignore`, `config.yaml`, and
  `metadata.json`, and `PRIME.md`, the repo's Beads conventions that
  `bd prime` prints. `config.yaml` keeps `sync.remote` commented out as a
  record and pins `backup.git-push: false`, so backups never travel over
  git.
- **GitHub Issues kept, but idle.** The open GitHub issues were imported
  into Beads once, one way, on 2026-09-24; each Beads copy carries its
  GitHub URL as its external reference. GitHub Issues stays enabled and the
  imported issues stay open there as stale copies: Beads holds the live
  versions, nothing is filed or changed on GitHub until the long tail moves
  back, and there is no sync in either direction. Pinned issue #18 says so
  for anyone arriving from the web.
- **Agents go through [`bdw`](../bdw/index.md).** Raw `bd` and `beads`
  are denied, reads included.
- **Permission rules** in `.claude/settings.json` decide which Beads calls
  run, prompt, or are refused. `cli/repo_policy_test.py` is their spec: it
  generates the expected rules from use-bd's canonical rule set
  (`skills/use-bd/rules.json`) plus a local layer, and requires the JSON to
  equal them.
- **The loop** and everything else about working Beads is taught by the
  [use-bd](../use-bd/index.md) Skill; this repo's conventions (labels, the
  friction log, `TODO` citations) are in `.beads/PRIME.md`, and a PR body
  names the Issue it lands (`Lands agent-tooling-xyz`).
- **Another repo** can repeat the setup with use-bd's onboarding
  checklist, `skills/use-bd/onboarding.md`.

Why the setup has this shape, and the alternatives it rules out, is in
[design.md](design.md). The [phase-two proposal](phase-two.md), dated
2026-10-01, records the plan for closing the trial that ADR 0011 replaced.

## Status

| Capability | State | Where |
|---|---|---|
| Beads as the sole, local-only Issue Tracker, with only its config committed | shipped | `.beads/`; [design.md](design.md) |
| One-way import of the open GitHub issues, with GitHub Issues kept but idle | shipped | `CLAUDE.md`; pinned issue #18 |
| Permission rules for `bd`, `bdw`, and `beads`, with a spec test that requires the JSON to equal its generated set | shipped | `.claude/settings.json`; `cli/repo_policy_test.py` |
| Trial verdict: Beads kept for agent-swarmed work | shipped | [ADR 0011](../../adr/0011-beads-for-swarmed-work-forge-issues-for-long-lived-work.md) |
| A private Dolt remote on the maintainer's self-hosted Forgejo | planned | [ADR 0012](../../adr/0012-beads-data-syncs-to-private-forgejo-remote.md); `agent-tooling-cy3` |
| Beads and forge issues together, so the long tail moves back to forge issues while swarms check work out to Beads | planned | [ADR 0011](../../adr/0011-beads-for-swarmed-work-forge-issues-for-long-lived-work.md); `agent-tooling-ze3` |
| Phase two: a second repo syncing its Issues before a verdict | retired | [ADR 0011](../../adr/0011-beads-for-swarmed-work-forge-issues-for-long-lived-work.md) |

### Known gaps

- The database and its backups live only on the maintainer's machine, so
  losing that machine loses the Issue Tracker, until the private remote
  lands (`agent-tooling-cy3`).
- Prefix rules cannot see a verb hidden inside a nested shell string, so
  the Permission rules are not safe in auto mode until a parsed-command deny
  hook lands (`agent-tooling-1790288522490-13-6d52b051`).
- A deny rule also matches a write whose Issue text names a denied verb or
  flag, so Issue text spells those in words (`agent-tooling-9nx`).

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
- `bd dolt remote add` writes `sync.remote` into the tracked `config.yaml`
  and commits it, with any other pending change to that file, to the
  current git branch without asking (as "bd: update sync.remote").
- A Dolt push to a git repository with no branches fails ("initialize the
  repository with an initial branch/commit first"). Once it succeeds, the
  repository holds `refs/dolt/data` and a `__dolt_remote_info__` branch.
- With no Dolt remote configured, `bd dolt push` offers to adopt one
  derived from the git origin; `--no-adopt` or `BD_NO_REMOTE_ADOPT=1`
  disables that.
- In embedded mode bd does not push after writes, even with `sync.remote`
  set. Environment variables `BD_SYNC_REMOTE` and `BD_NO_PUSH` set
  `sync.remote` and `no-push` without touching tracked config (the
  `BEADS_` prefix does not, for these keys).
