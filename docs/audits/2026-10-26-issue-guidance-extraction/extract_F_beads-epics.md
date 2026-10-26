# Extract F: the maintainer's sketches and rulings recorded in Beads Issues

> This document captures state as of 2026-10-26. For current state, see [docs/index.md](../../index.md).

Source group: Beads Issues in this repo,
read with `bdw show` and `bdw comments` on 2026-10-26. None of the nine named
Issues has any comments (`bdw comments` printed "No comments on ..." for each).
Only agent-tooling-0pe (the Beads trial verdict) has a comment.

How to read the citations. A Beads Issue has no line numbers, so "Current text"
gives `bdw show <id>` plus the section (DESCRIPTION, NOTES, CLOSE REASON).
Quotes are verbatim except for re-wrapping: `bdw show` hard-wraps at 78 columns,
and I joined those lines back together. Bullets render as "•" in `bdw show`.
"Earliest form" for an Issue is its creation date. `bdw history` gives 704
undiffed snapshots for agent-tooling-u9n alone, so I could not trace text drift
inside an Issue (see Judgement calls). Where the same principle also lives in
the repo, I traced the repo text with `git log -S`.

Provenance labels:
- **ratified**: an ADR, or a passage the Issue itself calls a "maintainer ruling",
  "user ruling", "user-approved", "maintainer decided", or "ratified".
- **sketch (raised, not ratified)**: the Issue says the maintainer raised it and
  says outright that it is not ratified. I treat this as a fourth label, kept
  apart from both ratified and agent-elaborated.
- **agent-elaborated**: text an agent wrote around a ruling or a sketch (Why
  sections, "Likely shape", requirements lists), with no ruling attached.

Every Issue here was created by an agent job (`claude-job-...`). So even a
ruling is an agent's transcription of what the maintainer said.

---

## Principles

### F1: Split the Issue Tracker skills into a tool-agnostic layer plus thin tool-specific skills
- Category: setup / other (skill architecture)
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-u9n`, DESCRIPTION): "Decide whether the Issue Tracker skills become a family split by layer: a tool-agnostic layer (how this ecosystem structures, breaks down, links, and triages Issues) with thin tool-specific skills on top (Beads, GitHub Issues), for both setup and day-to-day use, and with triage-issues made tool-agnostic."
- Earliest form: agent-tooling-u9n created 2026-10-08 (job 521331be, the use-bd home-in session). Unchanged as far as I can see.
- Provenance: sketch (raised, not ratified). Evidence: "Sketch raised by the maintainer on 2026-10-07 (not ratified, a starting point to scope)". The NOTES ruling of 2026-10-26 (F5) commits to doing the split ("the skill family is split for progressive disclosure and use-case focus from the start"). So the split itself is now ratified; the four-skill shape below is still a sketch.

### F2: setup-issue-tracker, generic guidance for structuring Issues in a project
- Category: setup
- Generic or specific: mixed. The generic part is setup-issue-tracker; the specific part is "setup-github-issues and setup-bd add the tool specifics".
- Current text (verbatim, `bdw show agent-tooling-u9n`, DESCRIPTION): "setup-issue-tracker: generic guidance for structuring Issues in a project; setup-github-issues and setup-bd add the tool specifics."
- Earliest form: agent-tooling-u9n, 2026-10-08. Unchanged.
- Provenance: sketch (raised, not ratified). Same evidence as F1. Note: no `setup-bd` skill exists. Beads setup today is `skills/use-bd/onboarding.md`, a supporting file inside use-bd.

### F3: use-issues, generic guidance for thinking about Issues and project management
- Category: other (skill architecture: lifecycle, triage, process)
- Generic or specific: mixed. The generic part is use-issues; the specific part is "use-bd and use-github-issues add the tool specifics and quirks".
- Current text (verbatim, `bdw show agent-tooling-u9n`, DESCRIPTION): "use-issues: generic guidance for thinking about Issues and project management; use-bd and use-github-issues add the tool specifics and quirks."
- Earliest form: agent-tooling-u9n, 2026-10-08. Unchanged.
- Provenance: sketch (raised, not ratified). Note: the existing skill is named `use-github`, not `use-github-issues`. Also, use-github covers PRs and the `TODO(#N)` rule as well as Issues.

### F4: create-issue, and above all breaking down, deduplicating, and linking new Issues
- Category: filing / breakdown / relationships
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-u9n`, DESCRIPTION): "create-issue: tool-agnostic guidance for creating, and above all breaking down, deduplicating, and linking, new Issues."
- Earliest form: agent-tooling-u9n, 2026-10-08. Unchanged.
- Provenance: sketch (raised, not ratified). The priority order matters: "above all" ranks breakdown, deduplication, and linking above the act of creation itself.

### F5: triage-issues becomes fully tool-agnostic, built on the skills above
- Category: triage
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-u9n`, DESCRIPTION): "triage-issues: fully tool-agnostic, relying on the skills above."
- Earliest form: agent-tooling-u9n, 2026-10-08. Unchanged.
- Provenance: sketch (raised, not ratified). Today triage-issues is GitHub-only. The Status values it calls an 8-state model are GitHub Project board columns (`skills/triage-issues/SKILL.md:54-55`, "`Needs Triage` | Screening / bookkeeping | Fully agent-autonomous", "`Needs Scope` | Business-level scoping (define the goal) | Agent + human-in-loop").

### F6: Why the split: guidance is converging across trackers, and duplicating it invites drift
- Category: other (rationale)
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-u9n`, DESCRIPTION, "## Why"): "The guidance is converging across trackers, and duplicating it per tool invites drift."
- Earliest form: agent-tooling-u9n, 2026-10-08. Unchanged.
- Provenance: agent-elaborated, my judgement. The sketch is attributed to the maintainer, but this Why paragraph has no attribution. The same paragraph also contains the agent's own cross-reference ("Related to, but separate from, the progressive-disclosure epic filed alongside").

### F7: The family is split for progressive disclosure and use-case focus from the start, and pilots that restructure
- Category: other (skill architecture)
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-u9n`, NOTES): "2026-10-26, maintainer ruling: this epic is now the pilot for progressive disclosure, so the skill family is split for progressive disclosure and use-case focus from the start. agent-tooling-jat now waits on it (a blocks edge)."
- Earliest form: the motive was first recorded on agent-tooling-jat, created 2026-10-08: "an agent loads only what its use case needs and not a long manual every time ... the material irrelevant to the task at hand dilutes the agent's context and can confuse it. Raised by the maintainer on 2026-10-07." The 2026-10-26 ruling turns that motive into a design constraint on u9n.
- Provenance: ratified (the note is labelled "maintainer ruling"). The jat motive is "raised by the maintainer".

### F8: Scoping procedure: recover the original intent, do not relitigate, and take the union of principles
- Category: other (process for this scoping)
- Generic or specific: generic (as a process)
- Current text (verbatim, `bdw show agent-tooling-u9n.1`, DESCRIPTION): "The maintainer set the procedure on 2026-10-26. The aim is to recover the maintainer's original design philosophy rather than relitigate it, and to undo drift accumulated through sessions and layers of agents each reinterpreting the last one's text." Also: "They take the union of the principles, not the common subset. Each principle is quoted verbatim with its source, traced through history to its earliest form, and marked ratified by the maintainer, elaborated by an agent, or unknown. Conflicts are listed separately." Later steps: "a short plain-English set of requirements for a generic use-issues model: how agents use Issues and think about triage and process on every platform. The maintainer reads every word, approves what is aligned, and discusses each disconnect, one per turn." Then "A /home-in on the rest of the problem space only."
- Earliest form: agent-tooling-u9n.1, created 2026-10-08, rewritten 2026-10-26. I cannot see the earlier description (no diff in `bdw history`).
- Provenance: ratified (the Issue says "The maintainer set the procedure on 2026-10-26"). Open item in the same text: "(whether it is a dated proposal or design.md is still open)".

### F9: Capture during flow is never blocked; file with what you know, honestly, with no placeholder text
- Category: filing / lifecycle
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-c86`, DESCRIPTION): "New Issues land in a starting state such as needs_triage with whatever the filer knows, so capture during flow is never blocked (a bug whose repro is unknown still gets filed, and says so honestly rather than with placeholder text)."
- Earliest form: agent-tooling-c86, created 2026-10-10, quoting a sketch from 2026-10-09. The same principle already stood in the use-bd design: commit 733d6d4 (2026-10-09, "use-bd design: filing through a validated plan file; advisory lint") added `docs/projects/use-bd/v1-proposal.md` "No barrier to capture." That text reads "Beads' section lint (`bd lint`) is type-dependent and, if enforced at creation, would refuse a bug filed before anyone knows how to reproduce it, inviting placeholder text. So `validation.on-create` stays off ...". It has not changed since.
- Provenance: mixed. The c86 statement is a sketch ("Sketch from the maintainer (2026-10-09, use-bd home-in, agent-tooling-aio), not ratified"). The "No barrier to capture" anti-goal sits in the use-bd design settled during the home-in, which agent-tooling-aio calls "settled", so the principle is effectively ratified for Beads.

### F10: Requirements are exit requirements per lifecycle state, checked when an Issue moves on, not at creation
- Category: lifecycle
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-c86`, DESCRIPTION): "A status lifecycle for Issues on Beads in which each state has exit requirements, checked when an Issue moves on, rather than requirements checked at creation."
- Earliest form: agent-tooling-c86, 2026-10-10. Unchanged.
- Provenance: sketch (raised, not ratified): "Sketch from the maintainer (2026-10-09, use-bd home-in, agent-tooling-aio), not ratified".

### F11: Exit from needs_triage: title, description, priority, conforming labels, and repro steps for a bug
- Category: triage / lifecycle / labels-priority
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-c86`, DESCRIPTION): "To leave needs_triage: a reasonable title and description, a priority, labels conforming to the project's scheme, and for a bug, steps to reproduce. It then moves to needs_scope, in the manner of the triage-issues skill's state model."
- Earliest form: agent-tooling-c86, 2026-10-10. Unchanged.
- Provenance: sketch (raised, not ratified). The sketch adopts the triage-issues state model by reference ("in the manner of"), so that model's Needs Triage and Needs Scope states are its intended frame.

### F12: Exit from needs_scope: success criteria for Branch Issues, acceptance criteria for Leaf Issues
- Category: lifecycle / breakdown
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-c86`, DESCRIPTION): "To leave needs_scope: success criteria (Branch Issues) or acceptance criteria (Leaf Issues). And so on through the lifecycle."
- Earliest form: agent-tooling-c86, 2026-10-10. Unchanged.
- Provenance: sketch (raised, not ratified). The split between success criteria and acceptance criteria matches the practice on agent-tooling-aio ("## Success Criteria") and its children ("## Acceptance Criteria").

### F13: Exit requirements are declared per repo as conventions, not policy
- Category: setup / lifecycle
- Generic or specific: mixed. The generic part is that per-repo exit requirements are conventions, not Permission policy. The specific part (custom statuses, the bdw config file, a tier-3 Verb, `bd lint`) is listed under mechanics.
- Current text (verbatim, `bdw show agent-tooling-c86`, DESCRIPTION, "## Likely shape"): "Lifecycle states as custom statuses; each state's exit requirements declared per repo in the bdw config file (conventions, not policy); a tier-3 bdw Verb for transitions (ADR 0010, bdw carries Beads policy in tiers) that checks them."
- Earliest form: agent-tooling-c86, 2026-10-10. Unchanged.
- Provenance: agent-elaborated. The "Likely shape" section has no attribution. The split between conventions and policy comes from the ratified use-bd design ("One Skill, many repos": "policy (what agents may do) versus conventions (how this project does things)").

### F14: Filing-time checks are best effort; a batch pass across the whole tracker catches what they miss
- Category: triage / relationships
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-r6b`, DESCRIPTION): "Automated triage of the Issue Tracker as an offline, batch process: periodically reconcile what filing-time checks miss or get wrong, across the whole tracker, rather than one Issue at a time." And: "Filing-time checks are best effort: an agent sees only part of the tracker, and wrong or missing relationships, implicit shared parents, stale Issues, and anomalies (for example a Branch Issue that is not of a branch kind) accumulate. A batch pass is where those get caught."
- Earliest form: agent-tooling-r6b, created 2026-10-09. Unchanged.
- Provenance: mixed. That a batch triage pass should exist is the maintainer's: "Raised by the maintainer on 2026-10-08 during the use-bd home-in (agent-tooling-aio) as orthogonal to use-bd version one." The list of what accumulates and the "best effort" wording read as agent elaboration (my judgement). r6b does not say it is unratified, but it is a Branch Issue whose "first pass scopes it".

### F15: The four relationships at filing; agents add dependencies on their own, and raise the rest unless very confident
- Category: relationships / agent-vs-human
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-r6b`, DESCRIPTION): "The use-bd design asks agents to look for four relationships when they file an Issue (dependency, contradiction, duplication, composition), and lets them add dependencies unilaterally, guarded only by an echo of what left ready work." The full form lives in `skills/use-bd/SKILL.md:149` ("The four relationships. At filing, look for each:", with a "When on your own" column: dependency "always", duplication, composition, and contradiction "only when very confident") and `skills/use-bd/SKILL.md` "Otherwise raise it with the user (unattended: report it)."
- Earliest form: `docs/projects/use-bd/v1-proposal.md`, commit ee85c50 (2026-10-08, "use-bd design: what must never happen (Anti-goals exit)"): "**Unilateral relationships.** Agents add dependencies they find at filing time on their own; contradiction, duplication, and composition only when very confident, and otherwise raise them (or, unattended, report them)." The "four relationships" wording first appears in commit 74ce46f (2026-10-09). The r6b restatement is unchanged.
- Provenance: ratified via the use-bd home-in design (agent-tooling-aio: "The design is settled in docs/projects/use-bd/v1-proposal.md (home-in session 2026-10-07 to 2026-10-09)"). r6b only restates it.

### F16: A pick-up point is a state doc, rewritten in place; a running record is a stream doc, appended
- Category: lifecycle / docs-linkage
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-aio`, NOTES): "2026-09-25 session three (job f8e97923), user ruling: the skill should standardize how an issue's notes field is used as a pick-up point. Observed on the phase-one epic (agent-tooling-w7p): its notes grew stream-style (a pick-up note, a second note superseding it, then three addenda), so a reader must replay five entries to get the current state. Distinguish the two kinds: a pick-up point is a state doc and is rewritten in place each session; a friction log or running record (as on w7p.4) is a stream doc and grows by appending. Decide which field carries which (notes versus design versus a dedicated child), and how a rewrite preserves provenance (history lives in the issue's event history, not in the body)."
- Earliest form: this note, 2026-09-25. The current skill settles the field question: `skills/use-bd/SKILL.md:196-199` "An Issue's description is its state: rewrite it in place (`--body-file`) so it always reads as the current picture, including a `## Pick-up` section that tells the next session where the work stands. Notes and comments are its log: append, never rewrite." That is drift in placement only: the ruling said "notes field ... as a pick-up point", and the skill moved the pick-up to the description.
- Provenance: ratified ("user ruling"). The choice of field is agent-settled; I could not find a ruling on it in this source group.

### F17: Reason about recency or staleness from exact timestamps, not rendered dates
- Category: triage (staleness)
- Generic or specific: mixed. The generic part: compare exact instants against the current time. The specific part: `bd show` renders UTC dates.
- Current text (verbatim, `bdw show agent-tooling-aio`, NOTES): "2026-09-25 session three (job f8e97923), user ruling: the skill must warn agents that bd show renders Created and Updated as UTC calendar dates with no local conversion (not configurable in 1.3.0; TZ ignored), so a date can read one day ahead of local time in the evening. Agents reasoning about recency or staleness use the exact UTC instants in the JSON output of bd show and compare against the date command, never the rendered date."
- Earliest form: this note, 2026-09-25. Not traced further, since it is mostly a tool quirk.
- Provenance: ratified ("user ruling").

### F18: Never claim an epic: it is a container, and its work is its children (SUPERSEDED)
- Category: lifecycle / breakdown
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-aio`, NOTES): "2026-09-25 session three (job f8e97923), user ruling: the skill carries these epic conventions ... (b) Never claim an epic; it is a container and its work is its children. (c) Close an epic individually once its children are closed, or run bd epic close-eligible only after its dry-run form ..." It also survives in the w7p pick-up note's "Standing rules for agents on this repo": "find work with the ready verb plus the epic type exclusion; never claim an epic."
- Earliest form: this note, 2026-09-25. Reversed later by ADR 0009 (dated 2026-10-08, `docs/adr/0009-branch-issues-are-worked-in-passes.md`): "A Branch Issue is ready work exactly when it has no open children, and each claim on it is one session-sized pass that ends either by adding children or by verifying completion and closing it." Also "A Branch Issue is never closed merely because its children closed; a pass verifies it first." Its rejected alternative "Branch Issues as passive containers" is exactly rulings (b) and (c).
- Provenance: ratified as a "user ruling" on 2026-09-25, then superseded by ratified ADR 0009. Neither the aio note nor the w7p note has been marked superseded (see Contradictions C1).

### F19: Branch Issues are worked in passes; only branch kinds take children; a Branch Issue with open children cannot be claimed
- Category: breakdown / lifecycle
- Generic or specific: mixed. The generic part is the pass model of ADR 0009. The specific part is bdw's ready query and its claim refusals.
- Current text (verbatim, `bdw show agent-tooling-aio.4`, DESCRIPTION): "bdw's own ready (tier 3 of ADR 0010): Leaf Issues with no open blockers, and Branch Issues with no open children; never a Branch Issue with open children." "Refuse to claim a Branch Issue that has open children." "When the session holding a Branch Issue's claim adds children to it, release the claim in the same call". "Refuse to add a child to an Issue that is not of a branch kind, with a refusal that teaches the sibling-plus-dependency form or retyping".
- Earliest form: ADR 0009, 2026-10-08. aio.4 was filed 2026-10-10 and is still open (not built).
- Provenance: ratified (ADR 0009).

### F20: Always state the relationship type; a wrong blocking edge silently hides work
- Category: relationships
- Generic or specific: mixed. The generic part: make the relationship type explicit, because blocking edges hide work from the ready queue. The specific part: `bd dep add` defaults to blocks.
- Current text (verbatim, `bdw show agent-tooling-aio`, NOTES): "2026-09-26 session three (job f8e97923), items for the skill, user-approved: (a) Dependencies: bd dep add defaults to a blocks edge, which hides the dependent from bd ready, and the warning prints only to a terminal; always pass the type explicitly (related, discovered-from, blocks) and treat a bare dep add as a bug". Same ruling: "(d) Link children with the parent flag only; never add a blocks dependency from a parent to its own children, which deadlocks silently (upstream #6506)."
- Earliest form: this note, 2026-09-25 and 2026-09-26. The current skill (`skills/use-bd/SKILL.md`) keeps it: "Always pass `--type` to `dep add`: bare, it creates a blocking edge, and a wrong blocking edge silently removes work from `bdw ready`."
- Provenance: ratified ("user ruling" and "user-approved").

### F21: Heartbeat held claims (SUPERSEDED by "the lease procedure is open")
- Category: lifecycle / agent-vs-human
- Generic or specific: specific (Beads leases). Included because the 2026-10-24 ruling reopened it.
- Current text (verbatim, `bdw show agent-tooling-aio`, NOTES): "(b) Heartbeat: bd heartbeat is allowed by the command policy and leases live in a node-local table that writes no history, so heartbeating at every loop step costs nothing; prescribe it wherever a claim is held across long work". Later, `bdw show agent-tooling-3lo`, DESCRIPTION: "The maintainer ruled (2026-10-24) that the intended lease procedure is itself open for design and discussion here: this Issue does not prescribe a solution."
- Earliest form: 2026-09-26 ("user-approved"). Reopened 2026-10-24.
- Provenance: ratified, then reopened by a later ruling. Note also `skills/use-bd/SKILL.md:87-88`: "A claim never outlives its session: continuity lives in the Issue's pick-up section and metadata, never in a claim."

### F22: An Issue's kind lives in the tracker's native type field, not in a label, with consistent kinds across repos
- Category: labels-priority / setup
- Generic or specific: mixed. The generic part: record kind once, in the native field, and keep the kinds consistent across repos. The specific part is the Beads type mapping.
- Current text (verbatim, `bdw show agent-tooling-aio.7`, DESCRIPTION): "In Beads an Issue's kind lives in its native type field, so these labels duplicate (or contradict) the type. Convert them and retire the labels, as the maintainer decided on 2026-10-09: • bug -> type bug; feature -> type feature • improvement -> type feature (Beads' feature is "new feature or enhancement") • debt -> type chore • meta -> a new custom type meta (design documents, planning, non-code project work), since no built-in type covers it (decision is ADRs only)". Acceptance: "use-bd's onboarding.md tells new repos to register the same custom type, so kinds stay consistent across repos."
- Earliest form: aio.7 created 2026-10-10, recording a decision of 2026-10-09. The current skill: `skills/use-bd/SKILL.md:140` "**Kind goes in the type field** ... never in a label."
- Provenance: ratified ("as the maintainer decided on 2026-10-09"). The cross-repo consistency criterion is probably agent-elaborated (it sits in the acceptance criteria, not in the decision).

### F23: Templated phases for Branch Issues: evaluate them, deferred
- Category: breakdown
- Generic or specific: mixed. The generic part is a standard phase list for Branch Issues. The specific part is Beads formulas.
- Current text (verbatim, `bdw show agent-tooling-sn6`, DESCRIPTION): "Evaluate Beads formulas (bd formula, bd cook, bd mol pour) as templates that stamp out a Branch Issue's standard phases (e.g., scoping, product design, engineering design, implementation, testing, rollout), and decide whether to adopt them. In scope for the use-bd work, deferred from the first shipment (maintainer ruling, 2026-10-09, use-bd home-in, agent-tooling-aio)." Done when: "whether templated phases earn their complexity".
- Earliest form: sn6 created 2026-10-09. Unchanged.
- Provenance: the deferral is ratified ("maintainer ruling"). The phase list is unknown: it is an "e.g." and could come from either the maintainer or the agent. The phase list resembles triage-issues' states (Needs Scope, Needs Eng Design, Needs Impl).

### F24: Is closing an Issue or PR an agent act or a human-confirmed one? (OPEN)
- Category: closing / agent-vs-human
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-k6z`, DESCRIPTION): "Is a close an ordinary reversible act that needs only a reason, with triage's restriction scoped to its unattended passes, or a judgement the human confirms everywhere, in which case use-github and fjw should say when an agent may close? Probably not ADR-worthy." Evidence it cites: "Agent act: ghw-issue-close closes on a grant ... bdw close is allowed to sessions" against "Human-confirmed: triage proposes every close and waits for a human ... interactive passes included, with no reason beyond its bounded-autonomy rule", and "Sub-agents may not close Beads Issues ... but nothing stops them closing a GitHub issue or a Forgejo PR."
- Earliest form: k6z created 2026-10-12 from `docs/audits/2026-10-11-agent-versus-human-line.md` inconsistency 2. Unchanged.
- Provenance: open decision. No ruling yet. The framing is agent-elaborated (by the audit).

### F25: Every close carries a comment, the audit record; forge auto-close on PR merge is the one exception
- Category: closing
- Generic or specific: generic. Shipped for ghw and planned for fjw.
- Current text (verbatim, `bdw show agent-tooling-75z`, DESCRIPTION): "The fjw issue-Verbs proposal makes fjw-issue-close's comment mandatory (the comment is the audit record: "done because X, see commit Y") and states the rule is meant to hold across Wrapper families, with forge auto-close on PR merge as the one sanctioned exception." Shipped in `skills/use-github/SKILL.md:216-219`: "the comment file is required: the close carries its reason in one call, and a missing or blank comment is exit 2. The forge's auto-close on PR merge is the one sanctioned comment-less close."
- Earliest form: `docs/projects/fjw/issue-verbs.md`, commit edd9853 (2026-10-01, "docs: migrate the fjw and installer project docs; add ADR 0007"). 75z (created 2026-10-01) carried it across to ghw, and it shipped in PR #88.
- Provenance: unknown, leaning agent-elaborated. It came from a migrated design proposal. 75z's mandate is a maintainer request, which asked for filing, not for this rule. Follow-up agent-tooling-0fm (open): "The completed / not planned reason is carried, or the decision not to is recorded."

### F26: Sub-agents may not claim, close, or rewrite Beads Issues; the stated reason is in question (OPEN)
- Category: agent-vs-human
- Generic or specific: generic (whether a delegated agent may take ownership acts)
- Current text (verbatim, `bdw show agent-tooling-i4e`, DESCRIPTION): "use-bd forbids sub-agents to claim, close, or rewrite because "a sub-agent's environment cannot be told from its parent's"". "If the reason is attribution, it applies to every write; if it is that a claim asserts ownership a shared Actor cannot prove, the ban is narrower and its stated reason should say so." Decision needed: "Is the ban about attribution ... or about ownership"?
- Earliest form: i4e created 2026-10-12 (from audit inconsistency 8).
- Provenance: the ban is shipped in use-bd. Its reason is an open decision.

### F27: What "unattended" means (OPEN in Beads)
- Category: agent-vs-human
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-7kn`, DESCRIPTION): "found three definitions in use: • The prompt says so: use-lexicon treats a session as unattended only if its prompt says "unattended" ... • A background job: the Actor is claude-job-<id> in a background job and attended-<user> otherwise ... • No dialogue possible: triage's unattended mode is headless". Decision needed: "Which definition governs, and should Attended and Unattended become lexicon terms every Skill uses".
- Earliest form: 7kn created 2026-10-12.
- Provenance: open in Beads.

### F28: Must agent acts on a forge be distinguishable from the user's? (OPEN)
- Category: agent-vs-human
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-0vm`, DESCRIPTION): "Should agent acts on a forge be distinguishable from the user's, as fjw decided, and if so is a machine account, a body marker, or nothing the GitHub answer? Likely passes the ADR gate for GitHub." Evidence: on GitHub "triage's mutations are "indistinguishable from genuine manual activity" (skills/triage-issues/SKILL.md:402); no passage records this as a decision."
- Earliest form: 0vm created 2026-10-12.
- Provenance: open decision.

### F29: One canonical per-repo config home for the label schema and the triage config (OPEN)
- Category: setup / labels-priority
- Generic or specific: mixed (whether per-repo tracker conventions live in one committed place, plus the ghw staging mechanics)
- Current text (verbatim, `bdw show agent-tooling-wx5`, DESCRIPTION): "Decide one canonical per-repo home that serves both: where it lives, its format, which Verbs and wrappers read it, how it squares with invariant 9 (a committed in-repo file is not a staging path, and the schema's names and descriptions get published), and whether it counts as policy under the Permission-rules statement or only as data."
- Earliest form: wx5 created 2026-10-01.
- Provenance: open decision. A parallel exists on the Beads side (aio.6's `.beads/bdw.json`, "Conventions only: it may steer what bdw itself does ... but never touches the Permission rules").

### F30: If agents swarm it, use Beads; long-lived, low-churn, or human-driven work belongs on an issue host
- Category: setup
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-ze3`, DESCRIPTION): "Maintainer ruling, 2026-10-16, at the end of the Beads trial: Beads' one real advantage over a hosted issue tracker is agent-native operation (a computed ready queue, single-owner claims, per-session Actors, no forge round-trip). Ownership and self-hosting argue for Forgejo as much as for Beads. So the rule is: if agents swarm it, Beads; for long-term, low-churn, or human-driven work, an issue host. Some projects need both."
- Earliest form: ze3 created 2026-10-16. Recorded as ADR 0011 ("Beads tracks agent-swarmed work; long-lived work belongs in forge issues"), per the agent-tooling-0pe close reason.
- Provenance: ratified (maintainer ruling plus ADR 0011).

### F31: One writable home per Issue at any moment; moving an Issue between trackers is an explicit, visible transfer
- Category: setup / lifecycle
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-ze3`, DESCRIPTION, "## Requirements (high level)"): "**One writable home per Issue at any moment.** Moving an Issue between the host and Beads is an explicit transfer, visible on both sides; there is never a period where both copies take edits." Also: "**A human reading the host can follow along** without opening Beads." Also: "**Through the wrappers.** Every write goes through the ghw/fjw and bdw wrappers and the Permission rules, with the Actor recorded; no raw sync." Non-goal: "Continuous bidirectional sync, or per-field conflict resolution. ADR 0001 and docs/projects/beads-trial/design.md record why two live writable trackers were rejected."
- Earliest form: ze3, 2026-10-16. Unchanged.
- Provenance: mixed. The no-two-live-trackers part is ratified (ADR 0001, cited). The rest of the requirements list is unattributed. The epic "records the requirements only" and its acceptance criterion is "A scoping pass turns these requirements into a ratified design", so I read the list as agent-drafted from the ruling and not yet ratified.

### F32: GitHub Issues are stale copies: nothing filed, edited, or closed there until the long tail moves back
- Category: setup / closing
- Generic or specific: specific to this repo, but it states a generic rule: a tracker that holds stale copies takes no writes
- Current text (verbatim, `bdw show agent-tooling-0pe`, CLOSE REASON): "Per the maintainer's ruling, GitHub Issues was neither wound down nor refiled: it stays enabled with the imported issues open until the long tail moves back (agent-tooling-ze3)." Comment on pinned GitHub issue #18 (the pinned freeze-announcement issue, quoted in `bdw show agent-tooling-0pe`, COMMENTS): "**GitHub Issues stays enabled, but takes no new work until then.** Nothing here is filed, edited, or closed in the meantime." Also: "**Pull requests are unaffected.** PR bodies name the Beads issue they land (Lands agent-tooling-xyz)."
- Earliest form: 0pe was created 2026-10-01 with a different plan: "4. **On go**: the maintainer closes every open GitHub issue with a pointer to its Beads replacement through ghw-issue-close, then disables GitHub Issues in the repo settings." The 2026-10-16 ruling reversed that plan.
- Provenance: ratified (maintainer ruling 2026-10-16; ADR 0011).

### F33: The verdict, and the announcing comment, are the maintainer's; agents draft
- Category: agent-vs-human
- Generic or specific: generic (decisions belong to the human; agents draft them)
- Current text (verbatim, `bdw show agent-tooling-0pe`, DESCRIPTION): "That comment is the deliberate unfreeze act and the one sanctioned write to frozen GitHub Issues. It is a maintainer act, not agent work." "Precondition: the verdict itself is the maintainer's; an agent drafts the ADR from the friction log (agent-tooling-w7p.4) and the phase-one epic (agent-tooling-w7p)." The same stance appears in `bdw show agent-tooling-xla`, DESCRIPTION: "Proposes, for each inconsistency, which side should give, as a question for the maintainer rather than a change. The decisions themselves are the maintainer's". It also says "this Issue closes when the audit document is on main, not when the decisions are made."
- Earliest form: 0pe, 2026-10-01; xla, 2026-10-11.
- Provenance: unknown, leaning ratified. 0pe derives it from "the ratified phase-two proposal (docs/projects/beads-trial/phase-two.md)". The xla wording is the ask written into the Issue. Note: the #18 comment is in fact authored by `claude-job-6f526271` (the agent posted the maintainer's drafted comment).

### F34: Issue text is self-contained and publishable-grade, with no private path beyond the front door
- Category: filing
- Generic or specific: generic (self-contained issue text). Knowledge-base-specific in its privacy clause.
- Current text (verbatim, `bdw show agent-tooling-eta`, DESCRIPTION): "Constraints: issue text is self-contained and publishable-grade, with no upstream path beyond the front door." Also, from w7p's "Standing rules for agents on this repo" (`bdw show agent-tooling-w7p`, NOTES): "No [knowledge base] path beyond the front door in issue text."
- Earliest form: eta, created 2026-09-27, "a draft ratified in outline by the maintainer on 2026-09-26".
- Provenance: ratified in outline (eta: "ratified in outline by the maintainer on 2026-09-26. It is not final").

### F35: Bulk backlog conversion: one verdict per TODO, a merger dedupes, the maintainer reviews, one serial filer
- Category: filing / breakdown / relationships / agent-vs-human
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-eta`, DESCRIPTION): "Every TODO gets one verdict: file (type, title, self-contained body citing in-repo docs, proposed dependencies), already covered by an existing issue (cite it), done in code (clean up upstream), stays upstream, or needs a maintainer ruling. No writes to Beads." "Merger: one subagent reads all the proposal files. It dedupes across projects, wires the dependencies across projects, and writes one unified plan file for the maintainer to review. The plan is a full document, not a list of IDs, because a person has to review it." "Filer: one subagent files the approved issues serially through bdw, one writer at a time. It sets explicit dependency types, uses the epic type for work that needs further decomposition, and validates the resulting graph." Also: "Only meta-level or privacy-sensitive TODOs stay upstream."
- Earliest form: eta, 2026-09-27. The note of 2026-10-01 adds: "Proposers should treat those as existing Issues when deduplicating."
- Provenance: ratified in outline (2026-09-26), "not final: revisit it when the gate clears".

### F36: Every filing is one validated plan, with a near-duplicate search and an echo of what left the ready queue
- Category: filing / relationships
- Generic or specific: mixed. The generic part: validate structure before submitting, search for duplicates, and show the effect on ready work. The specific part: `bd create --graph`, the denied create paths.
- Current text (verbatim, `bdw show agent-tooling-aio.5`, DESCRIPTION): "every filing goes through a graph plan (the JSON bd create --graph understands; one Issue is a one-node plan). Before submitting, bdw validates the plan (parent kinds, dependency types), searches for near-duplicates, reports bd lint findings as warnings, and after submitting echoes what left ready work (built on ready --explain). Draft, preview with dry-run, submit."
- Earliest form: `docs/projects/use-bd/v1-proposal.md`, commit 733d6d4 (2026-10-09, "use-bd design: filing through a validated plan file; advisory lint"). aio.5 was filed 2026-10-10 and is still open.
- Provenance: ratified via the use-bd home-in design (agent-tooling-aio, "The design is settled").

### F37: Per-repo conventions (label scheme, link keys, Docs Inbox) are declared data; Permission rules alone decide what agents may run
- Category: setup / labels-priority / docs-linkage
- Generic or specific: mixed. The generic part: conventions are separate from policy, and labels are checked against a declared scheme. The specific part: `.beads/bdw.json`.
- Current text (verbatim, `bdw show agent-tooling-aio.6`, DESCRIPTION): "The repo's structured Beads conventions file, .beads/bdw.json ...: the label scheme, extra document link keys, the Docs Inbox path. Conventions only: it may steer what bdw itself does (e.g., which labels the filing Verb accepts) but never touches the Permission rules, which alone decide what an agent may run." "Label checks against the declared scheme in the filing Verb and on label changes." "The Docs Inbox Verb (tier 3): drop material in the repo's Docs Inbox and file a Leaf Issue to incorporate it, with the link recorded as metadata."
- Earliest form: the use-bd v1 proposal ("One Skill, many repos"), October 2026 home-in. aio.6 filed 2026-10-10.
- Provenance: ratified via the use-bd home-in design.

### F38: One way for a commit to name its Issue, and whether "lands" differs from "touches" (OPEN)
- Category: todo-comments / docs-linkage
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-nbj`, DESCRIPTION): "CLAUDE.md ("Issue tracking & workflow") says how a TODO comment cites an Issue (TODO(agent-tooling-xyz)) and how a PR body names the Issue it lands (Lands agent-tooling-xyz). It says nothing about how a commit message names its Issue. Codify that." "Does the trailer replace Lands ... / Refs ... / Toward ...? Or does it sit beside a Lands-vs-Refs distinction (does this commit complete the Issue or only touch it)?" "A trailer named Bead: bakes the trial's tool into permanent history".
- Earliest form: nbj, 2026-10-01. The TODO rule now lives in `.beads/PRIME.md:22` ("**`TODO` comments** cite the Issue ID (`TODO(agent-tooling-xyz)`).") rather than CLAUDE.md, so nbj's pointer to CLAUDE.md is stale.
- Provenance: open decision. The TODO and PR-body forms are this repo's current conventions.

### F39: Every Issue goes through the creation Verb with its type and area labels, the triage ledger included (OPEN)
- Category: filing / labels-priority
- Generic or specific: mixed (GitHub-specific in detail)
- Current text (verbatim, `bdw show agent-tooling-5kf`, DESCRIPTION): "The one-time triage bootstrap creates the ledger issue with raw gh issue create, the only GitHub write in the ghw ecosystem's documented flows that bypasses a Verb." "Decide first: which type label (likely meta) and which area: label the ledger takes, and whether every bootstrapped repo's label schema must then include that area (a setup-github-issues change) or ghw-issue-create grows a narrow exception."
- Earliest form: 5kf, 2026-10-01.
- Provenance: open decision.

### F40: Requests that should be Issues should be filed as Issues through a sanctioned path, not transcribed from mail (design item)
- Category: filing / setup
- Generic or specific: generic (an outside consumer gets a read path and a sanctioned filing path, with Actor attribution)
- Current text (verbatim, `bdw show agent-tooling-137.2`, DESCRIPTION): "requests that should be Issues arrive as mailbox Messages that a repo session must transcribe by hand". "**A sanctioned filing path**: a request that today becomes a mailbox Message becomes an Issue directly, with the right Actor attribution and within the Permission rules (writes through bdw)."
- Earliest form: 137.2, 2026-10-01.
- Provenance: the placement is ratified ("Child of agent-tooling-137 ..., ruled by the maintainer 2026-10-01"). The "Wanted" content is agent-elaborated.

### F41: Should every act a skill calls human-only carry an explicit ask or deny rule? (OPEN)
- Category: agent-vs-human
- Generic or specific: generic
- Current text (verbatim, `bdw show agent-tooling-4l0`, DESCRIPTION): "Should every act a Skill calls human-only carry an explicit ask or deny row in the rules this repo ships or recommends (README minimum, the Beads spec), so the gate survives auto mode and a later broad allow? If so, which acts? Likely passes the ADR gate."
- Earliest form: 4l0, 2026-10-12.
- Provenance: open decision.

### F42: Unattended triage is safe only if its permission boundary equals its autonomy boundary
- Category: triage / agent-vs-human
- Generic or specific: generic principle with a specific mechanism
- Current text (verbatim, `bdw show agent-tooling-ys3`, DESCRIPTION): "An unattended triage pass is safe only because its permission boundary equals its autonomy boundary: it runs --permission-mode dontAsk with only the six triage-* wrappers granted."
- Earliest form: ys3, 2026-10-01, which cites `docs/projects/ghw/design.md` "Unattended triage". Not traced further: it belongs to another reader's sources.
- Provenance: agent-elaborated (restates the ghw design; no ruling in this Issue). Related open decision: agent-tooling-4zm, "Is "bounded output, target named by an in-repo profile" enough to justify a user-level write grant?"

---

## Platform-specific mechanics

One line each, not traced:
- Beads custom statuses: `status.custom`, each with a category of active, wip, done, or frozen (c86).
- `bd lint` is type-dependent only, with validation only on create and close (`validation.on-create`, `validation.on-close`) and no status-dependent rules in 1.3.0 (c86).
- Stopgap: `validation.on-create` stays off, and the filing Verb's dry run reports `bd lint` findings as warnings only (c86).
- `bd ready` in 1.3.0 lists open epics as ready, so use `--exclude-type epic` (aio note, 2026-09-25; upstream #5583).
- `bd epic close-eligible` closes every eligible epic at once, so run its dry-run form first; `bd epic status` shows per-epic progress (aio note).
- A blocks edge from a parent to its own child deadlocks silently, so link children with the parent flag (aio note; upstream #6506).
- `bd heartbeat` leases live in a node-local table that writes no history; a claim sets `lease_expires_at` 5 minutes ahead; `bd reclaim` is denied (aio note, 3lo).
- `.beads/PRIME.md` replaces `bd prime`'s default text (aio note, 2026-09-26).
- `bd show` renders dates in UTC; use the JSON instants (aio note).
- Beads type mapping: bug to bug, feature and improvement to feature, debt to chore, meta to custom type `meta` via `config set types.custom`, which is ask-ruled (aio.7).
- The four relationships map to Beads as dependency to `blocks`, duplication to `duplicate --of`, composition to `parent-child`, and contradiction to `relates-to` plus a label (v1-proposal; r6b cites it).
- The filing Verb `bdw file graph` takes `bd create --graph` JSON; other creation paths (create forms, q, todo, `create -f`, link, parent-child `dep add`) are denied (aio.5).
- File forms for inline-only bd fields: title, acceptance criteria, notes replaced, and the defer, unclaim, and human-dismiss reasons (aio.6).
- Name flags in words inside issue text, because the actor-flag deny row matches literal text; notes that name the VCS go through files (w7p standing rules; agent-tooling-9nx).
- `ghw-issue-close` requires a comment file, and a missing or blank one is exit 2; `fjw-issue-close` is planned the same way (75z).
- Triage closes still use raw `gh issue close --reason completed|"not planned"` (0fm, open bug).
- The ghw label-sync schema file lives only in staging, while TRIAGE.md is committed with a JSON config block (wx5).
- `ghw-issue-create` requires exactly one type label and at least one `area:` label (5kf).
- Unattended triage runs `--permission-mode dontAsk` with only the six triage-* wrappers granted (ys3).
- Beads formulas (`bd formula`, `bd cook`, `bd mol pour`) produce a poured root of type molecule (sn6).

---

## Contradictions

**C1. "Never claim an epic" and "close an epic once its children close" against ADR 0009.**
- `bdw show agent-tooling-aio`, NOTES (2026-09-25, "user ruling"): "(b) Never claim an epic; it is a container and its work is its children. (c) Close an epic individually once its children are closed".
- `docs/adr/0009-branch-issues-are-worked-in-passes.md:17`: "A Branch Issue is never closed merely because its children closed; a pass verifies it first." The ADR's Decision: "each claim on it is one session-sized pass". Its rejected alternative "Branch Issues as passive containers" is ruling (b) and (c).
- The ADR is later and ratified, so it governs. The aio note has no superseded marker. The w7p pick-up note's "Standing rules for agents on this repo" still says "never claim an epic" (`bdw show agent-tooling-w7p`, NOTES, as of 2026-10-01). An agent reading either Issue is told the opposite of the ADR.

**C2. Where the pick-up point lives: notes against description.**
- `bdw show agent-tooling-aio`, NOTES (2026-09-25 ruling): "the skill should standardize how an issue's notes field is used as a pick-up point ... a pick-up point is a state doc and is rewritten in place each session".
- `bdw show agent-tooling-w7p`, NOTES: "Pick-up point, as of 2026-10-01 (job 4d3f379c). Rewritten in place per the user ruling that a pick-up point is a state doc". That is a NOTES field rewritten in place.
- `skills/use-bd/SKILL.md:196-199`: "An Issue's description is its state ... including a `## Pick-up` section ... Notes and comments are its log: append, never rewrite."
- The skill's rule (description holds the state; notes are append-only) contradicts the field the ruling named and the practice on w7p. The ruling itself left the field open ("Decide which field carries which").

**C3. Exit requirements per state against requirements at filing.**
- `bdw show agent-tooling-c86`: "each state has exit requirements, checked when an Issue moves on, rather than requirements checked at creation". It also puts "labels conforming to the project's scheme" at needs_triage exit and "acceptance criteria (Leaf Issues)" at needs_scope exit.
- `skills/use-bd/SKILL.md:142`: "every Issue has at least one area label". `skills/use-bd/SKILL.md:146`: "**Description:** what and why, then a `## Acceptance Criteria` section." The v1 proposal adds "**No empty Issues.** `create.require-description` is on".
- These are not formally in conflict: c86 is an unratified sketch, and the use-bd rules are filing discipline in a skill, not enforced validation. But a generic use-issues layer must choose whether the label and acceptance-criteria requirements apply at filing or at a later state exit. The sketch's motive ("capture during flow is never blocked") argues for state exit.

**C4. Closing: agent act or human-confirmed (open; agent-tooling-k6z).**
- `skills/use-github/SKILL.md:216-219` shows closing as an ordinary granted Verb with a required comment. `bdw show agent-tooling-k6z` adds that "bdw close is allowed to sessions".
- `skills/triage-issues/SKILL.md:132`: "reparenting, tracker creation, and especially issue-closing await human confirmation." Also `skills/triage-issues/SKILL.md:197-198`: "→ `Done` (rare; ... needs human OK)" and "→ `Rejected` (... needs human OK)".

**C5. Heartbeating: prescribed, then reopened.**
- `bdw show agent-tooling-aio`, NOTES (2026-09-26, "user-approved"): "prescribe it wherever a claim is held across long work". The same rule appears in w7p's standing rules: "Heartbeat held claims; it is policy-allowed and writes no history."
- `bdw show agent-tooling-3lo` (2026-10-24 ruling): "the intended lease procedure is itself open for design and discussion here". The same Issue says the skill text "never mentions that every claim carries a lease ... An agent following the loop as written never heartbeats."

**C6. Three definitions of "unattended" (open; agent-tooling-7kn).**

**C7. The u9n sketch names skills that do not exist.** "setup-bd" and "use-github-issues" appear in `bdw show agent-tooling-u9n`. The actual units are `skills/use-bd/onboarding.md` (setup inside use-bd) and `skills/use-github` (which also covers PRs). Probably shorthand, but the requirements step should not read it as a rename instruction without asking.

**C8. Kind as a native field against kind as a label.** aio.7 (ratified): "In Beads an Issue's kind lives in its native type field, so these labels duplicate (or contradict) the type." GitHub side: `skills/triage-issues/SKILL.md:88` "R-LABEL-1: Every issue must have **exactly one** label from the profile's *type* family", and `ghw-issue-create` requires one type label (5kf). This is a platform difference, not a conflict, as long as the generic rule is "record kind once, in the tracker's native mechanism".

**C9. The original trial-end plan against the ruling.** agent-tooling-0pe's description (2026-10-01): "On go: the maintainer closes every open GitHub issue ... then disables GitHub Issues". The ruling of 2026-10-16 and the #18 comment: "Nothing here is filed, edited, or closed in the meantime." The close reason records the reversal, so this is resolved, but the description was never rewritten.

---

## Judgement calls

1. **Four provenance labels instead of three.** The brief asks me to separate a sketch "raised by the maintainer, not ratified" from a ruling. Neither "ratified" nor "agent-elaborated" fits such a sketch, so I used "sketch (raised, not ratified)" as its own label.
2. **Rulings transcribed by agents count as ratified.** Every Issue was written by an agent job. Text labelled "user ruling", "maintainer ruling", "user-approved", or "the maintainer decided" counts as ratified. Nearby unattributed prose (Why sections, "Likely shape", requirements lists) counts as agent-elaborated, even when it is in the same Issue.
3. **No drift tracing inside Issues.** `bdw history agent-tooling-u9n` lists 704 snapshots with no field diffs. Diffing them is impractical, and the brief allows read-only access only. So "Earliest form" for Beads-only text is the Issue's creation date. Where the principle also lives in repo files, I traced it with `git log -S` (commits ee85c50, 74ce46f, 733d6d4, edd9853).
4. **Search scope.** `bdw search` matches titles and IDs only (`skills/use-bd/SKILL.md:134`), so `bdw search breakdown` and `bdw search duplicat` found nothing. The only description search I ran was the brief's `bdw list --desc-contains=maintainer --all`, which returned 77 Issues. From those I read the ones whose titles concern issue handling: 0fm, i4e, ze3, 4l0, 75z, nbj, 5kf, 0pe, xla, 137.2, aio.1, aio.4 through aio.7, 3lo, sn6, jat, w7p, 4zm, ys3, eta, and j6x. I skipped Issues about wrappers, exit codes, git, the installer, and push mechanics. j6x, aio.1, xla's body, and the w7p.4 friction log yielded no new issue-handling principle, except as noted in F33. I did not read w7p.4 (the friction log), since its findings feed other sources.
5. **Repo files used only for cross-reference.** I quoted from the repo (`skills/use-bd/SKILL.md`, `docs/projects/use-bd/v1-proposal.md`, ADR 0009, `skills/triage-issues/SKILL.md`, `skills/use-github/SKILL.md`) only to trace history or to show a contradiction. Those files are other readers' primary sources.
6. **Out of scope.** I left out the trial-verdict rulings in 0pe's notes (the attribution rule for friction, "The trial tests Beads run well"). They are about evaluating Beads, not about how agents use Issues.
7. [omitted: private source]

Weird things to flag:
- agent-tooling-u9n.1 (the scoping task for this very extraction) is claimed IN_PROGRESS by this session's Actor, with a 5-minute lease. It will lapse while the extraction runs, and as a read-only reader I did not heartbeat it.
- agent-tooling-nbj still points to CLAUDE.md for the `TODO(...)` rule, which has since moved to `.beads/PRIME.md:22`.
