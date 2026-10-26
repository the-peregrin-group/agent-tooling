# fjw: the Forgejo Wrapper

## Overview

fjw is the Wrapper over a self-hosted Forgejo forge. Its `fjw-*` Verbs let
agents operate on pull requests through commands that Permission rules can
grant as literal prefixes: the repo, the Verb, and any scope token sit in
fixed positions, and nothing prompts or hangs. Every API write acts as the
deployment's machine account, never the human user, and agents never see
its token. Merge is deliberately absent: it is a human act.

The use-forgejo Skill teaches agents the conventions: bare-name invocation,
staged body files, the Exit-code contract, and the absent merge. How fjw
works and why is in [design.md](design.md). The Installer that ships fjw is
its own project ([installer](../installer/index.md)).

## Status

| Capability | State | Where |
|---|---|---|
| Open a PR, optionally as a draft | shipped | `fjw-pr-create` |
| Read open PRs, one PR, and a PR's comments | shipped | `fjw-pr-list`, `fjw-pr-view`, `fjw-pr-comments` |
| Read a PR's reviews with their inline review comments | shipped | `fjw-pr-reviews` |
| Probe a head branch's open-PR state (none, draft, mergeable, conflicted) | shipped | `fjw-pr-query` |
| Close a PR with a mandatory comment | shipped | `fjw-pr-close` |
| Comment on a PR within a pinned head-branch prefix, or any PR under a bare `/` | shipped | `fjw-pr-comment` |
| Agent conventions for the Verbs | shipped | use-forgejo Skill |
| Issue and label Verbs, with PR/issue index guard | planned | [issue-verbs.md](issue-verbs.md); `agent-tooling-1vr` |

### Known gaps

- The shipped PR Verbs exit 3, not 2, on an issue number (agent-tooling-1vr.6).
- The Verbs still exit the earlier seven-code taxonomy, not the six-code
  Exit-code contract (agent-tooling-cjvo.3).
