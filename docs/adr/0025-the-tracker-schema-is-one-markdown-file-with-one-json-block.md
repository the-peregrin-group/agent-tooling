---
date: 2026-11-13
status: current
---

# The Tracker Schema is a Markdown file with one JSON block for what tooling reads, each fact in exactly one place

**Context:** Every repo carries its own copy of the Tracker Schema ([ADR 0020](0020-every-repo-carries-its-own-copy-of-the-tracker-schema.md), every repo carries its own copy of the Tracker Schema), but the file's format was left open. The file has two readers with opposite needs: the Wrappers, which run on the system Python 3.9 with the standard library only, and the people and agents who write and judge the Issue State Diagram's natural-language mini-prompts. The file as built is described in the [use-issues design](../projects/use-issues/design.md).

**Decision:** The Tracker Schema is Markdown with one fenced JSON block, each fact living in exactly one place: the JSON block holds the Issue Kinds, the Issue Priorities with their staleness thresholds, the Issue Label Schema, each Issue State's name with its open or closed flag, and the provenance, and the prose holds the state meanings and the transition conditions, keyed by state name.

**Rationale:** The system Python's standard library parses JSON and neither TOML nor YAML, and multi-paragraph mini-prompts are poor to write and review inside JSON strings.

## Consequences

- Folding `TRIAGE.md`'s config block into this file's JSON block is left to `agent-tooling-u9n.8` (make triage-issues tool-agnostic).

## Alternatives Considered

### Pure Markdown prose

**Description:** The whole schema, kinds and priorities and labels included, is written as prose and tables with no machine-read block.
**Rejection rationale:** The Wrappers would parse prose.

### A pure JSON file

**Description:** The whole schema, state meanings and transition conditions included, is one JSON file.
**Rejection rationale:** Multi-paragraph mini-prompts in JSON strings are poor to write and review.
