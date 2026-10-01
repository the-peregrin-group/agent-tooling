---
date: 2026-09-30
status: current
---

# ADRs duplicate their motivating document on purpose

**Context:** The ADR writing guide said nothing about how an ADR relates to the state doc that motivated it, and agents inferred a deduplication rule ("cite the design doc instead of repeating it"), which turns the ADR into a pointer to a document that may change rather than a record of its own. The decision was made for the guide as a whole, not for one skill; the design that surfaced it and holds the analysis is [home-in: design](../skills/home-in/design.md), in the section on ADRs and the artifact.

**Decision:** An ADR carries its own context, rationale, and alternatives even when a design doc holds the full analysis; the ADR links that doc, the doc summarizes and links the ADR, and there is no deduplication rule.

**Rationale:** The design doc is state and may be rewritten, and the ADR is the snapshot that must survive that.

## Consequences

- Alternatives Considered is never omitted, since the gate guarantees alternatives existed.
- Context, Decision, and Rationale limits are fixed in every case; Alternatives Considered is the one section that flexes, one sentence per field when a design doc holds the analysis and unbounded rejection rationale, cut to what prevents relitigation, when the ADR stands alone.
- Citations of ADRs give an inline summary plus a link, never a bare `ADR-XXXX`.

## Alternatives Considered

### Deduplicate toward the design doc

**Description:** The ADR cites the design doc for its context and rationale instead of stating them.
**Rejection rationale:** A rewritten design doc leaves the ADR meaningless.

### Link a pinned revision of the design doc

**Description:** Cite the design doc at the commit current when the decision was made, so the rewrite problem disappears.
**Rejection rationale:** The reader must leave the ADR and find one sentence inside a stale revision of a long document, when an ADR's job is to be read in a minute.

### Two ADR length tiers

**Description:** A very terse form when a design doc exists and a longer form when the ADR stands alone.
**Rejection rationale:** The terse tier cannot be shorter than the snapshot minimum, and a longer tier is a mode agents select for themselves.
