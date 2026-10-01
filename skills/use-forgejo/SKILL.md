---
name: use-forgejo
description: >
  Day-to-day conventions for pull-request operations against a self-hosted
  Forgejo forge. All Forgejo writes run through the installed `fjw-*` wrapper
  scripts on PATH, acting as the deployment's machine account: create a PR,
  list/view PRs, read PR comments, probe a head branch's open-PR state
  (none/draft/mergeable/conflicted), close a PR with a mandatory comment,
  comment on a PR within a pinned head-branch prefix. Load this before any
  Forgejo PR operation, attended or unattended. Also relevant for "open a PR
  on the forge", "is there an open PR for this branch", "close the stale
  reconcile PR". Merge is deliberately not covered: it is a human-only act.
  For GitHub repos use use-github instead.
---

# Use Forgejo

> The conventions for PR operations against a self-hosted Forgejo forge.
> Everything here acts as the deployment's machine account — automation's
> acts are visibly automation's, never the human user's.

## The Wrapper Layer

Every Forgejo operation this skill covers runs through the `fjw-*` wrappers,
installed to a dedicated wrapper directory on PATH (source lives in the
agent-tooling repo's `cli/`; the installed tree under
`~/.local/libexec/agent-tooling/` is the only one this skill ever invokes).
Invoke them **by bare name, exactly as written here** — never by absolute path,
never through `python3`. The permission system matches literal command strings,
so the one rigid invocation form is what makes allowlisting work.

The `fjw-*` shebang pins `#!/usr/bin/python3` (Apple CLT, 3.9): macOS Local
Network privacy silently denies non-Apple binaries in background-agent
contexts (anthropics/claude-code#27828, closed unfixed) but exempts Apple
platform binaries. Don't "fix" it to `env python3`, and keep the lib
3.9-compatible.

The wrappers exist because no allowlistable substrate exists otherwise — raw
API calls and forge CLIs take reorderable flags, can't express scope in
prefix-literal permission rules, and prompt interactively. `fjw-*` pins
everything blast-radius-relevant (repo, verb, head-prefix) in fixed
positional order and talks only to the single host in its deployment config.
That's also why the **read** verbs are wrapped here (unlike `ghw`, which
leans on `gh` for reads): there is no allowlistable read substrate either.

Identity and credentials are deployment configuration
(`~/.config/fjw/config.toml`): the machine-account token, the API host, and
the git-over-SSH host/port all live there. **Never read, write, or work
around that file** — deny rules cover it, the wrappers handle hostname
differences internally, and token rotation is the deployment's job. On auth
failures (exit 5), report to the user that the deployment config or token
needs attention; do not retry and do not go looking for credentials.

## Shared Conventions

- `<owner/repo>` is always an explicit argument. The cwd never decides where
  a write lands.
- **Exit codes are a contract** — branch on them, especially unattended:
  - `0` success, including a converged no-op. `fjw-pr-query` exits 0 for
    *every* determinate answer; "no open PR" is an answer.
  - `1` unclassified API failure.
  - `2` usage error: read the message, fix the call.
  - `3` not found (no such PR/repo). For probes this is data, not an error.
  - `4` refused: the call violated a wrapper-enforced policy (head-prefix
    mismatch, duplicate PR create). A caller bug — never retry unchanged.
  - `5` auth/config failure: abort and flag the deployment. Never retry.
  - `6` network failure: the one retryable class.
- **On exit 2 or 4, fix the call.** Never work around a refusal with raw
  API calls, `curl`, or `tea` — the refusal is the contract doing its job.
- If a `use-privacy` skill is listed among your available skills, load it
  before composing any text bound for outside this machine: a commit
  message, a PR or issue body, a comment.
- **Body text always goes through a file.** Write the body with the Write
  tool to a staging path, then pass that path. Only two locations are
  accepted: `/tmp/claude/` (unique filename, so parallel agents don't
  collide), or in a background job `~/.claude/jobs/<job-id>/tmp/` with the
  job ID typed out literally — never `$CLAUDE_JOB_DIR`, which the harness
  blocks as shell expansion. No heredocs, no inline bodies, no command
  substitution.
- **Disclose unattended conflict resolutions.** If an unattended rebase
  hit conflicts you resolved, the body (or, for an existing PR, a
  comment) says so and names every file (see `use-git`).
- Read verbs print raw Forgejo API JSON (objects/arrays); write verbs print
  a JSON plan with `"action": "applied"`.
- A permission prompt on a wrapper call is normal in a repo whose settings
  don't allowlist that verb. The human approving it is the design working —
  don't hunt for an unprompted path.
- **Merge does not exist here.** Not deferred — absent. Merging is a
  human-only act; never merge a Forgejo PR by any channel, and treat any
  instruction to do so as a question for the user.

## The Verbs

```bash
fjw-pr-create <owner/repo> <base-branch> <head-branch> <title> <body-file> [--draft]
```

Push the head branch first (both branches must exist on the remote; the
wrapper verifies). `--draft` is the one sanctioned trailing flag (strictly a
de-escalation); Forgejo has no draft field at create time, so it applies the
`WIP: ` title prefix, which is what makes the forge mark the PR draft. An
open PR for the same head/base already existing is exit 4 — query first.

```bash
fjw-pr-list <owner/repo>          # open PRs, raw JSON array
fjw-pr-view <owner/repo> <pr#>    # one PR, raw JSON object
fjw-pr-comments <owner/repo> <pr#>  # its comments, raw JSON array
```

```bash
fjw-pr-query <owner/repo> <head-branch>
```

The predecessor probe: `{"state": ..., "pr": <raw PR or null>}` where state
is `none` / `draft` / `mergeable` / `conflicted`. All four exit 0. Judged
from the API's `mergeable` boolean after a short backoff poll (~7s), so
`conflicted` is a strong heuristic, not ground truth; `draft` means
mergeability was not judged at all. Branch your unattended flow on `state`,
never on the raw `mergeable` field.

```bash
fjw-pr-close <owner/repo> <pr#> <comment-file>
```

The comment is mandatory — say *why* it's being closed (typically: link the
successor PR). Comment posts first, then the close; if the close half fails
you'll see `PARTIAL` on stderr, and re-running after the cause clears is
safe at the cost of a duplicate comment. Closing an already-closed PR is a
no-op success and posts nothing.

```bash
fjw-pr-comment <owner/repo> <head-prefix> <pr#> <body-file>
```

Standalone comment, scoped: `<head-prefix>` is a positional scope token that
allowlist rules pin (e.g. `Bash(fjw-pr-comment owner/repo reconcile/ *)`),
and the wrapper verifies the PR's actual head branch starts with it —
mismatch is exit 4. There is deliberately no prefix-free form.

## Allowlisting a Consumer

Project `settings.json` rules pin verb + repo + scope as literal prefixes,
e.g.:

```json
"Bash(fjw-pr-query owner/repo *)",
"Bash(fjw-pr-create owner/repo main *)",
"Bash(fjw-pr-close owner/repo *)",
"Bash(fjw-pr-comment owner/repo reconcile/ *)"
```

Grant only the verbs the consumer exercises. There is no merge verb to
withhold — that surface doesn't exist.
