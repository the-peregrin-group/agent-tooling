---
name: use-lexicon
description: >
  Establishes, extends, or refines rigorous DDD-style domain language within a project. Use this skill proactively any time new
  concepts, features, entities, etc. are being discussed so that they are properly catalogued in the project's language.
---

# Use Lexicon

This skill defines and executes the practice of maintaining consistent domain language within a project.

The key artifact is a `LEXICON.md` file at the project's root which aims to contain _high-level_ definitions for all _concepts_ used in the project. We use the term "lexicon" (from formal linguistics, i.e., "collection of lexemes") to emphasize the conceptual nature of this list.

**Always read `LEXICON.md` in its entirety.**

This skill was designed for use in software projects, but remains very useful in other settings. If working outside of software, please extend the metaphor into the project domain as best you can. Ask the user for guidance if unclear.

## If no `LEXICON.md` exists

Create one by copying in the `./lexicon-template.md` bundled with this skill and renaming it accordingly. Delete the sections of the new copied lexicon doc that are marked `--delete on copy--`.

## How to write `LEXICON.md`

All edits to `LEXICON.md` should follow the guidelines laid out in `./writing-lexicon.md`.

## Make changes immediately

Changes to `LEXICON.md` should always come with the user decisions that motivate them. Do not accumulate changes and batch them into single edits at a later time. By delaying/batching you risk loss or misrepresentation of decisions on context bloat or unexpected session end.

## High-level concepts, not implementation, not history

An entry in the lexicon should change only when we've decided to change its _conceptual identity_, not its implementation. Therefore, lexical entries _should not describe or reference "internal implementation"_, i.e., anything that is not core to the entry's identity.

Example: If defining a "Home Screen" for an application, the focus is on what that screen is conceptually, what its purpose is, what it means to users, etc. It does not matter what it looks like in today's visual design, or that it is styled using Tailwind, or that it loads asynchronously.

Include _only current state and definitions_, never the change history. It is tempting to explain amendments in the lexicon itself, annotate dates and rationales for changes, etc. This is verbose, confusing, and ultimately harmful.

## Apply the terminology yourself

Use the precise, correct terminology in all settings: documents, code, discussions with the user and other agents, commit messages, PRs, etc. Don't make up new terms that have not yet been officially incorporated.

## Hold user accountable

If the user is imprecise in their language or uses the wrong terms to describe known concepts, clarify and ask that they use proper lexical entries.

Similarly, if the user makes claims about a concept's definition and relationships to other concepts (especially in software), explore the project data (e.g., source code) to confirm or deny the user's claims. Remember that you are looking for truth about the _concept_ and _identity_ (e.g., "Users and Accounts are actually one-to-many, not one-to-one!"), not implementation (e.g., "Users are authenticated with OAuth2").

## Vet new concepts

As new concepts arise, consider them against the lexicon and ensure that they are both compatible (they don't conflict) and consistent (they relate intuitively) with the existing entries.

## Don't capture generic concepts

Only add entries for concepts that are specific to the project and not de facto givens in industry. For instance, in a software project, it is unnecessary to establish entries for well-understood software terms like "object-oriented programming," "semaphore," "schema," etc.

## Bootstrapping from `CONTEXT.md`

For projects that declare a `CONTEXT.md` but no `LEXICON.md`, on first encounter, parse `CONTEXT.md` and rewrite as a sibling `LEXICON.md` in [the proper format](#how-to-write-lexiconmd). Ask the user if they want to delete `CONTEXT.md`, or, if the session is unattended, leave it.
