# Onboarding a repo to Beads

Setting Beads 1.3.0 up in a new repo so that its Issue Tracker stays
local to the machine, only its config lands in version control, and agents
work it through `bdw` under this skill. This is a maintainer procedure:
agents are denied `init` and every `dolt` subcommand, and the backup
commands ask, so a human runs or approves each step. An agent may draft
the files (`PRIME.md`, the Permission rules) and the change that lands
them.

## Before init

- [ ] `bd` and `bdw` are on PATH. `bdw` is installed machine-wide by the
  agent-tooling installer.
- [ ] Pin bd in the package manager that installed it, so it changes
  only deliberately: `bdw` and `quirks.md` are verified against one
  version, and an upgrade means re-verifying them.

## Init and its cleanup

- [ ] Initialize without hooks or agent files:

  ```sh
  bd init --skip-hooks --skip-agents
  ```

- [ ] Undo init's commit, before any `config.yaml` edit, because a reset
  after the edits discards them. Init commits `.beads/README.md`, the three
  config files, and root `.gitignore` patterns (five on 1.3.0) straight to
  the current branch. Reset that commit away, mixed or soft, and land only
  the three config files through review; drop the README and every root
  pattern init added (`.beads/.gitignore` covers what lives under
  `.beads/`; the gate lock gets its own root line, next item).

  ```sh
  git reset --mixed HEAD~1
  ```

  Never hard: the commit contains the three tracked config files, and
  with `metadata.json` gone from the working tree bd silently switches to
  an empty database.

- [ ] Ignore the gate lock. Init keeps `.beads.gate.lock` at the repo root,
  beside `.beads/`, not inside it. Add one root `.gitignore` line:

  ```gitignore
  /.beads.gate.lock*
  ```

- [ ] Remove the sync remote. Init sets `sync.remote` in
  `.beads/config.yaml` to the repo's origin; delete the line. The Dolt
  repo holds its own copy, so also run, in the primary checkout:

  ```sh
  bd dolt remote remove origin
  ```

  Untested: `bd config --help` lists `dolt.local-only`, a `config.yaml`
  key that skips wiring the remote at init; whether init overwrites a
  `config.yaml` written before it is open.

- [ ] Move the backup out of the repo. Init enables auto-backup when a
  remote exists, and the first backup lands in `.beads/backup/` inside
  the repo (already ignored, so this is disk hygiene). Point it at a local
  directory outside the repo, then delete the in-repo `.beads/backup/`:

  ```sh
  bd backup init <local-path-outside-the-repo>
  bd backup sync
  ```

  Alternatively, `enabled: false` under `backup:` in `config.yaml` skips
  backups entirely.

- [ ] Pin `git-push: false` under `backup:` in `config.yaml`. It is the
  default; stating it in the tracked file keeps backups on the machine in
  every clone.

- [ ] Turn usage metrics off, once per machine: `bd metrics off`; check
  with `bd metrics`. The setting lives in `~/.config/bd/config.yaml`, so
  every repo on the machine inherits it.

- [ ] Ignore the backup destination records. `.beads/dolt-backup.json`
  stores the absolute path of the backup destination and must never be
  committed; a fresh init does not ignore it. Add to `.beads/.gitignore`:

  ```gitignore
  dolt-backup.json
  dolt-backup-state.json
  ```

- [ ] Require a description, so every Issue says what it is. The setting
  lives in the database, not in `config.yaml`:

  ```sh
  bd config set create.require-description true
  ```

  Leave `validation.on-create` off: bd's section lint would refuse a
  bug filed before anyone knows how to reproduce it.

- [ ] If the repo has an outbound lint that flags respellings of its name,
  allow the Dolt database name: `metadata.json` names it after the Issue
  prefix with underscores (e.g., `agent_tooling`).

## Agent wiring

- [ ] Commit `.beads/PRIME.md`. `bd prime` prints it instead of its
  default text, which contradicts this skill. Keep it short: one line
  telling agents to load `/use-bd`, then the repo's conventions in words
  (its labels, where friction is logged, how a PR names the Issue it
  lands, how a `TODO` comment cites an Issue). It describes and points;
  it never permits or forbids anything, because what agents may do is
  decided only by the reviewed Permission rules.
- [ ] Add Permission rules for `bdw` to the repo's `.claude/settings.json`:
  reads and reversible writes allowed through `bdw`, raw `bd` and `beads`
  writes asked for or denied, and the irreversible, off-machine, and
  record-falsifying verbs denied. Until use-bd ships its canonical rule
  set, agent-tooling's own `.claude/settings.json` and the spec that
  generates it (`cli/repo_policy_test.py`) are the model to copy.
- [ ] Point the repo's `CLAUDE.md` at this skill rather than restating
  Beads procedure: "Issues are tracked in Beads; load `/use-bd`."

## The committed footprint

Under `.beads/`: `.gitignore`, `config.yaml`, `metadata.json`, and
`PRIME.md`. Everything else under `.beads/` is local state and stays
ignored. Never delete the tracked files, even to let a pull restore them.
