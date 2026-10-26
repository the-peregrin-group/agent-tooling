# Extract C: the `triage-issues` skill (plus triage-describing project docs)

> This document captures state as of 2026-10-26. For current state, see [docs/index.md](../../index.md).

Sources read (paths relative to the repo root):

- `skills/triage-issues/SKILL.md` (all 654 lines)
- `skills/triage-issues/reference/README.md`, `reference/DEPLOYMENT.md`
- `skills/triage-issues/reference/triage-apply-sync`, `triage-fix-label`, `lib_profile.py` (policy parts only)
- `docs/projects/ghw/index.md`, `docs/projects/ghw/design.md` (triage passages), `docs/projects/ghw/triage-library-rebase.md` (skimmed)
- `docs/projects/fjw/issue-verbs.md` (triage passages), `docs/projects/use-bd/v1-proposal.md` (triage passages)
- Beads Issues that describe triage intent: `agent-tooling-r6b` (automated batch triage), `agent-tooling-c86` (status-gated lifecycle on Beads), `agent-tooling-u9n` (split the tracker skills into a tool-agnostic layer)
- For contradictions only: `skills/use-github/SKILL.md`, `skills/use-bd/SKILL.md`, `docs/audits/2026-10-11-agent-versus-human-line.md`

## A note on history that applies to almost every entry

`skills/triage-issues/` has only four commits in this repo (`git log --follow`):
`cb6f1eb` 2026-09-22 "Initial import: shared Claude Code agent tooling", two
use-privacy one-liners (`ca67ca6`, `78150fe`, 2026-10-01), and `5ec1a8c`
2026-10-11 "Make the guard-script background job the one triage launch form"
(Lands agent-tooling-za1). The initial import says the tree was "Extracted
2026-09-22 from a private predecessor repository ... its history stays there
and this repository's history begins here by design." So for every SKILL.md
principle below, the earliest *traceable* form is `cb6f1eb` and the text is
unchanged since then except where noted; the real origin and any drift before
2026-09-22 are not visible from this repo. Provenance is therefore mostly
"unknown". I did not read the predecessor repo (location unknown; the brief
forbids the maintainer's knowledge base).

Where the 2026-10-11 agent-versus-human audit
(`docs/audits/2026-10-11-agent-versus-human-line.md:150-164`) records "None
given" as the reason for a triage restriction, I cite that as evidence the rule
is unexplained, not that it is agent-elaborated.

---

## Principles

### C1: Status answers "what kind of expert attention does this need next?"
- Category: lifecycle
- Generic or specific: generic
- Current text (verbatim, with path:line): "The skill is **opinionated** about the model. Status answers: **\"what kind of expert attention does this issue need next?\"**" (`skills/triage-issues/SKILL.md:50`)
- Earliest form: cb6f1eb, 2026-09-22, Initial import; unchanged
- Provenance: unknown, leaning ratified; evidence: the maintainer's own Beads lifecycle sketch (agent-tooling-c86, "Sketch from the maintainer (2026-10-09, use-bd home-in ...), not ratified") says an Issue "moves to needs_scope, in the manner of the triage-issues skill's state model", i.e. the maintainer cites this model as the template.

### C2: The eight canonical states and per-state autonomy
- Category: lifecycle / agent-vs-human
- Generic or specific: generic (state names and their semantics); the "Project board Status field" carrier is GitHub-specific
- Current text (verbatim, with path:line): table at `skills/triage-issues/SKILL.md:52-61`: "| `Needs Triage` | Screening / bookkeeping | Fully agent-autonomous |", "| `Needs Scope` | Business-level scoping (define the goal) | Agent + human-in-loop |", "| `Needs Eng Design` | Engineering-level scoping (design decisions) | Agent + human-in-loop |", "| `Needs Impl` | Decisions made; ready for any implementer | (PM-axis only) |", "| `In progress` | Claimed; being executed | (PM-axis only) |", "| `In review` | Reviewer attention | (PM-axis only) |", "| `Done` | Resolved | Terminal |", "| `Rejected` | Decided not to do | Terminal |"; and "The split between fully-autonomous work (screening) and agent+human collaboration (scoping/design) is explicit per state." (`:17`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown; evidence: none in-repo; the audit (row R1) classifies it under "Bounded autonomy; Ratify". The same eight states are provisioned by `ghw-board-sync` ("`Status` (the eight canonical triage states)", `docs/projects/ghw/design.md:208`), so the model is load-bearing across the ecosystem.

### C3: All eight states required; omission is deferred, full customization out of scope
- Category: lifecycle / setup
- Generic or specific: generic
- Current text (verbatim, with path:line): "**Future customizability (deferred):** v1 requires all 8 states. Future versions may allow simpler/informal projects to *omit* some intermediate states (e.g., merge `Needs Scope` and `Needs Eng Design`). Full state-graph customization is out of scope." (`skills/triage-issues/SKILL.md:63`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C4: Forward transitions (default exits per state)
- Category: lifecycle
- Generic or specific: generic
- Current text (verbatim, with path:line): "- `Needs Triage` → `Needs Scope` | `Done` | `Rejected`" / "- `Needs Scope` → `Needs Eng Design` | `Needs Impl` (if narrow/clear) | `Rejected`" / "- `Needs Eng Design` → `Needs Impl` | `Rejected`" / "- `Needs Impl` → `In progress` | `Rejected`" / "- `In progress` → `In review` | `Needs Impl` (released back to queue) | `Rejected`" / "- `In review` → `Done` | `In progress` (revisions) | `Rejected`" (`skills/triage-issues/SKILL.md:68-73`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C5: Regression allowed any time; triage proposes, human approves
- Category: lifecycle / agent-vs-human
- Generic or specific: generic
- Current text (verbatim, with path:line): "**Backward (regression):** allowed at any time. Triage *proposes*; human approves." / "- → `Needs Scope` if new info invalidates the goal" / "- → `Needs Eng Design` if new info requires re-design" (`skills/triage-issues/SKILL.md:75-77`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown; the audit records the reason as "None given." (`docs/audits/2026-10-11-agent-versus-human-line.md:151`)

### C6: Tracker open/closed state and Status must agree (autonomous sync)
- Category: lifecycle / closing
- Generic or specific: mixed (generic: an open Issue cannot sit in a terminal state and vice versa; specific: board Status vs GitHub issue state, close reason "not planned")
- Current text (verbatim, with path:line): "- **R-SYNC-1:** Open Issue + Status `Done`/`Rejected` → must move. Default: demote to `Needs Scope`; surface for human if ambiguous." / "- **R-SYNC-2:** Closed Issue + Status not `Done`/`Rejected` → must set to `Done` (or `Rejected` if the close reason supports it)." (`skills/triage-issues/SKILL.md:83-84`). The wrapper encodes it as: "R-SYNC-2: issue CLOSED but Status not terminal  -> set Done (or Rejected if the issue was closed as not-planned). R-SYNC-1: issue OPEN but Status terminal (Done/Rejected) -> demote to Needs Scope." (`skills/triage-issues/reference/triage-apply-sync:10-12`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C7: Label compliance: exactly one type label, one or more area labels, checked every pass
- Category: labels-priority
- Generic or specific: mixed (generic: every Issue has exactly one kind and at least one area; specific: carried as labels with an `area:` prefix)
- Current text (verbatim, with path:line): "- **R-LABEL-1:** Every issue must have **exactly one** label from the profile's *type* family and **one or more** `area:*` area labels. Labels outside the profile's declared families (e.g. unprefixed scope labels) are neither required nor flagged. Validated on every triage pass, not just at `Needs Triage`. Profile supplies the actual labels." (`skills/triage-issues/SKILL.md:88`); and "- **R-SCREEN-1:** Verify label compliance (R-LABEL-1). Fix if obvious; flag if ambiguous." (`:185`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown; the same contract is in use-github ("**Every issue gets exactly one type label plus one or more `area:` labels.**", `skills/use-github/SKILL.md:120`), also from cb6f1eb.

### C8: Split criteria for a bundled checklist (per item; vetoes, strong trigger, meatiness)
- Category: breakdown
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-SPLIT-1:** If an issue body contains a checklist of N items, evaluate each item against the split criteria below. The rule applies *per item*: a bundle can be partially split (some items peeled off as peer/sub-issues, others remaining in the bundle)." (`skills/triage-issues/SKILL.md:92`); "- **V-THEME:** No unifying theme — items are a grab-bag of unrelated work → split into peers." (`:95`); "- **V-ATOMIC:** Items cannot be cleanly decomposed into discrete atomic changes → do **not** split; find a better decomposition or accept the bundle. Dependence between atoms is fine; intertwining that prevents atomic decomposition is not." (`:96`); "- **T-DOC:** The item, if executed in isolation, would warrant its own design doc per the consequence rubric in E-WORK-2 (2+ consequence signals fire). Sub-issue if a component of the parent's initiative; peer issue if orthogonal." (`:99`); "- **M-SCOPE:** Sufficient scope — the item, as its own issue, would be sized M+. XS items rarely worth splitting; S is borderline." (`:102`); "- **M-CTX:** Context-switch cost — implementing the item requires loading a different mental model from its siblings (different subsystem, layer, or abstraction). High cost favors splitting; low cost (same mechanical pattern across files, e.g.) makes splitting discretionary." (`:103`); "Decision: both meatiness signals favor splitting → propose split. Mixed → judgment call; default to batched." (`:105`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown (the rule-ID density and lettered sub-rules look like agent-structured text, but the criteria themselves could be the maintainer's; no evidence either way)

### C9: Two split flavors: peer split and parent-child decomposition
- Category: breakdown / relationships
- Generic or specific: mixed (generic: the two flavors and when to use each; specific: "GitHub sub-issues API")
- Current text (verbatim, with path:line): "- **Peer split:** item becomes a separate sibling issue; original may close (or stay open with remaining items, in a partial split)." / "- **Parent-child decomposition:** original becomes parent; children link via GitHub sub-issues API. Both sized independently. Use when the work is cohesive but multi-step." / "Flavor choice: T-DOC and the meatiness heuristic produce sub-issues for items that are components of the parent's initiative, peer issues for orthogonal items. V-THEME (grab-bag bundle) splits into peers by definition." (`skills/triage-issues/SKILL.md:108-111`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C10: Grouping (parent flavor): the whole-goal gate; dependency is never a grouping signal; prefer vertical slices
- Category: breakdown / relationships
- Generic or specific: generic
- Current text (verbatim, with path:line): "**Detection (cheap pre-filter):** 2+ open issues sharing a type label and an overlapping `area:*`. Shared labels are *necessary, not sufficient* — a coincidental label match is not a group. Membership is established by the gates below, not by labels." (`skills/triage-issues/SKILL.md:115`); "- **G-WHOLE (gate):** the goal is *incomplete until all members are done*. Operational test: \"does landing any single member alone deliver standalone value?\" If **no** (each member is inert without the others) → group. If **yes** for all (each ships value independently) → do **not** group; they are independent issues. Link via blocked-by if dependent — dependency is *never itself* a grouping signal (R-BLOCK-4)." (`:118`); "- **GV-HORIZ (veto):** the cluster is a *horizontal* slice (one shared concern spanning many features) where a *vertical* slice (one feature end-to-end) was possible. Prefer vertical. Exception: the horizontal IS the entire deliverable (e.g., \"add test coverage across the codebase\" — testing is the whole project, not stage M of an N-stage feature)." (`:119`); "- Members keep independent status (R-PARENT-1) and independent size (R-PARENT-4). Members may be any size; meaty children are expected and normal here." (`:121`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C11: Grouping is semantic only; releases and schedules are not parents
- Category: relationships
- Generic or specific: mixed (generic: thematic/release ties are not composition; specific: "Use GitHub Milestones")
- Current text (verbatim, with path:line): "- **GV-MILESTONE (veto):** the tie among members is merely thematic, or is a release / schedule / deliverable grouping. Grouping is for *semantic relatedness* only. Use GitHub Milestones for releases and schedules — never a parent tracker." (`skills/triage-issues/SKILL.md:120`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C12: Merge (collapse) flavor is rare; don't over-decompose; absorbed Issues are closed with a back-link
- Category: breakdown / closing / filing
- Generic or specific: mixed (generic: rarity, the gates, close-with-back-link; specific: "close-reason enum has no 'merged' option")
- Current text (verbatim, with path:line): "**Flavor 2 — Merge into one issue (collapse).** Inverse of peer split (one issue → N peers becomes N peers → one issue). Fold several issues into one, closing the others. **Expected to be rare** — 99% of the time the right move is to not over-decompose into a swarm of XS issues in the first place." (`skills/triage-issues/SKILL.md:123`); "- **GM-RELATED:** members are *the same task applied across an axis* (e.g., the same two-line boilerplate change on 10 test files) OR all serve the same single goal/outcome." / "- **GM-SIZE:** the members' *aggregate* size is ≤ M." (`:125-126`); "- **R-SCREEN-7 hand-off:** if the members collapse to literally *one* change (not N distinct changes), they are duplicates, not a merge — route to duplicate handling instead." (`:127`); "- **Action:** fold into the clearest primary issue (or a fresh one); close the absorbed issues as *not planned* with a mandatory `Absorbed into #X` comment and back-link. The close-reason enum has no \"merged\" option — \"not planned\" is lossy, but the back-link preserves traceability. Leaving the absorbed issues open is *not* an option; it re-creates the noise the merge exists to remove." (`:128`); "**Type discriminator (size decides):** meaty members that are individually moot → Flavor 1 (parent). Small members, aggregate ≤ M, over-decomposed → Flavor 2 (merge). Meaty members that each ship value independently → neither; leave separate (link if dependent)." (`:130`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C13: Grouping never auto-acts
- Category: agent-vs-human
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-GROUP-2:** Grouping never auto-acts. The agent surfaces proposals in the \"Grouping candidates\" report group; reparenting, tracker creation, and especially issue-closing await human confirmation." (`skills/triage-issues/SKILL.md:132`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown; audit row R3 records the reason as "None given." (`docs/audits/2026-10-11-agent-versus-human-line.md:152`)

### C14: Parent status is independent of children (no derived status)
- Category: lifecycle / relationships
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-PARENT-1:** Parent trackers have an *independent* status from their children. Derived state breaks down on mixed-state child sets." (`skills/triage-issues/SKILL.md:136`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C15: Parent lifecycle: what the parent itself needs next
- Category: lifecycle
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-PARENT-2:** Parent lifecycle (status answers \"what does the parent itself need next?\"):" then "- `Needs Eng Design` — foundational eng-scoping (global criteria, decomposition strategy) pending. *Per-child* eng-scoping happens at child level and does NOT keep parent here." / "- `Needs Impl` — generally N/A for parents" / "- `In progress` — foundational eng-scoping done AND any child has non-zero progress" / "- `In review` — optional final walkthrough" / "- `Done` — all children Done or Rejected" (`skills/triage-issues/SKILL.md:137-144`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C16: Formal parent-child linkage is the source of truth; a body checklist is narrative only
- Category: relationships / docs-linkage
- Generic or specific: mixed (generic: the tracker's native link is authoritative over prose; specific: "GitHub sub-issues API")
- Current text (verbatim, with path:line): "- **R-PARENT-3:** Children must be linked via the GitHub sub-issues API. A body checklist can co-exist for narrative; formal linkage is the source of truth." (`skills/triage-issues/SKILL.md:145`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C17: Parents are sized independently of children
- Category: labels-priority / breakdown
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-PARENT-4:** Parents are sized independently of children (parent reflects total initiative scope; children reflect per-step scope)." (`skills/triage-issues/SKILL.md:146`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C18: Scope-completeness of a parent is a body convention, not a status
- Category: breakdown / lifecycle
- Generic or specific: generic (the convention); the default phrasing is a markdown checkbox
- Current text (verbatim, with path:line): "- **R-PARENT-5:** Scope-completeness is encoded by body convention, not status. Default convention: a `- [ ] All children created (scope locked)` checklist item in the parent body. Profile may override the phrasing." (`skills/triage-issues/SKILL.md:147`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C19: What a blocker is, and that it only matters once the Issue reaches the stage it bites
- Category: relationships / lifecycle
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-BLOCK-1:** A \"blocker\" is an external dependency (another issue, an engine update, a third-party release, team capacity in another domain) that prevents an issue from progressing beyond a specific lifecycle stage." / "- **R-BLOCK-2:** Determine the lifecycle stage at which the blocker actually bites. If the issue is currently *earlier* than that stage, its status reflects its true current lifecycle and progress continues freely — the blocker does not yet matter." (`skills/triage-issues/SKILL.md:151-152`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C20: Blocked marker in the body, plus the native relationship when the blocker is an Issue
- Category: relationships
- Generic or specific: mixed (generic: status stays at the blocking stage; mark it; use the native edge when the blocker is tracked; specific: `**Blocked on:**` markdown, GitHub blocked-by)
- Current text (verbatim, with path:line): "- **R-BLOCK-3:** If the issue has reached the blocking stage, add a `**Blocked on:** <description>` marker near the top of the body. Status stays at that stage until the blocker clears." / "- **R-BLOCK-4:** If the blocker is itself a GitHub issue, ALWAYS use GitHub's blocked-by / blocking relationships *in addition to* the body marker." (`skills/triage-issues/SKILL.md:153-154`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C21: Blocked Issues get their own report group and are re-checked each pass
- Category: triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-BLOCK-5:** Blocked issues are surfaced in a dedicated \"Blocked\" group in the triage report (see Output section) so they don't dilute \"needs attention\" signals. Each pass reviews the group to check if any blockers have resolved." (`skills/triage-issues/SKILL.md:155`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C22: ADR cue: three-part rubric, offered sparingly, never autonomous
- Category: docs-linkage / agent-vs-human
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-ADR-1:** Whenever a state captures a decision (scope, UX, eng design, direction), the agent evaluates the decision against this rubric (offer ADRs sparingly). All three must hold:" / "1. **Hard to reverse** — meaningful cost to change later" / "2. **Surprising without context** — a future reader will wonder \"why this way?\"" / "3. **Result of a real trade-off** — genuine alternatives existed; one was picked for specific reasons" (`skills/triage-issues/SKILL.md:159-162`); "- **R-ADR-2:** Never autonomous. The agent proposes; the human decides whether to create the ADR and drafts it (or asks the agent to) in the repo's ADR format." (`:166`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown, likely ratified upstream; evidence: the same three-part gate is the `use-adrs` skill's gate ("the three-part gate for what deserves one (several real options, costly to reverse, surprising without context)", per its description).

### C23: Bidirectional entry verification: every state checks readiness both ways; moves are proposals
- Category: triage / lifecycle / agent-vs-human
- Generic or specific: generic
- Current text (verbatim, with path:line): "**Bidirectional entry verification:** every state's playbook begins with an entry-verification block that checks whether the issue's *actual readiness* matches its current state. Two directions:" / "- *Downward* — if the issue is less prepared than its current state implies, propose **regression** to the appropriate earlier state." / "- *Upward* — if the issue already meets this state's exit criteria, propose **promotion** to the next state (or further, if multiple states' exit criteria are satisfied)." / "All entry-verification moves are *proposals*, not autonomous mutations. R-SYNC-1/2 remain the autonomous exceptions (terminal-status mismatches)." (`skills/triage-issues/SKILL.md:170-174`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C24: Minimum body substance at screening: problem/goal plus at least one pointer
- Category: filing / triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-SCREEN-2:** Verify body has minimum substance: problem/goal + at least one pointer (code location, repro, observable behavior). Flag if failing; do not auto-edit." (`skills/triage-issues/SKILL.md:186`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C25: Titles: tolerant; flag only actively useless ones
- Category: filing / triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-SCREEN-3:** Verify title is at least minimally descriptive. Flag only actively-useless titles (\"Bug\", \"TODO\", \"fix this\"). Tolerant otherwise." (`skills/triage-issues/SKILL.md:187`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C26: Priority at screening is an educated guess that schedules scoping; it is refined at scoping
- Category: labels-priority
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-SCREEN-4:** Verify Priority is set. Flag if missing. Priority assigned at this stage is by definition an *educated guess* — it drives the scheduling of scoping work, not the final priority of the issue. Real refinement happens at `Needs Scope` exit (S-WORK-6)." (`skills/triage-issues/SKILL.md:188`); "- **S-WORK-6:** Re-confirm Priority. Scoping is the moment of precision — `Needs Triage` only assigns an educated guess. If priority needs to change, flag for re-prioritization." (`:237`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C27: Size is skipped at screening and must be set by the end of engineering design
- Category: labels-priority
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-SCREEN-5:** Sizing is *skipped* in screening. Assigned no later than exit from `Needs Eng Design`." (`skills/triage-issues/SKILL.md:189`); "- **E-WORK-5:** Set Size before exit. This is the latest state where Size must be assigned." (`:301`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C28: Duplicate detection at screening: flag, never auto-merge
- Category: triage / relationships / agent-vs-human
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-SCREEN-7:** Cursory duplicate detection — fuzzy title/body match against other open issues. Flag candidates; do not auto-merge." (`skills/triage-issues/SKILL.md:191`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C29: Stale-irrelevant detection: look for merged work that resolved an Issue without linkage; flag only
- Category: triage / closing
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-SCREEN-8:** Cursory stale-irrelevant detection — for issues > N days, search for merged PRs that may have addressed them without proper linkage. Flag candidates; do NOT read code to verify; do NOT auto-close." (`skills/triage-issues/SKILL.md:192`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C30: Screening never changes an Issue's definition; even trivial body fixes are not autonomous
- Category: triage / agent-vs-human
- Generic or specific: mixed (generic: screening must not redefine the Issue, definition belongs to scoping; specific-ish: the reason body fixes are not autonomous is the wrapper boundary)
- Current text (verbatim, with path:line): "- **R-SCREEN-9:** Trivial body corrections (typos, grammar, broken/incorrect links) may be *proposed* but are **not autonomous.** Applying them needs a general free-text write to an arbitrary issue — the one capability that would puncture the fail-closed wrapper boundary (R-CAD-5), so v1 exposes no autonomous body-write wrapper. Surface such fixes for a human, or apply them in an interactive pass (where body writes are human-approved in-session). Forbidden at any autonomy level in this state: changing the issue's actual *definition* (belongs to `Needs Scope`)." (`skills/triage-issues/SKILL.md:193`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C31: Screening exits; closing straight out of screening needs a human
- Category: closing / agent-vs-human
- Generic or specific: generic
- Current text (verbatim, with path:line): "- → `Needs Scope` (default if screening passes)" / "- → `Done` (rare; if stale-irrelevant check confirms already-resolved — needs human OK)" / "- → `Rejected` (if incoherent, out of scope, garbage — needs human OK)" (`skills/triage-issues/SKILL.md:196-198`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown; audit row R6 records the reason as "None given." (`docs/audits/2026-10-11-agent-versus-human-line.md:155`)

### C32: Scoping checklist: problem not solution, beneficiary, acceptance criteria, out of scope, constraints, adjacencies
- Category: filing / triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **S-WORK-1:** Identify open scoping questions. Default checklist:" / "- Underlying problem / motivation (not the proposed solution)" / "- Beneficiary and benefit (end user? operator? future maintainer?)" / "- Concrete acceptance criteria / definition of done" / "- What's explicitly out of scope" / "- Constraints (technical, design, narrative) that bound the solution space" / "- Adjacencies: depends on / conflicts with / supersedes other backlog items" (`skills/triage-issues/SKILL.md:211-217`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C33: UX scoping when anything user-observable is affected, at wireframe depth
- Category: triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **Trigger:** does the issue affect anything *user-observable*? ... The profile may extend the trigger with project-specific surface types." / "- **Depth bar:** rough characteristics + wireframe-level layout. *Not* final pixels." (`skills/triage-issues/SKILL.md:220-221`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C34: Decomposition check at scoping; checklist items need tight exit criteria before split evaluation
- Category: breakdown
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **S-WORK-3:** Decomposition check — is this one cohesive scope question or several? Several → split candidate (R-SPLIT-1). If it's a parent initiative → R-PARENT-*." (`skills/triage-issues/SKILL.md:229`); "**Checklist-item exit-criteria precondition (for R-SPLIT-1):** before evaluating bundled-checklist items against R-SPLIT-1, each item must have *tight* exit criteria. Phrasing like \"fix any breakage\", \"update X if needed\", \"smoke test\", \"verify Y works\" hides arbitrary scope and prevents the meatiness heuristic from being evaluated. Tighten such items in place (definition *is* this state's work, per S-WORK-8); do not treat fuzzy items as automatically meaty for splitting purposes." (`:231`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C35: The rejection rubric lives at scoping; later states reject only what screams for it
- Category: closing / triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **S-WORK-4:** Rejection check — does this still align with project direction? Already addressed elsewhere? Cost wildly disproportionate to value? Any yes → surface as rejection candidate. (Rejection rubric is concentrated at this state; downstream states accept `Rejected` as an exit but rely on issues *screaming* for rejection rather than a careful pass.)" (`skills/triage-issues/SKILL.md:233`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C36: The scoped-Issue body template
- Category: filing / docs-linkage
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **S-WORK-8:** Body updates ARE allowed at this stage (explicit contrast to R-SCREEN-9; definition *is* the work here). After scoping, body should contain:" / "- **Problem / motivation** (required)" / "- **Goal** (required)" / "- **Acceptance criteria** (required)" / "- **User experience** (required if UX-bearing; rough characteristics + wireframe-level layout)" / "- **Out of scope** (optional)" / "- **Links** (optional)" / "Profile may extend (but not replace) this minimal template." (`skills/triage-issues/SKILL.md:241-249`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C37: Scoping is interactive by default; questions are surfaced, a design interview is suggested not demanded
- Category: agent-vs-human / triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "**Mode:** scope work is **interactive** by default. The agent surfaces questions in the triage report as \"Open scoping questions for #N\"; the human engages in a follow-up session to resolve. For complex scope or UX decisions, the agent may suggest a dedicated design-interview session — but does not demand it." (`skills/triage-issues/SKILL.md:251`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C38: Scope exit criteria; skipping engineering design is rare and suggestion-only
- Category: lifecycle
- Generic or specific: generic
- Current text (verbatim, with path:line): "**Exit criteria (all required):**" / "- Body contains clear business goal" / "- Body contains acceptance criteria" / "- Body contains UX scope, if UX-bearing" / "- Priority confirmed (possibly updated)" / "- Decomposition resolved (single issue, or split decided)" / "- No active scope-stage blockers" (`skills/triage-issues/SKILL.md:253-259`); "- Implementation appears mechanical (e.g., rename, dependency bump, doc fix, mechanical refactor) AND no engineering decisions are visible from the scoped goal." / "- Agent confidence bar: high. When uncertain, default to `Needs Eng Design`." / "- Surfaced as a \"skip-eng-design candidate\" in the report; the human confirms." (`:263-265`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C39: Don't do later-stage work on top of an earlier stage's gap
- Category: lifecycle / triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "If S-ENTRY-1 fails, surface as a misclassification in the triage report; do not proceed with scope work on top of a partially-screened issue." (`skills/triage-issues/SKILL.md:207`); "If any downward entry check fails, surface for human as a misclassification in the triage report; do not proceed with eng-design work on top of a fuzzy goal." (`:280`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C40: Engineering decisions: agent enumerates, human catches what it misses
- Category: agent-vs-human
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **E-WORK-1:** Identify open engineering decisions and surface them. The agent enumerates from the body + codebase context; the human catches what the agent misses. (Autonomous judgment criteria will be refined as we iterate; for v1, the human-in-loop is the safety net.)" (`skills/triage-issues/SKILL.md:284`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown ("as we iterate" suggests a maintainer-agent collaboration but is not evidence of a ruling)

### C41: Size-of-consequence rubric decides where a decision is explored (Issue body vs design doc)
- Category: docs-linkage
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **0 signals:** record decision in a `## Design decisions` section of the issue body. Discussion lives in comments; the decision itself is body content." / "- **1 signal:** judgment call — agent surfaces the signal, human decides body-vs-doc." / "- **2+ signals:** propose a design doc that stress-tests the trade-offs before deciding." (`skills/triage-issues/SKILL.md:286-288`); signals: "- Hard to reverse if wrong (one-way door)" / "- Crosses >1 subsystem or service" / "- Affects security, data integrity, or external contracts" / "- Decision rests on assumptions that affect things outside the immediate change" / "- Specialist domain knowledge required (crypto, ML, distributed systems, kernel, etc.)" (`:291-295`); "(Note: \"future maintainers would benefit from written rationale\" is *not* a consequence signal — that's an ADR concern, handled separately from design-doc triggering.)" (`:297`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C42: Engineering-design exit: an implementer could execute without further design input
- Category: lifecycle
- Generic or specific: generic
- Current text (verbatim, with path:line): "- All identified design decisions made AND captured (issue body or linked design doc)" / "- Size set" / "- No active blockers at the eng-design stage" / "- An implementer (human or agent) could pick this up and execute without further design input" (`skills/triage-issues/SKILL.md:304-307`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C43: Implementation states track the implementation artifact; "active-work indicator" = open linked PR or assignee
- Category: lifecycle
- Generic or specific: mixed (generic: status after design follows the artifact and the claim; specific: PR, assignee, GraphQL events)
- Current text (verbatim, with path:line): "These states have **entry verification but no work block**. Status here tracks the lifecycle of the *implementation artifact* (linked PR + assignee + recent commits), so entry checks are largely a matter of confirming that the issue's status agrees with that artifact's state. PM-axis still applies." (`skills/triage-issues/SKILL.md:316`); "*Active-work indicator* (v1 definition, shared with PROG-ENTRY-1): an open linked PR (closing or contributing) OR an assignee set. (Raw commit references are deliberately excluded — they surface only as the noise-filtered `ReferencedEvent`.)" (`:329`); "- **PROG-ENTRY-1:** (Downward) Snapshot check: no active-work indicator *right now* (no assignee AND no open linked PR — see I-ENTRY-2). If absent → propose regression to `Needs Impl`. This is a snapshot check; long-running-but-stale-progress is a separate PM-axis concern (staleness)." (`:333`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C44: Closing linkage vs contributing linkage; contributing work never advances past In progress
- Category: docs-linkage / lifecycle
- Generic or specific: mixed (generic: two kinds of work-to-Issue link, only closing work can reach review/done; specific: keyword lists and GitHub's auto-close)
- Current text (verbatim, with path:line): "- *Closing linkage:* `closes`, `fixes`, `resolves` (and variants ...). Surfaced directly by `closedByPullRequestsReferences`. Merge auto-closes the issue." / "- *Contributing linkage:* `furthers`, `contributes to`, `part of`, `towards`, `progresses`, `step toward`, `builds toward`. Merge advances the issue but does not finish it." (`skills/triage-issues/SKILL.md:322-323`); "- **L-LINK-3:** When multiple linked PRs exist, take the most-progressed *closing* PR as the primary signal (merged > open-non-draft > open-draft > closed-unmerged). Contributing PRs always indicate `In progress`; they never qualify for `In review`." (`:324`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown; the same closing/contributing split is in use-github ("For work that advances an issue without finishing it, use contributing language instead — `furthers #42`, `part of #42`, `towards #42`", `skills/use-github/SKILL.md:261-263`)

### C45: The PM axis never auto-acts; findings are batched for a human
- Category: agent-vs-human / triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "Triage **never auto-acts** on PM-axis findings. It surfaces them in a batch report for human decision." (`skills/triage-issues/SKILL.md:343`); and "2. **PM axis** — surface priority/size/staleness hygiene needs without auto-acting." (`:15`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown; audit row R7: "None given." (`docs/audits/2026-10-11-agent-versus-human-line.md:156`)

### C46: Staleness: priority-scaled thresholds over meaningful activity only; untriaged Issues are always reviewed
- Category: triage / labels-priority
- Generic or specific: mixed (generic: staleness = time since meaningful activity vs a priority-scaled threshold, bots and automation are not activity, Needs Triage has no threshold; specific: the GraphQL event allowlist)
- Current text (verbatim, with path:line): "**Computation:** at triage time, compute `staleness = now - mostRecentMeaningfulActivity`, and flag if `staleness > threshold(priority) × multiplier`." (`skills/triage-issues/SKILL.md:347`); thresholds "| P0 | 1d |", "| P1 | 7d |", "| P2 | 14d |", "| P3 | 28d |" (`:410-413`); "Exception: `Needs Triage` has no threshold — every triage pass reviews every `Needs Triage` issue regardless of age." (`:415`); "- Comments/edits authored by an excluded **bot account** (profile bot whitelist can reclassify a specific bot as meaningful)." (`:397`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C47: Size x Status x Time smells
- Category: triage / breakdown
- Generic or specific: generic
- Current text (verbatim, with path:line): "- XS/S sitting >threshold in `Needs Impl` → prompt: \"not really XS, or not really a priority?\"" / "- L/XL with no children → smells like missing decomposition" / "- Size unset at `Needs Impl` → flag (should have been set by exit from `Needs Eng Design`)" (`skills/triage-issues/SKILL.md:422-424`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C48: Priority exists to answer "what do I work on next?"; flag P0 overflow and bucket collapse
- Category: labels-priority
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **Priority-distribution sanity:** priority exists to answer \"what do I work on next?\" The distribution is pathological when the field has *lost discriminating power*, in two modes." (`skills/triage-issues/SKILL.md:425`); "- **P-DIST-1 — Tail overflow (absolute):** open P0 count > cap → flag. The cap does **not** scale with backlog size — \"P0\" means *drop everything*, which is bounded by human attention, not backlog volume. N open P0s means you provably cannot be dropping everything for all N, so the marker is lying. Default cap: **3** (flag at >3 open P0s); profile-tunable. Message: re-rank the weakest P0s down." (`:426`); "- **P-DIST-2 — Collapse (proportional):** a single priority bucket holds **≥ 80%** of *prioritized* open issues → flag \"priority isn't discriminating; re-rank to create signal.\" ... Guard: evaluate only when there are **≥ 10 prioritized open issues** ..." (`:427`); "- *Deferred:* a P1 WIP-style soft bound. P1 lacks P0's hard attention bound, so v1 omits it rather than invent a shaky threshold." (`:429`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C49: Inventory from the place status lives, so closed-but-nonterminal Issues are caught; reconcile against open Issues
- Category: triage
- Generic or specific: mixed (generic: inventory must include closed Issues in non-terminal states and open Issues missing a status; specific: ProjectV2 board)
- Current text (verbatim, with path:line): "The **ProjectV2 board is the inventory anchor**, not the repo's issue list. Reasons: the board is where Status lives (so R-SYNC needs it on both sides); it yields the **project item ID** (`PVTI_…`) required for every field mutation; and iterating items catches *closed* issues still in a non-terminal status (R-SYNC-2), which an open-issues-only scan would miss." (`skills/triage-issues/SKILL.md:437`); "Any open issue **not** on the board has no Status at all → surface as \"not on board\" (add + triage)." (`:475`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C50: The autonomy boundary: only status sync, schema label fixes, and the last-triaged stamp are written without asking
- Category: agent-vs-human
- Generic or specific: generic (the boundary); the field names are GitHub-board specific
- Current text (verbatim, with path:line): "**Autonomy boundary:** only R-SYNC status corrections, R-LABEL schema fixes, and `Last Triaged` bumps are written without asking (all bounded/enumerable field writes). Everything else — priority/size/status *transitions*, scoping/typo body rewrites (R-SCREEN-9 included), closes, reparenting — is **proposed** in the report and awaits human confirmation. There is deliberately no autonomous body-write path (R-CAD-5). Write `Last Triaged` **last** in a pass so the skip-optimization comparison stays clean (it generates no timeline event)." (`skills/triage-issues/SKILL.md:505`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown; audit row R8 gives the reason "All bounded, enumerable field writes." and classifies the principle as "Bounded autonomy" (`docs/audits/2026-10-11-agent-versus-human-line.md:157`)

### C51: Pass shape: inventory, per-issue loop, cross-issue pass, batch by decision type, then apply
- Category: triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "3. **Cross-issue pass:** with the full inventory in hand, run the checks that span issues rather than living inside one: grouping-candidate detection (R-GROUP-1) and duplicate detection (R-SCREEN-7). These cannot be evaluated in the per-issue loop because they compare issues against each other." / "4. **Batch surfacing:** group flags by decision type (re-prioritize / re-size / investigate-stale / commit-to-doing / reject / split / group / etc.). Present to human in batches, not per-issue." / "5. **Mutations:** apply approved actions. Update `Last Triaged` on every issue touched." (`skills/triage-issues/SKILL.md:517-519`); per-issue: "- Record per-issue action: mutate-now, flag-for-batch, or skip (already up-to-date)" (`:516`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C52: Skip unchanged Issues; re-evaluate only staleness
- Category: triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "If `Last Triaged > <most recent non-triage activity>`, the issue hasn't changed since last triage. Skip detailed checklist; only re-evaluate staleness." (`skills/triage-issues/SKILL.md:523`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C53: Report unit is the finding, not the Issue; fold identical findings, never summarize away divergence; omit empty groups but say they were checked
- Category: triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "The report's atomic unit is a **finding** — a `(group, finding, action)` tuple — **not** an issue. One issue may appear in several groups (a different finding in each); several issues may collapse into one finding (same finding + action across all of them)." (`skills/triage-issues/SKILL.md:548`); "- **R-RPT-3 — Divergence pulls out, never summarized-away.** A member that shares the group but differs in finding or action is **not** folded — it renders as its own full R-RPT-1 entry in the same group. No \"…except #N\" tails, no footnotes: every divergent outcome gets its own visible entry." (`:571`); "- **R-RPT-5 — Empty groups omitted.** A group with no findings is dropped entirely (no empty header). The report ends with a one-line \"clean:\" summary naming the standard groups that came back empty, so a reader knows they were checked, not skipped." (`:583`); "`action:` names the autonomy: auto-applied findings state what was done (past tense); proposed findings state what awaits confirmation, plus the one command/step to apply it where non-obvious." (`:559`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C54: Two run modes, one ledger; an unattended pass accumulates proposals but never resolves them
- Category: agent-vs-human / triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-CAD-1 — Two modes, one ledger.** *Interactive*: a human is present; the agent may conduct scope / eng-design dialogue (S-WORK / E-WORK) and apply proposed mutations the human approves in-session. *Unattended*: headless; no dialogue is possible. ... The only difference: an unattended run can *accumulate* proposals but never *resolve* the with-human ones." (`skills/triage-issues/SKILL.md:593`); "- **R-CAD-2 — Unattended scope.** ... It never conducts interactive work and never applies a with-human proposal. Everything needing a human surfaces as a pending ledger finding." (`:594`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C55: A permission denial is terminal for the pass; never route around it
- Category: agent-vs-human
- Generic or specific: mixed (generic: a refusal is recorded as pending and never worked around; specific: `--permission-mode dontAsk`)
- Current text (verbatim, with path:line): "On denial the agent records the intended action as a pending finding and moves on; it must **not** seek an alternate path to the same mutation. (Fail-safe: the dangerous direction stalls, the safe direction flows.)" (`skills/triage-issues/SKILL.md:595`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown; the audit names this "Rule is the gate" and finds the same stance in use-git and use-forgejo (`docs/audits/2026-10-11-agent-versus-human-line.md:51`)

### C56: The triage ledger: one durable skill-owned Issue; body = state, comments = events; excluded from triage
- Category: triage / docs-linkage
- Generic or specific: generic (a durable report artifact with state body and event log); the GitHub-issue carrier is specific
- Current text (verbatim, with path:line): "- **R-LEDG-1 — A durable, skill-owned GitHub issue.** The report is not regenerated into chat each pass; it is a single GitHub issue (the \"triage ledger\") whose number is bound in the profile (required). The skill *owns* this issue: it is the one issue triage writes to autonomously every pass, and it is **excluded from triage as a subject** — never itself triaged, sized, or prioritized." / "- **R-LEDG-2 — Body = state, comments = events.** The issue **body** holds the *current* set of open findings in the R-RPT format (groups, folding, ordering); each pass **rewrites the body** to reflect current state. The issue **comments** hold a per-pass **changelog** ... Body answers \"what needs my attention right now\"; comments answer \"what changed since I last looked.\"" (`skills/triage-issues/SKILL.md:601-602`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged (two later commits only added a use-privacy line above it)
- Provenance: unknown

### C57: Finding identity and carry-forward: the ledger is the memory the skip-optimization discards
- Category: triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-LEDG-3 — Finding identity.** A finding's stable identity across passes is `(rule-id, issue-number, action-key)` — independent of R-RPT-2 display folding ..." (`skills/triage-issues/SKILL.md:603`); "- **Carried-forward / pending** (issue unchanged, so the skip-optimization never recomputed it) → **keep the prior finding verbatim.** This is the crux: the skip-optimization means an unchanged issue is *not* re-examined, so without the ledger its pending proposal would silently vanish (the failure this whole design exists to fix). The ledger *is* the memory the skip-optimization discards." (`:607`); "- **R-CAD-4 — A pass computes a delta; the ledger presents a census.**" (`:613`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C58: Aging is informational; dismissal suppresses a finding until the Issue materially changes (provisional)
- Category: triage / agent-vs-human
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-LEDG-5 — Aging.** A carried-forward finding records `pending since <date> (<N> passes)`. Aging is informational — it makes chronic un-acted proposals visible — and does not auto-retire or auto-escalate in v1." / "- **R-LEDG-6 — Dismissal (minimal; PROVISIONAL).** A human declines a proposal by moving it into a `## Dismissed` section of the ledger body. A dismissed finding is suppressed (not re-added) until the underlying issue *materially* changes, operationalized as: the issue's `lastEditedAt` advances past the dismissal timestamp. ... **Most likely part of this design to need iteration** — flagged provisional; revisit once real dismissals accumulate." (`skills/triage-issues/SKILL.md:608-609`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C59: Autonomous write paths emit only bounded values or free text confined to one owned target; wrappers encode policy
- Category: agent-vs-human
- Generic or specific: mixed (generic: the invariant; specific: the six wrappers and allowlist)
- Current text (verbatim, with path:line): "- **Wrappers encode *policy*, not just *mechanism*.** An autonomous write wrapper is not a thin `gh` shim: it re-derives its own precondition and emits only the sanctioned result, so an allowlisted invocation cannot be coerced into a *proposed* mutation even with hostile arguments. ... **Invariant: every autonomous wrapper emits only a bounded/enumerable value (an option id, a schema label, a date) or free text confined to the one ledger issue — none can write free text to an arbitrary issue.** This is what lets \"permission boundary == autonomy boundary\" hold at the argument level, not just the command level." (`skills/triage-issues/SKILL.md:622`); "The autonomy boundary and the permission boundary are thereby *the same line*, enforced by both policy and the OS-level permission check." (`:620`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C60: Standing up triage (the ledger, the profile) is interactive and human-confirmed
- Category: setup / agent-vs-human
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **R-CAD-6 — Standing up triage in a new repo is an interactive bootstrap, never autonomous.** Once per project: (1) create the ledger issue (`gh issue create`), (2) write its number into the profile `TRIAGE.md`, (3) optionally pin it. Creating a durable artifact and editing a committed repo file are outside the autonomous set; a human confirms. Steady-state (including every unattended run) only ever *reads* the pointer and *edits* the existing ledger." (`skills/triage-issues/SKILL.md:628`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown; the audit groups it under a "Setup" principle shared with use-bd onboarding and tooling-install (`docs/audits/2026-10-11-agent-versus-human-line.md:47`)

### C61: Policy lives in the skill; per-project values live in a profile at the repo root
- Category: setup
- Generic or specific: mixed (generic: universal policy plus a per-repo binding; specific: `TRIAGE.md`, the JSON config block)
- Current text (verbatim, with path:line): "Universal triage skill. Policy lives here; each project binds it via a `TRIAGE.md` profile at its repo root." (`skills/triage-issues/SKILL.md:8`); "The opaque IDs + schema + tuning live in a fenced, marker-delimited JSON config block ... that block is the machine-readable source of truth the wrappers parse ...; surrounding prose is for humans only." (`:30`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown

### C62: Interactive single-Issue work belongs to the day-to-day skill; triage owns batch passes and transitions
- Category: triage / agent-vs-human
- Generic or specific: generic (the division of labor); the skill names are specific
- Current text (verbatim, with path:line): "For interactive, single-issue GitHub work (filing, labeling, commenting, PRs), the `use-github` skill is the canonical GitHub-I/O layer — this skill's `triage-*` wrappers exist solely as the autonomous write path for triage passes." (`skills/triage-issues/SKILL.md:8`); from the docs: "`use-github` keeps Status writes conservative: `Needs Triage` on filing, and only on a conforming board; transitions belong to triage." (`docs/projects/ghw/design.md:164-166`); and use-github: "Be liberal with Priority; be conservative with Status. New issues start at `Needs Triage` ... Status *transitions* belong to the `triage-issues` skill; don't invent them here." (`skills/use-github/SKILL.md:190-195`)
- Earliest form: cb6f1eb, 2026-09-22 (both skill passages); the ghw design wording from ff3c33c, 2026-10-01 "docs: migrate the ghw project docs"; unchanged
- Provenance: unknown; audit row H7 classifies it as "Ratify" (`docs/audits/2026-10-11-agent-versus-human-line.md:95`)

### C63: File-based TODO lists are out of scope for Issue triage
- Category: todo-comments / triage
- Generic or specific: generic
- Current text (verbatim, with path:line): "This skill operates on GitHub Issues + Projects only. TODO lists kept in files (a `TODO.md`, TODO sections in docs) are out of scope; a separate backlog-grooming pass, if you have one, handles them. Complementary, not overlapping." (`skills/triage-issues/SKILL.md:26`)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown (the `groom-backlog` skill is the complement)

### C64: Triage-owned body structures are load-bearing; body rewrites must preserve them
- Category: docs-linkage / filing
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **Triage-owned body structures are load-bearing:** the scoped-issue template (Problem / Goal / Acceptance criteria / User experience / Out of scope / Links), `## Design decisions` sections, the `**Blocked on:**` marker, and the parent tracker's `- [ ] All children created (scope locked)` checkbox. The Verbs do not parse them; the Skill texts warn `set-body` callers not to stomp them." (`docs/projects/ghw/design.md:304-309`)
- Earliest form: ff3c33c, 2026-10-01, "docs: migrate the ghw project docs" (migrated from the predecessor repo); unchanged
- Provenance: unknown

### C65: Labels encode the triage schema; changing an initialized repo's labels needs a human
- Category: labels-priority / agent-vs-human / setup
- Generic or specific: generic
- Current text (verbatim, with path:line): "- **Labels encode the project's triage schema; they are not fungible data.** Issues and PRs come and go, but a label changing name or meaning can break process repo-wide. An edit implies a schema version change or a conflicting schema to reconcile, and both want a human. The automated use case is first-time creation while initializing a repo; any other change to an initialized repo's labels is the signal to stop and ask." (`docs/projects/fjw/issue-verbs.md:43-48`)
- Earliest form: edd9853, 2026-10-01, "docs: migrate the fjw and installer project docs; add ADR 0007"; unchanged
- Provenance: ratified; evidence: the doc is "the issue-verbs proposal ratified 2026-09-14" (commit edd9853 message), and the doc is dated 2026-09-14.

### C66: Classifying your own new Issue is part of filing; changing the surface in place is triage; mislabels are what triage is for
- Category: filing / triage / agent-vs-human
- Generic or specific: generic
- Current text (verbatim, with path:line): "Contributor covers participation: filing, commenting, closing with a comment. Triage changes the surface in place: retitling, rewriting bodies, reopening, labeling, and relinking." (`docs/projects/fjw/issue-verbs.md:166-168`); "This is accepted on principle: classifying your own new issue is part of filing it, triage governs changing the surface in place, and mislabeled filings are what triage is for." (`:174-176`)
- Earliest form: edd9853, 2026-10-01; unchanged
- Provenance: ratified (same ratified 2026-09-14 proposal as C65)

### C67: Exit requirements are checked when an Issue leaves a state, so capture is never blocked (maintainer sketch)
- Category: lifecycle / filing
- Generic or specific: generic
- Current text (verbatim, with path:line): from Beads `agent-tooling-c86` description: "A status lifecycle for Issues on Beads in which each state has exit requirements, checked when an Issue moves on, rather than requirements checked at creation. Sketch from the maintainer (2026-10-09, use-bd home-in, agent-tooling-aio), not ratified:" / "• New Issues land in a starting state such as needs_triage with whatever the filer knows, so capture during flow is never blocked (a bug whose repro is unknown still gets filed, and says so honestly rather than with placeholder text)." / "• To leave needs_triage: a reasonable title and description, a priority, labels conforming to the project's scheme, and for a bug, steps to reproduce. It then moves to needs_scope, in the manner of the triage-issues skill's state model." / "• To leave needs_scope: success criteria (Branch Issues) or acceptance criteria (Leaf Issues). And so on through the lifecycle." (`bdw show agent-tooling-c86`)
- Earliest form: the Issue itself, created 2026-10-10 by claude-job-521331be; not in git
- Provenance: maintainer-raised, explicitly "not ratified"; evidence: the Issue text attributes it to the maintainer in the use-bd home-in.

### C68: Filing-time relationship checks are best effort; a batch triage pass catches what they miss (maintainer)
- Category: triage / relationships
- Generic or specific: generic
- Current text (verbatim, with path:line): from Beads `agent-tooling-r6b`: "Automated triage of the Issue Tracker as an offline, batch process: periodically reconcile what filing-time checks miss or get wrong, across the whole tracker, rather than one Issue at a time." / "Filing-time checks are best effort: an agent sees only part of the tracker, and wrong or missing relationships, implicit shared parents, stale Issues, and anomalies (for example a Branch Issue that is not of a branch kind) accumulate. A batch pass is where those get caught. Raised by the maintainer on 2026-10-08 during the use-bd home-in (agent-tooling-aio) as orthogonal to use-bd version one." (`bdw show agent-tooling-r6b`); echoed in `docs/projects/use-bd/v1-proposal.md:84` ("**Out of scope:** batch triage and reconciliation") and `:243-244` ("Batch reconciliation is separate work (`agent-tooling-r6b`, automated batch triage).")
- Earliest form: the Issue, created 2026-10-09; the v1-proposal wording from b08ba40, 2026-10-09, "use-bd: the design becomes a dated version-one proposal"
- Provenance: maintainer-raised (not ratified as design); evidence: the Issue text.

### C69: Triage should become fully tool-agnostic, built on the generic Issue skills (maintainer sketch)
- Category: other (skill architecture)
- Generic or specific: generic
- Current text (verbatim, with path:line): from Beads `agent-tooling-u9n`: "• triage-issues: fully tool-agnostic, relying on the skills above." and "• use-issues: generic guidance for thinking about Issues and project management; use-bd and use-github-issues add the tool specifics and quirks." "Sketch raised by the maintainer on 2026-10-07 (not ratified, a starting point to scope)" (`bdw show agent-tooling-u9n`)
- Earliest form: the Issue, created 2026-10-08
- Provenance: maintainer-raised, explicitly "not ratified"; a 2026-10-26 maintainer ruling in its notes makes it the progressive-disclosure pilot.

---

## Platform-specific mechanics (not traced)

- Profile `TRIAGE.md` with a `<!-- BEGIN triage-config -->` JSON block; required fields: repo, project number/node ID, Status/Priority/Size/Last Triaged field and option IDs, ledger issue number, label schema, staleness multiplier (`SKILL.md:30-46`; parser `reference/lib_profile.py`).
- `Size` "not used" exists only to grandfather old boards; `ghw-board-sync` provisions it on new boards and reports, never creates, a missing `Size` (`SKILL.md:35`; `docs/projects/ghw/design.md:211-213`).
- Board inventory via paginated ProjectV2 GraphQL `fieldValueByName`; skip non-Issue items; null field = unset (`SKILL.md:439-471`).
- Board vs open-issues reconciliation via `gh issue list --state open --limit 500` (`SKILL.md:475`).
- Staleness timeline query with a server-side `itemTypes` allowlist; `lastEditedAt` covers body/title edits; drop `wasAutomated` status changes and other projects' events (`SKILL.md:351-404`).
- Known v1 limitation: Priority/Size changes emit no timeline event and are invisible to staleness (`SKILL.md:401`).
- Known v1 limitation: triage runs under the operator's own GitHub account, so its own writes count as activity (`SKILL.md:402`).
- Linked closing PRs via `closedByPullRequestsReferences(includeClosedPrs:true, userLinkedOnly:false)`; contributing PRs only best-effort (`SKILL.md:481-489`).
- Raw `gh` mutation table (item-edit, issue edit/close/reopen, `sub_issues` REST with database ID) (`SKILL.md:495-503`).
- Blocked-by write path deferred in v1; set manually (`SKILL.md:507`, `:653`).
- Six wrappers: `triage-inventory`, `triage-timeline` (read); `triage-apply-sync` (policy-bound), `triage-fix-label` (schema-bound), `triage-bump-triaged` (value-bound), `triage-update-ledger` (target-bound); all writes take `--dry-run` (`reference/README.md:15-24`).
- Wrappers invoked as `python3 <installed path>`, allowlisted at user level in that exact form; never `Bash(gh *)` (`reference/DEPLOYMENT.md:57-76`).
- Unattended runs: `--permission-mode dontAsk`, never `bypassPermissions` (`reference/DEPLOYMENT.md:89-99`).
- Do not host unattended triage in a repo whose project or local settings grant `ghw-*` write Verbs (`SKILL.md:632`; `DEPLOYMENT.md:101-106`; Known gap agent-tooling-ys3).
- Launch form: guard script (marker, atomic lock, reaping) dispatching `claude --bg ... --worktree ... --permission-mode dontAsk --allowedTools "Edit(...)" < /dev/null`; the run writes its own success marker; stale-ledger tripwire (`SKILL.md:636`; `DEPLOYMENT.md:121-161`).
- Ruled out: `claude -p` (billed as API), Desktop Local and Cloud routines, in-session schedulers (`SKILL.md:636-638`; `DEPLOYMENT.md:163-175`).
- Billing: subscription auth, no `ANTHROPIC_API_KEY`, usage credits disabled, cost-efficient model for unattended (`SKILL.md:634`; `DEPLOYMENT.md:179-191`).
- Load `use-privacy` before composing an issue body, comment, or ledger body (`SKILL.md:493`, `:599`).
- `TRIAGE.md` discovery walks up to the git work-tree root only (`docs/projects/ghw/design.md:235-238`).

---

## Contradictions

1. **Who may close or mark duplicates: triage forbids it, use-bd allows it.**
   - Triage: "Flag candidates; do not auto-merge." (`skills/triage-issues/SKILL.md:191`); "Everything else — priority/size/status *transitions*, scoping/typo body rewrites (R-SCREEN-9 included), closes, reparenting — is **proposed** in the report and awaits human confirmation." (`:505`)
   - use-bd: "| duplication | `bdw duplicate <id> --of=<canonical>` (closes it) | only when very confident |" (`skills/use-bd/SKILL.md:154`)
   - The 2026-10-11 audit already raises this ("Is closing an Issue or a PR an agent act?", `docs/audits/2026-10-11-agent-versus-human-line.md:240-262`), with the auditor's lean that triage's restriction is "an unexplained exception".

2. **Who may reparent (composition): triage says a human, use-bd lets an agent.**
   - Triage: "reparenting, tracker creation, and especially issue-closing await human confirmation." (`SKILL.md:132`)
   - use-bd: "| composition | `--parent=<id>` at filing | only when very confident |" (`skills/use-bd/SKILL.md:155`). These may not truly conflict (filing time vs triage time), but no text says so.

3. **Where an Issue's kind lives: one type label vs the type field.**
   - Triage: "Every issue must have **exactly one** label from the profile's *type* family" (`SKILL.md:88`)
   - use-bd: "**Kind goes in the type field** (`--type=task|bug|feature|chore|epic|...`, `bdw types` lists them), never in a label." (`skills/use-bd/SKILL.md:139-140`)
   - The generic principle (exactly one kind per Issue) agrees; the carrier differs per tracker. A generic skill has to say "kind" without saying "label".

4. **Which Issues may have children.**
   - Triage: "**Parent-child decomposition:** original becomes parent" (`SKILL.md:109`): any Issue can become a parent.
   - use-bd: "Only an epic takes children. When a task proves bigger than a session, retype it first (`bdw update <id> --type=epic`) and break it down" (`skills/use-bd/SKILL.md:126-127`).

5. **Size vocabulary vs session-sized Leaf Issues.** Triage sizes with XS to XL and uses thresholds like "would be sized M+" (`SKILL.md:102`) and "aggregate size is ≤ M" (`:126`); use-bd sizes by "**One Issue, one session's work.** Anything bigger is an epic" (`skills/use-bd/SKILL.md:138`). Not contradictory in intent, but the two sizing models do not map onto each other anywhere.

6. **Leaving screening: triage's criteria vs the maintainer's Beads sketch.**
   - Triage requires "problem/goal + at least one pointer (code location, repro, observable behavior)" (`SKILL.md:186`) and skips sizing (`:189`).
   - The maintainer's sketch requires "a reasonable title and description, a priority, labels conforming to the project's scheme, and for a bug, steps to reproduce" (agent-tooling-c86). Steps to reproduce for every bug is stricter than "at least one pointer".
   - Leaving scoping: triage requires goal + acceptance criteria + UX scope (`SKILL.md:253-259`); the sketch requires "success criteria (Branch Issues) or acceptance criteria (Leaf Issues)" (agent-tooling-c86), a distinction triage does not make.
   - Also a timing tension: the sketch's "requirements checked when an Issue moves on, rather than requirements checked at creation" vs use-github's "Set both [Priority and Status] as part of filing, not later." (`skills/use-github/SKILL.md:165`). Setting priority at filing is not forbidden by the sketch, but the sketch makes it an exit requirement, not a filing one.

7. **R-SYNC-1's "surface for human if ambiguous" has no path in the code.** SKILL says "Default: demote to `Needs Scope`; surface for human if ambiguous." (`SKILL.md:83`), but the wrapper always demotes: "if state == \"OPEN\" and status_name in TERMINAL: return \"Needs Scope\"" (`reference/triage-apply-sync:62-63`). Nothing ever counts as ambiguous.

8. **Absorbed Issues must be closed with a comment, but the documented close path posts none.** "close the absorbed issues as *not planned* with a mandatory `Absorbed into #X` comment and back-link" (`SKILL.md:128`) vs the mutation table's "`gh issue close <NUM> --reason completed` / `gh issue close <NUM> --reason \"not planned\"`" (`:501`). Already a Known gap: "The triage Skill still closes approved issues with raw `gh issue close`, which posts no comment (`agent-tooling-0fm`)." (`docs/projects/ghw/index.md:44-45`). It also conflicts with ghw's rule that "a silent close is inexpressible through this Verb" (`docs/projects/ghw/design.md:145-148`).

9. **R-BLOCK-4 "ALWAYS" vs the deferred write path, and the stale deferral.** "ALWAYS use GitHub's blocked-by / blocking relationships *in addition to* the body marker." (`SKILL.md:154`) vs "**Deferred:** writing GitHub blocked-by / blocking relationships (R-BLOCK-4) — the mutation path is newer and unverified; v1 relies on the `**Blocked on:**` body marker (R-BLOCK-3) as primary, and sets the GitHub relationship manually when needed." (`:507`). Since then `ghw-issue-link ... add-blocked-by` has shipped ("Issue relationships: sub-issues and blocked-by | shipped | `ghw-issue-link`", `docs/projects/ghw/index.md:30`), so the deferral text is out of date.

10. **Commit references in or out of the active-work signal.** "Status here tracks the lifecycle of the *implementation artifact* (linked PR + assignee + recent commits)" (`SKILL.md:316`) and Open/TODO "\"Recent commits referencing this issue\" — concrete time window for I-ENTRY-2 / PROG-ENTRY-1 (e.g., last 7 days?)" (`:648`) vs "(Raw commit references are deliberately excluded — they surface only as the noise-filtered `ReferencedEvent`.)" (`:329`).

11. **The state table vs the playbooks.** The table lists `Needs Impl`, `In progress`, `In review` as "(PM-axis only)" (`SKILL.md:57-59`), but each has entry-verification rules (I-ENTRY, PROG-ENTRY, REV-ENTRY, `:326-339`). Minor: the table understates what triage does there.

12. **Screening-to-Done needs a human, but R-SYNC-2 is autonomous.** "→ `Done` (rare; ... needs human OK)" (`SKILL.md:197`) vs R-SYNC-2's autonomous set-to-`Done` for any closed Issue (`:84`). Consistent once you read "the Issue is already closed" as a human having acted, but the text never says so.

13. **R-SCREEN-8 threshold undefined.** "for issues > N days" (`SKILL.md:192`); N is never defined in the skill or the profile field list (`:30-46`).

14. **"Triage" means two things.** In fjw it is a permission tier that includes "rewriting bodies" as an allowed act (`docs/projects/fjw/issue-verbs.md:162,167-168`); in triage-issues, body rewrites at screening are "**not autonomous**" (`SKILL.md:193`) and body rewriting is reserved to scoping. They don't conflict on paper (tier = which Verbs can be granted; skill = when to use them), but the shared word invites drift.

15. **Repo-level mismatch worth knowing.** This repo's own `CLAUDE.md` says GitHub Issues "takes no work" and Beads is the only Issue Tracker, while triage-issues "operates on GitHub Issues + Projects only" (`SKILL.md:26`). So the one detailed triage policy in the repo targets a tracker this repo has stopped using; agent-tooling-r6b and agent-tooling-u9n are the open threads for porting it.

---

## Judgement calls

- **Provenance "unknown" for nearly everything.** The skill's history starts at the 2026-09-22 import from a private predecessor repo, so I could not tell which rules the maintainer wrote or ruled on and which an agent added. I did not label rules "agent-elaborated" just because of their style (rule-ID density, lettered sub-gates), since the predecessor history might show maintainer authorship. Where the 2026-10-11 audit records a restriction's reason as "None given", I cited that as a weakness, not as authorship.
- **Beads Issues included as sources.** agent-tooling-c86, agent-tooling-r6b, and agent-tooling-u9n are not under `docs/projects/`, but they are the only maintainer-attributed statements about triage intent I found, and the brief allows `bdw show`. I listed them as C67-C69 with their "not ratified" status quoted.
- **use-github, use-bd, and the audit used only for contradictions.** Other readers presumably cover use-github and use-bd. I extracted their principles only where they meet triage's (C44, C62), and otherwise quoted them only in Contradictions.
- **Merged closely related rules** (for example R-BLOCK-3 with R-BLOCK-4, R-LEDG-1 with R-LEDG-2, R-SCREEN-5 with E-WORK-5) into one entry each to keep the count meaningful. Every quoted sentence is verbatim; ellipses mark omitted text inside a quote.
- **Deployment, billing, and GraphQL details** went into Platform-specific mechanics without tracing, per the brief. The one deployment change in history (5ec1a8c, 2026-10-11, which retired the Desktop Local routine and `claude -p`) is tool mechanics, so I noted it but did not treat it as an Issue principle.
- **Didn't read** `triage-inventory`, `triage-timeline`, `triage-bump-triaged`, `triage-update-ledger`, or `lib_gh.py` in full. Their docstrings in README/DEPLOYMENT describe them as mechanism, and the brief limits script reading to policy. I read `triage-apply-sync` (it encodes the R-SYNC policy) and `triage-fix-label` (it encodes the label-schema bound).
