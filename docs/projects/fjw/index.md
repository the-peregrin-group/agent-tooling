# fjw: the Forgejo Wrapper

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
| Probe a head branch's open-PR state (none, draft, mergeable, conflicted) | shipped | `fjw-pr-query` |
| Close a PR with a mandatory comment | shipped | `fjw-pr-close` |
| Comment on a PR within a pinned head-branch prefix | shipped | `fjw-pr-comment` |
| Agent conventions for the Verbs | shipped | use-forgejo Skill |
| Issue and label Verbs, with PR/issue index guard | planned | [issue-verbs.md](issue-verbs.md); `agent-tooling-1vr` |

### Known gaps

- `fjw-pr-create` reports a repo the machine account cannot see as a
  missing branch ("push it first", exit 2) instead of exit 3 naming both
  possibilities (`agent-tooling-5np`).
- use-forgejo says the Wrapper reconciles the API and SSH hosts, but no Verb
  reads the `ssh_host`/`ssh_port` config keys (`agent-tooling-1t4`).
- use-forgejo and the `fjw-pr-comment` docstring carry a
  non-generic example head prefix (`agent-tooling-c57`).
