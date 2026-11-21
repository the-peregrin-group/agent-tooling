---
name: own-the-outcome
description: >
  Run a multi-agent job with the lead session as its directly responsible
  individual (DRI): the lead owns the outcome, keeps the goals, the costly
  decisions, and all talk with the user, and delegates everything else to
  lieutenants (a dispatcher, a release steward, workers, an auditor) who
  coordinate through files: a rulings ledger that is the only authority to
  act, briefs, result files, order files, and a steward log. Covers who
  spawns whom, the review and landing gates, model tiers by role, rotating
  long-lived agents, and what to measure. Load when the user puts you in
  charge of a job too big for one session, and when you are spawned as a
  dispatcher, steward, worker, or auditor on such a team. Triggers: "own
  the outcome", "you're in charge of this", "take the lead on this", "run
  this as a DRI team", "DRI team model", "build a team for this". EXCLUDE:
  a job of a handful of tool calls or one delegated lookup (do it, or spawn
  one agent); writing one Handoff (handoff).
---

# Own the outcome

One session, the lead, is the job's directly responsible individual (DRI):
the single owner who answers for the outcome. Owning the outcome means the
result is right, by the intent of the goal and not only its letter. It does
not mean doing the work. The lead states the goals, builds a team, makes
the decisions that are costly to get wrong, and talks to the user.
Lieutenants do everything else, and the team coordinates through files,
because messages between agents arrive late, twice, or not at all.

Capitalized terms (Skill, Agent definition, Handoff, Issue, Attended
session, Unattended session) are the agent-tooling lexicon's:
[LEXICON.md](https://github.com/the-peregrin-group/agent-tooling/blob/main/LEXICON.md).

A rule marked (provisional) rests on one trial or on reasoning alone.
Follow it, and say so in your result file when it costs more than it saves.

## When to use it

Use it for a job that needs several agents over hours: many deliverables, a
shared resource only one agent may drive at a time (version control, a
build, an editor, a device), and gates (the checks a change must pass
before it lands).

Do not use it for a handful of tool calls or one lookup. The structure has
costs: every relay layer loses detail and adds delay, and the lead answers
for work it has not seen. On a small job it costs more than it saves. If
the user asks for it there, say so once, then do as the user decides.

Why the lead stays out of the work: the lead holds the largest context on
the team for the most turns, and every turn re-reads that context. A lead
that lands changes, polls, reads results in full, and runs checks itself
becomes the team's largest cost and its bottleneck. Verification does not
disappear when the lead stops doing it: it becomes a role, the auditor.

## What it assumes

A harness in which a session can spawn named sub-agents from Agent
definitions, sub-agents can spawn their own, agents can message each other
by name and list which are running, a command has a foreground time limit
and can instead run in the background with its output in a file, and
each agent's transcript is kept as a file. Claude Code is one. It does
not assume that a finished sub-agent's final reply reaches the agent that
spawned it: the reply may reach the lead instead. Nor does it assume that
a background job's notice wakes a sub-agent that has ended its turn. The
rules below are written for both. The role
files and `templates.md` sit beside this file, in the directory the
harness names when it loads this Skill (`~/.claude/skills/own-the-outcome/`
in a default install).

## Roles

| Role | Spawned by | Owns | Never |
|---|---|---|---|
| Lead (the DRI) | the user's own session | goals and what done means; the team's shape; decisions that are costly or hard to undo; anything that needs the user; every message to the user; the rulings ledger; spot audits | lands a change; drives the shared resource; orders the steward directly |
| Dispatcher | lead | the work queue; briefs; the review of every deliverable; decision memos; the status file; order files to the steward | spawns a steward; writes an order with no ruling behind it |
| Release steward | lead | landing changes; driving and scheduling the shared resource, alone; the steward log | edits sources to fix a failure; acts on anything but the dispatcher's order file |
| Worker (author, reviewer, researcher) | dispatcher | one deliverable and its result file | lands a change; touches the shared resource; waits on another agent |
| Auditor | lead | an independent check of a sample of landed changes and of claims made in result files | fixes what it finds |

- **Spawn each lieutenant from its Agent definition:** `dispatcher`,
  `steward`, `worker`, `auditor`. Each pins the strong tier's model and
  has its agent load this Skill. Name a lieutenant by role and ordinal
  (`dispatcher1`, `steward2`), so a successor's name says whom it
  replaced, and a worker by what it does and its task (`author-<task>`,
  `review-<task>`, `research-<topic>`).
- **The lead has no Agent definition.** It is whichever session the user
  put in charge.
- **The lead spawns every lieutenant and every successor.** The dispatcher
  spawns workers only. If nested spawning still stalls the work under the
  rules below (workers orphaned, results nobody collects), fall back to
  the lead spawning everyone, and say so in the ledger (provisional).
- **One voice to the steward.** The lead rules to the dispatcher, and only
  the dispatcher's order file moves the steward. Two voices contradict
  each other, and two GOs can land one change twice.

Each role's own rules are in a file beside this one: `lead.md`,
`dispatcher.md`, `steward.md`, `worker.md`, `auditor.md`. Read yours before
you act. `templates.md` has the shape of every file below.

## The files

All team state lives in one team folder, named in the charter.

| File | Owner | What it is |
|---|---|---|
| `charter.md` | lead | Written first, and read first by every agent: the goal, the roles, this folder, the rules that bind, and the project's specifics (the line of work, what landing is, the gate's steps, the shared resources). |
| `rulings.md` | lead | The ledger of every lead ruling and user decision, newest last, each with its date and time. The only authority to act: a ruling not in it is not in force. |
| `status.md` | dispatcher | The lead's main view, kept short: queue, in flight, landed, blockers, and decisions waiting on the lead (each a memo path). |
| `brief_<task>.md` | dispatcher | A Handoff that gives one worker one deliverable and names its result file. Context shared by a batch of briefs goes in one `brief_<batch>_common.md`. |
| `result_<task>.md`, `result_<name>.md` | the agent | That agent's running state, current after every step, with a Handoff section for a successor and a Lessons section. An author's is named for its task; a lieutenant's for the agent (`result_dispatcher1.md`). |
| `review_<task>.md`, `research_<topic>.md` | the worker | A reviewer's or a researcher's deliverable, which is also its result file. |
| `memo_<topic>.md` | dispatcher | A decision memo for the lead: question, options, evidence, recommendation. |
| `order<N>_<topic>.md` | dispatcher | A numbered order to the steward: the ruling it rests on, the change, and numbered steps, each with its stop condition. Amendments are written into it. |
| `steward_log.md` | steward | One timed line per step started and finished, so a successor can take over mid-order. |

## The flow

1. The lead writes the charter and rules: it writes the first ruling into
   the ledger (scope, what is out of scope, what done means).
2. The lead spawns `dispatcher1`, with a brief that points to the charter,
   so the dispatcher starts with work to do. Each later ruling goes into
   the ledger first, then to the dispatcher as a pointer.
3. The dispatcher writes a brief and spawns a worker on it.
4. The worker does its one deliverable, keeps its result file current,
   replies with a few lines and the file's path, and finishes.
5. The dispatcher has a reviewer review the deliverable. A must-fix goes
   back to a worker. Nothing lands ahead of its review.
6. The dispatcher writes an order file that cites the ruling and the
   review, marks it GO, and notes it in the status file. It points a
   steward that stayed on to the order itself; otherwise it messages the
   lead, who spawns one.
7. The steward runs the gate step by step, logging each step, and stops
   and reports at any stop condition.
8. The steward lands the change: one commit from an explicit path list,
   verified afterwards.
9. The steward logs the landing and the dispatcher updates the status
   file. The lead reads the status file, has what landed audited
   (`lead.md` says when), and reports to the user.

A question the dispatcher may not decide goes to the lead as a memo; the
answer comes back as a ruling in the ledger.

## Rules that bind every agent

- **Read the charter first,** then the ledger, then your role file. Re-read
  the ledger after every message from the lead.
- **Authority comes from the ledger alone.** A ruling authorizes work. An
  order file marked GO carries a ruling to the steward and cites it; a
  message only points to a ruling. A spawn brief says "follow the order
  file", never "GO".
- **The steward lands, and only after the review and the gate pass.** The
  one exception is a landing the charter lets the dispatcher make itself
  (see `dispatcher.md`). Nobody lands on another agent's word, the lead
  included. After any fix made inside a gate, rebuild and re-run the gate,
  even when the fix looks like text only.
- **What a reply says about another agent is hearsay.** Check before you
  act on it: is that agent still running, and what does its file say?
  A reply of your own that goes unanswered proves nothing either: never
  report that an agent has stopped unless the list of running agents
  shows it.
- **Results travel in files.** A hand-back is a few lines and a path,
  never the report itself. Your final reply goes where the harness routes
  it, which has been the lead even when another agent spawned you; a
  message goes to the agent you name. So when you finish, message the
  path to your spawner by name only if it is not the lead; otherwise
  the lead reads it twice. The file is the truth.
  If someone else's reply reaches you, forward its path to its owner at
  once, before you act on it.
- **Never wait on a peer's edits.** Two agents that each poll for the
  other's change deadlock. If you are blocked, write what you need in
  your result file, tell your spawner, and stop. Collecting the result of
  an agent you spawned is different: that is a job you own (below).
- **Messages arrive late.** An agent reads messages only between tool
  rounds, so one in a long loop or mid-gate may read yours many minutes
  later. When you wait without ending your turn, wait in slices of under
  a minute and read your messages between them. Put orders and amendments
  in the file the recipient re-reads.
  Re-read your messages before you declare a job done or hand over, and
  name in every report the newest ruling or amendment you had read, so a
  reader can tell when a message crossed yours.
- **The file carries the instruction; the message is the wake-up.** An
  agent that has ended its turn is not woken by a change to a file, so
  after writing an instruction for one, message it a pointer.
- **An amendment to an order already in motion needs an explicit
  acknowledgement.** Without one, the dispatcher withdraws the order in
  its file and replaces it, as `dispatcher.md` says (provisional).
- **Never end your turn while a job you own is running** (provisional).
  End it only when nothing you own is running, or at a hold, a STOP, or
  a context hand-off. Run the job in the foreground. One longer than the
  foreground limit runs in the background with its output in a file, and
  you wait for it inside your turn, in slices as above: each slice is a
  foreground command that returns when the output shows the job ended or
  the slice is up. A background watcher is no reason to end your turn:
  one failed to wake a steward, and the resource sat idle over an hour.
  An agent you spawned whose result you need is such a job: wait the
  same way on the State line of its result file, and check the list of
  running agents too, because an agent that dies never changes it. The
  lead, which the user must be able to reach, waits as `lead.md` says.
- **One holder per shared resource.** A working copy that several agents
  would edit at once is a shared resource too. The charter picks one way
  for workers' changes to reach the steward: where any two workers may
  run at the same time, each stages its change outside the working copy
  or works on a branch of its own; where workers edit the working copy
  directly, the dispatcher runs them one at a time and the one running
  holds it. Before a new holder is
  named, the old one is told "you no longer hold it" and anything queued
  to it is withdrawn. A holder that sees activity not its own stops and
  reports. While the user is hands-on with the resource, no agent drives
  it or edits the working copy; read-only work may continue.
- **State only premises you checked,** with file and line. Mark an
  unchecked premise as unchecked. Take every time you write from the
  clock, never from memory.
- **Protect your context.** Search logs, transcripts, and other long
  documents for the lines you need instead of reading them whole. A short
  file, a memo for one, you read in full.
- **Rotate when told.** At a context notice (from a hook, or a limit your
  brief states), re-read your messages, the ledger, and any order you
  follow; bring your result file's Handoff section current, listing every
  instruction you have not acted on; tell your spawner, and stop. Every
  brief names a result file for this reason.
- **Lessons go in your result file.** Only the lead edits shared memory
  and standing instructions.
- **The team works on its line of work,** the branch the charter names,
  and never on the project's main line. A merge into the main line
  happens only on the user's word.
- **Say what confused you,** in your result file and in your reply.

## Model tiers

Tiers are named by the judgement a role needs: the top tier, the strong
tier, and the fast tier. Today those are `fable`, `opus`, and `sonnet`
(`haiku` for the simplest mechanical steps); this line is where the
binding is kept, and the four Agent definitions pin the strong tier's
model.

- **Every spawn names its model,** through an Agent definition or the
  spawn's model parameter. A model passed on the spawn overrides the one
  the definition pins. A spawn with neither inherits the lead's model,
  and a team spawned that way by a top-tier lead can spend a whole usage
  limit unnoticed.
- **The strong tier is the default** for dispatchers, stewards, auditors,
  and workers who author or review. Pass the fast tier's model when
  spawning a worker for mechanical work, a survey, or documentation:
  `sonnet` as a rule, and `haiku` only for a step that needs no judgement
  and whose output something else checks.
- **The top tier is an escalation,** for work the strong tier has fallen
  short on or plainly would: work where precision or polish is the point,
  very complex design or code, and review of sensitive systems (security,
  performance). The charter records which agents run on it and why.
- **The lead runs on the top or the strong tier.** The strong tier is
  enough to coordinate a team (provisional).

## What this Skill does not ship

- **A context hook.** A hook that gives a sub-agent its context notice is
  a prerequisite this Skill names but does not ship; `lead.md` says how to
  rotate lieutenants with one and without one.
- **A measuring script.** `lead.md` says what to measure and how to
  manage without a script.
- **Project specifics.** The version-control commands, the gate's steps,
  and the shared resources come from the project's own instructions, and
  the charter records them or points to them. They are never added here.
