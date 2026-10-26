# Extract D: use-bd skill, .beads/PRIME.md, Beads project docs

> This document captures state as of 2026-10-26. For current state, see [docs/index.md](../../index.md).

Source group D, read 2026-10-26 at `main` = 2bf1ca6. Paths are relative to
the repo root. Abbreviations:
`SKILL` = skills/use-bd/SKILL.md, `QUIRKS` = skills/use-bd/quirks.md,
`ONB` = skills/use-bd/onboarding.md, `PRIME` = .beads/PRIME.md,
`PROP` = docs/projects/use-bd/v1-proposal.md (dated 2026-10-09, "ratified in a
home-in session (2026-10-07 to 2026-10-09)", PROP:8-9), `UBD` =
docs/projects/use-bd/index.md, `BTI`/`BTD` = docs/projects/beads-trial/index.md
and design.md, `EPIC` = Beads epic agent-tooling-aio (use-bd skill), whose
notes carry three dated "user ruling" entries from 2026-09-25/26.

Provenance key used below: **ratified** = stated in an ADR, in the home-in
output (PROP, or the home-in design commits 2bbf978..30a2ed7 on
2026-10-07..09, all by job claude-job-521331be), or in a note recorded as a
"user ruling"/"maintainer ruling"/"raised by the maintainer". **agent-
elaborated** = first appears in the v0 Skill (a46755f / 0665cd7, 2026-10-09)
or later with no ruling behind it. Nearly all of SKILL.md is unchanged from
its first commit a46755f (2026-10-09, "use-bd v0: the guidance-only Skill and
its project docs"); later commits touched only push/exit/permission
mechanics. So for most principles the real history is in the home-in design
commits that preceded the Skill.

---

## Principles

### D1: A denied call is the policy working; a blocked normal path is a gap to report
- Category: agent-vs-human
- Generic or specific: mixed (generic: do not route around a refusal, report the gap; specific: `bdw`, prefix rules, exit codes)
- Current text (verbatim, with path:line): "**A denied call is the policy working.** Do not look for another spelling of it. If the normal path for a real need is denied or prompts, that is a gap: say so (see Friction, below)." (SKILL:36-38); "A refusal is not something to rephrase around: on exit 4 fix the call or report the gap; on exit 5 stop and report it." (SKILL:48-50)
- Earliest form: 50e29e6, 2026-09-24, "CLAUDE.md: tracking moves to Beads for the trial; GitHub Issues frozen": "Which `bd` subcommands an agent may run is policy in `.claude/settings.json` (allow, ask, deny), not judgment. A denied call is the policy working; do not look for another spelling of it." Drift: the "gap: say so" half was added in v0 (a46755f) and matches PROP success criterion 2.
- Provenance: ratified (the gap half); evidence: PROP:49-54, success criteria 1-2, "The normal path never prompts ... a prompt or denial on routine work is a defect" and "No workarounds ... A real use case with no normal path is a gap to fix." The first half predates the home-in; unknown who authored it, but it was carried into the ratified design.

### D2: The session loop: orient, find ready work, claim before touching, file discoveries linked back, append progress, close on acceptance criteria
- Category: lifecycle
- Generic or specific: mixed (generic: the loop's steps; specific: `prime`, `ready`, `--claim`, `discovered-from`, `gate check`)
- Current text: "1. `bdw prime` at session start, then `bdw gate check` ... 2. `bdw ready` to find work, `bdw show <id>` to read it. ... 3. `bdw update <id> --claim` before touching anything. 4. File what you find along the way as new Issues linked back: `--deps=discovered-from:<id>` (see Filing). 5. Append progress to the Issue as you go (see Free text). 6. `bdw close <id> --reason-file=<path>` when its acceptance criteria hold." (SKILL:74-84)
- Earliest form: 50e29e6, 2026-09-24: "Loop: `bd prime` at session start, `bd ready` to find work, `bd update <id> --claim` before touching code, `bd create --deps=discovered-from:<id>` for anything you find along the way, `bd close <id>` when done, and close or unclaim everything you hold before the session ends." Drift: "before touching code" became "before touching anything"; "when done" became "when its acceptance criteria hold"; "append progress" added (home-in, PROP:78-80).
- Provenance: ratified; evidence: PROP:78-80 "**Version one covers** the loop (prime, ready, claim, file discovered work, append progress to the Issue, close, and land the plane ...)". The pre-home-in loop closely mirrors upstream Beads' own `bd prime` workflow (my inference, not verified against upstream text).

### D3: Land the plane: a claim never outlives its session; continuity lives in the Issue
- Category: lifecycle
- Generic or specific: generic (the claim/unclaim verbs are specific)
- Current text: "**Land the plane.** Before the session ends, close or release (`bdw unclaim <id>`) every Issue you claimed. A claim never outlives its session: continuity lives in the Issue's pick-up section and metadata, never in a claim." (SKILL:85-88)
- Earliest form: e6b9834, 2026-09-24 (ADR 0001 / CONTEXT.md commit): "6. Land the plane: close or unclaim everything you hold before the session ends." Drift: the "continuity lives in the Issue" rationale was added at the home-in (b90e669, 2026-10-08).
- Provenance: ratified; evidence: PROP:337-340 "**A claim never outlives its session.** Before a session ends it closes or releases every Issue it claimed; continuity between sessions lives in the Issue (its pick-up note and metadata), never in a claim. Longer-lived agents would revisit this." PROP:321-323 marks the whole Identity section as "deliberate choices for version one, made around current limitations rather than as lasting architecture".

### D4: Agents that share a session's identity (sub-agents) read, file, and append, but never claim, close, or rewrite
- Category: agent-vs-human
- Generic or specific: mixed (generic: who may change an Issue's state; specific: the reason is that Beads' Actor comes from the session env)
- Current text: "**an agent that shares its session's Actor (a sub-agent, a workflow agent) reads, files new Issues, and appends notes and comments, but never claims, closes, or rewrites an Issue.** The session that holds the conversation does those. An orchestrator puts this rule in every brief it hands down." (SKILL:95-99)
- Earliest form: b90e669, 2026-10-08 (home-in, Success exit): "So an agent without an Actor ID of its own reads, files new Issues, and appends, but never claims, closes, or rewrites; the session that holds the conversation does those. The Skill teaches this, and orchestrators' briefs carry it; `bdw` cannot enforce it." Unchanged in substance.
- Provenance: ratified; evidence: PROP:331-336 (same text). UBD:58-59 lists it as a Known gap: "The sub-agent rule cannot be enforced ... (`agent-tooling-jk2`)."

### D5: Every state change has exactly one owner
- Category: lifecycle
- Generic or specific: generic
- Current text: "4. **Every state change has one owner.** Every claim, close, and rewrite is attributable to exactly one Actor." (PROP:58-59; not stated as such in SKILL)
- Earliest form: b90e669, 2026-10-08; unchanged.
- Provenance: ratified (home-in success criterion 4).

### D6: Never take over someone else's claim; a successful claim does not prove the Issue is yours
- Category: agent-vs-human
- Generic or specific: mixed (generic: never take over a claim, ask; specific: bd's silent re-claim and `attended-<user>` fallback)
- Current text: "So a successful claim does not prove the Issue is yours: if `bdw show` already showed it `in_progress` under your Actor before you claimed it, another agent or session may hold it; stop and ask. ... Never take over someone else's claim (`unclaim --force`, `update --assignee`); ask." (SKILL:104-108); "**A contested claim's message steers to `reclaim`.** ... Do not; ask whoever holds it, or the user." (QUIRKS:16-18)
- Earliest form: a46755f, 2026-10-09: "Attended sessions of one user share one Actor today, so two attended sessions must not work the same Issue. Never pass `--actor`; `bdw` refuses it. Never take over someone else's claim; ask." Drift: the "two attended sessions" sentence was replaced by the claim-proof caveat once bdw derived per-session Actors (aio.2, 2026-10-11).
- Provenance: ratified in intent; evidence: PROP:225-226 asks for "`unclaim --force` and `update --assignee` (taking over a claim, like `assign`)"; PROP:204-209 "**Ask** ... for anything that steps around a `bdw` or `bd` safeguard". The "ask" wording in the Skill is agent-elaborated from that.

### D7: Never reap expired claims
- Category: agent-vs-human
- Generic or specific: mixed (generic: never revert another session's claim because it looks stale; specific: lease/`reclaim`)
- Current text: "`reclaim` reverts claims whose lease expired more than `--older-than` ago to open. Agents never run `reclaim`." (QUIRKS:11-12); rules.json:107 "A lapsed lease is inert until reclaim runs, and sessions sit for hours waiting on a human, so a reclaim would rob live work. Denied rather than asked for, by the maintainer's ruling."
- Earliest form: not traced to its first commit (mechanics-heavy); BTD:88-90 carries the same rationale.
- Provenance: ratified; evidence: rules.json:107 "by the maintainer's ruling".

### D8: Agents choose their next work explicitly; no auto-claim of the next Issue
- Category: lifecycle
- Generic or specific: mixed (generic: the choice of what to work on is the agent's deliberate act; specific: the flags)
- Current text: "**`close --claim-next`, `close --continue`, and `ready --claim` claim the next Issue for you,** skipping the choice of what to work on. Claim explicitly instead." (QUIRKS:31-33)
- Earliest form: f319d19, 2026-10-09 (home-in, "fold in the bd 1.3.0 feature audit"): "deny ... `close --claim-next` and `--continue` and `ready --claim` (they claim around `bdw ready`)" (PROP:220-222). Drift: the rationale shifted from "they claim around `bdw ready`" (i.e., around the planned Branch-aware ready) to "skipping the choice of what to work on".
- Provenance: ratified (the deny); the "choice of what to work on" rationale is agent-elaborated.

### D9: Branch Issue vs Leaf Issue
- Category: breakdown
- Generic or specific: generic
- Current text: "A **Leaf Issue** is a unit of work sized for one session. A **Branch Issue** holds other Issues as children (an epic): its own work is management, scoping it, breaking it down, and verifying it is done." (SKILL:112-114). LEXICON.md (outside this group, cited by PROP:91) defines both, with Branch Issue invariants "ready work exactly when it has no open children; never closed without a pass verifying completion".
- Earliest form: 92ccc6d, 2026-10-08, "LEXICON: add Branch Issue and Leaf Issue"; home-in. Unchanged.
- Provenance: ratified; evidence: EPIC description "the lexicon entries Branch Issue, Leaf Issue, Actor, Actor ID, and Docs Inbox"; ADR 0009.

### D10: Branch Issues are worked in passes; a Branch Issue is ready work exactly when it has no open children
- Category: breakdown
- Generic or specific: generic (the tracker's readiness computation is specific)
- Current text: "It is worked in **passes**, each a session that claims it and ends in one of two ways:" (SKILL:115-116); "**Branch Issues are worked in passes.** A Branch Issue is ready work exactly when it has no open children; each claim on it is one pass that ends by adding children or by verifying completion and closing it. It is never closed merely because its children closed." (PROP:93-96); ADR 0009 Decision: "A Branch Issue is ready work exactly when it has no open children, and each claim on it is one session-sized pass that ends either by adding children or by verifying completion and closing it." (docs/adr/0009-branch-issues-are-worked-in-passes.md:10)
- Earliest form: bf8609a / b90e669, 2026-10-08 (home-in). Unchanged. It REVERSES an earlier user ruling, see Contradictions X1.
- Provenance: ratified (ADR 0009, home-in).

### D11: A breakdown pass drafts the whole breakdown before filing any of it
- Category: breakdown
- Generic or specific: generic (`--parent`, `unclaim` are specific)
- Current text: "**Breakdown.** Draft the whole breakdown first (each child's title, description file, type, labels, and dependencies), then file the children in one sitting with `--parent=<id>`, add the dependencies between them, and release the Branch Issue (`bdw unclaim <id>`). Each child is ready work the moment it exists, so file only what is drafted." (SKILL:118-122)
- Earliest form: b90e669, 2026-10-08: "A pass drafts its whole breakdown before submitting it, as one atomic batch (`bd create --graph`, previewed with `--dry-run`), because the children are ready work as soon as they exist; restructuring afterwards is an ordinary edit made knowing children may be claimed." Drift: the ratified form is one atomic previewed batch (planned filing Verb, aio.5); the Skill's interim form is "in one sitting".
- Provenance: ratified; evidence: ADR 0009 Consequences "Children added in a pass become ready work as soon as they exist, so a pass drafts its whole breakdown before submitting it."

### D12: A verifying pass closes a Branch Issue; never close it because its children closed
- Category: closing
- Generic or specific: generic (`epic close-eligible` is specific)
- Current text: "**Verification.** When every child is closed, check the Branch Issue's own acceptance criteria against the result, then close it or file the children still missing." (SKILL:123-125); "**`epic close-eligible` closes epics because their children closed,** skipping the verifying pass. Never run it." (QUIRKS:21-22)
- Earliest form: b90e669, 2026-10-08. Unchanged. Reverses EPIC user ruling (c), see X2.
- Provenance: ratified (ADR 0009 Consequences: "A Branch Issue is never closed merely because its children closed; a pass verifies it first.")

### D13: Only branch kinds take children; a task that outgrows a session is retyped, not given subtasks
- Category: breakdown
- Generic or specific: generic (the type names are specific)
- Current text: "Only an epic takes children. When a task proves bigger than a session, retype it first (`bdw update <id> --type=epic`) and break it down; otherwise file a sibling Leaf Issue linked by a dependency." (SKILL:127-129)
- Earliest form: b90e669, 2026-10-08: "**Only branch kinds take new children.** ... This is a convenience guard, not a correctness rule: an Issue that somehow gains a child is a Branch Issue by definition and is treated as one. Its job is to stop an agent's habit (subtasks under a task) from silently turning a task in progress into a project; a task that proves bigger than a session is retyped instead." Drift: the Skill says "Only an epic", where the ratified design leaves which kinds count as branch kinds open (PROP:401-403, "Which Issue types count as branch kinds beyond the epic ... `agent-tooling-aio.4`"), and drops the "convenience guard, not a correctness rule" nuance.
- Provenance: ratified (home-in); "Only an epic" is an agent narrowing for v0.

### D14: Never claim a Branch Issue that has open children
- Category: lifecycle
- Generic or specific: generic
- Current text: "Never claim a Branch Issue that has open children." (SKILL:129-130)
- Earliest form: a46755f, 2026-10-09 (first in Skill); ratified form PROP:115-117 "never a Branch Issue with open children (`bdw` also refuses to claim one)".
- Provenance: ratified.

### D15: Search for duplicates before filing; sweep afterwards
- Category: filing
- Generic or specific: mixed (generic: search first; specific: `search` matches titles only, `find-duplicates` method)
- Current text: "**Search first:** `bdw search <words>` (titles and IDs) and `bdw list --desc-contains=<words> --all`. Afterwards, `bdw find-duplicates` sweeps for near-duplicates (its default method stays on the machine)." (SKILL:134-137)
- Earliest form: f319d19, 2026-10-09 (home-in): "Before filing, agents search for near-duplicates themselves (`search`); the filing Verb's own near-duplicate check is a backstop, and `find-duplicates` sweeps after filing." (PROP:237-240). Unchanged in substance.
- Provenance: ratified (home-in).

### D16: One Issue, one session's work; anything bigger is a Branch Issue broken down in its own pass
- Category: filing
- Generic or specific: generic
- Current text: "**One Issue, one session's work.** Anything bigger is an epic, broken down in its own pass." (SKILL:138-139)
- Earliest form: b90e669, 2026-10-08, success criterion 7: "**Organizational hygiene.** Work is broken down into Leaf Issues sized for one session, under Branch Issues for anything bigger, and the four relationships ... are looked for when an Issue is filed." (PROP:67-70). Unchanged.
- Provenance: ratified.

### D17: An Issue's kind goes in the type field, never in a label
- Category: labels-priority
- Generic or specific: mixed (generic only on trackers with a type field; on GitHub the kind is a label, see X9)
- Current text: "**Kind goes in the type field** (`--type=task|bug|feature|chore|epic|...`, `bdw types` lists them), never in a label." (SKILL:140-141); "Issues imported from GitHub also carry their old type labels ...; do not add those to new Issues, since kind goes in the type field." (PRIME:12-14)
- Earliest form: 8f58e26, 2026-10-09 (home-in, Constraints exit): "Beads' own type field carries the Issue's kind, so labels carry only areas and the like." Drift: the "only areas" corollary was retracted by 44e6387 (D18).
- Provenance: ratified (home-in, PROP:295 "An Issue's kind lives in Beads' type field, not in a label.")

### D18: Every Issue has at least one area label and may carry others; follow the project's declared scheme
- Category: labels-priority
- Generic or specific: generic (the per-repo scheme location is specific)
- Current text: "**Labels:** every Issue has at least one area label and may carry others; use the ones already in use (`bdw label list-all`) unless the repo's `PRIME.md` says otherwise." (SKILL:142-144); "8. **Labels follow the project's conventions.**" (PROP:71)
- Earliest form: 8f58e26, 2026-10-09: "**Labels** follow the scheme the repo declares; `bdw create` refuses unknown labels or a missing required category. Beads' own type field carries the Issue's kind, so labels carry only areas and the like." Drift: 44e6387, 2026-10-09, "use-bd proposal: an Issue has an area label and may carry others", corrected it: "'Labels carry only areas' read the GitHub schema's rule (one type label, at least one area label) as if Beads' native type field made areas the only family allowed. The rule is the conditional, not the biconditional".
- Provenance: ratified (criterion 8 and "the scheme the repo declares" are home-in); the 44e6387 correction was made by a later job (claude-job-5dff43f7) with no recorded ruling, so its provenance is unknown, though its message reads like a correction to the maintainer's intent.

### D19: Description says what and why, then has an Acceptance Criteria section
- Category: filing
- Generic or specific: mixed (generic: what, why, acceptance criteria; specific: bd's `--acceptance` is inline only)
- Current text: "**Description:** what and why, then a `## Acceptance Criteria` section. bd's `--acceptance` flag takes inline text only, so the criteria live in the description file." (SKILL:146-148)
- Earliest form: a46755f, 2026-10-09; unchanged. Not in PROP.
- Provenance: agent-elaborated as a filing template (first in v0, absent from PROP). The maintainer's c86 sketch distinguishes "success criteria (Branch Issues) or acceptance criteria (Leaf Issues)", see X7.

### D20: No empty Issues
- Category: setup
- Generic or specific: mixed (generic: every Issue says what it is; specific: `create.require-description`)
- Current text: "Require a description, so every Issue says what it is." (ONB:128); "**No empty Issues.** `create.require-description` is on, so every Issue says what it is." (PROP:256-257)
- Earliest form: f319d19, 2026-10-09 (home-in); unchanged.
- Provenance: ratified (home-in).

### D21: No barrier to capture: do not demand structure at filing time
- Category: filing
- Generic or specific: generic (bd lint is the specific)
- Current text: "Leave `validation.on-create` off: bd's section lint would refuse a bug filed before anyone knows how to reproduce it." (ONB:135-136); "**No barrier to capture.** Beads' section lint (`bd lint`) is type-dependent and, if enforced at creation, would refuse a bug filed before anyone knows how to reproduce it, inviting placeholder text. ... Rigor that arrives as an Issue moves through its lifecycle is separate work (`agent-tooling-c86`, a status-gated Issue lifecycle)." (PROP:258-264)
- Earliest form: 733d6d4, 2026-10-09 (home-in, "filing through a validated plan file; advisory lint"); unchanged.
- Provenance: ratified; evidence: agent-tooling-c86 description: "Sketch from the maintainer (2026-10-09, use-bd home-in ...), not ratified: New Issues land in a starting state such as needs_triage with whatever the filer knows, so capture during flow is never blocked (a bug whose repro is unknown still gets filed, and says so honestly rather than with placeholder text)." The no-barrier stance is ratified; the lifecycle states are explicitly not.

### D22: Look for four relationships at filing; add dependencies on your own, the other three only when very confident
- Category: relationships
- Generic or specific: generic (the Beads mapping is specific)
- Current text: "**The four relationships.** At filing, look for each: | dependency | ... | always | duplication | ... | only when very confident | composition | ... | only when very confident | contradiction | ... | only when very confident | Otherwise raise it with the user (unattended: report it)." (SKILL:149-158)
- Earliest form: ee85c50, 2026-10-08 (home-in, Anti-goals exit): "**Unilateral relationships.** Agents add dependencies they find at filing time on their own; contradiction, duplication, and composition only when very confident, and otherwise raise them (or, unattended, report them)." Unchanged.
- Provenance: ratified (home-in; also success criterion 7, PROP:67-70). agent-tooling-r6b records that the maintainer raised batch triage on 2026-10-08 because "Filing-time checks are best effort".

### D23: A wrong blocking dependency silently removes work from ready; always state the dependency type; provenance links do not block
- Category: relationships
- Generic or specific: mixed (generic: blocking edges hide work, so make them deliberately; specific: bare `dep add` defaults to blocks)
- Current text: "Always pass `--type` to `dep add`: bare, it creates a blocking edge, and a wrong blocking edge silently removes work from `bdw ready`. `discovered-from` records provenance and does not block." (SKILL:158-161)
- Earliest form: EPIC note, 2026-09-26, "items for the skill, user-approved: (a) Dependencies: bd dep add defaults to a blocks edge, which hides the dependent from bd ready, and the warning prints only to a terminal; always pass the type explicitly (related, discovered-from, blocks) and treat a bare dep add as a bug". Drift: the home-in added the planned echo of what left ready work (PROP:234-236).
- Provenance: ratified (user-approved EPIC note; home-in PROP:234-236).

### D24: Contradiction is a relationship; where the tracker has no type for it, relate the two and label the contradiction
- Category: relationships
- Generic or specific: mixed
- Current text: "| contradiction | `bdw dep add <a> <b> --type=relates-to`, plus a label naming it | only when very confident |" (SKILL:156); "contradiction, which Beads has no type for, to `relates-to` plus a label naming the contradiction" (PROP:242-243)
- Earliest form: f319d19, 2026-10-09 (home-in feature audit). Unchanged.
- Provenance: ratified (home-in).

### D25: Context that belongs in a standard document goes there; the Issue links it
- Category: docs-linkage
- Generic or specific: mixed (generic: Issue points to docs; specific: metadata keys)
- Current text: "**Context outside the tracker.** Material that belongs in a standard document (requirements, design, UX, an ADR, a lexicon entry) goes there, and the Issue links it through a metadata key per document type ... If you do not know where it belongs, keep it in the description." (SKILL:162-167)
- Earliest form: 8f58e26, 2026-10-09 (home-in, Constraints exit): "If information makes sense in a requirements doc, a design doc, a UX design, an ADR, a lexicon entry, or any other standard document type the project uses, it goes there, and the Issue links to it through a metadata key per document type ... A filing agent need not know the repo's layout: it drops the material in the repo's docs inbox, and the same `bdw` Verb files a Leaf Issue to incorporate it, whose worker moves it to its proper home". Drift: b66891c made incorporation "a reading and a judgment, not a move" (PROP:304-308); the Skill's "keep it in the description" fallback for an agent that does not know is a v0 stopgap, since the Docs Inbox is planned (UBD:52, `agent-tooling-aio.6`). Ratified fallback was only "A repo with no docs home keeps such context in the Issue's description." (PROP:309)
- Provenance: ratified (home-in); the "do not know, keep it in the description" fallback is agent-elaborated, see X8.

### D26: A cold pick-up works from the tracker alone; the Issue points to context rather than holding it
- Category: docs-linkage
- Generic or specific: generic
- Current text: "3. **A cold pick-up works.** A fresh session can resume any Issue from the Issue Tracker alone. The Issue points to the context it needs rather than holding all of it, so nothing is duplicated where it can drift." (PROP:55-57)
- Earliest form: b90e669, 2026-10-08; unchanged.
- Provenance: ratified (home-in success criterion 3).

### D27: Description is state (rewritten in place, with a Pick-up section); notes and comments are a log (append only)
- Category: lifecycle
- Generic or specific: generic (the field names are specific)
- Current text: "**State versus log.** An Issue's description is its state: rewrite it in place (`--body-file`) so it always reads as the current picture, including a `## Pick-up` section that tells the next session where the work stands. Notes and comments are its log: append, never rewrite." (SKILL:196-199)
- Earliest form: EPIC note, 2026-09-25, "user ruling: the skill should standardize how an issue's notes field is used as a pick-up point. ... a pick-up point is a state doc and is rewritten in place each session; a friction log or running record (as on w7p.4) is a stream doc and grows by appending. Decide which field carries which (notes versus design versus a dedicated child), and how a rewrite preserves provenance (history lives in the issue's event history, not in the body)." Drift: the ruling left open which field; the home-in/v0 put the pick-up in the description (PROP:81-83 "pick-up notes (a summary of where the work stands, for the next session to resume from, rewritten in place rather than appended)").
- Provenance: ratified (user ruling + home-in); the choice of the description field is the agent's resolution of an open item.

### D28: Free text through files; when inline text is refused, switch to the file form, never reword
- Category: filing
- Generic or specific: mixed (generic: never reword content to get past a refusal; specific: harness refuses inline text naming git)
- Current text: "**When inline text is refused, switch to the file form; never reword the text to get past the refusal.**" (SKILL:175-176); "A title is the one place where keeping the word out is sanctioned until `bdw` adds a file form; log a friction entry when it happens." (SKILL:189-191)
- Earliest form: a46755f, 2026-10-09; ratified form PROP:185-192 and success criterion 2 "no agent rewords Issue text to dodge a refusal or skips a field because it only takes inline text." Unchanged.
- Provenance: ratified; the title exception is agent-elaborated (a v0 concession, tracked as UBD:60-61 Known gap). See X5 for a conflicting Known gap.

### D29: Work waiting on a human leaves ready work through a blocker, not a custom status, and joins one human queue
- Category: lifecycle
- Generic or specific: mixed (generic: release the claim, block on the human, one queue for the maintainer; specific: gates, `human` label, `gh:pr`)
- Current text: "When an Issue cannot move until a person acts (a PR in review, a decision), release it and block it with a gate, so it leaves ready work without a custom status: ... Add the `human` label (`bdw label add <id> human`), so the maintainer has one queue: `bdw human list`." (SKILL:203-214)
- Earliest form: b90e669, 2026-10-08: "**Work waiting on a human** (e.g., a PR in review) is released into a custom status that keeps it out of ready work". Drift: f319d19, 2026-10-09 (home-in feature audit) replaced the custom status with native gates and the `human` label.
- Provenance: ratified (home-in, PROP:341-348).

### D30: A review closes through the normal close after merge, never through a shortcut that closes at once
- Category: closing
- Generic or specific: mixed
- Current text: "An open gate blocks closing as well as ready work. After merge, run `bdw gate check`, then close the Issue the normal way; never force the close. Never close it through `bdw human respond`, which closes at once." (SKILL:216-218); "`gate resolve` has no rule, so it prompts: resolving a human gate is the human's act." (BTD:100-101)
- Earliest form: f319d19, 2026-10-09: "A review closes through the normal close after merge, never through `bd human respond`, which closes the Issue at once." (PROP:346-348). "never force the close" added later (agent).
- Provenance: ratified (home-in); "resolving a human gate is the human's act" appears in rules.json:297 without a ruling cited (unknown).

### D31: Record branch and PR as structured metadata, the one current answer
- Category: docs-linkage
- Generic or specific: mixed
- Current text: "Record the Issue's branch and PR as metadata, the one current answer: `bdw update <id> --set-metadata=branch=<name> --set-metadata=pr=<number>`." (SKILL:220-221); "Beads' provenance log (`bd provenance`) supplements them ...; it does not replace them, as a stream never replaces the state it records." (PROP:351-353)
- Earliest form: b90e669, 2026-10-08: "the Issue records its branch and PR as metadata keys, which are structured and queryable, rather than as prose in its notes." Unchanged in substance.
- Provenance: ratified (home-in).

### D32: Report friction; offer upstream bug reports, never file them on your own
- Category: agent-vs-human
- Generic or specific: generic
- Current text: "When a `bdw` refusal, a prompt, or bd itself surprises you, say so: log a friction entry where the repo's `PRIME.md` says, and mention anything about the Issue Tracker that felt awkward in your final report. Offer to report a Beads bug or contribute a fix upstream; never do it on your own. Unattended, mention the bug in your final report." (SKILL:225-229)
- Earliest form: 8f58e26, 2026-10-09 (Upstream) and 929c2fb (friction as disconfirming evidence, PROP:427-429); the upstream text adds "and especially not during the trial" (PROP:316-317), dropped in the Skill.
- Provenance: ratified (home-in).

### D33: Policy versus conventions: policy lives only in reviewed permission rules; conventions in prose the agent reads
- Category: setup
- Generic or specific: generic (PRIME.md / settings.json are specific)
- Current text: "It states conventions and points; it never grants or denies an operation, because what agents may run is decided only by the reviewed Permission rules." (ONB:148-150); "**Policy** stays in each repo's reviewed Permission rules, never in a file an agent could edit to loosen its own limits." (PROP:275-276)
- Earliest form: 8f58e26, 2026-10-09: "Neither may grant or limit anything an agent may do." Drift: later wording allows `bdw.json` to "steer what the `bdw` executable itself does" (PROP:289-291).
- Provenance: ratified (home-in, "One Skill, many repos").

### D34: Policy has one home; each rule is written once and everything else points to it
- Category: setup
- Generic or specific: generic
- Current text: "6. **Policy has one home.** Each rule is written once: its procedure in the Skill, its rationale in the project's design doc or an ADR; `CLAUDE.md`, the README, and the trial docs point to the Skill." (PROP:62-66); "Point the repo's `CLAUDE.md` at this skill rather than restating Beads procedure" (ONB:172-173)
- Earliest form: b90e669, 2026-10-08: "Each rule is written once, in the Skill or this design; `CLAUDE.md`, the README, and the trial docs point here." Drift: split into procedure (Skill) vs rationale (design/ADR) vs enforcement (rules, bdw).
- Provenance: ratified.

### D35: Command policy classes: deny irreversible, off-machine, and record-falsifying; ask for safeguard bypasses; allow the reversible, and when to use it is filing discipline, not permission
- Category: agent-vs-human
- Generic or specific: generic (the verb lists are specific)
- Current text: "**Deny** what is irreversible, sends Issue data off the machine, or falsifies the record ... **Ask** for what fits the deny criteria but normal work still occasionally needs ... and for anything that steps around a `bdw` or `bd` safeguard or changes the safeguards or configuration themselves ... **Allow** everything else. Beads is meant as a tracker for agents, by agents: reversible, visible operations such as marking a duplicate or superseding an Issue are allowed, and when to use them is a filing discipline, not a permission." (PROP:198-213)
- Earliest form: ee85c50, 2026-10-08 (home-in, Anti-goals exit); unchanged except raw `bd` reads moved from open to denied (74ce46f).
- Provenance: ratified.

### D36: No reach outside the project
- Category: agent-vs-human
- Generic or specific: generic
- Current text: "**No reach outside the project.** An agent acts only on its own project's Issues unless expressly given permission to act on another's." (PROP:265-266). Not in SKILL.
- Earliest form: ee85c50, 2026-10-08; unchanged.
- Provenance: ratified (home-in). Dropped from the Skill (see X10).

### D37: One writable home per Issue; no sync in either direction
- Category: setup
- Generic or specific: generic
- Current text: "**One writable home per Issue.** Today that means one Issue Tracker for the repo, Beads. When the long tail moves back to forge issues, Beads and forge issues will both hold Issues, but each Issue is writable in exactly one of them at a time. **No sync, in either direction.** Any cross-repo view of Issues is read-only aggregation on top of each repo's Issue Tracker." (BTD:16-22)
- Earliest form: ADR 0001 (2026-09-24): "Beads is this repo's only tracker ... with the open GitHub issues imported once and then frozen and no sync in either direction." Drift: 9612742 (2026-10-16, ADRs 0011/0012) generalized "one tracker per repo" to "one writable home per Issue".
- Provenance: ratified (ADR 0001, ADR 0011 Consequences: "each Issue with one writable home at a time").

### D38: Which tracker for which work: agent-swarmed work on Beads, long-lived/low-churn/human-driven work on forge issues
- Category: setup
- Generic or specific: generic
- Current text: "**Decision:** The trial ends with Beads kept for work that agents swarm, while long-lived, low-churn, or human-driven work belongs in forge issues (GitHub or Forgejo Issues)" (docs/adr/0011-beads-for-swarmed-work-forge-issues-for-long-lived-work.md:10); BTI:7-9.
- Earliest form: 9612742, 2026-10-16; unchanged.
- Provenance: ratified (ADR 0011).

### D39: Tracker data stays private unless deliberately published
- Category: setup
- Generic or specific: mixed (generic: Issue content does not leave via a path the repo's outbound lint never sees; specific: Dolt bypasses git hooks)
- Current text: "**Issue data stays private.** The database's one remote is a private repository on the maintainer's self-hosted Forgejo, never the public GitHub origin" (BTD:23-27); "Optionally, give the database a private Dolt remote, never one on a public origin" (ONB:65-66)
- Earliest form: ADR 0001 "local-only"; ADR 0012 (2026-10-16) private remote.
- Provenance: ratified (ADRs 0001, 0012).

### D40: Never delete tracker records; closed Issues are hidden, so forgetting buys nothing
- Category: closing
- Generic or specific: mixed
- Current text: "**Forgetting off.** Closed Issues are hidden from agents' default views, so the lossy forgetting commands buy nothing; they are denied, and nothing else in Beads deletes." (BTD:50-52)
- Earliest form: ADR 0001 (2026-09-24) Rationale: "closed beads are hidden from agents by default so forgetting buys nothing." Unchanged.
- Provenance: ratified (ADR 0001).

### D41: Memories never live in the tracker
- Category: other
- Generic or specific: mixed
- Current text: "Memories stay in the harness's own memory files, never in Beads." (QUIRKS:73); rules.json:96 same.
- Earliest form: 50e29e6, 2026-09-24: "memory stays in the harness's memory files". Unchanged.
- Provenance: unknown (pre-home-in CLAUDE.md; carried into the ratified design as a deny, PROP:219-223).

### D42: TODO comments cite the Issue ID
- Category: todo-comments
- Generic or specific: generic (ID format specific)
- Current text: "**`TODO` comments** cite the Issue ID (`TODO(agent-tooling-xyz)`)." (PRIME:22)
- Earliest form: 50e29e6, 2026-09-24: "a `TODO` comment cites the bead ID (`TODO(agent-tooling-xyz)`), not `#N`." Unchanged.
- Provenance: unknown (repo convention since trial start; consistent with use-github's `TODO(#N)` rule).

### D43: A PR names the Issue it lands
- Category: docs-linkage
- Generic or specific: mixed (the "Lands X" vs "Closes #N" spelling is tracker-specific)
- Current text: "a PR body names the Issue it lands (`Lands agent-tooling-xyz`)" (BTI:46-47)
- Earliest form: 50e29e6, 2026-09-24: "a PR body names the bead it lands (`Lands agent-tooling-xyz`) instead of `Closes #N`." Unchanged.
- Provenance: unknown (trial-start CLAUDE.md).

### D44: File a Known-gaps line when filing a bug against a shipped capability
- Category: docs-linkage
- Generic or specific: generic (repo's doc convention)
- Current text: "**Known gaps at filing.** A bug or omission against a shipped capability gets its Known-gaps line, citing the new Issue ID, when you file it (rules in `CLAUDE.md`, Documentation)." (PRIME:19-21)
- Earliest form: fb5f8bd, 2026-10-24, "CLAUDE.md: Documentation rules for done, Known gaps, overviews, dated docs"; unchanged.
- Provenance: unknown; agent-authored commit implementing CLAUDE.md doc rules (the CLAUDE.md rules read as maintainer-directed, but no ruling is recorded in my sources).

### D45: Imported Issues carry their source URL as external reference
- Category: setup
- Generic or specific: mixed
- Current text: "**Imported Issues** carry their GitHub issue URL as the external reference." (PRIME:23-24)
- Earliest form: 50e29e6, 2026-09-24; unchanged.
- Provenance: unknown (trial setup).

### D46: Tracker setup is a maintainer procedure; an agent may draft it
- Category: setup
- Generic or specific: generic
- Current text: "This is a maintainer procedure, and the Permission rules suggested below deny agents `init` and every `dolt` subcommand, so a human runs or approves each step. An agent may draft the files (`PRIME.md`, the Permission rules) and the change that lands them." (ONB:5-9)
- Earliest form: not traced (ONB came from docs/beads-init.md, folded in at v0).
- Provenance: ratified in part; evidence: PROP:204-206 "**Ask** ... (it then runs only with a human attending, e.g., `init` when onboarding a repo, restoring a backup)".

### D47: Replace the tracker's default agent instructions with one pointer to the skill ("one voice")
- Category: setup
- Generic or specific: mixed
- Current text: "Commit `.beads/PRIME.md`. `bd prime` prints it instead of its default text, which contradicts this skill. Keep it short: one line telling agents to load `/use-bd`, then the repo's conventions in words (its labels, where friction is logged, how a PR names the Issue it lands, how a `TODO` comment cites an Issue)." (ONB:144-148)
- Earliest form: EPIC note, 2026-09-26, user-approved: "(c) Priming: ... Preferred over denying bd prime or overriding it in bdw: a committed PRIME.md that points at this skill redirects anyone who runs bd prime, keeps bdw thin". Unchanged in substance.
- Provenance: ratified (user-approved EPIC note; PROP:254-255 "One voice").

### D48: Pin the tracker version; behavior notes are verified per version
- Category: setup
- Generic or specific: specific mostly (generic kernel: tool-quirk guidance is valid only for the version it was verified on)
- Current text: "Verified against bd 1.3.0 (`bdw version`). On any other version, treat this list as unverified, and re-verify it when upgrading." (QUIRKS:3-4)
- Earliest form: 8f58e26, 2026-10-09 (home-in). Unchanged.
- Provenance: ratified.

### D49: Batch triage is separate from filing-time checks
- Category: triage
- Generic or specific: generic
- Current text: "Batch reconciliation is separate work (`agent-tooling-r6b`, automated batch triage)." (PROP:243-244); "**Out of scope:** batch triage and reconciliation" (PROP:84-85)
- Earliest form: ee85c50, 2026-10-08. agent-tooling-r6b: "Raised by the maintainer on 2026-10-08 during the use-bd home-in (agent-tooling-aio) as orthogonal to use-bd version one."
- Provenance: ratified (maintainer-raised).

### D50: Status lifecycle with exit requirements per state (sketch, not ratified)
- Category: lifecycle
- Generic or specific: generic
- Current text (agent-tooling-c86 description): "A status lifecycle for Issues on Beads in which each state has exit requirements, checked when an Issue moves on, rather than requirements checked at creation. Sketch from the maintainer (2026-10-09, use-bd home-in, agent-tooling-aio), not ratified: ... To leave needs_triage: a reasonable title and description, a priority, labels conforming to the project's scheme, and for a bug, steps to reproduce. ... To leave needs_scope: success criteria (Branch Issues) or acceptance criteria (Leaf Issues)."
- Earliest form: agent-tooling-c86, filed 2026-10-10. Unchanged.
- Provenance: maintainer-raised, explicitly "not ratified".

### D51: The tool-agnostic skill family (sketch, not ratified)
- Category: other
- Generic or specific: generic
- Current text (agent-tooling-u9n description): "Sketch raised by the maintainer on 2026-10-07 (not ratified, a starting point to scope): ... use-issues: generic guidance for thinking about Issues and project management; use-bd and use-github-issues add the tool specifics and quirks. create-issue: tool-agnostic guidance for creating, and above all breaking down, deduplicating, and linking, new Issues. triage-issues: fully tool-agnostic". Note 2026-10-26, "maintainer ruling: this epic is now the pilot for progressive disclosure".
- Provenance: maintainer-raised; the split itself is not ratified.

### D52: Design stance: settle usage first, then encode; enforce one-sentence rules in code with refusals that teach
- Category: other
- Generic or specific: generic (about tooling around a tracker)
- Current text: "**Usage first, then encoding.** ... **Enforce the simple rule in code.** Where a rule fits in one sentence and agents' habits (industry practice in their training data) pull against it, `bdw` enforces it with a refusal that teaches the right form, rather than the Skill spending paragraphs on judgment." (PROP:29-36)
- Earliest form: 2bbf978, 2026-10-07 (usage first); b90e669, 2026-10-08 (enforce in code). Unchanged.
- Provenance: ratified (home-in).

### D53: Each operation has one spelling
- Category: other
- Generic or specific: mixed
- Current text: rules.json:73 "Aliases ... and link ... are denied so the use-bd Skill's one spelling of each operation is the only one, while bdw does not map them."; BTD:83-84 "so each operation has one spelling".
- Earliest form: f319d19, 2026-10-09 (PROP:223-224 "the `link` command and the `new`, `done`, and `hb` aliases unless `bdw` maps them").
- Provenance: ratified (home-in); the "one spelling" rationale is agent-elaborated.

---

## Platform-specific mechanics (not traced)

- Always `bdw`, never `bd`/`beads`, reads included (SKILL:30-31).
- Verb first, global flags after; flag-first refused exit 4 (SKILL:32-35).
- `bdw` refuses `--actor`, `-C`, `--directory`, `--db`, `--database`, `--global` (exit 4); missing `.beads/metadata.json` or unverified bd version on a non-read (exit 5) (SKILL:40-50).
- `bdw help <verb>` instead of `bdw <verb> --help` (SKILL:23-25; QUIRKS:65-67).
- Background push after writes; push warnings reported once; push-host allowlist is the user's decision (SKILL:52-62).
- `bdw gate check` at session start (SKILL:74-75).
- `bdw ready` lists Branch Issues with open children; skip by hand; `bdw epic status --eligible-only` (SKILL:76-79; QUIRKS:19-20).
- `--claim` silently succeeds for same Actor; `attended-<user>` fallback (SKILL:101-104).
- Claim leases lapse unless `bdw heartbeat` (QUIRKS:9-15).
- `ready` hides `hooked`; gated Issue shows OPEN; ignore "Resolve with: bd gate resolve" (QUIRKS:23-28).
- No built-in "in review" status (QUIRKS:29-30).
- `dep add <a> <b>` means a depends on b (QUIRKS:39).
- `update --notes` replaces; `--append-notes`/`note --file` append (QUIRKS:40-41).
- Children inherit parent labels unless `--no-inherit-labels` (SKILL:144-145; QUIRKS:42-43).
- `-f` means different things per verb (QUIRKS:44-46).
- No file form for title, acceptance, replacing notes, reasons on `unclaim`/`gate` (SKILL:186-191; QUIRKS:47-48).
- `list -s` repeated keeps last; `search` titles/IDs only; `find-duplicates --method=ai` sends text off-machine; `children` includes closed; `list` hides gates (QUIRKS:49-55).
- Dates in `bd show` are UTC; imported Issues have long IDs (QUIRKS:59-61).
- `bd prime` prints PRIME.md but appends memories (QUIRKS:71-76).
- Missing metadata.json silently switches databases; never delete tracked `.beads/` files; `admin cleanup`/`prune`/`gc`/`admin compact` lossy; `config get` beats `config show`; Dolt push bypasses git hooks (QUIRKS:80-88).
- Free-text file-form table (SKILL:178-184); temp files in harness temp dir, unique names (SKILL:193-194).
- `gh:pr` gate works only on GitHub-hosted repos; otherwise `human` gate (SKILL:207-212).
- Onboarding: `bd init --skip-hooks --skip-agents`, undo init commit (mixed/soft, never hard), ignore gate lock, remove sync remote, private Dolt remote steps and restore check, backup outside repo, `git-push: false`, metrics off, ignore dolt-backup.json, lint allowance for db name, canonical rules expansion via `canonical_rows()` (ONB:13-171).
- rules.json structure (groups with `why`, `rows` or `verbs`×`shapes`) (ONB:156-160).
- PRIME: friction log on `agent-tooling-w7p.4`, dated numbered entries (PRIME:15-18); area labels in use (PRIME:11).

---

## Contradictions

**X1. "Never claim an epic" (user ruling) vs Branch Issues claimed in passes.**
EPIC note 2026-09-25: "user ruling: the skill carries these epic conventions ... (b) Never claim an epic; it is a container and its work is its children." vs SKILL:115-116 "It is worked in **passes**, each a session that claims it" and ADR 0009, whose first rejected alternative is "Branch Issues as passive containers". The home-in (2026-10-08) superseded the ruling, but the EPIC note still stands unannotated.

**X2. Closing an epic when its children close (user ruling) vs never.**
EPIC note 2026-09-25 (c): "Close an epic individually once its children are closed, or run bd epic close-eligible only after its dry-run form". vs QUIRKS:21-22 "**`epic close-eligible` closes epics because their children closed,** skipping the verifying pass. Never run it." and rules.json:86 (denied). Also superseded by ADR 0009 and not annotated.

**X3. `--exclude-type epic` (user ruling) vs "skip those by hand".**
EPIC note 2026-09-25 (a): "Find work with the ready verb plus the type exclusion for epics (bd ready --exclude-type epic)". vs SKILL:76-78 "`bdw ready` also lists Branch Issues (below) that still have open children; skip those by hand." The change follows from ADR 0009 (an epic with no open children IS ready work, so excluding epics would hide verification passes); my inference, not recorded anywhere.

**X4. Rulings dropped from the Skill.** Three user-approved EPIC notes are no longer in SKILL/QUIRKS:
- UTC dates, 2026-09-25: "Agents reasoning about recency or staleness use the exact UTC instants in the JSON output of bd show and compare against the date command, never the rendered date." Current QUIRKS:59 keeps only "**Dates in `bd show` are UTC.**"
- Heartbeat, 2026-09-26 (b): "prescribe it wherever a claim is held across long work". SKILL never mentions heartbeat; QUIRKS:9-11 notes leases lapse "unless renewed with `bdw heartbeat <id>`" without prescribing it. (rules.json:107 says "A lapsed lease is inert until reclaim runs", which may be why it was dropped; not recorded.)
- Parent/child deadlock, 2026-09-25 (d): "Link children with the parent flag only; never add a blocks dependency from a parent to its own children, which deadlocks silently (upstream #6506)." Absent from SKILL and QUIRKS.

**X5. "Never reword" vs a Known gap that says to reword.**
SKILL:175-176 "**When inline text is refused, switch to the file form; never reword the text to get past the refusal.**" and PROP:52-54 "no agent rewords Issue text to dodge a refusal". vs BTI:72-73 Known gap: "A deny rule also matches a write whose Issue text names a denied verb or flag, so Issue text spells those in words (`agent-tooling-9nx`)." The file form already sidesteps deny matching (SKILL:173-175), so the Known gap's instruction looks stale or overbroad (judgement).

**X6. "Only an epic takes children" vs open branch-kind set.** SKILL:127 "Only an epic takes children." vs PROP:401-402 "Which Issue types count as branch kinds beyond the epic ... (`agent-tooling-aio.4`)" and LEXICON.md Branch Issue "of a kind designated to hold children (e.g., an epic)".

**X7. Success criteria vs acceptance criteria for Branch Issues.** Maintainer sketch (agent-tooling-c86): "success criteria (Branch Issues) or acceptance criteria (Leaf Issues)"; LEXICON.md Branch Issue work includes "setting success criteria"; the EPIC itself has a "## Success Criteria" section. vs SKILL:124 "check the Branch Issue's own acceptance criteria" and SKILL:146 (every Issue gets "## Acceptance Criteria").

**X8. Unknown doc home: Docs Inbox vs description.** PROP:302-304 "One that does not [know where material belongs] drops it in the repo's Docs Inbox"; PROP:309 "A repo with no docs home keeps such context in the Issue's description." vs SKILL:166-167 "If you do not know where it belongs, keep it in the description." The Skill's fallback is a v0 stopgap (Docs Inbox planned, UBD:52) but is broader than the ratified fallback, and UBD's Known gaps do not list it.

**X9. Kind in a field vs kind in a label, across trackers.** SKILL:140-141 "**Kind goes in the type field** ... never in a label." vs skills/use-github/SKILL.md:120 "**Every issue gets exactly one type label plus one or more `area:` labels.**" Not a conflict within a tracker, but a generic `use-issues` must phrase the principle as "kind has one home, the tracker's type mechanism" (44e6387's message already frames GitHub's rule this way).

**X10. Ratified principles absent from the Skill.** "No reach outside the project" (PROP:265-266), "Every state change has one owner" (PROP:58-59), and the "cold pick-up" criterion (PROP:55-57) are in the ratified design but not taught in SKILL.md.

**X11. Branch Issue readiness invariant vs current behavior, without a Known gap.** LEXICON.md: Branch Issue is "ready work exactly when it has no open children". vs SKILL:76-78 (`bdw ready` lists Branch Issues with open children). UBD:50 tracks the fix as `planned` (agent-tooling-aio.4), but UBD's Known gaps (UBD:56-61) omits it, while CLAUDE.md says a shortfall in a shipped capability belongs there.

**X12 (stale, minor).** PROP:316-317 "they never do it on their own, and especially not during the trial" — the trial ended 2026-10-16 (ADR 0011). PROP is dated, so this is fine by the repo's dated-doc rule; noted only so `use-issues` does not copy it.

**X13 (outside generic scope).** docs/projects/bdw/index.md:44 and :50 say "exit 1" for no `bd` on PATH and for missing `metadata.json`; cli/bdw:17 and :24 say exit 3 and exit 5, matching SKILL:43-46. The bdw doc looks stale against the exit-code change 4600e66 (2026-10-11).

---

## Judgement calls

- **Scope.** I read the in-group files in full, plus ADRs 0001, 0002, 0009, 0010, 0011, the LEXICON.md tracking entries, the EPIC and its notes, Beads Issues agent-tooling-aio.1, u9n, c86, r6b, and friction log agent-tooling-w7p.4 (searched for "ruling"), as evidence. bdw/index.md was skimmed for principles and found to be mostly mechanics. ADRs 0012-0016 (push/remote) were treated as mechanics except D39.
- **Provenance standard.** Text first written in the 2026-10-07..09 home-in design commits (job claude-job-521331be) is counted as ratified, because PROP:8-9 and the EPIC description say the design was "ratified in a home-in session". Text first appearing in the v0 Skill (a46755f) with no PROP counterpart is counted as agent-elaborated, even when plausible. Pre-home-in CLAUDE.md text (50e29e6, 2026-09-24) is "unknown": it was written at trial adoption by an agent, with no recorded ruling.
- **Unannotated superseded rulings.** I treated the 2026-09-25 EPIC user rulings (b) and (c) as superseded by the later, also-maintainer-ratified ADR 0009, not as live contradictions of equal weight. The maintainer should confirm.
- **History depth.** Since SKILL.md is nearly unchanged from its first commit, I traced each generic principle to its home-in design commit or the earlier EPIC note/CLAUDE.md, not through SKILL.md's later push/exit commits.
- **Granularity.** Planned capabilities (filing Verb, Docs Inbox, label checks) are folded into their principles as drift notes, not listed separately. D50 and D51 are included although explicitly "not ratified", because they are maintainer-raised and bear directly on `use-issues`.
- **Pickaxe ambiguity.** One combined `git log -S` run (for "An open gate blocks closing") returned output I could not attribute with certainty, so I give no earliest commit for that phrase.
