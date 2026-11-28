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
   after the positional block (no late `--repo`). More strictly, a Verb
   accepts exactly its usage line: a surplus positional or an unrecognized
   flag is exit 2, and `ghw-issue-create`'s label tail refuses a
   flag-shaped label before it fetches the registry. A middle-wildcard
   Permission rule is only as tight as this; the
   [argument contract](../../index.md#argument-contract) states it and its
   reason.
4. **The Wrapper enforces the contracts.** The three GitHub Skills form one
   ecosystem, and every Verb enforces its shared contracts (the repo's
   Tracker Schema, the priority regime, the canonical board schema) in code
   rather than trusting the caller.
5. **Idempotency is a contract** for every `-sync` and `-set` Verb, and for
   `ghw-issue-edit`, `ghw-issue-close`, and `ghw-issue-link`: declarative
   desired state, re-runs are converged no-ops. Deliberate exception:
   `ghw-issue-create`, which is inherently not idempotent; duplicate search
   stays skill guidance (the discipline in `create-issue`, the command in
   `use-github`).
6. **No ghw Permission rules at user level, reads included, and no
   `allowed-tools` grant.** Grants live in each repo's project or local
   settings, scoped to that repo's risk profile. Even `ghw-orient` is granted
   per repo, because it exposes the label registry and board structure of any
   repo the token can see. `use-github`'s frontmatter carries no
   `allowed-tools` entry: such a grant is repo-unpinned for the length of the
   Skill invocation, the same exposure a user-level read rule would create.
7. **Unattended triage writes only through the `triage-*` wrappers.** Those
   six wrappers are the only writes an unattended pass is granted; how that is kept
   is in Unattended triage.
8. **Command-string ask and deny rules do not reach a Verb's subprocesses.**
   Rules match the Bash command string; a Verb's internal `gh` calls never
   produce one, so `gh api` ask or deny rules do not apply to them. Each
   Verb's own validation is the only guard, which obligates airtight
   validation in every write Verb.
9. **File arguments come only from the agent's staging directories.** Every
   Verb that reads a file (`<body-file>`, `<comment-file>`) resolves
   symlinks and accepts only paths under `/tmp/claude/` or
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
- Python 3 stdlib only, shebang `#!/usr/bin/python3`, the
  same pin as the gitw, fjw, and bdw wrappers (the system interpreter is the
  one macOS grants privacy permissions to; no PATH lookup can land elsewhere).
  There is no venv or
  lockfile a bare command name could express, so any third-party dependency
  would be an unmanaged machine-local install; stdlib-only removes
  supply-chain risk and cross-machine skew at no cost, since `gh` does the API
  work and the Python only orchestrates. Corollary: the part of a repo's
  `TRACKER.md` the Verbs read is a JSON block, never YAML.
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
  `ghw-board-set --project`. It also reads the repo's Tracker Schema,
  prints its warnings, and reports under `tracker_schema` which file it
  read, whether it could be read, and how many warnings it gave. IDs
  resolve live on every call.

### Day-to-day writes

- `ghw-issue-create <repo> <kind-label> <title> <body-file> [label ...]`:
  holds the labels to the label attachment contract, which comes from the
  repo's Tracker Schema: `<kind-label>` is one of its Issue Kinds and no
  second kind is among the labels; every label is one the schema declares
  (a kind, a priority, an axis's label, or a label on no axis), so a label
  that exists on GitHub but not in the schema is refused; and every axis
  the schema marks as carried by every Issue has a label among them. Every
  label must also exist in the live registry, since `ghw-label-sync` is the
  only way labels get created. `TRIAGE.md` plays no part in label
  validation.
- `ghw-issue-comment <repo> <issue#> <body-file>`.
- `ghw-issue-edit <repo> <add-label|remove-label|retitle|set-body> <issue#>
  <value>`: the subverb at position 2 lets a grant include label edits while
  withholding `set-body`, since an arbitrary body rewrite is a write a repo
  may want to withhold. `set-body` takes a staged file, never inline text.
  `add-label` applies the attachment contract and refuses a second kind
  label, naming the incumbent; reclassifying takes two visible calls.
  `remove-label` refuses to remove an issue's last label on an axis the
  schema marks as carried by every Issue. Each subverb converges to a no-op
  when already satisfied.
- `ghw-issue-close <repo> <issue#> <comment-file>`: its own Verb, never a flag
  on edit, so closing is independently grantable. The comment is mandatory (a
  missing or blank one is exit 2): it is the audit record of why the issue was
  closed, so a silent close is inexpressible through this Verb; forge
  auto-close on PR merge is the one sanctioned comment-less close. Closing an
  already-closed issue is a converged no-op, and the comment is then not
  posted, since the close it explains did not happen here.
- `ghw-issue-link <repo> <add-sub|remove-sub|add-blocked-by|remove-blocked-by>
  <issue#> <other-issue#>`: a thin validating Verb over `gh issue edit`'s
  native flags, with a runtime check for `gh` 2.94.0 or later. `<issue#>` is
  always the subject (the parent, or the blocked issue). "X blocks Y" is
  spelled `add-blocked-by Y X`; there are no blocking subverbs, so each
  relationship has one spelling. Issue numbers only. Self-links are refused,
  edges to other repos are ignored, and when the edge list comes back
  truncated without the target in it, the Verb refuses rather than guess.
- `ghw-board-set <repo> <field-name> <option-name> <issue#> [--project <n>]`:
  the field name at position 2 lets `ghw-board-set <repo> Priority *` grant
  Priority without Status. Adds the issue to the board if missing, then sets
  the field; refuses fields that are not single-select; reports
  `changed: false` when already set. `use-github` keeps Status writes
  conservative: `Needs Triage` by default on filing, and only on a
  conforming board; a later move is judged against the repo's Issue State
  Diagram (`work-issue`).
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
  positional mode, so a Permission rule pins it. It accepts only `merge`
  and refuses `squash`, because squash is banned by policy
  (invariant 10); the slot stays so existing Permission rules keep matching.
  Gates, all required: the PR
  is open, its actual base equals `<base-branch>`, it is not a draft, and its
  checks are green or absent (pending blocks). The merge is pinned to the
  head commit that passed the gates. There is no force or override path:
  merging over red checks is a human using raw `gh`. Never deletes the head
  branch, since a worktree may still have it checked out. Many repos have no
  branch protection, so these gates are the only enforcement.

### Schema sync (bootstrap-grade, declarative)

- `ghw-label-sync <repo> <plan|apply|apply-delete>`: takes no file. The
  desired labels are exactly what the repo's Tracker Schema declares: every
  Issue Kind as its Kind Label, every Issue Priority where the repo carries
  priority as labels, every axis's labels, and every label on no axis, each
  with the schema's name, meaning as its description, and colour. Whether
  priority is carried as labels is the priority regime `ghw-orient` reports
  from the board: on `p-labels` the priorities are desired labels, on
  `board-field` they are not (so live priority labels are deletion
  candidates), and on `unknown` they are neither created nor deleted, with a
  warning. A meaning longer than GitHub's 100-character limit for a label
  description is cut at a word boundary and ends in `...`. Two declared
  names that GitHub would treat as one label (they differ only in case) are
  kept once, the first declared, with a warning. Anything else in the repo
  is a deletion candidate, which clears GitHub's stock labels at bootstrap
  unless the schema declares one (the shipped default declares `bug`).
  `plan` is a pure read printing the full diff, and the JSON names the
  schema it read (`tracker_schema`) and the priority regime. `apply` creates
  and fixes colour and description drift, and prints deletes without
  executing them. `apply-delete` also executes the deletes, open issues
  included; deletion authority is granted by granting that mode. Deletion
  derives from every section that declares labels, so when one of them is
  not complete (see Following the Tracker Schema), `plan` and `apply` show
  no deletes and say why under `delete_refused`, and `apply-delete` is
  refused with exit `4` before any write. In every mode, deletion
  candidates attached to open issues are listed on stderr (and in the JSON
  plan), because `plan` is exactly where a human decides whether to grant
  deletion. Case-only mismatches are reported; creates run before deletes;
  a partial failure lists the writes that landed.
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
  Creating boards is setup's job by convention (`setup-issue-tracker`'s
  GitHub steps), so every bootstrapped repo is triage-ready from birth.

**Colours.** Every label and board option colour comes from the repo's
Tracker Schema, which gives each kind, priority, label, and state a colour
of six hex digits with no `#`, treated exactly like its description: where
the live colour differs, a sync changes it to the schema's (see the
[use-issues design](../use-issues/design.md#format) and
[ADR 0027](../../adr/0027-the-tracker-schema-block-holds-state-order-entry-state-close-reasons-and-colours.md),
the block also holds every colour). What a Verb does when the schema's
colour for an entry is missing or bad is the general Wrapper rule in the
use-issues design's Format. A label takes the hex value as it is. A board option cannot: `createProjectV2Field`
and `updateProjectV2Field` take each option's `color` as
`ProjectV2SingleSelectFieldOptionColor`, a required enum of eight names
(`GRAY`, `BLUE`, `GREEN`, `YELLOW`, `ORANGE`, `RED`, `PINK`, `PURPLE`;
GitHub's GraphQL reference, Projects), and `board_schema.py`'s
`_OPTION_COLORS` uses those names today. So the board Verb maps each
state's and priority's hex colour to the nearest of the eight, and
defining what "nearest" means is part of that Verb's Issue
(`agent-tooling-u9n.21`). The shipped default's state and priority colours
were chosen with that mapping in mind, to read as the names today's
open-state and priority options carry; its `Closed` state has no option on
today's boards. `ghw-label-sync` takes every label colour from the schema;
`ghw-board-sync` still uses `schema.py`'s constants, and the Known gaps in
[index.md](index.md) say so.

### Following the Tracker Schema

The label Verbs and `ghw-orient` read the repo's Tracker Schema from
`TRACKER.md` on the default branch, through `lib/github/repo_schema.py`,
and print every warning the reader gives, even when nothing is blocked.
When the file is missing, cannot be fetched, or a section cannot be used,
each Verb follows the use-issues design's three-way split
([How a Wrapper uses the schema](../use-issues/design.md#how-a-wrapper-uses-the-schema)): reads and writes that need
nothing from the schema always work, additive writes go ahead on what can
be verified, and a destructive write is refused (exit `4`, naming the part)
unless every section it derives from is complete.

| Verb | No readable schema | A section is unusable | A section is incomplete |
|---|---|---|---|
| `ghw-label-sync` `plan`, `apply` | nothing to create; no deletes, `delete_refused` says why | that section adds no labels; no deletes | adds what was read; no deletes |
| `ghw-label-sync` `apply-delete` | refused, exit `4` | refused, exit `4` | refused, exit `4` |
| `ghw-issue-create`, `ghw-issue-edit add-label` | registry check only | its checks are skipped; the declared-label check needs every label-declaring section usable | checks run on what was read |
| `ghw-issue-edit remove-label` | goes ahead | axes unusable: no axis is held as required | checks run on what was read |
| `ghw-orient` | reports it under `tracker_schema` | reports it | reports it |
| Every other Verb | does not read the schema | | |

The label-declaring sections are the Issue Kinds, the Issue Priorities, the
label axes, and the labels on no axis; for `ghw-label-sync` the Issue
Priorities count only where the priority regime is not `board-field`.
Additive checks use what is usable rather than what is complete, so a label
lost from a usable section is refused as undeclared, and the warning for
that section says why. `remove-label` is an edit to one issue, not a write
derived from the schema, so a check it cannot run is skipped rather than
refused.

Rejected:
- a local schema file or fallback for `ghw-label-sync`, since the labels
  would then follow whichever file a caller passed rather than the schema
  every other Verb reads;
- refusing every write when the schema cannot be read, since filing an
  Issue on a forge that is reachable but whose `TRACKER.md` is broken would
  then stop all work;
- deriving `ghw-label-sync`'s deletions from a usable but incomplete
  section, since an entry the reader lost would read as a label to delete.

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
  candidates and write Verbs refuse.

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
- A triage write path beyond the six `triage-*` scripts (moves between open
  states, priority changes, body rewrites, comments, closes, reparenting):
  an unattended pass is granted only the scripts, and an attended one uses
  the Verbs above (see Triage on GitHub).
- Anything git: that is gitw and `use-git`.

## Shared conventions

- **Exit codes:** ghw follows
  [the Exit-code contract](../../index.md#exit-code-contract); why one
  contract covers all agent-tooling software is
  [ADR 0013 (one exit-code contract for all agent-tooling software)](../../adr/0013-one-exit-code-contract-for-all-agent-tooling.md).
  A malformed call is `2` whether the Verb catches it while parsing or
  only after fetching the label registry, so every violation of the
  label attachment contract exits `2`. The merge gates are `4`. Where
  this doc says a Verb refuses without naming a code, its placement under
  the contract is classified by `agent-tooling-cjvo.2`. The Verbs do not
  exit this way yet; see the Known gaps in
  [ghw's index](index.md#known-gaps).
- **`gh` and API failures** are classified in one place, `gh.classify`;
  `gh.GhError` carries the code and every Verb exits with it.
  `gh.classify` matches `gh`'s stderr loosely and case-insensitively,
  because its wording is not a stable interface. A GraphQL `errors`
  payload is classified by its `type` first (`NOT_FOUND` is `3`), because
  `gh` exits nonzero on those and prints only a terse message to stderr.
  Bare "not found" is not a not-found hint (a GraphQL schema error says
  it); only `HTTP 404` and `Could not resolve to a ...` are. A Verb's own
  not-found (a missing issue or board node) is `3`. A 403 counts as a
  grant too weak for the action (`4`) only when nothing in `gh`'s text
  points at rate limiting, abuse or secondary limits, or SAML
  enforcement; those are not the caller's grant, and are `1`. Whether
  GraphQL `INSUFFICIENT_SCOPES` is `4` (a grant too weak) or `1` (a
  credential fault) is classified by `agent-tooling-cjvo.2`. Auth
  failures, a missing `gh` binary, a `gh` below `ghw-issue-link`'s
  version floor, and network failures are `1`.
- **A write that may have landed exits `1`**, broken on our side, like
  any network failure. The code alone does not stop a re-run, since a
  caller applies its own retry threshold to a `1`; the protection is the
  error message, which says the write may have landed and to check
  before re-running. That matters most here: a timeout or reset may land
  after the request was sent, so a re-run create or comment Verb may post
  twice; `ghw-issue-close` posts its mandatory comment in a first request
  and closes in a second, so a re-run may post the comment twice; and a
  re-run `ghw-board-sync new` orphans a second project. For the same
  reason `ghw-board-sync new` exits `1` once the project exists, whatever
  fails after, and its error names the half-built project. The
  `triage-*` wrappers follow the same contract; where they fall short is
  a Known gap in [index.md](index.md).
- **JSON output:** write Verbs print a JSON plan with `"action": "applied"`
  (or `"plan"`, from `ghw-label-sync plan` only), most with a `changed`
  field. `ghw-orient` prints its own blob.
- **Bodies always through a staged file** (invariant 9), with the staging
  path typed literally: never `$CLAUDE_JOB_DIR`, which the harness blocks as
  shell expansion, and never heredocs or command substitution.
- **Usage errors that self-correct:** rigid positional signatures make
  mistakes fail at the Verb, so the message must let an agent fix the call in
  one round trip.

## Shared library

- `cli/lib/` (forge-neutral, shared with the other Wrappers): `schema.py`
  holds the constants the board Verbs still use: P0 to P3 as board options,
  canonical field names, the eight Status states with their exact casing
  (title case like `Needs Triage` beside sentence case like `In progress`),
  the terminal-state set, and Size XS to XL. It holds no labels: those come
  from the repo's Tracker Schema. Also
  `staging.py` (invariant 9), `plan.py` (JSON plan and exit codes),
  `arguments.py` (repo charset check, issue-number parsing), and
  `paths.py` (each tool's subdirectory of the Machine Config Directory and
  the Machine State Directory, per the
  [Path layout](../../index.md#path-layout)), and `tracker_schema.py`
  (the reader for a repo's Tracker Schema; see the
  [use-issues design](../use-issues/design.md#the-reader)).
- `cli/lib/github/`: `gh.py` is the subprocess layer. Every call has a
  120-second timeout with stdin closed when nothing is piped, so a prompting
  subcommand or stalled connection fails loudly instead of hanging an
  unattended run; non-JSON or dataless responses raise `GhError` rather than
  escaping as tracebacks. `boards.py` (orientation, disambiguation, `TRIAGE.md`
  discovery, board mutations), `repo_schema.py` (fetches `TRACKER.md` from
  the default branch, reads it with `tracker_schema.py`, and prints its
  warnings), `labels.py` (the label attachment contract, from the schema),
  `label_schema.py` (`ghw-label-sync`'s desired labels and their diff
  against the live ones), `board_schema.py` (conformance and provisioning),
  and `pulls.py` (merge gates) sit on it.
- Name-to-ID resolution is live on every call, with no on-disk cache (see
  Rejected alternatives).

The `triage-*` wrappers do not use this library yet: they carry their own
`lib_gh.py` and `lib_profile.py`, and `triage-apply-sync` declares its own
terminal-state set. The planned rebase is
[triage-library-rebase.md](triage-library-rebase.md).

## Skills

- **use-github** is wrapper-first end to end: orientation through
  `ghw-orient`, the invocation form and literal staging paths, and the
  guidance no Verb can absorb (the search command for `create-issue`'s
  search-first step; `Closes #N`, added in the text above a PR body's
  `Lands:` or `Advances:` trailer only where auto-close is wanted; the
  `TODO(#N)` rule). The discipline of working and changing an issue is `work-issue`.
- **setup-issue-tracker** is generic
  ([use-issues](../use-issues/design.md#setup-issue-tracker)); its GitHub
  steps are the bundled `github.md`, read on demand. They bootstrap labels
  by merging the repo's `TRACKER.md` and then running `ghw-label-sync`, and
  the board with `ghw-board-sync <repo> new`, so the
  full canonical schema, `Size` included, exists from day one; boards that
  predate `Size` are tolerated by board-sync's report-only behavior. They
  point to `use-github` as the canonical GitHub layer, and to
  `triage-issues` for the optional `TRIAGE.md` and ledger-issue bootstrap,
  which is per-repo policy rather than board schema.
- **triage-issues** is generic: its text names no platform and no state,
  and a pass is read against the repo's Tracker Schema
  ([use-issues design](../use-issues/design.md#triage-issues)). GitHub is
  one section of it, "Platform mechanics", which points to `use-github` for
  attended writes and to the six `triage-*` scripts for bulk reads and
  unattended writes. The scripts live in
  `skills/triage-issues/reference/`, install with the Skills, and are the one
  exception to bare-name invocation: they run as `python3 <path>` (see
  Permission rules). What they do and assume is in Triage on GitHub.

## Permission rules

Every rule uses the space-star form, `Bash(ghw-orient <repo> *)`, never the
colon form. The matcher is a plain string-prefix match, so the literal space
before `*` supplies the token boundary: a rule ending `… release *` cannot
match `… release-2 …`, while `release:*` would. A space-star rule also
matches the bare command with no trailing arguments, so no separate exact
rule is needed (see Evidence).

- **User level:** no ghw rules (invariant 6). The cost is one prompt when
  orienting in a repo with no project grants yet, which is the attended
  `setup-issue-tracker` bootstrap case. `ghw-label-sync` gets no user-level
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

## Triage on GitHub

The `triage-issues` Skill carries the discipline of a pass and is written
against no platform. These are the GitHub mechanics behind it, and the
reasons for them.

- **The project board is the inventory anchor,** not the repo's issue
  list. The board is where the Issue State is recorded (the `Status`
  field), it yields the project item ID every field write needs, and
  iterating its items catches closed issues whose `Status` still says open.
  `triage-inventory` then lists the open issues missing from the board.
- **Latest activity is computed from a server-side allowlist of timeline
  events** (`triage-timeline`): comments, title changes, label, assignee,
  and milestone changes, close and reopen, linked and unlinked pull
  requests, duplicate marks, transfers, board adds, removes, and `Status`
  changes, and sub-issue, parent, and blocked-by changes. Cross-references,
  mentions, subscriptions, pins, and locks are never fetched. The latest of
  those is compared with the body's `lastEditedAt`, because body and title
  edits emit no timeline event. Dropped after the fetch: anything by a bot
  account the profile lists, and `Status` changes made by GitHub's built-in
  board automation or on another project.
- **Two accepted limits of that computation.** Priority and Size changes
  are board field changes that emit no timeline event, so they do not count
  as activity. And a pass runs under the operator's own GitHub account, so
  its own label fixes and `Status` corrections cannot be told from a
  person's; `Last Triaged` writes emit no event, which is why the pass
  writes that field last.
- **Pull request evidence is GitHub's own closing linkage**
  (`closedByPullRequestsReferences`, closed pull requests included). A pull
  request that names an issue any other way is not reported;
  `triage-timeline` declares a list of contributing keywords and uses it
  nowhere (`agent-tooling-m1sl`, teach triage to read the Lands and
  Advances trailers). The Skill treats this as evidence to weigh against
  the Issue State Diagram and never as the definition of a state.
- **`triage-apply-sync` cannot be told a target.** It re-reads the issue
  and derives the one correction that makes open-or-closed and `Status`
  agree, so a granted call cannot be turned into an arbitrary state move.
  The same idea bounds the other three write scripts: a label from the
  profile's lists, a date, or free text confined to the one ledger issue.

The scripts predate the Tracker Schema and still work to the `TRIAGE.md`
profile and eight board `Status` options; the Skill's GitHub section says
exactly what they assume, and [index.md](index.md)'s Known gaps name what
is not yet true.

## Unattended triage

An unattended triage pass runs deny-by-default (`--permission-mode dontAsk`)
with only the six `triage-*` wrappers granted, so any other write (raw `gh`,
a `ghw-*` Verb) is denied rather than executed. What the pass may do on its
own is exactly those Permission rules; the Skill says nothing about it.
Never `bypassPermissions`, which would approve a stray write.

The launch form this design endorses is a background job dispatched by a
guard script
([DEPLOYMENT.md](../../../skills/triage-issues/reference/DEPLOYMENT.md) §4): a `launchd` agent or `SessionStart`
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
