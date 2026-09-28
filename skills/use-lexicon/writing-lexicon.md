# Writing LEXICON.md

`LEXICON.md` is a glossary, not an encyclopedia. Its sole job is to make
everyone (humans, agents, documents, code) use the same terms to mean the same
things: in domain-driven design terms, the ubiquitous language of the bounded
context this repo addresses.

## Content rules

### What belongs

- The canonical term names of this project's domain.
- For each: a conceptual definition that bridges business purpose and applied
  solution.
- Invariants that any valid implementation must uphold.
- Relationships between terms: hierarchy, cardinality, sibling distinctions.
- Retired terms, in their fixed forms.

### What does not belong

- Technical specifications: IP ranges, ports, paths, schemas, model numbers,
  capacities, versions.
- Configuration values.
- Implementation choices that could change without changing the concept.
- Tradeoff rationale (that belongs in an ADR).
- Operational state: deployment dates, current status, who owns what.
- Change history: amendment notes, dates, rationale for changes. Retired
  terms is the one place old names live.
- A flagged-ambiguities section. A resolved ambiguity goes into a definition
  or an Avoid list; an open one becomes a naming discussion (procedure B) or a
  proposal (procedure C).
- A standalone invariants section, or example dialogue.

### Litmus test

> If the concrete implementation changed tomorrow (renumbering, hardware swap,
> vendor change, topology revamp), would this still read true?

Every definition sentence and every invariant must pass. Treat the test as
nearly absolute; a failure means the content belongs downstream.

Example: a "Home Screen" entry says what that screen is, what it is for, and
what it means to users. Today's visual design, its Tailwind styling, and its
asynchronous loading do not belong.

### Examples in entries

- Mark every example "e.g.".
- An example must pass this test: delete it, and the definition still stands.
- Prefer identity-level examples.
- An implementation-level example may appear only on a more general entry, to
  illustrate it, and never in the entry of the instance it names.
- Fixing a stale example is mechanical.

### Named instances

A named instance gets an entry only when it is itself a domain concept. E.g.,
the gitw, ghw, and bdw wrapper families are concepts, and individual commands
like `gitw-commit` are not: a generic Wrapper entry defines what they share,
and thin entries for gitw, ghw, and bdw reference it.

### Code identifiers

Being a code identifier never earns a term an entry. The judgment runs one
way: some entries coincide with code identifiers, by identity or by naming
equivalence, but the entry exists because of the concept.

### Resolving ambiguity

Test: whenever a reader asks "what kind of ___ do you mean?", there must be
exactly one clear answer.

Every term carries an implicit project specifier: in the lexicon for `MyApp`,
every term means "MyApp <Term>".

When a term is ambiguous within the lexicon, improve it or add a narrowing
specifier. E.g., "allowlist" is ambiguous in almost any lexicon; narrow it:

- Port Allowlist
- User Allowlist
- Hostname Allowlist
- Tool Allowlist

Usage may drop the specifier when the narrower meaning is clear (in a
discussion solely about port configuration, "allowlist" means Port
Allowlist), but the entry's term name keeps it.

### Avoid lists

An Avoid list is optional and need not be exhaustive. It steers readers away
from common synonyms and easily confused concepts. Add a word when you observe
it misused; do not guess ahead. A retired name goes in Retired terms only,
never in an Avoid list.

### Authority

The lexicon is authoritative for the concept; downstream documents are
authoritative for the implementation. When two downstream documents disagree
on an implementation detail, that is theirs to reconcile, not the lexicon's.

## Format

### Sections

In this order:

1. `# <Project>`, then one sentence describing the project's context (link
   the README if more is needed).
2. `## Entries`. Group entries under subsection headings, nested as deep as
   the lexicon's size warrants. Soft maximum: 10 entries per section.
3. `## Relationships`: one bullet per relationship.
4. `## Retired terms`: one bullet per retired term.

### Entry format

```md
**Permissions Grant**: The authority an Account holds to act on a resource.
...
- _Invariants_: never outlives the Account that holds it; ...
- _Avoid_: permission, ACL, role
```

- The term in bold, then a colon, then the definition sentences.
- `_Invariants_` is optional: clauses separated by semicolons.
- `_Avoid_` is optional: words separated by commas.
- Put a blank line between entries.
- Refer to another entry by its term name, capitalized as defined (plural:
  "Accounts").
- Every term used in a definition, invariant, or relationship is either
  defined in the lexicon or an everyday word.

### Retired terms

Each line takes one of these fixed forms, and no other:

- `X: removed YYYY-MM-DD`
- `X: renamed to Y`
- `A, B: merged into Y`
- `X: split into Y and Z`

Pruning a line needs ratification. When the section exceeds 20 lines, move
its lines to the end of `LEXICON-RETIRED.md` next to `LEXICON.md`, and leave
in the section a link to that file. The move is mechanical.

### Worked example

```md
# MyApp

A social application where people publish content.

## Entries

**User**: A unique human who uses the application. A single human engaging
with the application multiple times in parallel is still one User.
- _Avoid_: account, customer

**Account**: The in-app identity through which a User acts. Nothing stops a
User from having multiple Accounts.
- _Avoid_: user, customer, login, username

**Post**: A single piece of content published in the application by an
Account. A Post can contain plain text or mixed media (e.g., embedded links,
video, audio, polls).
- _Invariants_: never changes its publishing Account
- _Avoid_: tweet, share

## Relationships

- A User has one or more Accounts.
- An Account can publish many Posts.

## Retired terms

- Profile: merged into Account
```

## Procedures

`<root>` is the root found in procedure A of SKILL.md.

### B. Name a concept (attended)

1. Raise the need as an overt discussion, one concept per turn. Never slip an
   unratified term into conversation, documents, or code.
2. Pose and answer these yourself, then present them:
   1. Why a term: it will be used often, and no clear industry term exists to
      adopt. If an industry term fits, use it; it needs no entry.
   2. Core identity: what the concept is, independent of implementation.
   3. Candidates: the top 3-5 names, and why the chosen one is best.
   4. Collisions: whether any candidate fully or partially overlaps an entry,
      an Avoid list word, or a retired term.
3. Agree on the concept's core identity with the user first; name it only
   after that.
4. Push back with specific concerns wherever you have them. The user decides.
5. Draft the entry in the format above. When the user ratifies it, write it to
   `LEXICON.md` at once, with any new relationships. If the user says "park
   it", write a proposal (procedure C, steps 2-4) instead.

### C. Propose a term (unattended)

Never edit `LEXICON.md` in an unattended session. Never file a tracker issue
for a proposal.

1. Answer the questions of procedure B, step 2, yourself, and choose the name.
2. Write one proposal per file at
   `<root>/lexicon-proposals/<slug>--<epoch>.md`: `<slug>` is the term in
   lowercase kebab-case, `<epoch>` is the output of `date +%s`. It contains:
   - the draft entry, in the format above
   - your answers to the naming questions
   - where the name is used in code (file paths)
3. Use the proposed name in code.
4. Commit the proposal file together with the code that motivated it.

### D. Review proposals

1. Group the files in `<root>/lexicon-proposals/` by slug. Present one group
   per turn: its draft entries and answers.
2. The user chooses one outcome for the group: discard, ratify as-is, or alter
   then ratify.
3. On ratification, write the entry to `LEXICON.md`. If the ratified entry
   renames a term, or its name differs from the proposed name the code uses,
   continue with procedure E, steps 2-6.
4. Every outcome deletes the group's proposal files.

### E. Rename or retire a term

1. Agree the change: a rename, merge, or split goes through the naming
   discussion (procedure B); a removal needs the user's ratification.
2. Add the term's line to Retired terms, in its fixed form. Remove the old name
   from every Avoid list.
3. Update the lexicon mechanically: every definition, invariant, relationship,
   and example that uses the old name.
4. In the same change, update state documents (README, CLAUDE.md, design
   docs, plans, skills) that use the old name. Never rewrite stream documents
   (ADRs, logs, changelogs, commit messages).
5. List the code identifiers that use the old name, with file:line, and ask the
   user whether to rename them now, file the rename for later, or keep them
   deliberately.
6. If Retired terms now exceeds 20 lines, move its lines to
   `LEXICON-RETIRED.md` (see Retired terms above).

### F. Resolve a code-vs-lexicon conflict

A conflict is code that violates an entry's invariant or relationship, or
uses a term with a different meaning than its entry.

- Never silently fix either side.
- Check only definitive evidence (e.g., the defining type or schema), and
  stop at the first clear answer. Audit the codebase only on request.

Attended:

1. Present the conflict: the entry, and the code with file:line.
2. The user rules which side is right.
3. Ask whether to fix it now or file it for later. A fix to the lexicon is a
   change the user ratifies; a rename follows procedure E.

Unattended:

- If the lexicon is likely stale, write a proposal (procedure C).
- If the code is likely wrong, fix it if the fix is within your task's scope.
  Otherwise file it in the project's tracker (search for a duplicate first; if
  one exists, reference it or add your evidence to it), or report it in your
  final deliverable.
