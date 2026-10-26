# Extract A: setup-github-issues

> This document captures state as of 2026-10-26. For current state, see [docs/index.md](../../index.md).

Sources read: `skills/setup-github-issues/SKILL.md` (the only file in the
skill directory, 508 lines, at `main` 2bf1ca6); the passages that describe it
in `docs/projects/ghw/index.md` and `docs/projects/ghw/design.md`; its rows in
the dated audit `docs/audits/2026-10-11-agent-versus-human-line.md`. For
cross-checks: `skills/use-github/SKILL.md`, `.beads/PRIME.md`, ADR 0011, and
Beads Issues `agent-tooling-xla`, `agent-tooling-n0p`, `agent-tooling-76b`.

## History note that governs every "Earliest form" below

The file has five commits in this repo:

- `cb6f1eb` 2026-09-22 "Initial import: shared Claude Code agent tooling". Its
  message: "Extracted 2026-09-22 from a private predecessor repository ... its
  history stays there and this repository's history begins here by design."
- `6ac3f23` 2026-09-23 "Fix the setup-github-issues source grep so its include globs match" (Beads bug `agent-tooling-1790288520885-2-59031ac1`, closed).
- `ca67ca6` 2026-10-01 "skills: load use-privacy before git and forge writes" (Lands `agent-tooling-n0p`).
- `78150fe` 2026-10-01 "skills: move use-privacy lines to the steps that draft outward text".
- `8b0fccf` 2026-10-11 "ghw-issue-close: make the closing comment mandatory".

`git diff cb6f1eb HEAD` on the file touches only those three areas (the grep,
the use-privacy sentence, the historical close). **Every other principle below
is unchanged since `cb6f1eb`**, and its real earliest form lives in the
predecessor repository, which is not readable from here. So for those I
record "Earliest form: cb6f1eb, 2026-09-22, Initial import; unchanged" and
"Provenance: unknown" (no ADR, ruling, or Issue in this repo speaks to them).

---

## Principles

### A1: GitHub Issues as the single source of truth, replacing scattered TODOs
- Category: setup
- Generic or specific: mixed (generic: one canonical tracker replaces TODOs scattered across docs, comments, notes, memory; specific: that tracker is GitHub Issues)
- Current text (verbatim, with path:line): "Bootstrap GitHub Issues as the canonical task tracker for a repository. This replaces scattered TODOs (in docs, comments, notes-vault entries, memory files) with a structured label schema and well-scoped issues." (skills/setup-github-issues/SKILL.md:17-19); description: "Set up GitHub Issues as the single source of truth for a repository's task tracking." (SKILL.md:4-5); CLAUDE.md template: "This project uses **GitHub Issues** as the single source of truth for work tracking" (SKILL.md:434-435)
- Earliest form: cb6f1eb, 2026-09-22, Initial import; unchanged
- Provenance: unknown; evidence: predates this repo's history. See Contradiction C1 against ADR 0011.

### A2: Confirm the target repo with the user before proceeding
- Category: agent-vs-human
- Generic or specific: mixed (generic: confirm which project/tracker you are about to set up; specific: `gh repo view` to get `owner/repo`)
- Current text: "Run `gh repo view --json nameWithOwner -q .nameWithOwner` from the repo root to get the `owner/repo` identifier. Confirm it with the user before proceeding." (SKILL.md:43-44)
- Earliest form: cb6f1eb, 2026-09-22; unchanged
- Provenance: unknown; the 2026-10-11 audit logs it as row S1 with "Reason given: None given." (docs/audits/2026-10-11-agent-versus-human-line.md:170)

### A3: Priority lives in exactly one place: a board field if there is a board, else a label
- Category: labels-priority
- Generic or specific: mixed (generic: one home for priority, chosen once per repo; specific: ProjectV2 field vs P-labels)
- Current text: "**\"Do you want to link a GitHub Project for board views and priority tracking? If so, I'll track priority as a project field instead of issue labels.\"**" (SKILL.md:51-53); "If the user says no, priority will be managed via issue labels (P0-P3) as in the non-project workflow." (SKILL.md:113-114); "If a GitHub Project is linked (Step 2), don't create these labels. Priority is tracked as a project field instead." (SKILL.md:194-195); "**Priority (P0-P3) is tracked as a GitHub Project field**, not as an issue label" (SKILL.md:484); template fallback: "Priority is an issue label (`P0`-`P3`), exactly one per issue." (SKILL.md:444-445)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A4: Priority levels and their meanings
- Category: labels-priority
- Generic or specific: generic (the four levels and meanings hold on any tracker)
- Current text: "| `P0` | `#b60205` | Drop-everything and address now |", "| `P1` | `#d93f0b` | Most important non-emergency work |", "| `P2` | `#fbca04` | Standard backlog work |", "| `P3` | `#0e8a16` | Nice-to-have; opportunistic |" (SKILL.md:189-192)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A5: Every issue gets exactly one type label, from a fixed universal set of five
- Category: labels-priority
- Generic or specific: generic (the type taxonomy and the one-type rule); colors and the wrapper's enforcement are specific
- Current text: "**Type labels** — every issue gets exactly one:" followed by "`feature` ... New feature, system, or capability", "`improvement` ... Enhancement or refinement of existing functionality", "`bug` ... Something is broken or performs incorrectly", "`debt` ... Code quality, refactoring, documentation", "`meta` ... Design documents, planning artifacts, and non-code project work" (SKILL.md:173-181); "Every repo gets the same universal label structure." (SKILL.md:163)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown. See C4 (debt vs meta overlap on documentation).

### A6: Every issue gets one or more area labels; the per-regime label contract
- Category: labels-priority
- Generic or specific: generic (classification by area is tracker-neutral); the `area:` prefix and wrapper enforcement are specific
- Current text: "**Without a GitHub Project:** - **Every issue gets exactly one type label + one priority label + one or more area labels**" (SKILL.md:478-480); "**With a GitHub Project:** - **Every issue gets exactly one type label + one or more area labels**" (SKILL.md:482-483); "The wrapper enforces exactly one type label and at least one `area:` label, all validated against the registry just synced in 6a" (SKILL.md:354-355)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A7: How to design area labels: few, clearly separated, consistently applied
- Category: labels-priority
- Generic or specific: generic
- Current text: "Look at the repo structure, the types of TODOs found, and the project's domain to decide what area labels make sense. Aim for 3-8 area labels to start (more can be added over time as deemed necessary). There should be enough labels for meaningful labeling, but few enough with clear separation as to be consistently applied." (SKILL.md:219-222); "Project-specific labels are inferred from the audit and repo structure." (SKILL.md:163-164)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A8: Two near-universal areas: dev-x and test
- Category: labels-priority
- Generic or specific: generic
- Current text: "Almost every repo will need `area:dev-x`, for work that is primarily targeting the _project-internal_ developer experience. This includes things like build system, tooling, observability, CI/CD, etc." (SKILL.md:205-207); "Almost every repo will need `area:test`, for work on testing that goes beyond the standard mandatory testing practices for all code changes (e.g., unit testing new code). Examples might be building an end-to-end test system, a large push to eliminate accrued test debt, a project to increase test runtime performance, etc." (SKILL.md:209-212)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown (the first-person, opinionated phrasing reads maintainer-authored, but that is a guess)

### A9: Scope labels only when the distinction is real
- Category: labels-priority
- Generic or specific: generic
- Current text: "**Scope labels** (optional) — if the project spans multiple sites, environments, teams, or deployment targets, add scope labels." (SKILL.md:224-225); "Only add scope labels if there's a clear, meaningful distinction. Don't create them just because you can." (SKILL.md:229-230)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A10: Attach only labels that exist; labels come from the declared schema
- Category: labels-priority
- Generic or specific: mixed (generic: no ad hoc labels, the schema is the authority; specific: `ghw-label-sync` is the only creator)
- Current text: "all validated against the registry just synced in 6a" (SKILL.md:355); docs: "The registry is the attachment authority, and `ghw-label-sync` is the only way labels get created." (docs/projects/ghw/design.md:135-136). use-github restates it: "Every label you attach must already exist in the registry — propose a schema addition rather than inventing a label ad hoc" (skills/use-github/SKILL.md:121-122)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A11: Audit every place TODOs hide before filing (optional, asked)
- Category: setup
- Generic or specific: generic
- Current text: "Ask the user: **\"Do you want me to audit the repo for existing TODOs and work history before we create issues, or are you starting fresh?\"**" (SKILL.md:118-119); sources table: "`TODO.md` or `TODO`", "`CLAUDE.md` | Read the project's CLAUDE.md; look for TODO/backlog/planned sections", "Memory files | Check `~/.claude/projects/*/memory/MEMORY.md` for the current project", "Notes vault | If the user keeps a notes or knowledge repo, look there for a matching project entry", "Source code" (SKILL.md:123-129)
- Earliest form: cb6f1eb; the source-code row was originally "`grep -rn 'TODO\|FIXME\|HACK\|XXX' --include='*.{py,js,ts,rs,go,java,rb,sh,yml,yaml}' .`" and was fixed in 6ac3f23 (mechanics only)
- Provenance: unknown. See C2 (notes vault).

### A12: Offer a code review to surface issues TODOs miss
- Category: filing
- Generic or specific: generic
- Current text: "After the audit, also ask: **\"Want me to run a code review to surface additional issues (bugs, debt, improvements)? This takes longer but can catch things TODOs miss.\"**" (SKILL.md:143-145); "focusing on: bugs, correctness issues, code quality problems, missing functionality, and potential improvements. Categorize findings by type and severity." (SKILL.md:148-150)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A13: Completed work may be recorded as closed issues, if the user wants
- Category: filing
- Generic or specific: generic (the ordering trick is specific to sequential numbering)
- Current text: "If the audit reveals evidence of completed work (e.g., past features listed in docs, git log milestones, \"done\" items in TODO lists), ask: **\"I found some completed work items. Want me to create closed issues for these as historical record?\"**" (SKILL.md:154-157); "**For historical/closed issues:** create them first (in chronological order, so they get the lowest numbers), then close each immediately." (SKILL.md:367-368); "(Historical/closed issues instead get `Status` `Done` if you add them to the board at all.)" (SKILL.md:393-394)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A14: Keep the source of every audited item
- Category: filing
- Generic or specific: generic
- Current text: "Compile all findings into a single list, noting the source of each item." (SKILL.md:159)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A15: Present the whole plan; wait for explicit approval; iterate
- Category: agent-vs-human
- Generic or specific: generic
- Current text: "Before executing anything, present the complete plan as markdown for user approval." (SKILL.md:238-239); "**Wait for explicit user approval before proceeding to execution.**" (SKILL.md:284); "The user may want to adjust priorities, rename issues, add/remove items, or change labels. Iterate on the plan until they're happy." (SKILL.md:286-287)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown; audit row S2 classifies it "Setup; Ratify" with reason "The user may adjust it." (docs/audits/2026-10-11-agent-versus-human-line.md:171)

### A16: What a backlog plan shows: per-issue labels, priority, notes, and dependencies; grouped to scan
- Category: breakdown
- Generic or specific: generic
- Current text: "Show all issues organized by category, with columns for: - Issue number (sequential, for reference in the plan) - Title - Type label - Priority (label or project field, depending on Step 2 choice) - Area/scope labels - Brief description or notes - Dependencies (if any, as `-> #N` references)" (SKILL.md:255-262); "Group issues logically (by area, by theme, or by priority — whatever makes the plan easiest to scan). If there are historical/closed issues, list them in a separate section." (SKILL.md:264-266); plus a "Priority Summary" count table (SKILL.md:268-279)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A17: Create issues in dependency order so cross-references resolve
- Category: relationships
- Generic or specific: mixed (generic: file prerequisites first so links point at real Issues; specific: `#N` numbering)
- Current text: "Create issues in the order specified in the plan (dependency order matters so that `#N` cross-references resolve correctly)." (SKILL.md:349-350)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown. Note: the skill expresses dependencies only as body cross-references; it never calls `ghw-issue-link` (sub-issues, blocked-by), which ghw ships (docs/projects/ghw/index.md:30).

### A18: Load use-privacy before composing outward text
- Category: other
- Generic or specific: generic (conditional on the skill existing)
- Current text: "If a `use-privacy` skill is listed among your available skills, load it before composing any text bound for outside this machine: an issue title or body, a label description, a TODO comment, a commit message." (SKILL.md:234-236)
- Earliest form: ca67ca6, 2026-10-01, "skills: load use-privacy before git and forge writes"; moved to the top of Step 5 in 78150fe ("setup-github-issues drafts issue titles and bodies in Step 5 ... so its sentence moves to the top of Step 5"). The Issue's mandated wording was "a commit message, a PR or issue body, a comment"; the skill tailored the list.
- Provenance: agent-elaborated from a filed Issue; evidence: `agent-tooling-n0p` ("Reference use-privacy from every Skill that writes outward") was created by `claude-job-4d3f379c`, the same job that landed it.

### A19: Every close carries its reason
- Category: closing
- Generic or specific: generic (wrapper enforcement is specific)
- Current text: "A close requires a comment, so stage one canned comment once (unique filename, per the staging rule) and reuse it for every historical close:" (SKILL.md:368-370); canned text "Imported as already-resolved history" (SKILL.md:373)
- Earliest form: cb6f1eb: "then close each immediately:" with `ghw-issue-close <owner/repo> <number>` (no comment). Changed by 8b0fccf, 2026-10-11, whose message states the principle: "The comment is the audit record of why an issue was closed, so a silent close should be inexpressible."
- Provenance: unknown/agent-elaborated; evidence: commit 8b0fccf is `Executed-By: claude-job-d50fd9b9`; no ADR. use-github carries the same rule with one exception: "The forge's auto-close on PR merge is the one sanctioned comment-less close." (skills/use-github/SKILL.md:212-213)

### A20: Status is set at filing to the canonical entry state
- Category: lifecycle
- Generic or specific: mixed (generic: a new Issue enters a defined triage entry state; specific: unset Status is invisible in ProjectV2 grouped views)
- Current text: "Set Status as well as Priority: `Needs Triage` is the canonical entry state, and an unset Status leaves the issue invisible in the board's grouped views." (SKILL.md:391-393); "**Status starts at `Needs Triage`**, set at filing time — an unset Status is invisible in the board's grouped views" (SKILL.md:486-487)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A21: The canonical eight-state lifecycle
- Category: lifecycle
- Generic or specific: mixed (generic: the state set and order; specific: exact casing for GitHub single-select options)
- Current text: "The eight canonical states, in order, with **exact** casing — note the deliberate mix of title and sentence case: 1. `Needs Triage` 2. `Needs Scope` 3. `Needs Eng Design` 4. `Needs Impl` 5. `In progress` 6. `In review` 7. `Done` 8. `Rejected`" (SKILL.md:86-96)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown. The states' definitions live in `triage-issues`, not here.

### A22: Never mutate live tracker schema that already carries data; report drift, leave it to a human
- Category: agent-vs-human
- Generic or specific: mixed (generic: an agent does not rewrite schema whose change can orphan assigned values; specific: ProjectV2 single-select options)
- Current text: "On an existing board this creates only the fields that are missing and *reports* drift on fields that already exist rather than editing them — replacing a live single-select's options can orphan values already assigned to items, so that stays a human decision. A missing `Size` is reported, not created." (SKILL.md:78-82); "If the output's `conformance.gaps` reports missing `Status` options, the user has to add them by hand" (SKILL.md:84-85)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown; audit row H8: "Drift on live board fields is reported, never edited; a second board is never created." (docs/audits/2026-10-11-agent-versus-human-line.md:96)

### A23: Leave user-added states alone
- Category: agent-vs-human
- Generic or specific: generic
- Current text: "Anything listed under `conformance.extra_options` is a state the user added themselves; leave it alone unless they want it gone. Triage needs only the canonical eight to be present." (SKILL.md:98-100)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A24: Field and option meanings live in the skill texts, not in tracker help text
- Category: docs-linkage
- Generic or specific: mixed
- Current text: "(The board field's option descriptions stay empty on purpose — the states' meanings are defined by the skill texts, and option help text would be a second source of truth.)" (SKILL.md:195-197)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown. Oddly placed: it sits in the Priority-labels section but speaks of "the states' meanings".

### A25: Deleting labels needs the user's approval of the plan; the plan warns of in-use labels
- Category: agent-vs-human
- Generic or specific: mixed (generic: show deletions, and what they would strip from open Issues, before deleting; specific: `plan` / `apply-delete` modes)
- Current text: "The plan prints the full diff plus a warning listing any to-be-deleted labels still attached to open issues. Show it to the user; on approval:" (SKILL.md:330-331)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown; audit row H9 and question 7 ask whether label deletion, "which is not recoverable, should be an ask rule rather than a grantable mode" (docs/audits/2026-10-11-agent-versus-human-line.md:401-403); still open as `agent-tooling-76b` ("Name the criterion for how irreversible deletion is gated", P3, open).

### A26: Retire the old TODO sources once their items are Issues; leave pointers
- Category: setup
- Generic or specific: mixed (generic: after migration, the old lists go and pointers to the tracker replace them; specific: `git rm`, file names)
- Current text: "- **TODO.md**: Delete it if all its items are now issues (`git rm TODO.md` — the tracked-file-fenced form; per `use-git`, shell `rm` on repo content is not yours) - **CLAUDE.md**: If it has TODO/backlog sections, replace them with a pointer ... - **Notes-vault entry**: Same treatment — replace TODO sections with a GitHub Issues pointer - **Memory files**: Update MEMORY.md to remove TODO items that are now issues" (SKILL.md:400-408)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown; audit row S3: "An agent deletes `TODO.md` with `git rm` once every item is an issue. | None given. | none" (docs/audits/2026-10-11-agent-versus-human-line.md:172). See C2.

### A27: Convert source TODOs to cite their Issue; separate commit
- Category: todo-comments
- Generic or specific: mixed (generic: each TODO cites its Issue; specific: the `#N` form)
- Current text: "**Source code TODOs**: If source code TODOs were converted to issues, update them to reference issue numbers: `# TODO(#N): description`. Offer to do this as a separate commit since it touches many files." (SKILL.md:409-411)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A28: TODO-comment contract: no bare TODOs, clean up on close, FIXME for engine/platform bugs
- Category: todo-comments
- Generic or specific: mixed (generic: rule; specific: `#N` ID form)
- Current text: "- **TODO format in source code**: `# TODO(#N): brief description` — every TODO links to a GitHub issue - **No bare TODOs**: All new TODOs must reference an issue number - **On issue close**: grep for `TODO(#N)` and clean up associated comments - **FIXME prefix**: Retained for engine/platform bugs: `# FIXME(#N): description`" (SKILL.md:490-494)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown. See C5 (FIXME), C7 (ID form).

### A29: The repo's CLAUDE.md points at the operating-manual skill; it does not copy the conventions
- Category: docs-linkage
- Generic or specific: generic (pointer-not-copy; idempotent section rewrite)
- Current text: "None of this survives if the next agent to open the repo can't see it. Write a short, loud pointer into the target repo's `CLAUDE.md`, creating the file if it doesn't exist" (SKILL.md:415-417); "Keep it to a pointer. The conventions themselves — label schema, board fields, `TODO(#N)`, branch/PR workflow — live in the `use-github` skill, which loads only for agents that actually touch GitHub. Restating them in CLAUDE.md costs every agent context and gives the two copies a chance to disagree." (SKILL.md:420-423); "**Be idempotent.** Look for an existing `## Issue tracking & workflow` heading and rewrite its body in place ... Never append a second copy on a re-run." (SKILL.md:425-427); template: "Don't improvise these conventions." (SKILL.md:441)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A30: Verify and report counts, including bare TODOs remaining
- Category: setup
- Generic or specific: mixed (generic: verify the setup and report; specific: the commands)
- Current text: "Report a summary: number of labels created, number of open issues, number of closed issues, project items (if applicable), and any bare TODOs remaining." (SKILL.md:468-469)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A31: New issues join the board
- Category: lifecycle
- Generic or specific: specific (board membership), generic in spirit (every Issue is visible in the prioritization surface)
- Current text: "New issues should be added to the project (or auto-added via workflow)" (SKILL.md:485); "Have the user configure the \"Auto-add to project\" workflow in the project's Settings > Workflows to auto-import new issues — that one is not available through the CLI." (SKILL.md:109-111)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A32: All tracker I/O through the wrapper layer; raw CLI only for reads it lacks
- Category: agent-vs-human
- Generic or specific: mixed (generic: agents write to the tracker only through the policy-carrying wrapper; specific: `ghw-*`, `gh`)
- Current text: "**All GitHub I/O through the `use-github` skill's `ghw-*` wrappers** — it is the canonical GitHub-I/O layer for day-to-day work; raw `gh` is for reads the wrappers don't cover" (SKILL.md:495-497)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

### A33: Setup provisions the full board schema; triage policy is separate and per-repo
- Category: triage
- Generic or specific: mixed (generic: the tracker is born ready for the triage model, while triage policy is a separate per-repo opt-in; specific: TRIAGE.md, ledger issue)
- Current text: "The board this skill provisions is born triage-ready — the full canonical schema is already in place. What recurring triage still needs is per-repo *policy* configuration, which belongs to the `triage-issues` skill: a `TRIAGE.md` profile at the repo root and a bootstrapped ledger issue. If the user wants the repo under recurring triage, point them at that skill's bootstrap section as the follow-on." (SKILL.md:501-506); docs: "Creating boards is `setup-github-issues`' job by convention, so every bootstrapped repo is triage-ready from birth." (docs/projects/ghw/design.md:218-219)
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown ("by convention", no ADR)

### A34: Setup is safe to re-run
- Category: setup
- Generic or specific: mixed
- Current text: "Re-runs converge to a no-op, so a re-run of the skill is harmless." (SKILL.md:338-339); with A29's idempotent CLAUDE.md section.
- Earliest form: cb6f1eb; unchanged
- Provenance: unknown

---

## Platform-specific mechanics (not traced)

- Prereqs: `gh` authenticated; repo exists; `project` scope via `gh auth refresh -s project` (SKILL.md:24-27).
- `ghw-board-sync <owner/repo> new` creates, links, and provisions a ProjectV2 (Priority P0-P3, Status, Size, Last Triaged); refuses if an open board is linked (SKILL.md:57-67).
- `ghw-board-sync <owner/repo> <project-number>` provisions an existing board, verifying linkage (SKILL.md:69-76).
- `ghw-orient` returns `conformance` (`gaps`, `tolerated_gaps`, `extra_options`), labels registry, `node_id`, field and option IDs; agents capture no IDs (SKILL.md:104-108, 506-508).
- Source-TODO grep needs one `--include=` per extension; brace globs silently match nothing (SKILL.md:131-141).
- Universal labels are baked into `ghw-label-sync` constants and must never be redeclared in the schema file; the wrapper refuses one that does (SKILL.md:168-171).
- Schema JSON: `priority_labels` (true only without a board), bare `area` names (wrapper adds `area:`), required `description`, optional `color`, omit empty `scope`; staged under `/tmp/claude/` with a unique name (SKILL.md:293-318, 341-342).
- Default colors: area `#bfdadc`, scope `#c5def5` (SKILL.md:203, 226).
- `ghw-label-sync plan` then `apply-delete`; `apply` skips deletions; stock labels delete, stock `bug` is drift-fixed (SKILL.md:320-339).
- Label changes later: rebuild the whole schema from `ghw-orient`'s registry, since a partial file deletes omitted labels (SKILL.md:342-345).
- Issue bodies and close comments as files via the Write tool; never heredocs or command substitution (SKILL.md:352-353).
- `ghw-issue-create <repo> <type> "<title>" <body-file> [P-label] area:<x> ...` (SKILL.md:358-365).
- `ghw-issue-close <repo> <n> <comment-file>` (SKILL.md:375).
- `ghw-board-set <repo> Priority|Status <value> <n>` adds to the board if needed (SKILL.md:382-389).
- Verification commands: `ghw-orient`, `gh issue list` (open, closed), `gh project item-list`, bare-TODO grep (SKILL.md:452-466).
- Auto-add workflow is UI-only (SKILL.md:109-111).
- Scope labels pass `ghw-issue-create` because it accepts any registry label that is not a second type label (docs/projects/ghw/design.md:130-135).
- No user-level ghw Permission rule; attended bootstrap takes one prompt (docs/projects/ghw/design.md:368-372).

---

## Contradictions

**C1. "Single source of truth" vs. two trackers by kind of work.**
- SKILL.md:4-5: "Set up GitHub Issues as the single source of truth for a repository's task tracking."
- docs/adr/0011-beads-for-swarmed-work-forge-issues-for-long-lived-work.md:10: "The trial ends with Beads kept for work that agents swarm, while long-lived, low-churn, or human-driven work belongs in forge issues (GitHub or Forgejo Issues)"; and :17: "A project with both kinds of work needs Beads and forge issues together, each Issue with one writable home at a time".
- The skill has no notion of a second tracker; its CLAUDE.md template would claim sole authority in a repo that also runs Beads. ADR 0011's "one writable home at a time" is per Issue, not per repo. The skill also covers only GitHub, though ADR 0011 names Forgejo Issues as an equal home.

**C2. The skill edits and reads the notes vault directly.**
- SKILL.md:406-407: "**Notes-vault entry**: Same treatment — replace TODO sections with a GitHub Issues pointer"; SKILL.md:128: "If the user keeps a notes or knowledge repo, look there for a matching project entry".
- [omitted: private source]

**C3. Label deletion: a grantable mode vs. the recoverability criterion.**
- SKILL.md:330-334 (show the plan, "on approval" run `apply-delete`) treats label deletion as an agent act once the user approves in conversation.
- docs/audits/2026-10-11-agent-versus-human-line.md:399-406: "A tracked file survives in history; a stripped label assignment and a compacted Issue do not. No passage says so." Auditor's lean: "label deletion moved to an ask rule." Unresolved; open as `agent-tooling-76b`.
- Related: the same audit flags `git rm TODO.md` (SKILL.md:400-402) as "None given" / principle "none" (row S3).

**C4. Type taxonomy overlaps on documentation.**
- SKILL.md:180: "`debt` ... Code quality, refactoring, documentation"
- SKILL.md:181: "`meta` ... Design documents, planning artifacts, and non-code project work"
- A documentation Issue fits both; the "exactly one type" rule (SKILL.md:173) has no tie-breaker. The same table is copied verbatim in skills/use-github/SKILL.md:126-132 (two copies of one fact, against A29's own pointer-not-copy rule).

**C5. FIXME rule is unexplained and smells of a single origin project.**
- SKILL.md:494: "**FIXME prefix**: Retained for engine/platform bugs: `# FIXME(#N): description`"; skills/use-github/SKILL.md:236: "`# FIXME(#42): brief description   <- engine/platform bugs`".
- "engine" fits the game-repo example (SKILL.md:215) and no other domain; "Retained" implies an earlier convention never stated. Step 7's check (SKILL.md:465) greps only `TODO[^(]`, so bare FIXMEs are never verified, and only in `*.py` and `*.ts` while Step 3's audit grep covers ten extensions (SKILL.md:132-135). `TODO[^(]` would also match `TODO.md` and `TODOs` in prose or comments.

**C6. TODO citation form differs by tracker.**
- SKILL.md:490: "`# TODO(#N): brief description` — every TODO links to a GitHub issue"
- .beads/PRIME.md:22: "**`TODO` comments** cite the Issue ID (`TODO(agent-tooling-xyz)`)."
- Same principle (every TODO cites its Issue), different ID syntax. Not a real conflict, but the generic rule is never stated apart from the GitHub form.

**C7. Where Status meanings live.**
- SKILL.md:196-197: "the states' meanings are defined by the skill texts" (plural, unnamed). use-github says "Status *transitions* belong to the `triage-issues` skill" (skills/use-github/SKILL.md:194-195). The skill lists the eight states and the entry state but never says which skill owns their definitions.

**C8. Dependencies only as body references.**
- SKILL.md:262: "Dependencies (if any, as `-> #N` references)" and SKILL.md:349-350 (dependency order for `#N` cross-references). ghw ships "Issue relationships: sub-issues and blocked-by" (docs/projects/ghw/index.md:30). The bootstrap never creates native links, so planned dependencies end up as prose only. This is more an omission than a contradiction.

---

## Judgement calls

- **Provenance is "unknown" for everything from the initial import.** The import commit says the predecessor's history "stays there". I had no access to it and did not search for it (it may sit near the maintainer's knowledge base, which the brief bars). I did not mark that text "agent-elaborated", because nothing in this repo shows who wrote it.
- **Doc scope.** No `docs/projects/setup-github-issues/` exists. The skill is documented as part of the ghw project (docs/projects/ghw/index.md:16, :36; design.md:134, :218, :346-353, :371). I included those passages. I also used the dated audit's rows S1-S3, H8, H9 and its question 7, because they are the only recorded analysis of this skill's agent-vs-human lines.
- **Merging restatements.** Where the skill says something twice (for example Step 6c and "Conventions Established" on Status, or Step 2 and the Conventions on priority), I made one principle and quoted both places.
- **Cross-checks were limited** to use-github, PRIME.md, and ADR 0011, since other readers cover those groups. I recorded only conflicts that touch this skill's text.
- **Not read:** anything in the maintainer's knowledge base.
- **A18 and A19 provenance.** I judged both agent-elaborated or unknown. Each landing commit was executed by a Claude job, and no ADR or recorded maintainer ruling backs either one. A18's Issue was also filed by the same job that landed it.
