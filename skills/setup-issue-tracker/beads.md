# Setting up Beads

The Beads mechanics of `setup-issue-tracker`, read when its plan reaches a
step on Beads 1.3.0. The procedure, the plan, and the approval are the
skill's; this file says only how each step is done on Beads today, so that
the tracker stays local to the machine, only its config lands in version
control, and agents work it through `bdw` under the `use-bd` skill.

## Whose step is whose

Each step below says whether it is the agent's or the owner's. The line
follows the canonical Permission rules for Beads: they deny agents every
raw `bd` call, and through `bdw` they deny `init` and every `dolt`
subcommand and ask before configuration and backup changes.

- **The agent's:** reads and checks through `bdw`; drafting the repo's
  own files (`.beads/config.yaml` and the `.gitignore` files, `PRIME.md`,
  the Permission rules, the Tracker Schema copy) and the change that lands
  them through the repo's normal review; and turning bd's usage metrics
  off, the one machine-wide write the canonical rules allow.
- **The owner's:** every raw `bd` call (written `bd ...` below), rewriting
  the repo's history after init, creating a remote repository, and
  everything else on the machine outside the repo: the package manager,
  Machine Config, a backup directory, a scratch clone.

The plan says which owner steps it needs and in what order, so the owner
can run them where they fall.

## Before init

- [ ] Owner: `bd` and `bdw` are on PATH. `bdw` is installed machine-wide by
  the agent-tooling installer.
- [ ] Owner: pin bd in the package manager that installed it, so it
  changes only deliberately: `bdw` and `quirks.md` in the `use-bd` skill's
  directory are verified against one version, `bdw` refuses writes on any
  other, and an upgrade means re-verifying them.

## Init and its cleanup

- [ ] Owner: initialize without hooks or agent files:

  ```sh
  bd init --skip-hooks --skip-agents
  ```

- [ ] Owner: undo init's commit, before any `config.yaml` edit, because a
  reset after the edits discards them. Init commits `.beads/README.md`, the
  three config files, and root `.gitignore` patterns (five on 1.3.0)
  straight to the current branch. Reset that commit away, mixed or soft:

  ```sh
  git reset --mixed HEAD~1
  ```

  Never hard: the commit contains the three tracked config files, and
  with `metadata.json` gone from the working tree bd silently switches to
  an empty database.

- [ ] Agent: land only the three config files through review; drop the
  README and every root pattern init added (`.beads/.gitignore` covers
  what lives under `.beads/`; the gate lock gets its own root line, next
  item).

- [ ] Agent: ignore the gate lock. Init keeps `.beads.gate.lock` at the
  repo root, beside `.beads/`, not inside it. Add one root `.gitignore`
  line:

  ```gitignore
  /.beads.gate.lock*
  ```

- [ ] Remove the sync remote. Agent: init sets `sync.remote` in
  `.beads/config.yaml` to the repo's origin; delete the line, or comment
  it out as a record. Owner: the Dolt repo holds its own copy, so also
  run, in the primary checkout:

  ```sh
  bd dolt remote remove origin
  ```

  `bdw help config` lists `dolt.local-only`, a `config.yaml` key that
  skips wiring a Dolt sync remote during init. To take effect it must be in
  a `config.yaml` written before init, and whether init overwrites that
  file is untested. `bdw help dolt remote` confirms `remove <name>`.

- [ ] Owner, optionally: give the database a private Dolt remote, never one
  on a public origin; `bdw` then pushes to it after every write, but only
  to hosts on its push-host allowlist, and never to a remote that names the
  same repository as a git remote of the workspace. In the primary
  checkout:
  1. Create the remote repository with an initial commit (a README is
     enough): a Dolt push to a repository with no branches fails.
  2. Add it: `bd dolt remote add origin <url>`. This writes `sync.remote`
     into the tracked `config.yaml` and commits it to the current branch
     without asking, so check `git log` at once and drop that commit
     (and the line) before anything pushes it; Dolt keeps its own copy of
     the remote, which is all `bdw` needs. In a public repository the
     remote's address must never be committed.
  3. List the remote's host in the push-host allowlist, once per machine,
     in `~/.config/agent-tooling/bdw/config.toml` (or under
     `$XDG_CONFIG_HOME`): `push_hosts = ["<host>"]`, the host alone, with
     no scheme, user, port, or path. Until it does, every push is refused
     and `bdw` warns; the warning clears once a push `bdw` runs succeeds
     (the next write starts one), not after a `bd dolt push` by hand. The
     format is in the
     [bdw project doc](https://github.com/the-peregrin-group/agent-tooling/blob/main/docs/projects/bdw/index.md).
  4. Push once by hand (`bd dolt push --no-adopt`) to confirm access.
  5. Confirm a restore works, without touching the live database: clone
     the remote with the standalone dolt CLI into a scratch directory
     outside the repo (`dolt clone <url> <scratch-dir>`). In the clone,
     `dolt sql -q "select count(*) from issues"` must equal plain
     `bdw count` in the checkout, which shows the copy is complete. Then
     look up an Issue closed recently
     (`dolt sql -q "select id, status from issues where id = '<id>'"`) and
     confirm it reads closed, which shows the copy is current. Never use
     `bd init --remote <url>` for this: it persists `sync.remote` into the
     tracked `config.yaml`. Restoring over a checkout's own database is the
     owner's step too, done only after a real loss.

- [ ] Owner: move the backup out of the repo. Init enables auto-backup when
  a remote exists, and the first backup lands in `.beads/backup/` inside
  the repo (already ignored, so this is disk hygiene). Point it at a local
  directory outside the repo, then delete the in-repo `.beads/backup/`:

  ```sh
  bd backup init <local-path-outside-the-repo>
  bd backup sync
  ```

  Agent, alternatively: `enabled: false` under `backup:` in `config.yaml`
  skips backups entirely.

- [ ] Agent: pin `git-push: false` under `backup:` in `config.yaml`. It is
  the default; stating it in the tracked file keeps backups on the machine
  in every clone.

- [ ] Agent: turn usage metrics off, once per machine: `bdw metrics off`;
  check with `bdw metrics`. The setting lives in `~/.config/bd/config.yaml`,
  so every repo on the machine inherits it.

- [ ] Agent: ignore the backup destination records.
  `.beads/dolt-backup.json` stores the absolute path of the backup
  destination and must never be committed; a fresh init does not ignore
  it. Add to `.beads/.gitignore`:

  ```gitignore
  dolt-backup.json
  dolt-backup-state.json
  ```

- [ ] Owner: require a description, so every Issue says what it is. The
  setting lives in the database, not in `config.yaml`:

  ```sh
  bd config set create.require-description true
  ```

  Leave `validation.on-create` off: bd's section lint would refuse a
  bug filed before anyone knows how to reproduce it.

- [ ] Agent: if the repo has an outbound lint that flags respellings of its
  name, allow the Dolt database name: `metadata.json` names it after the
  Issue prefix with underscores (e.g., `agent_tooling`).

## Agent wiring

- [ ] Agent: commit `.beads/PRIME.md`. `bd prime` prints it instead of its
  default text, which contradicts `use-bd`. Keep it short: one line
  telling agents to load `/use-bd`, then the repo's conventions in words
  (where friction is logged, how a PR names the Issue it lands, how a
  `TODO` comment cites an Issue). The repo's kinds, priorities, and labels
  are not among them: they live in its Tracker Schema, `TRACKER.md` at the
  repo root, which `PRIME.md` points at. It states conventions and
  points; it never grants or denies an operation, because what agents may
  run is decided only by the reviewed Permission rules.
- [ ] Agent: add the canonical Permission rules for `bdw` to the repo's
  `.claude/settings.json`. They are `rules.json` in the `use-bd` skill's
  directory: reads and reversible writes allowed through `bdw`; raw `bd`
  and `beads` denied outright, reads included; the irreversible,
  off-machine, and record-falsifying verbs denied; and what steps around a
  safeguard (taking over a claim, forcing a close) asked for. Each of its
  `deny`, `ask`, and `allow` lists is a list of groups, and each group says
  why it exists and gives its rows outright (`rows`) or as `verbs` that
  fill in each of its `shapes` at `{v}`. Expand every group into the
  matching list of the repo's settings. No shipped tool does the expansion
  yet; agent-tooling's `canonical_rows()` in
  `cli/use_bd_rules_test_support.py` is the reference, so expand with a
  copy of it rather than by hand, since a hand-dropped spelling of a
  denied verb prompts instead of being refused. The repo may add rules of
  its own but keeps every canonical row. Shell indirections (`env *`,
  `sh -c *`, `xargs *`, `eval *`, and similar) hide a verb from prefix
  matching, so asking for them is worth considering too; they are not in
  the canonical set because they rule on every shell command, not only on
  Beads. Give the repo a spec test that checks its settings contain the
  canonical set; agent-tooling's `cli/repo_policy_test.py` is one to copy.
- [ ] Agent: the pointer in the repo's `CLAUDE.md` names `use-bd` as the
  skill to load.

## Tailoring the Tracker Schema to Beads

The agent drafts these changes to the copy, for the owner to approve with
the rest of the plan.

- [ ] Kind is bd's type, so each kind in the copy is a type bd accepts
  (`bdw types` lists them): `task`, which bd gives an Issue filed without a
  type, and `epic`, while `use-bd` says only an epic takes children,
  included. A default kind that is not a bd type is replaced by one or
  registered as a custom type; registering one changes bd's configuration,
  so it is the owner's. A bd type the repo does not use is said not to be
  a kind.
- [ ] bd has a fifth priority level, P4: declare it with a meaning and a
  staleness threshold, or say in the copy that it is not used.
- [ ] Until the repo's Beads holds the diagram's states as statuses, an
  Issue's state is recorded nowhere: no state labels.

## Verify

Agent: `bdw prime` prints the repo's `PRIME.md`, `bdw types` lists every
kind the copy declares, and `bdw config get create.require-description`
reads `true`.

## The committed footprint

Under `.beads/`: `.gitignore`, `config.yaml`, `metadata.json`, and
`PRIME.md`. Everything else under `.beads/` is local state and stays
ignored. Never delete the tracked files, even to let a pull restore them.
