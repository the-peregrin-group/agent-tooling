# own-the-outcome: one lead answers for a team's work

## Overview

The `own-the-outcome` Skill runs a multi-agent job with one session, the
lead, as its directly responsible individual (DRI). The lead answers for
the outcome and keeps only what needs its judgement: the goals, the team's
shape, decisions that are costly or hard to undo, and every exchange with
the user. Lieutenants do the rest. A dispatcher runs the work queue and
briefs workers; a release steward lands the team's changes and alone
drives the shared resource; workers each produce one deliverable; an
auditor independently checks a sample of what landed.

The team coordinates through files in one team folder, because messages
between agents arrive late, duplicated, or not at all: a charter, a
lead-owned rulings ledger that is the only authority to act, briefs, result
files, reviews, decision memos, numbered order files, and a steward log.

Four Agent definitions (`dispatcher`, `steward`, `worker`, `auditor`)
ship with the Skill. Each pins the strong tier's model, so a spawn from
one cannot inherit the lead's model by accident, and has its agent load
the Skill. Project specifics (version-control commands, the gate's
steps, the shared resources) live in each team's charter, not in the
Skill. The [design](design.md) has the reasons and the rejected
alternatives.

## Status

| Capability | State | Where |
|---|---|---|
| The shared protocol: roles and who spawns whom, the team's files, the flow from ruling to landing, the rules that bind every agent, and model tiers by role | shipped | `skills/own-the-outcome/SKILL.md` |
| The lead's part: framing the job with the user, delegated authority, ruling through the ledger with stops for approval, protecting what the user designed, watching and rotating lieutenants, auditing, and what to measure and report | shipped | `skills/own-the-outcome/lead.md` |
| The dispatcher's part: briefs, the review gate, order files and their amendments, the status file, decision memos | shipped | `skills/own-the-outcome/dispatcher.md` |
| The release steward's part: acting on order files only, the steward log, the gate, landing as one verified commit, holding the shared resource | shipped | `skills/own-the-outcome/steward.md` |
| The worker's and the auditor's parts | shipped | `skills/own-the-outcome/worker.md`, `skills/own-the-outcome/auditor.md` |
| Templates for the charter (with the project's specifics), a ruling, a brief, a result file, a review, a research file, a memo, an order, the status file, and the steward log | shipped | `skills/own-the-outcome/templates.md` |
| Four Agent definitions, one per lieutenant role, that pin the strong tier's model and have the agent load the Skill | shipped | `agents/dispatcher.md`, `agents/steward.md`, `agents/worker.md`, `agents/auditor.md` |

### Known gaps

- The Skill tells agents to rotate at a context notice but ships no hook
  that gives one; without a hook, the limit has to be written into each
  brief and order (agent-tooling-saey).
- The Skill asks the lead to report each role's share of a run's cost but
  ships no script that measures it (agent-tooling-2at3).
- A cold read of the installed copy is still unsure in several places,
  among them what the rules mean for agents that run as teammates and how
  a fix reaches the steward after a gate stop (agent-tooling-lt23).
- The Skill names no durable place for agents' scratch copies and no way
  to clean them up that the Permission rules allow (agent-tooling-ppji).
