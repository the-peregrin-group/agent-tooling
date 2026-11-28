---
date: 2026-11-25
status: current
---

# The Tracker Schema's JSON block also holds the state order, the Entry State, the Close Reasons, and every colour

**Context:** [ADR 0025](0025-the-tracker-schema-is-one-markdown-file-with-one-json-block.md) (the Tracker Schema is a Markdown file with one JSON block for what tooling reads) lists what the block holds, and the Wrappers, which must now follow each repo's Tracker Schema, need facts it lacked: which Issue State is the Entry State, the order of the states, the Close Reasons, and the label and board colours ghw hard-codes. The block said its state list's order carried no meaning, and the Entry State and Close Reasons were prose only. The file as built is described in the [use-issues design](../projects/use-issues/design.md).

**Decision:** The Schema's JSON block lists the Issue States in Issue State Diagram order. Exactly one open state is flagged as the Entry State. The Close Reasons sit in a list of their own, each with its name and meaning. Every Issue Kind, Issue Priority, Issue Label, and Issue State has a colour. Bringing the tracker in line with the file applies that colour just as it applies a description.

**Rationale:** Each is a fact tooling acts on, so it lives once, in the block, and a colour is declared data like a description rather than a special case for the Wrappers.

## Consequences

- The prose keeps only meanings and conditions keyed by name: it no longer names the Entry State or holds the order, and each Close Reason's condition stays under "Into Closed".
- ghw's colour constants become a copy the label and board Verbs retire when they read the schema.

## Alternatives Considered

### A colour rule in the Wrappers

**Description:** The Wrappers derive colours (one per axis or role, and a fixed palette cycled over states and priorities in order) instead of the schema declaring them.
**Rejection rationale:** It makes colour a special case unlike every other part of the schema; a repo that wants other colours should change its `TRACKER.md`, and a sync should make the tracker match it, as it does for descriptions.

### Colours set on creation only

**Description:** A Wrapper gives a new label or option a default colour and never touches colour again.
**Rejection rationale:** Another special case: a difference between `TRACKER.md` and the live tracker is fixed by a sync for descriptions, and colours should work the same way.

### A new key for unprefixed repo-specific labels

**Description:** A key of its own for labels a repo adds that take no prefix, such as one per site or deployment.
**Rejection rationale:** The block's existing list of labels on no axis already holds them.
