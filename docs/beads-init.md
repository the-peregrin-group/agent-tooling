# Beads post-init checklist

What to undo after initializing Beads 1.3.0 in a new repo, so the tracker
stays local-only and only its config lands in git. This is a maintainer
procedure: agents are denied `init` and every `dolt` subcommand, and
`bd backup init` asks.

## Checklist

- [ ] Initialize without hooks or agent files:

  ```sh
  bd init --skip-hooks --skip-agents
  ```

  The command policy denies `init` to agents, so the maintainer runs it.
  Not checked against `bd init --help`; the flags are the ones in this
  repo's init commit.

- [ ] Undo init's commit, before any `config.yaml` edit, because a reset
  after the edits discards them. Init commits `.beads/README.md`, the three
  config files, and root `.gitignore` patterns (five on 1.3.0) straight to
  the current branch. Reset that commit away, mixed or soft, never hard,
  and land only the three config files by PR; drop the README and every
  root pattern init added (`.beads/.gitignore` covers what lives under
  `.beads/`; the gate lock gets its own root line, next item).

  ```sh
  git reset --mixed HEAD~1
  ```

  Never hard: the commit contains the three tracked config files, and
  with `metadata.json` gone from the working tree bd silently switches to
  an empty database (see the last item).

- [ ] Ignore the gate lock. Init keeps `.beads.gate.lock` at the repo root,
  beside `.beads/`, not inside it. Add one root `.gitignore` line:

  ```gitignore
  /.beads.gate.lock*
  ```

- [ ] Remove the sync remote. Init sets `sync.remote` in
  `.beads/config.yaml` to the git origin; delete the line (this repo keeps
  it commented out as a record). The Dolt repo holds its own copy, so the
  maintainer also runs, in the primary checkout:

  ```sh
  bd dolt remote remove origin
  ```

  Run here by the maintainer on 2026-09-25 (the epic's session-one note
  records it); agents are denied every `dolt` subcommand, so it was not
  checked against `bd dolt --help`. Untested: `bd config --help` lists
  `dolt.local-only`, a `config.yaml` key that skips wiring the remote at
  init; the open question is whether init overwrites a `config.yaml`
  written before it.

- [ ] Move the backup out of the repo. Init enables auto-backup because a
  git remote exists, and the first backup lands in `.beads/backup/` inside
  the repo. It is already ignored, so this is disk hygiene (no backups of
  backups), not git hygiene. Point it at a local directory outside the
  repo:

  ```sh
  bd backup init <local-path-outside-the-repo>
  bd backup sync
  ```

  Then delete the in-repo `.beads/backup/`. Alternatively, setting
  `enabled: false` under `backup:` in `config.yaml` (documented in that
  file's own comment block) skips backups entirely; this repo kept them,
  to a local path, per the trial plan.

- [ ] Pin `git-push: false` under `backup:` in `config.yaml`. It is the
  default, but stating it in the tracked file keeps backups on the machine
  in every clone:

  ```yaml
  backup:
    git-push: false
  ```

- [ ] Turn usage metrics off, once per machine: `bd metrics off`; check
  with `bd metrics`. The setting lives in `~/.config/bd/config.yaml`, so a
  second repo on the same machine inherits it.

- [ ] Ignore the backup destination records. `.beads/dolt-backup.json`
  stores the absolute path of the machine-local backup destination and
  must never be committed; a fresh init does not ignore it. Add these two
  lines to `.beads/.gitignore`:

  ```gitignore
  dolt-backup.json
  dolt-backup-state.json
  ```

- [ ] Allow the Dolt database name through the pre-push lint.
  `metadata.json` names the Dolt database as the issue prefix with
  underscores (`agent_tooling` here). A pre-push lint that flags
  respellings of the repo name must allow that string; this repo's did not
  until 2026-09-24.

- [ ] Never delete the tracked `.beads/` files, even to let a pull restore
  them. With `metadata.json` absent, bd prints a warning, falls back to a
  database named `beads`, creates it empty on the first read, and later
  writes miss the real database.

## The committed footprint

Three files under `.beads/`:

```text
.beads/.gitignore
.beads/config.yaml
.beads/metadata.json
```

Everything else under `.beads/` is local state and stays ignored. The
reasons behind the trial's shape are in
[ADR 0001](adr/0001-adopt-beads-for-the-tracker-trial.md).
