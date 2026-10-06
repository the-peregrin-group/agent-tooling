---
name: use-git
description: >
  The git discipline for working in any repo: hygiene (never act on
  unverified-fresh state), concurrent-agent operating modes, history policy
  (semi-linear with integration bubbles, no squash, rebase-before-integrate),
  and the installed `gitw-*` wrapper verbs that carry every mutating git
  operation — orient, branch-start, commit, rebase, push, integrate,
  repo-register. Load this before any git operation in a repo, attended or
  unattended. Also relevant for "start a branch", "commit this",
  "rebase onto main", "push my branch", "integrate this branch", "is this
  checkout fresh". Everything after the push — PRs, review flow, forge
  merge — belongs to use-forgejo/use-github; worktree creation and removal
  belong to the harness, not to git commands.
---

# Use Git

> The discipline for acting on a git repo: freshness before action, explicit
> repo identity, your own branch in your own worktree, and every mutation
> through a `gitw-*` verb. The root invariant: **never act on
> unverified-fresh state.**

## The Wrapper Layer

Every mutating git operation runs through the `gitw-*` wrappers, installed
to a dedicated wrapper directory on PATH (source lives in the
agent-tooling repo's `cli/`; `tooling-install` copies it to
`~/.local/libexec/agent-tooling/`, and that installed tree is what runs,
never a checkout). Invoke them **by bare name, exactly as written here** —
never by absolute path, never through `python3`. The permission system matches
literal command strings, so the one rigid invocation form is what makes
allowlisting work.

**Reads stay raw git.** `status`, `log`, `show`, `diff`, `grep`, `blame`,
`ls-files`, `ls-tree`, `rev-parse`, `fetch <remote>` and friends are yours
directly — research legitimately needs git's full read surface. Mutations
are wrapper-only, with one consequence worth internalizing: **the index is
not your scratch space. Never run `git add`** — `gitw-commit` owns staging
outright, and the commit is the unit you control.

One narrow carve-out, expressed in settings grants rather than judgment:
`git mv` / `git rm` may be granted per-repo, path-narrowed, for
move/delete-heavy flows. Git fences both to tracked, in-repo paths —
shell `mv`/`rm` have no such fence and are never allowlisted — and the
staged rename or deletion rides `gitw-commit`'s commit-all form.

- **Repo identity is a roster label, not a path and not cwd.** Every verb's
  first argument is a short label resolved against the machine-local roster
  (`~/.config/gitw/repos.toml`), which pins the one blessed checkout, its
  authoritative remote, and its default branch. The wrapper
  trust-but-verifies the working copy you're standing in against that entry
  and refuses a mismatch — a second clone of the same repo is refused even
  with the right URL. Never edit the roster by hand to make a refusal go
  away; registration is `gitw-repo-register`'s ceremony, and removals are
  the user's hand-edits. The label is conventionally the checkout's
  directory name: run `gitw-orient <that name>`, and treat exit 3 (unknown
  label) as a question for the user — the repo may be registered under
  another label, or not at all (see Orient First). Never read the roster
  file to discover a label.
- **Exit codes are a contract** — branch on them, especially unattended:
  - `0` success, including a converged no-op.
  - `1` unclassified git failure.
  - `2` usage error: read the message, fix the call.
  - `3` not found (unknown label, missing branch, vanished remote). For
    probes this is an answer, not an error.
  - `4` refused: the call violated wrapper-enforced policy (identity or
    prefix mismatch, dirty worktree, stale rebase, lease failure, sweep
    guard, local pre-push hook refusal). A caller bug — **never retry
    unchanged, never work around it with raw git.** The refusal is the
    contract doing its job.
  - `5` roster/auth failure: abort and flag the deployment. Never retry.
  - `6` network failure: the one retryable class.
- **Load `use-privacy` first, if listed.** If a `use-privacy` skill is
  listed among your available skills, load it before composing any text
  bound for outside this machine: a commit message, a PR or issue body, a
  comment.
- **Commit and merge messages always go through a staged file.** Write the
  message with the Write tool to `/tmp/claude/` (unique filename), or in a
  background job `~/.claude/jobs/<job-id>/tmp/` with the job ID typed out
  literally — never `$CLAUDE_JOB_DIR`. No heredocs, no `-m` flags, no
  inline messages.
- Write verbs print a JSON plan with `"action": "plan"`, `"applied"`, or
  `"conflict"` (a rebase stop: deliberate, resumable state).
- A permission prompt on a wrapper call is normal in a repo whose settings
  don't allowlist that verb. The human approving it is the design working —
  don't hunt for an unprompted path.

## The Hygiene Principles

Non-optional, not user preference:

1. **Start from authoritative truth.** New work branches from the
   authoritative instance of the repo's default branch — which is why
   `gitw-branch-start` fetches first and branches from the remote-tracking
   ref. Branching from whatever happens to be checked out is not a
   mechanism, it's the failure mode.
2. **Merge-readiness is a freshness loop.** Before pushing a PR for
   review, requesting re-review, or integrating: sync the base; merge
   *correctly*, including semantic and functional conflicts that produce no
   textual conflict; re-run the repo's full validation surface (all test
   types, build, linters, CI, app smoke where relevant — the repo's own
   CLAUDE.md and docs define it); then re-verify the base has not advanced.
   If it has, loop. Green on a stale base proves nothing.
3. **Research reads from confirmed state.** Before gathering ground truth,
   confirm what you're standing on (branch and commit — `gitw-orient` does
   this). When researching a historical state, confirm you are observing
   the state you intend, not whatever was left checked out.

## Orient First

The mandated first call of any session touching a repo:

```bash
gitw-orient <repo>
```

Fetches the authoritative remote (machine-local repos skip the fetch and
measure against the local default) and reports branch, commit,
dirty/untracked tallies, upstream, and ahead/behind vs. the fetched
authoritative default — staleness is visible before work begins. When
orient shows staleness, or dirt on a working copy that might be shared,
tell the user in one passing sentence — visibility, not ceremony — and
apply the concurrency rules below before touching anything.

Exit 3 with an unknown label means the repo is not registered. Attended,
propose the `gitw-repo-register` plan; unattended, stop and flag it.
Never fall back to raw mutating git because a label is missing.

## Whose Working Copy Is This?

**A working copy is never presumed yours.** Either the user confirms, in an
attended session, that nothing else is or will be in flight (checking a
process list is NOT sufficient — it cannot see the agent the user is about
to start), or you default to your own branch in your own worktree.

Three operating modes, escalating in required trust:

- **(a) Worktree + feature branch + push + PR.** The default everywhere,
  absent a repo-CLAUDE.md exemption. The only trunk-affecting act is
  pushing your own branch and opening a PR (forge skills take it from
  there).
- **(b) Worktree + feature branch, direct integration.** Only where the
  repo's CLAUDE.md grants it; attended when the base is trunk or a
  protected branch, on the repo's own terms into an integration branch it
  designates. Rebase onto current trunk, run the full merge-readiness
  loop, then `gitw-integrate`. No PR.
- **(c) Work directly on the default branch.** Very rare: repo exemption
  + attended + the user's explicit assurance of zero parallel agents for
  the session's duration. Sync the branch to its authoritative instance
  first.

Implications:

- **You own getting your changes committed** in the right place, the right
  way, at the right time. No dropping untracked files or uncommitted
  changes into working copies — `gitw-commit`'s commit-all form leaves the
  tree clean by construction, and its JSON reports anything that lingers.
- Do not mutate a shared working copy outside confirmed-exclusive mode (c).
  Assume doing so corrupts someone else's work.
- **`settings.local.json` is a grey area:** untracked, so clobbering it is
  git-invisible. Outside user-blessed automation, changes to it are
  attended-only and require both a competing-work check and an explicit
  user go-ahead.

## History Policy

- **The default branch is the trunk**, the integration branch everything
  flows into; the authoritative remote is the source of truth and every
  clone is a working copy, not a peer repo.
- **Semi-linear history with integration bubbles:** feature branches
  rebase onto trunk, then land as a two-parent merge commit. `git log
  --first-parent <trunk>` is the table of contents; one integration is one
  revert target (`git revert -m 1`).
- **No squash, anywhere.** Rebase-before-merge already yields readable
  history; squash destroys bisect/revert granularity and rename detection.
  The effort goes into authoring-time commit hygiene instead — small,
  coherent commits with real messages — which you, unlike a human, can
  actually be held to.
- **The rewrite boundary:** never rewrite integrated or shared history.
  Your own unmerged feature branch is not just rewritable but *required*
  to be rewritten (rebased onto trunk) before it lands.
- **Stash is banned.** The stash stack is shared across every worktree and
  session — a concurrency hazard by construction. A WIP commit on your own
  branch does everything stash does, safely.
- **Machine-local degradation:** a repo with no remote treats its local
  default branch as the authoritative instance. Freshness checks degrade
  (nothing to fetch); `gitw-push` and `gitw-integrate` refuse outright —
  there is no remote to push to, and no safe direct-integration path.

## The Verbs

```bash
gitw-branch-start <repo> <branch-prefix> <name> [resume]
```

Bare form: fetch, create `<branch-prefix><name>` from the fetched
authoritative default, switch the current worktree onto it. Refuses a
branch that already exists locally or on the remote (a collision with
in-flight work — resume it or pick another name) and a dirty worktree:
commit first, or park the changes as a WIP commit on your own branch (the
stash ban's replacement); actually discarding work means stopping to ask —
raw `git checkout`/`git restore` are not yours to run. `resume`: switch
onto an existing branch — created from the remote if only there — refusing
one checked out in another worktree: that refusal means **another agent
may be live on that branch**; stop and tell the user, don't maneuver
around it.

The branch prefix (`fix/`-style: lowercase, single-level, trailing slash)
is the allowlist scope token on every mutating verb, with a deliberate
split: for `gitw-branch-start` it names the branch being created or
resumed — the verb legitimately runs from the default branch or the
harness's `worktree-*` placeholder, so there is no current-branch check.
For commit, rebase, push, and integrate, the branch you're standing on
must match the prefix or the verb refuses.

A bare `/` is the no-constraint prefix: it matches any branch except the
repo's authoritative default, which every verb refuses under it. Use it
for a branch that has no prefix, such as a human's `foo-bar` branch with
an open PR handed to you: `gitw-branch-start <repo> / foo-bar resume`,
then `gitw-commit <repo> / <message-file>` and `gitw-push <repo> /`. Under
`/` the name (or push target) is the whole branch name, slashes allowed.
Write it bare, never quoted: the permission rule matches the literal
text. Whether `/` is granted is the repo's policy, not your choice; a
prompt on it is the policy asking.

```bash
gitw-commit <repo> <branch-prefix> <message-file> [<pathspec>...]
```

No pathspec: stage-and-commit the entire working tree, leaving it clean by
construction. With pathspecs: commit exactly those changes; the JSON then
reports remaining dirt so nothing lingers silently — and pre-existing
staged changes outside the pathspecs are refused rather than swept in.
Small, coherent commits are the floor: one commit per logical change,
message written to a staged file first. A **local-file sweep guard**
refuses staged sets touching `settings.local.json` or `.env*`; its
refusal message is self-documenting (including the one sanctioned
`.env.example` exception) — fix the gitignore or narrow the pathspec,
and beyond that it's the user's call. The wrapper appends an
`Executed-By:` trailer derived from the session environment; do not
write one yourself.

```bash
gitw-rebase <repo> <branch-prefix> [continue|abort]
```

Bare form: fetch and rebase the current branch onto the fetched
authoritative default. A conflict leaves the standard git conflict state
in place — it IS the work product — and exits 4 with a JSON listing of
conflicted paths. Resolve, then `continue` (which stages exactly the
resolutions and refuses files still carrying a full conflict-marker
triple); the cycle repeats per conflicted commit. `abort` restores the
pre-rebase branch. There is deliberately no `skip`: silently dropping a
commit is a human decision.

```bash
gitw-push <repo> <branch-prefix> [<name>]
```

Bare form: push the branch you're standing on to the same-named ref on
the authoritative remote and set its upstream. It always carries
force-with-lease semantics: under rebase-before-merge, non-fast-forward
pushes of your own branch are routine, and a lease failure converts
"someone else moved my branch" into a loud exit-4 refusal — fetch and
reconcile, never blind-retry. **Do not fetch immediately before pushing**:
refreshing the remote-tracking ref is exactly what would blind the lease.
The wrapper relays git's own push output to stderr beside the JSON,
including whatever the local pre-push hook prints; a local hook that
refuses the push is an exit-4 refusal too — fix what it reported, never
retry unchanged. A rejection by the remote's own hooks is still
reported as exit 6 today (issue agent-tooling-h3c).
Pushing the trunk is structurally refused regardless of prefix; the push
of your own branch is the boundary, and the forge skills own what happens
next.

Named-target form: push the same branch's tip to `<branch-prefix><name>`
on the remote instead, and set that ref as the branch's upstream. This is
the pointer move for flows that keep one stable review ref that no branch
ever commits on (a scheduled job, say: fresh dated branch each run,
`reconcile/current` moved to its tip, PR opened once from that ref). The
lease is the target's remote-tracking value as last fetched, or "must not
exist yet" if it never was, so a target that a human or another run moved
since your fetch is a refusal, not a clobber. The dated branch itself
never reaches the remote in this form.

```bash
gitw-integrate <repo> <base-branch> <branch-prefix> <message-file>
```

Mode (b) only — only where the repo grants it; attended when the base is
trunk or a protected branch, on the repo's own terms into an integration
branch it designates. The loop:
`gitw-rebase`, then the full merge-readiness validation (skill-side,
driven by the repo's own CLAUDE.md — the wrapper runs no validation), then
integrate. The wrapper verifies your branch tip descends from the freshly
fetched base tip, builds the two-parent bubble without ever checking out
the base, and pushes it under an exact lease. Both refusals — "not a
descendant" and "moved during the attempt" — mean the same thing: **the
base moved; loop again from the rebase.** As with `gitw-push`, the
wrapper relays git's own push output to stderr beside the JSON,
including whatever the local pre-push hook prints; a local hook that
refuses the push is an exit-4 refusal too, but it does not mean the base
moved — fix what it reported on the branch, then loop again from the
rebase; never retry unchanged. A rejection by the remote's own hooks is
still reported as exit 6 today (issue agent-tooling-h3c). Afterwards your
worktree is still on the (now-integrated) feature branch; leave local
trunk syncing and branch cleanup to the harness and the human.

```bash
gitw-repo-register <label> <checkout-path> [<remote-name>] [apply]
```

The attended registration ceremony (every invocation is ask-ruled — the
prompt is the human gate). The bare form derives the entry from the
checkout itself and prints the exact TOML delta as a plan; the human reads
it; the `apply` form writes it. Run plan first, always. Everything else
about the roster — removals, `operable_from` edits — is the user's
hand-edit, not yours.

## Unattended Sessions

- **Rebase your own branch freely**, attended or not, conflicts included.
  Your own branch is one you started, or resumed on the user's say-so; a
  branch another author pushed is shared history, behind the rewrite
  boundary. `gitw-rebase` never reaches the trunk.
- **Disclose conflicts you resolved unattended**, naming every file (the
  union of each stop's `conflicts` list) in the PR body, or in a PR
  comment when the PR already exists, so the reviewer checks those
  resolutions. A conflict you cannot resolve with confidence is still a
  stop: `abort`, push what you have, and say so in the same place.
- **Trunk advances only with a human in the loop.** Integrating into the
  default branch, or any branch the project protects, is attended,
  always. A project may designate its own integration branches and let
  `gitw-integrate` land there unattended; its CLAUDE.md and settings
  rule. Where they are silent, push-and-PR is the unattended ceiling.

## Cross-Repo Work

Operating on any repo other than the session's anchor is an anti-pattern,
**default-forbidden** — no ambient reach into checkouts that happen to be
on disk. The sanctioned exception is expressed, never judged: a cross-repo
write requires two independently-maintained artifacts to agree — the
anchoring repo's settings grant the verb for the second label, AND the
roster's `operable_from` list for that label includes the anchoring repo.
If the wrapper refuses your cwd, that interlock is missing; ask the user
rather than relocating.

## What This Skill Does Not Cover

**The push is the boundary.** Everything up to and including getting
commits onto the authoritative remote lives here; everything that happens
to a pushed branch — PRs, review flow, forge merge — belongs to
`use-forgejo` / `use-github`. Commit *messages* are this skill's floor;
PR *descriptions* are forge artifacts. Worktree creation, switching, and
cleanup belong to the harness (EnterWorktree and session isolation), never
to git commands. Tags, releases, and remote branch deletion are absent
pending a consumer that proves need. Stash is not deferred — it is banned
(see History Policy).

## Allowlisting a Consumer

Project `settings.json` rules pin verb + label + branch prefix as literal
prefixes; the trailing slash on the prefix is the token boundary:

```json
"Bash(gitw-orient rocket-sled)",
"Bash(gitw-branch-start rocket-sled fix/ *)",
"Bash(gitw-commit rocket-sled fix/ *)",
"Bash(gitw-rebase rocket-sled fix/ *)",
"Bash(gitw-push rocket-sled fix/)"
```

A rule ending in a space and a star, with no other star, also matches
the bare call (see Wildcard patterns, code.claude.com/docs/en/permissions),
so the starred `gitw-rebase` row covers its bare form and its
`continue`/`abort` modes. A harness that does not honour the rule makes
the bare call prompt rather than run, so an allow row fails closed; a
deny row would fail open, which is why agent-tooling's own policy spec
carries exact deny rows as well. `gitw-push` never takes a star: the set
of refs a consumer may move is a deliberate enumeration, so its bare
form is one exact row and each named target is its own exact row
(`"Bash(gitw-push rocket-sled reconcile/ current)"`).

The bare `/` prefix is granted like any other
(`"Bash(gitw-commit rocket-sled / *)"`, `"Bash(gitw-push rocket-sled /)"`);
a repo that wants prefix segmentation simply does not grant it. A row
starred right after the label (`"Bash(gitw-commit rocket-sled *)"`)
already admits it.

Grant only the verbs and prefixes the consumer exercises;
`gitw-integrate` is granted per-repo, deliberately, and only where direct
integration is sanctioned. `gitw-repo-register` is never allowlisted — it
lives under a global ask rule so registration can never go silent.
