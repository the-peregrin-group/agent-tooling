# gitw: design

How and why the gitw Wrapper and the `use-git` Skill work, describing the
code as it is. What is shipped, planned, or broken lives in
[index.md](index.md)'s Status. A planned addition, `gitw-trunk-sync`, is
specified in the dated proposal [trunk-sync.md](trunk-sync.md).

## Problem

Two coupled gaps:

1. **Agents need a standard git discipline.** Without one, rules scatter
   across per-repo instructions and per-session correction, and the same
   failures recur: acting on stale state (branching from arbitrary local
   state, validating against an old base, researching from a stale
   checkout) and concurrent agents corrupting a shared working copy.
2. **Raw `git` cannot be granted safely.** Permission rules match literal
   command prefixes, but git flags reorder freely and escalation hides in
   trailing flags (`push --force`, push options). "Push only your own
   branch" or "merge only in this repo" cannot be written as a prefix
   rule. Broad raw-git grants are too wide; narrow ones cause prompt
   fatigue.

The answer: encode the discipline in the `use-git` Skill, wrap every
sanctioned mutation in a gitw Verb, and deny (or at least never grant)
raw mutating `git`. The coverage bar: every consumer's mutating git runs
on gitw Verbs, with raw mutating `git` removed from its Permission rules.

## Ownership split

- **The Wrapper** enforces what a machine can check: scope pinning (Roster
  label, Branch prefix), freshness preconditions (fetch before branch,
  rebase, integrate), and refusal of structurally forbidden operations
  (pushing the default branch, rewriting integrated history).
- **The Skill** carries what needs judgment: the merge-readiness loop,
  "is this working copy mine?", commit size and message discipline, and
  which operating mode applies.
- **Permission rules** (per-repo settings) carry policy: which repos get
  which Verbs, which Branch prefixes, whether direct integration is granted
  at all. The Wrapper stays consumer-generic: no repo names, branch names,
  or hostnames in its code; repo identity lives in the Roster.

## Hygiene principles

Non-optional. The root invariant: **never act on unverified-fresh state.**

1. **Start from authoritative truth.** New work branches from the
   remote-tracking ref of the repo's default branch, which is why
   `gitw-branch-start` fetches first. Branching from whatever is checked
   out is the failure mode, not a mechanism.
2. **Merge-readiness is a freshness loop.** Before pushing for review,
   requesting re-review, or integrating: sync the base; merge correctly,
   including semantic conflicts that produce no textual conflict; re-run
   the repo's full validation surface; then re-verify the base has not
   advanced. If it has, loop. Green on a stale base proves nothing.
3. **Research reads from confirmed state.** Before gathering ground truth,
   confirm the branch and commit you are observing (`gitw-orient` reports
   both).

## Operating model

**Universal worktree isolation.** Every agent session, attended or
background, in every repo, runs in a harness-provided worktree on its own
branch. The primary checkout, and the local default branch inside it,
belong to the human. Git enforces the split: a worktree cannot check out
a branch the primary checkout holds, so an isolated agent cannot stand on
the default branch even by accident. A consumer needs this because no
process list can see the agent a human is about to start; only isolation
makes concurrent sessions safe by construction.

**Session-start ceremony**, in order: enter the harness worktree (the
harness does this for isolated sessions; otherwise the session enters one
itself); `gitw-orient`; `gitw-branch-start` (the harness's placeholder
branch is not a branch to work on); only then read or edit files, from the
worktree's paths. `use-git` does not yet carry this ceremony (a known
gap in index.md's Status).

**Two operating modes:**

- **(a) Push + PR.** Worktree, own branch, `gitw-push`, then a PR through
  the forge's Skill. The default everywhere. The only act affecting a
  shared branch is pushing your own branch.
- **(b) Direct integration.** Worktree, own branch, rebase, the full
  merge-readiness loop, then `gitw-integrate`. No PR. Only where the
  repo's instructions and Permission rules grant it. The gate inside this
  mode depends on the base branch's type:
  - **Trunk (the default branch) or a protected branch:** attended,
    always. Trunk advances only with a human in the loop.
  - **An integration branch the project designates:** may run
    unattended, on the project's own terms (its instructions and
    Permission rules). Where a project is silent, push + PR is the
    unattended ceiling.

Nothing in the code distinguishes attended from unattended sessions:
`gitw-integrate` is gated only by whether a Permission rule grants it for
that base. Enforcement beyond the grant belongs to a future capability
system.

**Unattended rebase.** An agent may rebase its own branch unattended,
conflicts included. Its own branch is one it started, or resumed on the
user's say-so; a branch another author pushed is shared history. Every
file whose conflict it resolved unattended is disclosed in the PR body
(or a PR comment when the PR exists) so the reviewer checks those
resolutions. A conflict it cannot resolve with confidence is a stop:
abort, push what it has, and say so. The rationale: `gitw-rebase` cannot
reach trunk, so the risk is never the rebase itself but unreviewed
resolutions reaching a shared branch, which disclosure addresses.

**Implications:** an agent owns getting its changes committed; it never
leaves untracked files or uncommitted changes in a working copy, its own
worktree included (the harness may remove it at session exit). It never
mutates the primary checkout. Untracked `settings.local.json` is a grey
area: clobbering it is invisible to git, so outside user-blessed
automation, changes to it are attended-only and need a competing-work
check and an explicit go-ahead.

## History policy

- **The default branch is trunk**, the branch everything flows into. The
  authoritative remote is the source of truth; every clone is a working
  copy, not a peer. This removes most of git's distributed surface from
  the Wrapper's scope.
- **Semi-linear history with integration bubbles.** Feature branches
  rebase onto trunk, then land as a two-parent merge commit, whether
  through a forge PR or `gitw-integrate`. `git log --first-parent` is the
  table of contents; one integration is one revert target
  (`git revert -m 1`).
- **No squash, anywhere.** Rebase-before-merge already yields readable
  history; squash destroys bisect and revert granularity and the rename
  detection that `git log --follow` depends on. The effort goes into
  authoring-time commit hygiene instead, which agents can be held to.
- **The rewrite boundary.** Never rewrite integrated or shared history.
  Your own unmerged branch is not just rewritable but required to be
  rebased onto trunk before it lands. Corollary: force-push exists only
  for your own Branch prefix, never trunk.
- **Stash is banned.** The stash stack is shared across every worktree
  and session, a concurrency hazard by construction. A WIP commit on your
  own branch does everything stash does, safely.
- **Machine-local degradation.** A repo with no remote treats its local
  default branch as authoritative; freshness checks have nothing to fetch,
  and `gitw-push` and `gitw-integrate` refuse outright.

## Repo identity: the Roster

In a forge Wrapper, a repo argument stops cwd from redirecting a write.
For git, cwd *is* the repo, so every Verb takes a leading Roster label
resolved against the machine-local Roster, `~/.config/gitw/repos.toml`.

- **Entry fields:** `checkout` (required, absolute path of the primary
  checkout), `remote_url`, `remote` (default `origin`, only with a URL),
  `default_branch` (default `main`), `operable_from` (list of absolute
  paths). A repo with no remote has a path-only entry. A missing or
  malformed Roster or an unknown key is exit 5; a mode looser than 0600
  warns and proceeds; an unknown label is exit 3 and lists the known
  labels. The parser is a hand-written TOML subset (stdlib `tomllib` is
  absent on Python 3.9).
- **Identity check:** the parent of cwd's git common directory must equal
  the registered checkout (linked worktrees pass; a second clone fails),
  and the configured remote's URL must match (normalized for a trailing
  `.git` or `/`). Mismatch is exit 4. This pins not just the project but
  the one blessed working copy.
- **Registration** is an attended ceremony: `gitw-repo-register` prints
  the exact TOML delta as a plan and writes it only in its `apply` form,
  under an `ask` Permission rule, so registration can never go silent.
  Removals and `operable_from` edits are the user's hand-edits; friction
  there is deliberate. The Verbs only read the Roster.

## Cross-repo operation

Operating on a repo other than the session's own is default-forbidden in
the Skill: no ambient reach into checkouts that happen to be on disk.
The intended exception is expressed in configuration, never judged: two
independently maintained artifacts must agree, the anchoring repo's
Permission rules granting Verbs for the second label, and the second
label's `operable_from` listing the anchoring repo. It is a
mistake-proofing interlock, not adversary-grade security.

What the code does today: a cwd outside the repo is admitted only under
an `operable_from` root, and only `gitw-orient` accepts that, reporting
on the primary checkout with `cwd_in_repo: false`. Every mutating Verb
refuses such a cwd with exit 4. Mutating Verbs are therefore cwd-bound:
they act on the branch checked out at cwd, so cross-repo mutation means
standing in a worktree of the target repo. What `operable_from` should
admit for mutating Verbs is an open design question
(`agent-tooling-1790288522193-11-242cbfe6`).

Why cwd binds working-tree Verbs: cwd is the statement "this working tree
is mine". Resolving the tree any other way, such as by branch-prefix
lookup, could commit another agent's in-flight changes.

## Worktree and branch ownership

The harness owns worktree directories; gitw owns branches. The family has
no worktree-lifecycle Verbs: the harness already handles creation,
session cwd switch, the live-session roster, and cleanup, and worktree
removal is a destructive operation gitw is better off without.
`gitw-branch-start` runs inside whatever worktree the harness provided and
re-verifies freshness itself. Branch prefixes, not worktree mechanics, are
therefore the policy vocabulary that Permission rules pin. A Branch
prefix is lowercase, single-level, and ends in `/`, or is a bare `/`.

The bare `/` means no branch constraint: it admits any branch except the
repo's authoritative default branch, and under it a branch-start name or
push target is the whole branch name, slashes allowed. The prefix has no
value of its own; it segments permissions only where a rule pins a
particular value, so the unconstrained scope exists and the rules decide
whether to grant it. `/` was chosen because it needs no shell quoting and
cannot collide with a real prefix (a git ref name cannot begin with a
slash); the empty string, an optional token, and a reserved word were
rejected (see [ADR 0008, bare `/` means no branch
prefix](../../adr/0008-bare-slash-means-no-branch-prefix.md)). The
default-branch refusal is explicit because a real prefix can never match
a slashless default like `main`, and `gitw-commit`, `gitw-integrate`,
and `gitw-branch-start resume` relied on that implicitly.

## Wrapper invariants

Family-wide, shared with ghw and fjw:

- **Rigid positional scope.** Scope tokens come first in a fixed order,
  so a Permission rule's literal prefix is the grant. Escalation is a
  positional mode, never a trailing flag. No scope-relevant flags follow
  the positional block. Arguments are parsed by hand, positionally.
- **Trust-but-verify.** Every scope claim is checked against reality;
  mismatch is a refusal (exit 4 in gitw and fjw; ghw reports refusals as
  2). In gitw: the label against the Roster and cwd, the Branch prefix
  against the current branch.
- **Staged message files.** Message and body files come only from under
  `/tmp/claude/` or `~/.claude/jobs/<job-id>/tmp/`; any other path is
  exit 2. In gitw an empty message is exit 2 as well.
- **Machine-readable output.** Write Verbs print JSON with `"action"`
  `"plan"`, `"applied"`, or `"conflict"` (a deliberate, resumable stop).
  Usage errors aim for one-round-trip self-correction; `-h`/`--help`
  prints the Verb's docstring, which is its CLI contract.
- **Stdlib-only Python**, compatible with 3.9.

gitw's own:

- **Token grammar.** Label `^[a-z0-9][a-z0-9._-]*$`; Branch prefix
  `^[a-z][a-z0-9-]*/$` or a bare `/` (the grammar lives in the shared
  `cli/lib/arguments.py`, which fjw uses too); branch-name tail without a
  slash, `..`, trailing `.`, or `.lock`, except that under `/` the name is
  a full branch and may contain slashes; an integration base may contain
  slashes. A bad token is exit 2.
- **Non-interactive git.** Every git call runs with terminal prompts off,
  the editor set to `true`, the pager to `cat`, askpass to
  `/usr/bin/false`, optional locks off, `LC_ALL=C`, and ssh in batch mode
  unless the user controls ssh. A 300-second timeout ends any call: exit
  6 for a remote call, else 1.
- **Fetch prunes.** Every fetch is `git fetch --prune <remote>`, so a ref
  deleted on the remote reads as absent instead of leaving a stale
  tracking ref that wedges later Verbs.
- **`gitw-orient` prints a bare report** rather than an action plan.
- **Interpreter:** every gitw Verb runs under `/usr/bin/python3`.
- **Anti-requirements, absent by design:** no force path to trunk, no
  rewrite of integrated commits, no deletion of trunk, no stash Verbs, no
  push to anything but the verified authoritative remote, no tags or
  release Verbs, no remote branch deletion. The last two wait for a
  consumer that proves the need.

### Exit codes

gitw implements the full shared Exit-code contract; the taxonomy and
every family's implemented codes live in
[the Exit-code contract](../../index.md#exit-code-contract). gitw's codes:

- `0` success, including a converged no-op.
- `1` unclassified git failure, or a local (non-remote) timeout.
- `2` usage error, including a bad token or an unusable or empty message
  file.
- `3` not found: unknown label, missing branch or base, vanished remote
  repository.
- `4` refusal: identity or prefix mismatch, dirty worktree, stale rebase,
  lease failure, sweep guard, nothing to commit or integrate, default-
  branch push, machine-local push or integrate, local pre-push hook
  refusal. Also `gitw-rebase`'s conflict stop, which is expected,
  resumable state rather than a caller bug.
- `5` Roster or authentication failure: Roster missing or malformed, a
  registered checkout that no longer exists, remote auth failure. The
  code's label for 5 is "auth failure"; gitw folds Roster problems in
  because both mean "fix the deployment".
- `6` network failure or remote timeout, the one retryable class.
  Remote failures are classified by git's English messages: auth markers
  to 5, "repository not found" to 3, anything else to 6.

### Attribution

`gitw-commit` writes an `Executed-By: <Actor>` trailer on every commit:
`claude-job-<id>` in a background job, `attended-<user>` otherwise,
derived from the environment and replacing any one the caller wrote
(more than one is exit 4). A reader of history needs to know which
session made a commit without trusting the message author. The Actor
derivation is shared with bdw (see [ADR 0002, Beads
identity](../../adr/0002-beads-identity.md): one Actor per background
job, a visibly distinct fallback for attended sessions). Only
`gitw-commit` writes the trailer; `gitw-integrate`'s merge bubble carries
the caller's message unchanged.

## Verbs

**`gitw-orient <repo>`.** Verifies identity, fetches (skipped for
machine-local repos), and reports branch, commit or detached state,
dirty and untracked tallies, `clean`, ahead/behind against the fetched
default branch, upstream ahead/behind, and `cwd_in_repo`. The mandated
first call of any session touching a repo: hygiene rules 1 and 3 made
executable. When it shows staleness, or dirt on a copy that might be
shared, the Skill says to tell the user in one passing sentence.

**`gitw-branch-start <repo> <prefix> <name> [resume]`.** Must run inside
the repo. Refuses a dirty worktree in both modes, checked again after the
fetch: commit or park the changes as a WIP commit, never carry them
silently across branches. Create form: refuses if the branch exists
locally or on the remote (a collision with in-flight work), then creates
`<prefix><name>` from the remote-tracking default without tracking it
(`gitw-push` sets the upstream later); a missing default branch is exit
3. `resume`: needs the branch locally or on the remote (else exit 3),
creating a tracking branch when it exists only remotely, and refuses a
branch checked out in another worktree. That refusal, courtesy of git's
one-checkout-per-branch rule, means another agent may be live on the
branch. For this Verb the prefix names the branch being created, so there
is no current-branch check: it legitimately runs from the harness's
placeholder branch. One grant covers both modes; create versus resume does
not change the blast radius.

**`gitw-commit <repo> <prefix> <message-file> [<pathspec>...]`.** Must run
inside the repo on a branch matching the prefix. No pathspec: stage and
commit the whole working tree (`add -A`), leaving it clean by
construction, the mechanical form of "no droppings". With pathspecs:
commit exactly those, refusing pre-existing staged changes outside them,
and report remaining dirt in the JSON. Raw `git add` is never needed: the
index stops being agent-visible state. Refusals (exit 4): a pending
merge, cherry-pick, or revert; unresolved conflicts; nothing to commit;
the sweep guard; more than one caller-written `Executed-By` trailer.

The **sweep guard** refuses any would-be-staged set, in either form,
that contains a local-only file: a path component matching
`settings.local.json` or `.env*`, compared case-folded. Exactly
`.env.example`, as the final component, is exempt: one sanctioned name
for a committable bootstrap guide, so broadening it is a design act, not
an implementation one. The refusal message states the policy and the
exemption. The other half of the guard is repo hygiene: local-only files
belong in `.gitignore`.

**`gitw-rebase <repo> <prefix> [continue|abort]`.** Bare form: refuses
an in-progress rebase, a prefix mismatch, standing on the default branch,
and a dirty worktree (before and after the fetch); then fetches and
rebases the current branch onto the remote-tracking default branch, the
only base it supports. A conflict leaves git's conflict state in place,
since it is the work product, and exits 4 with `"action": "conflict"`,
the conflicted paths, and a hint. `continue` verifies the in-progress
branch against the prefix, refuses files still carrying a full
conflict-marker triple, applies the sweep guard, stages exactly the
conflicted paths, and continues; the cycle repeats per conflicted commit.
`abort` restores the pre-rebase branch. There is deliberately no `skip`:
silently dropping a commit is a human decision.

**`gitw-push <repo> <prefix> [<name>]`.** Must run inside the repo on a
branch matching the prefix; refuses a machine-local repo, and refuses if
the branch or the target is the default branch, regardless of prefix.
Pushes only to the authoritative remote.

- **Bare form** pushes the current branch to the same-named remote ref
  with `--force-with-lease --force-if-includes` and sets the upstream.
  Force is not an escalation here: under rebase-before-merge, non-fast-
  forward pushes of your own branch are routine. The lease turns "someone
  else moved my branch" into a loud exit-4 refusal, which doubles as the
  another-agent-touched-my-branch detector. **No fetch precedes the
  push**: refreshing the tracking ref would make the lease vacuous.
  Accepted residual: a mangled local branch over an intact remote passes
  the lease and overwrites the remote branch (rare; recoverable from local
  and server reflogs).
- **Named-target form** pushes the current branch's tip to
  `<prefix><name>` and sets that ref as the upstream. It exists for
  recurring jobs that work on a fresh branch each run but keep one stable
  review ref that no branch ever commits on, such as a scheduled job that
  moves a `review/current` pointer to each run's tip and keeps one PR
  open from it. The lease is explicit,
  `--force-with-lease=<target>:<expect>`, where `<expect>` is the target's
  remote-tracking value in this clone, or empty ("must not exist yet")
  when the clone has never fetched it; the payload's `previous_target`
  reports it (null means never fetched here). `--force-if-includes` is
  not passed: git defines it as a no-op beside an explicit `<expect>`.
  A target that a human or another run moved since the last fetch is
  therefore a refusal, not a clobber. Because `resume` correctly refuses
  a branch another worktree holds, moving a pointer under a lease is the
  way to hand a review ref from run to run without a takeover mode.

Both forms relay git's own push output verbatim to stderr beside the JSON,
so whatever a pre-push hook prints reaches the caller. A local pre-push
hook refusal is exit 4, detected from git's trace2 event stream (a
nonzero exit of the `pre-push` hook child), because git otherwise prints
only a generic "failed to push some refs". The hook verdict is checked
before lease text, since a refusing hook ends the push before git prints
any ref status. If trace2 events are unavailable, classification falls
back to text and a hook refusal reads as exit 6, which the error line
states. Lease markers ("stale info", "remote ref updated since checkout")
are exit 4; other failures are classified as auth (5), not found (3), or
network (6).

**`gitw-integrate <repo> <base-branch> <prefix> <message-file>`.** The
mode-(b) Verb. Must run inside the repo on a branch matching the prefix
and different from the base, with a clean worktree; refuses machine-local
repos (moving a possibly checked-out local base is exactly the
primary-checkout mutation it avoids). It never checks out the base:

1. Fetch; a base missing on the remote is exit 3 (the prune keeps a
   deleted base from being silently recreated).
2. Verify the branch tip descends from the fetched base tip (the rebase
   is current); otherwise exit 4, "rebase first, then loop". Equal tips
   are exit 4, nothing to integrate.
3. Build the two-parent bubble with `git commit-tree`: the branch tip's
   tree, first parent the base tip, second parent the branch tip, message
   from the staged file.
4. Push it to `refs/heads/<base>` under the exact lease
   `--force-with-lease=refs/heads/<base>:<fetched-tip>`, a compare-and-swap
   on the tip the descendant check used. If the base has moved or been
   rewound, the push rejects (exit 4): the base moved, loop again from the
   rebase.

`<base-branch>` is whatever the Permission rule pins. It is deliberately
not required to equal the Roster's default branch, because a repo may
designate a second integration branch. Validation stays in the Skill,
driven by the repo's own instructions; the Wrapper runs no repo-declared
command. Output relay and hook detection match `gitw-push`; a hook
refusal is exit 4 but does not mean the base moved. Afterwards the
worktree is still on the integrated feature branch; syncing the human's
local trunk and cleaning up branches are left to the harness and the
human. `gitw-integrate` is the only Verb that writes to trunk.

**`gitw-repo-register <label> <checkout> [<remote-name>] [apply]`.**
Derives the Roster entry from the checkout, which must be a primary
checkout root. One remote is used automatically; several need a name;
none makes the entry machine-local. The default branch comes from
`<remote>/HEAD`, falling back to `main` then `master`; a machine-local
repo's comes from `HEAD`, refusing a detached or slash-named one. The
plan form prints the delta; `apply` appends it atomically (mode 0600),
preserving the file's text, after validating the candidate. The same
data again is a converged no-op (hand-added `operable_from` is ignored
in the comparison); different data for the label, or a checkout another
label claims, is exit 4. Any Roster error, such as an existing Roster
that is malformed, is exit 5. It never writes `operable_from`.

## Permission rules

Rules pin Verb, label, and Branch prefix as literal prefixes:

```json
"Bash(gitw-orient rocket-sled)",
"Bash(gitw-branch-start rocket-sled fix/ *)",
"Bash(gitw-commit rocket-sled fix/ *)",
"Bash(gitw-rebase rocket-sled fix/ *)",
"Bash(gitw-push rocket-sled fix/)"
```

- **A rule ending in a space and a star, with no other wildcard, also
  matches the bare command.** `Bash(gitw-rebase rocket-sled fix/ *)`
  covers the bare call and its `continue`/`abort` modes. This is
  documented Claude Code behavior and has been observed directly. A
  harness that did not honor it would make the bare call prompt, so an
  allow rule fails closed; a deny rule would fail open, so exact deny
  rules are kept beside starred ones (whether they stay is
  `agent-tooling-na2`).
- **`gitw-push` never takes a star.** The set of refs a consumer may move
  is a deliberate enumeration: the bare form is one exact rule and each
  named target its own exact rule
  (`Bash(gitw-push rocket-sled review/ current)`).
- **`gitw-integrate`** is granted per repo and per base, deliberately,
  only where direct integration is sanctioned.
- **The bare `/` prefix is granted like any other**
  (`Bash(gitw-commit rocket-sled / *)`, `Bash(gitw-push rocket-sled /)`),
  and a repo that wants prefix segmentation simply does not grant it. A
  rule starred right after the label (`Bash(gitw-commit rocket-sled *)`)
  already admits it.
- **`gitw-repo-register`** is never allowed; a global `ask` rule keeps
  every registration a visible human approval (`ask` outranks `allow`).
- **`git mv` / `git rm`** may be granted raw, per repo and path-narrowed,
  for move- or delete-heavy flows. Git fences both to tracked, in-repo
  paths (shell `mv`/`rm` have no such fence), and the staged result rides
  `gitw-commit`'s commit-all form.

## Raw git reads and the displacement posture

- **Mutations are Wrapper-only.** No mutating raw-git rule is ever granted
  (a broad `git checkout *` both switches branches and silently discards
  edits). The recommended deny set covers the flagship destructive
  prefixes (`git push`, `commit`, `merge`, `rebase`, `reset`, `stash`,
  `filter-branch`, `checkout`, and more), so no future broad allow can
  swallow them. Deny rules should deploy only after every live consumer's
  mutating git runs on Verbs: never deny raw git ahead of the
  replacement.
- **Reads stay raw** under a curated set: `status`, `log`, `show`,
  `diff`, `grep`, `blame`, `ls-files`, `ls-tree`, `ls-remote`,
  `rev-parse`, `branch --show-current` and bare `git branch` (exact
  forms; `-D` is one flag away from a starred rule), `check-ignore`,
  `worktree list`, and `fetch` (it writes remote-tracking refs, but the
  hygiene rules want more fetching, not less).
- **Everything else falls to the default prompt**, the real control; the
  deny list is loud failure for the worst offenders.

Why reads are not wrapped: a forge Wrapper wraps reads because the raw
tool offers no grantable substrate. Git's read surface is prefix-pinnable
and enormous, research needs all of it (`log -S`, blame ranges,
`show <rev>:<path>`), and wrapping it means dozens of Verbs or a
passthrough. Raw reads also keep agents' trained git competence working.

The cost: git's flags are too many to call any command read-only by name.
Three escape classes survive a prefix rule: command execution
(`git grep -O<pager>`, `--upload-pack=<cmd>`), file writes
(`--output=<path>` on the log and diff family), and ref writes through
reads (`git fetch <remote> +x:main`). Each retained read rule was audited
against them, narrowed where possible, and the remaining holes accepted
and documented: [read-allowlist-audit.md](read-allowlist-audit.md).
Raw reads also leave research freshness (hygiene rule 3) as a Skill
obligation, since a Wrapper cannot intercept what it does not mediate.

## Boundary with neighbors

**The push is the boundary.** `use-git` owns everything up to and
including getting commits onto the authoritative remote: hygiene,
concurrency, branch, commit, rebase, and push discipline, history policy,
direct integration, and the floor of message discipline (small coherent
commits, messages from staged files). The forge Skills (`use-github`,
`use-forgejo`) own everything that happens to a pushed branch: PRs, review,
forge merge. Commit messages are repo content and belong here; PR
descriptions are forge artifacts. Writing style beyond that floor is out
of scope.

## Installation

Source lives in agent-tooling's `cli/` (the `gitw-*` Verbs flat, shared
code under `cli/lib/` and `cli/lib/git/`). The Installer, `tooling-install`,
copies them to the Install Target `~/.local/libexec/agent-tooling/`, which
is on PATH; the installed copy is what runs, never a checkout. Verbs are
invoked by bare name, never by path or through `python3`, because
Permission rules match literal command strings. The Installer, its
Cohorts, and its Receipts are described in the [installer
project](../installer/index.md).

## Rejected alternatives

- **Wrapping the git CLI one-to-one.** A passthrough inherits the full
  surface the Wrapper exists to suppress.
- **Trailing-flag escalation** (honoring `--force`, push options). A
  prefix rule cannot see a trailing flag, so escalation must be a
  positional mode.
- **Local checkout-and-merge for direct integration.** It needs the base
  checked out somewhere, which means touching the primary checkout; the
  `commit-tree` bubble pushed under a lease needs no checkout.
- **A Wrapper-run, repo-declared validation command.** A granted binary
  that executes whatever a repo file declares lets repo content control
  a trusted binary, the same escape class the read audit hunts in git.
  Validation stays Skill-driven.
- **A validation attestation flag** (`--validated`). Unverifiable, so it
  proves nothing.
- **A third operating mode: work directly on the default branch.** It
  required the user's assurance that no other agent was running, which
  no one can guarantee, and it put agent work on the human's copy.
  Universal worktree isolation removes both the need and the
  possibility.
- **Trunk Verbs for that mode** (`gitw-trunk-commit`, `-push`, `-rebase`),
  retired unbuilt: with no agent ever on trunk, commit has no caller,
  rebase would move only the human's own commits, and push duplicates
  `gitw-integrate`. Only the fast-forward convenience survives, as the
  planned `gitw-trunk-sync`.
- **Stash Verbs.** The stash stack is shared across worktrees and
  sessions; a WIP commit is the safe substitute.
- **Squash merges.** They destroy bisect and revert granularity and
  rename detection, and rebase-before-merge already reads cleanly.
- **A takeover mode for a branch held by another worktree, or an alias
  branch pushed by raw refspec.** The holder may be a live agent, so the
  refusal is correct; moving a pointer ref under a lease
  (`gitw-push`'s named-target form) removes the need.
- **A deny list scoped to spare attended trunk work.** Permission rules
  cannot tell attended from unattended, so the carve-out would leave raw
  `git commit` and `git push` reachable everywhere.
