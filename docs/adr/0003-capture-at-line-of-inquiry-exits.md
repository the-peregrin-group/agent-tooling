---
date: 2026-09-30
status: current
---

# Capture lexicon and ADR work at Line of Inquiry Exits

**Context:** A home-in interrogation raises concepts and decisions continuously, but the lexicon naming procedure takes two turns per term and an ADR can be written only once a decision has landed, so running either inline derails the interrogation into ceremony. The design that holds the analysis is [home-in: design](../skills/home-in/design.md).

**Decision:** Formal lexicon and ADR work runs only at a Line of Inquiry Exit, draining the Resolution Queue; between exits a concept has its identity fixed inline and carries a marked working name that must be resolved at the next exit.

**Rationale:** Inline capture derails the interrogation, wrap-up capture lets unratified names and unchecked decisions compound for a whole session, and the exit is the first moment a subtree's content is stable enough to capture.

## Consequences

- This deviates from `use-lexicon`'s rule never to use an unratified term; home-in states the deviation explicitly rather than leaving agents to infer it.
- A working name that crosses a Line of Inquiry Exit unresolved is a failure the exit report calls out.

## Alternatives Considered

### Inline capture

**Description:** Run the naming procedure and the ADR gate the moment a concept or decision arises.
**Rejection rationale:** Two turns per term turns every insight into a naming discussion and the interrogation loses its thread.

### End-of-session batch

**Description:** Defer all capture to the wrap-up.
**Rejection rationale:** Names and decisions accumulate unchecked for the whole session and the wrap-up becomes a cliff.
