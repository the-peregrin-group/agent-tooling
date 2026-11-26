# Tracker Schema

This file is this repo's Tracker Schema: the repo's declared structure for
its Issue Tracker. It holds the repo's Issue Kinds, Issue Priorities, Issue
Label Schema, and Issue State Diagram, and it is the one home for them.
Agents and tooling both read it. The skills say nothing about states beyond
"judge every move against the repo's Issue State Diagram", so everything
needed to judge a move is written here.

Each fact lives in exactly one place in this file:

- The JSON block below holds the Issue Kinds, the Issue Priorities with
  their staleness thresholds, the Issue Label Schema, the Issue States in
  order with each one's open or closed flag and which one is the entry
  state, the close reasons, a colour for every kind, priority, label, and
  state, and the provenance.
- The prose after it holds the state meanings and the transition
  conditions, keyed by state name, and when each close reason may be
  given, keyed by the reason's name.

The file is the repo owner's to change. It is a tracked file, changed
through the repo's normal review. It was copied from a shipped default, and
every edit to it is this repo's customization. It is data that grants
nothing, since what an agent may do is decided by Permission rules alone
(a Permission rule is a declared rule that decides whether an agent may take
an action on its own, only with a human's approval, or never).

## What tooling reads

<!-- BEGIN tracker-schema -->
```json
{
  "provenance": {
    "source_repo": null,
    "source_commit": null,
    "default_path": null
  },
  "issue_kinds": [
    {
      "name": "feature",
      "meaning": "New feature, system, or capability",
      "color": "a2eeef"
    },
    {
      "name": "improvement",
      "meaning": "Enhancement or refinement of what exists, including its quality, structure, and docs",
      "color": "0075ca"
    },
    {
      "name": "bug",
      "meaning": "Something is broken or performs incorrectly",
      "color": "d73a4a"
    },
    {
      "name": "debt",
      "meaning": "Work skipped or done poorly earlier: stale docs, test gaps, expedient hacks, dead code",
      "color": "fbca04"
    },
    {
      "name": "meta",
      "meaning": "Design documents, planning artifacts, and non-code project work",
      "color": "7057ff"
    }
  ],
  "issue_priorities": [
    {
      "name": "P0",
      "meaning": "Drop everything",
      "stale_after_days": 1,
      "color": "b60205"
    },
    {
      "name": "P1",
      "meaning": "Most important non-emergency",
      "stale_after_days": 7,
      "color": "d93f0b"
    },
    {
      "name": "P2",
      "meaning": "Standard backlog",
      "stale_after_days": 14,
      "color": "fbca04"
    },
    {
      "name": "P3",
      "meaning": "Opportunistic",
      "stale_after_days": 28,
      "color": "0e8a16"
    }
  ],
  "issue_label_schema": {
    "axes": [
      {
        "name": "area",
        "prefix": "area:",
        "meaning": "The part of the project an Issue concerns",
        "every_issue_carries_at_least_one": true,
        "labels": []
      }
    ],
    "labels": [
      {
        "name": "human",
        "meaning": "Waiting on a person",
        "color": "d876e3"
      }
    ]
  },
  "issue_states": [
    {
      "name": "Needs Triage",
      "open": true,
      "entry": true,
      "color": "d73a4a"
    },
    {
      "name": "Needs Scope",
      "open": true,
      "color": "d93f0b"
    },
    {
      "name": "Needs Eng Design",
      "open": true,
      "color": "fbca04"
    },
    {
      "name": "Needs Impl",
      "open": true,
      "color": "0075ca"
    },
    {
      "name": "In progress",
      "open": true,
      "color": "7057ff"
    },
    {
      "name": "In review",
      "open": true,
      "color": "db61a2"
    },
    {
      "name": "Closed",
      "open": false,
      "color": "6a737d"
    }
  ],
  "close_reasons": [
    {
      "name": "done",
      "meaning": "The work it asked for is finished"
    },
    {
      "name": "rejected",
      "meaning": "It was decided not to do it"
    },
    {
      "name": "duplicate",
      "meaning": "Another Issue is the same work"
    },
    {
      "name": "superseded",
      "meaning": "Other work has replaced what it asked for"
    }
  ]
}
```
<!-- END tracker-schema -->

### How the block is delimited

The block sits between two marker lines, each an HTML comment alone on its
line: the one above the block begins with BEGIN and the one below it begins
with END, and both name `tracker-schema`, written exactly as they are above.
The file has exactly one of each. Between them is exactly one fenced code
block, opened by a line that is exactly `` ```json `` and closed by a line
that is exactly `` ``` ``, with nothing else there but blank lines, and the
lines inside that fence are one JSON object. A reader finds the two marker
lines by matching each as a whole line, takes the lines strictly inside the
fence between them, and parses those as JSON. A marker or fence line still
matches when it has trailing whitespace or a CRLF line ending, since
neither can make prose look like a marker; an indented line is not a
marker, since indentation changes what a line means in Markdown. A file
that strays from this form but whose block is still plain to see (an
indented copy of a marker, a fence spelled another way, a stray line
beside the fence) is read anyway, with a warning. One where it is unclear
which block is meant (a marker missing or repeated, no fence or two, a
fence never closed) is reported and never guessed at. Keep any other code
block you add to this file outside the markers.

### What each key holds

- `provenance`: which revision of the shipped default this file was copied
  from, so later changes to the default can be shown against it.
  `source_repo` is the name of the repo that ships the default,
  `source_commit` is the full commit of that repo the copy was made from,
  and `default_path` is the default's path in that repo at that commit.
  "What has the default changed since" is a diff of that path at the
  recorded commit against the default as it is now, whose path may have
  changed since. In the shipped default itself all
  three are `null`, because it is the original and not a copy; in a repo's
  copy all three are set, and a copy in which any is `null` has lost its
  provenance.
- `issue_kinds`: the Issue Kinds, each with its `name`, its `meaning`, and
  its `color`. Every Issue has exactly one, recorded once, in the tracker's
  own mechanism for kind.
- `issue_priorities`: the Issue Priorities, listed from highest to lowest,
  each with its `name`, its `meaning`, its staleness threshold,
  `stale_after_days`, and its `color`. Priority answers "what do I work on
  next?". Every Issue has one from filing on, set as best the filer can and
  adjusted later. Staleness is judged from exact timestamps compared with
  the current time, against the threshold each priority level declares, in
  days.
- `issue_label_schema`: the allowed Issue Labels, their meanings, and the
  axes they classify along. `axes` lists each axis with its `name`, the
  `prefix` every label on it begins with, its `meaning`, whether every
  Issue carries at least one label from it, and its `labels`, each written
  in full, as it appears on an Issue, with its `meaning` and its `color`.
  `labels` lists the labels that belong to no axis, with the same keys; a
  repo's own labels that take no prefix go there. An unknown label is a
  mistake to fix, not a new label. Where the tracker has no field for an
  Issue's kind, priority, or state, a label named for it carries it; that
  label is declared by the kind, priority, or state it names, takes its
  colour, and is not an unknown label. The labels on the area axis are the
  repo's own, since the parts of a project are that project's, and the
  repo owner fills them in. While the axis lists none, no Issue's labels
  can conform, so no Issue can be in a state later than Needs Triage.
- `issue_states`: the Issue States, listed in the order an Issue normally
  moves through them, which is the order of the Issue State Diagram below:
  "earlier" and "later" there mean earlier and later in this list. Each
  has its `name`, its `open` flag, `true` for an open state and `false`
  for a closed one, and its `color`. Exactly one open state also has
  `"entry": true`: it is the entry state, where an Issue is filed when its
  right state is not known; the other states need no `entry` key. The
  order and those two flags are the only structure the states have. Every
  Issue is in exactly one state, and whether an Issue is open or closed
  follows from its Issue State.
- `close_reasons`: the reasons an Issue is closed with, each with its
  `name` and its `meaning`. When each may be given is under "Into Closed"
  below, keyed by its name.

A `color`, wherever one appears, is six hex digits with no leading `#`
(`d73a4a`, say), and it is declared like a meaning: where the Issue
Tracker shows the thing (as a label, or as an option on a board), it shows
it in that colour, and bringing the tracker in line with this file brings
the colour too. A tracker with no colours ignores them, and one that
offers only a few named colours shows the nearest.

Tools use whatever in the block is valid and warn about the rest: a key
they do not know is ignored, and a mistake in one part leaves the other
parts in use. Only a file in which it is unclear which block is meant, or
whose block does not parse as a JSON object, leaves them nothing to use.

## Issue State Diagram

An Issue State says what kind of expert attention the Issue needs next. The
ready queue is defined by the agent: unclaimed, unblocked Issues in the
Issue States it works.

Terms used below. A Branch Issue is an Issue that holds other Issues as its
children: a project, rather than a unit of work one session finishes. An
Issue is a Branch Issue if it has any children, open or closed, or if it is
meant to hold children, even before it has any. A Leaf Issue is an Issue
that is not a Branch Issue: a unit of work meant to be claimed and finished
in one session. A pass is one session's work on a Branch Issue. A claim
makes it visible that someone is working on an Issue, since one person or
agent advances an Issue at a time; a release gives the claim up.

### What each state means

The states are described in the order the block lists them, the order an
Issue normally moves through them, and "earlier" and "later" below mean
earlier and later in that order.

#### Needs Triage

An Issue is returned here when it is found lacking and where it belongs is
not known. It needs screening, someone to check that it is a real Issue,
classified, with enough in it for scoping to start. A filer who knows the
Issue already meets every bar up to a later state files it there: a small
bug, diagnosed, with a clear fix and no trade-offs to weigh, goes straight
to Needs Impl when its description carries the problem, the reproduction,
the root cause, and the nature of the fix.

#### Needs Scope

It needs scoping: someone to define what is wanted and why, before anyone
designs how to engineer it. That covers the problem and the requirements a
solution must meet and, where the work has them, the product-level
specification of behaviour and the design of the user experience. A repo
whose work regularly needs product design or user experience design as
steps of their own splits this state in its diagram.

#### Needs Eng Design

It needs engineering design, someone to make the design decisions an
implementer would otherwise have to stop and ask about.

#### Needs Impl

The decisions are made and it needs an implementer. Nobody is working on
it.

#### In progress

Someone has claimed it and is implementing it. It needs that implementer to
finish. A Branch Issue is the one exception, described below.

#### In review

The work is finished as far as whoever did it can tell, and it needs
review: someone else confirming it was done well. What review a piece of
work needs, and whether it needs any, is a judgement that depends on the
work. While an Issue is here it is released, and it says what review it is
waiting on.

#### Closed

It needs no attention. Done and rejected are not attention states; they
are Closed plus a close reason.

#### A Branch Issue in these states

A Branch Issue's state describes the Branch Issue itself, never the states
of its children. It moves through the same states, read this way:

- Needs Triage, Needs Scope, In review, and Closed mean what they mean for
  any Issue.
- Needs Eng Design: the decisions that span its children are not yet made.
- Needs Impl: it is scoped and designed, and it needs a pass to break it
  down.
- In progress: its open children cover all the work that remains, as far as
  anyone knows. No claim is needed: a
  claim on a Branch Issue marks a pass in flight and never changes its
  state.

A Branch Issue may have children in flight in any open state. Having
children, or children being worked, moves nothing: a Branch Issue whose
first children exist to find out what the rest of the work is stays in
Needs Scope while they are worked.

### When an Issue moves

A transition is taken only when its condition holds, judged by whoever
moves the Issue. A wrong state puts later work on an earlier gap, so when
unsure whether a condition holds, leave the state as it is. An Issue enters
at, or moves directly to, any state whose earlier conditions it already
meets: an Issue that needs no engineering design passes straight through
Needs Eng Design, and a filer who knows an Issue already meets every bar up
to a later state files it there.

#### Out of Needs Triage

To Needs Scope, when all of these hold:

- The universal bar is met: a title that states the outcome; a body that says
  what is known and what is not, with no placeholder text; and an Issue
  Kind, an Issue Priority, and the entry Issue State, each set as best the
  filer can.
- Its labels conform to the Issue Label Schema.
- It carries a pointer: a code location, an observable behavior.
- For a bug, it says what was observed and what was expected.

#### Out of Needs Scope

To Needs Eng Design, when all of these hold:

- What is wanted is defined, and how it will be engineered is not:
  motivation, beneficiary, criteria, out of scope, constraints,
  adjacencies, and, where the work calls for them, the product behaviour
  and the user experience.
- A Branch Issue states its success criteria and a Leaf Issue its
  acceptance criteria; either may carry the other as well.
- For a bug, it says how to reproduce it, or for an intermittent one what
  was observed, how often, and under what conditions, enough that a
  debugger knows where to start.

Scoping a bug is reproducing it, so there is no separate investigation
state; a repo that works that way adds one to its diagram.

#### Out of Needs Eng Design

To Needs Impl, when an implementer could proceed without further design
input. For a Branch Issue, when the rest of the work could be broken down
without further design input.

#### Out of Needs Impl

A Leaf Issue moves to In progress when someone claims it, or when whoever
already holds a claim on it starts implementing. A claim moves a Leaf Issue
from Needs Impl to In progress and otherwise leaves the state as it is.

A Branch Issue moves to In progress when its scope and design bars are met
and its open children cover all the work that remains, as far as anyone
knows. The test: if every open child closed today, would the pass that
verifies it expect to close it? If more work would still need charting, it
belongs in the earliest state whose bar it does not meet.

#### Out of In progress

To In review, when the work is finished and needs review. Whoever moves it
releases the Issue and says what review it needs.

To Needs Impl, when a Leaf Issue is released with the work unfinished. No
earlier bar failed, so this is not a regression. A Branch Issue released at
the end of a pass stays in the state it is in.

#### Out of In review

To Closed, as "Into Closed" says.

#### Into Closed, from any open state

Every close carries its reason, one of the close reasons the block
declares; forge auto-close on PR merge is the one exception. A reason is
given only when its meaning holds and so does its condition here:

- `done`: a Leaf Issue's acceptance criteria hold, or a Branch Issue's
  success criteria have been checked against the outcome by the pass that
  verifies it, and everything that describes the Issue agrees with the
  change. A Branch Issue is never closed merely because its children
  closed.
- `rejected`: nothing beyond its meaning.
- `duplicate`: any context this Issue holds that the other lacks has gone
  to the other Issue first.
- `superseded`: nothing beyond its meaning.

#### Out of Closed

To an open state, when the reason it was closed no longer holds (the work
regressed, say, or it was closed unfinished). Every reopen carries its
reason. The Issue returns to the state the rule for a regression, below,
gives.

#### Back to an earlier state, from any open state

A regression is a transition like any other, whose condition is that an
earlier bar turned out not to be met. An Issue may regress to an earlier
state at any time, and no later-stage work goes on top of an earlier
stage's gap. It returns to the earliest state whose bar it does not meet. A
Leaf Issue that meets every bar returns to Needs Impl, or to In progress if
someone holds a claim on it. A Branch Issue that meets every bar returns to
In progress.

### What is not a state

"Blocked" and "waiting on a human" are not states. A blocking dependency
blocks in every state. Waiting on a human is shown per platform: the `human`
label everywhere, and on Beads a gate as well.

### Where an Issue State is recorded

An Issue State is recorded once, in the tracker's own mechanism for status
where it has one, otherwise in the one place this file designates. Only the
line for this repo's Issue Tracker applies:

- Beads: the Issue's status, once the repo's Beads holds these states as
  statuses. Until then nothing records which open state an Issue is in:
  judge it from the Issue itself, and write it nowhere, a label included.
- GitHub with a project board: the board's status field.
- A forge with no status mechanism beyond open and closed (Forgejo, and
  GitHub without a project board): not designated in the shipped default.
  A repo on such a forge designates its own place here, as a customization;
  a label axis for status is one workable choice.
