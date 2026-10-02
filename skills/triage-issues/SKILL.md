---
name: triage-issues
description: Repeatable, mostly-autonomous triage + backlog grooming over a repo's GitHub Issues and Project board — screens/labels/syncs issues, moves them through an 8-state "what attention does this need next?" model, and surfaces PM-axis hygiene (priority, staleness, duplicates, split/group) into a durable ledger issue. Use for "run triage", "triage pass", "groom the backlog", "triage issue #N", or a recurring autonomous pass. Requires a project-root TRIAGE.md profile. Not for TODO lists kept in files; those need a separate backlog-grooming pass.
---

# Triage Issues — Skill

> Universal triage skill. Policy lives here; each project binds it via a `TRIAGE.md` profile at its repo root. GitHub I/O runs through the wrappers in `reference/` (see `reference/README.md`); recurring/unattended operation is covered in `reference/DEPLOYMENT.md`. For interactive, single-issue GitHub work (filing, labeling, commenting, PRs), the `use-github` skill is the canonical GitHub-I/O layer — this skill's `triage-*` wrappers exist solely as the autonomous write path for triage passes.

## Purpose

Repeatable, mostly-autonomous triage process for a repo's GitHub Issues + Project board. Two axes:

1. **Execution axis** — keep issues moving through a defined state machine.
2. **PM axis** — surface priority/size/staleness hygiene needs without auto-acting.

The split between fully-autonomous work (screening) and agent+human collaboration (scoping/design) is explicit per state.

## When to use

- "Run triage" / "groom the backlog" / "triage pass" / "triage issue #N"
- Proactively as a recurring autonomous pass over `Needs Triage` items

## Boundary with file-based TODOs

This skill operates on GitHub Issues + Projects only. TODO lists kept in files (a `TODO.md`, TODO sections in docs) are out of scope; a separate backlog-grooming pass, if you have one, handles them. Complementary, not overlapping.

## Profile binding

The skill expects a `TRIAGE.md` at project root binding it to project-specific values. The opaque IDs + schema + tuning live in a fenced, marker-delimited JSON config block (`<!-- BEGIN triage-config -->` … `<!-- END triage-config -->`) — that block is the machine-readable source of truth the wrappers parse (see `reference/README.md`); surrounding prose is for humans only. Required fields:

- Project identification (repo, project number, node ID)
- Status field ID + canonical-state → option ID mapping
- Priority field ID + level → option ID mapping
- Size field ID + size → option ID mapping (or "not used"). `Size` is canonical going forward — `ghw-board-sync` (the `use-github` skill's board wrapper, run by `setup-github-issues` at bootstrap) provisions it on every new board — and "not used" exists to grandfather boards that predate it (a missing `Size` on an existing board is reported, never auto-created)
- Last Triaged field ID
- Triage ledger issue number — the durable report issue the skill owns and rewrites every pass (see `## Cadence & autonomous operation`). Always required.
- Label schema (type labels + area labels; optionally scope labels, which R-LABEL-1 exempts from its checks)
- Staleness multiplier (optional; default 1)

Optional overrides:
- Bot account whitelist (additions to skill's bot exclusion list)
- Per-priority staleness threshold overrides
- Priority-distribution thresholds (P0 cap, collapse %, min-N guard — see P-DIST-1/2; defaults 3 / 80% / 10)
- Marker phrasing overrides (e.g., parent-tracker scope-locked marker)
- Cadence config — schedule + run-mode defaults for unattended operation. Consumed by the *deployment* layer (see `reference/DEPLOYMENT.md`), not the skill's own logic; the skill behaves identically however it was invoked. The ledger issue (required, above) exists independently of whether cadence is configured.

## The state model

The skill is **opinionated** about the model. Status answers: **"what kind of expert attention does this issue need next?"**

| Canonical state | Semantic | Triage autonomy |
|---|---|---|
| `Needs Triage` | Screening / bookkeeping | Fully agent-autonomous |
| `Needs Scope` | Business-level scoping (define the goal) | Agent + human-in-loop |
| `Needs Eng Design` | Engineering-level scoping (design decisions) | Agent + human-in-loop |
| `Needs Impl` | Decisions made; ready for any implementer | (PM-axis only) |
| `In progress` | Claimed; being executed | (PM-axis only) |
| `In review` | Reviewer attention | (PM-axis only) |
| `Done` | Resolved | Terminal |
| `Rejected` | Decided not to do | Terminal |

> **Future customizability (deferred):** v1 requires all 8 states. Future versions may allow simpler/informal projects to *omit* some intermediate states (e.g., merge `Needs Scope` and `Needs Eng Design`). Full state-graph customization is out of scope.

## Allowed transitions

**Forward (default exits per state):**
- `Needs Triage` → `Needs Scope` | `Done` | `Rejected`
- `Needs Scope` → `Needs Eng Design` | `Needs Impl` (if narrow/clear) | `Rejected`
- `Needs Eng Design` → `Needs Impl` | `Rejected`
- `Needs Impl` → `In progress` | `Rejected`
- `In progress` → `In review` | `Needs Impl` (released back to queue) | `Rejected`
- `In review` → `Done` | `In progress` (revisions) | `Rejected`

**Backward (regression):** allowed at any time. Triage *proposes*; human approves.
- → `Needs Scope` if new info invalidates the goal
- → `Needs Eng Design` if new info requires re-design

## Cross-cutting rules

### Sync (autonomous)

- **R-SYNC-1:** Open Issue + Status `Done`/`Rejected` → must move. Default: demote to `Needs Scope`; surface for human if ambiguous.
- **R-SYNC-2:** Closed Issue + Status not `Done`/`Rejected` → must set to `Done` (or `Rejected` if the close reason supports it).

### Label compliance (autonomous, perpetual)

- **R-LABEL-1:** Every issue must have **exactly one** label from the profile's *type* family and **one or more** `area:*` area labels. Labels outside the profile's declared families (e.g. unprefixed scope labels) are neither required nor flagged. Validated on every triage pass, not just at `Needs Triage`. Profile supplies the actual labels.

### Split / group (with-human; agent proposes, human confirms)

- **R-SPLIT-1:** If an issue body contains a checklist of N items, evaluate each item against the split criteria below. The rule applies *per item*: a bundle can be partially split (some items peeled off as peer/sub-issues, others remaining in the bundle).

  **Veto checks (pre-filter; apply to the bundle as a whole):**
  - **V-THEME:** No unifying theme — items are a grab-bag of unrelated work → split into peers.
  - **V-ATOMIC:** Items cannot be cleanly decomposed into discrete atomic changes → do **not** split; find a better decomposition or accept the bundle. Dependence between atoms is fine; intertwining that prevents atomic decomposition is not.

  **Strong trigger (auto-promote item to its own issue):**
  - **T-DOC:** The item, if executed in isolation, would warrant its own design doc per the consequence rubric in E-WORK-2 (2+ consequence signals fire). Sub-issue if a component of the parent's initiative; peer issue if orthogonal.

  **Meatiness heuristic (when no veto fires and no strong trigger; per-item):**
  - **M-SCOPE:** Sufficient scope — the item, as its own issue, would be sized M+. XS items rarely worth splitting; S is borderline.
  - **M-CTX:** Context-switch cost — implementing the item requires loading a different mental model from its siblings (different subsystem, layer, or abstraction). High cost favors splitting; low cost (same mechanical pattern across files, e.g.) makes splitting discretionary.

  Decision: both meatiness signals favor splitting → propose split. Mixed → judgment call; default to batched.

- **R-SPLIT-2:** Split has two flavors, applied per-item (a single bundle may use both):
  - **Peer split:** item becomes a separate sibling issue; original may close (or stay open with remaining items, in a partial split).
  - **Parent-child decomposition:** original becomes parent; children link via GitHub sub-issues API. Both sized independently. Use when the work is cohesive but multi-step.

  Flavor choice: T-DOC and the meatiness heuristic produce sub-issues for items that are components of the parent's initiative, peer issues for orthogonal items. V-THEME (grab-bag bundle) splits into peers by definition.

- **R-GROUP-1:** The inverse of R-SPLIT-1. Where splitting examines *one issue's* checklist, grouping scans *across* open issues for clusters that should become a single unit of work. Detection is therefore a backlog-level pass (see Triage pass workflow), not a per-issue check. Two flavors, mirroring R-SPLIT-2's two split flavors.

  **Detection (cheap pre-filter):** 2+ open issues sharing a type label and an overlapping `area:*`. Shared labels are *necessary, not sufficient* — a coincidental label match is not a group. Membership is established by the gates below, not by labels.

  **Flavor 1 — Parent grouping (reparent under a tracker).** Inverse of parent-child decomposition (one issue → N children becomes N issues → one parent). Recognize that several separate issues are components of one overarching goal, and reparent them under a tracking issue (creating it if absent, per R-PARENT-*).
  - **G-WHOLE (gate):** the goal is *incomplete until all members are done*. Operational test: "does landing any single member alone deliver standalone value?" If **no** (each member is inert without the others) → group. If **yes** for all (each ships value independently) → do **not** group; they are independent issues. Link via blocked-by if dependent — dependency is *never itself* a grouping signal (R-BLOCK-4).
  - **GV-HORIZ (veto):** the cluster is a *horizontal* slice (one shared concern spanning many features) where a *vertical* slice (one feature end-to-end) was possible. Prefer vertical. Exception: the horizontal IS the entire deliverable (e.g., "add test coverage across the codebase" — testing is the whole project, not stage M of an N-stage feature).
  - **GV-MILESTONE (veto):** the tie among members is merely thematic, or is a release / schedule / deliverable grouping. Grouping is for *semantic relatedness* only. Use GitHub Milestones for releases and schedules — never a parent tracker.
  - Members keep independent status (R-PARENT-1) and independent size (R-PARENT-4). Members may be any size; meaty children are expected and normal here.

  **Flavor 2 — Merge into one issue (collapse).** Inverse of peer split (one issue → N peers becomes N peers → one issue). Fold several issues into one, closing the others. **Expected to be rare** — 99% of the time the right move is to not over-decompose into a swarm of XS issues in the first place. Only when over-decomposition has already happened:
  - **Gate (both required):**
    - **GM-RELATED:** members are *the same task applied across an axis* (e.g., the same two-line boilerplate change on 10 test files) OR all serve the same single goal/outcome.
    - **GM-SIZE:** the members' *aggregate* size is ≤ M.
  - **R-SCREEN-7 hand-off:** if the members collapse to literally *one* change (not N distinct changes), they are duplicates, not a merge — route to duplicate handling instead.
  - **Action:** fold into the clearest primary issue (or a fresh one); close the absorbed issues as *not planned* with a mandatory `Absorbed into #X` comment and back-link. The close-reason enum has no "merged" option — "not planned" is lossy, but the back-link preserves traceability. Leaving the absorbed issues open is *not* an option; it re-creates the noise the merge exists to remove.

  **Type discriminator (size decides):** meaty members that are individually moot → Flavor 1 (parent). Small members, aggregate ≤ M, over-decomposed → Flavor 2 (merge). Meaty members that each ship value independently → neither; leave separate (link if dependent).

- **R-GROUP-2:** Grouping never auto-acts. The agent surfaces proposals in the "Grouping candidates" report group; reparenting, tracker creation, and especially issue-closing await human confirmation.

### Parent-tracker issues

- **R-PARENT-1:** Parent trackers have an *independent* status from their children. Derived state breaks down on mixed-state child sets.
- **R-PARENT-2:** Parent lifecycle (status answers "what does the parent itself need next?"):
  - `Needs Triage` — same as regular
  - `Needs Scope` — initiative not yet business-scoped
  - `Needs Eng Design` — foundational eng-scoping (global criteria, decomposition strategy) pending. *Per-child* eng-scoping happens at child level and does NOT keep parent here.
  - `Needs Impl` — generally N/A for parents
  - `In progress` — foundational eng-scoping done AND any child has non-zero progress
  - `In review` — optional final walkthrough
  - `Done` — all children Done or Rejected
- **R-PARENT-3:** Children must be linked via the GitHub sub-issues API. A body checklist can co-exist for narrative; formal linkage is the source of truth.
- **R-PARENT-4:** Parents are sized independently of children (parent reflects total initiative scope; children reflect per-step scope).
- **R-PARENT-5:** Scope-completeness is encoded by body convention, not status. Default convention: a `- [ ] All children created (scope locked)` checklist item in the parent body. Profile may override the phrasing.

### Blocker handling

- **R-BLOCK-1:** A "blocker" is an external dependency (another issue, an engine update, a third-party release, team capacity in another domain) that prevents an issue from progressing beyond a specific lifecycle stage.
- **R-BLOCK-2:** Determine the lifecycle stage at which the blocker actually bites. If the issue is currently *earlier* than that stage, its status reflects its true current lifecycle and progress continues freely — the blocker does not yet matter.
- **R-BLOCK-3:** If the issue has reached the blocking stage, add a `**Blocked on:** <description>` marker near the top of the body. Status stays at that stage until the blocker clears.
- **R-BLOCK-4:** If the blocker is itself a GitHub issue, ALWAYS use GitHub's blocked-by / blocking relationships *in addition to* the body marker.
- **R-BLOCK-5:** Blocked issues are surfaced in a dedicated "Blocked" group in the triage report (see Output section) so they don't dilute "needs attention" signals. Each pass reviews the group to check if any blockers have resolved.

### ADR cue (with-human; agent proposes, human confirms)

- **R-ADR-1:** Whenever a state captures a decision (scope, UX, eng design, direction), the agent evaluates the decision against this rubric (offer ADRs sparingly). All three must hold:
  1. **Hard to reverse** — meaningful cost to change later
  2. **Surprising without context** — a future reader will wonder "why this way?"
  3. **Result of a real trade-off** — genuine alternatives existed; one was picked for specific reasons

  If all three → surface as an ADR-creation suggestion in the triage report ("ADR-creation candidates" group). If any miss → no ADR cue.

- **R-ADR-2:** Never autonomous. The agent proposes; the human decides whether to create the ADR and drafts it (or asks the agent to) in the repo's ADR format.

## Per-state playbooks

> **Bidirectional entry verification:** every state's playbook begins with an entry-verification block that checks whether the issue's *actual readiness* matches its current state. Two directions:
> - *Downward* — if the issue is less prepared than its current state implies, propose **regression** to the appropriate earlier state.
> - *Upward* — if the issue already meets this state's exit criteria, propose **promotion** to the next state (or further, if multiple states' exit criteria are satisfied).
>
> All entry-verification moves are *proposals*, not autonomous mutations. R-SYNC-1/2 remain the autonomous exceptions (terminal-status mismatches).

### `Needs Triage` — screening (autonomous)

**Entry verification:**

- **T-ENTRY-1:** (Downward) N/A — `Needs Triage` is the entry-point state; there is no earlier state to regress to. Open/closed mismatches are handled autonomously by R-SYNC-1/2.
- **T-ENTRY-2:** (Upward) If R-SCREEN-1..7 already pass AND the body already contains a clear business goal + acceptance criteria (plus UX scope if applicable per S-WORK-2 trigger), propose **promotion** directly to `Needs Eng Design`. If screening passes but scoping content is missing, propose promotion to `Needs Scope`.

**Screening checks:**

- **R-SCREEN-1:** Verify label compliance (R-LABEL-1). Fix if obvious; flag if ambiguous.
- **R-SCREEN-2:** Verify body has minimum substance: problem/goal + at least one pointer (code location, repro, observable behavior). Flag if failing; do not auto-edit.
- **R-SCREEN-3:** Verify title is at least minimally descriptive. Flag only actively-useless titles ("Bug", "TODO", "fix this"). Tolerant otherwise.
- **R-SCREEN-4:** Verify Priority is set. Flag if missing. Priority assigned at this stage is by definition an *educated guess* — it drives the scheduling of scoping work, not the final priority of the issue. Real refinement happens at `Needs Scope` exit (S-WORK-6).
- **R-SCREEN-5:** Sizing is *skipped* in screening. Assigned no later than exit from `Needs Eng Design`.
- **R-SCREEN-6:** Verify Project Status ↔ Issue state agree (delegates to R-SYNC-*).
- **R-SCREEN-7:** Cursory duplicate detection — fuzzy title/body match against other open issues. Flag candidates; do not auto-merge.
- **R-SCREEN-8:** Cursory stale-irrelevant detection — for issues > N days, search for merged PRs that may have addressed them without proper linkage. Flag candidates; do NOT read code to verify; do NOT auto-close.
- **R-SCREEN-9:** Trivial body corrections (typos, grammar, broken/incorrect links) may be *proposed* but are **not autonomous.** Applying them needs a general free-text write to an arbitrary issue — the one capability that would puncture the fail-closed wrapper boundary (R-CAD-5), so v1 exposes no autonomous body-write wrapper. Surface such fixes for a human, or apply them in an interactive pass (where body writes are human-approved in-session). Forbidden at any autonomy level in this state: changing the issue's actual *definition* (belongs to `Needs Scope`).

**Exit transitions:**
- → `Needs Scope` (default if screening passes)
- → `Done` (rare; if stale-irrelevant check confirms already-resolved — needs human OK)
- → `Rejected` (if incoherent, out of scope, garbage — needs human OK)

### `Needs Scope` — business and UX scoping (agent + human)

**Entry verification (autonomous, runs first):**

- **S-ENTRY-1:** (Downward) Issue has passed `Needs Triage` screening (R-SCREEN-1..7 substance). If failing → propose **regression to `Needs Triage`**.
- **S-ENTRY-2:** (Upward) If body already contains a clear business goal + acceptance criteria (plus UX scope if applicable), propose **promotion to `Needs Eng Design`** — the issue is scope-complete and was misclassified into `Needs Scope`.

If S-ENTRY-1 fails, surface as a misclassification in the triage report; do not proceed with scope work on top of a partially-screened issue.

**Scope work (agent + human-in-loop; interactive by default):**

- **S-WORK-1:** Identify open scoping questions. Default checklist:
  - Underlying problem / motivation (not the proposed solution)
  - Beneficiary and benefit (end user? operator? future maintainer?)
  - Concrete acceptance criteria / definition of done
  - What's explicitly out of scope
  - Constraints (technical, design, narrative) that bound the solution space
  - Adjacencies: depends on / conflicts with / supersedes other backlog items

- **S-WORK-2:** **UX scoping** (when applicable).
  - **Trigger:** does the issue affect anything *user-observable*? For a desktop or mobile app, that might mean screens, panels, overlays, controls/gestures, pacing/feel; for a web app, pages, components, flows, perceived latency. The profile may extend the trigger with project-specific surface types.
  - **Depth bar:** rough characteristics + wireframe-level layout. *Not* final pixels.
  - **Surface questions:**
    - Desired experience characteristics (immediate vs. deliberative, dense vs. sparse, exploratory vs. directed)
    - Wireframe-level layout (top bar? side panel? overlay? modal?)
    - Key affordances (click / hover / drag / implicit)
    - Information density and hierarchy (primary vs. secondary vs. on-demand)
    - Reference patterns (existing in-project; external)

- **S-WORK-3:** Decomposition check — is this one cohesive scope question or several? Several → split candidate (R-SPLIT-1). If it's a parent initiative → R-PARENT-*.

  **Checklist-item exit-criteria precondition (for R-SPLIT-1):** before evaluating bundled-checklist items against R-SPLIT-1, each item must have *tight* exit criteria. Phrasing like "fix any breakage", "update X if needed", "smoke test", "verify Y works" hides arbitrary scope and prevents the meatiness heuristic from being evaluated. Tighten such items in place (definition *is* this state's work, per S-WORK-8); do not treat fuzzy items as automatically meaty for splitting purposes.

- **S-WORK-4:** Rejection check — does this still align with project direction? Already addressed elsewhere? Cost wildly disproportionate to value? Any yes → surface as rejection candidate. (Rejection rubric is concentrated at this state; downstream states accept `Rejected` as an exit but rely on issues *screaming* for rejection rather than a careful pass.)

- **S-WORK-5:** Blockers (R-BLOCK-*). A scope-stage blocker prevents the goal from being defined (e.g., stakeholder unavailable; depends on resolving #X first).

- **S-WORK-6:** Re-confirm Priority. Scoping is the moment of precision — `Needs Triage` only assigns an educated guess. If priority needs to change, flag for re-prioritization.

- **S-WORK-7:** ADR cue (R-ADR-*). If scope or UX work produces a decision that meets all three criteria (hard to reverse, surprising without context, real trade-off), surface as an ADR-creation suggestion.

- **S-WORK-8:** Body updates ARE allowed at this stage (explicit contrast to R-SCREEN-9; definition *is* the work here). After scoping, body should contain:
  - **Problem / motivation** (required)
  - **Goal** (required)
  - **Acceptance criteria** (required)
  - **User experience** (required if UX-bearing; rough characteristics + wireframe-level layout)
  - **Out of scope** (optional)
  - **Links** (optional)

  Profile may extend (but not replace) this minimal template.

**Mode:** scope work is **interactive** by default. The agent surfaces questions in the triage report as "Open scoping questions for #N"; the human engages in a follow-up session to resolve. For complex scope or UX decisions, the agent may suggest a dedicated design-interview session — but does not demand it.

**Exit criteria (all required):**
- Body contains clear business goal
- Body contains acceptance criteria
- Body contains UX scope, if UX-bearing
- Priority confirmed (possibly updated)
- Decomposition resolved (single issue, or split decided)
- No active scope-stage blockers
- → `Needs Eng Design` (default)

**Direct exit to `Needs Impl` (rare, suggestion-only):**
- Implementation appears mechanical (e.g., rename, dependency bump, doc fix, mechanical refactor) AND no engineering decisions are visible from the scoped goal.
- Agent confidence bar: high. When uncertain, default to `Needs Eng Design`.
- Surfaced as a "skip-eng-design candidate" in the report; the human confirms.

**Other allowed exits:**
- → `Needs Triage` (regression if S-ENTRY-1 fails)
- → `Rejected` (per S-WORK-4)

### `Needs Eng Design` — engineering scoping (agent + human)

**Entry verification (autonomous, runs first):**

- **E-ENTRY-1:** (Downward) Body contains a clear business goal (e.g., "user can...", "tests cover...", "engineers can..."). If missing → propose regression to `Needs Scope`.
- **E-ENTRY-2:** (Downward) Body contains acceptance / completion criteria. If missing → propose regression to `Needs Scope`.
- **E-ENTRY-3:** (Downward) If UX-bearing (per S-WORK-2 trigger), body contains UX scope (rough characteristics + wireframe-level layout). If missing → propose regression to `Needs Scope`.
- **E-ENTRY-4:** (Upward) If all of this state's exit criteria already appear satisfied (decisions captured, size set, no active blockers), propose **promotion to `Needs Impl`** — the issue is design-complete and was misclassified into `Needs Eng Design`.

If any downward entry check fails, surface for human as a misclassification in the triage report; do not proceed with eng-design work on top of a fuzzy goal.

**Eng-design work (agent + human-in-loop):**

- **E-WORK-1:** Identify open engineering decisions and surface them. The agent enumerates from the body + codebase context; the human catches what the agent misses. (Autonomous judgment criteria will be refined as we iterate; for v1, the human-in-loop is the safety net.)
- **E-WORK-2:** For each decision, run the **size-of-consequence rubric**. The rubric determines where the decision is *explored*:
  - **0 signals:** record decision in a `## Design decisions` section of the issue body. Discussion lives in comments; the decision itself is body content.
  - **1 signal:** judgment call — agent surfaces the signal, human decides body-vs-doc.
  - **2+ signals:** propose a design doc that stress-tests the trade-offs before deciding.

  **Consequence signals:**
  - Hard to reverse if wrong (one-way door)
  - Crosses >1 subsystem or service
  - Affects security, data integrity, or external contracts
  - Decision rests on assumptions that affect things outside the immediate change
  - Specialist domain knowledge required (crypto, ML, distributed systems, kernel, etc.)

  (Note: "future maintainers would benefit from written rationale" is *not* a consequence signal — that's an ADR concern, handled separately from design-doc triggering.)

- **E-WORK-3:** If decisions reveal significant complexity → consider decomposition (parent-child split per R-SPLIT-2).
- **E-WORK-4:** Identify blockers (R-BLOCK-*). If a blocker bites at this stage, add the body marker and surface in the Blocked report group.
- **E-WORK-5:** Set Size before exit. This is the latest state where Size must be assigned.

**Exit criteria (all required):**
- All identified design decisions made AND captured (issue body or linked design doc)
- Size set
- No active blockers at the eng-design stage
- An implementer (human or agent) could pick this up and execute without further design input
- → `Needs Impl`

**Other allowed exits:**
- → `Needs Scope` (regression — entry checks failed, or new info invalidates the goal)
- → `Rejected` (if eng-design reveals it shouldn't be done)

### `Needs Impl` / `In progress` / `In review` (entry verification only)

These states have **entry verification but no work block**. Status here tracks the lifecycle of the *implementation artifact* (linked PR + assignee + recent commits), so entry checks are largely a matter of confirming that the issue's status agrees with that artifact's state. PM-axis still applies.

**Linked-PR detection (shared definition for all three states):**

- **L-LINK-1:** Enumerate closing PRs via the issue's GraphQL `closedByPullRequestsReferences(includeClosedPrs:true, userLinkedOnly:false)` connection (see `## Operations → linked closing PRs` for the concrete query). This returns exactly the PRs whose merge would close the issue. *Contributing*-linkage PRs do not appear here (they don't auto-close); detect those best-effort from cross-referenced PRs' bodies if needed.
- **L-LINK-2:** Classify linkage by keyword in the PR body:
  - *Closing linkage:* `closes`, `fixes`, `resolves` (and variants: `close`/`closed`, `fix`/`fixed`, `resolve`/`resolved`). Surfaced directly by `closedByPullRequestsReferences`. Merge auto-closes the issue.
  - *Contributing linkage:* `furthers`, `contributes to`, `part of`, `towards`, `progresses`, `step toward`, `builds toward`. Merge advances the issue but does not finish it. Not surfaced by `closedByPullRequestsReferences` (best-effort detection only).
- **L-LINK-3:** When multiple linked PRs exist, take the most-progressed *closing* PR as the primary signal (merged > open-non-draft > open-draft > closed-unmerged). Contributing PRs always indicate `In progress`; they never qualify for `In review`.

**Entry verification — `Needs Impl` (I-ENTRY):**

- **I-ENTRY-1:** (Downward) `Needs Eng Design` exit criteria still met (decisions captured in body or linked doc; Size set; no active blockers). If anything is missing → propose regression to `Needs Eng Design`.
- **I-ENTRY-2:** (Upward) If any **active-work indicator** is present, propose **promotion to `In progress`**. *Active-work indicator* (v1 definition, shared with PROG-ENTRY-1): an open linked PR (closing or contributing) OR an assignee set. (Raw commit references are deliberately excluded — they surface only as the noise-filtered `ReferencedEvent`.) If a non-draft closing PR exists with review requested/active, propose direct promotion to `In review`. If a closing PR is merged, propose `Done` (R-SYNC-2 handles autonomously when the issue closes).

**Entry verification — `In progress` (PROG-ENTRY):**

- **PROG-ENTRY-1:** (Downward) Snapshot check: no active-work indicator *right now* (no assignee AND no open linked PR — see I-ENTRY-2). If absent → propose regression to `Needs Impl`. This is a snapshot check; long-running-but-stale-progress is a separate PM-axis concern (staleness).
- **PROG-ENTRY-2:** (Upward) Open *closing* PR that is non-draft and ready for review → propose **promotion to `In review`**. Closing PR merged → propose `Done` (autonomous via R-SYNC-2 if the issue closes; otherwise propose explicitly). Contributing PRs alone never advance status past `In progress`.

**Entry verification — `In review` (REV-ENTRY):**

- **REV-ENTRY-1:** (Downward) No open *closing* PR, OR the closing PR is in draft, OR the closing PR is closed-without-merge → propose regression. Default target: `In progress` if any active-work indicator remains; `Needs Impl` if no claim remains.
- **REV-ENTRY-2:** (Upward) Closing PR merged → propose `Done` (autonomous via R-SYNC-2 if the issue closes; otherwise propose explicitly).

## PM axis

Triage **never auto-acts** on PM-axis findings. It surfaces them in a batch report for human decision.

### Staleness

**Computation:** at triage time, compute `staleness = now - mostRecentMeaningfulActivity`, and flag if `staleness > threshold(priority) × multiplier`. `mostRecentMeaningfulActivity` is the **max** of:
1. the `createdAt` of the newest meaningful timeline event (allowlist below), and
2. the issue's `lastEditedAt` — body/title edits do **not** generate timeline events, so they are only visible via this field (gated on `editor` not being an excluded bot).

**Concrete query** (the `since:` bound also powers the skip-optimization — fetch only events newer than `Last Triaged`):

```graphql
query($owner:String!, $repo:String!, $number:Int!, $since:DateTime) {
  repository(owner:$owner, name:$repo) {
    issue(number:$number) {
      lastEditedAt
      editor { login }
      timelineItems(since:$since, first:100, itemTypes:[
        ISSUE_COMMENT, RENAMED_TITLE_EVENT,
        LABELED_EVENT, UNLABELED_EVENT,
        ASSIGNED_EVENT, UNASSIGNED_EVENT,
        MILESTONED_EVENT, DEMILESTONED_EVENT,
        CLOSED_EVENT, REOPENED_EVENT,
        CONNECTED_EVENT, DISCONNECTED_EVENT,
        MARKED_AS_DUPLICATE_EVENT, UNMARKED_AS_DUPLICATE_EVENT,
        TRANSFERRED_EVENT, CONVERTED_TO_DISCUSSION_EVENT,
        ADDED_TO_PROJECT_V2_EVENT, REMOVED_FROM_PROJECT_V2_EVENT,
        PROJECT_V2_ITEM_STATUS_CHANGED_EVENT,
        SUB_ISSUE_ADDED_EVENT, SUB_ISSUE_REMOVED_EVENT,
        PARENT_ISSUE_ADDED_EVENT, PARENT_ISSUE_REMOVED_EVENT,
        BLOCKED_BY_ADDED_EVENT, BLOCKED_BY_REMOVED_EVENT,
        BLOCKING_ADDED_EVENT, BLOCKING_REMOVED_EVENT
      ]) {
        nodes {
          __typename
          ... on IssueComment { createdAt author { login } }
          ... on ProjectV2ItemStatusChangedEvent {
            createdAt actor { login } wasAutomated project { number }
          }
          # every other allowlisted type: request `createdAt` and `actor { login }`
          # via an inline fragment (all of them expose both — verified against schema).
        }
      }
    }
  }
}
```

Two node shapes matter: `IssueComment` carries `author`, every other allowlisted event carries `actor`. The remaining inline fragments are mechanical (`... on LabeledEvent { createdAt actor { login } }`, etc.) and omitted here for brevity.

**Meaningful-activity allowlist:** the `itemTypes:` set above. Server-side filtering means the noise set is never fetched. Add `ISSUE_TYPE_*` / `ISSUE_FIELD_*` to the list only for a project that uses GitHub's *native* issue types/fields (a repo on this ecosystem's schema — labels + ProjectV2 fields — never emits them).

**Excluded (noise), for the record:** `CROSS_REFERENCED`, `REFERENCED`, `MENTIONED`, `SUBSCRIBED`/`UNSUBSCRIBED`, `PINNED`/`UNPINNED` (+ comment-pin variants), `LOCKED`/`UNLOCKED`, `COMMENT_DELETED`, `USER_BLOCKED`, `CONVERTED_FROM_DRAFT` (PR-only), and the deprecated classic-project events (`ADDED_TO_PROJECT`, `REMOVED_FROM_PROJECT`, `MOVED_COLUMNS_IN_PROJECT`, `CONVERTED_NOTE_TO_ISSUE`).

**Exclusions applied client-side after fetch:**
- Comments/edits authored by an excluded **bot account** (profile bot whitelist can reclassify a specific bot as meaningful).
- `PROJECT_V2_ITEM_STATUS_CHANGED_EVENT` with `wasAutomated == true` (GitHub built-in board automation) or scoped to a `project` other than the profile's.

**Known v1 limitations (accepted — launch-and-iterate):**
- **Priority/Size changes are invisible to staleness.** They are ProjectV2 single-select field changes, which emit no timeline event (only Status does, via `PROJECT_V2_ITEM_STATUS_CHANGED_EVENT`). Reading them from the project item's field values would lose actor attribution and be poisoned by the skill's own `Last Triaged` writes — so v1 does not count them. Status changes *are* captured.
- **The skill's own mutations are not excluded by actor.** v1 runs under the operator's own GitHub account (no dedicated bot identity), so triage's autonomous status-syncs/label-fixes are indistinguishable from genuine manual activity. Tolerable because: `Last Triaged` writes emit no timeline event (skip-optimization stays clean if `Last Triaged` is written last in a pass), and the autonomous mutation set (R-SYNC, R-LABEL) is small and self-limiting — a one-time clock reset, not perpetual freshness. Revisit if triage ever runs under a bot identity.

**Bonus — the query does double duty.** The same fetch feeds other rules, so don't design redundant queries for them: `CONNECTED`/`DISCONNECTED` → L-LINK (linked-PR detection), `SUB_ISSUE_*`/`PARENT_ISSUE_*` → R-PARENT-3 linkage, `BLOCKED_BY_*`/`BLOCKING_*` → R-BLOCK-4.

**Default thresholds:**

| Priority | Threshold |
|---|---|
| P0 | 1d |
| P1 | 7d |
| P2 | 14d |
| P3 | 28d |

Exception: `Needs Triage` has no threshold — every triage pass reviews every `Needs Triage` issue regardless of age.

Multiplier applied per-profile (default 1).

### Other PM checks

- **Size×Status×Time smells:**
  - XS/S sitting >threshold in `Needs Impl` → prompt: "not really XS, or not really a priority?"
  - L/XL with no children → smells like missing decomposition
  - Size unset at `Needs Impl` → flag (should have been set by exit from `Needs Eng Design`)
- **Priority-distribution sanity:** priority exists to answer "what do I work on next?" The distribution is pathological when the field has *lost discriminating power*, in two modes. Both surface in the "PM-distribution flags" report group; neither auto-acts. Skill defines the checks; the profile tunes the numbers.
  - **P-DIST-1 — Tail overflow (absolute):** open P0 count > cap → flag. The cap does **not** scale with backlog size — "P0" means *drop everything*, which is bounded by human attention, not backlog volume. N open P0s means you provably cannot be dropping everything for all N, so the marker is lying. Default cap: **3** (flag at >3 open P0s); profile-tunable. Message: re-rank the weakest P0s down.
  - **P-DIST-2 — Collapse (proportional):** a single priority bucket holds **≥ 80%** of *prioritized* open issues → flag "priority isn't discriminating; re-rank to create signal." Set high deliberately so a legitimately-skewed-but-healthy backlog does not trip it. Guard: evaluate only when there are **≥ 10 prioritized open issues** (so 2-of-2 = 100% on a tiny backlog can't fire). Both numbers profile-tunable.
  - Unset priority is **not** re-counted here — R-SCREEN-4 flags each unset issue per-issue, and P-DIST-2's denominator is *prioritized* issues only, avoiding double-counting.
  - *Deferred:* a P1 WIP-style soft bound. P1 lacks P0's hard attention bound, so v1 omits it rather than invent a shaky threshold.

## Operations (data plane)

Concrete reads/writes the skill issues against GitHub. All commands assume the profile supplies the repo, project node ID, field IDs, and option IDs. The skill runs under the **operator's own `gh` credentials** (no bot identity — see Staleness "Known v1 limitations").

### Source of truth: the project board

The **ProjectV2 board is the inventory anchor**, not the repo's issue list. Reasons: the board is where Status lives (so R-SYNC needs it on both sides); it yields the **project item ID** (`PVTI_…`) required for every field mutation; and iterating items catches *closed* issues still in a non-terminal status (R-SYNC-2), which an open-issues-only scan would miss.

### Read — inventory (one paginated query drives the whole pass)

```graphql
query($project:ID!, $cursor:String) {
  node(id:$project) {
    ... on ProjectV2 {
      items(first:50, after:$cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id                                   # project item ID — required for mutations
          status:       fieldValueByName(name:"Status")       { ... on ProjectV2ItemFieldSingleSelectValue { name optionId } }
          priority:     fieldValueByName(name:"Priority")     { ... on ProjectV2ItemFieldSingleSelectValue { name optionId } }
          size:         fieldValueByName(name:"Size")         { ... on ProjectV2ItemFieldSingleSelectValue { name optionId } }
          lastTriaged:  fieldValueByName(name:"Last Triaged") { ... on ProjectV2ItemFieldDateValue { date } }
          content {
            __typename
            ... on Issue {
              number databaseId title state stateReason url lastEditedAt
              editor { login }
              labels(first:30)    { nodes { name } }
              assignees(first:10) { nodes { login } }
              parent { number }
              subIssues(first:1)  { totalCount }
            }
          }
        }
      }
    }
  }
}
```

Per item this yields everything the per-issue loop and the cross-issue pass need: current field values, labels, assignees, parent/child linkage, edit recency, and the item ID for writes. Skip items whose `content.__typename` is not `Issue` (draft cards, PRs). A `null` field value means *unset* (e.g., unset Status → treat as un-triaged; feeds R-SCREEN-4 for Priority).

### Read — board ↔ open-issues reconciliation

Cheap second query: list open issue numbers and diff against the board's `content.number` set. Any open issue **not** on the board has no Status at all → surface as "not on board" (add + triage). `gh issue list --repo <repo> --state open --limit 500 --json number`.

### Read — staleness / timeline

See `## PM axis → Staleness` for the concrete `timelineItems` query. The `since:` bound is `Last Triaged` from the inventory. That same fetch supplies linkage events for L-LINK / R-PARENT / R-BLOCK (double duty).

### Read — linked closing PRs (L-LINK)

```graphql
closedByPullRequestsReferences(first:20, includeClosedPrs:true, userLinkedOnly:false) {
  nodes { number state isDraft merged mergedAt title url body }
}
```

`includeClosedPrs:true` surfaces closed-unmerged closing PRs (needed by L-LINK-3's ordering); `userLinkedOnly:false` catches keyword-based linkage, not just sidebar-linked PRs. **Caveat:** this field returns only *closing*-linkage PRs. *Contributing*-linkage PRs (`furthers`/`part of`/…) do not auto-close, so they are **not** returned here — they appear only as cross-references. Since contributing PRs never advance status past `In progress` (L-LINK-3), v1 treats closing-PR detection as authoritative and contributing-PR detection as best-effort (scan cross-referenced PRs' bodies for contributing keywords if needed).

### Write — mutations

If a `use-privacy` skill is listed among your available skills, load it before composing any text bound for outside this machine: an issue body, a comment.

| Target | Command |
|---|---|
| Status / Priority / Size | `gh project item-edit --id <ITEM_ID> --project-id <PROJECT_NODE_ID> --field-id <FIELD_ID> --single-select-option-id <OPTION_ID>` |
| Last Triaged | `gh project item-edit --id <ITEM_ID> --project-id <PROJECT_NODE_ID> --field-id <LAST_TRIAGED_FIELD_ID> --date <YYYY-MM-DD>` |
| Labels | `gh issue edit <NUM> --add-label <L> --remove-label <L>` |
| Body (only where the playbook permits) | `gh issue edit <NUM> --body-file <file>` |
| Close as Done / Rejected (approved transitions) | `gh issue close <NUM> --reason completed` / `gh issue close <NUM> --reason "not planned"` |
| Reopen | `gh issue reopen <NUM>` |
| Sub-issue link (R-PARENT-3, R-GROUP) | `gh api -X POST repos/<owner>/<repo>/issues/<PARENT_NUM>/sub_issues -F sub_issue_id=<CHILD_DATABASE_ID> -H "Accept: application/vnd.github+json"` (typed `-F`, database ID — *not* issue number or node ID) |

**Autonomy boundary:** only R-SYNC status corrections, R-LABEL schema fixes, and `Last Triaged` bumps are written without asking (all bounded/enumerable field writes). Everything else — priority/size/status *transitions*, scoping/typo body rewrites (R-SCREEN-9 included), closes, reparenting — is **proposed** in the report and awaits human confirmation. There is deliberately no autonomous body-write path (R-CAD-5). Write `Last Triaged` **last** in a pass so the skip-optimization comparison stays clean (it generates no timeline event).

**Deferred:** writing GitHub blocked-by / blocking relationships (R-BLOCK-4) — the mutation path is newer and unverified; v1 relies on the `**Blocked on:**` body marker (R-BLOCK-3) as primary, and sets the GitHub relationship manually when needed. Verify and automate in a later edition.

## Triage pass workflow

1. **Inventory:** run the board inventory query + reconciliation diff above. Cross-reference with profile.
2. **Per-issue loop:** for each open issue:
   - Apply cross-cutting rules (sync, label, parent-tracker)
   - Apply current-state playbook
   - Compute staleness + PM-axis signals
   - Record per-issue action: mutate-now, flag-for-batch, or skip (already up-to-date)
3. **Cross-issue pass:** with the full inventory in hand, run the checks that span issues rather than living inside one: grouping-candidate detection (R-GROUP-1) and duplicate detection (R-SCREEN-7). These cannot be evaluated in the per-issue loop because they compare issues against each other.
4. **Batch surfacing:** group flags by decision type (re-prioritize / re-size / investigate-stale / commit-to-doing / reject / split / group / etc.). Present to human in batches, not per-issue.
5. **Mutations:** apply approved actions. Update `Last Triaged` on every issue touched.

### Skip optimization

If `Last Triaged > <most recent non-triage activity>`, the issue hasn't changed since last triage. Skip detailed checklist; only re-evaluate staleness.

## Output: triage report

Generated at the end of a triage pass. Groups affected issues by the kind of attention they need. Each group is its own section.

**Standard groups:**

- **Auto-applied changes** — what triage already did without asking (label fixes, status/issue-state syncs, `Last Triaged` rev'd, etc.). FYI only.
- **Needs label fixes** — issues missing type or area labels where the right label isn't obvious.
- **Likely duplicates** — fuzzy-matched pairs/groups for human merge confirmation.
- **Stale-irrelevant candidates** — issues that may have been resolved by other work (per R-SCREEN-8); needs human verification.
- **Split candidates** — issues meeting R-SPLIT-1 criteria.
- **Misclassified state** — issues failing entry verification for their current state, in either direction: *downward* (e.g., `Needs Eng Design` items lacking a business goal → should regress to `Needs Scope`) or *upward* (e.g., `Needs Triage` items that already have full goal + AC + UX scope → should promote directly to `Needs Eng Design`).
- **Open scoping questions** — items in `Needs Scope` with pending business or UX scoping questions; the agent surfaces specific questions for human input.
- **Open eng-design decisions** — items in `Needs Eng Design` with pending decisions; the agent surfaces specific decisions for human input.
- **Skip-eng-design candidates** — items in `Needs Scope` where the agent believes the work is mechanical enough to bypass `Needs Eng Design` (per S-WORK direct-exit criteria). Human confirms.
- **ADR-creation candidates** — captured decisions (scope, UX, eng design) where the R-ADR-1 three-part rubric fires. Human decides whether to create the ADR.
- **Stale — needs PM attention** — items past staleness threshold, grouped by likely action: re-prioritize / re-size / commit-to-doing / reject.
- **Blocked** — items at their blocking stage with a `Blocked on:` marker. Scanned each pass to detect resolved blockers; otherwise sits quietly.
- **Grouping candidates** — clusters of open issues that should become one unit of work: reparented under a tracker (parent grouping) or merged into one issue (collapse). Per R-GROUP-1.
- **PM-distribution flags** — priority distribution has lost discriminating power: tail overflow (too many open P0s, P-DIST-1) or collapse (one bucket holds ≥80% of prioritized issues, P-DIST-2).

### Per-item format

The report's atomic unit is a **finding** — a `(group, finding, action)` tuple — **not** an issue. One issue may appear in several groups (a different finding in each); several issues may collapse into one finding (same finding + action across all of them). This decoupling is what lets the report stay legible on a backlog with dozens of identically-broken issues.

- **R-RPT-1 — Entry skeleton.** Every entry, single or folded, renders a three-line core:

  ```
  #N "short title"  [current-state → proposed-state]
    finding: <which rule fired and what it saw>
    action: <what is proposed, or — for auto-applied — what was done>
  ```

  - The `[state → state]` bracket shows a proposed status transition. Collapse to `[current-state]` (no arrow) when the finding proposes no status change (label fix, PM flag, scoping question).
  - `action:` names the autonomy: auto-applied findings state what was done (past tense); proposed findings state what awaits confirmation, plus the one command/step to apply it where non-obvious.

- **R-RPT-2 — Folding (homogeneous-cluster collapse).** Within a group, members sharing an **identical `(finding, action)`** fold into one entry. The fold key is the *outcome* (finding + action), never parent/child structure — so a tracker's 25 children that all trip the same rule collapse to a single entry, while a child tripping a *different* rule is not swept in. Folded render:

  ```
  <count> issues — <shared finding>  [shared state → state]
    action: <shared action>
    members: #a "title", #b "title", #c "title", …
  ```

  The shared `[state → state]` appears in the header only when identical across all members; otherwise drop it from the header and let each member carry its own bracket in the member list. (Without this, dozens of `Needs Triage` items plus a tracker's children would drown the report.)

- **R-RPT-3 — Divergence pulls out, never summarized-away.** A member that shares the group but differs in finding or action is **not** folded — it renders as its own full R-RPT-1 entry in the same group. No "…except #N" tails, no footnotes: every divergent outcome gets its own visible entry. (Cost: a near-homogeneous cluster with one oddball renders as one fold + one standalone — the intended legibility trade.)

- **R-RPT-4 — Group-specific extras.** Beyond the skeleton, some groups append structured fields:

  | Group | Extra fields per entry |
  |---|---|
  | Split candidates | per-checklist-item verdict: each item → {peel / keep} + the rule that decided (V-/T-/M-) + proposed sub-vs-peer flavor |
  | Grouping candidates | cluster members, detected flavor (parent / merge), and the gate that passed (G-WHOLE, or GM-RELATED+GM-SIZE) with a one-line justification |
  | Stale — needs PM attention | `age: <Nd> (P<k> × mult <m> = <threshold>d; last activity <event> on <date>)` |
  | Blocked | the `Blocked on:` marker text + whether the blocker is a tracked issue (link) or external |
  | PM-distribution flags | **aggregate only** — no per-issue entries; renders the per-bucket counts + which check fired (P-DIST-1/2) + the recommended re-rank |

- **R-RPT-5 — Empty groups omitted.** A group with no findings is dropped entirely (no empty header). The report ends with a one-line "clean:" summary naming the standard groups that came back empty, so a reader knows they were checked, not skipped.

- **R-RPT-6 — Ordering.** Within a group: folded entries first (descending member count), then standalone entries by priority (P0 first), then issue number. Exception: the staleness group orders by descending age. Across groups: lead with the autonomous/FYI **Auto-applied** group, then the human-actionable groups in lifecycle order, ending with the **PM-distribution** aggregate.

## Cadence & autonomous operation

> How triage runs *repeatedly and unattended*. The skill is invocable two ways — **interactive** (a human is present) and **unattended** (headless, e.g. a scheduled background job). Both reconcile the same durable ledger; they differ only in how far a finding can be carried toward resolution in-session.

### Run modes

- **R-CAD-1 — Two modes, one ledger.** *Interactive*: a human is present; the agent may conduct scope / eng-design dialogue (S-WORK / E-WORK) and apply proposed mutations the human approves in-session. *Unattended*: headless; no dialogue is possible. Both modes run the same pass (inventory → per-issue → cross-issue → reconcile ledger) and write the same ledger artifact. The only difference: an unattended run can *accumulate* proposals but never *resolve* the with-human ones.
- **R-CAD-2 — Unattended scope.** An unattended pass does exactly: (a) apply the autonomous set (R-SYNC status corrections, R-LABEL schema fixes, `Last Triaged` bumps — all bounded/enumerable writes; body typo-fixes are *not* in this set, per R-SCREEN-9), (b) recompute findings for changed issues, (c) reconcile the ledger (R-LEDG-*). It never conducts interactive work and never applies a with-human proposal. Everything needing a human surfaces as a pending ledger finding.
- **R-CAD-3 — The permission layer is the enforcement; a denial is terminal for the pass.** Unattended runs use `--permission-mode dontAsk` with an allowlist of wrapper-script names only (R-CAD-5). A tool call outside the allowlist is *auto-denied*, not prompted — so a stray attempt at a proposed mutation fails closed instead of hanging. On denial the agent records the intended action as a pending finding and moves on; it must **not** seek an alternate path to the same mutation. (Fail-safe: the dangerous direction stalls, the safe direction flows.)

### The triage ledger

If a `use-privacy` skill is listed among your available skills, load it before composing any text bound for outside this machine: the ledger body, a changelog comment.

- **R-LEDG-1 — A durable, skill-owned GitHub issue.** The report is not regenerated into chat each pass; it is a single GitHub issue (the "triage ledger") whose number is bound in the profile (required). The skill *owns* this issue: it is the one issue triage writes to autonomously every pass, and it is **excluded from triage as a subject** — never itself triaged, sized, or prioritized.
- **R-LEDG-2 — Body = state, comments = events.** The issue **body** holds the *current* set of open findings in the R-RPT format (groups, folding, ordering); each pass **rewrites the body** to reflect current state. The issue **comments** hold a per-pass **changelog**: what was auto-applied this pass, plus a one-line delta (`+N new, −M resolved, K pending`). Body answers "what needs my attention right now"; comments answer "what changed since I last looked."
- **R-LEDG-3 — Finding identity.** A finding's stable identity across passes is `(rule-id, issue-number, action-key)` — independent of R-RPT-2 display folding (which folds homogeneous findings across issues for *rendering* only). Identity is per-issue-per-rule; folding is a presentation layer on top.
- **R-LEDG-4 — Reconciliation (the core).** Each pass reconciles recomputed findings against the prior ledger:
  - **New** (identity absent last pass) → add.
  - **Resolved** (issue changed *and* recomputation shows the rule no longer fires, or the issue left the relevant state / was closed) → retire; note it in the changelog.
  - **Carried-forward / pending** (issue unchanged, so the skip-optimization never recomputed it) → **keep the prior finding verbatim.** This is the crux: the skip-optimization means an unchanged issue is *not* re-examined, so without the ledger its pending proposal would silently vanish (the failure this whole design exists to fix). The ledger *is* the memory the skip-optimization discards.
- **R-LEDG-5 — Aging.** A carried-forward finding records `pending since <date> (<N> passes)`. Aging is informational — it makes chronic un-acted proposals visible — and does not auto-retire or auto-escalate in v1.
- **R-LEDG-6 — Dismissal (minimal; PROVISIONAL).** A human declines a proposal by moving it into a `## Dismissed` section of the ledger body. A dismissed finding is suppressed (not re-added) until the underlying issue *materially* changes, operationalized as: the issue's `lastEditedAt` advances past the dismissal timestamp. This kills the daily nag of re-proposing something already declined, while letting a genuine later edit resurface it. **Most likely part of this design to need iteration** — flagged provisional; revisit once real dismissals accumulate.

### Delta vs. census (synthesis)

- **R-CAD-4 — A pass computes a delta; the ledger presents a census.** The skip-optimization means a recurring pass only *recomputes* issues changed since `Last Triaged` — inherently a delta. Carry-forward (R-LEDG-4) means the ledger **body** nonetheless always shows the *full* current set of open findings. Cheap incremental passes, full-state artifact. This is what makes a *daily* cadence worth more than an occasional manual full run without re-deriving the whole backlog every morning.

### Wrapper-enforced autonomy boundary

- **R-CAD-5 — All GitHub I/O routes through skill-owned wrapper scripts; the allowlist is wrapper names only.** Reads and autonomous writes are performed by small wrapper commands in `reference/` (e.g. `triage-inventory`, `triage-timeline`, `triage-apply-sync`, `triage-fix-label`, `triage-bump-triaged`, `triage-update-ledger`). The headless allowlist (`permissions.allow`) contains **only these wrapper names** — never raw `gh`. Consequences, by construction:
  - Per-project opaque IDs (field IDs, option IDs, project node ID, ledger issue number) live only in the profile, are read only by the wrappers, and never appear in a shell command or a settings file — so the allowlist stays project-agnostic and can live in global `~/.claude/settings.json`.
  - Wrappers read the profile internally, so the agent never constructs `gh … --field-id $(…)`, sidestepping the command-substitution permission-parser pitfall.
  - **Proposed** mutations (status/priority/size transitions, scope-body rewrites, closes, reparent / `sub_issues`) have **no allowlisted wrapper path** — under `dontAsk` they fail closed (R-CAD-3). The autonomy boundary and the permission boundary are thereby *the same line*, enforced by both policy and the OS-level permission check.
  - The ledger update (R-LEDG-2) is itself an autonomous write and gets its own wrapper (`triage-update-ledger`).
  - **Wrappers encode *policy*, not just *mechanism*.** An autonomous write wrapper is not a thin `gh` shim: it re-derives its own precondition and emits only the sanctioned result, so an allowlisted invocation cannot be coerced into a *proposed* mutation even with hostile arguments. Concretely: `triage-apply-sync` re-reads the issue's open/closed state + current Status and applies only the R-SYNC-1/2 correction it derives (it cannot be *told* a target status); `triage-fix-label` refuses any label outside the profile schema; `triage-bump-triaged` writes only the Last Triaged date; `triage-update-ledger` takes no issue number and writes only to the profile's ledger issue. **Invariant: every autonomous wrapper emits only a bounded/enumerable value (an option id, a schema label, a date) or free text confined to the one ledger issue — none can write free text to an arbitrary issue.** This is what lets "permission boundary == autonomy boundary" hold at the argument level, not just the command level. (It is also why R-SCREEN-9 body typo-fixes are *not* autonomous — see that rule.)

  (The Operations data-plane table lists the raw `gh` commands each wrapper encapsulates; wrappers are the only allowlisted entry points to them.)

### Bootstrap (interactive, one-time, per project)

- **R-CAD-6 — Standing up triage in a new repo is an interactive bootstrap, never autonomous.** Once per project: (1) create the ledger issue (`gh issue create`), (2) write its number into the profile `TRIAGE.md`, (3) optionally pin it. Creating a durable artifact and editing a committed repo file are outside the autonomous set; a human confirms. Steady-state (including every unattended run) only ever *reads* the pointer and *edits* the existing ledger.

### Deployment

The *scheduling mechanism* is a per-deployment concern, not skill policy, and lives in `reference/DEPLOYMENT.md`. Do not host unattended triage in a repo whose project settings allowlist `ghw-*` write verbs: that grants a write path outside the triage wrappers, so the permission boundary no longer equals the autonomy boundary (see the caveat in `reference/DEPLOYMENT.md` §3).

**Recommended: a Claude Desktop *Local* routine.** It runs against the real local repo, honors `~/.claude/settings.json` (so the wrapper allowlist + R-CAD-3 fail-closed boundary apply unchanged), and lets the Desktop app own scheduling and subscription auth — no trigger script to maintain. Configure it deny-by-default (`dontAsk` or equivalent — **never** `bypassPermissions`, which would auto-approve proposed mutations and defeat the fail-safe).

**Billing.** Authenticate via the subscription (never `ANTHROPIC_API_KEY` — an all-or-nothing switch to pay-as-you-go) and leave Console *usage credits* **disabled** (an exhausted run stops rather than overflowing to paid API). Run the unattended pass on a **cost-efficient model** — the autonomous pass is mechanical; reserve Opus for interactive scope/eng-design (the cadence config may bind the model).

**Fallback: a background job dispatched by a guard script.** A trigger (a `launchd` agent on a schedule, or a `SessionStart` hook) runs a small script that skips if a marker file says today's pass already ran, takes a lock so two triggers cannot dispatch twice, and dispatches `claude --bg "<prompt>" --name <job-name> --worktree <name> --permission-mode dontAsk --allowedTools "Edit(<worktree-root>/**),Edit(<job-tmp-root>/**)" < /dev/null`. The Edit grants are required because `dontAsk` denies every file write, even in the run's own worktree, and the run must write the ledger body file. The run, not the guard, writes the success marker as its final act after the ledger update; the guard reaps finished runs' worktrees and branches so they do not accumulate. It needs run-level failure surfacing (logfile + the stale-ledger tripwire: the ledger's last-updated date not advancing). `claude -p` from the same trigger is an alternative; it may be billed differently from interactive use on subscription plans, so check your plan's terms before adopting it. Details in `reference/DEPLOYMENT.md` §4.

Claude Code's in-session schedulers (`CronCreate` / `/loop` / `ScheduleWakeup`) are **not** suitable — they require an open REPL and expire after 7 days. A Desktop *Cloud* routine executes against a repo clone with connector-based writes and **bypasses this skill's local wrapper/allowlist model** — avoid it for autonomous mutation.

## Open / TODO

- ~~Triage cadence / auto-invocation hooks~~ — **specced** in `## Cadence & autonomous operation` (ledger + reconciliation + headless contract + wrapper-enforced boundary).
- ~~Write the GitHub-I/O wrapper scripts (`reference/`)~~ — **done.** Six policy-bound wrappers + `lib_profile.py`/`lib_gh.py`, validated against a real board (reads live, writes dry-run). See `reference/README.md`.
- ~~Write `reference/DEPLOYMENT.md`~~ — **done.**
- R-LEDG-6 dismissal is provisional and likely needs iteration (revisit once real dismissals accumulate).
- First **live** (non-dry) triage run: not yet exercised end to end. A first live pass recomputes its findings from the board's current state, so it needs no queued input.
- UX trigger heuristic refinement — current trigger ("user-observable surface") is somewhat informal; tighten as cases accumulate
- "Recent commits referencing this issue" — concrete time window for I-ENTRY-2 / PROG-ENTRY-1 (e.g., last 7 days?). Probably ties to staleness thresholds; revisit when those are tuned.
- Linkage keyword coverage — current closing/contributing keyword sets may need extension as we encounter real PR-body phrasings
- Contributing-PR detection is best-effort in v1 (`closedByPullRequestsReferences` returns closing PRs only) — revisit if contributing-linkage signals prove load-bearing
- Upper-bound issue-size check — should L/XL issues be auto-flagged for decomposition? Deferred until oversized issues show up in practice.
- Validation: profile confirmed sufficient for the data plane (field IDs + canonical names cover every read/write). Re-confirm if the report format or cadence work needs new profile fields.
- Blocked-by / blocking *write* path (R-BLOCK-4) — newer API, unverified; v1 sets relationships manually. Automate later.
