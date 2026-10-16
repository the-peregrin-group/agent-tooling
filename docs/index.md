# Documentation

The front door to this repo's documentation. `README.md` is the bootstrap
and the install model; `LEXICON.md` is the vocabulary; `docs/adr/` holds the
decisions. Everything else lives under `docs/projects/`, one directory per
project, in the shape `CLAUDE.md` ("Documentation") prescribes: a living
`index.md` with a Status table, an optional living `design.md`, and dated
targeted docs. The one exception is a dated audit that spans several
projects, which lives under `docs/audits/`.

## Projects

### Wrappers and the Installer

- [bdw](projects/bdw/index.md): the Wrapper over Beads.
- [fjw](projects/fjw/index.md): the Wrapper over a Forgejo forge; its
  [design](projects/fjw/design.md) and the issue-verbs proposal.
- [ghw](projects/ghw/index.md): the Wrapper over GitHub, with the triage
  reference wrappers; its [design](projects/ghw/design.md) and the
  triage-library-rebase proposal.
- [gitw](projects/gitw/index.md): the Wrapper over git; its
  [design](projects/gitw/design.md), the trunk-sync proposal, and the
  read-rule audit.
- [installer](projects/installer/index.md): `tooling-install`, the
  Installer that ships Source repos' tooling into Install Targets; its
  [design](projects/installer/design.md).

### Tracking work

- [beads-trial](projects/beads-trial/index.md): the in-repo trial of
  Beads as the Issue Tracker; its [design](projects/beads-trial/design.md)
  and the phase-two proposal.
- [use-bd](projects/use-bd/index.md): the Skill that is the operating
  manual for Beads through `bdw`, including onboarding a new repo; its
  version-one proposal.

### Skills

- [understanding](projects/understanding/index.md): the `home-in`,
  `use-adrs`, and `use-lexicon` Skills, one project because home-in
  captures lexicon entries and ADRs through the other two; its
  [home-in design](projects/understanding/home-in-design.md), as of
  2026-09-30.
- [handoff](projects/handoff/index.md): the Skill that writes a Handoff.
- [refine-state-doc](projects/refine-state-doc/index.md): the guide for
  writing and refining State docs.

## Cross-cutting audits

Dated audits that span several projects live under `audits/`; like every
dated doc, each is never updated after its date.

- [The agent-versus-human line](audits/2026-10-11-agent-versus-human-line.md),
  as of 2026-10-11: every point where a Skill or Wrapper decides what an
  agent may do on its own and what needs a human, the principles behind
  them, and the inconsistencies awaiting the maintainer's decisions.

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
| `5` | roster/auth/config (deployment): a Roster, authentication, or configuration failure, fixed by the deployment | abort and flag the deployment |
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
| `ghw-*` (12 Verbs) | the full taxonomy, 0 to 6: `gh` failures classify (not found → 3, auth or a `gh` below `ghw-issue-link`'s version floor → 5, network or timeout → 6, anything unrecognized → 1; the create and comment Verbs and `ghw-board-sync new` (project creation) report a timeout or reset as 1, since the write may have landed, and `ghw-issue-close` reports any network failure during the close as 1, since the comment is posted first); a policy refusal past parse time (label contract, merge gates, an unlinked board, a missing branch) → 4 |
| `triage-*` (reference wrappers of `triage-issues`) | 0, 1, 2 only |
| `bdw` | 4 on an argument refusal (bd's `--actor` flag, a database-switching flag, a flag before the verb), 5 on a configuration refusal (no workspace config, a write on an unverified bd version), 3 when no `bd` is on PATH, 1 when bd cannot be started; otherwise bd's own exit code (128 + N when signal N ends it) |
| `tooling-install` | its own set: 0 in sync, 1 drift, 2 usage, 4 refused |

Each family's Skill and `design.md` state the family's codes and link here.

## Argument contract

A Wrapper accepts exactly the arguments its usage line defines. A
surplus positional is a usage error, exit `2`, and so is a flag-shaped
token (one beginning with `-`) anywhere the usage line has no required
slot for it:

- **Fixed arity.** A Verb checks its argument count exactly, before it
  reads a roster, a forge, or an Install Target, so one extra token,
  flag-shaped or not, is refused.
- **Optional slots.** A flag-shaped token in an optional positional
  slot is refused at parse time, never taken as the value: a remote
  name, a target name, or a mode word.
- **Variadic tails** consume every element, and refuse a flag-shaped
  one at parse time. `gitw-commit`'s pathspecs and `ghw-issue-create`'s
  labels take no flags (a path that really begins with `-` is spelled
  `./-name`); `tooling-install`'s option tail refuses any token it does
  not parse. Any other element is validated like the rest of the tail:
  an extra `ghw-issue-create` label must exist in the repo's live label
  registry.
- **Required slots** take their token as the value and validate it on
  their own terms, flag-shaped or not. A title of `--bogus` is a title,
  and a message or body file named `--bogus` is read when, resolved
  against the working directory, it names a file in a staging directory.
  A Permission rule that leaves a required slot to a wildcard grants
  every value that slot accepts. One required slot is stricter:
  `ghw-issue-close`'s comment file refuses a flag-shaped path at parse
  time (spell such a path `./-name`).

The reason is the Permission system. A rule may put its wildcard in the
middle (`Bash(foo bar * baz)`), and that rule matches
`foo bar x baz --something-dangerous` too. Such a rule is only as tight
as the Wrapper's own grammar: a Wrapper that ignored or absorbed the
trailing token would run a command the rule's author never meant to
grant. Rejecting what the usage line does not define is therefore a
security property, not a nicety.

The contract covers the `gitw-*`, `ghw-*`, and `fjw-*` Verbs and
`tooling-install`, and each Verb's test file pins it with a surplus
positional and an unrecognized flag (the shared case for the `gitw-*`,
`ghw-*`, and `fjw-*` Verbs lives in `cli/ghw_test_support.py`;
`tooling-install`'s cases are in `cli/lib/install_test.py`). `bdw` is outside it by design: it passes its
arguments to `bd`, whose own parser owns the refusal. The `triage-*`
reference wrappers have not been audited against it.
