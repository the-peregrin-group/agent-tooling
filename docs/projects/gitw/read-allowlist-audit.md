# gitw displacement: read-allowlist flag audit

> **Audit as of 2026-09-13.** Correction: the claim below that a
> space-star rule alone never matches the bare command is wrong.
> `Bash(x *)` matches bare `x` when the trailing space-star is the rule's
> only wildcard (documented Claude Code behavior, observed directly).
> Fixed-arity calls therefore do not need separate exact rules, though
> `gitw-push` still gets exact rules only, by deliberate enumeration (see
> [design.md](design.md#permission-rules)). Section references below
> predate design.md's 2026-10-01 rewrite.

The audit the displacement plan in [design.md](design.md) requires: every
retained raw-`git` read Permission rule audited against the three escape
classes before deny rules deploy. It fed the settings displacement work
directly.

**Sources audited:** the user-level settings' git allow and ask rules,
and the git rules in the project and local settings of the candidate
consumer repos. Several repos carried read rules (status, log, diff, fetch,
checkout, ls-tree, ls-files) and mutating rules (commit, mv, rm, push);
one repo's local settings carried a broad mutating set including a
`git -C <worktree-path> *` rule (see Open items).

**Threat model** (inherited from the design): mistake-proofing and
prompt-fatigue reduction, not adversary-grade security. "Accepted hole"
below means: reachable only by an agent already off the rails (prompt
injection or gross malfunction) that also knows the specific flag; the
default-prompt boundary and human review remain the real controls.

## The three escape classes

1. **Command execution**: a flag that makes a "read" run an arbitrary
   command (`git grep -O<pager>`, `--upload-pack=<cmd>`, pager/textconv/
   ext-diff machinery).
2. **File writes**: a flag that redirects output to an arbitrary path
   (`--output=<file>` on the log/diff family).
3. **Ref writes through reads**: `git fetch <remote>
   +refs/heads/x:refs/heads/main` refspec smuggling force-moves local
   branches; fetch is on the read list yet can rewrite local refs.

## Rule-grammar facts the audit leans on

- **Space-star prefix matching:** `Bash(git log *)` matches any command
  whose literal prefix is `git log `; the star tail is unconstrained.
  There is no grammar for "this prefix but never flag X": a flag cannot
  be excluded from a starred rule, and a deny rule (also prefix-shaped)
  cannot catch a flag that appears mid-tail. So the only narrowing
  moves available are (a) exact-form rules with no star and (b) pinning
  more literal tokens before the star.
- **Exact and starred forms are distinct** (superseded; see the
  correction above): `Bash(git status *)` does not match bare
  `git status`; commands commonly run bare need both rules. Ruled
  2026-09-14 from prior experience with the matcher: the space-star form
  demands at least a trailing space after the last literal token.
  Consequence for the gitw grants: fixed-arity wrapper calls
  (`gitw-push <repo> <prefix>`, bare `gitw-rebase <repo> <prefix>`) need
  starless exact rules; a space-star rule alone would never match them.
- **Option permutation defeats positional pinning of flags** (verified
  2026-09-13, git 2.43.0): `git ls-remote . refs/heads/main --heads`
  honors `--heads` after the positionals. Git's builtin option parser
  permutes, so a starred tail admits any flag *anywhere*, even after
  pinned positionals. Consequence: pinning positionals (a remote name, a
  `--heads`) constrains *which positional slots are filled* (the first
  non-flag word wins the repository slot) but never excludes flags.
  Abbreviated long options (`--upl=` for `--upload-pack=`) make
  flag-targeted deny rules doubly hopeless.
- **Global-option forms are blocked by rule shape:** no allow rule
  begins `Bash(git *)`, `Bash(git -c*)`, or `Bash(git -C*)`, so
  `git -c core.pager=<cmd> log`, `git -c alias.x='!cmd' x`,
  `git --git-dir=… <cmd>`, `git -C <path> <cmd>`, and `git --paginate
  <cmd>` match nothing and fall to the default prompt. This kills an
  entire escape class (config/alias/pager injection) at the grammar
  level, provided no `git *`-shaped or `git -C …*` rule ever exists (one
  did in one repo's local settings; see Open items).
- **Config-gated executors die with the above:** pager, `core.fsmonitor`,
  textconv, `diff.external`/`--ext-diff` all execute only commands
  declared in git config. `git config` writes are not granted and `-c`
  injection is shape-blocked, so these need a *second*, prompt-gated
  hole first. Treated as closed throughout; noted per command where
  relevant.
- **Wrapper-internal git is not permission-checked:** gitw Verbs run git
  as subprocesses of an already-allowed command. Narrowing the raw rules
  therefore does not starve the Wrapper; it only narrows what agents can
  compose by hand.
- **Where the harness blocks shell expansion** (`$(...)`/`$VAR`) **and
  `find -exec`**, the "smuggle a command through expansion" route inside
  otherwise-allowed rules is already closed.

## Per-command audit

### git status

- **Current:** `Bash(git status)` + `Bash(git status *)` at user level;
  star or exact forms in some repos.
- **Escape analysis:** no flags in any class. Writes only the benign
  opportunistic index refresh inside its own repo. Hook-shaped
  machinery (`core.fsmonitor`) is config-gated (closed, see grammar
  facts).
- **Final:** keep both forms unchanged. Clean.

### git log

- **Current:** `Bash(git log)` + `Bash(git log *)` at user level.
- **Escape analysis:** class 2: `--output=<file>` writes the output to
  an arbitrary path (create-or-truncate; can clobber any writable file,
  e.g. a settings file). Class 1: pager and `--ext-diff`/`--textconv`
  executors are config-gated (closed). Class 3: none.
- **Narrowing:** none possible. Research legitimately needs the full
  expressive surface (`-S`/`-G` pickaxe, `--follow`, ranges, formats),
  and the flag rides anywhere in the tail.
- **Final:** keep both forms. **Accepted hole: `--output` arbitrary
  file write.** Severity moderate: destructive (clobber), but requires
  an already-compromised agent naming a specific flag, and such an agent
  has ampler write paths inside every working directory anyway.

### git show

- **Current:** `Bash(git show)` + `Bash(git show *)` at user level.
- **Escape analysis:** identical to `git log` (same diff-option family):
  class 2 `--output`; config-gated class 1; no class 3.
  `git show <rev>:<path>` blob reads are in-repo only.
- **Final:** keep both forms. Same accepted `--output` hole as log.

### git diff

- **Current:** `Bash(git diff)` + `Bash(git diff *)` at user level.
- **Escape analysis:** class 2: `--output=<file>` as above. Class 1:
  config-gated only. Class 3: none. One extra read-scope quirk:
  `git diff --no-index <a> <b>` diffs arbitrary filesystem paths, which
  can surface content the `Read()` deny list refuses (e.g.
  `git diff --no-index /dev/null ~/.ssh/<key>`).
- **Final:** keep both forms. Accepted holes: `--output` (as log);
  `--no-index` arbitrary-file read, severity negligible wherever generic
  text-tool allows already read any path without a prompt, as they did
  here at the time (see Open items).

### git grep

- **Current:** `Bash(git grep *)` at user level.
- **Escape analysis:** class 1: `-O[<pager>]` /
  `--open-files-in-pager[=<pager>]` opens matched files in an arbitrary
  "pager", i.e. executes an arbitrary shell command with matched paths as
  arguments. **This is the worst hole on the retained list: arbitrary
  command execution inside a granted rule.** No class 2 (no
  output-to-file flag) or class 3. `--no-index` searches untracked cwd
  files, the same negligible marginal read exposure as `diff --no-index`.
- **Narrowing:** none possible under the grammar (the flag rides
  anywhere; deny can't reach mid-tail). Alternative considered, dropping
  the rule and leaning on the Grep tool or `grep *`: rejected, because
  `git grep <rev>` searches historical trees with tracked-only scoping,
  which nothing else covers, and the design ratified retention.
- **Final:** keep `Bash(git grep *)` (bare `git grep` is a usage error;
  no exact form needed). **Accepted hole, documented as the list's
  worst:** requires injection plus specific flag knowledge; the threat
  model explicitly tolerates this class rather than pretend a prefix
  grammar can express "grep minus one flag".

### git blame

- **Current:** no rule; every blame prompted, despite being on the
  ratified read list.
- **Escape analysis:** no flags in any class (`--contents`,
  `-S <revs-file>`, `-L` are reads; output is stdout-only).
- **Final:** **add** `Bash(git blame *)`. Clean. (Bare `git blame` is a
  usage error; no exact form.)

### git ls-files

- **Current:** `Bash(git ls-files *)` at user level; one repo had the
  no-space variant `git ls-files*`.
- **Escape analysis:** no flags in any class; index/worktree listing
  only.
- **Final:** keep the star form and **add exact** `Bash(git ls-files)`
  (bare invocation is the common case and was unmatched). No-space forms
  should be normalized to the same pair.

### git ls-tree

- **Current:** `Bash(git ls-tree *)` at user level.
- **Escape analysis:** no flags in any class; requires a tree-ish, so no
  exact form needed.
- **Final:** keep unchanged. Clean.

### git ls-remote

- **Current:** `Bash(git ls-remote *)` at user level.
- **Escape analysis:** class 1: `--upload-pack=<exec>` (and legacy
  `--exec`) names the program that serves the refs. For a **local-path
  repository argument it executes locally**: with the broad rule,
  `git ls-remote --upload-pack=<cmd> /some/path` is granted arbitrary
  execution. For ssh remotes the command runs server-side, where forge
  forced-command wrappers accept only the git service verbs (neutered);
  for https it is inert. Class 3: none (ls-remote writes no refs). Also
  mild egress: the broad rule lets an agent contact any URL.
- **Narrowing:** pin the repository positional to a named remote. The
  first non-flag word claims the repository slot, so a starred tail can
  no longer substitute a local path. Option permutation then works *for*
  us: `git ls-remote origin --heads 'refs/heads/x/*'` matches
  `Bash(git ls-remote origin *)` with full flag expressiveness.
  Residual: `--upload-pack` in the tail is forwarded to the *pinned*
  remote; local execution would require the remote's URL in repo config
  to be a filesystem path, and config mutation is prompt-gated. Low
  severity, accepted.
- **Final:** replace the broad rule with per-remote pinned forms:
  user-level `Bash(git ls-remote origin *)`; a repo whose authoritative
  remote has another name adds `Bash(git ls-remote <remote> *)`.
  Consumer migration note: a habitual `git ls-remote --heads <remote> …`
  ordering no longer matches; reorder to
  `git ls-remote <remote> --heads …` (equivalent output,
  permutation-verified).

### git rev-parse

- **Current:** no rule; on the ratified list but prompting.
- **Escape analysis:** pure plumbing; all output to stdout; no flags in
  any class.
- **Final:** **add** `Bash(git rev-parse)` + `Bash(git rev-parse *)`.
  Clean.

### git branch (read forms only)

- **Current:** `Bash(git branch --show-current)` (exact, already the
  ratified shape), `Bash(git branch)` (exact, safe list form),
  `Bash(git branch -m *)` (**mutating; dies** with the displacement).
- **Escape analysis:** the reason these are exact-form: `-D`, `-f`, `-m`,
  `--set-upstream-to` all live one flag away from any starred
  `git branch` rule. The two exact forms have zero tail, so nothing to
  audit.
- **Final:** keep `Bash(git branch --show-current)` and
  `Bash(git branch)` (the bare list form was an unratified addition to
  the design's read list, since ratified; see Open items). Listing needs
  beyond that (`-a`, `-vv`) fall to the prompt; `gitw-orient` covers the
  routine case.

### git check-ignore

- **Current:** `Bash(git check-ignore *)` at user level, granted but
  absent from the design's ratified read list.
- **Escape analysis:** pure read (`-v`, `-z`, `--stdin`); no flags in any
  class.
- **Final:** keep (an unratified addition, since ratified; see Open
  items). It earns its place: `gitw-commit`'s local-file sweep guard
  makes gitignore verification a routine agent read.

### git worktree list

- **Current:** `Bash(git worktree list*)` at user level: a no-space star,
  a sloppy shape that also matches a hypothetical `git worktree listX`.
  The literal `list` still pins the subcommand, so `worktree add` /
  `remove` / `prune` never match.
- **Escape analysis:** flags (`-v`, `--porcelain`, `-z`) all benign; no
  flags in any class.
- **Final:** normalize to the clean pair `Bash(git worktree list)` +
  `Bash(git worktree list *)`. Clean.

### git fetch: the flagship narrowing

- **Current:** `Bash(git fetch *)` at user level and in some repos.
- **Escape analysis:** class 3: refspecs are *positional*:
  `git fetch <remote> +refs/heads/x:refs/heads/main` force-moves local
  `main` under the broad rule; `--refmap` variants equally. Class 1:
  `--upload-pack=<cmd>` executes locally when the repository argument is
  a local path (and the repository is also positional, so a starred tail
  can supply one). Class 2: none. Broad fetch also permits arbitrary-URL
  egress.
- **Narrowing:** because both dangerous vectors are positional, **no
  starred fetch rule is safe; exact forms only.** Bare `git fetch` and
  `git fetch <remote>` use the *configured* refspec
  (`+refs/heads/*:refs/remotes/<remote>/*`), touching only
  remote-tracking refs and FETCH_HEAD: exactly the sanctioned,
  freshness-positive write. Mutating the configured refspec would require
  prompt-gated config writes. This closes all three classes completely.
- **Final:** replace the broad rule with exact forms: user-level
  `Bash(git fetch)`, `Bash(git fetch origin)`, `Bash(git fetch --all)`;
  a repo whose authoritative remote has another name adds
  `Bash(git fetch <remote>)`. Single-branch fetches, `--prune`, depth
  tricks, and URL fetches fall to the prompt, which is cheap because
  every mutating gitw Verb fetches internally under its own rule, so raw
  fetch is only a research convenience. Skill text should standardize on
  bare `git fetch <remote>`.

## Consolidated proposed read rules

User-level allow:

| Rule | Status | Residual hole |
| --- | --- | --- |
| `Bash(git status)` / `Bash(git status *)` | keep | none |
| `Bash(git log)` / `Bash(git log *)` | keep | `--output` file write |
| `Bash(git show)` / `Bash(git show *)` | keep | `--output` file write |
| `Bash(git diff)` / `Bash(git diff *)` | keep | `--output`; `--no-index` reads |
| `Bash(git grep *)` | keep | **`-O` arbitrary exec (worst)** |
| `Bash(git blame *)` | **add** | none |
| `Bash(git ls-files)` / `Bash(git ls-files *)` | keep + add exact | none |
| `Bash(git ls-tree *)` | keep | none |
| `Bash(git ls-remote origin *)` | **narrowed** from `git ls-remote *` | `--upload-pack` to pinned remote (neutered) |
| `Bash(git rev-parse)` / `Bash(git rev-parse *)` | **add** | none |
| `Bash(git branch --show-current)` | keep (exact, ratified) | none |
| `Bash(git branch)` | keep (exact) | none |
| `Bash(git check-ignore *)` | keep | none |
| `Bash(git worktree list)` / `Bash(git worktree list *)` | normalized from `list*` | none |
| `Bash(git fetch)`, `Bash(git fetch origin)`, `Bash(git fetch --all)` | **narrowed** from `git fetch *` to exact forms | none; all three classes closed |

Per-repo additions where the authoritative remote is not `origin`:

| Rule | Status |
| --- | --- |
| `Bash(git fetch <remote>)` | add (exact) |
| `Bash(git ls-remote <remote> *)` | add (pinned remote) |

Dying alongside (mutating, per the ratified displacement; listed only so
the settings edit is one coherent diff): user-level `git add *`,
`git branch -m *`, `git checkout *`; the ask rules `git merge *` /
`git rebase *` (superseded by deny); and every per-repo mutating raw-git
rule (commit, mv, rm, push, checkout).

Companion deny set (flagship destructive prefixes per the design;
no-space star so bare forms match too): `Bash(git push*)`,
`Bash(git commit*)`, `Bash(git merge*)`, `Bash(git rebase*)`,
`Bash(git reset*)`, `Bash(git stash*)`, `Bash(git filter-branch*)`,
`Bash(git checkout*)`, `Bash(git restore*)`, `Bash(git clean*)`,
`Bash(git add*)`. Optional shape-hardening denies, cheap insurance that
no future broad allow ever swallows the global-option injection class:
`Bash(git -c*)`, `Bash(git -C*)`, `Bash(git --git-dir*)`,
`Bash(git --work-tree*)`. Sequencing (a design constraint): denies land
only together with the Verbs and grants that replace the dying rules,
never ahead.

## Open items

- **Ratify the two additions:** ruled 2026-09-14, keep both. Bare
  `Bash(git branch)` (exact form only; starred forms stay dead) and
  `Bash(git check-ignore *)` (flag surface audited clean; a routine
  agent read now that `gitw-commit`'s sweep guard makes
  ignore-verification part of the workflow) join the ratified read list.
- **A `Bash(git -C <worktree-path> *)`-shaped rule must die with the
  displacement.** It is a full escape: the star covers the entire
  remainder, so it admits any mutation *and* re-opens the otherwise
  shape-blocked `-c` config/alias/pager injection
  (`git -C <worktree> -c core.pager=<cmd> log` matches). Its job is
  exactly what worktree-aware gitw Verbs replace.
- **`git mv` / `git rm` have no gitw Verb.** Their raw rules die as
  mutating rules, but some consumers perform renames. Plain `mv` plus
  `gitw-commit`'s stage-everything semantics preserves rename detection
  (it is content-based, not `git mv`-based), but plain `mv`/`rm` are not
  granted either. Resolution: allow narrow `git mv`/`git rm` forms per
  repo (see design.md's Permission rules) or accept the prompt.
- **`git pull` never returns:** composite fetch+merge; consumers migrate
  to `git fetch <remote>` + gitw Verbs.
- **Read-deny porosity:** generic text-tool allows read any path the
  `Read()` deny list protects without a prompt, because the Bash matcher
  checks only redirect targets against file rules, not file arguments.
  Closed 2026-09-20 with Bash deny rules mirroring the protected
  patterns. `git diff --no-index` / `git grep --no-index` remain
  accepted above.
- **Prune forms deferred:** `git fetch --prune` variants are excluded
  from the exact-form set; add per-remote exact forms only if a consumer
  shows real need.
- **Non-flagship mutations stay prompt-gated, not denied:**
  `cherry-pick`, `revert`, `am`, `apply`, `worktree add/remove` fall to
  the default prompt by omission; adding them to deny was judged noise
  (the design's deny list is loud failure for the worst offenders, not
  an enumeration of git).
