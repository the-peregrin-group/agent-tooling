# Catalog: generic Issue principles, merged from extracts A to G

> This document captures state as of 2026-10-26. For current state, see [docs/index.md](../../index.md).

Built 2026-10-26 from the seven extracts in this directory (A setup-github-issues,
B use-github and ghw docs, C triage-issues, D use-bd and Beads docs, E Forgejo
issue conventions, F Beads Issues carrying the maintainer's sketches and
rulings, G ADRs, LEXICON, CLAUDE.md). Extract IDs (A12, D7, ...) point to entries in
those files. Quotes are copied from the extracts, which quote the repo
verbatim. Repo paths are relative to the repo root.
`bdw show <id>` stands in for a path:line when the text lives only in a Beads Issue.

Provenance tags:
- **ratified**: an ADR, the use-bd home-in output (2026-10-07 to 10-09, including
  docs/projects/use-bd/v1-proposal.md, "PROP"), the fjw issue-verbs proposal ratified
  2026-09-14, the lexicon's ratified state (8201891), or a note recorded as a
  maintainer or user ruling.
- **sketch**: raised by the maintainer and explicitly "not ratified" (c86, u9n, r6b's framing).
- **unknown**: mostly the 2026-09-22 import (cb6f1eb) of setup-github-issues,
  use-github, and triage-issues from a private predecessor; who wrote it is not visible.
- **agent-elaborated**: first appears in agent text with no ruling behind it.

Correction applied: extract G's G29 (the claim/discovered-from/release loop) and G31
("A denied call is the policy working; do not look for another spelling of it")
did not disappear. skills/use-bd/SKILL.md:36 and :74-88 carry both today. They are
merged below as moved, not lost (K44, K14).

---

## Setup and the tracker itself

### K1: The tracker is the one system of record for actionable work
- Category: setup
- Best statement: "**Issue Tracker**: The one system of record (e.g., Beads, GitHub Issues) for this repo's actionable work: each unit of work is an Issue, tracked from filed to done." (LEXICON.md:193-196)
- Also stated in: G1, A1, A26
- Provenance: ratified (lexicon 8201891, ADR 0001). Drift: "one per repo" was softened by ADR 0011 (see K3 and Disconnect 1). A1's "single source of truth ... replaces scattered TODOs" is unknown.

### K2: An Issue is one unit of actionable work, with a status and dependencies
- Category: filing
- Best statement: "**Issue**: One tracked unit of actionable work in the Issue Tracker (e.g., a bug, a feature, a task), with a status and dependencies on other Issues." (LEXICON.md:198-200)
- Also stated in: G2
- Provenance: ratified (8201891).

### K3: Which tracker holds work follows who drives it; one writable home per Issue, no sync
- Category: setup
- Best statement: "Beads kept for work that agents swarm, while long-lived, low-churn, or human-driven work belongs in forge issues (GitHub or Forgejo Issues)" (docs/adr/0011-beads-for-swarmed-work-forge-issues-for-long-lived-work.md:10); "A project with both kinds of work needs Beads and forge issues together, each Issue with one writable home at a time" (ADR 0011:17); "**No sync, in either direction.**" (docs/projects/beads-trial/design.md:16-22)
- Also stated in: D37, D38, F30, F31, G12, G13
- Provenance: ratified (ADR 0001, ADR 0011, maintainer ruling 2026-10-16 on agent-tooling-ze3). F31's "explicit transfer, visible on both sides" is agent-drafted requirements on ze3.

### K4: A copy that is not an Issue's home takes no writes
- Category: agent-vs-human
- Best statement: "No GitHub issue is filed, edited, relabeled, reprioritized, or closed until the long tail moves back to forge issues (`agent-tooling-ze3`)." (CLAUDE.md:50-54)
- Also stated in: G14, F32
- Provenance: ratified (ADR 0011, ruling recorded on agent-tooling-0pe). The text is about this repo; the general rule is the inference.

### K5: Issue data stays private unless deliberately published
- Category: setup
- Best statement: "a private, self-hosted remote keeps unlinted Issue content, with its full Dolt history, from ever being published." (docs/adr/0012-beads-data-syncs-to-private-forgejo-remote.md:12)
- Also stated in: D39, G18
- Provenance: ratified (ADRs 0001, 0012).

### K6: Load the privacy rules before composing any text bound off the machine
- Category: other
- Best statement: "If a `use-privacy` skill is listed among your available skills, load it before composing any text bound for outside this machine: a commit message, a PR or issue body, a comment." (skills/use-github/SKILL.md:53-56)
- Also stated in: A18, B19, E24, C (mechanics, triage-issues SKILL.md:493)
- Provenance: agent-elaborated (agent-tooling-n0p, filed and landed by one job).

### K7: Setting up a tracker is a human procedure; an agent drafts, confirms the target, and waits for approval of the whole plan
- Category: setup / agent-vs-human
- Best statement: "This is a maintainer procedure ... so a human runs or approves each step. An agent may draft the files (`PRIME.md`, the Permission rules) and the change that lands them." (skills/use-bd/onboarding.md:5-9); "**Wait for explicit user approval before proceeding to execution.**" (skills/setup-github-issues/SKILL.md:284)
- Also stated in: D46, A2, A15, C60, F35
- Provenance: ratified in part (PROP:204-206 puts `init` under Ask); A2/A15/C60 unknown.

### K8: Setup is a one-time bootstrap, separate from day-to-day use; triage policy is a further per-repo opt-in
- Category: setup
- Best statement: "`setup-github-issues` is the one-time bootstrap that created the label schema and board this skill assumes." (skills/use-github/SKILL.md:296-297); "What recurring triage still needs is per-repo *policy* configuration, which belongs to the `triage-issues` skill" (skills/setup-github-issues/SKILL.md:501-506)
- Also stated in: B24, A33, C61
- Provenance: unknown ("by convention", docs/projects/ghw/design.md:218-219).

### K9: Setup is safe to re-run
- Category: setup
- Best statement: "Re-runs converge to a no-op, so a re-run of the skill is harmless." (skills/setup-github-issues/SKILL.md:338-339)
- Also stated in: A34, A29 ("**Be idempotent.**")
- Provenance: unknown.

### K10: Policy has one home; the repo's instructions and the tracker's own agent text point to the skill, never copy it
- Category: docs-linkage / setup
- Best statement: "6. **Policy has one home.** Each rule is written once: its procedure in the Skill, its rationale in the project's design doc or an ADR; `CLAUDE.md`, the README, and the trial docs point to the Skill." (PROP:62-66)
- Also stated in: D34, D47, A29, A24, G32
- Provenance: ratified (home-in; EPIC note 2026-09-26 "user-approved" for the PRIME.md pointer). A29 ("Keep it to a pointer") and A24 (meanings live in the skill texts, not tracker help text) are unknown but agree.

### K11: Policy (what agents may run) lives only in reviewed Permission rules; conventions (how this project does things) are per-repo declared data
- Category: setup / agent-vs-human
- Best statement: "**Policy** stays in each repo's reviewed Permission rules, never in a file an agent could edit to loosen its own limits." (PROP:275-276); "Conventions only: it may steer what bdw itself does ... but never touches the Permission rules, which alone decide what an agent may run." (`bdw show agent-tooling-aio.6`)
- Also stated in: D33, F13, F37, E26, B22
- Provenance: ratified (home-in, "One Skill, many repos").

### K12: Capability is granted per operation and per repo; the grant level is the maintainer's choice
- Category: agent-vs-human
- Best statement: "**Granularity is the point.** Comment without merge, label edits without `set-body`, merge into one branch and not another: each is expressed by which rules exist ... There are no side-channel policy files; all policy is visible in settings." (docs/projects/ghw/design.md:385-388); "What grant the machine account holds on a repo is the maintainer's per-repo policy, not an fjw decision (ruling 2026-10-24)" (`bdw show agent-tooling-1vr.1`)
- Also stated in: B22, E11, E14, E15, E19, E26 ("Grant only the verbs the consumer exercises.")
- Provenance: ratified (fjw proposal tiers 2026-09-14; ruling 2026-10-24). B22 wording unknown.

### K13: Enforce simple rules in code agents cannot talk past, with refusals that teach
- Category: other
- Best statement: "**Enforce the simple rule in code.** Where a rule fits in one sentence and agents' habits (industry practice in their training data) pull against it, `bdw` enforces it with a refusal that teaches the right form, rather than the Skill spending paragraphs on judgment." (PROP:29-36)
- Also stated in: D52, G15, C59, E20
- Provenance: ratified (home-in; ADR 0010; ruling 2026-10-24 on agent-tooling-1vr for E20). This is about the tooling, not about agent conduct.

### K14: A denial, refusal, or permission prompt is the policy working: fix the call or report the gap; never route around it
- Category: agent-vs-human
- Best statement: "**A denied call is the policy working.** Do not look for another spelling of it. If the normal path for a real need is denied or prompts, that is a gap: say so" (skills/use-bd/SKILL.md:36-38)
- Also stated in: D1, B17, B18, C55, E18, E23, G31 (moved here, not lost)
- Provenance: ratified (the gap half: PROP:49-54 success criteria 1-2; E18 by ruling). First half dates to 50e29e6 (2026-09-24), unknown author, carried into the ratified design.

### K15: Never reword Issue text to get past a refusal
- Category: filing
- Best statement: "no agent rewords Issue text to dodge a refusal or skips a field because it only takes inline text." (PROP success criterion 2, cited in extract D28)
- Also stated in: D28, X5
- Provenance: ratified. The title exception (skills/use-bd/SKILL.md:189-191) is agent-elaborated.

---

## Filing

### K16: Search open and closed Issues before filing; comment on a near-twin instead of filing one
- Category: filing
- Best statement: "Before filing, agents search for near-duplicates themselves (`search`); the filing Verb's own near-duplicate check is a backstop, and `find-duplicates` sweeps after filing." (PROP:237-240); "Create is not idempotent: search open and closed issues before filing." (docs/projects/fjw/issue-verbs.md:239); "If something close already exists, comment on it instead of filing a near-twin." (skills/use-github/SKILL.md:115-116)
- Also stated in: B1, D15, E7, F36
- Provenance: ratified (home-in; fjw proposal). B1's "Duplicate issues are the main failure mode" is unknown.

### K17: Capture is never blocked: file with what you know, honestly, without placeholder text
- Category: filing
- Best statement: "**No barrier to capture.** Beads' section lint (`bd lint`) is type-dependent and, if enforced at creation, would refuse a bug filed before anyone knows how to reproduce it, inviting placeholder text." (PROP:258-264); "New Issues land in a starting state such as needs_triage with whatever the filer knows, so capture during flow is never blocked (a bug whose repro is unknown still gets filed, and says so honestly rather than with placeholder text)." (`bdw show agent-tooling-c86`)
- Also stated in: D21, F9, C67
- Provenance: ratified (home-in anti-goal); the c86 framing is a sketch.

### K18: No empty Issues
- Category: filing
- Best statement: "**No empty Issues.** `create.require-description` is on, so every Issue says what it is." (PROP:256-257)
- Also stated in: D20
- Provenance: ratified (home-in).

### K19: Title states the outcome; the body says what, why, and what done looks like, readable by someone outside the conversation
- Category: filing
- Best statement: "Write the title as an imperative statement of the outcome (\"Cache label lookups per session\"), not a symptom fragment. The body should say what's wrong or wanted, why it matters, and what \"done\" looks like — enough that someone who isn't in this conversation can pick it up." (skills/use-github/SKILL.md:136-139)
- Also stated in: B4, D19 ("what and why, then a `## Acceptance Criteria` section"), F34 ("issue text is self-contained and publishable-grade"), C24, C25
- Provenance: unknown (B4); D19 agent-elaborated; F34 "ratified in outline" 2026-09-26 (agent-tooling-eta). Several sources agree.

### K20: Screening tolerates weak titles and asks only for minimum substance
- Category: triage / filing
- Best statement: "Verify body has minimum substance: problem/goal + at least one pointer (code location, repro, observable behavior). Flag if failing; do not auto-edit." (skills/triage-issues/SKILL.md:186); "Flag only actively-useless titles (\"Bug\", \"TODO\", \"fix this\"). Tolerant otherwise." (:187)
- Also stated in: C24, C25
- Provenance: unknown. Compare c86's needs_triage exit (K39).

### K21: One Issue, one session's work; anything bigger is a Branch Issue
- Category: filing / breakdown
- Best statement: "**Organizational hygiene.** Work is broken down into Leaf Issues sized for one session, under Branch Issues for anything bigger, and the four relationships ... are looked for when an Issue is filed." (PROP:67-70)
- Also stated in: D16, G5
- Provenance: ratified (home-in success criterion 7; lexicon 92ccc6d).

### K22: File what you find along the way as a new Issue, linked to the Issue whose work surfaced it
- Category: filing / relationships
- Best statement: "File what you find along the way as new Issues linked back: `--deps=discovered-from:<id>`" (skills/use-bd/SKILL.md:81-82); "`discovered-from` records provenance and does not block." (:160-161)
- Also stated in: D2, G29, G30 (moved, not lost)
- Provenance: ratified (PROP:78-80 "file discovered work").

### K23: Classifying your own new Issue is part of filing; changing the surface in place is triage; mislabels are what triage is for
- Category: filing / agent-vs-human
- Best statement: "This is accepted on principle: classifying your own new issue is part of filing it, triage governs changing the surface in place, and mislabeled filings are what triage is for." (docs/projects/fjw/issue-verbs.md:174-176)
- Also stated in: C66, E9
- Provenance: ratified (fjw proposal 2026-09-14).

### K24: A new Issue enters an intake state and is set up at filing, not later
- Category: lifecycle / filing
- Best statement: "**This is the step that gets skipped.** ... unset fields are invisible in the board's grouped views — the issue is filed, on the board, and effectively lost. Set both as part of filing, not later." (skills/use-github/SKILL.md:162-165); "Be liberal with Priority; be conservative with Status. New issues start at `Needs Triage`" (:190-191)
- Also stated in: B5, B7, A20, F9
- Provenance: unknown. The mechanism (board views) is GitHub-specific; c86 agrees on the intake state but makes priority an exit requirement (Disconnect 3).

### K25: Bulk conversion of an existing backlog: audit every hiding place, keep each item's source, one verdict per item, one deduplicated plan the maintainer reviews, one serial filer
- Category: filing / setup
- Best statement: "Every TODO gets one verdict: file (type, title, self-contained body citing in-repo docs, proposed dependencies), already covered by an existing issue (cite it), done in code (clean up upstream), stays upstream, or needs a maintainer ruling." ... "The plan is a full document, not a list of IDs, because a person has to review it." ... "Filer: one subagent files the approved issues serially" (`bdw show agent-tooling-eta`)
- Also stated in: F35, A11, A12, A13, A14, A16, A17 ("dependency order matters so that `#N` cross-references resolve"), A26
- Provenance: ratified in outline (eta, 2026-09-26, "not final"); A-items unknown.

### K26: Requests that should be Issues become Issues through a sanctioned path, not hand transcription
- Category: filing
- Best statement: "**A sanctioned filing path**: a request that today becomes a mailbox Message becomes an Issue directly, with the right Actor attribution and within the Permission rules" (`bdw show agent-tooling-137.2`)
- Also stated in: F40
- Provenance: agent-elaborated content under a ratified placement.

---

## Kind, labels, priority, size

### K27: Every Issue has exactly one kind, recorded once, in the tracker's own mechanism for kind
- Category: labels-priority
- Best statement: "**Kind goes in the type field** (`--type=task|bug|feature|chore|epic|...`, `bdw types` lists them), never in a label." (skills/use-bd/SKILL.md:140-141); "**Every issue gets exactly one type label plus one or more `area:` labels.**" (skills/use-github/SKILL.md:120)
- Also stated in: A5, B2, C7, D17, F22, X9
- Provenance: ratified for Beads (PROP:295; maintainer decision 2026-10-09 on aio.7); unknown for GitHub. Generic core (one kind, one home) is inferred from both; the carrier differs (Disconnect 5).

### K28: The kinds: feature, improvement, bug, debt, meta
- Category: labels-priority
- Best statement: "`feature` ... New feature, system, or capability", "`improvement` ... Enhancement or refinement of existing functionality", "`bug` ... Something is broken or performs incorrectly", "`debt` ... Code quality, refactoring, documentation", "`meta` ... Design documents, planning artifacts, and non-code project work" (skills/setup-github-issues/SKILL.md:173-181)
- Also stated in: A5, B3, F22 (maps the five onto Beads, adding custom type `meta` so kinds stay consistent across repos)
- Provenance: unknown (taxonomy); the Beads mapping is a maintainer decision of 2026-10-09. Debt and meta overlap on documentation (A C4).

### K29: Every Issue has at least one area, from a few clearly separated areas, and may carry other labels
- Category: labels-priority
- Best statement: "**Labels:** every Issue has at least one area label and may carry others; use the ones already in use (`bdw label list-all`) unless the repo's `PRIME.md` says otherwise." (skills/use-bd/SKILL.md:142-144); "Aim for 3-8 area labels to start ... enough labels for meaningful labeling, but few enough with clear separation as to be consistently applied." (skills/setup-github-issues/SKILL.md:219-222)
- Also stated in: A6, A7, A8 (dev-x and test as near-universal areas), A9 (scope labels only when the distinction is real), B2, C7, D18
- Provenance: ratified in part (PROP criterion 8 "**Labels follow the project's conventions.**"; 44e6387's "conditional, not the biconditional" correction is unknown); A7-A9 unknown.

### K30: Attach only labels that exist in the declared scheme; an unknown label is a typo to fix, and a new label is a schema proposal
- Category: labels-priority
- Best statement: "An unknown-label exit 4 means fix the call. Never create a label to satisfy a typo; label edits are human-gated because labels encode the triage schema." (docs/projects/fjw/issue-verbs.md:240-242); "propose a schema addition rather than inventing a label ad hoc" (skills/use-github/SKILL.md:121-122)
- Also stated in: A10, B2, E8, F37
- Provenance: ratified (fjw proposal; ruling 2026-10-24 on exit code).

### K31: Labels encode the triage schema; changing an initialized repo's labels or tracker schema needs a human
- Category: labels-priority / agent-vs-human
- Best statement: "**Labels encode the project's triage schema; they are not fungible data.** ... The automated use case is first-time creation while initializing a repo; any other change to an initialized repo's labels is the signal to stop and ask." (docs/projects/fjw/issue-verbs.md:43-48)
- Also stated in: C65, E5, A22 (report drift on live schema, never edit it), A23 (leave user-added states alone), A25, B23, E16
- Provenance: ratified (fjw proposal). A22/A23/A25 unknown. Label deletion's gate is open (agent-tooling-76b).

### K32: Priority has four levels, lives in exactly one place per repo, and exists to answer "what do I work on next?"
- Category: labels-priority
- Best statement: "| `P0` | Drop-everything and address now |" / "| `P1` | Most important non-emergency work |" / "| `P2` | Standard backlog work |" / "| `P3` | Nice-to-have; opportunistic |" (skills/use-github/SKILL.md:173-176); "priority exists to answer \"what do I work on next?\"" (skills/triage-issues/SKILL.md:425)
- Also stated in: A3, A4, B6, B9, C48 (P0 count bounded by human attention; flag bucket collapse)
- Provenance: unknown.

### K33: Priority at intake is an educated guess that schedules scoping; it is refined at scoping
- Category: labels-priority
- Best statement: "Priority assigned at this stage is by definition an *educated guess* — it drives the scheduling of scoping work, not the final priority of the issue. Real refinement happens at `Needs Scope` exit (S-WORK-6)." (skills/triage-issues/SKILL.md:188)
- Also stated in: C26, B7 ("Be liberal with Priority")
- Provenance: unknown.

### K34: Size is set by the end of engineering design, not at intake; a parent is sized independently of its children
- Category: labels-priority
- Best statement: "Sizing is *skipped* in screening. Assigned no later than exit from `Needs Eng Design`." (skills/triage-issues/SKILL.md:189); "Parents are sized independently of children" (:146)
- Also stated in: C17, C27, C47
- Provenance: unknown. Sizing vocabulary (XS-XL) does not map onto session-sized Leaf Issues (Disconnect 9).

### K35: Read the tracker's live configuration; never guess names, numbers, or where priority lives; ask when it is ambiguous
- Category: setup
- Best statement: "Read from it — never guess label names, board numbers, or field options" (skills/use-github/SKILL.md:79-80); "On `\"unknown\"`, don't guess a regime: ... or ask the user — then re-orient." (:94-101)
- Also stated in: B8, B9
- Provenance: unknown.

---

## Breakdown

### K36: Branch Issue and Leaf Issue
- Category: breakdown
- Best statement: "**Branch Issue**: An Issue that holds other Issues as its children: a project, rather than a unit of work one session finishes. ... The work of a Branch Issue is management: scoping, setting success criteria, breaking down into child Issues, and verifying completion." (LEXICON.md:206-211); "**Leaf Issue**: An Issue that is not a Branch Issue: a unit of work meant to be claimed and finished in one session" (LEXICON.md:216-217)
- Also stated in: D9, G4, G5, G6
- Provenance: ratified (92ccc6d, home-in).

### K37: Branch Issues are worked in session-sized passes; one is ready work exactly when it has no open children; it has no long-lived owner
- Category: breakdown / lifecycle
- Best statement: "**Decision:** A Branch Issue is ready work exactly when it has no open children, and each claim on it is one session-sized pass that ends either by adding children or by verifying completion and closing it." (docs/adr/0009-branch-issues-are-worked-in-passes.md:10)
- Also stated in: D10, D14 ("Never claim a Branch Issue that has open children."), F19, G7, G8
- Provenance: ratified (ADR 0009). Supersedes the 2026-09-25 rulings "Never claim an epic" (F18, X1).

### K38: A pass drafts its whole breakdown before filing any of it
- Category: breakdown
- Best statement: "Children added in a pass become ready work as soon as they exist, so a pass drafts its whole breakdown before submitting it." (docs/adr/0009-branch-issues-are-worked-in-passes.md:18)
- Also stated in: D11, G10, A16, A17
- Provenance: ratified (ADR 0009). Drift: the Skill's interim form is "in one sitting", the ratified one an atomic previewed batch.

### K39: A Branch Issue is closed only by a pass that verifies it, never because its children closed
- Category: closing
- Best statement: "A Branch Issue is never closed merely because its children closed; a pass verifies it first." (docs/adr/0009-branch-issues-are-worked-in-passes.md:17)
- Also stated in: D12, G9
- Provenance: ratified (ADR 0009). Supersedes ruling (c) of 2026-09-25 (X2).

### K40: Only kinds designated to hold children take them; a task that outgrows a session is retyped, or gets a sibling linked by a dependency
- Category: breakdown
- Best statement: "**Only branch kinds take new children.** ... This is a convenience guard, not a correctness rule: an Issue that somehow gains a child is a Branch Issue by definition and is treated as one. Its job is to stop an agent's habit (subtasks under a task) from silently turning a task in progress into a project" (b90e669, home-in, quoted in extract D13)
- Also stated in: D13, G16, F19
- Provenance: ratified (home-in, ADR 0010 names the policy). Skill narrows to "Only an epic" (agent). Triage lets any Issue become a parent (Disconnect 8).

### K41: No placeholder breakdown or acceptance tasks
- Category: breakdown
- Best statement (rejected alternative): "File a breakdown task first and an acceptance task, blocked by every sibling, last." / "The acceptance task's dependencies must be kept current as children are added, which works against the grain and is easily misunderstood or skipped." (docs/adr/0009-branch-issues-are-worked-in-passes.md:29-30)
- Also stated in: G11
- Provenance: ratified (ADR 0009 Alternatives Considered).

### K42: When to split, group, or merge
- Category: breakdown
- Best statement: "**G-WHOLE (gate):** the goal is *incomplete until all members are done*. Operational test: \"does landing any single member alone deliver standalone value?\" ... dependency is *never itself* a grouping signal" (skills/triage-issues/SKILL.md:118); "Grouping is for *semantic relatedness* only." (:120); "**Expected to be rare** — 99% of the time the right move is to not over-decompose into a swarm of XS issues in the first place." (:123)
- Also stated in: C8 (per-item split criteria; grab-bags split into peers), C9 (peer split versus parent-child: components become children, orthogonal items peers), C10 (prefer vertical slices), C11, C12 (absorbed Issues closed with a back-link), C34 (tighten fuzzy checklist items before judging a split)
- Provenance: unknown.

### K43: A parent has its own status and lifecycle, not one derived from its children; scope-completeness is a body convention
- Category: lifecycle / breakdown
- Best statement: "Parent trackers have an *independent* status from their children. Derived state breaks down on mixed-state child sets." (skills/triage-issues/SKILL.md:136); "Scope-completeness is encoded by body convention, not status." (:147)
- Also stated in: C14, C15, C18
- Provenance: unknown. Consistent in spirit with K37/K39.

### K43a: Templated phases (numbered 43a to keep later IDs stable) for Branch Issues are deferred
- Category: breakdown
- Best statement: "In scope for the use-bd work, deferred from the first shipment (maintainer ruling, 2026-10-09, use-bd home-in, agent-tooling-aio)." (`bdw show agent-tooling-sn6`)
- Also stated in: F23
- Provenance: ratified deferral; the phase list is an "e.g." of unknown origin.

---

## Session loop and relationships

### K44: The session loop: orient, choose work explicitly, claim before touching, file discoveries, append progress, close on acceptance criteria, release everything held
- Category: lifecycle
- Best statement: "**Version one covers** the loop (prime, ready, claim, file discovered work, append progress to the Issue, close, and land the plane ...)" (PROP:78-80); "`close --claim-next`, `close --continue`, and `ready --claim` claim the next Issue for you, skipping the choice of what to work on. Claim explicitly instead." (skills/use-bd/quirks.md:31-33)
- Also stated in: D2, D8, G29 (moved, not lost)
- Provenance: ratified (home-in). D8's rationale is agent-elaborated; the deny is ratified. "Claim" and "ready" are Beads-native (Disconnect 13).

### K45: Look for four relationships at filing; add dependencies on your own, the other three only when very confident, otherwise raise or report them
- Category: relationships / agent-vs-human
- Best statement: "**Unilateral relationships.** Agents add dependencies they find at filing time on their own; contradiction, duplication, and composition only when very confident, and otherwise raise them (or, unattended, report them)." (PROP, ee85c50, 2026-10-08)
- Also stated in: D22, D24 (contradiction as a relation plus a label), F15
- Provenance: ratified (home-in). Conflicts with triage's "flag, do not auto-merge" (Disconnect 2).

### K46: Make each relationship's type explicit; a wrong blocking edge silently hides work; provenance links do not block
- Category: relationships
- Best statement: "always pass the type explicitly (related, discovered-from, blocks) and treat a bare dep add as a bug" (`bdw show agent-tooling-aio`, NOTES, 2026-09-26, user-approved); "a wrong blocking edge silently removes work from `bdw ready`." (skills/use-bd/SKILL.md:158-161)
- Also stated in: D23, F20
- Provenance: ratified (user-approved note; PROP:234-236).

### K47: Each relationship has one spelling and a fixed direction
- Category: relationships
- Best statement: "\"X blocks Y\" is spelled `add-blocked-by Y X`; there are no blocking subverbs, so each relationship has one spelling." (docs/projects/ghw/design.md:155-159)
- Also stated in: B12, D53, E11
- Provenance: ratified for Beads (home-in deny of aliases); ghw form unknown.

### K48: The tracker's native link is the source of truth; prose checklists and body references are narrative
- Category: relationships
- Best statement: "A body checklist can co-exist for narrative; formal linkage is the source of truth." (skills/triage-issues/SKILL.md:145)
- Also stated in: C16, C20, A17 (note: setup-github-issues records dependencies only as body references)
- Provenance: unknown.

### K49: A blocker matters only once the Issue reaches the stage it bites; mark it, link it when it is an Issue, and recheck blocked Issues every pass
- Category: relationships / lifecycle
- Best statement: "Determine the lifecycle stage at which the blocker actually bites. If the issue is currently *earlier* than that stage, its status reflects its true current lifecycle and progress continues freely — the blocker does not yet matter." (skills/triage-issues/SKILL.md:152)
- Also stated in: C19, C20, C21
- Provenance: unknown.

### K50: Work waiting on a human leaves ready work through a blocker, not a custom status, and joins one human queue
- Category: lifecycle
- Best statement: "When an Issue cannot move until a person acts (a PR in review, a decision), release it and block it with a gate, so it leaves ready work without a custom status ... so the maintainer has one queue" (skills/use-bd/SKILL.md:203-214)
- Also stated in: D29
- Provenance: ratified (home-in, PROP:341-348). Drift: the home-in first chose a custom status, then gates.

---

## Lifecycle and state

### K51: Status answers "what kind of expert attention does this Issue need next?", through eight states
- Category: lifecycle
- Best statement: "Status answers: **\"what kind of expert attention does this issue need next?\"**" (skills/triage-issues/SKILL.md:50); states `Needs Triage`, `Needs Scope`, `Needs Eng Design`, `Needs Impl`, `In progress`, `In review`, `Done`, `Rejected` (:52-61)
- Also stated in: C1, C2, C3, A21, F11 ("in the manner of the triage-issues skill's state model")
- Provenance: unknown, leaning ratified: the maintainer's c86 sketch adopts this model by reference.

### K52: Transitions go forward by defined exits; regression is allowed any time and is proposed, not applied
- Category: lifecycle
- Best statement: "**Backward (regression):** allowed at any time. Triage *proposes*; human approves." (skills/triage-issues/SKILL.md:75)
- Also stated in: C4, C5, C23 (every state checks readiness both ways)
- Provenance: unknown.

### K53: Each state has exit requirements, checked when an Issue moves on, not at creation
- Category: lifecycle
- Best statement: "A status lifecycle for Issues on Beads in which each state has exit requirements, checked when an Issue moves on, rather than requirements checked at creation." (`bdw show agent-tooling-c86`); "To leave needs_triage: a reasonable title and description, a priority, labels conforming to the project's scheme, and for a bug, steps to reproduce." ... "To leave needs_scope: success criteria (Branch Issues) or acceptance criteria (Leaf Issues)."
- Also stated in: C67, D50, F10, F11, F12; triage's per-state exit criteria (C38, C42) are the same shape
- Provenance: sketch (maintainer, 2026-10-09, "not ratified"). Disconnects 3 and 4.

### K54: Do not do later-stage work on top of an earlier stage's gap
- Category: lifecycle
- Best statement: "do not proceed with eng-design work on top of a fuzzy goal." (skills/triage-issues/SKILL.md:280)
- Also stated in: C39, C23
- Provenance: unknown.

### K55: Scoping defines the problem, not the solution: motivation, beneficiary, acceptance criteria, out of scope, constraints, adjacencies
- Category: triage / filing
- Best statement: "Underlying problem / motivation (not the proposed solution)" / "Beneficiary and benefit (end user? operator? future maintainer?)" / "Concrete acceptance criteria / definition of done" / "What's explicitly out of scope" / "Constraints (technical, design, narrative) that bound the solution space" / "Adjacencies: depends on / conflicts with / supersedes other backlog items" (skills/triage-issues/SKILL.md:211-217)
- Also stated in: C32, C33 (UX scope when user-observable), C36 (scoped body template), C38 (exit criteria), C35 (rejection rubric concentrated at scoping)
- Provenance: unknown.

### K56: Engineering design is done when an implementer could execute without further design input; size of consequence decides whether a decision lives in the Issue or a design doc
- Category: lifecycle / docs-linkage
- Best statement: "An implementer (human or agent) could pick this up and execute without further design input" (skills/triage-issues/SKILL.md:307); "**0 signals:** record decision in a `## Design decisions` section of the issue body. Discussion lives in comments; the decision itself is body content." (:286)
- Also stated in: C41, C42
- Provenance: unknown.

### K57: Open/closed and status must agree; after design, status follows the implementation artifact and the claim
- Category: lifecycle
- Best statement: "Open Issue + Status `Done`/`Rejected` → must move." / "Closed Issue + Status not `Done`/`Rejected` → must set to `Done` (or `Rejected` if the close reason supports it)." (skills/triage-issues/SKILL.md:83-84); "Status here tracks the lifecycle of the *implementation artifact*" (:316)
- Also stated in: C6, C43, C44
- Provenance: unknown.

### K58: A claim never outlives its session; continuity lives in the Issue
- Category: lifecycle
- Best statement: "**A claim never outlives its session.** Before a session ends it closes or releases every Issue it claimed; continuity between sessions lives in the Issue (its pick-up note and metadata), never in a claim. Longer-lived agents would revisit this." (PROP:337-340)
- Also stated in: D3, G8, G29
- Provenance: ratified (home-in; marked a version-one choice, PROP:321-323).

### K59: Never take over or reap someone else's claim; ask
- Category: agent-vs-human
- Best statement: "Never take over someone else's claim (`unclaim --force`, `update --assignee`); ask." (skills/use-bd/SKILL.md:104-108); "A lapsed lease is inert until reclaim runs, and sessions sit for hours waiting on a human, so a reclaim would rob live work. Denied rather than asked for, by the maintainer's ruling." (skills/use-bd/rules.json:107)
- Also stated in: D6, D7
- Provenance: ratified (ruling; PROP:204-209, 225-226).

### K60: Every state change has exactly one owner, recorded; agents cannot choose their recorded identity; automation's acts are visibly automation's
- Category: agent-vs-human
- Best statement: "4. **Every state change has one owner.** Every claim, close, and rewrite is attributable to exactly one Actor." (PROP:58-59); "Everything here acts as the deployment's machine account — automation's acts are visibly automation's, never the human user's." (skills/use-forgejo/SKILL.md:19-20)
- Also stated in: D5, G17, G28, E21, F28 (open on GitHub)
- Provenance: ratified (home-in; ADR 0002); E21 unknown. Dropped from use-bd's Skill (X10). Disconnect 15.

### K61: An agent that shares its session's identity reads, files, and appends, but never claims, closes, or rewrites
- Category: agent-vs-human
- Best statement: "**an agent that shares its session's Actor (a sub-agent, a workflow agent) reads, files new Issues, and appends notes and comments, but never claims, closes, or rewrites an Issue.** The session that holds the conversation does those. An orchestrator puts this rule in every brief it hands down." (skills/use-bd/SKILL.md:95-99)
- Also stated in: D4, F26
- Provenance: ratified (PROP:331-336). Its reason (attribution or ownership) is open on agent-tooling-i4e.

### K62: An Issue's description is its state, rewritten in place with a pick-up section; notes and comments are its log, appended
- Category: lifecycle / docs-linkage
- Best statement: "a pick-up point is a state doc and is rewritten in place each session; a friction log or running record (as on w7p.4) is a stream doc and grows by appending. ... (history lives in the issue's event history, not in the body)." (`bdw show agent-tooling-aio`, NOTES, 2026-09-25, user ruling); "An Issue's description is its state: rewrite it in place (`--body-file`) so it always reads as the current picture, including a `## Pick-up` section ... Notes and comments are its log: append, never rewrite." (skills/use-bd/SKILL.md:196-199)
- Also stated in: D27, F16, C56 (the triage ledger: body = state, comments = events)
- Provenance: ratified (ruling); the choice of field is agent-settled (Disconnect 6).

### K63: Issues are living documents edited in place; PRs append
- Category: lifecycle
- Best statement: "**Issues are living documents; PRs are append-only submissions.** An issue moves from placeholder to corrected and expanded over its life, so editing in place is expected; reconstructing its current truth from a trail of comments is worse for whoever implements it." (docs/projects/fjw/issue-verbs.md:24-28)
- Also stated in: E1, E2 (no closed-Issue edit guard), E12 (edits should be audited mutation, not history destruction)
- Provenance: ratified (fjw proposal).

### K64: A cold pick-up works from the tracker alone; the Issue points to its context rather than holding it
- Category: docs-linkage
- Best statement: "3. **A cold pick-up works.** A fresh session can resume any Issue from the Issue Tracker alone. The Issue points to the context it needs rather than holding all of it, so nothing is duplicated where it can drift." (PROP:55-57)
- Also stated in: D26
- Provenance: ratified (home-in). Dropped from the Skill (X10).

### K65: Material that belongs in a standard document goes there and the Issue links it; unplaced material goes to a Docs Inbox owned by an open Issue
- Category: docs-linkage
- Best statement: "If information makes sense in a requirements doc, a design doc, a UX design, an ADR, a lexicon entry, or any other standard document type the project uses, it goes there, and the Issue links to it" (8f58e26, home-in, quoted in extract D25); "every item in it is owned by an open Issue to incorporate it; nothing is meant to stay in it" (LEXICON.md:248-256)
- Also stated in: D25, G26
- Provenance: ratified (home-in). The Skill's "If you do not know where it belongs, keep it in the description" is agent-elaborated (Disconnect 16).

### K66: Preserve the structure other processes rely on when rewriting a body
- Category: lifecycle
- Best statement: "Before rewriting a body wholesale, preserve any triage-owned structure already in it ... The wrapper doesn't parse these; stomping them breaks triage." (skills/use-github/SKILL.md:206-215)
- Also stated in: B10, C64
- Provenance: unknown.

### K67: Record branch and PR as structured data, the one current answer
- Category: docs-linkage
- Best statement: "the Issue records its branch and PR as metadata keys, which are structured and queryable, rather than as prose in its notes." (b90e669, quoted in extract D31)
- Also stated in: D31
- Provenance: ratified (home-in).

### K68: Agents note progress on Issues, including human-filed ones, by comment
- Category: agent-vs-human
- Best statement: "a creator pin breaks the main use case (noting progress on human-filed issues). Comments are append-only, attributed, and auditable." (docs/projects/fjw/issue-verbs.md:85-89)
- Also stated in: E10, D2 ("Append progress to the Issue as you go")
- Provenance: ratified (fjw proposal; home-in loop).

---

## Closing

### K69: Close when the acceptance criteria hold
- Category: closing
- Best statement: "6. `bdw close <id> --reason-file=<path>` when its acceptance criteria hold." (skills/use-bd/SKILL.md:84)
- Also stated in: D2 (drift from "when done", 50e29e6)
- Provenance: ratified (home-in).

### K70: Every close carries its reason, the audit record; forge auto-close on PR merge is the one exception
- Category: closing
- Best statement: "a silent close must be inexpressible, and the comment is the audit record (\"done because X, see commit Y\") ... The mandatory close comment is meant to hold across Wrapper families" (docs/projects/fjw/issue-verbs.md:96-103)
- Also stated in: A19, B11, E13, F25
- Provenance: ratified (fjw proposal 2026-09-14); its spread to ghw is agent work (8b0fccf, agent-tooling-75z).

### K71: Reopening is its own act, with a reason, and needs more authority than closing
- Category: lifecycle / agent-vs-human
- Best statement: "reopening is a state change with a reason (\"closed in error\", \"regressed\") ... It sits in a higher tier than close: an agent that may close its own finished work does not thereby get to resurrect anything." (docs/projects/fjw/issue-verbs.md:105-109)
- Also stated in: E14
- Provenance: ratified (fjw proposal).

### K72: Nothing is deleted from the tracker; closed Issues are hidden, not forgotten
- Category: closing
- Best statement: "closed beads are hidden from agents by default so forgetting buys nothing." (docs/adr/0001-adopt-beads-for-the-tracker-trial.md:10)
- Also stated in: D40, G19
- Provenance: ratified (ADR 0001).

### K73: Work under review closes through the normal close after merge; resolving a human's gate is the human's act
- Category: closing
- Best statement: "A review closes through the normal close after merge, never through `bd human respond`, which closes the Issue at once." (PROP:346-348); "`gate resolve` has no rule, so it prompts: resolving a human gate is the human's act." (docs/projects/beads-trial/design.md:100-101)
- Also stated in: D30
- Provenance: ratified (home-in); the gate-resolve rationale unknown.

### K74: An Issue is done only when everything that describes it agrees
- Category: closing
- Best statement: "**Per task:** an Issue is done only when every reference across every surface we control agrees with the change, however many PRs, repos, deployments, or authors that takes" (CLAUDE.md:127-132)
- Also stated in: G22, G24, G25, D44 (Known-gaps line at filing)
- Provenance: unknown in the repo.

---

## TODO comments and linkage

### K75: Every TODO comment cites a real Issue; file the Issue first; clean up the TODOs when it closes
- Category: todo-comments
- Best statement: "**Every TODO references a real issue.** No bare TODOs." (skills/use-github/SKILL.md:232); "If you're about to write a TODO and there's no issue for it, file the issue first" (:239-240); "When an issue closes, grep for `TODO(#N)` and clean up the comments it left behind." (:240-241)
- Also stated in: A27, A28, B13, B14, D42, G21
- Provenance: unknown; consistent across trackers (only the ID syntax differs).

### K76: TODO lists kept in files are outside Issue triage
- Category: todo-comments / triage
- Best statement: "TODO lists kept in files (a `TODO.md`, TODO sections in docs) are out of scope; a separate backlog-grooming pass, if you have one, handles them." (skills/triage-issues/SKILL.md:26)
- Also stated in: C63
- Provenance: unknown.

### K77: Every reference to an Issue includes its Issue ID
- Category: docs-linkage
- Best statement: "every reference to an Issue includes its Issue ID" (LEXICON.md:202-204)
- Also stated in: G3
- Provenance: ratified (8201891). Drift from "the only way ... refer to" to "includes".

### K78: A PR or commit says whether it finishes an Issue or only advances it
- Category: docs-linkage
- Best statement: "For work that advances an issue without finishing it, use contributing language instead — `furthers #42`, `part of #42`, `towards #42` — which links without auto-closing." (skills/use-github/SKILL.md:260-263)
- Also stated in: B15, C44, D43, G20 ("Lands agent-tooling-xyz"), F38 (commit form open, agent-tooling-nbj)
- Provenance: unknown; consistent.

---

## Triage

### K79: Filing-time checks are best effort; a separate batch pass across the whole tracker reconciles what they miss
- Category: triage
- Best statement: "Automated triage of the Issue Tracker as an offline, batch process: periodically reconcile what filing-time checks miss or get wrong, across the whole tracker, rather than one Issue at a time." ... "Raised by the maintainer on 2026-10-08" (`bdw show agent-tooling-r6b`)
- Also stated in: C68, D49, F14, B20 (single-Issue work versus a whole-backlog pass), C62
- Provenance: ratified that it exists (maintainer-raised); the "best effort" list reads agent-elaborated.

### K80: Triage writes on its own only bounded, enumerable corrections; transitions, body rewrites, closes, duplicates, grouping, and reparenting are proposals for a human
- Category: triage / agent-vs-human
- Best statement: "**Autonomy boundary:** only R-SYNC status corrections, R-LABEL schema fixes, and `Last Triaged` bumps are written without asking (all bounded/enumerable field writes). Everything else — priority/size/status *transitions*, scoping/typo body rewrites (R-SCREEN-9 included), closes, reparenting — is **proposed** in the report and awaits human confirmation." (skills/triage-issues/SKILL.md:505)
- Also stated in: C13, C28, C29, C30, C31, C45, C50, B21, F42
- Provenance: unknown (audit records "None given" for several restrictions). Disconnect 2.

### K81: Unattended runs accumulate proposals but never resolve the ones needing a human; a denial becomes a pending item
- Category: triage / agent-vs-human
- Best statement: "The only difference: an unattended run can *accumulate* proposals but never *resolve* the with-human ones." (skills/triage-issues/SKILL.md:593); "On denial the agent records the intended action as a pending finding and moves on; it must **not** seek an alternate path to the same mutation." (:595)
- Also stated in: C54, C55, D22 ("unattended: report it"), D32
- Provenance: unknown (triage); the "unattended: report it" form is ratified (home-in).

### K82: Scoping and design are interactive: the agent enumerates questions and decisions, the human decides
- Category: triage / agent-vs-human
- Best statement: "The agent enumerates from the body + codebase context; the human catches what the agent misses." (skills/triage-issues/SKILL.md:284); "the agent may suggest a dedicated design-interview session — but does not demand it." (:251)
- Also stated in: C37, C40, C22 (ADR rubric, offered sparingly, never autonomous), F33 (decisions are the maintainer's; agents draft)
- Provenance: unknown; C22 matches the use-adrs gate.

### K83: A triage report is a durable record: findings, not Issues, are its unit; its body is current state and its comments the log; pending items carry forward until acted on or dismissed
- Category: triage
- Best statement: "The report's atomic unit is a **finding** ... **not** an issue." (skills/triage-issues/SKILL.md:548); "Body answers \"what needs my attention right now\"; comments answer \"what changed since I last looked.\"" (:602); "The ledger *is* the memory the skip-optimization discards." (:607)
- Also stated in: C53, C56, C57, C58, C51, C52
- Provenance: unknown. Dismissal is marked "PROVISIONAL" in the source.

### K84: Staleness is time since meaningful activity against a priority-scaled threshold, from exact timestamps; untriaged Issues are always reviewed
- Category: triage
- Best statement: "compute `staleness = now - mostRecentMeaningfulActivity`, and flag if `staleness > threshold(priority) × multiplier`." (skills/triage-issues/SKILL.md:347); "Agents reasoning about recency or staleness use the exact UTC instants in the JSON output of bd show and compare against the date command, never the rendered date." (`bdw show agent-tooling-aio`, NOTES, 2026-09-25, user ruling)
- Also stated in: C46, C47, C49 (inventory must catch closed-but-nonterminal and open-without-status), F17
- Provenance: unknown (triage); the timestamp rule ratified (ruling), but dropped from the Skill (X4).

### K85: Standing up triage in a repo is an interactive, human-confirmed bootstrap
- Category: setup / triage
- Best statement: "**R-CAD-6 — Standing up triage in a new repo is an interactive bootstrap, never autonomous.**" (skills/triage-issues/SKILL.md:628)
- Also stated in: C60
- Provenance: unknown.

---

## Agent versus human (other)

### K86: Act only on your own project's Issues unless expressly permitted
- Category: agent-vs-human
- Best statement: "**No reach outside the project.** An agent acts only on its own project's Issues unless expressly given permission to act on another's." (PROP:265-266)
- Also stated in: D36
- Provenance: ratified (home-in). Dropped from the Skill (X10).

### K87: Report friction with the tracker; offer upstream bug reports, never file them on your own
- Category: agent-vs-human
- Best statement: "Offer to report a Beads bug or contribute a fix upstream; never do it on your own. Unattended, mention the bug in your final report." (skills/use-bd/SKILL.md:225-229)
- Also stated in: D32
- Provenance: ratified (home-in).

### K88: Memories do not live in the tracker
- Category: other
- Best statement: "Memories stay in the harness's own memory files, never in Beads." (skills/use-bd/quirks.md:73)
- Also stated in: D41, G32
- Provenance: unknown (2026-09-24 CLAUDE.md), carried into the ratified deny set.

### K89: Decisions are the maintainer's; agents draft them
- Category: agent-vs-human
- Best statement: "Precondition: the verdict itself is the maintainer's; an agent drafts the ADR" (`bdw show agent-tooling-0pe`); "The decisions themselves are the maintainer's" (`bdw show agent-tooling-xla`)
- Also stated in: F33, C22, K82
- Provenance: unknown, leaning ratified (0pe derives it from the ratified phase-two proposal).

---

## Skill-family architecture (not agent conduct; listed for completeness)

### K90: A generic Issue layer with thin tool-specific skills, split for progressive disclosure and use-case focus
- Category: other
- Best statement: "2026-10-26, maintainer ruling: this epic is now the pilot for progressive disclosure, so the skill family is split for progressive disclosure and use-case focus from the start." (`bdw show agent-tooling-u9n`, NOTES)
- Also stated in: F1-F7, C69, D51
- Provenance: ratified (the split, 2026-10-26); the four-skill shape (setup-issue-tracker, use-issues, create-issue, tool-agnostic triage-issues) is a sketch.

### K91: Skill text carries only what an operating agent needs
- Category: docs-linkage
- Best statement: "carries only what an operating agent needs (no history, dates, or prior-version residue), and is as concise as clarity allows." (docs/projects/fjw/issue-verbs.md:246-248)
- Also stated in: E27
- Provenance: ratified (fjw proposal).

### K92: Tool-behavior notes hold only for the version they were verified on
- Category: other
- Best statement: "Verified against bd 1.3.0 (`bdw version`). On any other version, treat this list as unverified, and re-verify it when upgrading." (skills/use-bd/quirks.md:3-4)
- Also stated in: D48
- Provenance: ratified (home-in).

---

## Platform-specific residue

One line each: rules a platform skill must keep. Extract IDs in brackets.

### Beads (use-bd)
- Always `bdw`, verb first; `bdw` refuses `--actor`, `-C`, `--db`, and similar; `bdw help <verb>` [D mechanics].
- `bdw prime` then `bdw gate check` at session start; `.beads/PRIME.md` replaces bd's default prime text [D2, D47].
- `bdw ready` still lists Branch Issues with open children; skip them by hand until aio.4 [D10, X11].
- `--claim` silently succeeds for the same Actor, so a claim does not prove ownership; `attended-<user>` fallback [D6].
- Leases lapse without `bdw heartbeat`; `reclaim` denied; the lease procedure is open (agent-tooling-3lo) [D7, F21].
- Deny `close --claim-next`, `close --continue`, `ready --claim` [D8].
- Never run `epic close-eligible` [D12].
- Kind in the type field; GitHub kinds map to bug, feature, chore, and a custom `meta` type [D17, F22].
- Children inherit parent labels unless `--no-inherit-labels` [D mechanics].
- Always pass `--type` to `dep add`; `dep add <a> <b>` means a depends on b; contradiction is `relates-to` plus a label; never add a blocks edge from a parent to its own child (deadlocks, upstream #6506) [D23, D24, X4, F20].
- Free text through files; table of fields with no file form; when inline is refused switch to the file form [D28].
- Description holds state with `## Pick-up`; `--append-notes` appends, `--notes` replaces [D27].
- Waiting on a human: release, gate (`gh:pr` only on GitHub-hosted repos, else `human`), `human` label, `bdw human list`; never close through `human respond`; `gate resolve` prompts [D29, D30].
- Branch and PR as metadata keys [D31].
- Friction log location per PRIME.md [D32].
- Forgetting commands denied; never delete tracked `.beads/` files; `find-duplicates --method=ai` sends text off-machine [D40, D mechanics].
- `bd show` dates are UTC; use JSON instants [F17, X4].
- Onboarding: `init` and `dolt` are human steps; private Dolt remote only; `validation.on-create` off; `create.require-description` on [D20, D21, D39, D46].
- Imported Issues carry their source URL as external reference [D45].
- `TODO(<issue-id>)`; PR body `Lands <issue-id>` [D42, D43].
- Planned: filing through a validated graph plan with near-duplicate search and a ready-work echo (aio.5); conventions file `.beads/bdw.json` and Docs Inbox Verb (aio.6); status lifecycle with custom statuses (c86) [F36, F37, F13].

### GitHub (use-github, setup-github-issues, triage-issues)
- All writes through `ghw-*` by bare name; `<owner/repo>` explicit; bodies through staged files [B mechanics, A32].
- Orient once per session with `ghw-orient`; read `priority_regime`, board `conformance`, `extra_options` [B8, B9].
- Priority is a board field when a board is linked, else exactly one P-label; in the `p-labels` regime there is no status beyond open/closed [A3, B9].
- Exactly one type label and at least one `area:` label, enforced by `ghw-issue-create`; reclassify in two calls [A6, B2].
- `ghw-label-sync` is the only label creator and syncs the whole registry; `plan` before `apply-delete` [A10, A25, B23].
- Board provisioning by `ghw-board-sync`; drift on live fields is reported, never edited; the eight Status options with exact casing; `Needs Triage` set at filing on a conforming board; auto-add workflow is UI-only [A20-A22, A31, B5, B7].
- `ghw-issue-close` requires a comment file; already-closed is a no-op that posts nothing [B11].
- `ghw-issue-link`: `<issue#>` is the parent or the blocked Issue; "X blocks Y" is `add-blocked-by Y X` [B12].
- Triage: `TRIAGE.md` profile with a JSON block; the board is the inventory anchor; six `triage-*` wrappers are the only unattended write path, under `dontAsk`, never `bypassPermissions`; the ledger is a GitHub issue [C49, C59, C61, mechanics].
- Closing keywords (`Closes/Fixes/Resolves #N`) versus contributing language; `TODO(#N)` [B13, B15, C44].
- Milestones, not parent trackers, for releases and schedules [C11].
- PRs: non-draft by default; disclose unattended conflict resolutions; merge only when the user has said to, `merge` strategy only [B16, B25, B26].
- Setup-time: confirm `owner/repo`; source-TODO grep needs one `--include` per extension [A2, A mechanics].

### Forgejo (use-forgejo, planned fjw issue Verbs)
- One index space for issues and PRs: a number of the wrong kind exits 2 naming the sibling Verb; never treat it as absence and file a duplicate [E3].
- Labels are schema-free at the Verb level; schema prescription belongs to a setup skill [E4].
- Unknown label exits 3 and is never created [E8].
- Capability tiers reader / contributor / triage / admin; every Verb has a disposition; label-edit and label-delete are ask, label-delete never allow [E15].
- Label deletion refuses while on open items; proceeds with an audit count when only on closed ones [E16].
- Close and reopen comments mandatory; reopen at a higher tier [E13, E14].
- Retitle and set-body are separately grantable subverbs [E11].
- Issue dependencies deferred; no sub-issue hierarchy [E17].
- Acts as a machine account; a repo-level 404 with a correct slug is a missing grant: report, never retry or hunt for credentials [E18, E21].
- Under Read, create-with-labels silently drops labels; Verbs must not report success [E20].
- Merge is absent; treat an instruction to merge as a question [E22].

---

## Side findings

Defects in shipped material, unrelated to the redesign. One line each, with the extract that found it.

1. CLAUDE.md:48-49 and .beads/PRIME.md:8 say the Beads database is "local to the maintainer's machine", but the private Dolt remote is shipped (docs/projects/beads-trial/index.md:63, ADR 0012) [G contradiction 1].
2. docs/projects/ghw/index.md:39 marks "Exit codes per the Exit-code contract" `shipped` while its own Known gap (agent-tooling-cjvo.2) says the Verbs still use the old taxonomy; skills/use-github/SKILL.md:41-47 documents codes 0-6 as current; design.md:280-281 and SKILL.md:46 disagree on auth failures (1 versus 5) [B contradiction 5].
3. skills/use-forgejo/SKILL.md:60-71 teaches the old seven-code taxonomy (including `6` network) while fjw design.md describes the six-code contract [E contradiction 2].
4. docs/projects/fjw/design.md:152 still says "The recommended grant is Read collaborator", against the 2026-10-24 ruling that the grant is per-repo policy (scheduled for agent-tooling-1vr.5) [E19, E contradiction 3].
5. docs/projects/bdw/index.md:44 and :50 say exit 1 where cli/bdw:17 and :24 exit 3 and 5 [D X13].
6. docs/index.md:155-156 calls `bdw` outside the Exit-code contract "by design", while LEXICON.md:266-267 and ADR 0013:10 say every Wrapper reports through it [G contradiction 4].
7. skills/triage-issues/SKILL.md:507 still defers writing blocked-by relationships, though `ghw-issue-link add-blocked-by` is shipped (docs/projects/ghw/index.md:30); R-BLOCK-4 (:154) says "ALWAYS" [C contradiction 9].
8. skills/triage-issues/SKILL.md:83 says R-SYNC-1 surfaces ambiguous cases for a human, but reference/triage-apply-sync:62-63 always demotes [C contradiction 7].
9. skills/triage-issues/SKILL.md:192 (R-SCREEN-8) uses "issues > N days" with N never defined [C contradiction 13].
10. skills/triage-issues/SKILL.md:316 and :648 count recent commits as an active-work signal while :329 excludes raw commit references [C contradiction 10].
11. skills/triage-issues/SKILL.md:57-59 labels three states "(PM-axis only)" though each has entry-verification rules (:326-339) [C contradiction 11].
12. skills/setup-github-issues/SKILL.md:465's bare-TODO check greps only `TODO[^(]` in `*.py` and `*.ts` (Step 3 audits ten extensions), never checks FIXMEs, and matches "TODO.md" in prose [A C5].
13. skills/setup-github-issues/SKILL.md:494 and skills/use-github/SKILL.md:236 keep an unexplained "FIXME ... engine/platform bugs" rule that looks like a leftover from a game-engine predecessor project [A C5, B judgement].
14. [omitted: private source]
15. The kind table is copied verbatim in skills/use-github/SKILL.md:126-132 and skills/setup-github-issues/SKILL.md:173-181, and debt and meta both claim documentation with no tie-breaker [A C4].
16. skills/use-github/SKILL.md:23-24 says "Every GitHub operation this skill covers runs through the `ghw-*` wrappers" but Step 2 uses raw `gh issue list` and orient falls back to raw `gh repo view` [B contradiction 1].
17. skills/use-github/SKILL.md:270 says merge "only when the user has said to" with no exception for project rules, while CLAUDE.md lets agents merge into `integrate/` branches unattended (ghw design.md:80 reconciles; the Skill does not) [B contradiction 2].
18. skills/use-github/SKILL.md:96 and :167-169: the `p-labels` regime has no status beyond open/closed and skips the status step, but nothing says what replaces intake triage there [B judgement].
19. The agent-tooling-aio note of 2026-09-25 (rulings b and c) and the agent-tooling-w7p standing rules still say "never claim an epic" and close epics when children close, with no superseded marker, against ADR 0009 [D X1-X2, F C1].
20. agent-tooling-nbj points to CLAUDE.md for the TODO citation rule, which now lives in .beads/PRIME.md:22 [F].
21. agent-tooling-0pe's description still carries the pre-ruling plan to close every GitHub issue and disable GitHub Issues [F C9].
22. docs/projects/beads-trial/index.md:72-73's Known gap tells agents to spell denied verbs "in words" in Issue text, against "never reword" (skills/use-bd/SKILL.md:175-176); the file form already sidesteps deny matching [D X5].
23. docs/projects/use-bd/index.md Known gaps omits two shortfalls: Branch Issue readiness (`bdw ready` lists Branch Issues with open children) and the Skill's description fallback in place of the Docs Inbox [D X8, X11].
24. docs/projects/fjw/issue-verbs.md:128-129's label-delete "exit 4" was never re-mapped by a ruling under ADR 0013 (a conflict with existing state would be 2); the implementation (agent-tooling-1vr) needs the answer [E contradiction 1].
25. fjw tier table (docs/projects/fjw/issue-verbs.md:162) allows `fjw-label-create` at triage tier unconditionally, while :47-48 says any change to an initialized repo's labels is the signal to stop and ask [E contradiction 4].
26. LEXICON.md dropped "External reference" at 8201891 without a Retired line [G13].
