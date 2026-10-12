# fjw issue and label Verbs

**Proposal, ratified 2026-09-14. Not implemented.** This captures the plan as
ratified; [index.md](index.md) tracks its status. It extends the shipped
design in [design.md](design.md), whose invariants (machine-account
identity, config, transport, Exit-code contract, staged bodies, installed
copies, grant form) carry over unchanged and are not restated here.
Implementation deviates only with the deviation called out.

## Problem

The shipped Verbs cover PRs only, so agents cannot read, file, comment on,
label, or close Forgejo issues. A consumer whose task surface is a Forgejo
repo's issues needs all of that. Labels are in scope from the start:
managing a repo's label registry, and adding or removing labels on both
issues and PRs, is table stakes for any issue-tracker-shaped surface. What
stays out is schema prescription: deciding which labels should exist, and
validating against a canonical schema, belongs to a separate setup Skill.

## Principles

- **Issues are living documents; PRs are append-only submissions.** An
  issue moves from placeholder to corrected and expanded over its life, so
  editing in place is expected; reconstructing its current truth from a
  trail of comments is worse for whoever implements it. A PR is close to
  done when opened, and changes append. Hence `fjw-issue-edit` exists and
  `fjw-pr-edit` does not (see design.md's rejected alternatives).
- **No closed-issue edit guard.** Blocking edits on closed issues is
  theater, since the issue can be reopened.
- **The PR/issue index guard is load-bearing.** Forgejo's REST API keeps
  PRs and issues in one index space (the shipped `fjw-pr-comment` already
  posts through `/issues/{index}/comments`). Every `fjw-issue-*` Verb
  checks that its index names a real issue, like `fjw-pr-comments`' PR
  check, but exits 4 where the shipped check exits 3. Without the guard,
  `fjw-issue-comment` would bypass `fjw-pr-comment`'s head-prefix pin,
  and `fjw-issue-edit set-body` would silently rewrite a PR description.
  Symmetrically, `fjw-pr-label` checks that its index names a PR.
- **Schema-free labels.** Label Verbs manage and apply the repo's live
  registry as it is: no canonical type labels, no area contract, no sync
  machinery.
- **Labels encode the project's triage schema; they are not fungible
  data.** Issues and PRs come and go, but a label changing name or meaning
  can break process repo-wide. An edit implies a schema version change or
  a conflicting schema to reconcile, and both want a human. The automated
  use case is first-time creation while initializing a repo; any other
  change to an initialized repo's labels is the signal to stop and ask.
- **Naming follows the PR Verbs.** The plural read and singular write
  pair (`fjw-issue-comments`, `fjw-issue-comment`) mirrors the shipped PR
  siblings. Permission rules end in a literal space before the star, so
  neither rule matches the other; the distinction is cosmetic, not a leak.

## Verb catalog

### Reads

- `fjw-issue-list <owner/repo> [open|closed|all] [label ...]` prints raw
  issue JSON, paginated to exhaustion. Position 2 is a state if and only if
  it is one of the three keywords (default `open`, so the bare call matches
  `fjw-pr-list`); positions 3 and later are server-side label filters,
  ANDed. Label filters therefore need the state spelled out: a label named
  `open` filters as `fjw-issue-list <owner/repo> open open`, a documented
  quirk rather than a hazard, since reads carry no scope tokens. Filters
  exist because duplicate search before filing and "was this settled
  before?" checks need closed issues, and label filtering is the basic
  triage read. It must pass `type=issues`: Forgejo's issues endpoint also
  returns PRs unless filtered.
- `fjw-issue-view <owner/repo> <issue#>` prints one issue; a PR number
  exits 4.
- `fjw-issue-comments <owner/repo> <issue#>` prints the comment array;
  index guard applies.
- `fjw-label-list <owner/repo>` prints the repo's label registry.

### Writes: issue lifecycle

- `fjw-issue-create <owner/repo> <title> <body-file> [label ...]` files an
  issue. Each trailing label must exist in the live registry; unknown
  labels exit 4, named. That is typo refusal against what exists, not
  schema prescription. Labels are payload, not scope tokens: grants pin
  the repo. Deliberately not idempotent, like `ghw-issue-create`; searching
  for duplicates stays Skill guidance.
- `fjw-issue-comment <owner/repo> <issue#> <body-file>` posts a staged
  comment; index guard applies. It has no scope token like
  `fjw-pr-comment`'s head prefix, and repo-pinned grants suffice. Branches
  give PRs a natural ownership namespace fixed at creation; issues have
  none. A label pin is mutable by anyone who can add labels, and a creator
  pin breaks the main use case (noting progress on human-filed issues).
  Comments are append-only, attributed, and auditable. The accepted cost:
  adding a positional pin later changes the arity and breaks existing
  grants, a migration paid if a consumer ever needs it.
- `fjw-issue-edit <owner/repo> <retitle|set-body> <issue#> <value>`. The
  subverb at position 2 lets a grant pin `retitle` without `set-body`.
  `set-body` takes a staged file path; `retitle` takes an inline string.
  Label changes are not edit subverbs, so each operation has one spelling.
- `fjw-issue-close <owner/repo> <issue#> <comment-file>` closes with a
  mandatory comment, matching `fjw-pr-close`: a silent close must be
  inexpressible, and the comment is the audit record ("done because X, see
  commit Y"). The comment posts first, then the close; an already-closed
  issue is a no-op success that posts nothing. The mandatory close comment
  is meant to hold across Wrapper families: `ghw-issue-close` should
  require one too, with forge automation's auto-close on PR merge as the
  one sanctioned exception.
- `fjw-issue-reopen <owner/repo> <issue#> <comment-file>` is its own Verb,
  not an edit subverb: reopening is a state change with a reason ("closed
  in error", "regressed"), and a separate Verb keeps it separately
  grantable. Comment mandatory, as for close. It sits in a higher tier than
  close: an agent that may close its own finished work does not thereby
  get to resurrect anything.

### Writes: labels

Adding and removing labels is a symmetric standalone pair on both
surfaces, unlike ghw's labels-as-edit-subverbs: with no `fjw-pr-edit`, PR
labeling needs a standalone Verb anyway, and one operation should be
spelled the same way on both surfaces. Registry management is separate from
assignment because the blast radii differ.

- `fjw-issue-label <owner/repo> <add|remove> <issue#> <label>`: subverb at
  position 2 (grant `add` without `remove`); idempotent; issue index guard.
- `fjw-pr-label <owner/repo> <add|remove> <pr#> <label>`: same grammar;
  PR index guard.
- `fjw-label-create <owner/repo> <name> <color> [description]`: short
  inline arguments, like PR titles.
- `fjw-label-edit <owner/repo> <rename|recolor|redescribe> <name>
  <value>`: subverb at position 2, like `fjw-issue-edit`.
- `fjw-label-delete <owner/repo> <name>`: its own Verb, never a flag, so
  deletion is separately grantable. It refuses (exit 4) while the label is
  on any open issue or PR, reporting the count and example indices; the
  path forward is the visible two-step of removing it from the open items,
  then deleting. With attachments only on closed items it proceeds and
  reports the closed-attachment count in its plan, so the history cost
  (deletion detaches closed items too) is in the audit record. Blocking
  there would push agents to the worse workaround of stripping labels off
  closed issues. It is the one fjw Verb that scans the whole repo before
  acting, which is acceptable for a rare destructive operation.

### Deferred with a sketch

- **Issue dependencies** (Forgejo's blocked-by/blocks relation, the
  counterpart of `ghw-issue-link`'s blocked-by half; Forgejo has no
  sub-issue hierarchy as of this proposal). Deferred, not rejected,
  because the first use case is a flat task list. It can land later as
  `fjw-issue-dep <owner/repo> <add|remove> <issue#> <other-issue#>`
  without disturbing anything here.

### Non-Verbs

- **Merge**: absent, as in the shipped design.
- **`fjw-pr-edit`**: see Principles.

## Capability tiers

Each Verb's default disposition, by the tier of agent capability that
should hold it. A deployment renders these into Permission rules; every
Verb must have a disposition.

| Tier | Disposition | Verbs |
|---|---|---|
| reader | allow | `fjw-issue-list`, `fjw-issue-view`, `fjw-issue-comments`, `fjw-label-list` |
| contributor | allow | `fjw-issue-create`, `fjw-issue-comment`, `fjw-issue-close` |
| triage | allow | `fjw-issue-edit`, `fjw-issue-reopen`, `fjw-issue-label`, `fjw-pr-label`, `fjw-label-create`, and later `fjw-issue-dep` |
| triage | ask | `fjw-label-edit` (labels encode the triage schema) |
| admin | ask | `fjw-label-delete`; denied below admin, never allowed anywhere |

Contributor covers participation: filing, commenting, closing with a
comment. Triage changes the surface in place: retitling, rewriting bodies,
reopening, labeling, and relinking. `fjw-label-create` sits in triage
because first-time creation during repo setup is the automated use case.

**Accepted leak.** A contributor can pass trailing labels to
`fjw-issue-create`. Labels are payload past the repo pin, and the Wrapper
does not know the caller's tier, so neither the Permission rule nor the
Wrapper can strip them. This is accepted on principle: classifying your own
new issue is part of filing it, triage governs changing the surface in
place, and mislabeled filings are what triage is for.

## Grant grammar

Permission rules use the shipped space-star form, with the repo always
pinned at position 1.

- **Repo pin only:** `fjw-issue-list`, `fjw-issue-view`,
  `fjw-issue-comments`, `fjw-label-list`, `fjw-issue-create`,
  `fjw-issue-comment`, `fjw-issue-close`, `fjw-issue-reopen`,
  `fjw-label-create`, `fjw-label-delete`.
- **Subverb also pinnable at position 2:** `fjw-issue-edit`
  (`retitle`, `set-body`), `fjw-issue-label` (`add`, `remove`),
  `fjw-pr-label` (`add`, `remove`), `fjw-label-edit` (`rename`,
  `recolor`, `redescribe`).
- `fjw-label-edit` and `fjw-label-delete` render as `ask` rules; nothing
  renders `fjw-label-delete` as `allow`.

## 404 disambiguation

Forgejo answers 404 for a repo the caller may not see, so a missing grant
reads as a missing resource. The shipped `fjw-pr-create` already misreports
this way (see index.md's Known gaps), and every issue Verb's index guard
walks the same path with more causes (no such issue, it is a PR, the repo
is invisible). The fix lives in the shared `cli/lib/forgejo` layer. It was
ratified to ship with this work; it is now planned to ship ahead of it
(see Implementation notes):

- **Lazy.** No extra call on the happy path. Only when a resource-level GET
  404s does the library probe `GET /repos/{owner}/{repo}` once.
- **Repo visible:** the resource is really missing, and the Verb keeps its
  contextual handling. A missing branch still says "push it first"; a
  missing issue is exit 3; a PR number given to an issue Verb is the
  exit-4 index guard.
- **Repo also 404:** exit 3, with a message naming both possibilities:
  the repo does not exist, or this identity cannot see it; if the slug is
  right, the machine account lacks a grant, so report to the user. Exit 5
  was rejected: a mistyped slug and a missing grant are indistinguishable
  by the server's design, so 3 is the honest class, and the escalation
  guidance travels in the message and Skill text rather than in a falsely
  certain exit code.
- Held loosely: if real use shows this classification misbehaving, the
  approach changes.

## Empirical probes before acceptance

- Whether a Read-collaborator machine account may create, edit, close, and
  label issues, and manage the label registry. The `write:issue` token
  scope is already required, but the server-side grant is the real control
  and is unverified for issue writes.
- Whether Forgejo's label API adds and removes by name or requires IDs. The
  Wrapper resolves names against the live registry either way; the probe
  decides how.
- Whether Forgejo records edit history for issue title and body PATCHes, so
  that `fjw-issue-edit` is audited mutation rather than history
  destruction.

## use-forgejo changes

A catalog section for the new Verbs, mirroring the existing one
(signatures, exit codes, output shapes), plus conventions:

- Index-guard exit 4 means the number names the other kind: use the
  sibling Verb.
- Close and reopen comments are mandatory; they are the audit record.
- Create is not idempotent: search open and closed issues before filing.
- An unknown-label exit 4 means fix the call. Never create a label to
  satisfy a typo; label edits are human-gated because labels encode the
  triage schema.
- A repo-level 404 with a correct slug is a missing grant: report it to
  the user; never retry, never hunt for credentials.

After the changes, an editorial pass checks that the whole Skill is
coherent, carries only what an operating agent needs (no history, dates, or
prior-version residue), and is as concise as clarity allows.

## Implementation notes

These notes reflect the repo's layout as of 2026-10-01.

- New `cli/lib/forgejo/issues.py` and `cli/lib/forgejo/labels.py` beside
  `pulls.py`; flat entry points in `cli/`, `#!/usr/bin/python3`,
  3.9-compatible, stdlib only; offline tests with the network mocked.
- Ship through the Installer; Skill text invokes Verbs by bare name and
  stays consumer-generic.
- The 404 disambiguation helper is planned as a separate fix to the
  shipped Verbs (index.md, Known gaps); these Verbs will reuse it.
- The issue-index guard's exit 4 differs from the shipped
  `fjw-pr-comments` check, which exits 3 for an issue index; aligning the
  two is an open decision.
- Run the empirical probes before relying on the behavior they cover; the
  Read-collaborator issue-write probe must pass live before acceptance.
