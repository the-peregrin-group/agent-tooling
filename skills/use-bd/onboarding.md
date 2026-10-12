# Onboarding a repo to Beads

Setting Beads 1.3.0 up in a new repo so that its Issue Tracker stays
local to the machine, only its config lands in version control, and agents
work it through `bdw` under this skill. This is a maintainer procedure,
and the Permission rules suggested below deny agents `init` and every
`dolt` subcommand, so a human runs or approves each step. An agent may draft
the files (`PRIME.md`, the Permission rules) and the change that lands
them.

## Before init

- [ ] `bd` and `bdw` are on PATH. `bdw` is installed machine-wide by the
  agent-tooling installer.
- [ ] Pin bd in the package manager that installed it, so it changes
  only deliberately: `bdw` and `quirks.md` are verified against one
  version, `bdw` refuses writes on any other, and an upgrade means
  re-verifying them.

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
  `.beads/config.yaml` to the repo's origin; delete the line, or comment
  it out as a record. The Dolt
  repo holds its own copy, so also run, in the primary checkout:

  ```sh
  bd dolt remote remove origin
  ```

  `bdw help config` lists `dolt.local-only`, a `config.yaml` key that
  skips wiring a Dolt sync remote during init. To take effect it must be in
  a `config.yaml` written before init, and whether init overwrites that
  file is untested. `bdw help dolt remote` confirms `remove <name>`.

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
  lands, how a `TODO` comment cites an Issue). It states conventions and
  points; it never grants or denies an operation, because what agents may
  run is decided only by the reviewed Permission rules.
- [ ] Add the canonical Permission rules for `bdw` to the repo's
  `.claude/settings.json`. They ship beside this file as `rules.json`:
  reads and reversible writes allowed through `bdw`; raw `bd` and `beads`
  denied outright, reads included; the irreversible, off-machine, and
  record-falsifying verbs denied; and what steps around a safeguard
  (taking over a claim, forcing a close) asked for. Each of its `deny`,
  `ask`, and `allow` lists is a list of groups, and each group says why it
  exists and gives its rows outright (`rows`) or as `verbs` that fill in
  each of its `shapes` at `{v}`. Expand every group into the matching
  list of the repo's settings. No shipped tool does the expansion yet
  (agent-tooling-j6x); agent-tooling's `canonical_rows()` in
  `cli/use_bd_rules_test_support.py` is the reference, so expand with a
  copy of it rather than by hand, since a hand-dropped spelling of a
  denied verb prompts instead of being refused. The repo may add rules of
  its own but keeps every canonical row. Shell indirections (`env *`,
  `sh -c *`, `xargs *`, `eval *`, and similar) hide a verb from prefix
  matching, so asking for them is worth considering too; they are not in
  the canonical set because they rule on every shell command, not only on
  Beads. Give
  the repo a spec test that checks its settings contain the canonical set;
  agent-tooling's `cli/repo_policy_test.py` is one to copy.
- [ ] Point the repo's `CLAUDE.md` at this skill rather than restating
  Beads procedure: "Issues are tracked in Beads; load `/use-bd`."

## The committed footprint

Under `.beads/`: `.gitignore`, `config.yaml`, `metadata.json`, and
`PRIME.md`. Everything else under `.beads/` is local state and stays
ignored. Never delete the tracked files, even to let a pull restore them.
