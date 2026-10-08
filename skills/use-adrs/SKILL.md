---
name: use-adrs
description: >
  Read and write Architecture Decision Records (ADRs): where a project keeps
  them, numbering and file naming, the three-part gate for what deserves one
  (several real options, costly to reverse, surprising without context), the
  Context/Decision/Rationale format, the optional Consequences and required
  Alternatives Considered sections, and which edits a landed ADR takes. Load
  before creating or editing anything under an ADR directory, when a design
  or project decision is being made or revisited, when a proposed change
  contradicts a recorded decision, and when the user asks why something was
  decided. Triggers: "write an ADR", "record this decision", "should this be
  an ADR", "why did we decide", "supersede ADR", "amend ADR", "true up this
  ADR", "what did we decide about". Applies to non-code repos too (knowledge
  vaults, business and project decisions). EXCLUDE: general documentation,
  design docs, and plans (state docs, see refine-state-doc), vocabulary
  (use-lexicon), and issue tracking.
---

# Use ADRs

An ADR, Architecture Decision Record, is one decision and its why, recorded
at the time it was made. This skill covers when to read and write them.

ADRs live in `meta_docs/adr/` when the project has a `meta_docs/` directory
(docs about the project, kept apart from user-facing `docs/`), otherwise in
`docs/adr/`. Create the directory if it is missing. If ADRs already exist
somewhere else, ask before creating a second home; do not adopt their
format.

ADRs are numbered from `0001`, zero-padded to four digits; a new ADR takes
the highest existing number plus one. Gaps are never backfilled and ADRs are
never renumbered. Filenames are
`XXXX-kebab-case-slug.md`.

## Why and when

ADRs preserve *why* a decision was made, so that later decisions stay
consistent with it, settled questions are not relitigated, and an obsolete
decision can be recognized as such. Anything that does not serve that goal is
cut, including the ADR itself.

Offer to write one only when all three hold. If unsure whether they do, offer
anyway and name the criterion in doubt. Never create one unasked.
Unattended, a gate-passing decision you had to make yourself gets a draft ADR
in the same change, called out for the reviewer; the review is the
ratification.

1. There were several compelling options. One decent option is no decision.
2. Reversing it later would be expensive. Cheap to change means not worth recording.
3. It would surprise a reader without the background.

## Reading ADRs

Skim the ADR titles before design work in an area they may cover, and read
the ones that apply. Before proposing anything that contradicts a recorded
decision, cite the ADR and propose a new one that amends or supersedes it
rather than diverging silently. When asked why the project does something,
look here first.

Check `status:` first: a `superseded` ADR binds nothing, and an `amended`
one binds only what its `## Amended by` lines leave standing. An ADR with no
`status:` is current.

What binds is the one decision an ADR records: the part that would pass the
gate above on its own. ADRs written to an earlier standard often carry
implementation detail, sometimes so prominently that it reads as the
decision; replacing that detail does not contradict the ADR and needs no new
one. Before you treat any part of an ADR as non-binding, name the decision
you take it to record, so the user can correct you. Then, attended, offer to
true the ADR up (`writing-adrs.md`); unattended, mention it in your final
report.

## ADRs are not _the_ documentation

An ADR is a stream doc: one decision at one point in time, and that decision
is never rewritten; `writing-adrs.md` says which edits it does take.
Everything else, including what the decision produced and how it works today,
belongs in the project's state docs.

## ADRs in non-code repos

The same gate and format apply in non-code repos, a knowledge vault for
instance, to project, business, and life decisions.

## Examples of ADR-worthy decisions

- Rejecting the obvious choice
  - "We price in Swiss Francs even though every customer is in the US."
- A non-obvious constraint
  - "No S-corp election, despite the standard advice, because we hold appreciating assets."
- An identity decision
  - "This is written in Go."
  - "We are a non-profit."
- Removing a capability
  - "Cameras get no internet access at all."

## How to write an ADR

If a `use-privacy` skill is listed among your available skills, load it
before composing any text bound for outside this machine: an ADR in a repo
that is pushed or shared.

See `./writing-adrs.md`.
