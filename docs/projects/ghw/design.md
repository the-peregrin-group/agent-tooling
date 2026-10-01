# ghw design

How the GitHub Wrapper works and why: architecture, invariants, the Verb
catalog, and the alternatives ruled out. Status lives in [index.md](index.md);
this document describes the code as it is.

## Problem

Raw `gh` cannot encode scope in a way a Permission rule's command-prefix match
can pin. Flags are freely ordered, mutations hide behind `gh api`, and "write
to this repo only" or "comment but never merge" is inexpressible. A consumer
either grants raw `gh` (and with it every write the token allows) or approves
every call by hand: permission fatigue in attended sessions, hangs in
unattended ones. Separately, every board write costs an agent several calls
of context-burning inference (label lookups, ProjectV2 field and option-ID
resolution) before the write itself.

## Core invariants

1. **Scope first, in rigid positional order.** Everything
   blast-radius-relevant (repo, Verb mode, base branch, merge strategy, field
   name) appears left of where a Permission rule's wildcard sits, in fixed
   order; free-form content (titles, bodies, labels) comes after. A rule's
   literal prefix *is* the grant. Corollary: destructive escalation is never a
   trailing flag, because trailing flags sit under the wildcard and are
   silently approved; escalation is a positional mode. The only trailing flags
   are ones that cannot widen blast radius: `--draft` on `ghw-pr-create` (a
   de-escalation) and `--project` on `ghw-board-set` (narrows a grant already
   given).
2. **Trust but verify scope claims.** Where a scope argument is a claim about
   an existing object rather than a parameter of the operation, the Verb
   verifies it and fails loudly on mismatch (e.g. `ghw-pr-merge` checks the
   PR's actual base branch). `<repo>` is always passed explicitly, so the
   working directory can never redirect a write.
3. **No scope overrides in the tail.** Verbs never honor scope-relevant flags
   after the positional block (no late `--repo`).
4. **The Wrapper enforces the contracts.** The three GitHub Skills form one
   ecosystem, and every Verb enforces its shared contracts (label schema,
   priority regime, canonical board schema) in code rather than trusting the
   caller.
5. **Idempotency is a contract** for every `-sync` and `-set` Verb, and for
   `ghw-issue-edit`, `ghw-issue-close`, and `ghw-issue-link`: declarative
   desired state, re-runs are converged no-ops. Deliberate exception:
   `ghw-issue-create`, which is inherently not idempotent; duplicate search
   stays in `use-github`'s text as guidance.
6. **No ghw Permission rules at user level, reads included, and no
   `allowed-tools` grant.** Grants live in each repo's project or local
   settings, scoped to that repo's risk profile. Even `ghw-orient` is granted
   per repo, because it exposes the label registry and board structure of any
   repo the token can see. `use-github`'s frontmatter carries no
   `allowed-tools` entry: such a grant is repo-unpinned for the length of the
   Skill invocation, the same exposure a user-level read rule would create.
7. **Unattended triage writes only through the `triage-*` wrappers.** Those
   six wrappers are the only autonomous write path; how the boundary is kept
   is in Unattended triage.
8. **Command-string ask and deny rules do not reach a Verb's subprocesses.**
   Rules match the Bash command string; a Verb's internal `gh` calls never
   produce one, so `gh api` ask or deny rules do not apply to them. Each
   Verb's own validation is the only guard, which obligates airtight
   validation in every write Verb.
9. **File arguments come only from the agent's staging directories.** Every
   Verb that reads a file (`<body-file>`, `<comment-file>`, and
   `ghw-label-sync`'s `<schema-file>`, whose names and descriptions get
   published) resolves symlinks and accepts only paths under `/tmp/claude/` or
   `~/.claude/jobs/<job-id>/tmp/`, UTF-8 only; anything else is exit 2 with a
   self-correction hint. The check lives once, in `cli/lib/staging.py`.
   Rationale: a granted write Verb that reads an arbitrary path is a
   promptless exfiltration channel. The Read tool's deny rules for `.ssh`,
   `.env` and the like do not reach a subprocess's own reads, so without this
   a granted `ghw-issue-comment <repo> *` would publish any file on disk.
   Restricted to staging, a Verb never reads anything the agent could not, and
   every body first passes through a visible, permission-mediated Write.
10. **Merging is a human act.** `ghw-pr-merge` is never granted to unattended
    agents absent project rules that say otherwise, and `use-github` merges
    only when the user has said to. History policy is `use-git`'s: squash is
    banned in every repo, so `merge` is the only strategy to use.

## Placement and invocation

- Source: `cli/ghw-*` and `cli/lib/` in this repo, with unit tests beside
  them (`cli/ghw_*_test.py`, `cli/lib/**/*_test.py`). The Installer installs
  them into `~/.local/libexec/agent-tooling/`, which is on PATH, and the
  Skills into `~/.claude/skills/`; the installed trees are never edited.
- Verbs are invoked by bare name, never by path or through `python3`. The
  permission matcher is a literal prefix match, so exactly one invocation form
  can match the rules that grant it.
- Python 3 stdlib only, shebang `#!/usr/bin/env python3`. There is no venv or
  lockfile a bare command name could express, so any third-party dependency
  would be an unmanaged machine-local install; stdlib-only removes
  supply-chain risk and cross-machine skew at no cost, since `gh` does the API
  work and the Python only orchestrates. Corollary: the `ghw-label-sync`
  schema file is JSON, never YAML.
- Positional parsing is hand-rolled (see Rejected alternatives).
- Permission rules approve command strings, not binaries: whatever a name
  resolves to on PATH is what runs, so anything earlier on PATH shadows it.
  This is accepted for a single-user machine and stated so the assumption is
  explicit.

## Verb catalog

### Read

- `ghw-orient <repo>`: one JSON blob replacing a multi-call orientation:
  repo identity, the live label registry, every **open** linked ProjectV2
  board with its field and option name-to-ID maps, which board is canonical
  and by which rule (see Board disambiguation), a `canonical_note`, the
  priority regime (`board-field`, `p-labels`, or `unknown` when boards exist
  but none is canonical or the Priority field is missing or nonconforming),
  and `priority_labels_present`. Each board carries a conformance verdict
  against the canonical board schema: `conforms` is false on any gap (an
  absent field, a field of the wrong data type, a missing canonical option).
  A missing `Size` is the one tolerated gap, reported separately, and extra
  user-authored options are advisory `extra_options`. Extras cannot break a
  Verb, which only writes canonical options; a missing state breaks
  `ghw-board-set` outright. The canonical-board choice is advisory: every
  board ships its full map, and write-side choice belongs to
  `ghw-board-set --project`. IDs resolve live on every call.

### Day-to-day writes

- `ghw-issue-create <repo> <type-label> <title> <body-file> [label ...]`:
  requires exactly one canonical type label (`feature`, `improvement`, `bug`,
  `debt`, `meta`) and at least one `area:` label; otherwise accepts any label
  in the repo's live registry that is not a second type label (which admits
  `setup-github-issues`' unprefixed scope labels for multi-site repos). The
  registry is the attachment authority, and `ghw-label-sync` is the only way
  labels get created. `TRIAGE.md` plays no part in label validation.
- `ghw-issue-comment <repo> <issue#> <body-file>`.
- `ghw-issue-edit <repo> <add-label|remove-label|retitle|set-body> <issue#>
  <value>`: the subverb at position 2 lets a grant include label edits while
  withholding `set-body`, since an arbitrary body rewrite belongs to triage's
  proposed-mutation class. `set-body` takes a staged file, never inline text.
  `add-label` applies the attachment contract and refuses a second type
  label, naming the incumbent; reclassifying takes two visible calls. Each
  subverb converges to a no-op when already satisfied.
- `ghw-issue-close <repo> <issue#> [comment-file]`: its own Verb, never a flag
  on edit, so closing is independently grantable. The comment is optional.
  Closing an already-closed issue is a converged no-op, and a supplied comment
  is then not posted, since the close it explains did not happen here.
- `ghw-issue-link <repo> <add-sub|remove-sub|add-blocked-by|remove-blocked-by>
  <issue#> <other-issue#>`: a thin validating Verb over `gh issue edit`'s
  native flags, with a runtime check for `gh` 2.94.0 or later. `<issue#>` is
  always the subject (the parent, or the blocked issue). "X blocks Y" is
  spelled `add-blocked-by Y X`; there are no blocking subverbs, so each
  relationship has one spelling. Issue numbers only. Self-links are refused,
  edges to other repos are ignored, and when the edge list comes back
  truncated without the target in it, the Verb refuses (exit 1) rather than
  guess.
- `ghw-board-set <repo> <field-name> <option-name> <issue#> [--project <n>]`:
  the field name at position 2 lets `ghw-board-set <repo> Priority *` grant
  Priority without Status. Adds the issue to the board if missing, then sets
  the field; refuses fields that are not single-select; reports
  `changed: false` when already set. `use-github` keeps Status writes
  conservative: `Needs Triage` on filing, and only on a conforming board;
  transitions belong to triage.
- `ghw-pr-create <repo> <base-branch> <head-branch> <title> <body-file>
  [--draft]`: the head branch is explicit, never inferred from the working
  directory, so an agent in the wrong worktree cannot open a PR nobody meant
  to ship. Both branches must exist on the remote and differ; when the
  checked-out branch differs from `<head-branch>` the Verb warns but does not
  refuse. Always created through the REST `POST /repos/{owner}/{repo}/pulls`
  endpoint, which needs no local git context. Non-draft by default.
- `ghw-pr-comment <repo> <pr#> <body-file>`: its own Verb because
  `gh issue comment` refuses PR numbers.
- `ghw-pr-merge <repo> <base-branch> <strategy> <pr#>`: the strategy is a
  positional mode, so a Permission rule pins it. It accepts `merge` or
  `squash`; squash is banned by policy (invariant 10), and removing the token
  is a Known gap in [index.md](index.md). Gates, all required: the PR
  is open, its actual base equals `<base-branch>`, it is not a draft, and its
  checks are green or absent (pending blocks). The merge is pinned to the
  head commit that passed the gates. There is no force or override path:
  merging over red checks is a human using raw `gh`. Never deletes the head
  branch, since a worktree may still have it checked out. Many repos have no
  branch protection, so these gates are the only enforcement.

### Schema sync (bootstrap-grade, declarative)

- `ghw-label-sync <repo> <plan|apply|apply-delete> <schema-file>`: the five
  canonical type labels and colors come from the shared constants; the JSON
  schema file supplies only the repo's families:
  `{"priority_labels": <bool>, "area": [{name, description, color?}…],
  "scope": […]}`. `area` names are written bare and the Verb adds the
  prefix; `priority_labels: true` adds P0 to P3 to the desired set, so on a
  label-regime repo `apply-delete` cannot delete the repo's own priority
  labels. Anything else in the repo is a deletion candidate, which clears
  eight of GitHub's nine stock labels at bootstrap (stock `bug` is a
  canonical type label). `plan` is a pure read printing the full diff.
  `apply` creates and fixes color and description drift, and prints deletes
  without executing them. `apply-delete` also executes the deletes, open
  issues included; deletion authority is granted by granting that mode. In
  every mode, deletion candidates attached to open issues are listed on
  stderr (and in the JSON plan), because `plan` is exactly where a human
  decides whether to grant deletion. Case-only mismatches are reported;
  creates run before deletes; a partial failure lists the writes that landed.
- `ghw-board-sync <repo> <project#|new>`: one canonical board schema:
  `Priority` (P0 to P3), `Status` (the eight canonical triage states),
  `Size`, `Last Triaged`. Given a project number, it creates missing fields
  and **reports, never edits**, drift on existing ones: mutating a live
  single-select's options can orphan assigned values. On an existing board a
  missing `Size` is reported, not created, matching triage's tolerance of an
  unused `Size`. Given `new`, it refuses if an open board is already linked;
  otherwise it creates a ProjectV2 titled after the repo, links it, and
  provisions the schema. The one Status edit it ever makes is replacing the
  stock options on that freshly created board. If provisioning fails midway,
  the error names the half-built project and says not to re-run `new`.
  Creating boards is `setup-github-issues`' job by convention, so every
  bootstrapped repo is triage-ready from birth.

### Board disambiguation

`ghw-board-set` and `ghw-orient` resolve the canonical board among **open**
linked boards by these rules, which `ghw-orient` names in its output:

- `only-linked`: exactly one board is linked; use it (orient still notes a
  disagreeing `TRIAGE.md`);
- `triage-md`: several are linked, and a `TRIAGE.md` found from the working
  directory decides, but only if the repo it declares matches `<repo>` and the
  board it names is linked (trust but verify: otherwise a session in an
  unrelated directory would apply another repo's profile);
- `none-linked` and `ambiguous`: no canonical board; `ghw-orient` reports the
  candidates and write Verbs refuse with exit 2.

`TRIAGE.md` discovery walks upward from the working directory and stops at
the enclosing git work tree's root; outside a work tree there is no
discovery, so a stray `TRIAGE.md` in `/tmp` or `$HOME` can never decide a
repo's board. Triage's `lib_profile.py` applies the same bound.

A trailing `--project <number>` on `ghw-board-set` overrides the choice. It
is safe in trailing position because the rule's prefix already granted
writes to this repo, and the flag only narrows which board is touched.

### Deliberately not Verbs

- `triage-inventory` and `triage-timeline`: triage-shaped bulk reads, already
  read-only and separately granted; bulk reads stay there.
- Triage's proposed-mutation set (status, priority, and size transitions,
  scope-body rewrites, closes, reparenting) has no autonomous path by design
  (see Unattended triage).
- Anything git: that is gitw and `use-git`.

## Shared conventions

- **Exit codes, as implemented:** `0` success, including a converged no-op;
  `1` any `gh` or API failure; `2` a usage error or any policy refusal, at
  parse time or after (label contract, merge gates, an unlinked `--project`,
  a missing head or base branch, `ghw-board-sync new` on an already-boarded
  repo). The `triage-*` wrappers use the same three codes. ghw does not yet
  use the shared taxonomy's codes 3 to 6; see the
  [Exit-code contract](../../index.md#exit-code-contract). Callers key on
  exit 2 for every refusal today, so splitting refusals across the taxonomy
  changes that contract for them.
- **JSON output:** write Verbs print a JSON plan with `"action": "applied"`
  (or `"plan"`, from `ghw-label-sync plan` only), most with a `changed`
  field. `ghw-orient` prints its own blob.
- **Bodies always through a staged file** (invariant 9), with the staging
  path typed literally: never `$CLAUDE_JOB_DIR`, which the harness blocks as
  shell expansion, and never heredocs or command substitution.
- **Usage errors that self-correct:** rigid positional signatures make
  mistakes fail at the Verb, so the message must let an agent fix the call in
  one round trip.
- **Triage-owned body structures are load-bearing:** the scoped-issue
  template (Problem / Goal / Acceptance criteria / User experience / Out of
  scope / Links), `## Design decisions` sections, the `**Blocked on:**`
  marker, and the parent tracker's `- [ ] All children created (scope
  locked)` checkbox. The Verbs do not parse them; the Skill texts warn
  `set-body` callers not to stomp them.

## Shared library

- `cli/lib/` (forge-neutral, shared with the other Wrappers): `schema.py` is
  the single home for the type labels and colors, P0 to P3, area and scope
  colors, canonical field names, the eight Status states with their exact
  casing (title case like `Needs Triage` beside sentence case like
  `In progress`), the terminal-state set, and Size XS to XL. Also
  `staging.py` (invariant 9), `plan.py` (JSON plan and exit codes), and
  `arguments.py` (repo charset check, issue-number parsing).
- `cli/lib/github/`: `gh.py` is the subprocess layer. Every call has a
  120-second timeout with stdin closed when nothing is piped, so a prompting
  subcommand or stalled connection fails loudly instead of hanging an
  unattended run; non-JSON or dataless responses raise `GhError` rather than
  escaping as tracebacks. `boards.py` (orientation, disambiguation, `TRIAGE.md`
  discovery, board mutations), `labels.py` (attachment contract),
  `label_schema.py`, `board_schema.py` (conformance and provisioning), and
  `pulls.py` (merge gates) sit on it.
- Name-to-ID resolution is live on every call, with no on-disk cache (see
  Rejected alternatives).

The `triage-*` wrappers do not use this library yet: they carry their own
`lib_gh.py` and `lib_profile.py`, and `triage-apply-sync` declares its own
terminal-state set. The planned rebase is
[triage-library-rebase.md](triage-library-rebase.md).

## Skills

- **use-github** is wrapper-first end to end: orientation through
  `ghw-orient`, the invocation form and literal staging paths, and the
  guidance no Verb can absorb (search before filing, Status conservatism,
  linkage keywords: `Closes #N` auto-closes while `furthers`, `part of`, and
  `towards` link without closing; the `TODO(#N)` rule).
- **setup-github-issues** bootstraps labels with `ghw-label-sync` (its JSON
  schema file declaring the `area:` and scope families) and the board with
  `ghw-board-sync <repo> new`, so the full canonical schema, `Size`
  included, exists from day one; boards that predate `Size` are tolerated by
  board-sync's report-only behavior. It points to `use-github` as the
  canonical GitHub layer, and to `triage-issues` for the optional `TRIAGE.md`
  and ledger-issue bootstrap, which is per-repo policy rather than board
  schema.
- **triage-issues** points to `use-github` as the canonical layer and keeps
  its own `triage-*` wrappers for autonomous writes. They live in
  `skills/triage-issues/reference/`, install with the Skills, and are the one
  exception to bare-name invocation: they run as `python3 <path>` (see
  Permission rules).

## Permission rules

Every rule uses the space-star form, `Bash(ghw-orient <repo> *)`, never the
colon form. The matcher is a plain string-prefix match, so the literal space
before `*` supplies the token boundary: a rule ending `… release *` cannot
match `… release-2 …`, while `release:*` would. A space-star rule also
matches the bare command with no trailing arguments, so no separate exact
rule is needed (see Evidence).

- **User level:** no ghw rules (invariant 6). The cost is one prompt when
  orienting in a repo with no project grants yet, which is the attended
  `setup-github-issues` bootstrap case. `ghw-label-sync` gets no user-level
  rule either: `plan` lists open issues' numbers, titles, and URLs for every
  deletion candidate, more exposure than orient. The six `triage-*` wrappers
  are granted at user level, in the exact `python3 <path>` form they are
  invoked with.
- **Per repo (project or local settings):** grant Verb by Verb, pinned to the
  repo. A typical day-to-day core: `ghw-orient`, `ghw-issue-create`,
  `ghw-issue-comment`, `ghw-issue-edit` with `add-label`, `remove-label`, and
  `retitle` only (`set-body` withheld), `ghw-issue-close`,
  `ghw-board-set <repo> Priority` (Status withheld), and `ghw-pr-comment`.
  Add `ghw-pr-create` pinned to a base branch where agents open PRs, and
  `ghw-label-sync <repo> plan` where needed. No `ghw-pr-merge` grant unless
  the repo's own rules put merging into a designated branch in agents' hands
  (invariant 10).
- **Granularity is the point.** Comment without merge, label edits without
  `set-body`, merge into one branch and not another: each is expressed by
  which rules exist, not by Wrapper configuration. There are no side-channel
  policy files; all policy is visible in settings.

## Unattended triage

An unattended triage pass runs deny-by-default (`--permission-mode dontAsk`)
with only the six `triage-*` wrappers granted, so any other write (raw `gh`,
a status transition) is denied rather than executed: the permission boundary
equals the autonomy boundary. Never `bypassPermissions`, which would approve
a stray proposed mutation.

The launch form this design endorses is a background job dispatched by a
guard script
([DEPLOYMENT.md](../../../skills/triage-issues/reference/DEPLOYMENT.md) §4's
fallback recipe today; the shipped triage docs still lead with retired forms,
see Known gaps in [index.md](index.md)): a `launchd` agent or `SessionStart`
hook runs a script that skips if today's pass already ran, takes an atomic
lock, and dispatches `claude --bg` from the project directory with
`--permission-mode dontAsk` and Edit grants scoped to the run's own worktree
and job tmp directory.

Normal launches load user, project, and local settings, so ghw write grants
in a repo's project or local settings reach an unattended pass launched
there and give it a second write path. The posture is avoidance: unattended
triage is not hosted in such a repo. A mechanism that isolates the pass from
those grants will be built when a repo needs both.

## Evidence

Point-in-time observations behind claims above:

- Issue dependencies work on GitHub's Free plan: confirmed 2026-08-11 by
  adding and removing a real blocked-by edge, verified server-side through
  `gh issue view --json blockedBy`.
- The `blockedBy` and `subIssues` response shapes `ghw-issue-link` parses
  were confirmed 2026-08-16 against a live dependency edge.
- Space-star rules cover the bare command and hold the token boundary:
  confirmed 2026-08-16 in a live session, where the pinned repo's bare
  `ghw-orient` ran promptless while a sibling-prefix repo and another repo
  both prompted.
- Unverified: whether `gh`'s remove flags work on dependency or sub-issue
  edges created under older server-side states (GraphQL documents
  `addBlockedBy` but no remove mutation). Removal works on fresh edges.

## Rejected alternatives

- **Global (user-level) read rules.** Even reads are repo-pinned: orient
  exposes the label registry and board structure of any repo the token can
  see.
- **An `allowed-tools` grant in `use-github`**, even for `ghw-orient` alone:
  it is repo-unpinned for the whole Skill invocation.
- **`argparse`.** It accepts flags intermixed with positionals, which breaks
  invariant 3; the scoped positional block is hand-parsed.
- **An on-disk ID cache.** It buys an invalidation problem to save one API
  round trip per board write, invisible to agent context. It can drop in
  behind the same interface if latency ever hurts.
- **Destructive modes as trailing flags** (e.g. `--delete`): a trailing flag
  sits under the rule's wildcard and is approved silently.
- **Excluding the project settings layer at launch** to keep ghw grants out
  of an unattended pass: fail-open, since forgetting the flag once on any
  launch turns `dontAsk` plus project grants into silent autonomous writes.
- **Scattered user-level denies** to cancel project grants: deny does win
  across layers, but a deny list must track every grant everywhere.
