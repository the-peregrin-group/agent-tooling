# fjw design

How the Forgejo Wrapper works and why. What is shipped and what is planned
is in [index.md](index.md); the planned issue Verbs are specified in
[issue-verbs.md](issue-verbs.md). fjw is motivated by the same concerns and
design choices that led to the GitHub Wrapper, and this doc assumes them;
refer to the [ghw design](../ghw/design.md) for background.

## Problem

Agents need to write to a self-hosted Forgejo forge, including unattended
runs that open, query, and close their own PRs. Raw forge CLIs and the raw
API fail the same way raw `gh` does: flags reorder, scope cannot be
expressed in prefix-literal Permission rules, and interactive prompts hang
unattended sessions. Forgejo writes must also act as a machine account,
not the human user, with a credential the calling agent can never see.

## Invariants

- **Identity.** Every API operation acts as the deployment's machine
  account, never the human user, so automation's acts are visibly
  automation's. Which account is deployment config, not code.
- **Merge is absent.** Merging is a human act. No Verb merges, and none is
  deferred: the surface does not exist.
- **Grantable by literal prefix.** The discriminating tokens (Verb, repo,
  scope) sit in fixed leading positions. No ambient defaults, no
  reorderable arguments, no scope flags in the tail. `<owner/repo>` is
  always explicit; the working directory never decides where a write lands.
- **Non-interactive.** Missing input, auth failure, or ambiguity exits
  non-zero at once with a diagnostic on stderr.
- **Machine-readable.** Read Verbs print raw Forgejo API JSON
  (`fjw-pr-query` wraps the raw PR in its state object). Write Verbs
  print a JSON plan (`"action": "applied"`). Exit codes classify failures.
- **Multi-line text only by file.** PR bodies and comments come from staged
  files under `/tmp/claude/` or `~/.claude/jobs/<job-id>/tmp/`; any other
  path exits 2. Wrapper reads bypass the agent's Read deny rules, so an
  open path would be an exfiltration channel.
- **One host.** Requests go only to the configured Forgejo host. Paths are
  always relative to `{api_url}/api/v1`, so egress elsewhere is impossible
  by construction. No telemetry or update checks.
- **The token stays out of reach.** It never appears in arguments, output,
  or any agent-readable file. It lives in the config file, which deny
  rules cover wholesale.
- **Consumer-generic code and Skill.** No consumer's branch names, repos,
  or hostnames belong in the Wrapper or use-forgejo; Permission rules
  carry the policy. One example prefix still breaks this rule (see
  [index.md](index.md)'s Known gaps).
- **Bare-name invocation.** Skills invoke Verbs by bare name, resolved on
  PATH to the installed copy, which is the form Permission rules match.

## Verbs

fjw wraps its read Verbs too, unlike ghw, because Forgejo offers no
grantable read substrate. Every Verb validates `owner/repo` against
Forgejo's name charset (rejecting `.` and `..` halves) and requires PR
numbers to be positive integers.

- `fjw-pr-create <owner/repo> <base> <head> <title> <body-file> [--draft]`
  opens a PR. It refuses an empty base, head, or title, and head equal to
  base (exit 2), and checks that head and base exist on the forge before
  posting (missing branch: exit 2, "push it first"). `--draft` is the one
  trailing flag, allowed because it only de-escalates. Forgejo's create
  API has no draft field, so `--draft` prepends `WIP: ` to the title,
  which is what makes the forge report the PR as draft. A 409 (an open PR
  for this head and base exists) is exit 4: callers query first, so a
  duplicate create is a caller bug.
- `fjw-pr-list <owner/repo>` prints the open PRs, paginated.
- `fjw-pr-view <owner/repo> <pr#>` prints one PR. An issue number 404s on
  the PR endpoint and exits 3.
- `fjw-pr-comments <owner/repo> <pr#>` checks that the number names a PR
  (exit 3 otherwise), then prints its comments, paginated.
- `fjw-pr-query <owner/repo> <head-branch>` is the predecessor probe. It
  prints `{"repository", "head", "state", "pr"}` with state `none`,
  `draft`, `mergeable`, or `conflicted`, and exits 0 for every determinate
  answer. With several open PRs on one head it judges the newest.
- `fjw-pr-close <owner/repo> <pr#> <comment-file>` closes with a mandatory
  comment, so a silent unattended close is inexpressible. It reads the PR
  first; an already-closed PR is a no-op success that posts nothing. It
  then posts the comment and PATCHes the state. If the comment fails, the
  PR stays open. If the close fails after the comment, stderr says
  `PARTIAL: comment <id> posted but close failed` and the exit code is the
  close failure's.
- `fjw-pr-comment <owner/repo> <head-prefix> <pr#> <body-file>` posts a
  standalone comment. `<head-prefix>` is a positional scope token that
  Permission rules pin; the Wrapper fetches the PR and refuses (exit 4)
  unless its head branch matches the prefix. The prefix takes gitw's
  grammar from the shared `cli/lib/arguments.py`: lowercase,
  single-level, ending in `/`, or a bare `/` that admits any head branch
  (see [ADR 0008, bare `/` means no branch
  prefix](../../adr/0008-bare-slash-means-no-branch-prefix.md)). No form
  omits the token, so a grant reaches other actors' review threads only
  through a rule that pins `/` explicitly.

## Forgejo API mechanics

fjw is a thin REST client over the Python standard library (`urllib`), with
no dependencies. It sends `Authorization: token …` and a fixed
`User-Agent`, uses a 30-second timeout, and passes raw API objects through.

- **Mergeability is quad-state, honestly.** The API's `mergeable` boolean
  conflates a running check, a conflict, a check error, and a draft; the
  internal status is not exposed. `fjw-pr-query` reports `draft` without
  judging mergeability, and reports `conflicted` only after re-reading a
  non-mergeable PR with backoff (1, 2, then 4 seconds). Checks usually
  settle within that window, but no "check finished" signal exists, so
  `conflicted` is a strong heuristic, not ground truth.
- **Head filtering is feature-probed.** The `?head=` list filter exists
  only in Forgejo v16 and later. The Wrapper reads the instance's
  `/swagger.v1.json` for the parameter, and filters client-side when it is
  absent; either way it re-verifies the exact head match. The
  `/pulls/{base}/{head}` endpoint ignores PR state (an upstream bug), so it
  is never used for open-PR existence.
- **API compatibility is per major version.** Forgejo majors ship
  quarterly. The tests use synthetic swagger fixtures, so re-verify the
  mechanics above against a live instance on each major upgrade.
- **Close is comment, then PATCH.** Forgejo has no atomic close-with-
  comment, so partial failure is detected and reported (see
  `fjw-pr-close`).
- **Token scopes cannot exclude merge.** The minimal scopes are
  `write:repository` (PR routes) and `write:issue` (comment routes, which
  live under issues). `write:repository` covers create, close, and merge
  alike.
- **The server-side grant is the real merge control,** and it holds even
  against a stolen token. Merge needs code-write permission. The
  recommended grant is Read collaborator: such an account can open PRs for
  branches already on the forge, comment, and close PRs it opened. The
  fallback is write permission with a branch-protection merge whitelist
  that excludes the account.
- **Branch pushes are outside fjw.** A consumer pushes its head branches
  over git with its own SSH identity, while fjw's API writes act as the
  machine account. Attribution is split; this is accepted for now and is
  not a long-term design.

## Configuration

`~/.config/fjw/config.toml` holds one identity:

- `api_url` (required, `https://` only; a trailing `/api/v1` is
  normalized away)
- `token` (required)
- `ssh_host`, `ssh_port` (optional): the git-over-SSH endpoint, which
  differs from the API host. They are parsed, but no Verb uses them today:
  no Verb touches git over SSH.

The file is the stable interface between the Wrapper and whoever
provisions the machine account: rotating the token means rewriting the
file, with no consumer-side change. The parser is a strict flat-TOML subset
(comments, escape-free strings, integers, booleans; anything else fails
loudly), because `tomllib` needs Python 3.11 and the Wrapper runs on the
system Python 3.9. Mode 0600 is advised; a wider mode only warns.

Deny rules cover `~/.config/fjw/**` wholesale (Read and Edit, plus
shell-read patterns). Deny rules are the one rule class safe to deploy at
the user level, because a deny rule only ever narrows, so deploying it at
the user level cannot widen any project's grants; and directory-wide
coverage means files added later are covered at birth. Deny rules stop
tool-mediated reads, not a determined shell one-liner: they raise the bar,
not a wall. A profiles section for several identities would be a
backward-compatible addition if a second consumer needs one.

## Exit codes

fjw implements the full Exit-code contract; the taxonomy and each Wrapper
family's coverage live in
[the Exit-code contract](../../index.md#exit-code-contract).

| Code | fjw meaning |
|---|---|
| 0 | success, including a converged no-op and every `fjw-pr-query` answer |
| 1 | unclassified: HTTP statuses other than 401, 403, and 404, or a non-JSON response |
| 2 | usage error or refusal at parse time, including a bad staging path and a missing branch on create |
| 3 | not found: HTTP 404 |
| 4 | policy refusal past parse: a 409 on create, or a head-prefix mismatch |
| 5 | auth or config: HTTP 401 or 403, and every config error |
| 6 | network: connection failure or timeout; the one retryable class |

A config error maps to 5 because an unattended caller cannot tell a missing
config from revoked credentials: both mean abort and flag the deployment.

## Implementation

The Verbs are flat executables in `cli/` over `cli/lib/forgejo/` (`api`,
`config`, `pulls`) and the shared `cli/lib/` (`arguments`, `plan`,
`staging`). They pin `#!/usr/bin/python3`: macOS Local Network privacy
silently denies non-Apple interpreters in background-agent sessions, and
the Apple-signed system Python is exempt. The code stays stdlib-only and
3.9-compatible. Tests are offline `unittest` with `urlopen` mocked.

fjw ships through the Installer like every other tool in the repo; why
nothing runs from a checkout is the
[Installer's design](../installer/design.md).

## Rejected alternatives

- **`tea` as the substrate.** It ships `tea pr merge`, a surface the
  Wrapper would have to suppress. It tracks Gitea rather than Forgejo, so
  it would never use the v16 `head=` filter. Its prompting depends on a
  TTY rather than being non-interactive by construction. Its JSON output is
  its own tabular shape, not the raw fields quad-state needs. It keeps its
  own plaintext token outside the deny-ruled config.
- **AGit push-option PR creation** (`git push -o title=… refs/for/<base>`).
  AGit PRs are authored by the pushing identity, which breaks the
  machine-account requirement; split attribution covers branch pushes, not
  PR authorship. It replaces one Verb of seven, so it adds a second,
  differently-permissioned write channel instead of shrinking the surface,
  and `git push` grants are far blunter than a `fjw-pr-create` prefix rule.
  Push options are trailing flags that prefix rules cannot see. AGit PRs
  also behave oddly in Forgejo's UI.
- **`fjw-pr-edit`.** Not an anti-Verb like merge, but the burden of proof
  for editing a PR is high: a PR is close to done when opened, and changes
  append as comments. The convention is that a later comment supersedes the
  description. Issues differ: they are living documents, so the planned
  issue Verbs include an edit Verb ([issue-verbs.md](issue-verbs.md)).
- **A Wrappers-only install directory.** The install directory is not
  reserved for credential-fronting Wrappers; see the
  [Installer design](../installer/design.md#the-executable-tooling-directory).
- **No `fjw-orient`.** The Verb set is exactly what consumers exercise;
  an orient Verb waits for a consumer that needs one.
