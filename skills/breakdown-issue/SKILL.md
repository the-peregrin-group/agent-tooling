---
name: breakdown-issue
description: >
  Work a Branch Issue (an Issue that holds other Issues as its children, an
  epic for instance) in a pass: check its scope against its children and
  fix any mismatch, ending either by reorganizing its children (adding,
  removing, or redrawing their boundaries), with the whole reorganization
  drafted before any of it is filed, or by verifying it against its success
  criteria. Load before claiming a Branch Issue, when an Issue proves
  bigger than one session, and when deciding whether an Issue belongs under
  a parent. Triggers: "break this down", "break this epic down", "split
  this issue", "is this epic done", "verify the epic". EXCLUDE: filing one
  Issue (create-issue) and a triage pass over the whole tracker
  (triage-issues).
---

# Break down an Issue

The concepts are the lexicon's **Branch Issue** and **Leaf Issue**
([LEXICON.md](https://github.com/the-peregrin-group/agent-tooling/blob/main/LEXICON.md)),
and the lexicon is authoritative for them. This skill is written against no
platform: for the command behind a step, run your wrapper's help for the
Verb, or load your tracker's platform skill (`use-bd` for Beads).

## What a Branch Issue's work is

A Branch Issue's work is management: scoping, setting success criteria,
breaking down, and verifying completion. It is worked in session-sized
passes, is ready exactly when it has no open children, and is never closed
merely because its children closed. Ready says when a pass is due
unprompted. A pass may also be started for cause while children are open: a
child that does not belong under it, or one whose boundary was drawn wrong.

An Issue is a Branch Issue if it has any children, open or closed, or if it
is of a kind designated to hold children (e.g., an epic), even before it
has any. A new Branch Issue is ready work at once, and its first pass
breaks it down.

A Branch Issue states success criteria, which its verifying pass checks
against the outcome. A Leaf Issue states acceptance criteria and is closed
when they hold. Either may carry the other as well.

## A pass

A pass is one session's work on a Branch Issue: it checks the Branch
Issue's scope against its children and fixes any mismatch, ending either by
reorganizing its children (adding, removing, or redrawing their boundaries)
or by verifying it against its criteria.

1. Before touching the Branch Issue, make it visible that you are working
   on it, since one person or agent advances an Issue at a time.
   An agent sharing its session's Actor ID (a sub-agent, a workflow agent)
   does not claim, close, or rewrite: it drafts the pass and hands the
   draft to the session that holds the claim.
2. Read the Branch Issue's scope and success criteria, then every child,
   open and closed. Judge every move against the repo's Issue State
   Diagram, the Branch Issue's own moves included.
3. End the pass in one of the two ways below.
4. Before you stop, close or release everything you hold. The pick-up note,
   a section of the Branch Issue's description, says where the pass left
   it.

### Ending by reorganizing

A pass drafts its whole reorganization before filing any of it, with no
placeholder breakdown or acceptance tasks. Children added in a pass become
ready work as soon as they exist.

- **Draft** every change first: each new child's title, body, Issue Kind,
  Issue Priority, Issue Labels, and dependencies, and each change to a
  child that already exists.
- **Adding.** File each new child under the Branch Issue, to the same
  filing bar as any Issue (`create-issue`), in one sitting.
- **Removing.** A child whose scope is not part of the Branch Issue's scope
  leaves it: closed with its reason when the work is not wanted, moved out
  from under the Branch Issue when it is wanted elsewhere. An Issue is
  closed, not deleted; the closed Issue stays as the record.
- **Redrawing.** A child whose boundary is wrong has its description
  rewritten in place, or is split or merged.
- **Relationships.** Record every relationship with its type explicit;
  blocking is never the default, because a wrong blocking link silently
  hides work.

Changing or destroying existing data requires more delegation than purely
additive change. Within that, less judgement is needed when the action
merely executes an existing, already-authorized plan (forming Issues from a
design document's scope, say), and more when the agent is making the
decision itself rather than carrying one out (inferring a new overarching
project and reparenting existing Issues under it). So adding children is
routine, and removing or redrawing them may be denied or asked: if the
grant exists, do the act; if not, that is the answer. Unattended, an act
that would need a person's approval is written up as a proposal in the
report instead of attempted. Never take over someone else's work in
progress: when a child you would remove or redraw is claimed, ask.

### Ending by verifying

When every child is closed, check the Branch Issue's success criteria
against the outcome. A parent's status is judged against its own definition
and criteria, not on the state of its children. Then close it, with its
reason. A verifying pass that finds the criteria unmet ends as a
reorganizing pass. An Issue is done only when everything that describes it
agrees with the change.

## What goes under a parent

An Issue goes under a parent only when its scope is part of the parent's
scope: work bigger than a session is a Branch Issue, broken down into
children. A dependency or a shared schedule is never by itself a reason to
group; link it instead. Prefer vertical slices and do not over-decompose.

## Sizing a Leaf Issue

A Leaf Issue is one focused task sized for one session, whether an agent or
a human does it. Anything bigger is a project, not a task, and is tracked
by a Branch Issue whose children are Leaf or Branch Issues; it is never
shoehorned into a Leaf Issue. A Leaf Issue that proves bigger than a
session is reorganized as a Branch Issue and broken down into session-sized
children.

"Session-sized" is a subjective, best-effort guideline: a task that runs
past one session simply carries into the next, with no extra Issues. Split
off a sibling Issue only when the remainder cannot be done now, or is
substantial.
