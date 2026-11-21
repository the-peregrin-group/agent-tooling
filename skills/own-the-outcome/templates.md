# File templates

The shape of each file in the team folder. Fill in the angle brackets and
drop what does not apply. Take every time from the clock (`date`), never
from memory.

## `charter.md` (lead)

The charter is where the project's specifics live. A project that runs
teams often keeps them in a document of its own, and the charter points
to it.

```markdown
# <Job> team charter

Written <date> by the lead. Every agent on this team reads this first.
The team runs under the `own-the-outcome` Skill; its rules bind unless
this charter says otherwise.

## Goal
<What the job is, what done means, and the document that is the source of
truth for scope.>

## Team
- Lead: <session>. Dispatcher: `dispatcher1`. Stewards are spawned by
  the lead when an order is ready.
- Top-tier agents, and why: <none | agent, reason>.
- Authority the user delegated to the lead: <none | the grant and its
  conditions, as recorded in rulings.md>.

## Team folder
`<path>`: rulings.md, status.md, briefs, results, reviews, memos, orders,
steward_log.md. <Give the absolute path, so every agent reaches the same
folder from wherever it works. Keep it outside the working copy, or
ignored by version control, so that it never shows as a pending change.
Unless the project has a place for it, use a folder in the project's
primary checkout (not in a worktree of it), `<checkout>/.team/<job>/`,
ignored through a local exclude rule and not through a tracked ignore
file, which would itself be a change to land (provisional). Avoid a
temporary directory that may be wiped during the run.>

## This project
- Line of work: `<branch>` <and, if it does not exist yet, the command
  that creates it>. Main line: `<branch>`, never written by the team;
  merges only on the user's word.
- Landing means: <the write the steward makes, and the command, taken
  from the project's own instructions>.
- Landings the dispatcher may make itself: <none | which, e.g.
  documentation only>.
- How a worker's change reaches the steward: <in the working copy, one
  worker at a time | staged per task under `<path>/staged/<task>/`, with
  that task's manifest `<path>/staged/<task>/manifest.txt` and its
  originals under `<path>/orig/<task>/` | on the worker's own branch,
  which the steward integrates (provisional)>. <One way for the whole
  job. Choose the first only where no two workers ever run at the same
  time.>
- Shared resources with one holder at a time: <resource: holder>.
- The gate, in order: <step: command, and where its authoritative result
  is read | none beyond the review, for a project with nothing to build
  or test>.
- Baselines for generated output: <path, and how to reproduce>.
- Project rules to read: <paths>.

## Rules added for this job
<Only what the Skill does not already say.>
```

## `rulings.md` (lead)

Newest last. One section per ruling. The heading carries the date and the
time, so that an order can cite it without ambiguity.

```markdown
## <YYYY-MM-DD HH:MM> <topic> (<user | lead>)
Scope: <exactly what is to be done>.
Out of scope: <what is not>.
Done means: <the observable result>.
Stops for approval: <none | before <step>: <what> is approved by <the
lead | the user, through the lead>; work holds there until a later ruling
lifts it>.
```

## `brief_<task>.md` (dispatcher)

```markdown
# Brief: <task>, for <worker name> (<dispatcher>, <time>)

Ruling: rulings.md "<heading>". Charter: <path>.
Deliverable: <the one thing>. Result file: `result_<task>.md` <for a
review, `review_<task>.md`; for research, `research_<topic>.md`>.
Leave the change: <where, per the charter; the staging, manifest, and
originals paths if it is staged>.

## What is known
- <Premise> (<file>:<line>).
- UNCHECKED: <premise nobody has verified>.

## What done means
<Observable result, and how the worker should check it.>

## Out of scope
<What to leave alone.>

If your context passes <limit>, bring your Handoff section current, reply
"over", and stop.
```

## `result_<agent-or-task>.md` (its agent)

```markdown
# Result: <task or agent> (<name>)

## Handoff
<Current after every step. A successor starts here.>
- State: <working | blocked | done> (<time>).
- Last read: <the newest ruling or amendment heading you have read>.
- Stands at: <where the work is>.
- Next: <the next step>.
- Blocked on: <what, and whom>.
- In flight: <for a dispatcher, each worker and its result file>.
- Done means: <cite the brief or ruling>. Verify by: <how>.

## Done
<What changed, with paths. What was checked, and how.>

## Not done, not checked
<Plainly.>

## Lessons
<For the lead to consider for shared memory or the charter.>
```

## `review_<task>.md` (reviewer)

```markdown
# Review: <task> (<reviewer>, <time>)

Reviewed against: brief <path>, ruling "<heading>".

## Must-fix
1. <file>:<line>: <finding, and why it must be fixed>.

## Should-fix
1. <file>:<line>: <finding>.

Verdict: <ready to order | not until the must-fixes land>.
```

## `research_<topic>.md` (researcher)

```markdown
# Research: <the question> (<researcher>, <time>)

## Found
- <fact> (<file>:<line>).

## Not established
<What you could not find out, and what you tried.>
```

## `memo_<topic>.md` (dispatcher, for the lead)

Under about 60 lines.

```markdown
# Memo: <the question> (<dispatcher>, <time>)

Blocks: <what cannot proceed until this is decided | nothing>.

## Options
A. <option>: <cost, risk, how reversible; if it changes something the
   user designed, what that thing is for and where the user's plan says
   so>.
B. <option>: <...>.

## Evidence
- <fact> (<file>:<line>).

## Recommendation
<One option, and the reason.>
```

## `order<N>_<topic>.md` (dispatcher, for the steward)

```markdown
# ORDER <N> for <steward> (<dispatcher>, <time>): <topic>. GO.

Ruling: rulings.md "<heading>". Author: <result path>. Review: <review
path>. Change: <paths, or for each staged task: staged at `<path>` with
manifest `<path>` and originals `<path>`>.

0. Before you start: the latest commit on the line of work is <commit>,
   nothing is pending, <resource state>. Otherwise STOP and report. <If
   the line of work does not exist yet: first create it with <command>;
   <commit> is then the commit it starts from.>
1. Apply: <how>. STOP if a file differs from its original.
2. <Gate step>: <command>; the authoritative result is <where>. STOP on
   <condition>; write <what> to <path>.
3. <Further gate steps, each with its STOP or HOLD condition. A stop for
   approval in the ruling is a step of its own: "HOLD: write <what> to
   <path> and message the path to <dispatcher> and the lead; resume only
   when this file cites the ruling that approves.">
4. Land: ONE commit of exactly <path list>, message "<message>". Verify
   one new commit after <commit> and nothing pending.
5. Afterwards: <finish | stay on for the next order, still holding
   <resource>>.

STOP: the order cannot go on as written; report and end your turn. HOLD:
pause before the next step until this file lifts it. Log every step's
start and end in steward_log.md. Report in `result_<steward>.md` under
"ORDER <N>", and message <dispatcher> at each STOP and at the end.

## Amendment 1 (<dispatcher>, <time>): <what changes>
<The change, and the step to resume from. Acknowledge in steward_log.md.>

## HOLD (<dispatcher>, <time>): <why>
<Acknowledge in steward_log.md. Lifted: <time>, resume at step <n>; the
dispatcher messages the steward when it writes the lift.>
```

## `status.md` (dispatcher)

Under about 40 lines.

```markdown
Updated <time> by <dispatcher>. Latest commit: <commit>.

## Queue
## In flight
## Landed
- <time> <change> (<commit>)
## Blockers
## Waiting on the lead
- <memo path>: <the question in a few words>
```

## `steward_log.md` (steward)

One line per event, appended.

```
<time> <steward> ORDER <N> step <n> START
<time> <steward> ORDER <N> step <n> DONE <verdict> <commit, if a landing>
<time> <steward> ORDER <N> amendment <n> ACK
<time> <steward> ORDER <N> HOLD ACK before step <n>
<time> <steward> ORDER <N> done; staying on, still holding <resource>.
<time> <steward> rotating at step <n>; <successor> resumes. I no longer hold <resource>.
```
