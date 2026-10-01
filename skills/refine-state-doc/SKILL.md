---
name: refine-state-doc
description: >
  Guidance for writing and refining effective "state docs" (vs. their counterpart, "stream docs").
  Load proactively when working with a known "state doc" (vs. a "stream doc"), or when directed
  explicitly by the user or another agent to refine a specific state doc.
---

# Refine state doc

## What makes a good state doc?

Above all: clarity and concision. If I can't understand the current state easily (without reading an encyclopedia's worth of text or doing complex mental gymnastics to reconcile conflicting data), it's a failed state doc.

- Fixed moment in time: It tracks the state of an entity (could be anything from a software design, a business plan, a
  person in a rolodex, an owned vehicle) at a fixed point in time ("now" / "current state" by default).
- Focus on the target time: The first priority is to clearly convey the totality of state at the target time. Everything
  else is a distraction (including the history of how we got there).
- One clear owning section for a given piece of state: There is one place where a single piece of "leaf-node"/detailed
  state is stored, and only one. All other mentions are referential to this one place.
- Clear organizational hierarchy and progressive disclosure: Big-picture, summary, key-data at the beginning; minute,
  in-the-weeds details at the end; a clear and understandable progression of increasing levels of detail between the
  two ends.

## How to refine a state doc

Obviously, improving a state doc comes by finding anti-patterns to the rules above and fixing them. In particular, I
suggest:

### Process

If a `use-privacy` skill is listed among your available skills, load it before composing any text bound for outside
this machine: a state doc in a repo that is pushed or shared.

1. **Establish your desired organization:** What are all of the things that need to be conveyed? Where should be the one
   dedicated "owning" home for each piece of relevant data? Should some of them live in other docs entirely with references
   only in this doc? Where are cross-references useful? How can you reorder the doc to maximize organizational hierarchy
   and progressive disclosure (i.e., most important things first, least-used things last)?

2. **Identify the current state for each data point:** Consolidate all of the various mentions of a piece of data
   and determine which one is actually accurate as of the point-in-time of the doc. 

3. **Fill in your desired organization with the correct data:** Clearly and concisely lay out the correct state you have
   identified using your desired organization as the template. In particular, _drop all references to past states,
   transitions, meta-process, etc._ that are not relevant to the doc's target point-in-time.

### Guardrails

- **"Embedded stream" sections (see below) _are_ in-scope for rewriting.** Stream sections catalog a stream of real or
  conceptual events, and their value is derived precisely from that incremental history. Do not eliminate the event
  statements, but you _can_ delegate elaboration to an appropriate state section or separate state doc when it makes
  sense.
  
  For instance, if a TODO includes a two-paragraph in-depth description of the user auth model for a software project but the state section is precisely a design document for that software project, the TODO could be reduced to `implement user auth model [link to auth model design].` If a "work log" stream entry describes plumbers scoping a sewer and making numerous discoveries, but then also reiterates the entire known system state, keep the _event statements_ but delegate the description of the overall sewer system to the relevant state section (or separate doc).

- **Currency stamps should not be updated:** You're rewriting, not changing the actual state. If you observe that the
  state already described suggests a newer currency stamp, raise it with the user, but don't unilaterally change it.

- **Mention detected staleness, but don't act on it:** if you notice that a doc outdated information in it, mention it to
  the user in the form of a single-sentence generic FYI at the end (see below). The reason for _NOT_ enumerating all issues
  discovered without prompting is that often the user already knows and wants to focus on your revision, not the staleness
  (which, in context, is more noise than signal).

  > I saw things in this doc that are clearly out of date; let me know if you want to dig in.

Assess the quality of your output at the end by comparing against the invariants in [What makes a good state doc?](#what-makes-a-good-state-doc) above. Iterate again if needed.

## Exceptions

There are a few types of state that look like "history" or "narrative" at first glance, but which are actually important state. Presenting them correctly comes down to recognizing why they're there and why they add value:

- Alternatives considered: don't present these as history. Present them as context that define the current plan by having
  been explored and ruled out (and most importantly, the key reasons why).
- Major reversals in decisions: the important state here comes from the likely case that the reversed decision _looked_ 
  like the right one at some point and likely will look enticing to somebody again in the future. Without a record of why
  the reversal happened (in terms of the decision-making criteria, not the history), it's likely to be forgotten or
  relitigated.
- Root causes and conditions: imagine the case of a plumbing project; one could categorize the account of what went wrong as
  "history" and eliminate it, but this would be a mistake. The date, time, start conditions, and sequence of events that led
  to e.g., a sewer backup ARE the base state upon which the whole project persists.
- "Embedded" streams: sometimes mini "stream docs" are embedded within a state doc, e.g., TODOs, work logs, revision logs, etc. See the dedicated sub-section below.

In the case of all of these exceptions, however, _how_ they are presented is very important. They should not be
_interleaved_ with current state, but rather separated out and placed in the organizational hierarchy where is most
appropriate for the level of detail they convey. For instance:

- Alternatives considered and major decision changes: these often go together and they are often two halves of the same
  coin. They may be used individually or together in keeping with practices of the given document.
  - "Alternatives considered" is state, and is kept to preserve the reasoning (not the history/events/process) behind the
    decision ultimately made. The important bits here are the trade-offs considered and the ultimately disqualifying
    reason because of which a given alternative was not selected. When, how, by whom, etc. the alternatives were considered
    are not germane.
  - "Major decision changes" or "major decision reversals" is stream of events. One captures these _events_ to preserve the
    entity's history and, in particular, to preserve decision provenance so that past decisions are not mindlessly
    relitigated.
  - One can use both by having state sections that describe alternatives considered (and rejected) while also recording the
    event/process context of those rejections in a stream section "decision/revision/design/etc. log" at the end of the doc.
- Account of a motivating plumbing incident: summarized very briefly and concisely at the top of the doc to motivate the
  project, with a long-form play-by-play account at the end in an appendix.

### Embedded streams and stream doc counterparts

In general, it is ok to embed a "stream" section inside of a state doc, but the following must be true:

1. Stream sections are, almost by definition, the most "in the weeds details" there are, and thus should usually come at
   the _end_ of a state doc.
2. Embedded stream sections own events (i.e., "history"); state sections own facts. A stream "event" might be "on this date
   we learned/decided/received/did/were told/etc. XYZ." Entries are therefore naturally _diffs_, whereas state sections
   encode _values_. (In the case of a TODO list, it's still an event: an incomplete TODO is a _future_ event, e.g., "_will_
   decide/receive/do/..." whereas a complete TODO is a past event.) An entry may point to sections written later, but must
   contain nothing learned after its date.
3. Stream sections must be _additive_. All core facts should live outside of stream sections. Moreover, it should not be
   necessary to read through and rationalize an entire stream section of a state doc to understand the current state of the 
   entity at a high-level. For instance, I should be able to tell what the current design is for a software project by
   reading the first high-level sections of the doc, and I should _not_ have to read through an entire trailing "revision 
   log" and mentally merge all of its entries to arrive at the current state.
4. The stream should add something _important_, and should still be _distilled_. If the stream is just one-for-one
   duplicating git commit diffs (e.g., "added these characters, rewrote this sentence"), it should be deleted. (Note that
   the "same as git" criterion can never apply to a stream of data that is not available in git, e.g., real-world events.)
   
   For instance, a "revision log" that includes diffs of incremental document polish changes and rewrites does _not_ add
   anything useful that is not already available from git history. If I want to know how the doc was constructed, git 
   history is far better.
   
   A useful "revision log" focuses on a distilled list of key changes that have semantic importance to understanding the
   current state of the project (e.g., "originally planned on approach Foo but switched to Bar on YYYY-MM-DD after
   attempted implementation surfaced unanticipated and unacceptable costs").
5. A stream should only be embedded if it is bounded, small, and has no other more natural home. If it does not meet these
   criteria, the stream section should live in a dedicated separate document (whether new or existing).

   For instance, a list of 15 TODOs required to complete a project is fine. A list of major decision reversals (of which
   there will never be too many) is fine. A list of the 4 different working sessions in which plumbers came to complete a
   sewer line replacement is fine.

   On the other hand, the work log for an ongoing weekly yardwork contract that goes on for years _demands_ a separate
   "work log" document (which can be referenced from the state document). It is unbounded and will quickly grow to be far
   longer than the state doc itself.

### About embedded TODO lists

TODO lists are especially tricky because they have a tendency to represent _both_ state _and_ stream. This is, however, a bad smell that should usually be corrected.

The role of a TODO list should ONLY be tracking progress through a project/initiative. _Tracking_, not _defining_.

That, in turn, means two things:

1. With one exception, the plan of work to be done should be defined as part of the core state of a doc, not only in the
   doc's "TODO" stream section. The one exception: meta-TODOs about altering the state doc itself (e.g., "extend the plan to
   cover running on both worktrees and repo main working copies").
2. TODOs themselves should be short-hand invocations of known parts of a plan (known because they are defined in the plan's
   "state" sections). For instance, if there's a section of a construction plan that details how trim is going to be cut,
   stained, finished, and installed, the TODOs can be terse items like "take trim rough measurements," "rough-cut all trim
   lengths," "pre-treat all trim boards," etc., rather than each of those TODOs being its own in-depth novella about how to 
   accomplish the task.
3. Event/process/history-focused notes about the completion of the task _are_ ok on _completed_ TODOs, as that is a perfect
   match for the stream philosophy.

If you come across a badly fudged TODO list (i.e., tons of state encoded in the TODOs only, verbose TODOs, TODOs at a very
different level of granularity than anything in the doc, or seemingly orthogonal to the doc's core focus), it's best to:

- In an attended session: raise the concern with the user and work through resolution interactively.
- In an unattended session: leave the list untouched and report the smell.
