# Beads in agent-tooling

**Agents: load the `/use-bd` skill now,** before your next `bdw` call. It
is the operating manual; this file holds only this repo's conventions.

- **Issue Tracker.** Beads is this repo's only Issue Tracker (see
  `docs/projects/beads-trial/index.md`; why GitHub Issues takes no work is
  in `CLAUDE.md`). The database is local to the maintainer's machine, and
  `bdw` pushes it after every write to a private Dolt remote; never push it
  by hand.
- **Tracker Schema.** `TRACKER.md` at the repo root declares this repo's
  Issue Kinds, Issue Priorities, Issue Labels, and Issue State Diagram, and
  says what the Beads status does and does not record. Read it before
  filing, classifying, or moving an Issue.
- **Friction log.** Append friction, surprises, and refusals to
  `agent-tooling-w7p.4` with `bdw note agent-tooling-w7p.4 --file=<path>`:
  a dated entry, numbered after the last one in its notes
  (`bdw show agent-tooling-w7p.4`).
- **Known gaps at filing.** A bug or omission against a shipped capability
  gets its Known-gaps line, citing the new Issue ID, when you file it (rules
  in `CLAUDE.md`, Documentation).
- **`TODO` comments** cite the Issue ID (`TODO(agent-tooling-xyz)`).
- **Imported Issues** carry their GitHub issue URL as the external
  reference. Some still carry a GitHub type label, which the Tracker Schema
  does not declare: never add one, and `agent-tooling-aio.7` (convert the
  imported type labels to Beads types) retires them.
