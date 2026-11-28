---
name: triage-issues
description: >
  Run a triage pass over a repo's whole Issue Tracker. Load when asked to
  triage, and for a scheduled triage run.
---

# Triage Issues

Capitalized terms (Issue, Branch Issue, Tracker Schema, Issue State
Diagram, Permission rule, and the rest) are the lexicon's
([LEXICON.md](https://github.com/the-peregrin-group/agent-tooling/blob/main/LEXICON.md)),
and the lexicon is authoritative for them. This skill is written against no
platform: where a step needs a command, run your wrapper's help. Until each
wrapper's help carries its own usage, the last section, Platform mechanics,
says what each platform has today.

The procedure says what must be done, not who may do it. What you may do
yourself is decided by the repo's Permission rules: if the grant exists, do
the act; if not, the call is denied or asked, and that is the answer. Fix
the call or report the gap, and never look for another spelling or reword
the text to get past it. A pass may run under Permission rules of its own,
which may differ from a working session's in the same repo.

## What a pass is

Filing-time checks are best effort; a separate batch pass across the whole
tracker reconciles what they miss. A triage pass is that batch pass. It
checks every Issue against the repo's Tracker Schema, corrects what it can,
asks a person about the rest, and records when it last looked at each
Issue.

A pass checks Issues; it does not work them. Scoping, designing,
implementing, and breaking down are work on one Issue, done by whoever
claims it (`work-issue`, `breakdown-issue`). Asked to triage one Issue, run steps 2 to 5 for it, with the
overlap search of step 3.

## Before the pass

- Read the repo's Tracker Schema in full: `TRACKER.md` at the repo root.
  It declares the Issue Kinds, the Issue Priorities with their staleness
  thresholds, the Issue Label Schema, and the Issue State Diagram, and it
  is the only place those are defined. A repo with no Tracker Schema file
  yet declares its kinds, priorities, and labels wherever its tracker was
  set up; for the staleness thresholds and the Issue State Diagram read
  the shipped default Tracker Schema, and say in the digest that you did.
  Platform mechanics says where each of these is.
- Take the current time from the system clock. Judge recency and staleness
  from exact timestamps compared with the current time, never from
  rendered dates.
- If a `know-unattended` skill is listed, load it: it says how to tell an
  attended session from an unattended one. If a `use-privacy` skill is
  listed, load it before composing any text bound for outside this
  machine: a comment, the digest.

## The pass

### 1. Take inventory

List every open Issue, and every closed Issue the tracker still records in
an open state. Leave out the digest Issue (step 6). For each Issue you need
its kind, priority, labels, recorded state, claim, relationships, the time
of its latest activity, and the time a pass last looked at it.

Activity is something a person or a working agent did to the Issue. A
pass's own writes and the tracker's automation are not activity. An Issue
with no activity since a pass last looked at it only needs its staleness
judged again.

### 2. Check each Issue

- **Classification.** It has exactly one kind and a priority, and its
  labels conform to the Issue Label Schema. An unknown label is a mistake
  to fix, not a new label.
- **State.** Judge every move against the repo's Issue State Diagram.
  Check the recorded state against the diagram in both directions: an
  Issue that does not meet a bar its state implies, and an Issue that
  already meets the condition of a later transition. Open-or-closed always
  agrees with status. A Branch Issue is judged on itself: a parent's status
  is judged against its own definition and criteria, not on the state of
  its children.
- **Claims.** Whether a state needs a claim is the diagram's call, so an
  Issue with no claim is not for that reason abandoned. A claim that has
  gone stale is a question for whoever holds it: never take over someone
  else's work in progress; ask.
- **Staleness.** An Issue is stale when the time since its latest activity
  exceeds `stale_after_days` for its priority. Every open Issue is judged,
  whatever its state. Stale is a question (is it still wanted or already
  done by other work, is its priority right, who takes it), not a verdict.
- **Relationships.** A relationship lives in the tracker's native link,
  with its type explicit; one that exists only as prose in a body is
  missing. Look also for a blocking link that does not really block, and
  for an Issue still marked as waiting on a person whose question has been
  answered.
- **Size and shape.** An Issue that is plainly bigger than one session, or
  a child that does not belong under its parent, is raised, not fixed
  here: reorganizing is a pass on the Branch Issue (`breakdown-issue`).

### 3. Check across Issues

- **Overlap.** Look for what a filer's search looks for (`create-issue`,
  "Search first"): duplicates, contradictions, partial overlap, and an
  Issue that is really the parent or the child of another.
- **Priorities.** Priority exists to answer "what do I work on next?" When
  the spread of priorities no longer answers that (more Issues at the top
  level than anyone could drop everything for, or nearly everything at one
  level), demote the weakest until the top level means something.

### 4. Act on what you found

Change an Issue yourself only when you are confident the change is right,
above all in an unattended pass, where nobody sees the change as it is
made. When you are not, leave the Issue as it is and put the question to a
person (step 5).

Be liberal with priority and conservative with state: a wrong priority
costs little and the next pass corrects it, while a wrong state puts later
work on an earlier gap.

- Correct what the Tracker Schema settles: a classification with one right
  answer, an open-or-closed that disagrees with the state, a priority, a
  native link for a relationship the Issue already states.
- Move an Issue to another state only when the diagram's condition plainly
  holds, and say why on the Issue. Every close and every reopen carries
  its reason.
- Prefer the additive act: comment rather than rewrite a description.
- Whatever you are unsure of, and whatever is denied or would need a
  person's approval, is not attempted another way. It goes to a person
  (step 5).

### 5. Put what needs a person on the Issue

What needs a person goes on the affected Issue as a comment with the
`human` label, which is the one queue on every platform. The comment says
what was found, what the pass proposes, and what the person is asked to
decide.

Read what earlier passes left before you comment. Do not repeat a finding
that still stands. Where the person has answered, the answer stands: act on
it if you may, and take the label off when nothing waits on them any more.

Attended, put the findings to the person in the session, grouped by the
kind of decision. What they settle there is acted on and not queued.

### 6. Record the pass

- **Each Issue.** Record on each Issue you looked at that the pass looked
  at it, and when. Make it the last write to that Issue, so the pass's own
  changes fall before it.
- **The digest.** The pass's digest is one Issue of kind `meta`, classified
  like any Issue and skipped by triage as work. Its body is the current
  report, rewritten in place each pass: everything that now waits on a
  person, read back from the `human` queue and not from memory, grouped by
  the kind of decision, with like findings folded together and each
  pointing at its Issue, and anything the pass could not check. Its
  comments are the log of passes: one comment per pass, saying what the
  pass changed. The digest is not the queue. A person answers on the
  affected Issue.

## Standing up triage in a repo

Setting up a tracker, or standing up triage in a repo, is a human
procedure: the agent confirms the target, drafts the whole plan, and waits
for approval. The plan covers the digest Issue and, for a recurring
unattended pass, the Permission rules the pass runs under and how it is
launched.

## Platform mechanics

These stand in for each wrapper's help until the wrappers carry triage
Verbs of their own. Free text (a comment, the digest's body) always goes
through a file. The shipped default Tracker Schema is
`TRACKER.default.md` in the `setup-issue-tracker` skill's directory,
whatever the platform.

### Beads

There is no triage tooling for Beads yet. A pass is run by hand with the
`bdw` Verbs `use-bd` teaches. The repo's kinds, priorities, and labels are
in `.beads/PRIME.md` until it has a Tracker Schema.

- Inventory: `bdw list --status=open,in_progress,blocked,deferred --json`
  gives each Issue's `issue_type`, `priority`, `labels`, `status`,
  `dependencies`, and `updated_at`; `bdw show <id>` gives its comments.
- A finding for a person: `bdw comments add <id> -f <path>`, then
  `bdw label add <id> human`. The queue is `bdw human list`.
- What Beads cannot do yet, to be said in the digest as a limit of the
  pass: its statuses are its own and cannot record a state the diagram
  names; it has no field for when a pass last looked at an Issue; and
  `updated_at` does not tell a pass's own writes from anyone else's. Keep
  the time of each pass in the digest's log and judge activity against
  that.

### GitHub

Six scripts under this skill's `reference/` directory do a pass's bulk
reads and its unattended writes. `reference/README.md` lists them and how
to call them; `reference/DEPLOYMENT.md` covers the recurring unattended
pass, the Permission rules it runs under, and the one-time bootstrap. They
need a `TRIAGE.md` profile at the repo root, which binds the repo, its
project board, the board's field IDs, the label lists, and the digest
Issue's number (`ledger_issue`: the scripts call the digest the ledger).
Every other write, in an attended pass, goes through the `ghw-*` Verbs as
`use-github` teaches them.

How the steps above map onto the scripts:

- Inventory is `triage-inventory`, anchored on the project board, which is
  where the Issue State is recorded (the `Status` field). It also reports
  open issues that are not on the board; those have no recorded state.
  Attended, add them with `ghw-board-set`; otherwise each is a finding.
- Latest activity is `triage-timeline`'s `mostRecentMeaningfulActivity`,
  an exact timestamp that already leaves out board automation and the bot
  accounts the profile lists. Compare it with the current time yourself.
  It does not leave out the pass's own label fixes and `Status`
  corrections, and it does not see Priority changes.
- "When a pass last looked" is the board's `Last Triaged` date field,
  written by `triage-bump-triaged`. It is a calendar date with no time:
  treat it as the start of that day, so activity later the same day is
  looked at again.
- The digest is written by `triage-update-ledger`.

How GitHub evidence is read. None of it defines a state; it is evidence to
weigh against the diagram.

- `triage-timeline` reports the pull requests GitHub itself links as
  closing the issue, each with its state, draft flag, and merge time. An
  open one is evidence someone is working on the issue; a merged one is
  evidence the work may be finished. A pull request that names the issue
  any other way is not reported.
- An assignee is routing: whose work the issue is expected to be. It is
  not a claim and holds nothing by itself.

What today's scripts assume, which the text above does not:

- They read `TRIAGE.md`, never the Tracker Schema. `triage-fix-label`
  accepts only the labels the profile lists. With no Tracker Schema, the
  kinds and labels are the profile's `labels.type` and `labels.area`, and
  the priorities are the board's `Priority` options. The staleness numbers
  in the profile are not used; the thresholds are the Tracker Schema's,
  or the shipped default's where the repo has none.
- A board carries the Issue States its repo's Tracker Schema declares,
  but the scripts expect eight `Status` options: Needs Triage, Needs
  Scope, Needs Eng Design, Needs Impl, In progress, In review, Done, and
  Rejected. The shipped default diagram has the first six and one closed
  state, where an Issue's Close Reason says why. On a board that still
  has Done and Rejected, read them as closed with that Close Reason.
- `triage-apply-sync` only makes open-or-closed and `Status` agree. For a
  closed issue it writes Done, or Rejected when the issue was closed as
  not planned. For an open issue whose `Status` is Done or Rejected it
  writes Needs Scope, whatever the diagram would say; if the diagram puts
  the issue elsewhere, that is a further move for the pass or a person.
- No script comments on an affected issue or adds the `human` label. Until
  the scripts can, a pass that can do neither, as an unattended pass
  granted only the six scripts cannot, puts each finding in the digest's
  body with a link to its issue and says there that the queue could not be
  written. This is a stopgap, and the one exception to "the digest is not
  the queue".
- No script returns an issue's body or comments, or the digest's current
  body. A pass that has only the scripts can check classification,
  open-or-closed against `Status`, staleness, and pull request evidence.
  It cannot judge a bar that depends on what an issue says, cannot read an
  earlier finding, a person's answer, or a claim recorded as a comment,
  and cannot carry a finding forward. So it derives every finding afresh
  each pass (the shortcut in step 1 for an Issue with no activity does not
  apply to it) and says in the digest what it could not check.

### Forgejo

`fjw` has no issue Verbs yet, and there is no triage tooling.
