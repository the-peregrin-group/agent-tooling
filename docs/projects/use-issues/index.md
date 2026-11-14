# use-issues: the Issue Tracker skill family

## Overview

"use-issues" names every issue-related Skill, script, and Wrapper as one
family: generic Skills split by the moment an agent needs them, a Knowledge
Skill for the fundamentals, platform Skills that only point at their
Wrapper, and Wrappers whose issue Verbs document themselves and share one
top-level grammar. It is being built in slices, and the Status table below
says which have shipped. Today's issue guidance is the
`setup-github-issues`, `use-github`, and `triage-issues` Skills (documented
under [ghw](../ghw/index.md)), `use-bd` ([use-bd](../use-bd/index.md)), and
`use-forgejo` ([fjw](../fjw/index.md)), and they stay in force until the
slice that replaces each one lands.

The design of what has shipped is in [design.md](design.md). The design of
the rest, its alternatives, the plan, and the approved requirements are
in the [proposal](2026-11-13-proposal.md); the decisions are ADRs 0017 to
0023, and
[ADR 0025](../../adr/0025-the-tracker-schema-is-one-markdown-file-with-one-json-block.md)
(the Tracker Schema is one Markdown file with one JSON block). The work is
tracked under `agent-tooling-u9n` (split the Issue
Tracker skills into a generic layer and platform layers); the Wrapper work
is tracked in `agent-tooling-84n3` (bdw), `agent-tooling-fyxo` (ghw),
`agent-tooling-1vr` (fjw), and `agent-tooling-2340` (the triage scripts).

## Status

| Capability | State | Where |
|---|---|---|
| The default Tracker Schema, with its Issue State Diagram | shipped | `skills/setup-github-issues/TRACKER.default.md`; [design](design.md) |
| `know-issues`, the Knowledge Skill for the issue fundamentals | planned | [proposal](2026-11-13-proposal.md), slice 1; `agent-tooling-u9n.4` |
| `create-issue` and `work-issue`, generic, against today's Verbs | planned | [proposal](2026-11-13-proposal.md), slice 2; `agent-tooling-u9n` |
| `breakdown-issue`, and `triage-issues` read against the Issue State Diagram | planned | [proposal](2026-11-13-proposal.md), slice 3; `agent-tooling-u9n` |
| bdw rebuilt with its own issue Verbs and per-Verb help; `use-bd` as a failsafe pointer | planned | [proposal](2026-11-13-proposal.md), slice 4; `agent-tooling-84n3` |
| ghw issue Verbs on the shared grammar, with Forge identity | planned | [proposal](2026-11-13-proposal.md), slice 5; `agent-tooling-fyxo` |
| fjw issue Verbs on the shared grammar, `setup-issue-tracker`, and the triage scripts as Wrappers | planned | [proposal](2026-11-13-proposal.md), slice 6; `agent-tooling-1vr`, `agent-tooling-u9n.9`, `agent-tooling-2340` |
| Stage-aware blocking | planned | [proposal](2026-11-13-proposal.md), R27; `agent-tooling-aas0` |
| Source-taking forms of high-judgement Verbs | proposed | [proposal](2026-11-13-proposal.md), R46's note; `agent-tooling-zkox` |

### Known gaps

- Nothing reads the default Tracker Schema's JSON block yet, and no test
  checks that the shipped default is well formed (`agent-tooling-rtag`).
- No setup copies the default into a repo, and no repo has a `TRACKER.md`
  yet (`agent-tooling-u9n.9`, `agent-tooling-u9n.3`).
- The default leaves open where an Issue State is recorded on a forge with
  no status mechanism (`agent-tooling-vb2v`), and neither Beads statuses
  nor a GitHub board field holds the default's states today
  (`agent-tooling-c86`).
- The shipped triage tooling still works to its own eight-state model, not
  the default's Issue State Diagram (`agent-tooling-u9n.8`).
