---
date: 2026-10-09
status: current
---

# bdw carries Beads policy, in the lightest tier that suffices

**Context:** `bdw` was built as an identity wrapper that otherwise execs `bd` with arguments untouched ([ADR 0002](0002-beads-identity.md), Beads identity). The use-bd design needs policy that Permission rules cannot express (which kinds may take children, what counts as ready work, releasing a Branch Issue's claim), and encoding it means `bdw` handling bd's arguments, where re-implementing bd's command grammar would tie `bdw` to bd's CLI. The analysis is in the [use-bd design](../projects/use-bd/design.md).

**Decision:** `bdw` carries the Beads policy that Permission rules cannot express, handling each operation in the lightest of three tiers that suffices: pass-through, a thin intercept that fails closed on any command line it cannot read unambiguously, or a Verb of its own whose superseded raw `bd` commands are denied.

**Rationale:** Policy then lives in code that agents cannot talk past, while `bdw` never re-implements more of bd's command grammar than the flag or two an intercept reads.

## Consequences

- Agents learn `bdw`'s own Verb names for the operations raised to a Verb, and lose bd's names for those.
- A bd upgrade re-verifies every intercept and Verb along with the known quirks.

## Alternatives Considered

### Pure pass-through

**Description:** Keep `bdw` to identity and leave all policy to the Skill's text and the Permission rules.
**Rejection rationale:** Prefix rules cannot express kind checks, readiness, or claim release, and text alone loses to agents' habits.

### Every operation a `bdw` Verb, as gitw does

**Description:** Replace bd's whole surface with curated Verbs and deny raw `bd` entirely.
**Rejection rationale:** It duplicates large parts of bd for operations that carry no policy, which is the spinoff this ecosystem is not building.

### Intercept bd's command lines wherever policy is needed

**Description:** Keep bd's interface everywhere and parse its arguments to apply each rule.
**Rejection rationale:** It needs bd's full argument grammar, so an upgrade could silently change what `bdw` lets through.
