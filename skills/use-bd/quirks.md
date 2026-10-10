# Beads 1.3.0: known behavior

Verified against bd 1.3.0 (`bdw version`). On any other version, treat
this list as unverified, and re-verify it when upgrading. Each entry says
what bd does and what to do about it.

## Claims and ready work

- **Claims carry a lease that only `heartbeat` extends.** A claim's lease
  lapses after a few minutes (the length is undocumented) unless renewed
  with `bdw heartbeat <id>`. A lapsed lease is inert until `reclaim` runs,
  which reverts every expired claim to open. Agents never run `reclaim`;
  where it is denied, a lapsed lease does nothing.
- **A contested claim's message steers to `reclaim`.** When `--claim`
  fails because someone else holds the Issue, bd suggests reclaiming it.
  Do not; ask whoever holds it, or the user.
- **`bdw ready` lists Branch Issues with open children.** Skip them by
  hand (`bdw show <id> --children`).
- **`epic close-eligible` closes epics because their children closed,**
  skipping the verifying pass. Never run it.
- **`ready` hides a status `bd` does not document:** `hooked`, alongside
  in_progress, blocked, and deferred.
- **There is no "in review" status.** An unclaimed open Issue reads as
  ready work. Block work waiting on a human with a gate (see SKILL.md).
- **`close --claim-next`, `close --continue`, and `ready --claim` claim
  the next Issue for you,** skipping the choice of what to work on. Claim
  explicitly instead.

## Filing and editing

- **Bare `dep add` creates a blocking edge,** and warns about it only on a
  terminal, so an agent never sees the warning. Always pass `--type`.
- **`dep add <a> <b>` means a depends on b** (b blocks a).
- **`update --notes` replaces the notes;** `--append-notes` and
  `note --file` append.
- **Children inherit their parent's labels** unless filed with
  `--no-inherit-labels`.
- **`-f` means different things:** a markdown batch file on `create`,
  `--force` on `close`.
- **No file form** for the title, acceptance criteria, replacing notes,
  or the reasons on `unclaim`, `gate create`, and `gate resolve`.
- **`list -s` repeated keeps only the last value;** pass a comma list.
- **`search` matches titles and IDs only;** use
  `list --desc-contains` for descriptions.
- **`find-duplicates --method=ai` sends Issue text to an external model.**
  The default (`mechanical`) stays on the machine.
- **`bdw children <id>` includes closed children.**
- **`list` hides gates** unless given `--include-gates`.

## Reading output

- **Dates in `bd show` are UTC.**
- **Issues imported from GitHub** have long timestamp-and-hash IDs and
  none of their GitHub history.

## Help and denied verbs

- **`bd help <verb>` works for a denied verb.** To read a denied verb's
  flags, use `bdw help <verb>`; running the verb with `--help` matches
  its deny rule.

## Prime and memories

- **`bd prime` prints `.beads/PRIME.md` instead of its default text** when
  the file exists, but still appends persistent memories (`bd remember`).
  Memories stay in the harness's own memory files, never in Beads.
- **The default prime text contradicts local policy** (raw `bd` writes,
  `bd remember`, not pushing); that is why a repo commits its own
  `PRIME.md`.

## Database

- **A missing `.beads/metadata.json` silently switches databases.** bd
  falls back to an empty database named `beads`, and later writes miss the
  real one. Never delete the tracked `.beads/` files, even to let a pull
  restore them.
- **Nothing deletes on its own** under the default config. `admin
  cleanup`, `prune`, `gc`, and `admin compact` lose data.
- **`config show` and `config get` can disagree;** `config get` is right.
- **A Beads push bypasses the repo's own hooks:** Dolt pushes over its own
  client, so pre-push hooks never see it.
