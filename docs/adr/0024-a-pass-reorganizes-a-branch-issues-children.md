---
date: 2026-11-13
status: current
---

# A pass reorganizes a Branch Issue's children, not only adds them

**Context:** [ADR 0009](0009-branch-issues-are-worked-in-passes.md) (Branch Issues are worked in passes) ruled that each pass ends either by adding children or by verifying completion and closing the Branch Issue. The review of the issue guidance's requirements on 2026-10-26 found that a pass which can only add cannot repair a Branch Issue whose children no longer match its scope: one that does not belong under it, or one whose boundary was drawn wrong. The requirements and their design are in the [Issue Tracker skill family proposal](../projects/use-issues/2026-11-13-proposal.md) (R22). Writing the skill for passes on 2026-11-13 showed a second gap (`agent-tooling-n963`): ADR 0009 made a Branch Issue ready work exactly when it has no open children, and `use-bd` taught that as "never claim a Branch Issue that has open children", yet removing and redrawing mean something only for open children. The maintainer ruled on it the same day.

**Decision:** A pass checks the Branch Issue's scope against its children and fixes any mismatch, ending either by reorganizing its children (adding, removing, or redrawing their boundaries) or by verifying it against its criteria. A Branch Issue is still ready work exactly when it has no open children, as ADR 0009 ruled; that says when a pass is due unprompted, and a pass may also be started for cause while children are open.

**Rationale:** A Branch Issue's work is keeping its scope and its children in agreement, and a mismatch is as often a child that should go or be redrawn as one that is missing, so a pass limited to adding leaves the rest of that work with no session to do it. A pass that could start only when no child is open could never remove or redraw one, so the ready rule cannot also be a bar on starting a pass.

## Consequences

- A pass drafts its whole reorganization, not only its new children, before filing any of it, with no placeholder breakdown or acceptance tasks.
- Removing and redrawing change existing Issues, which calls for more delegation than adding does, so a repo may grant the parts of a pass separately and a pass may find some of them asked or denied.
- A verifying pass that finds the criteria unmet ends as a reorganizing pass.
- The pass rules that bdw was planned to enforce (`agent-tooling-aio.4`) were drawn for adding children and for a claim only when no child is open; they are re-read against the wider ending and the wider start, and a claim on a Branch Issue that has open children is not refused.
- `use-bd`'s "never claim a Branch Issue that has open children" is withdrawn. A Branch Issue with open children is still not ready work, so no session picks one up unprompted.

## Alternatives Considered

### Leave ADR 0009 as it stands and read "adding children" loosely

**Description:** Treat removing and redrawing as detail under the existing ruling, with no new ADR.
**Rejection rationale:** "Ends by adding children" is the ruling's own text, the skill and bdw's planned enforcement were built on it literally (a claim released when children are added), and a reader holding ADR 0009 alone would take removing a child in a pass for a violation.

### Reorganize outside passes

**Description:** Keep a pass to adding and verifying, and leave removing or redrawing children to whoever notices the mismatch (a triage pass, or the session working a child).
**Rejection rationale:** Scope is the Branch Issue's own management work, so changing its children without holding it lets two sessions redraw the same tree at once, and a triage pass or a child's worker sees one Issue at a time rather than the Branch Issue's scope as a whole.

### Supersede ADR 0009 with one new ruling

**Description:** Restate the trigger, the pass, and both endings in a single ADR that replaces ADR 0009.
**Rejection rationale:** The ready rule and its rationale are unchanged and still carry ADR 0009's rejected alternatives (passive containers, breakdown and acceptance tasks, a long-lived lead, hidden children); only how a pass ends, and that one may be started for cause, changed, so an amendment keeps the standing part where it was decided.

### Keep the trigger strict

**Description:** A pass starts only when the Branch Issue has no open children, and removing or redrawing happens only when a verifying pass turns into a reorganizing one.
**Rejection rationale:** Removing and redrawing mean something only for open children, and by the time every child is closed there is nothing left to remove or redraw; the strict rule in `use-bd` predates this skill family and gives way to it.
