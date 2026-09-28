---
name: use-lexicon
description: >
  Maintain a project's LEXICON.md, the canonical definitions of its domain
  terms, and hold all work to those terms. Load when a concept needs a name;
  when a term is coined, renamed, retired, or disputed; when code and lexicon
  disagree; when lexicon proposals await review; or when a project has no
  LEXICON.md but needs one or has a glossary to convert. Triggers: "what do
  we call...", "add to the lexicon", "is X the same as Y", "rename X",
  "review lexicon proposals", "convert CONTEXT.md". EXCLUDE: generic
  industry vocabulary, API or reference docs, implementation documentation.
---

# Use Lexicon

A project's `LEXICON.md` holds the canonical definitions of its domain terms:
what each concept is, not how it is implemented. Humans, agents, documents,
and code all use those terms to mean those things. "Lexicon" (from
linguistics: a language's inventory of lexemes) stresses that it catalogs
concepts, not implementation.

## Ground rules

- One lexicon per repo: `LEXICON.md` at the root (procedure A defines the
  root). Never create a lexicon in a subdirectory.
- The user ratifies every change to the lexicon except mechanical ones.
  Mechanical changes include fixing a typo, fixing a stale example,
  applying an already-ratified rename or retirement through the lexicon
  (procedure E, steps 2-3, including removing the old name from Avoid lists),
  the mechanical steps of conversion (below), and moving Retired terms lines
  to `LEXICON-RETIRED.md`. Rewording and tightening need ratification. Write
  each ratified change at once; never batch changes for later.
- A session is unattended only if its prompt says "unattended"; otherwise it
  is attended. Never edit the lexicon in an unattended session: write a
  proposal instead (procedure C).
- Use lexicon terms exactly, everywhere: conversation, documents, code,
  commit messages, PRs. Coin a term only through procedure B or C.
- Before running any of procedures B-F, read `writing-lexicon.md` (bundled
  with this skill). It holds the content rules, the format, and those
  procedures.

Outside software, map the terms of this skill onto the project:

- code: the project's artifacts
- implementation: how a concept is currently realized
- code identifiers: names used in those artifacts
- commits and PRs: the project's change records
- git top-level: the root rule in procedure A, step 1

## A. Find the lexicon

1. Find the root: the git top-level (`git rev-parse --show-toplevel`). Outside
   a git repo, the nearest ancestor of the working directory that contains a
   `.claude/` directory, not counting the user-level `~/.claude`. Failing
   both, the working directory.
2. If `<root>/LEXICON.md` exists, read it in full, unless its full content is
   already in your context. Go to step 5.
3. If there is no `LEXICON.md`, but the project's CLAUDE.md or README names a
   glossary file as the project's vocabulary:
   - Attended: offer conversion (below), once per session. If the user
     declines, use that file as the lexicon for this session: for the rest of
     the session, `LEXICON.md` in every procedure means that file. Write new
     or changed entries in the lexicon format (this skill's), not the file's
     old format.
   - Unattended: use that file as the lexicon. Make no offer.

   Go to step 5.
4. If there is neither: attended, create `<root>/LEXICON.md` from
   `lexicon-template.md` (bundled with this skill) without asking permission
   to create it. Fill in the project name and its one-sentence description,
   and present the sentence to the user for ratification. Remove the
   placeholder entry, or replace it with the first ratified entry.
   Unattended, create nothing; proposals still go to
   `<root>/lexicon-proposals/`.
5. Attended: if `<root>/lexicon-proposals/` contains files, say so once this
   session and offer to review them (procedure D).

Whenever you look up a term that is not among the entries, check Retired
terms, then `LEXICON-RETIRED.md` if Retired terms links to it. A retired
term's line names what replaced it; use that.

**Conversion** is one change, made in this order:

1. Rewrite the old file's content into `LEXICON.md` in the format of
   `writing-lexicon.md`. Reformatting is mechanical; definition text carries
   over verbatim. A standalone invariants section moves onto its entries.
   Terms named in a resolved-ambiguity note may move into the relevant Avoid
   list. Drop example dialogue. Any change to definition text, including
   folding an ambiguity's resolution into a definition, needs ratification,
   one entry per turn, after the conversion lands. An open ambiguity becomes a
   naming discussion (procedure B) after the conversion.
2. Delete the old file.
3. Update every reference to the old file in state documents (CLAUDE.md,
   README, docs, skills) to point to `LEXICON.md`. Never rewrite stream
   documents (ADRs, logs, changelogs, commit messages).

## G. Correct drift in language

This applies to the user's language and to yours.

1. A known concept under the wrong name: use the correct term once, inline, in
   your reply. Do not ask the user to rephrase.
2. The same wrong name again after that correction: ask once whether the
   lexicon's name should change. If the user says yes, follow procedure E.
3. A concept the lexicon lacks: apply the naming tests (it will be used often;
   no clear industry term exists to adopt). Suggest a naming discussion
   (procedure B) only if it passes both.
4. Never correct everyday words used in their everyday sense.
5. When the user asserts a concept's definition or relationships, check the
   definitive evidence before accepting the claim (the scope set in procedure
   F: stop at the first clear answer). If the evidence contradicts the claim,
   say so, with file:line.

Unattended: skip step 2; in step 3, write a proposal (procedure C) instead of
suggesting a discussion.

## B-F. In `writing-lexicon.md`

- **B. Name a concept (attended):** a concept needs a name, or the user asks
  to add one to the lexicon.
- **C. Propose a term (unattended):** a concept needs a name or an entry needs
  changing in an unattended session, or the user says "park it".
- **D. Review proposals:** the user accepts the review offer or asks to
  review lexicon proposals.
- **E. Rename or retire a term:** a term needs a new name, or must be removed,
  merged, or split.
- **F. Resolve a code-vs-lexicon conflict:** code violates an entry's
  invariant or relationship, or uses a term with a different meaning.
