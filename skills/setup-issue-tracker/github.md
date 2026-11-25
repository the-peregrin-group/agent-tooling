# Setting up GitHub Issues

The GitHub mechanics of `setup-issue-tracker`, read when its plan reaches
a step on GitHub. The procedure, the plan, and the approval are the
skill's; this file says only how each step is done on GitHub today. Every
GitHub write goes through the installed `ghw-*` Verbs; `use-github` is
their operating manual.

## Before you start

- `gh` is authenticated with access to the repo, and the repo exists on
  GitHub. A project board needs the `project` scope on the token
  (`gh auth refresh -s project` adds it).
- Confirm the target with `gh repo view --json nameWithOwner -q
  .nameWithOwner` from the repo root, and use that `owner/repo` everywhere
  below.

## Forge identity, today

ghw has no Forge identities yet: every Verb acts as whatever account `gh`
is authenticated as, which is usually the owner's own, and there is no
Verb that registers an identity or grants a machine account access. That
is planned with ghw's issue Verbs on the shared grammar. Until then, say
in the plan that agents on this repo act under the owner's account, and
register nothing.

## Where priority and state are recorded

Ask the owner whether to link a project board. With a board, the Issue
Priority and the Issue State are board fields (`Priority` and `Status`).
Without one, priority is a label, one of `P0` to `P3` per Issue, and the
default leaves open where the state is recorded: the owner designates it
in the copy (a label axis for status is the default's suggestion), and the
plan creates whatever labels that takes.

**No board yet.** Create and provision one in a single call:

```bash
ghw-board-sync <owner/repo> new
```

It creates the board, links it to the repo, and provisions `Priority`
(P0 to P3), `Status`, `Size`, and `Last Triaged`. It refuses if the repo
already has a linked open board.

**A board already exists.** Ask for its project number (the `2` in
`https://github.com/users/<owner>/projects/2`), then:

```bash
ghw-board-sync <owner/repo> <project-number>
```

It checks that the board is linked to this repo and refuses if not. On an
existing board it creates only the missing fields and reports drift
on existing ones rather than editing them, since replacing a live
single-select's options can orphan values already set; that stays the
owner's call. A missing `Size` is reported, not created.

`Status` carries eight options, with this exact casing: `Needs Triage`,
`Needs Scope`, `Needs Eng Design`, `Needs Impl`, `In progress`,
`In review`, `Done`, `Rejected`. Match the open options to the open
states of the repo's Issue State Diagram; the default's are the first six.
Done and Rejected stay, because ghw and the triage scripts work to them,
and read as the closed state with that reason. Missing options reported under
`conformance.gaps` are added by the owner by hand, in the board's Project
settings. Options under `conformance.extra_options` are the owner's own;
leave them.

Then, either way:

- Run `ghw-orient <owner/repo>` and confirm its `conformance` verdict has
  no `gaps`. A missing `Size` on an older board shows under
  `tolerated_gaps` and needs nothing.
- Ask the owner to turn on the board's "Auto-add to project" workflow
  (Project settings, Workflows); the CLI cannot.

## Labels

`ghw-label-sync` manages labels declaratively. The five kind labels
(`feature`, `improvement`, `bug`, `debt`, `meta`), the `human` label, and
the four priority labels are the Wrapper's own constants, never declared
in the schema file: it refuses a kind or priority label there and ignores
a `scope` entry named `human` with a note. A board's `Priority` options
are the same `P0` to `P3`. So on GitHub the kinds are those five and the priority
levels those four until the Wrapper changes. Do not swap in GitHub's issue
types; a Tracker Schema that proposes other kinds or levels cannot be
applied here yet, so say so in the plan.

A schema file supplies only the repo's own families. Write it to
`/tmp/claude/` with a unique name; the Wrapper accepts only staging paths:

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

- `priority_labels` is `true` only when no board is linked; it opts the
  `P0` to `P3` labels in.
- `area` names are bare; the Wrapper adds the `area:` prefix and the
  family's color.
- `description` is required on every label; `color` is optional.
- `scope` labels are unprefixed, for a project that spans sites,
  environments, or deployment targets, and only where the distinction is
  clear and meaningful. Omit the key if there are none.

Preview, show the owner, and on approval apply:

```bash
ghw-label-sync <owner/repo> plan /tmp/claude/label_schema_<unique>.json
ghw-label-sync <owner/repo> apply-delete /tmp/claude/label_schema_<unique>.json
```

Every label the file does not declare is a deletion candidate, which is
how GitHub's stock labels go (stock `bug` matches the kind label and is
updated, not deleted). The plan warns about deletions still attached to
open issues. `apply` creates and fixes drift but deletes nothing; setup
normally wants `apply-delete`. A re-run converges to no change. To change
labels later, rebuild the whole file from `ghw-orient`'s live `labels`
plus the change: a partial file makes every omitted label a deletion
candidate.

## Filing the backlog

Write each body to a file under `/tmp/claude/` with a unique name, then
file with `ghw-issue-create` (its arguments are in `use-github`). It takes
exactly one kind label and at least one `area:` label, checked against the
labels just synced; without a board, the priority label goes with them.
Relationships go in with `ghw-issue-link` once both ends exist.

Work the backlog plan marks as already done, if the owner wants it as
history, is filed first, oldest first so it takes the lowest numbers, and
closed at once with `ghw-issue-close`, which
needs a comment file; one staged comment ("Imported as already-resolved
history") serves every such close.

With a board, set both fields on each filed Issue; `ghw-board-set` adds
the issue to the board if it is not there yet, and an unset `Status` hides
an issue from the board's grouped views:

```bash
ghw-board-set <owner/repo> Priority <P0-P3> <issue#>
ghw-board-set <owner/repo> Status "Needs Triage" <issue#>
```

Use the state the plan gives where it is later than `Needs Triage`. Closed
history, if added to the board, gets `Done`.

## Retiring sources the repo owns

- A tracked file every item of which now has a verdict is removed with
  `git rm`, never shell `rm`, and committed through `gitw-commit`.
- A source-code TODO that became an Issue cites it as `TODO(#N)`, as
  `use-github` teaches. Offer that as its own commit, since it touches
  many files.

## The pointer in `CLAUDE.md`

Look for an existing `## Issue tracking & workflow` heading and rewrite
its body in place; create the section, or the file, if there is none:

```markdown
## Issue tracking & workflow

This project uses **GitHub Issues** for work tracking:
<https://github.com/OWNER/REPO/issues>. Its Tracker Schema is `TRACKER.md`
at the repo root. Priority lives on the
[project board](https://github.com/users/OWNER/projects/N), not on labels.

**Load the `use-github` skill before filing, labeling, or prioritizing an
issue, before writing a `TODO` comment, and before opening a PR.**
```

Without a board, the priority sentence becomes: "Priority is an issue
label (`P0` to `P3`), exactly one per issue."

## Verify

```bash
ghw-orient <owner/repo>
gh issue list --repo <owner/repo> --state all --limit 200
gh project item-list <number> --owner <owner> --limit 200
```

`ghw-orient` shows the labels, the linked board, and its conformance in
one read. The last line applies only with a board. If TODO comments were
converted, search the tree for any left without an issue number. Report
the counts: labels, open and closed issues filed, and board items.

## Recurring triage

A board from `ghw-board-sync` already has every field triage reads. The
rest is `triage-issues`' own setup: its "Standing up triage in a repo"
section, and section 6 of `reference/DEPLOYMENT.md` in that skill's
directory for the `TRIAGE.md` profile and the digest issue. The opaque IDs
the profile needs all come from `ghw-orient`.
