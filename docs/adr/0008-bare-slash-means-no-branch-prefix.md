---
date: 2026-10-06
status: current
---

# A bare `/` branch prefix means no branch constraint, excluding the default branch

**Context:** Every mutating gitw Verb demanded a `fix/`-style Branch
prefix, so no grant could reach a branch without one, such as a
human-created branch whose open PR is handed to an agent, and renaming
that branch would destroy the PR. The prefix has no value of its own: it
segments permissions only when a Permission rule pins a particular
value, so in a repo with no prefix-specific rules it was pure toil. The
current mechanics are in the [gitw design](../projects/gitw/design.md).

**Decision:** Wherever a Branch prefix token exists (the mutating gitw
Verbs and `fjw-pr-comment`), a bare `/` is accepted and admits any
branch except the repo's authoritative default branch, while every
other value keeps the grammar lowercase, single-level, ending in `/`.

**Rationale:** The Wrapper's job is to make a capability grantable at a
pinnable scope, not to decide policy, so the unconstrained scope must
exist and be spelled as one literal that rules can grant or withhold.

## Consequences

- A real prefix can never match a slashless default branch like `main`,
  and `gitw-commit`, `gitw-integrate`, and `gitw-branch-start resume`
  relied on that implicitly; under `/` the shared scope check refuses
  the default branch explicitly.
- Under `/`, a `gitw-branch-start` name or a `gitw-push` target is the
  whole branch name, so slashes are allowed in it.
- An existing starred grant such as `gitw-commit <label> *` now also
  admits branches without a prefix.
- `fjw-pr-comment`, which accepted any non-empty string, now takes the
  same grammar as gitw.

## Alternatives Considered

### Make the token optional

**Description:** Let a Verb omit the prefix argument entirely.
**Rejection rationale:** The scope position would then hold either a
prefix or the next argument depending on its content, which breaks the
rigid positional grammar that lets a rule's literal prefix be the grant.

### The empty string

**Description:** Accept `""`, which is a prefix of every branch, so
matching needs no special case.
**Rejection rationale:** It has no unquoted spelling, so `""`, `''`,
and `$''` are equally natural ways to write it. Prefix rules match the
command text, not the parsed argument, so a rule pins only one of them.
An allow rule then prompts on the others, and a deny rule fails open.
Every token can be deliberately requoted; the empty string is the one
whose variants occur by accident.

### A reserved word such as `any`

**Description:** Spell the unconstrained scope as a word.
**Rejection rationale:** It reads like a prefix and would collide with
a legitimate `any/`. `/` cannot be a real prefix, because a git ref name
cannot begin with a slash, and it needs no quoting in bash or zsh.

### Exact branch names only

**Description:** Let the token name one exact branch instead of a
class, with no unconstrained form.
**Rejection rationale:** It covers the single-handoff case but still
forces a token value no rule cares about in repos without prefix rules.
It also leaves the policy choice in the Wrapper rather than in the
rules.
