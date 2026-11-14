---
date: 2026-11-13
status: current
---

# The Tracker Schema is one Markdown file at the repo root, with one JSON block for what tooling reads

**Context:** Every repo carries its own copy of the Tracker Schema, recording the revision of the shipped default it was copied from ([ADR 0020](0020-every-repo-carries-its-own-copy-of-the-tracker-schema.md), every repo carries its own copy of the Tracker Schema), but the file's format, its path in a repo, and what that revision is were left open, the path also being what `agent-tooling-wx5` (one canonical per-repo config home) asked for. The file has two readers with opposite needs: the Wrappers, which run on the system Python 3.9 with the standard library only, and the people and agents who write and judge the Issue State Diagram's natural-language mini-prompts. The file as built is described in the [use-issues design](../projects/use-issues/design.md).

**Decision:** A repo's Tracker Schema is `TRACKER.md` at the repo root, Markdown with one fenced JSON block, each fact living in exactly one place: the JSON block holds the Issue Kinds, the Issue Priorities with their staleness thresholds, the Issue Label Schema, each Issue State's name with its open or closed flag, and the provenance (the source repo, the full commit from the Installer's Receipt, and the default's path at that commit), and the prose holds the state meanings and the transition conditions, keyed by state name.

**Rationale:** The system Python's standard library parses JSON and neither TOML nor YAML, multi-paragraph mini-prompts are poor to write and review inside JSON strings, a file at the repo root is found with no configuration on any platform by the same convention as `LEXICON.md` and `TRIAGE.md`, and a recorded commit and path make "what has the default changed since" a diff of that path between the recorded commit and the current one.

## Consequences

- When the Receipt's commit is `-dirty` or unknown, setup stops and says so rather than recording a revision that cannot be diffed against.
- This settles `agent-tooling-wx5` (one canonical per-repo config home) for the schema; folding `TRIAGE.md`'s config block into this file's JSON block is left to `agent-tooling-u9n.8` (make triage-issues tool-agnostic).

## Alternatives Considered

### Pure Markdown prose

**Description:** The whole schema, kinds and priorities and labels included, is written as prose and tables with no machine-read block.
**Rejection rationale:** The Wrappers would parse prose.

### A pure JSON file

**Description:** The whole schema, state meanings and transition conditions included, is one JSON file.
**Rejection rationale:** Multi-paragraph mini-prompts in JSON strings are poor to write and review.

### A dot-directory, a path under `docs/`, or the tracker's own directory

**Description:** The file lives in a dot-directory, under `docs/`, or in the tracker's own directory such as `.beads/`.
**Rejection rationale:** The ruling records no reason against each of these separately; it chose the repo root because that is the convention `LEXICON.md` and `TRIAGE.md` already follow and it is found with no configuration on any platform.

### A hand-bumped revision number, or a content hash

**Description:** The copy records a revision number someone increments when the default changes, or a hash of the default's content, instead of a commit and path.
**Rejection rationale:** The ruling records no reason against each of these separately; it chose the commit and path because they make "what has the default changed since" a diff of that path between the recorded commit and the current one.
