# Proposal: Agent integration branch

## Draft entry

For `LEXICON.md`, section "Repos and branches":

**Agent integration branch**: A non-default branch a project creates for
agents to land work into unattended, typically for one run and under a
Branch prefix the project's CLAUDE.md designates (e.g., `integrate/` in this
repo). Which branch agents may land into is pinned per run by Permission
rules. The qualifier "agent" marks the separation: an integration branch in
general is any branch work flows into, the default branch included, and a
project that lets agents land into its default branch has no Agent
integration branch, only a default branch agents may land into. Whether
agents may land into a default branch is each project's policy, not this
term's.
- _Invariants_: never the default branch; agents land into one only while
  Permission rules pin that exact branch
- _Avoid_: integration branch (unqualified, for this sense), agent trunk,
  designated base

## Relationships

- A project has zero or more Agent integration branches; each is distinct
  from the default branch (trunk), and work landed in one reaches the
  default branch only on the project's own terms.

## Naming questions

1. Why a term: the CLAUDE.md designation, the rebase loop (`gitw-rebase
   ... onto`), and unattended PR merges all refer to the concept, and the
   unqualified "integration branch" already has its generic git sense in
   use-git's History Policy ("the trunk, the integration branch everything
   flows into").
2. Core identity: a non-default branch a project creates for agents to land
   work into unattended, pinned per run by Permission rules.
3. Candidates: Agent integration branch (chosen: keeps the familiar
   "integration branch" and adds the one qualifier that separates it from
   the generic sense), Integration branch (rejected: clashes with trunk as
   "the integration branch everything flows into"), Run branch (names the
   lifetime, not the role), Designated integration branch (says who
   designates, not who lands).
4. Collisions: none with an entry, an Avoid word, or a retired term. The
   clash flagged in the earlier draft, with use-git's "the trunk, the
   integration branch everything flows into", is resolved by the qualifier:
   that sentence keeps the generic sense, and this entry names only the
   agents' non-default branch. "Branch Issue" (Tracking Work) uses "Branch"
   in an unrelated sense.

Judgement for the reviewer: the litmus test may reject "pinned per run by
Permission rules" as implementation. If so, keep the invariant as "agents
land into one only while it is explicitly granted" and leave the mechanism
to the docs below.

## In code

- CLAUDE.md, section "Agent integration branches" (the designation of
  `integrate/`)
- docs/projects/gitw/design.md, the `gitw-rebase` onto form and the
  operating modes
- skills/use-git/SKILL.md, operating mode (b), The Verbs, Unattended
  Sessions
- cli/gitw-rebase (docstring)
