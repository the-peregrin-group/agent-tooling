# Beads post-init checklist

What to undo after initializing Beads 1.3.0 in a new repo, so the tracker
stays local-only and only its config lands in git. Each item is one side
effect of init and its reversal.

## After init

- [ ] Initialize without hooks or agent files:

  ```sh
  bd init --skip-hooks --skip-agents
  ```

  The command policy denies `init`, including its help, so the maintainer
  runs it. The command is as recorded in this repo's init commit; it was
  not re-verified against its help.

- [ ] Remove the sync remote. Init sets `sync.remote` to the git origin
  without being asked. Delete the `sync.remote` line from
  `.beads/config.yaml` (agent-tooling keeps it commented out as a record).
  The Dolt repo keeps its own copy of the remote, so separately, as the
  maintainer in the primary checkout (agents are denied every `dolt`
  subcommand; not verified against its help for the same reason):

  ```sh
  bd dolt remote remove origin
  ```

  Untried alternative: `bd config --help` lists a `dolt.local-only` key
  that skips wiring the sync remote during init. Whether it can be set
  before init has not been tested.

- [ ] Move the backup out of the repo. Auto-backup turns itself on in
  embedded mode whenever a git remote exists, and the first backup lands in
  `.beads/backup/` inside the repo. Point it at a local directory outside
  the repo, then move or remove the in-repo copy by hand:

  ```sh
  bd backup init <local-path-outside-the-repo>
  bd backup sync
  ```

  Pin git push of backups off in `.beads/config.yaml`, so the rule is in
  the tracked file rather than a default:

  ```yaml
  backup:
    git-push: false
  ```

- [ ] Turn usage metrics off (on by default after init):

  ```sh
  bd metrics off
  ```

- [ ] Undo init's commit. Init makes a raw commit on the current branch
  adding `.beads/README.md` and five root `.gitignore` patterns. The
  maintainer resets it off that branch so the files land by PR instead.
  On the PR branch, drop `.beads/README.md` and the five root patterns
  (`.beads/.gitignore` already covers everything under `.beads/`).

- [ ] Ignore the gate lock. Init keeps `.beads.gate.lock` at the repo root,
  beside `.beads/`, not inside it. Add one root `.gitignore` line:

  ```gitignore
  /.beads.gate.lock*
  ```

- [ ] Keep `.beads/dolt-backup.json` out of git. It records the backup
  destination as an absolute home path and must never be committed. It is
  untracked; make sure `.beads/.gitignore` lists it and its sibling:

  ```gitignore
  dolt-backup.json
  dolt-backup-state.json
  ```

- [ ] Never delete the tracked `.beads/` config files, even briefly (to let
  a pull restore them, say). With `metadata.json` absent, bd warns and
  silently falls back to a database named `beads`, creating an empty one on
  the first read, and writes then miss the real database.

## The committed footprint

Three files under `.beads/`, plus the one root ignore line for the gate
lock:

```text
.beads/.gitignore
.beads/config.yaml
.beads/metadata.json
```

Everything else under `.beads/` is local state and stays ignored. Two
notes for the command policy: Homebrew links the binary as both `bd` and
`beads`, so every policy row must guard both names; and a project
`.claude/settings.json` applies only to sessions launched from a checkout
whose checked-out branch contains it, so the policy is not enforced until
its PR merges. The reasons behind the trial's shape are in
[ADR 0001](adr/0001-adopt-beads-for-the-tracker-trial.md).
