---
date: 2026-11-03
status: current
---

# Issue Verbs share one top-level grammar across wrappers, adopted per wrapper

**Context:** Each wrapper's Verbs are separate executables with their own argument shapes (`ghw-issue-create`, bdw passing bd's syntax through, fjw's issue Verbs not yet built), so a generic skill could not name an operation without naming a platform, and a help form could not be granted the same way everywhere. Unifying every wrapper at once would rewrite every consumer's Permission rules in one move and gate the skill family on a tool rebuild. The 2026-11-03 home-in on the Issue Tracker skill family ([proposal](../projects/use-issues/2026-10-27-proposal.md)) settled it.

**Decision:** The issue Verbs of every wrapper share one top-level grammar in lexicon terms: the same nouns and verbs, with the repo and the Forge identity in the same leading positions, so a moment skill can name a Verb on every platform in one sentence. Beyond that, a Verb's arguments follow its platform, and where a platform lacks a capability its wrapper omits the Verb and says so in help. The grammar is adopted per wrapper as each is built or rebuilt, issue Verbs first; PR and git Verbs follow under their own epics.

**Rationale:** The generic skills and the help edge need one spelling to point at, while a per-wrapper adoption keeps each consumer's rule rewrite inside the epic that rebuilds that wrapper rather than stopping everything at once.

## Consequences

- Wrappers disagree with themselves for a while (`ghw issue create` beside `ghw-pr-create`); that is the planned state until the PR and git epics run.
- A consumer's Permission rules for a wrapper's issue Verbs change when that wrapper is rebuilt, and are regenerated from the repo's spec rather than hand-edited.
- The grammar is bound by the lexicon's terms, so a rename in the lexicon is a rename in every wrapper.

## Alternatives Considered

### Per-Verb executables with per-wrapper shapes, as today

**Description:** Leave each wrapper's Verbs as they are and let the moment skills carry a table of spellings per platform.
**Rejection rationale:** The table is the platform section ADR 0022 rejected, and the help edge would need a different grant on each platform.

### Unify every wrapper at once

**Description:** Rebuild gitw, ghw, fjw, and bdw to the grammar in one epic before the skills ship.
**Rejection rationale:** It couples the skill family, and the progressive-disclosure pilot waiting on it, to the largest tool rebuild in the repo, and rewrites every consumer's rules in one move.

### Identical grammar to the last argument

**Description:** Make every Verb's full argument list the same on every platform.
**Rejection rationale:** Forgejo has no sub-issues and GitHub has no gates; a grammar that pretends otherwise gives agents a spelling that lies, and agents follow spellings to the letter.
