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
  terms is the one place old names and their dates live.
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

Example invariants for Permissions Grant (defined in the worked example
below):

- Pass: "never outlives the Account that holds it"; "held by exactly one
  Account". Each survives any change of storage or topology.
- Fail: "stored in the grants table" (a schema); "checked by the API gateway"
  (a topology); "expires after 90 days" (a configuration value).

### Examples in entries

- Mark every example "e.g.".
- An example must pass this test: delete it, and the definition still stands.
- Prefer identity-level examples.
- An implementation-level example may appear only on a more general entry, to
  illustrate it, and never in the entry of the instance it names.
- Fixing a stale example is mechanical.

### Named instances

A named instance gets an entry only when it is itself a domain concept. E.g.,
the gitw, ghw, and bdw wrappers are concepts, and individual commands
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
**Permissions Grant**: The authority an Account holds to act on something it
does not own (e.g., another Account's Posts).
...
- _Invariants_: never outlives the Account that holds it; ...
- _Avoid_: permission, role
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
- `X: renamed to Y YYYY-MM-DD`
- `A[, B]: merged into Y YYYY-MM-DD` (one or more merged terms; Y may be new
  or existing)
- `X: split into Y and Z YYYY-MM-DD`

The date is when the change was ratified: a stream document written before
it uses the old term.

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

**Permissions Grant**: The authority an Account holds to act on something it
does not own (e.g., another Account's Posts).
- _Invariants_: never outlives the Account that holds it; held by exactly one
  Account
- _Avoid_: permission, role

## Relationships

- A User has one or more Accounts.
- An Account can publish many Posts.
- An Account can hold many Permissions Grants.

## Retired terms

- Person: split into User and Account 2026-06-02
- Status: renamed to Post 2026-07-14
- Like: removed 2026-08-30
- Profile: merged into Account 2026-09-27
```

## Procedures

`<root>` is the root found in procedure A of SKILL.md.

### B. Name a concept (attended)

The naming questions, which you pose and answer yourself:

1. Why a term: it will be used often, and no clear industry term exists to
   adopt. If an industry term fits, use it; it needs no entry.
2. Core identity: what the concept is, independent of implementation.
3. Candidates: the top 3-5 names, and why your recommendation is best.
4. Collisions: whether any candidate fully or partially overlaps an entry, an
   Avoid list word, or a retired term.

Steps:

1. Raise the need as an overt discussion, one concept per turn. Never use a
   term that is neither ratified nor proposed (procedure C).
2. First turn: present your answers to naming questions 1 and 2. Get the
   user's agreement on the concept's core identity before naming it.
3. Next turn: present your answers to naming questions 3 and 4: the
   candidates, your recommendation, and the collision check.
4. Push back with specific concerns wherever you have them. The user decides.
5. Draft the entry in the format above. When the user ratifies it, write it to
   `LEXICON.md` at once, with any new relationships. If the user says "park
   it", write a proposal (procedure C, steps 1-2) instead.

Example: the user asks for "a moderator role, or permission, or something"
so that some Accounts can moderate other Accounts' Posts.

- First turn: "This needs a term. Moderation work will refer to it
  constantly, and no industry term fits: a role is a bundle of authority
  given to many Accounts, and this is one Account's authority. Core identity:
  the authority an Account holds to act on something it does not own. Agree?"
  The user agrees. Nothing is named yet.
- Next turn: "Candidates: Permissions Grant (recommended: 'grant' says the
  authority is conferred, not inherent), Access Grant, Authority Grant.
  Collisions: none with an entry, an Avoid word, or a retired term. Since you
  said 'role' and 'permission' for it, both go in its Avoid list." The user
  picks Permissions Grant. Draft the entry (as in the worked example); when
  the user ratifies it, write it and its relationship at once.

### C. Propose a term (unattended)

Never edit `LEXICON.md` in an unattended session. Never file a tracker issue
for a proposal.

1. Write one proposal per file at
   `<root>/lexicon-proposals/<slug>--<epoch>.md`, where `<epoch>` is the
   output of `date +%s`.
   - For a new term: answer the naming questions (procedure B) and choose the
     name. `<slug>` is the proposed term in lowercase kebab-case. The file
     holds the draft entry and any new relationships in the format above,
     your answers to the naming questions, and where the name is used in
     code (file paths). Use the proposed name in code.
   - For a change to an existing entry: `<slug>` is the existing term in
     lowercase kebab-case. The file holds the revised entry in the format
     above, the reason for the change, and the evidence (file:line). The
     naming questions and using the name in code do not apply.
2. Commit the proposal file with the code that motivated it, if any.
3. List each proposal file you wrote in your final report, one line each.

Example: the moderation concept from procedure B's example, met instead in an
unattended session that chose a different name. The file is
`lexicon-proposals/access-grant--1790562646.md`:

```md
# Proposal: Access Grant

## Draft entry

**Access Grant**: The authority an Account holds to act on something it does
not own (e.g., another Account's Posts).
- _Invariants_: never outlives the Account that holds it; held by exactly one
  Account

## Relationships

- An Account can hold many Access Grants.

## Naming questions

1. Why a term: the moderation feature refers to it throughout, and no
   industry term fits (a role is a bundle given to many Accounts).
2. Core identity: the authority an Account holds to act on something it does
   not own.
3. Candidates: Access Grant (chosen: short, and names what it confers),
   Permissions Grant, Authority Grant.
4. Collisions: none with an entry, an Avoid word, or a retired term.

## In code

- src/grants/model.py (`AccessGrant`)
- src/moderation/service.py (`AccessGrant`)
```

Commit it with the motivating code; list it in the final report.

### D. Review proposals

1. Group the files in `<root>/lexicon-proposals/` by slug. Present one group
   per turn: its entries and their answers, reasons, and evidence.
2. The user chooses one outcome for the group: discard, ratify as-is, or alter
   then ratify.
3. Discard: nothing else changes. A proposed name left in code earns no entry.
4. Ratify:
   - If the ratified change renames, merges, splits, or retires an existing
     lexicon term, follow procedure E, steps 2-6.
   - Otherwise write the ratified entry and its relationships to
     `LEXICON.md`.
   - If the ratified name differs from the proposed name, rename the proposed
     name in code and state documents; this is mechanical. Add no Retired
     terms line: the proposed name was never a lexicon term.
5. Every outcome deletes the group's proposal files.

Example: the access-grant group holds the file from procedure C's example.
Present it in one turn. The user alters then ratifies it as Permissions
Grant, adding Avoid: permission, role. Write the Permissions Grant entry and
its relationship to `LEXICON.md`. Rename `AccessGrant` to `PermissionsGrant`
in both listed files, and "Access Grant" in any state document: mechanical,
no question asked. Add no Retired terms line, since
Access Grant was never a lexicon term. Delete the proposal file.

### E. Rename or retire a term

1. Agree the change: a rename, merge, or split goes through the naming
   discussion (procedure B); a removal needs the user's ratification.
2. Add the term's line to Retired terms, in its fixed form. Remove the old name
   from every Avoid list.
3. Update the lexicon mechanically. First change the entry itself: rename it;
   for a merge, delete the merged entries and write Y, or update it if it
   already exists; for a split, delete X and write Y and Z; for a removal,
   delete it. Then update every definition, invariant, relationship, and
   example that uses the old name.
4. In the same change, update state documents (README, CLAUDE.md, design
   docs, plans, skills) that use the old name. Never rewrite stream documents
   (ADRs, logs, changelogs, commit messages).
5. List the code identifiers that use the old name, with file:line, and ask the
   user whether to rename them now, file the rename for later, or keep them
   deliberately.
6. If Retired terms now exceeds 20 lines, move its lines to
   `LEXICON-RETIRED.md` (see Retired terms above).

Example: the user finds that a Profile and an Account are one concept.

1. The naming discussion keeps the name Account and agrees its merged
   definition.
2. Retired terms gains `Profile: merged into Account 2026-09-27`; "profile"
   leaves Account's Avoid list.
3. Delete the Profile entry, write the agreed Account definition, and delete
   the relationship "An Account has one Profile".
4. Replace "Profile" in the README and design docs; the ADRs keep it.
5. Ask: "Code still says Profile: `Profile` (src/models/profile.py:8),
   `profile_id` (src/models/post.py:21). Rename now, file the rename for
   later, or keep them deliberately?"

### F. Resolve a code-vs-lexicon conflict

A conflict is code that violates an entry's invariant or relationship, or
uses a term with a different meaning than its entry.

- Never silently fix either side.
- Check only definitive evidence (e.g., the defining type or schema), and
  stop at the first clear answer. Audit the codebase only on request.

Attended:

1. Present the conflict: the entry, and the code with file:line.
2. The user rules which side is right.
3. Ask whether to fix it now or file it for later. A lexicon fix now is a
   change the user ratifies; a rename follows procedure E. Filing a lexicon
   change for later means a proposal (procedure C); filing a code change
   means the project's tracker (search for a duplicate first).

Unattended:

- If the lexicon is likely stale, write a proposal (procedure C).
- If the code is likely wrong, fix it if the fix is within your task's scope.
  Otherwise, if you can write to the project's tracker, file it there (search
  for a duplicate first; if one exists, reference it or add your evidence to
  it); if you cannot, report it in your final deliverable.

Example: Permissions Grant says it is held by exactly one Account, but the
grants table's account_id column is nullable (db/schema.sql:40), so a grant
can exist with no holder. That settles it; read no further. Present the
invariant and the schema line. The user rules the code wrong, then chooses to
file it for later: search the tracker for a duplicate, find none, and file it.
