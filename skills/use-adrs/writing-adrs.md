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

**Context:** [the problem and what triggered the decision; max 3 sentences]

**Decision:** [what was decided, concretely; max 1 sentence]

**Rationale:** [why; max 1 sentence]

## Consequences

[optional: high-impact downstream effects only, one bullet and one sentence each]

## Alternatives Considered

[optional: only alternatives that took real reasoning to rule out, so nobody relitigates them; one ### per option]

### [Name of option]

**Description:** [max 1 sentence]
**Rejection rationale:** [the trade-off that ruled it out; max 3 sentences]

## Superseded by

[only if superseded; one line per superseding ADR, appended in order, scope first]

- [ADR-XXXX](XXXX-slug.md): [entirely, or partially; what it overturned or corrected in this ADR; max 1 sentence]
```

No section has a minimum length; a fragment that does the job is enough. If
Rationale wants a second sentence, the overflow is usually a rejected
alternative (move it to Alternatives Considered) or a constraint (move it to
Context).

## Status and supersession

An ADR's body is never edited once the decision lands, beyond typo fixes. A
decision stays current until another decision supersedes it, even after its
rationale has aged; there is no retired or deprecated state. A changed or
corrected decision is a new ADR that names the old one in its Context. The
old ADR then gets `status: superseded` and a `## Superseded by` line naming
the new ADR and its scope, because a supersession is often partial and the
new title alone rarely says which part. Those two edits are the only
sanctioned ones. Cite ADRs as `ADR-XXXX`, pointing at the sibling filename.
