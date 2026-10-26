# Extract B: use-github (skills/use-github/) and ghw project docs (docs/projects/ghw/)

> This document captures state as of 2026-10-26. For current state, see [docs/index.md](../../index.md).

Sources read in full: `skills/use-github/SKILL.md` (the only file under
`skills/use-github/`), `docs/projects/ghw/index.md`, `docs/projects/ghw/design.md`,
`docs/projects/ghw/triage-library-rebase.md`. All paths below are relative to
the repo root.

**History floor, read this first.** This repo's history begins at `cb6f1eb`
(2026-09-22, "Initial import: shared Claude Code agent tooling"), whose message
says the content was "Extracted 2026-09-22 from a private predecessor
repository ... its history stays there and this repository's history begins
here by design." So for `skills/use-github/SKILL.md`, "earliest form" below
means the earliest form *in this repo*; the real origin is in the predecessor
and could not be traced. The ghw project docs entered at `ff3c33c`
(2026-10-01, "docs: migrate the ghw project docs"), a migration of
pre-existing docs from elsewhere (its message: "the living design corrected to
the code"). No ADR in `docs/adr/` (0001 to 0016) ratifies any use-github
principle; those ADRs are about Beads, home-in, review, install, exit codes,
and paths.

## Principles

### B1: Search before filing; comment on a near-twin instead of filing
- Category: filing
- Generic or specific: mixed (the rule is generic; the `gh issue list --search` command is GitHub mechanics)
- Current text (verbatim, with path:line): "Duplicate issues are the main failure mode. Search before you file:" (skills/use-github/SKILL.md:109) ... "If something close already exists, comment on it instead of filing a near-twin." (skills/use-github/SKILL.md:115-116). Supporting rationale for why it stays as text: "Deliberate exception: `ghw-issue-create`, which is inherently not idempotent; duplicate search stays in `use-github`'s text as guidance." (docs/projects/ghw/design.md:49-51); and the Skill section lists it among "the guidance no Verb can absorb (search before filing, ..." (docs/projects/ghw/design.md:343-344)
- Earliest form: cb6f1eb, 2026-09-22, Initial import; unchanged. design.md wording from ff3c33c, 2026-10-01; unchanged.
- Provenance: unknown; evidence: predates this repo's history. The "main failure mode" framing is an empirical claim with no recorded source.

### B2: Exactly one type label plus at least one area label; only labels already in the registry
- Category: labels-priority
- Generic or specific: mixed (generic: every Issue is classified by exactly one type and at least one area, from a fixed schema, and a new label is a schema change, not an ad-hoc act; specific: `area:` prefix, `ghw-label-sync`, enforcement in `ghw-issue-create`)
- Current text (verbatim, with path:line): "**Every issue gets exactly one type label plus one or more `area:` labels.** Area labels are repo-specific and come from orient's label registry. Every label you attach must already exist in the registry — propose a schema addition rather than inventing a label ad hoc (via `ghw-label-sync`, see `setup-github-issues`; note it syncs the *whole* registry declaratively, so its schema file must restate every repo-specific label, not just the new one)." (skills/use-github/SKILL.md:120-126). Design: "The registry is the attachment authority, and `ghw-label-sync` is the only way labels get created. `TRIAGE.md` plays no part in label validation." (docs/projects/ghw/design.md:135-136)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo. It is enforced in code ("The Wrapper enforces the contracts", design.md:43-46), which suggests a settled decision, but no ruling is recorded here.

### B3: The five type labels and what each is for
- Category: labels-priority
- Generic or specific: generic (the taxonomy itself could hold on any tracker; Beads has its own native types, so see Contradictions)
- Current text (verbatim, with path:line): "| `feature` | New feature, system, or capability |" / "| `improvement` | Enhancement or refinement of existing functionality |" / "| `bug` | Something is broken or performs incorrectly |" / "| `debt` | Code quality, refactoring, documentation |" / "| `meta` | Design documents, planning artifacts, and non-code project work |" (skills/use-github/SKILL.md:130-134)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo. Shared with setup-github-issues and the code constants (`cli/lib/schema.py`, per design.md:314).

### B4: Title is an imperative outcome; body is self-contained with what, why, and done
- Category: filing
- Generic or specific: generic
- Current text (verbatim, with path:line): "Write the title as an imperative statement of the outcome (\"Cache label lookups per session\"), not a symptom fragment. The body should say what's wrong or wanted, why it matters, and what \"done\" looks like — enough that someone who isn't in this conversation can pick it up." (skills/use-github/SKILL.md:136-139)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo.

### B5: Set priority and status as part of filing, not later
- Category: lifecycle
- Generic or specific: mixed (generic: an Issue whose triage fields are unset is effectively lost, so filing includes setting them; specific: GitHub's "Auto-add to project" workflow and grouped board views as the cause)
- Current text (verbatim, with path:line): "**This is the step that gets skipped.** An \"Auto-add to project\" workflow adds new issues to the board with Priority and Status *unset*, and unset fields are invisible in the board's grouped views — the issue is filed, on the board, and effectively lost. Set both as part of filing, not later." (skills/use-github/SKILL.md:162-165)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo. "This is the step that gets skipped" reads like an observed failure being corrected, but there is no record of who observed it.

### B6: Priority scale P0 to P3
- Category: labels-priority
- Generic or specific: generic (the four-level meaning; where it lives, label or board field, is specific: see B9)
- Current text (verbatim, with path:line): "| `P0` | Drop-everything and address now |" / "| `P1` | Most important non-emergency work |" / "| `P2` | Standard backlog work |" / "| `P3` | Nice-to-have; opportunistic |" (skills/use-github/SKILL.md:173-176)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo. The same table is in skills/setup-github-issues/SKILL.md:189.

### B7: Be liberal with Priority, conservative with Status; Status transitions belong to triage
- Category: triage
- Generic or specific: mixed (generic: the filing agent sets priority freely, starts every Issue in the intake state, and does not move it further, since lifecycle moves are triage's job; specific: the `Needs Triage` option name and board-conformance check)
- Current text (verbatim, with path:line): "Be liberal with Priority; be conservative with Status. New issues start at `Needs Triage` — setting that on a freshly filed issue is safe **provided the board actually has the option**: check the board's `conformance` verdict from Step 1, since a board with `gaps` may lack canonical states and the wrapper will refuse an option the field doesn't have. Status *transitions* belong to the `triage-issues` skill; don't invent them here." (skills/use-github/SKILL.md:190-195). Design restatement: "`use-github` keeps Status writes conservative: `Needs Triage` on filing, and only on a conforming board; transitions belong to triage." (docs/projects/ghw/design.md:164-166)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo. Note the grant posture contradicts "liberal with Priority" only weakly: the typical grant includes `ghw-board-set <repo> Priority` with "Status withheld" (design.md:380), which matches it.

### B8: Orient once per session and read the tracker's live schema; never guess label names, board numbers, or field options
- Category: setup
- Generic or specific: mixed (generic: read the tracker's live schema before writing and never guess identifiers; specific: `ghw-orient` and its JSON fields)
- Current text (verbatim, with path:line): "Do this once per session, before the first issue or PR operation:" (skills/use-github/SKILL.md:70) ... "One JSON blob replaces the old multi-call dance. Read from it — never guess label names, board numbers, or field options:" (skills/use-github/SKILL.md:79-80). Also on board extras: "`extra_options` lists user-authored extras (advisory — leave them alone)." (skills/use-github/SKILL.md:89-90)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo.

### B9: When the priority regime is unknown, do not guess it; fix, disambiguate, or ask
- Category: labels-priority
- Generic or specific: mixed (generic: do not guess where priority lives, and ask when the tracker's configuration is ambiguous; specific: the `board-field`, `p-labels`, and `unknown` regimes)
- Current text (verbatim, with path:line): "`priority_regime` — `\"board-field\"` (priority lives on the board; don't create or apply `P0`–`P3` labels), `\"p-labels\"` (priority is an issue label, and there is no status beyond open/closed), or `\"unknown\"` ... On `\"unknown\"`, don't guess a regime: fix the board with `ghw-board-sync` (see `setup-github-issues`), disambiguate with `ghw-board-set --project`, or ask the user — then re-orient." (skills/use-github/SKILL.md:94-101)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo.

### B10: Preserve triage-owned body structure when rewriting an Issue body
- Category: lifecycle
- Generic or specific: mixed (generic: a body rewrite must keep the structure that triage or breakdown relies on, such as the scoped template, design decisions, a blocked-on marker, and a parent's scope-locked checkbox; specific: the exact section names and checkbox phrasing, and `TRIAGE.md` override)
- Current text (verbatim, with path:line): "Before rewriting a body wholesale, preserve any triage-owned structure already in it: the scoped-issue template sections (Problem / motivation, Goal, Acceptance criteria, User experience, Out of scope, Links), a `## Design decisions` section, a `**Blocked on:**` marker near the top, and a parent tracker's scope-locked checkbox (default phrasing `- [ ] All children created (scope locked)`; the repo's `TRIAGE.md` may override it). The wrapper doesn't parse these; stomping them breaks triage." (skills/use-github/SKILL.md:206-215). Design: "**Triage-owned body structures are load-bearing:** ... The Verbs do not parse them; the Skill texts warn `set-body` callers not to stomp them." (docs/projects/ghw/design.md:304-309)
- Earliest form: cb6f1eb, 2026-09-22; unchanged. design.md from ff3c33c, 2026-10-01.
- Provenance: unknown; evidence: predates this repo. This implies two breakdown concepts that use-github never defines: a "parent tracker" and its scope-lock (defined in triage-issues).

### B11: Every close carries its reason; a silent close is inexpressible; PR-merge auto-close is the one sanctioned exception
- Category: closing
- Generic or specific: generic (the rule is stated as meant to hold across Wrapper families; the already-closed no-op behavior is mechanics)
- Current text (verbatim, with path:line): "**Close:** `ghw-issue-close <owner/repo> <issue#> <comment-file>` — the comment file is required: the close carries its reason in one call, and a missing or blank comment is exit 2. The forge's auto-close on PR merge is the one sanctioned comment-less close." (skills/use-github/SKILL.md:216-219). Design: "The comment is mandatory (a missing or blank one is exit 2): it is the audit record of why the issue was closed, so a silent close is inexpressible through this Verb; forge auto-close on PR merge is the one sanctioned comment-less close." (docs/projects/ghw/design.md:146-150). Also "its own Verb, never a flag on edit, so closing is independently grantable." (docs/projects/ghw/design.md:145-146)
- Earliest form: cb6f1eb, 2026-09-22: "**Close:** `ghw-issue-close <owner/repo> <issue#> [comment-file]` — use the optional comment file so the close carries its reason in one call." Drift: went from optional-but-encouraged to mandatory in 8b0fccf (2026-10-11, "ghw-issue-close: make the closing comment mandatory"); the "one sanctioned comment-less close" wording came in c187791 (2026-10-11, "Address review of mandatory close comment: sanctioned-exception wording"), which narrowed an earlier "only comment-less close" claim because triage still closes with raw `gh`.
- Provenance: mixed, leaning ratified; evidence: Beads Issue agent-tooling-75z ("Make the closing comment mandatory on ghw-issue-close", labeled `human`) cites as its source the fjw issue-Verbs proposal (docs/projects/fjw/issue-verbs.md:96-103: "a silent close must be inexpressible, and the comment is the audit record (\"done because X, see commit Y\") ... The mandatory close comment is meant to hold across Wrapper families") and a maintainer request of 2026-10-01. That request is an instruction to file the proposal's Issues, not a ruling on this rule; whether the maintainer authored the fjw proposal's rule is not recorded here.

### B12: Relationships are parent/sub-issue and blocked-by, each with one spelling and a fixed direction
- Category: relationships
- Generic or specific: mixed (generic: two relationship kinds, parent/child and blocked-by; the subject is always the parent or the blocked Issue; "X blocks Y" is recorded as Y blocked-by X, so each relationship has one spelling; self-links refused; specific: argument order and `gh` version floor)
- Current text (verbatim, with path:line): "Argument order carries the direction, and the wrapper cannot detect an inversion: for `add-sub`/`remove-sub`, `<issue#>` is the **parent** and `<other-issue#>` the sub-issue; \"X blocks Y\" is expressed as Y `add-blocked-by` X." (skills/use-github/SKILL.md:225-227). Design: "`<issue#>` is always the subject (the parent, or the blocked issue). \"X blocks Y\" is spelled `add-blocked-by Y X`; there are no blocking subverbs, so each relationship has one spelling. Issue numbers only. Self-links are refused, edges to other repos are ignored, and when the edge list comes back truncated without the target in it, the Verb refuses rather than guess." (docs/projects/ghw/design.md:155-159)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo. Note: use-github says nothing about *when* to create a sub-issue or a blocked-by edge; it only covers how. (Beads' "four relationships" are in use-bd, outside this group.)

### B13: Every TODO references a real Issue; file the Issue first
- Category: todo-comments
- Generic or specific: mixed (generic: no bare TODOs, and file before you write the TODO; specific: the `#N` syntax)
- Current text (verbatim, with path:line): "**Every TODO references a real issue.** No bare TODOs." (skills/use-github/SKILL.md:232) ... "# TODO(#42): brief description" / "# FIXME(#42): brief description   <- engine/platform bugs" (skills/use-github/SKILL.md:235-236) ... "If you're about to write a TODO and there's no issue for it, file the issue first (Steps 2–4) and use its number." (skills/use-github/SKILL.md:239-240)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo. The `FIXME ... <- engine/platform bugs` distinction is unexplained (see Judgement calls).

### B14: When an Issue closes, clean up the TODOs that cite it
- Category: closing
- Generic or specific: generic
- Current text (verbatim, with path:line): "When an issue closes, grep for `TODO(#N)` and clean up the comments it left behind." (skills/use-github/SKILL.md:240-241)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo.

### B15: PR bodies link their Issue: closing keywords only for work that finishes it, contributing language otherwise
- Category: docs-linkage
- Generic or specific: mixed (generic: say whether a PR finishes an Issue or only advances it, and close only when it finishes; specific: GitHub's `Closes`/`Fixes`/`Resolves` keywords)
- Current text (verbatim, with path:line): "**Link the issue in the PR body.** `Closes #42` (or `Fixes`/`Resolves`) auto-closes the issue on merge. For work that advances an issue without finishing it, use contributing language instead — `furthers #42`, `part of #42`, `towards #42` — which links without auto-closing." (skills/use-github/SKILL.md:260-263)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo.

### B16: Merge only when the user has said to; merging is a human act
- Category: agent-vs-human
- Generic or specific: mixed (generic: merging is a human decision unless project rules delegate it; specific: the gates, no override, raw `gh` for a human override)
- Current text (verbatim, with path:line): "**Merge — only when the user has said to:**" (skills/use-github/SKILL.md:270) ... "There is no override: merging over red checks is a human decision made with raw `gh` at a human-attended prompt." (skills/use-github/SKILL.md:279-281). Design: "**Merging is a human act.** `ghw-pr-merge` is never granted to unattended agents absent project rules that say otherwise, and `use-github` merges only when the user has said to." (docs/projects/ghw/design.md:79-81)
- Earliest form: cb6f1eb, 2026-09-22 ("Choose `merge`, never `squash` (squash is banned; see `use-git`)" for strategy; "only when the user has said to" unchanged). design.md invariant 10 from ff3c33c, 2026-10-01.
- Provenance: unknown; evidence: predates this repo. PR-scoped, not Issue-scoped; included because it is the agent-vs-human line.

### B17: A refusal is the contract working: fix the call or the state, or stop and report; never route around it
- Category: agent-vs-human
- Generic or specific: generic (applies to any tracker wrapper's refusals; exit-code numbers are mechanics)
- Current text (verbatim, with path:line): "**On exit 2, read the message and fix the call. On exit 4, never retry unchanged:** read the message; fix the call or the state it names (push the branch, add the `area:` label), or stop and report. Never work around a refusal by dropping to raw `gh` — the refusal is the contract doing its job, not an obstacle." (skills/use-github/SKILL.md:48-52)
- Earliest form: cb6f1eb, 2026-09-22: "**On exit 2, read the message and fix the call.** Never work around a refusal by dropping to raw `gh` — the refusal is the contract doing its job, not an obstacle." Drift: the exit-4 clause ("never retry unchanged ... or stop and report") was added during the 2026-10-11/12 exit-code work (86127bd and following); core rule unchanged.
- Provenance: unknown; evidence: predates this repo.

### B18: A permission prompt is the design working; do not hunt for an unprompted path
- Category: agent-vs-human
- Generic or specific: generic
- Current text (verbatim, with path:line): "A permission prompt on a wrapper call is normal in a repo whose project settings don't allowlist that verb. The human approving it is the design working — don't hunt for an unprompted path." (skills/use-github/SKILL.md:64-66)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo.

### B19: Load use-privacy before composing outward text (Issue bodies, comments, PR bodies)
- Category: other
- Generic or specific: generic
- Current text (verbatim, with path:line): "**Load `use-privacy` first, if listed.** If a `use-privacy` skill is listed among your available skills, load it before composing any text bound for outside this machine: a commit message, a PR or issue body, a comment." (skills/use-github/SKILL.md:53-56)
- Earliest form: ca67ca6, 2026-10-01, "skills: load use-privacy before git and forge writes" (Lands agent-tooling-n0p, part); repositioned by 78150fe, 2026-10-01. Wording essentially unchanged.
- Provenance: unknown; evidence: agent commits (Executed-By claude-job-4d3f379c) landing a Beads Issue; I did not open agent-tooling-n0p to see whether the maintainer asked for it.

### B20: Single-issue work versus a whole-backlog triage pass are different modes
- Category: triage
- Generic or specific: mixed (generic: normal work files, labels, prioritizes, works, and closes one Issue at a time; screening, label compliance, status moves, and grooming are a separate, repeatable whole-backlog pass with a durable ledger; specific: the `triage-issues` skill, `TRIAGE.md`, the `triage-*` wrappers)
- Current text (verbatim, with path:line): "This skill is for acting on a single issue as normal work happens — file it, label it, prioritize it, work it, close it — through the `ghw-*` wrappers, interactively." (skills/use-github/SKILL.md:285-287) ... "`triage-issues` is a different mode: a repeatable, mostly-autonomous pass over the *whole* backlog that screens issues, enforces label compliance, moves them through the status model, and records findings in a durable ledger issue. ... Use it for \"run triage\" or a grooming pass — not for filing one issue." (skills/use-github/SKILL.md:289-294)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown; evidence: predates this repo.

### B21: Unattended triage has exactly one write path, and its proposed mutations have no autonomous path
- Category: agent-vs-human
- Generic or specific: mixed (generic: an unattended agent may make only a narrow, pre-agreed set of writes; status, priority, and size transitions, scope-body rewrites, closes, and reparenting are proposals for a human; the permission boundary equals the autonomy boundary; specific: `dontAsk`, the six wrappers)
- Current text (verbatim, with path:line): "**Unattended triage writes only through the `triage-*` wrappers.** Those six wrappers are the only autonomous write path" (docs/projects/ghw/design.md:59-60); "Triage's proposed-mutation set (status, priority, and size transitions, scope-body rewrites, closes, reparenting) has no autonomous path by design (see Unattended triage)." (docs/projects/ghw/design.md:248-250); "with only the six `triage-*` wrappers granted, so any other write (raw `gh`, a status transition) is denied rather than executed: the permission boundary equals the autonomy boundary. Never `bypassPermissions`, which would approve a stray proposed mutation." (docs/projects/ghw/design.md:393-396); and "an arbitrary body rewrite belongs to triage's proposed-mutation class" (docs/projects/ghw/design.md:140-141)
- Earliest form: ff3c33c, 2026-10-01 (docs migration); the launch-form paragraph was reworked in 5ec1a8c, 2026-10-11, "Make the guard-script background job the one triage launch form". The principle itself is unchanged.
- Provenance: unknown; evidence: migrated from a predecessor; the commit says "corrected to the code", which is agent work aligning an existing doc.

### B22: What an agent may do on the tracker is set per repo by grants, Verb by Verb
- Category: agent-vs-human
- Generic or specific: mixed (generic: capability boundaries are set per repo, each operation granted separately (comment without close, labels without body rewrite, priority without status), with policy visible in settings and no side channels; specific: Permission-rule syntax)
- Current text (verbatim, with path:line): "A typical day-to-day core: `ghw-orient`, `ghw-issue-create`, `ghw-issue-comment`, `ghw-issue-edit` with `add-label`, `remove-label`, and `retitle` only (`set-body` withheld), `ghw-issue-close`, `ghw-board-set <repo> Priority` (Status withheld), and `ghw-pr-comment`." (docs/projects/ghw/design.md:377-380); "**Granularity is the point.** Comment without merge, label edits without `set-body`, merge into one branch and not another: each is expressed by which rules exist, not by Wrapper configuration. There are no side-channel policy files; all policy is visible in settings." (docs/projects/ghw/design.md:385-388)
- Earliest form: ff3c33c, 2026-10-01; unchanged in substance.
- Provenance: unknown; evidence: migrated doc.

### B23: Deleting labels that are still attached to open Issues is a human decision
- Category: agent-vs-human
- Generic or specific: mixed (generic: schema deletions that touch open Issues are surfaced for a human to decide; specific: `plan`/`apply`/`apply-delete` modes)
- Current text (verbatim, with path:line): "`apply-delete` also executes the deletes, open issues included; deletion authority is granted by granting that mode. In every mode, deletion candidates attached to open issues are listed on stderr (and in the JSON plan), because `plan` is exactly where a human decides whether to grant deletion." (docs/projects/ghw/design.md:201-205)
- Earliest form: ff3c33c, 2026-10-01; unchanged.
- Provenance: unknown; evidence: migrated doc.

### B24: Tracker setup is a one-time bootstrap owned by a separate skill
- Category: setup
- Generic or specific: mixed (generic: schema (labels, board, fields) is created once at bootstrap so a repo is triage-ready from birth, and day-to-day work assumes it; specific: skill names)
- Current text (verbatim, with path:line): "`setup-github-issues` is the one-time bootstrap that created the label schema and board this skill assumes." (skills/use-github/SKILL.md:296-297); "Creating boards is `setup-github-issues`' job by convention, so every bootstrapped repo is triage-ready from birth." (docs/projects/ghw/design.md:217-219)
- Earliest form: cb6f1eb, 2026-09-22 (Skill); ff3c33c, 2026-10-01 (design); unchanged.
- Provenance: unknown; evidence: predates this repo.

### B25: PRs are non-draft by default
- Category: other
- Generic or specific: generic (PR, not Issue, policy)
- Current text (verbatim, with path:line): "PRs are **non-draft by default** and should stay that way unless the user asks for a draft." (skills/use-github/SKILL.md:257-259)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: [omitted: private source]

### B26: Disclose unattended conflict resolutions in the PR
- Category: other
- Generic or specific: generic (PR, not Issue, policy)
- Current text (verbatim, with path:line): "**Disclose unattended conflict resolutions.** If an unattended rebase hit conflicts you resolved, the body (or, for an existing PR, a comment) says so and names every file (see `use-git`)." (skills/use-github/SKILL.md:264-266)
- Earliest form: 1f13560, 2026-09-26, "use-github, use-forgejo: disclose unattended conflict resolutions" (Part of agent-tooling-7kz); aligned in a395200 the same day.
- Provenance: unknown; evidence: agent commit propagating a use-git requirement; I did not open agent-tooling-7kz.

## Platform-specific mechanics

- Every GitHub write goes through `ghw-*` Verbs, invoked by bare name only, never by path or through `python3` (SKILL.md:23-29).
- `<owner/repo>` is always explicit; the cwd never decides where a write lands (SKILL.md:39-40; design.md:33-34).
- Exit codes 0 to 6 as listed in SKILL.md:41-47; write wrappers print a JSON plan (`"plan"`/`"applied"`).
- Bodies always go through a staged file under `/tmp/claude/` or `~/.claude/jobs/<job-id>/tmp/`, typed out literally; never `$CLAUDE_JOB_DIR`, heredocs, inline bodies, or command substitution (SKILL.md:57-63; design.md:67-78).
- `ghw-orient` fields: `labels`, `boards` with `conformance`/`gaps`/`tolerated_gaps`/`extra_options`, `canonical_board`/`canonical_rule` (SKILL.md:82-93).
- Board disambiguation rules `only-linked`, `triage-md`, `none-linked`/`ambiguous`; `--project` override; `TRIAGE.md` discovery bounded by the git work tree (design.md:221-242).
- `ghw-issue-create` usage, with the P-label included in the `p-labels` regime (SKILL.md:142-158).
- `ghw-board-set` adds the issue to the board if missing, then sets the field; single-select only (SKILL.md:179-188; design.md:160-164).
- `ghw-issue-edit` subverbs; `add-label` refuses a second type label and names the incumbent; reclassifying is two calls (remove, then add); `set-body` takes a file (SKILL.md:200-206; design.md:138-144).
- Closing an already-closed issue is a no-op that does not post the comment; repost with `ghw-issue-comment` if needed (SKILL.md:219-222).
- Re-adding an existing link is a no-op; `gh` 2.94.0 floor for `ghw-issue-link` (SKILL.md:228; design.md:153-154).
- `ghw-pr-create`: head branch explicit and already pushed; warns, does not refuse, on branch mismatch (SKILL.md:252-257).
- `ghw-pr-comment` exists because `gh issue comment` refuses PR numbers (SKILL.md:267-269).
- `ghw-pr-merge` accepts only `merge`; refuses squash (exit 2), drafts, base mismatch, and red or pending checks (exit 4); never deletes branches (SKILL.md:272-281).
- `ghw-label-sync` syncs the whole registry declaratively; its schema file must restate every repo-specific label (SKILL.md:123-126; design.md:190-206).
- `ghw-board-sync` reports drift on existing fields and never edits it (design.md:207-219).
- No ghw Permission rules at user level, reads included; no `allowed-tools` in use-github (design.md:52-58).
- Idempotency contract for `-sync`/`-set`/edit/close/link Verbs; create is not idempotent (design.md:47-51).
- A write that may have landed exits `1`; check before re-running (design.md:282-294).
- Triage library rebase: wrappers import the shared library rather than shelling out to Verbs; no silent truncation of open-issue listings (triage-library-rebase.md:22-34).

## Contradictions

1. **Wrapper-only claim versus raw `gh` reads in the same Skill.** "Every GitHub operation this skill covers runs through the `ghw-*` wrappers" (skills/use-github/SKILL.md:23-24) versus Step 2's search, "gh issue list --repo <owner/repo> --search \"<keywords>\" --state all --limit 20" (skills/use-github/SKILL.md:112), and the orient fallback "`gh repo view --json nameWithOwner -q .nameWithOwner`" (skills/use-github/SKILL.md:76-77). The description is narrower ("All GitHub writes run through", SKILL.md:7-8), so the body overstates it. Duplicate search, the "main failure mode", has no Verb.
2. **Merge as human-only versus delegated unattended merges.** use-github says "**Merge — only when the user has said to:**" (skills/use-github/SKILL.md:270) with no exception. The repo CLAUDE.md lets agents "merge PRs into it unattended (`ghw-pr-merge the-peregrin-group/agent-tooling integrate/<run> merge <pr#>`)" (CLAUDE.md, "Agent integration branches"). design.md reconciles this ("absent project rules that say otherwise", docs/projects/ghw/design.md:80; "No `ghw-pr-merge` grant unless the repo's own rules put merging into a designated branch in agents' hands", design.md:382-384), but the Skill text does not.
3. **"Sanctioned exception" versus triage's raw close.** use-github: "The forge's auto-close on PR merge is the one sanctioned comment-less close." (skills/use-github/SKILL.md:218-219). The ghw Known gap: "The triage Skill still closes approved issues with raw `gh issue close`, which posts no comment (`agent-tooling-0fm`)." (docs/projects/ghw/index.md:44-45). This is acknowledged as a defect, not an intended exception.
4. **Every Issue takes type and area labels versus the triage ledger Issue.** B2 ("Every issue gets exactly one type label plus one or more `area:` labels", SKILL.md:120) versus the open question in the Known gap: "needs a decision first on whether the triage-excluded ledger issue takes the type and `area:` labels `ghw-issue-create` requires (`agent-tooling-5kf`)" (docs/projects/ghw/index.md:49-52).
5. **Exit-code documentation disagrees with itself.** SKILL.md:41-47 documents codes 0 to 6 as current behavior, and commit c479ffd is titled "docs: ghw implements the full Exit-code contract". But index.md:58-59 lists the Known gap "The `ghw-*` Verbs still exit the earlier seven-code taxonomy, not the six-code Exit-code contract (`agent-tooling-cjvo.2`)", and design.md:262-265 says "The Verbs do not exit this way yet". Also, index.md:39 marks "Exit codes per the Exit-code contract" as `shipped` while the Known gap says they are not. design.md:280-281 calls auth failures and the version-floor case `1`, while SKILL.md:46 calls them `5`. (Mechanics, but a live inconsistency.)
6. **TODO citation format by tracker.** use-github: "`# TODO(#42): brief description`" (SKILL.md:235). This repo's Beads conventions: "**`TODO` comments** cite the Issue ID (`TODO(agent-tooling-xyz)`)." (.beads/PRIME.md:22). They agree on the principle (B13) and differ on syntax. A generic skill must state the principle and leave the ID format to the tracker.
7. **PR linkage keyword by tracker.** use-github: "`Closes #42` (or `Fixes`/`Resolves`) auto-closes the issue on merge" (SKILL.md:260-261). Repo CLAUDE.md: "a PR body names the Issue it lands (`Lands agent-tooling-xyz`) instead of `Closes #N`", and says use-github's "issue-filing and board conventions do not apply while Beads is the Issue Tracker". Same principle (B15, say whether the PR finishes the Issue) with different vocabulary; the repo has no "contributing language" counterpart for Beads, though this repo's commits use "Part of agent-tooling-7kz" and "Toward the gate agent-tooling-bpj", which follow the same pattern.
8. **"Be liberal with Priority" versus triage's priority-distribution checks (a tension, not a strict contradiction).** use-github: "Be liberal with Priority" (SKILL.md:190). triage-issues flags inflation: "open P0 count > cap → flag ... \"P0\" means *drop everything*, which is bounded by human attention" (skills/triage-issues/SKILL.md:426). "Liberal" most likely means "always set it", not "set it high", but the text does not say which.

## Judgement calls

- Counted 26 principles. PR-only rules (B16 merge, B25 non-draft, B26 conflict disclosure) are included because the brief's agent-vs-human category covers them and they sit in the same Skill; a strict Issue-only reading would drop B25 and B26.
- Marked almost every Skill principle's provenance as "unknown", not "agent-elaborated", because the text predates this repo's history (cb6f1eb is an import from a private predecessor) and I had no evidence either way. I did not read the maintainer's knowledge base (forbidden) or the predecessor.
- B11 is marked "mixed, leaning ratified": a `human`-labeled Beads Issue whose source includes a maintainer request, but that request only says to file the proposal's Issues, not to adopt this rule.
- Folded the "reclassify takes two calls" and "second type label refused" behaviors into mechanics, since they enforce B2 rather than add a principle.
- Weird thing to flag: "`# FIXME(#42): brief description   <- engine/platform bugs`" (SKILL.md:236). "Engine/platform" means nothing in this tooling repo. It looks like a leftover from a game-engine project in the predecessor. The TODO/FIXME distinction it draws is never defined.
- Weird thing to flag: B9's `p-labels` regime says "there is no status beyond open/closed" (SKILL.md:96). So a p-labels repo has no intake state, and B7's "New issues start at `Needs Triage`" does not apply there. The Skill skips Step 4 entirely for that regime (SKILL.md:167-169) but never says what replaces intake triage.
- Did not open agent-tooling-n0p (privacy) or agent-tooling-7kz (conflict disclosure) to check for maintainer origin; those provenance calls are therefore "unknown".
