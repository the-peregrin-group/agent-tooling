# Proposal: Integration branch

## Draft entry

For `LEXICON.md`, section "Repos and branches":

**Integration branch**: A branch, named under a Branch prefix the repo
designates, that agents may rebase onto and land work into unattended, in
contrast to the repo's default branch (trunk), which only a human advances.
Each one serves a bounded run of work and is disposable afterwards (e.g., one
per work session).
- _Invariants_: never the repo's default branch; an agent may land work in
  one only while a Permission rule pins that exact branch; removing those
  Permission rules retires it
- _Avoid_: agent trunk, designated base

## Relationships

- A repo designates zero or more Integration branches, all under one
  designated Branch prefix; work landed in an Integration branch reaches
  the default branch only through a human.

## Naming questions

1. Why a term: the designation, the rebase loop (`gitw-rebase ... onto`),
   and unattended merges all refer to the concept, and "integration branch"
   alone is ambiguous in git usage (the default branch is also called the
   integration branch in the use-git skill's History Policy).
2. Core identity: a non-default branch agents may advance unattended, under
   a repo designation and a per-run Permission rule pin.
3. Candidates: Integration branch (chosen: the name already in use in the
   use-git skill, the gitw design doc, and this repo's CLAUDE.md; it fails
   the ambiguity test against "the trunk is the integration branch
   everything flows into", so the entry needs its contrast with the default
   branch, or the skill's History Policy wording should change), Designated
   integration branch (narrower, wordier), Run branch (names the lifetime,
   not the role).
4. Collisions: no entry, Avoid word, or retired term. Partial overlap with
   the everyday sense of "integration branch" for trunk, as noted above.
   Also note "Branch Issue" (Tracking Work) uses "Branch" in an unrelated
   sense.

Judgement for the reviewer: the litmus test may reject "pinned by a
Permission rule" as implementation; if so, keep the invariant as "an agent
may land work in one only while it is explicitly granted" and leave the
mechanism to the docs below.

## In code

- CLAUDE.md, section "Integration branches" (the designation of
  `integrate/`)
- docs/projects/gitw/design.md, the `gitw-rebase` onto form and the
  operating modes
- skills/use-git/SKILL.md, operating mode (b), The Verbs, Unattended
  Sessions
- cli/gitw-rebase (docstring)
