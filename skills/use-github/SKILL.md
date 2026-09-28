---
name: use-github
description: >
  Day-to-day conventions for working with GitHub in a repo whose tracking was
  bootstrapped by the setup-github-issues skill: filing and labeling issues,
  setting priority and status on the project board, the `TODO(#N)` source-code
  rule, and the PR workflow. All GitHub writes run through the installed
  `ghw-*` wrapper scripts on PATH. Load this before filing, labeling, or
  prioritizing an issue, before writing a TODO comment, and before opening a
  PR. Also relevant for "file an issue", "what label should this get", "is
  there an issue for this", "open a PR". For first-time repo setup use
  setup-github-issues; for a full triage or grooming pass use triage-issues.
---

# Use GitHub

> The conventions for a repo that already has GitHub Issues set up as its task
> tracker. The repo's CLAUDE.md points here; this file is the detail behind
> that pointer.

## The Wrapper Layer

Every GitHub operation this skill covers runs through the `ghw-*` wrappers,
installed to a dedicated wrapper directory on PATH (source lives in the
agent-tooling repo's `cli/`; the installed tree under
`~/.local/libexec/agent-tooling/` is the only one this skill ever invokes).
Invoke them **by bare name, exactly as written here** — never by absolute path,
never through `python3`. The permission system matches literal command strings,
so the one rigid invocation form is what makes allowlisting work.

The wrappers exist because raw `gh` can't encode scope in an allowlistable
way: they pin everything blast-radius-relevant (repo, subverb, base branch,
merge strategy, field name) in fixed positional order, enforce the ecosystem's
contracts (label schema, canonical board schema) programmatically, and resolve
GraphQL name→ID mappings internally so IDs never appear in your commands.

Shared conventions:

- `<owner/repo>` is always an explicit argument. The cwd never decides where
  a write lands.
- Exit codes: `0` success (including an already-converged no-op), `1` gh/API
  failure, `2` usage error or policy refusal. Write wrappers print a JSON
  plan with `"action": "plan"` or `"applied"`.
- **On exit 2, read the message and fix the call.** Never work around a
  refusal by dropping to raw `gh` — the refusal is the contract doing its
  job, not an obstacle.
- **Body text always goes through a file.** Write the body with the Write
  tool to a staging path, then pass that path. Only two locations are
  accepted: `/tmp/claude/` (unique filename, so parallel agents don't
  collide), or in a background job `~/.claude/jobs/<job-id>/tmp/` with the
  job ID typed out literally — never `$CLAUDE_JOB_DIR`, which the harness
  blocks as shell expansion. No heredocs, no inline bodies, no command
  substitution.
- A permission prompt on a wrapper call is normal in a repo whose project
  settings don't allowlist that verb. The human approving it is the design
  working — don't hunt for an unprompted path.

## Step 1: Orient

Do this once per session, before the first issue or PR operation:

```bash
ghw-orient <owner/repo>
```

(Get `owner/repo` from the repo's CLAUDE.md, or
`gh repo view --json nameWithOwner -q .nameWithOwner`.)

One JSON blob replaces the old multi-call dance. Read from it — never guess
label names, board numbers, or field options:

- `labels` — the live label registry (type labels, `area:` labels, any scope
  labels).
- `boards` — every open linked project board, each with its field and option
  maps and a `conformance` verdict against the canonical board schema:
  `conforms` is driven by `gaps` (missing canonical fields/options);
  `tolerated_gaps` (a missing `Size` field on a pre-existing board) is
  expected and not actionable — it's why triage grandfathers `Size`-less
  boards; `extra_options` lists user-authored extras (advisory — leave them
  alone).
- `canonical_board` / `canonical_rule` — which board writes will target, and
  why. Multiple boards with no `TRIAGE.md` to disambiguate is an error you'll
  see at write time; `ghw-board-set --project <number>` overrides explicitly.
- `priority_regime` — `"board-field"` (priority lives on the board; don't
  create or apply `P0`–`P3` labels), `"p-labels"` (priority is an issue
  label, and there is no status beyond open/closed), or `"unknown"` (boards
  exist but none resolved as canonical, or the canonical board's `Priority`
  field is missing or non-conforming). On `"unknown"`, don't guess a regime:
  fix the board with `ghw-board-sync` (see `setup-github-issues`),
  disambiguate with `ghw-board-set --project`, or ask the user — then
  re-orient.

If the repo root has a `TRIAGE.md`, the repo is also set up for the
`triage-issues` skill. That doesn't change anything below; see the boundary
note at the end.

## Step 2: Before Filing — Search

Duplicate issues are the main failure mode. Search before you file:

```bash
gh issue list --repo <owner/repo> --search "<keywords>" --state all --limit 20
```

If something close already exists, comment on it instead of filing a
near-twin.

## Step 3: File the Issue

**Every issue gets exactly one type label plus one or more `area:` labels.**
Area labels are repo-specific and come from orient's label registry. Every
label you attach must already exist in the registry — propose a schema
addition rather than inventing a label ad hoc (via `ghw-label-sync`, see
`setup-github-issues`; note it syncs the *whole* registry declaratively, so
its schema file must restate every repo-specific label, not just the new
one).

| Type | Use for |
|------|---------|
| `feature` | New feature, system, or capability |
| `improvement` | Enhancement or refinement of existing functionality |
| `bug` | Something is broken or performs incorrectly |
| `debt` | Code quality, refactoring, documentation |
| `meta` | Design documents, planning artifacts, and non-code project work |

Write the title as an imperative statement of the outcome ("Cache label
lookups per session"), not a symptom fragment. The body should say what's
wrong or wanted, why it matters, and what "done" looks like — enough that
someone who isn't in this conversation can pick it up. Write it to a staging
file (see The Wrapper Layer), then:

```bash
ghw-issue-create <owner/repo> <type-label> "<title>" <body-file> [label ...]
```

The wrapper enforces exactly one type label (the positional) and at least one
`area:` label among the trailing labels. In the `p-labels` regime, include
the priority label too:

```bash
# Board-field regime (priority set on the board in Step 4):
ghw-issue-create acme/rocket-sled bug "Fix telemetry dropout on stage separation" \
  /tmp/claude/issue_body_7c21.md area:telemetry

# P-labels regime:
ghw-issue-create acme/rocket-sled bug "Fix telemetry dropout on stage separation" \
  /tmp/claude/issue_body_7c21.md P2 area:telemetry
```

## Step 4: Set Priority and Status Immediately

**This is the step that gets skipped.** An "Auto-add to project" workflow adds
new issues to the board with Priority and Status *unset*, and unset fields are
invisible in the board's grouped views — the issue is filed, on the board, and
effectively lost. Set both as part of filing, not later.

**Board-field regime only.** In the `p-labels` regime the priority label was
attached at filing (Step 3), there is no board to write to, and this step is
skipped entirely.

| Priority | Meaning |
|----------|---------|
| `P0` | Drop-everything and address now |
| `P1` | Most important non-emergency work |
| `P2` | Standard backlog work |
| `P3` | Nice-to-have; opportunistic |

```bash
ghw-board-set <owner/repo> <field-name> <option-name> <issue#> [--project <number>]
```

The wrapper adds the issue to the board if it isn't there yet, then sets the
field — no item IDs, no field IDs:

```bash
ghw-board-set acme/rocket-sled Priority P2 41
ghw-board-set acme/rocket-sled Status "Needs Triage" 41
```

Be liberal with Priority; be conservative with Status. New issues start at
`Needs Triage` — setting that on a freshly filed issue is safe **provided the
board actually has the option**: check the board's `conformance` verdict from
Step 1, since a board with `gaps` may lack canonical states and the wrapper
will refuse an option the field doesn't have. Status *transitions* belong to
the `triage-issues` skill; don't invent them here.

## Working an Issue (any time after filing)

- **Comment:** `ghw-issue-comment <owner/repo> <issue#> <body-file>`
- **Edit:** `ghw-issue-edit <owner/repo> <add-label|remove-label|retitle|set-body> <issue#> <value>`
    - `add-label` validates against the live registry and refuses a second
      type label, naming the incumbent (unlike filing, it doesn't demand an
      `area:` label — the issue already carries its labels). Reclassifying an
      issue is deliberately two calls: `remove-label` the old type, then
      `add-label` the new one.
    - `set-body` takes a body **file** path (staging rule applies), never
      inline text. Before rewriting a body wholesale, preserve any
      triage-owned structure already in it: the scoped-issue template
      sections (Problem / motivation, Goal, Acceptance criteria,
      User experience, Out of scope, Links), a `## Design decisions` section,
      a `**Blocked on:**` marker near the top, and a parent tracker's
      scope-locked checkbox (default phrasing
      `- [ ] All children created (scope locked)`; the repo's `TRIAGE.md` may
      override it). The wrapper doesn't parse these; stomping them breaks
      triage.
- **Close:** `ghw-issue-close <owner/repo> <issue#> [comment-file]` — use the
  optional comment file so the close carries its reason in one call. Closing
  an already-closed issue is a no-op success, and in that case the comment is
  **not** posted (the plan's `note` says so — repost with
  `ghw-issue-comment` if the reason still needs to land).
- **Link:** `ghw-issue-link <owner/repo> <add-sub|remove-sub|add-blocked-by|remove-blocked-by> <issue#> <other-issue#>`
  — issue numbers only; the wrapper resolves everything else. Argument order
  carries the direction, and the wrapper cannot detect an inversion: for
  `add-sub`/`remove-sub`, `<issue#>` is the **parent** and `<other-issue#>`
  the sub-issue; "X blocks Y" is expressed as Y `add-blocked-by` X.
  Re-adding an existing link is a no-op success.

## Step 5: TODOs in Source Code

**Every TODO references a real issue.** No bare TODOs.

```
# TODO(#42): brief description
# FIXME(#42): brief description   <- engine/platform bugs
```

If you're about to write a TODO and there's no issue for it, file the issue
first (Steps 2–4) and use its number. When an issue closes, grep for
`TODO(#N)` and clean up the comments it left behind.

## Step 6: Branches and PRs

- **Git discipline — branching, committing, rebasing, pushing — lives in
  the `use-git` skill**; load it before any of that. This step begins where
  that skill's "push is the boundary" line ends: the head branch is
  already on the remote.
- **Open the PR:**

  ```bash
  ghw-pr-create <owner/repo> <base-branch> <head-branch> <title> <body-file> [--draft]
  ```

  The head branch is an explicit argument (it must already be pushed); the
  wrapper warns if it differs from the branch you're standing on but doesn't
  refuse — opening a PR for a branch you're not on is legitimate. PRs are
  **non-draft by default** and should stay that way unless the user asks for
  a draft.
- **Link the issue in the PR body.** `Closes #42` (or `Fixes`/`Resolves`)
  auto-closes the issue on merge. For work that advances an issue without
  finishing it, use contributing language instead — `furthers #42`,
  `part of #42`, `towards #42` — which links without auto-closing.
- **Disclose unattended conflict resolutions.** If an unattended rebase
  hit conflicts you resolved, the body (or, for an existing PR, a
  comment) says so and names every file (see `use-git`).
- **Respond to review feedback:**
  `ghw-pr-comment <owner/repo> <pr#> <body-file>` (PRs aren't issues to `gh`,
  so `ghw-issue-comment` won't work on them).
- **Merge — only when the user has said to:**

  ```bash
  ghw-pr-merge <owner/repo> <base-branch> <merge|squash> <pr#>
  ```

  Choose `merge`, never `squash` (squash is banned; see `use-git`). The
  wrapper verifies the PR's actual base matches `<base-branch>`, refuses
  drafts, and refuses red or pending checks. There is no override: merging
  over red checks is a human decision made with raw `gh` at a human-attended
  prompt. The wrapper never deletes branches (worktree hazard).

## Boundary with `triage-issues`

This skill is for acting on a single issue as normal work happens — file it,
label it, prioritize it, work it, close it — through the `ghw-*` wrappers,
interactively.

`triage-issues` is a different mode: a repeatable, mostly-autonomous pass over
the *whole* backlog that screens issues, enforces label compliance, moves them
through the status model, and records findings in a durable ledger issue. It's
driven by a `TRIAGE.md` profile and routes its autonomous writes through its
own `triage-*` wrappers — deliberately the only write path an unattended run
has. Use it for "run triage" or a grooming pass — not for filing one issue.

`setup-github-issues` is the one-time bootstrap that created the label schema
and board this skill assumes.
