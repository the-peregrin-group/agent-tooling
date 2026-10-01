---
date: 2026-09-30
status: current
---

# Independent review, delivered unfiltered, at home-in wrap-up

**Context:** A one-question-per-turn interrogation produces a chain of locally reasonable ratifications that can sum to a conclusion the user would never have endorsed cold, and neither the user nor the authoring agent can detect it from inside the chain. The design is [home-in: design](../projects/understanding/home-in-design.md).

**Decision:** At wrap-up, home-in offers a review by a separate agent that is given only the artifact and the session's new ADRs and writes a judicial opinion for the user, which the authoring agent relays verbatim with the author's response under its own heading.

**Rationale:** Only a reader blind to the path can judge whether the conclusion stands without it.

## Consequences

- This inverts the repo's `code-reviewer` pattern, in which review feeds the author to reach a merge; here the user is the audience and reaching yes is not the brief.
- The reviewer may reject the premise, the argument, or the conclusion, and may offer a counterproposal for the user to commission.

## Alternatives Considered

### Author self-review

**Description:** The authoring agent pressure-tests the composed conclusion itself.
**Rejection rationale:** It framed and anchored on every step, so it is the wrong entity to attack the whole.

### Ask the user whether they hold the opinion

**Description:** One direct question at wrap-up, answered without the document.
**Rejection rationale:** An acclimatized user cannot detect their own acclimatization, and it adds a mechanism where an existing one fits.

### Reviewer-to-author polish loop

**Description:** The standard review pattern, with feedback filtered through the author.
**Rejection rationale:** It optimizes for a yes, which is the failure being guarded against.
