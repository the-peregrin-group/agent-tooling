# use-issues: the Issue Tracker skill family

## Overview

"use-issues" names every issue-related Skill, script, and Wrapper as one
family: generic Skills split by the moment an agent needs them, a Knowledge
Skill for the fundamentals, platform Skills that only point at their
Wrapper, and Wrappers whose issue Verbs document themselves and share one
top-level grammar. It is being built in slices, and the Status table below
says which have shipped. The rest of today's issue guidance is the
`use-github` Skill (documented under [ghw](../ghw/index.md)), `use-bd`
([use-bd](../use-bd/index.md)), and `use-forgejo` ([fjw](../fjw/index.md)),
and they stay in force until the slice that replaces each one lands.

The design of what has shipped is in [design.md](design.md). The design of
the rest, its alternatives, the plan, and the approved requirements are
in the [proposal](2026-11-13-proposal.md); the decisions are ADRs 0017 to
0023,
[ADR 0024](../../adr/0024-a-pass-reorganizes-a-branch-issues-children.md),
which amends ADR 0009 (Branch Issues are worked in passes) so that a pass
reorganizes children, not only adds them, and
[ADR 0025](../../adr/0025-the-tracker-schema-is-one-markdown-file-with-one-json-block.md)
(the Tracker Schema is one Markdown file with one JSON block). The work is
tracked under `agent-tooling-u9n` (split the Issue
Tracker skills into a generic layer and platform layers); the Wrapper work
is tracked in `agent-tooling-84n3` (bdw), `agent-tooling-fyxo` (ghw),
`agent-tooling-1vr` (fjw), and `agent-tooling-2340` (the triage scripts).

## Status

| Capability | State | Where |
|---|---|---|
| The default Tracker Schema, with its Issue State Diagram | shipped | `skills/setup-issue-tracker/TRACKER.default.md`; [design](design.md) |
| This repo's own Tracker Schema, copied from the default and customized | shipped | `TRACKER.md` |
| `know-issues`, the Knowledge Skill for the issue fundamentals | shipped | `skills/know-issues/SKILL.md`; documented under [know](../know/index.md) |
| `create-issue`, generic, against today's Verbs | shipped | `skills/create-issue/SKILL.md` |
| `work-issue`, generic, against today's Verbs | shipped | `skills/work-issue/SKILL.md` |
| `breakdown-issue`, for Branch Issue passes | shipped | `skills/breakdown-issue/SKILL.md` |
| `triage-issues` read against the Issue State Diagram | shipped | `skills/triage-issues/SKILL.md`; [design](design.md#triage-issues) |
| `setup-issue-tracker`, generic, with each platform's setup steps read on demand | shipped | `skills/setup-issue-tracker/SKILL.md`; [design](design.md#setup-issue-tracker) |
| bdw rebuilt with its own issue Verbs and per-Verb help; `use-bd` as a failsafe pointer | planned | [proposal](2026-11-13-proposal.md), slice 4; `agent-tooling-84n3` |
| ghw issue Verbs on the shared grammar, with Forge identity | planned | [proposal](2026-11-13-proposal.md), slice 5; `agent-tooling-fyxo` |
| fjw issue Verbs on the shared grammar, and the triage scripts as Wrappers | planned | [proposal](2026-11-13-proposal.md), slice 6; `agent-tooling-1vr`, `agent-tooling-2340` |
| Stage-aware blocking | planned | [proposal](2026-11-13-proposal.md), R27; `agent-tooling-aas0` |
| Source-taking forms of high-judgement Verbs | proposed | [proposal](2026-11-13-proposal.md), R46's note; `agent-tooling-zkox` |

### Known gaps

- Nothing reads the default Tracker Schema's JSON block yet, and no test
  checks that the shipped default is well formed (`agent-tooling-rtag`).
- `setup-issue-tracker` cannot register a repo's Forge identities: ghw has
  none yet and acts as whoever `gh` is authenticated as, and fjw has only
  its one machine account (`agent-tooling-fyxo`, `agent-tooling-1vr`).
- On GitHub, a repo's Issue Kinds and Issue Priorities cannot follow its
  Tracker Schema, since ghw fixes the five kind labels and the four
  priority levels (`agent-tooling-xgzm`).
- This repo's `TRACKER.md` declares no `meta` kind, because it is not a
  registered Beads type, and some imported Issues still carry GitHub type
  labels the schema does not declare (`agent-tooling-aio.7`).
- The default leaves open where an Issue State is recorded on a forge with
  no status mechanism (`agent-tooling-vb2v`), and neither Beads statuses
  (`agent-tooling-c86`) nor a GitHub board field (`agent-tooling-u9n.12`)
  holds the default's states today.
- The `triage-issues` Skill is generic, but its GitHub scripts still read
  the `TRIAGE.md` profile and work to eight board `Status` options, not the
  repo's Tracker Schema (`agent-tooling-u9n.12`).
- An unattended GitHub pass cannot put a finding on the affected issue with
  the `human` label, so it lists findings in its digest instead
  (`agent-tooling-u9n.13`); and it cannot read an issue's body, its
  comments, or its own digest, so it cannot judge a bar that depends on
  what an issue says or carry a finding forward (`agent-tooling-u9n.14`).
- No triage pass has run end to end with real writes
  (`agent-tooling-8y73`).
- There is no triage tooling for Beads: a pass is run by hand, with nowhere
  to record when it last looked at an Issue and no way to tell its own
  writes from activity (`agent-tooling-53af`).
