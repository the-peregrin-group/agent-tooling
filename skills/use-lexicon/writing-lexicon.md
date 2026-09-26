# Writing LEXICON.md

## What LEXICON.md is

_A glossary, not an encyclopedia._ Its sole job is to ensure that everyone — humans, agents, and other documents — uses the same terminology to mean the same things (in domain-driven design terms: the "ubiquitous language" of the bounded context this repo addresses).

### What belongs

- The canonical identifiers for entities in this repo's domain
- For each: a conceptual definition that bridges business purpose and applied solution
- Qualitative invariants that any valid implementation must uphold
- Relationships between entities (hierarchy, cardinality, sibling distinctions)
- Flagged ambiguities and how they're resolved

### What does NOT belong

- Technical specifications: IP ranges, ports, paths, schemas, model numbers, capacities, versions
- Configuration values
- Implementation choices that could change without altering the concept
- Tradeoff rationale (that's an ADR)
- Operational state (deployment dates, current status, who-owns-what)

### Litmus test

> If the concrete implementation changed tomorrow — renumber, hardware swap, vendor change, topology revamp — would this entry still read true?

If yes, it's pitched at the right level. If no, you've slipped into encyclopedia territory and the content belongs downstream.

### Resolving ambiguity

The test: whenever a reader feels ambiguity, "what kind of ___ do you mean?" must have exactly one clear answer.

Every term defined in `LEXICON.md` should be considered to have an implicit `<Context Name>` specifier in its definition. E.g., in `LEXICON.md` for `MyApp`, every term is implicitly `MyApp <Term>`.

When a term is ambiguous _within_ the lexicon, improve the chosen term so that it is unambiguous and/or add a narrowing specifier to make it unambiguous.

Example: the term "allowlist" is almost certainly ambiguous in _any_ `LEXICON.md`. Improve by adding a narrowing specifier, e.g.,

- `Port Allowlist`
- `User Allowlist`
- `Hostname Allowlist`
- `Tool Allowlist`

These specifiers can be dropped in usage when the narrower meaning is clear (e.g., `Port` in `Port Allowlist` is unnecessary in a discussion focused soley on port configuration), but they must be part of the definition.

### Authority and drift

LEXICON.md is _authoritative for the concept._ Downstream documents in the repo will be authoritative for the _implementation._ If two downstreams disagree on an implementation detail, that's a downstream consistency problem, not LEXICON.md's job to adjudicate.

### "Avoid" terms

The "avoid" list for each lexical entry is _optional_ and _need not be exhaustive_. It is meant to steer readers away from common synonyms or other easily-confused concepts. Don't try to preemptively guess all possibly confused terms. Add to the list when terminology misuse is actually observed.

### Group entries to bring order

Add as many levels of nested subsection headings as makes sense, given the size of the lexicon, to group related entries into readable chunks. Soft max: don't have a single section with more than 10 entries.

## Be concise

Enough said.

## Structure

```md
# [project name]

[A single sentence describing the context of the project. Link to README or similar if more is required.]

## Entries

### [Optional subsection heading for grouping large lexicons]

**User:**
A unique human who uses the application. A single human engaging with the application multiple times
in parallel is still a single user.
_Avoid: account, customer_

**Account:**
The in-app entity that represents a single identity for a `User`. Nothing stops a `User` from having
multiple `Account`s.
_Avoid: user, customer, login, username_

**Post:**
A single piece of content published in the app by an `Account`. A `Post` can contain plain text or mixed-media,
including embedded links, video, audio, and polls.
_Avoid: tweet, share_

...

## Entry Relationships

- A `User` as one (or more) `Account`s
- An `Account` can publish many `Post`s
- An `Account` can `Like` the `Post` of another `Account`
- ...

```
