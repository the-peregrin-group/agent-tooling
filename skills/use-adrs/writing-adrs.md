# How to write an ADR

This guide is canon for every ADR written from now on and for every true-up
of an existing one. An ADR written to an earlier standard is still read by
the one decision it records, not judged by its format; `SKILL.md` ("Reading
ADRs") has that rule.

## Template

```md
---
date: [YYYY-MM-DD, the day the decision was made]
status: [current | amended | superseded]
---

# [decision title]

**Context:** [the problem and what triggered the decision; max 3 sentences; link the state doc that holds the analysis, if one exists]

**Decision:** [what was decided, concretely; max 1 sentence]

**Rationale:** [why; max 1 sentence]

## Consequences

[optional: high-impact downstream effects the deciders foresaw and accepted, one bullet and one sentence each]

## Alternatives Considered

[never omitted; one ### per option that took real reasoning to rule out, so nobody relitigates it]

### [Name of option]

**Description:** [max 1 sentence]
**Rejection rationale:** [the trade-off that ruled it out; 1 sentence when a state doc holds the analysis, otherwise as many as it takes to stop a reader reopening the option, and no more]

## Amended by

[only once a later ADR has changed this ruling; one line per amending ADR, appended in order]

- [ADR-XXXX](XXXX-slug.md): [what it changed in this ruling; max 1 sentence; starts "Fully superseded:" when it displaces whatever was left]
```

No section has a minimum length; a fragment that does the job is enough. If
Rationale wants a second sentence, the overflow is usually a rejected
alternative (move it to Alternatives Considered) or a constraint (move it to
Context).

## One decision

An ADR records one narrow decision. Most ADRs that later need amending
recorded several decisions at once, or recorded implementation as though it
were the decision: the wider the scope, the longer the ADR, and the more of
it turns out to be speculation about an implementation nobody had built yet.
Before writing, agree with the user on the one decision being recorded, in
one sentence.

Then test each clause of the draft Decision, and each option in Alternatives
Considered, against the gate in `SKILL.md` as though it stood alone:

- **It fails the gate:** it is implementation or speculation, and it stays
  out. "Backups run from cron" is cheap to reverse and surprises nobody; the
  decision it implements, "the orchestrating host pulls each host's data
  rather than each host pushing it", is the ADR.
- **It passes, but answers a different question:** it is a second decision,
  and it gets its own ADR.

Alternatives Considered holds the options for the one decision: pull versus
push, never cron versus systemd.

## A self-contained snapshot

An ADR is the minute of a meeting: it records a decision, with its context,
rationale, and alternatives, as they stood at the moment the decision was
made. It carries all of that itself even when a design doc holds the full
analysis, and it duplicates that doc on purpose. The design doc is a state
doc and may be rewritten tomorrow; the ADR is the snapshot that must
survive the rewrite. Never write "see the design doc" where the context or
rationale should be. When a design doc exists, Context links it, and the
design doc in turn summarizes and links the ADR; the overlap between them
is the design working, not a defect to deduplicate.

## Length

The limits on Context, Decision, and Rationale are hard in every case, and
they are routinely ignored; do not be the agent that ignores them. Full
analysis across several options and axes belongs in the design doc, never
here. Alternatives Considered is the one section that flexes, and it is
never omitted: the gate requires that real alternatives existed, and the
snapshot must show what was on the table.

- **A state doc holds the analysis.** Context links it. Each alternative
  gets one sentence of description and one of rejection rationale.
- **The ADR stands alone.** Description stays at one sentence. Rejection
  rationale runs as long as it takes to stop a future reader from reopening
  the option, and no longer: cut any sentence whose absence would not tempt
  a relitigation.

An ADR grows only through this section, never through longer sentences
elsewhere.

## After an ADR lands

An ADR records one decision as it stood at the moment it was made: the
ruling, the reasons that held then, and that moment. Those are the
decision's identity. Changing any of them, the date included, rewrites
history rather than correcting the record. Two other things may change: how
well the decision was written down, and where it stands now.

### Capture fixes

A capture fix corrects how a decision was written down without changing what
was decided: a guideline the ADR breaks, implementation detail stated as
decision, a design doc written inline where a link belonged, two decisions
recorded as one. The user ratifies every capture fix, so one is made only in
an attended session.

If a fix brings in information that was not known when the decision was
made, you are almost certainly changing the substance: stop, and treat it as
a new decision. The exception is information showing that the record
misstates the decision, such as the user saying its author misunderstood the
ruling.

An objective fix, which makes a broken thing not broken with no judgment
involved, needs no ratification and may be made in any session:

- A typo.
- A link repointed to the same document's new path after a move. When the
  document was merged into another, choosing its successor is a judgment
  and goes to the user; when it was deleted with no successor, the link
  stays as it is.
- A note on a renamed term, where the lexicon records a one-to-one rename
  with no change in meaning: "the command policy (now called Permission
  rules)". The original word stays. A term that was merged, split, or
  redefined gets no note. An ADR that keeps a retired term is not drift: the
  term was correct when the decision was made.

### Truing up an existing ADR

Bringing an existing ADR, typically one written before this guide, up to the
template is a set of capture fixes, and it is never required. Do it when the
user asks. Attended, when you notice an ADR that breaks this guide, offer to;
unattended, edit nothing and mention it in your final report. Before any
true-up, name the one decision you take the ADR to record and get the user's
agreement; everything else follows from it.

### Status, amendment, and supersession

`status:` records where the decision stands, and it is the one frontmatter
field that changes:

- `current`: the decision is in full effect, as recorded.
- `amended`: the decision is in partial effect; later ADRs, listed under
  `## Amended by`, have changed part of its ruling. `amended` refers to the
  ruling, never to edits of the text.
- `superseded`: the decision is no longer in effect; later ADRs have
  displaced all of it.

An ADR with no `status:`, written before this guide, is `current` and gains
the field when it is first amended.

A changed decision is always a new ADR, which names the old one in its
Context. The old ADR gets a `## Amended by` line naming the new ADR and what
it changed, and its status moves to `amended`. When the new ADR displaces the
whole ruling, or whatever earlier amendments left of it, the status moves to
`superseded` instead and the line starts "Fully superseded:". A later ADR
that only builds on this one, changing nothing it ruled, is not an amendment
and is not listed. A decision stays current until another decision amends or
supersedes it, even after its rationale has aged; there is no retired or
deprecated state.

### Observations after the decision

What is learned after the decision, about how it played out, never goes into
the ADR, Consequences included. Consequences records what the deciders
foresaw and accepted; a later addition there claims they weighed something
they never saw. The test is provenance: was this known when the decision was
made? A known effect the author left out is a capture fix. An unforeseen one
is an observation, and it goes in the project's Known gaps with its Issue
when it is a defect in what shipped, or in an Issue otherwise. If acting on
it would change the ruling, that is a new ADR that amends this one.

## Adopted ADRs

An ADR adopted from another project's decision record carries the date the
decision was made there, not the date it was adopted here: adopting records
a decision without making one, and the date is part of the decision's
identity. A later ruling on the same question is a separate decision with
its own date, so it is a separate ADR, amending the first if it changed it,
even when both are adopted at once.

## Citing an ADR

A bare number is a lookup the reader has to perform. Cite an ADR with an
inline summary and a link to its file, so the reader recovers the decision
from the sentence: "because we already decided on OAuth2 for the authz
layer (see [ADR-XXXX](XXXX-oauth2-for-authz.md))". The summary is a few
words, enough to retrieve the decision from memory; the link carries the
rest. This holds in prose, in other ADRs, in commit messages, and in PR
bodies.
