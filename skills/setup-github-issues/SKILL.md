---
name: setup-github-issues
description: >
  Set up GitHub Issues as the single source of truth for a repository's task
  tracking. Creates a custom label schema (type, area), optionally links a
  GitHub Project for priority tracking, converts scattered TODOs into
  well-scoped issues, and cleans up legacy tracking.
  Use this skill whenever the user wants to set up issues, create a label
  system, bootstrap a backlog, or migrate from ad-hoc TODOs to GitHub Issues
  for any repo. Also relevant when the user says things like "set up tracking",
  "create issues from TODOs", "organize the backlog", or "set up project
  management for this repo".
---

# Setup GitHub Issues

Bootstrap GitHub Issues as the canonical task tracker for a repository. This
replaces scattered TODOs (in docs, comments, notes-vault entries, memory files) with
a structured label schema and well-scoped issues. Optionally links a GitHub
Project for Kanban-style board views and priority tracking via project fields.

## Prerequisites

- `gh` CLI authenticated with access to the target repo
- The repo must already exist on GitHub
- If using a GitHub Project: the `project` scope must be on the `gh` token
  (`gh auth refresh -s project` to add it)

## Process Overview

1. Confirm the target repo
2. Ask about GitHub Project integration
3. (Optional) Audit for existing TODOs and work history
4. Design labels (universal + project-specific)
5. Present the full plan for user approval
6. Execute: labels, issues, project integration, cleanup, CLAUDE.md pointer
7. Verify

---

## Step 1: Confirm the Target Repo

Run `gh repo view --json nameWithOwner -q .nameWithOwner` from the repo root
to get the `owner/repo` identifier. Confirm it with the user before proceeding.

If the command fails, the user may not be in a git repo or `gh` may not be
authenticated. Help them resolve this before continuing.

## Step 2: GitHub Project Integration

Ask the user: **"Do you want to link a GitHub Project for board views and
priority tracking? If so, I'll track priority as a project field instead of
issue labels."**

If yes, ask whether the repo already has a board.

**No board yet** — create and provision one in a single call:

```bash
ghw-board-sync <owner/repo> new
```

That creates the ProjectV2, links it to the repo, and provisions the whole
canonical board schema: `Priority` (P0-P3), `Status` (the eight canonical
triage states), `Size`, and `Last Triaged`. The repo is born triage-ready, so
no separate board setup is needed later. It refuses if the repo already has a
linked open board.

**Board already exists** — ask for its project number (e.g., `2` from
`https://github.com/users/<owner>/projects/2`), then provision the same
schema onto it (the wrapper verifies the board is linked to this repo and
refuses if it isn't):

```bash
ghw-board-sync <owner/repo> <project-number>
```

On an existing board this creates only the fields that are missing and
*reports* drift on fields that already exist rather than editing them —
replacing a live single-select's options can orphan values already assigned to
items, so that stays a human decision. A missing `Size` is reported, not
created.

If the output's `conformance.gaps` reports missing `Status` options, the user
has to add them by hand in the board's Project settings (Status field → Edit
→ add option). The eight canonical states, in order, with **exact** casing —
note the deliberate mix of title and sentence case:

1. `Needs Triage`
2. `Needs Scope`
3. `Needs Eng Design`
4. `Needs Impl`
5. `In progress`
6. `In review`
7. `Done`
8. `Rejected`

Anything listed under `conformance.extra_options` is a state the user added
themselves; leave it alone unless they want it gone. Triage needs only the
canonical eight to be present.

Then, for both cases:

- Run `ghw-orient <owner/repo>` and confirm the board's `conformance` verdict
  is clean: no `gaps`. (A populated `tolerated_gaps` — a missing `Size` field
  on a pre-existing board — is expected and not actionable; triage
  grandfathers it.) No need to capture any IDs — the wrappers in Step 6
  resolve them internally.
- Have the user configure the "Auto-add to project" workflow in the project's
  Settings > Workflows to auto-import new issues — that one is not available
  through the CLI.

If the user says no, priority will be managed via issue labels (P0-P3) as in
the non-project workflow. Continue to Step 3.

## Step 3: Audit (Optional)

Ask the user: **"Do you want me to audit the repo for existing TODOs and work
history before we create issues, or are you starting fresh?"**

If they want an audit, check these sources in parallel:

| Source | How to find it |
|--------|---------------|
| `TODO.md` or `TODO` | Glob for `**/TODO*` in the repo root |
| `CLAUDE.md` | Read the project's CLAUDE.md; look for TODO/backlog/planned sections |
| Memory files | Check `~/.claude/projects/*/memory/MEMORY.md` for the current project |
| Notes vault | If the user keeps a notes or knowledge repo, look there for a matching project entry |
| Source code | `grep -rn 'TODO\|FIXME\|HACK\|XXX' --include='*.{py,js,ts,rs,go,java,rb,sh,yml,yaml}' .` |

After the audit, also ask: **"Want me to run a code review to surface
additional issues (bugs, debt, improvements)? This takes longer but can catch
things TODOs miss."**

If they say yes, perform a thorough code review using the Explore agent,
focusing on: bugs, correctness issues, code quality problems, missing
functionality, and potential improvements. Categorize findings by type and
severity.

### Historical Work

If the audit reveals evidence of completed work (e.g., past features listed in
docs, git log milestones, "done" items in TODO lists), ask: **"I found some
completed work items. Want me to create closed issues for these as historical
record?"**

Compile all findings into a single list, noting the source of each item.

## Step 4: Design Labels

Every repo gets the same universal label structure. Project-specific labels are inferred
from the audit and repo structure.

### Universal Labels (supplied by the wrapper — never redeclared)

The two tables below are baked into `ghw-label-sync`'s shared constants. They
appear in the plan (Step 5) for the user's benefit only and must **never** be
written into the schema file — the wrapper refuses a schema file that
redeclares a canonical label.

**Type labels** — every issue gets exactly one:

| Label | Color | Description |
|-------|-------|-------------|
| `feature` | `#a2eeef` | New feature, system, or capability |
| `improvement` | `#0075ca` | Enhancement or refinement of existing functionality |
| `bug` | `#d73a4a` | Something is broken or performs incorrectly |
| `debt` | `#fbca04` | Code quality, refactoring, documentation |
| `meta` | `#7057ff` | Design documents, planning artifacts, and non-code project work |

**Priority labels** — only if NOT using a GitHub Project for priority
(opted in via `"priority_labels": true` in the schema file, never declared
label-by-label):

| Label | Color | Description |
|-------|-------|-------------|
| `P0` | `#b60205` | Drop-everything and address now |
| `P1` | `#d93f0b` | Most important non-emergency work |
| `P2` | `#fbca04` | Standard backlog work |
| `P3` | `#0e8a16` | Nice-to-have; opportunistic |

If a GitHub Project is linked (Step 2), don't create these labels. Priority is
tracked as a project field instead. (The board field's option descriptions stay
empty on purpose — the states' meanings are defined by the skill texts, and
option help text would be a second source of truth.)

### Project-Specific Labels

**Area labels** — inferred from the repo's directory structure, services,
modules, or domains. They use the `area:` prefix and default to color
`#bfdadc` (`ghw-label-sync` applies both automatically).

Almost every repo will need `area:dev-x`, for work that is primarily targeting the
_project-internal_ developer experience. This includes things like build system,
tooling, observability, CI/CD, etc.

Almost every repo will need `area:test`, for work on testing that goes beyond the
standard mandatory testing practices for all code changes (e.g., unit testing new
code). Examples might be building an end-to-end test system, a large push to eliminate
accrued test debt, a project to increase test runtime performance, etc.

Examples (contrived):
- A game repo might have: `area:core`, `area:ui`, `area:rendering`, `area:content`, etc.
- An infra repo might have: `area:compute`, `area:networking`, `area:security`, `area:storage`, etc.
- A web app might have: `area:api`, `area:frontend`, `area:database`, `area:auth`, etc.

Look at the repo structure, the types of TODOs found, and the project's domain
to decide what area labels make sense. Aim for 3-8 area labels to start (more can be added
over time as deemed necessary). There should be enough labels for meaningful labeling, but
few enough with clear separation as to be consistently applied.

**Scope labels** (optional) — if the project spans multiple sites, environments,
teams, or deployment targets, add scope labels. These don't use a prefix; they
default to color `#c5def5`, with per-label overrides available in the schema
file when visually distinguishing several scopes matters.

Only add scope labels if there's a clear, meaningful distinction. Don't create
them just because you can.

## Step 5: Present the Plan

Before executing anything, present the complete plan as markdown for user
approval. The plan must include:

### Label Table

Show all labels (universal + project-specific) in a single table:

```markdown
| Label | Color | Description |
|-------|-------|-------------|
| `feature` | `#a2eeef` | New feature, system, or capability |
| ... | ... | ... |
| `area:api` | `#bfdadc` | API routes and middleware |
```

### Issue Table

Show all issues organized by category, with columns for:
- Issue number (sequential, for reference in the plan)
- Title
- Type label
- Priority (label or project field, depending on Step 2 choice)
- Area/scope labels
- Brief description or notes
- Dependencies (if any, as `-> #N` references)

Group issues logically (by area, by theme, or by priority — whatever makes
the plan easiest to scan). If there are historical/closed issues, list them
in a separate section.

### Priority Summary

A quick count table:

```markdown
| Priority | Count |
|----------|-------|
| P0 | 2 |
| P1 | 5 |
| P2 | 8 |
| P3 | 4 |
```

If using a GitHub Project, note that priorities will be set as project fields
after issue creation.

**Wait for explicit user approval before proceeding to execution.**

The user may want to adjust priorities, rename issues, add/remove items, or
change labels. Iterate on the plan until they're happy.

## Step 6: Execute

### 6a: Sync the Label Schema

Labels are managed declaratively by `ghw-label-sync`. The five type labels
(names, colors, descriptions) are baked into the wrapper's shared constants —
never redeclared. A JSON schema file supplies only the repo-specific families
from the approved plan. Write it with the Write tool to `/tmp/claude/` with a
unique name:

```json
{
  "priority_labels": false,
  "area": [
    {"name": "api", "description": "API routes and middleware"},
    {"name": "frontend", "description": "Web client"}
  ],
  "scope": [
    {"name": "site-a", "description": "The Site A deployment"}
  ]
}
```

- `priority_labels`: `true` only when **no** GitHub Project is linked (the
  Step 2 choice) — it opts the canonical `P0`–`P3` labels into the desired
  set. Leave `false` on board repos.
- `area` names are bare — the wrapper adds the `area:` prefix.
- `description` is required per label; `color` is optional (family defaults
  apply).
- Omit `scope` entirely if the plan has no scope labels.

Preview, then execute:

```bash
ghw-label-sync <owner/repo> plan /tmp/claude/label_schema_<unique>.json
```

Everything the schema doesn't declare is a deletion candidate — which is how
GitHub's stock labels get cleaned up. (Eight of the nine fall out as
deletions; stock `bug` collides case-insensitively with the canonical type
label, so it shows under `update` — description drift-fixed, not deleted.)
The plan prints the full diff plus a warning listing any to-be-deleted labels
still attached to open issues. Show it to the user; on approval:

```bash
ghw-label-sync <owner/repo> apply-delete /tmp/claude/label_schema_<unique>.json
```

(`apply` creates and drift-fixes but leaves deletions unexecuted; bootstrap
normally wants `apply-delete` so the stock labels actually go. Re-runs
converge to a no-op, so a re-run of the skill is harmless.)

The schema file is disposable and cannot live in the repo — the wrapper only
accepts staging paths. To change labels later, rebuild the **whole** file
from `ghw-orient`'s live `labels` registry plus your change: the sync is
declarative, so a partial file makes every omitted repo-specific label a
deletion candidate.

### 6b: Create Issues

Create issues in the order specified in the plan (dependency order matters so
that `#N` cross-references resolve correctly).

Write each issue body to a file with the Write tool — `/tmp/claude/` with a
unique filename; never heredocs or command substitution — then file with
`ghw-issue-create`. The wrapper enforces exactly one type label and at least
one `area:` label, all validated against the registry just synced in 6a:

```bash
# With project (priority as project field, set in 6c):
ghw-issue-create <owner/repo> <type> "<title>" \
  /tmp/claude/issue_body_<unique>.md area:<area1> [more labels]

# Without project (priority as label):
ghw-issue-create <owner/repo> <type> "<title>" \
  /tmp/claude/issue_body_<unique>.md <P0-P3> area:<area1> [more labels]
```

**For historical/closed issues:** create them first (in chronological order,
so they get the lowest numbers), then close each immediately:

```bash
ghw-issue-close <owner/repo> <number>
```

### 6c: Set Priority and Status on the Board

**Skip this step if not using a GitHub Project.**

After all issues are created, set each one's board fields. `ghw-board-set`
adds the issue to the board if the auto-add workflow hasn't already, then
sets the field — no item IDs or field IDs involved:

```bash
ghw-board-set <owner/repo> Priority <P0-P3> <issue#>
ghw-board-set <owner/repo> Status "Needs Triage" <issue#>
```

Set Status as well as Priority: `Needs Triage` is the canonical entry state,
and an unset Status leaves the issue invisible in the board's grouped views.
(Historical/closed issues instead get `Status` `Done` if you add them to the
board at all.)

### 6d: Clean Up TODO Sources

After issues are created:

- **TODO.md**: Delete it if all its items are now issues (`git rm TODO.md`
  — the tracked-file-fenced form; per `use-git`, shell `rm` on repo
  content is not yours)
- **CLAUDE.md**: If it has TODO/backlog sections, replace them with a pointer:
  `See [GitHub Issues](https://github.com/<owner>/<repo>/issues) for the
  project backlog.`
- **Notes-vault entry**: Same treatment — replace TODO sections with a GitHub Issues
  pointer
- **Memory files**: Update MEMORY.md to remove TODO items that are now issues
- **Source code TODOs**: If source code TODOs were converted to issues, update
  them to reference issue numbers: `# TODO(#N): description`. Offer to do this
  as a separate commit since it touches many files.

### 6e: Point the Repo's CLAUDE.md at the `use-github` Skill

None of this survives if the next agent to open the repo can't see it. Write a
short, loud pointer into the target repo's `CLAUDE.md`, creating the file if it
doesn't exist (a `# <Repo Name>` title plus this section is enough for a new
file).

Keep it to a pointer. The conventions themselves — label schema, board fields,
`TODO(#N)`, branch/PR workflow — live in the `use-github` skill, which loads
only for agents that actually touch GitHub. Restating them in CLAUDE.md costs
every agent context and gives the two copies a chance to disagree.

**Be idempotent.** Look for an existing `## Issue tracking & workflow` heading
and rewrite its body in place, through to the next heading of the same or
higher level. Never append a second copy on a re-run. If Step 6d already
replaced a TODO section with an Issues pointer, fold it into this section
rather than leaving both.

```markdown
## Issue tracking & workflow

This project uses **GitHub Issues** as the single source of truth for work
tracking: <https://github.com/OWNER/REPO/issues>. Priority lives on the
[project board](https://github.com/users/OWNER/projects/N), not on labels.

**Load the `use-github` skill before filing, labeling, or prioritizing an
issue, before writing a `TODO` comment, and before opening a PR.** It carries
the label schema, the board fields, the `TODO(#N)` rule, and the branch/PR
workflow. Don't improvise these conventions.
```

If no GitHub Project was linked, change the priority clause to: "Priority is an
issue label (`P0`-`P3`), exactly one per issue."

## Step 7: Verify

Run these checks and report the results:

```bash
# Confirm labels, board linkage, and a clean conformance verdict in one read
ghw-orient <owner/repo>

# Confirm issues (open)
gh issue list --repo <owner/repo>

# Confirm issues (closed, if any historical ones were created)
gh issue list --repo <owner/repo> --state closed

# If using a project, confirm items and priorities
gh project item-list <number> --owner <owner> --limit 100

# If source code TODOs were updated, verify no bare TODOs remain
grep -rn 'TODO[^(]' --include='*.py' --include='*.ts' . | grep -v vendor/
```

Report a summary: number of labels created, number of open issues, number of
closed issues, project items (if applicable), and any bare TODOs remaining.

## Conventions Established

After running this skill, the repo should follow these conventions going
forward. They are the contract the `use-github` skill enforces day to day, and
Step 6e is what tells future agents to load it. Mention these to the user at
the end:

**Without a GitHub Project:**
- **Every issue gets exactly one type label + one priority label + one or more
  area labels**

**With a GitHub Project:**
- **Every issue gets exactly one type label + one or more area labels**
- **Priority (P0-P3) is tracked as a GitHub Project field**, not as an issue label
- New issues should be added to the project (or auto-added via workflow)
- **Status starts at `Needs Triage`**, set at filing time — an unset Status
  is invisible in the board's grouped views

**Always:**
- **TODO format in source code**: `# TODO(#N): brief description` — every TODO
  links to a GitHub issue
- **No bare TODOs**: All new TODOs must reference an issue number
- **On issue close**: grep for `TODO(#N)` and clean up associated comments
- **FIXME prefix**: Retained for engine/platform bugs: `# FIXME(#N): description`
- **All GitHub I/O through the `use-github` skill's `ghw-*` wrappers** — it is
  the canonical GitHub-I/O layer for day-to-day work; raw `gh` is for reads
  the wrappers don't cover

## Optional Next Step: Recurring Triage

The board this skill provisions is born triage-ready — the full canonical
schema is already in place. What recurring triage still needs is per-repo
*policy* configuration, which belongs to the `triage-issues` skill: a
`TRIAGE.md` profile at the repo root and a bootstrapped ledger issue. If the
user wants the repo under recurring triage, point them at that skill's
bootstrap section as the follow-on. The opaque IDs the profile needs all come
from `ghw-orient`: the board's `node_id`, plus each field's `id` and option
IDs under `fields[<name>]`.
