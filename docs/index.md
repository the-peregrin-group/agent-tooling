# Documentation

The front door to this repo's documentation. `README.md` is the bootstrap
and the install model; `LEXICON.md` is the vocabulary; `docs/adr/` holds the
decisions. Everything else lives under `docs/projects/`, one directory per
project, in the shape `CLAUDE.md` ("Documentation") prescribes: a living
`index.md` with a Status table, an optional living `design.md`, and dated
targeted docs.

## Projects

### Wrappers and the Installer

- [fjw](projects/fjw/index.md): the Wrapper over a Forgejo forge; its
  [design](projects/fjw/design.md) and the issue-verbs proposal.
- [gitw](projects/gitw/index.md): the Wrapper over git; its
  [design](projects/gitw/design.md), the trunk-sync proposal, and the
  read-rule audit.
- [installer](projects/installer/index.md): `tooling-install`, the
  Installer that ships Source repos' tooling into Install Targets; its
  [design](projects/installer/design.md).

The other Wrappers (ghw, bdw) are documented today by their operating
manuals (`skills/use-github`, `CLAUDE.md` for bdw) and the docstrings in
`cli/`. Their project directories land with the documentation migration
that Issue `agent-tooling-bpj` gates.

### Understanding

The `home-in`, `use-adrs`, and `use-lexicon` Skills form one project: they
derive from a single original and share one contract (home-in clarifies a
problem space while capturing lexicon entries and ADRs through the other
two; they are split only so each can be invoked alone).

- [home-in: design](projects/understanding/home-in-design.md): the design
  of the home-in Skill and the two capture Skills it drives, as of
  2026-09-30.

### Other

- [Beads post-init checklist](beads-init.md): the maintainer's procedure
  for initializing Beads in another repo.

## Exit-code contract

Every Wrapper reports through one taxonomy (`cli/lib/plan.py`); callers
branch on it, unattended callers especially.

| Code | Meaning | Unattended caller |
|---|---|---|
| `0` | success, including a converged no-op | proceed |
| `1` | unclassified runtime failure | stop and report |
| `2` | usage error, or a policy refusal at argument-parse time | fix the call |
| `3` | not found | treat as an answer, not an error |
| `4` | validation or policy refusal past parse time | a caller bug: never retry unchanged, never work around it with the raw tool |
| `5` | auth failure; roster and configuration problems map here too | abort and flag the deployment |
| `6` | network failure | the one retryable class |

One nuance to `4`: `gitw-rebase` exits 4 on a conflict stop, which is
deliberate, resumable state (its JSON says `"action": "conflict"`), not a
caller bug.

Codes 3 to 6 were carved out of 1's space when the fjw Verbs arrived, so
families adopt them at their own pace. What each family implements today:

| Family | Codes implemented |
|---|---|
| `gitw-*` (7 Verbs) | the full taxonomy, 0 to 6 |
| `fjw-*` (7 Verbs) | the full taxonomy, 0 to 6 (HTTP 401/403 → 5, 404 → 3, other HTTP → 1, connection or timeout → 6, config error → 5, 409 on create → 4) |
| `ghw-*` (12 Verbs) | 0, 1, 2 only: every `gh` failure is 1, every refusal is 2; adopting 3 to 6 is planned and is a contract change for callers keying on 2 |
| `triage-*` (reference wrappers of `triage-issues`) | 0, 1, 2 only |
| `bdw` | 4 on bd's own `--actor` flag, 3 when no `bd` is on PATH, 1 when the exec fails; otherwise bd's own exit code, untouched |
| `tooling-install` | its own set: 0 in sync, 1 drift, 2 usage, 4 refused |

Each family's Skill and `design.md` state the family's codes and link here.
