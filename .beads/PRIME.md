# Beads in agent-tooling

**Agents: load the `/use-bd` skill now,** before your next `bdw` call. It
is the operating manual; this file holds only this repo's conventions.

- **Trial.** Beads is this repo's only Issue Tracker during a trial (see
  `docs/projects/beads-trial/index.md`; the GitHub Issues freeze is in
  `CLAUDE.md`). The database is local to the maintainer's machine and
  syncs nowhere.
- **Labels.** Area labels in use: `area:dev-x`, `area:installer`,
  `area:skills`, `area:wrappers`. Issues imported from GitHub also carry
  their old type labels (`bug`, `debt`, `feature`, `improvement`, `meta`);
  do not add those to new Issues, since kind goes in the type field.
- **Friction log.** Append friction, surprises, and refusals to
  `agent-tooling-w7p.4` with `bdw note agent-tooling-w7p.4 --file=<path>`:
  a dated, numbered entry that names the use-bd success criterion it bears
  on (`docs/projects/use-bd/v1-proposal.md`, "Success criteria"), or
  "none" when it fits no criterion.
- **`TODO` comments** cite the Issue ID (`TODO(agent-tooling-xyz)`).
- **Imported Issues** carry their GitHub issue URL as the external
  reference.
