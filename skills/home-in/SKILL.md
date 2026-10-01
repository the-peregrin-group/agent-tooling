---
name: home-in
description: >
  Interrogate the user toward a defensible opinion on a problem, and capture
  the result: an artifact the user chooses, lexicon entries through
  use-lexicon, and ADRs through use-adrs. The agent reads and verifies
  against what already exists, asks one question per turn across a tree of
  Lines of Inquiry, and pressure-tests every proposition including its own.
  Trigger only on the literal phrases "/home-in", "home in on", "hone in
  on", or "zero in on" applied to a problem, decision, plan, or proposal.
  Attended sessions only. EXCLUDE: ordinary help deciding something when no
  interrogation was asked for; writing up decisions already made
  (refine-state-doc); recording one decision (use-adrs); naming one concept
  (use-lexicon); reviewing code (code-reviewer).
argument-hint: "<the problem and the outcome you want, in your own words> [in <project>] | continue from <artifact>"
---

# Home in

The user has a problem and wants an opinion on it they can defend. You get
them there by interrogation: reading what exists, asking one question at a
time across every line of inquiry the problem has, and pressure-testing
each proposition, theirs and yours. The interrogation is the product. The
documents it leaves behind (an artifact, lexicon entries, ADRs) are its
record. Act as a wise steward, not a note-taker and not a critic.

## Attended only

This skill is live collaboration. There is no unattended form, and none of
the unattended branches of the skills it uses (lexicon proposals, draft
ADRs for a reviewer) apply within it. If the session is unattended, say so
and stop.

## Two rules that hold throughout

- **One question per turn.** Never two, never a list. A turn may carry a
  finding, a correction, or a proposal before the question, but it ends in
  exactly one question. Twenty turns on one topic is normal. Several
  questions at once get partial answers, and the unanswered ones have to be
  asked again later, so the conversation fragments and repeats itself.
- **Opaque ids carry an inline summary.** The first time a turn mentions
  anything identified by an opaque id (an issue or PR number, an ADR
  number, a bead id, a branch or commit, a lettered or numbered section of
  a document), pair the id with a few words of meaning: "issue #177 (the
  Godot 2D render race)", "ADR-XXXX (OAuth2 for the authz layer)". Once
  established in that turn, the bare id may recur. Ids that behave like
  hashes (commits, bead ids) get the summary every time. A summary is only
  what it takes to retrieve the thing from memory: a few words, a short
  sentence at most. The user's memory retrieves by meaning, not by
  identifier, and every bare id is a separate lookup that fragments
  attention; ten of them in one turn is a research task.

## Terms

- A **Line of Inquiry** (LOI) is one line of questioning that must be
  examined before an opinion is defensible. LOIs form a tree: ten roots
  ship with this skill (`lines-of-inquiry.md`), and each expands into the
  domain's own finer LOIs.
- A **Line of Inquiry Exit** (LOI Exit) is the event of leaving a LOI,
  exhausted or set aside. It is the only moment formal capture happens.
- The **Resolution Queue** is the set of everything raised that awaits
  formal resolution: candidate terms with their working names, candidate
  decisions, assumptions under test, gathering not yet done. It must be
  empty before the session is done.

## Invocation

Everything after the command is free text: what the user would say to a
colleague. Read the desired outcome from it, and the problem if stated;
whatever you cannot infer becomes the first question. Two phrases are
recognized anywhere in the text:

- `in <project>`: the owning project is that project instead of the
  session's root. Whether the override succeeds is the machine's policy,
  not yours.
- `continue from <path>`: resume a parked session from its artifact. Read
  its open-items section, rebuild the frontier and the Resolution Queue,
  and carry on from there.

Documents named in the text are the first things to gather, not arguments
to parse.

## Opening move

Before the first question of the interrogation. The opening move spans as
many turns as it needs; each still ends in exactly one question.

1. Load `use-lexicon`, `use-adrs`, and `refine-state-doc`. Read
   `lines-of-inquiry.md`, and the owning project's lexicon in full.
2. State the owning project: the repo or directory whose conventions the
   deliverables follow and whose lexicon and ADRs are used. By default it
   is the session's root, the directory the session was started in.
3. Read what already exists: the documents named, and whatever the project
   holds about the topic (notes, memory, past decisions). Report what it
   establishes and what it leaves open. If the invocation arrived with a
   proposal (a PRD, a plan, a design), this report is the first pressure
   test of it.
4. Ask what the deliverables are. There is no default. Propose one from the
   project's own layout and conventions, so the user can accept in a word
   (for a proposal, often the revised proposal itself in place), but write
   nothing until they answer. Project conventions inform this proposal
   only; they do not change the rules of this skill.
5. Sketch the tree of Lines of Inquiry for this domain one level deep: one
   line per root, naming the domain's first-level children under it, for
   the user to prune or extend before you walk it.

## Three sub-processes, interleaved

These run concurrently from the first question to the last. There are no
modes; invocations differ only in what is already on the table.

**Gather.** Read before asking. When an answer names something checkable
(a project, a document, an event the project has notes on), go and read it
before the next question, and check the user's account against the record,
not only fill gaps. A discrepancy comes back plainly, with its source,
before you continue. Gathering that no immediate question depends on goes
on the Resolution Queue and is done when the conversation next pauses
anyway (the user steps away, a subtree is nearly done), or at the LOI Exit
at the latest; a subagent between every turn kills momentum. Narrate every pause in one line ("You
mentioned Foo and Bar. Let me read what you wrote about them first.").

**Interrogate.** One question per turn, each belonging to a node of the
tree. Walk a LOI to the bottom before entering the next. Say where you are
when it helps ("Still on Success: ...").

**Pressure-test.** Always on. The adversary targets the strongest current
proposition: the premises when nothing is on the table yet, the user's
proposal when one arrived with the invocation, and your own emerging
recommendation once one forms, with equal vigor. Every adversarial
question names the assumption it tests, and that assumption goes on the
Resolution Queue. Devil's advocacy with no named assumption is forbidden.

## Lines of Inquiry

`lines-of-inquiry.md` holds the ten roots, the expansion rule, and one
example expansion. The short form:

- A root is a subtree, not a question. Expand it into the domain from your
  own knowledge of that domain; the skill encodes roots, never trees.
- Expansion is lazy (a subtree expands when entered) and depth-first.
- Every LOI is considered; not every LOI is asked. Each ends either
  explored to the depth the problem warrants, or set aside with a one-line
  reason.
- Coverage is the tree's frontier: exhausted, in progress, untouched, set
  aside. Report it at every LOI Exit.
- A question you wanted to ask that fits no root is a finding about the
  roots. Surface it at the next LOI Exit.

## Line of Inquiry Exits and capture

Formal capture runs only at a LOI Exit. The procedure is in `wrap-up.md`;
in short: report the frontier and the Resolution Queue, surface questions
that fit no root, drain the queue's items from that LOI (lexicon naming
one concept per turn; the ADR gate per decision), and rewrite the artifact
in place.

Between exits, capture is deferred but definition is not. When the
discussion cannot proceed without a concept, fix its identity inline
("what is this, independent of how it is built?") and give it a working
name, marked as such the first time it appears ("call it the *open list*
for now") and on the queue. A working name is spent, not chosen: the plainest
description available, no candidate generation, so nobody grows attached.
Every working name is resolved (ratified, renamed, or dropped) at the next
LOI Exit. None survives into the artifact unratified; one that crosses an
exit unresolved is a failure the exit report calls out. Provisional
decisions ("assume X for now") work the same way.

Using a working name is a deliberate, declared deviation from
`use-lexicon`'s rule against unratified terms, confined to the span
between two LOI Exits.

## The Resolution Queue

End every reply with the queue in one or two lines, so the user always
sees what is pending:

> Resolution Queue: working names *open list*, *the burnout question*;
> candidate decision: stay through the vesting date; assumption under test:
> the new role changes the thing the user wants changed; gather: the Foo
> retrospective.

Between LOI Exits the queue also lives in the artifact's open-items
section, so a dropped session loses nothing.

## The artifact

Produce whatever deliverable the user chose at the opening move. When they
had no format in mind, the default is a state doc as `refine-state-doc`
defines it: a coherent picture as of now, with context, problem, success
criteria, recommendation, rationale, and rejected paths. It never records
turn order or who said what; it is not a transcript, and if the user wants
one, that is a separate artifact produced by other means.

Draft it at the first LOI Exit and rewrite it in place at every exit after.
The wrap-up is then a final rewrite, not a big-bang authoring step; the
user can catch a misreading early; and the Resolution Queue has a durable
home.

Refer to every ADR the artifact touches with an inline summary and a link
("because we already decided on OAuth2 for the authz layer (see
[ADR-XXXX](path))"), never a bare code. The ADR carries its own snapshot of
context and rationale regardless; overlap between the two is by design.
`use-adrs` has the rule.

## Wrap-up

Done is the user's to declare. `wrap-up.md` has the procedure: the
frontier and queue check, the offered cold read, the offered independent
review delivered unfiltered, and park-and-resume. Never start the wrap-up
without the user, and never skip the offers.
