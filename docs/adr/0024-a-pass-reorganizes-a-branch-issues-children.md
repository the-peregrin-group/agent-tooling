---
date: 2026-10-26
status: current
---

# A pass reorganizes a Branch Issue's children, not only adds them

**Context:** [ADR 0009](0009-branch-issues-are-worked-in-passes.md) (Branch Issues are worked in passes) ruled that each pass ends either by adding children or by verifying completion and closing the Branch Issue. The review of the issue guidance's requirements on 2026-10-26 found that a pass which can only add cannot repair a Branch Issue whose children no longer match its scope: one that does not belong under it, or one whose boundary was drawn wrong. The requirements and their design are in the [Issue Tracker skill family proposal](../projects/use-issues/2026-11-13-proposal.md) (R22).

**Decision:** A pass checks the Branch Issue's scope against its children and fixes any mismatch, ending either by reorganizing its children (adding, removing, or redrawing their boundaries) or by verifying it against its criteria; what triggers a pass, the Branch Issue having no open children, stands as ADR 0009 ruled it.

**Rationale:** A Branch Issue's work is keeping its scope and its children in agreement, and a mismatch is as often a child that should go or be redrawn as one that is missing, so a pass limited to adding leaves the rest of that work with no session to do it.

## Consequences

- A pass drafts its whole reorganization, not only its new children, before filing any of it, with no placeholder breakdown or acceptance tasks.
- Removing and redrawing change existing Issues, which calls for more delegation than adding does, so a repo may grant the parts of a pass separately and a pass may find some of them asked or denied.
- A verifying pass that finds the criteria unmet ends as a reorganizing pass.
- The pass rules that bdw was planned to enforce (`agent-tooling-aio.4`) were drawn for adding children and are re-read against the wider ending.

## Alternatives Considered

### Leave ADR 0009 as it stands and read "adding children" loosely

**Description:** Treat removing and redrawing as detail under the existing ruling, with no new ADR.
**Rejection rationale:** "Ends by adding children" is the ruling's own text, the skill and bdw's planned enforcement were built on it literally (a claim released when children are added), and a reader holding ADR 0009 alone would take removing a child in a pass for a violation.

### Reorganize outside passes

**Description:** Keep a pass to adding and verifying, and leave removing or redrawing children to whoever notices the mismatch (a triage pass, or the session working a child).
**Rejection rationale:** Scope is the Branch Issue's own management work, so changing its children without holding it lets two sessions redraw the same tree at once, and a triage pass or a child's worker sees one Issue at a time rather than the Branch Issue's scope as a whole.

### Supersede ADR 0009 with one new ruling

**Description:** Restate the trigger, the pass, and both endings in a single ADR that replaces ADR 0009.
**Rejection rationale:** The trigger and its rationale are unchanged and still carry ADR 0009's rejected alternatives (passive containers, breakdown and acceptance tasks, a long-lived lead, hidden children); only how a pass ends changed, so an amendment keeps the standing part where it was decided.
