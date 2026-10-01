# How to write an ADR

This guide is canon. Where an existing ADR or a project convention disagrees
with it, follow this guide.

## Template

```md
---
date: [YYYY-MM-DD, the day the decision was made]
status: [current | superseded]
---

# [decision title]

**Context:** [the problem and what triggered the decision; max 3 sentences; link the state doc that holds the analysis, if one exists]

**Decision:** [what was decided, concretely; max 1 sentence]

**Rationale:** [why; max 1 sentence]

## Consequences

[optional: high-impact downstream effects only, one bullet and one sentence each]

## Alternatives Considered

[never omitted; one ### per option that took real reasoning to rule out, so nobody relitigates it]

### [Name of option]

**Description:** [max 1 sentence]
**Rejection rationale:** [the trade-off that ruled it out; 1 sentence when a state doc holds the analysis, otherwise as many as it takes to stop a reader reopening the option, and no more]

## Superseded by

[only if superseded; one line per superseding ADR, appended in order, scope first]

- [ADR-XXXX](XXXX-slug.md): [entirely, or partially; what it overturned or corrected in this ADR; max 1 sentence]
```

No section has a minimum length; a fragment that does the job is enough. If
Rationale wants a second sentence, the overflow is usually a rejected
alternative (move it to Alternatives Considered) or a constraint (move it to
Context).

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

## Status and supersession

An ADR's body is never edited once the decision lands, beyond typo fixes. A
decision stays current until another decision supersedes it, even after its
rationale has aged; there is no retired or deprecated state. A changed or
corrected decision is a new ADR that names the old one in its Context. The
old ADR then gets `status: superseded` and a `## Superseded by` line naming
the new ADR and its scope, because a supersession is often partial and the
new title alone rarely says which part. Those two edits are the only
sanctioned ones.

## Citing an ADR

A bare number is a lookup the reader has to perform. Cite an ADR with an
inline summary and a link to its file, so the reader recovers the decision
from the sentence: "because we already decided on OAuth2 for the authz
layer (see [ADR-XXXX](XXXX-oauth2-for-authz.md))". The summary is a few
words, enough to retrieve the decision from memory; the link carries the
rest. This holds in prose, in other ADRs, in commit messages, and in PR
bodies.
