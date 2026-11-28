# ghw: the GitHub Wrapper and its Skills

## Overview

ghw is the Wrapper over GitHub: every GitHub write an agent is allowed to make
goes through one of its twelve `ghw-*` Verbs, each shaped so a Permission rule
can grant it at exactly the intended scope. Raw `gh` cannot be granted that
way: its flags are freely ordered, mutations hide behind `gh api`, and "write
to this repo only" or "comment but never merge" is inexpressible as a command
prefix. The Verbs pin everything blast-radius-relevant (repo, mode, base
branch, field name) in fixed positional order, enforce the ecosystem's label
and board contracts in code, and resolve GitHub's name-to-ID mappings
internally, so agents never handle node IDs.

Three Skills sit on top. `use-github` teaches day-to-day issue and PR work
through the Verbs; the discipline of filing is the generic `create-issue`
Skill and that of working and changing an issue is `work-issue`
([use-issues](../use-issues/index.md)), and `use-github` keeps GitHub's
mechanics for them. The generic `setup-issue-tracker` Skill
([use-issues](../use-issues/index.md)) bootstraps a repo's labels and board
through its bundled GitHub steps. The generic `triage-issues` Skill
([use-issues](../use-issues/index.md)) has its GitHub mechanics here: six
`triage-*` scripts, the only writes an unattended pass is granted.

How and why it works: [design.md](design.md).

## Status

| Capability | State | Where |
|---|---|---|
| Orientation: repo identity, labels, linked boards, priority regime, board conformance, Tracker Schema warnings | shipped | `ghw-orient` |
| Issue filing under the label attachment contract, from the repo's Tracker Schema | shipped | `ghw-issue-create` |
| Issue comment, label edit, retitle, body rewrite | shipped | `ghw-issue-comment`, `ghw-issue-edit` |
| Issue close with a mandatory reason | shipped | `ghw-issue-close` |
| Issue relationships: sub-issues and blocked-by | shipped | `ghw-issue-link` |
| Board field writes (Priority, Status, other single-selects) | shipped | `ghw-board-set` |
| Label sync to the repo's Tracker Schema, with deletion as a separate grantable mode | shipped | `ghw-label-sync` |
| Board schema sync and new-board creation | shipped | `ghw-board-sync` |
| PR create, comment, and gated merge | shipped | `ghw-pr-create`, `ghw-pr-comment`, `ghw-pr-merge` |
| Day-to-day issue and PR conventions | shipped | `use-github` |
| Repo tracking bootstrap: labels, board, backlog import | shipped | `skills/setup-issue-tracker/github.md` |
| GitHub mechanics of a triage pass: bulk reads and bounded unattended writes | shipped | `triage-*` scripts |
| Scheduled unattended triage via a guard-script background job | shipped | [DEPLOYMENT.md](../../../skills/triage-issues/reference/DEPLOYMENT.md) |
| Exit codes per the [Exit-code contract](../../index.md#exit-code-contract), with `gh` and API failures classified in one place | shipped | `lib/github/gh.py`, each Verb |
| `triage-*` wrappers rebased onto the shared library | planned | [triage-library-rebase.md](triage-library-rebase.md); `agent-tooling-t7y` |

### Known gaps

- `ghw-issue-close` cannot carry GitHub's `state_reason` (completed or not
  planned), which `triage-apply-sync` reads to choose Done or Rejected
  (`agent-tooling-0fm`).
- Unattended triage cannot run in a repo whose project or local settings
  grant ghw write Verbs; no mechanism isolates the pass from those grants
  (`agent-tooling-ys3`).
- The triage bootstrap (`DEPLOYMENT.md` §6) creates the ledger issue with
  raw `gh issue create` instead of a Verb. The ledger is a `meta` issue
  classified like any other; which `area:` label it takes is not decided
  (`agent-tooling-5kf`).
- `ghw-board-sync`'s write path, including `new`, has never run against the
  live GitHub API; it is verified by schema introspection and unit tests only
  (`agent-tooling-2ul`).
- `triage-timeline` reports only the pull requests GitHub links as closing
  an issue; a PR that names it only by a `Lands:` or `Advances:` trailer is
  not reported (`agent-tooling-m1sl`).
- No triage script reads comments, so a claim recorded as a comment is
  invisible to a pass that has only the scripts (`agent-tooling-wtxg`).
- The `triage-*` Status row describes scripts bundled under
  `skills/triage-issues/reference/` and invoked by path, not `cli/` Wrappers
  on PATH (`agent-tooling-buqr`).
- The six `triage-*` reference scripts run the first `python3` on PATH
  rather than the system interpreter the Wrappers pin (`agent-tooling-15u`).
- The `ghw-*` Verbs still exit the earlier seven-code taxonomy, not the
  six-code Exit-code contract (`agent-tooling-cjvo.2`).
- The six `triage-*` reference scripts exit `0`, `1`, and `2` only, not
  the six-code Exit-code contract (`agent-tooling-cjvo.7`).
- The six `triage-*` scripts read the `TRIAGE.md` profile, not the repo's
  Tracker Schema, and work to eight board `Status` options where the
  default Issue State Diagram has six open states and one closed one:
  `triage-apply-sync` writes Done or Rejected to a closed issue and sends a
  reopened one to Needs Scope whatever the diagram says
  (`agent-tooling-u9n.12`).
- No `triage-*` script comments on an issue or adds the `human` label, so
  an unattended pass lists its findings in the ledger instead of putting
  each on the affected issue (`agent-tooling-u9n.13`).
- No `triage-*` script returns an issue's body or comments, or the
  ledger's current body, so an unattended pass cannot judge a bar that
  depends on what an issue says, read an earlier finding or a person's
  answer, or carry a finding forward (`agent-tooling-u9n.14`).
- No triage pass has run end to end with real writes; the scripts were
  validated with live reads and dry-run writes (`agent-tooling-8y73`).
- `triage-timeline` reads only the first 100 timeline events of an issue, so
  without `--since` a busy issue reports activity that is not its latest
  (`agent-tooling-oj8w`).
- A repo's board cannot follow its Tracker Schema on GitHub:
  `ghw-board-sync` provisions fixed `Status` and `Priority` options with
  fixed colours, the priority regime is judged against P0 to P3, and
  `ghw-orient`'s `priority_labels_present` reports only P0 to P3, rather
  than reading the repo's `TRACKER.md` from its default branch, as the
  [use-issues design](../use-issues/design.md#how-a-wrapper-uses-the-schema)
  says it should (`agent-tooling-u9n.21`).
- `ghw-label-sync` keeps a label named for an Issue State but never creates
  one, because where a repo with no board records an Issue's state is not
  decided (`agent-tooling-vb2v`).
- `ghw-issue-create` and `ghw-issue-edit` match label names exactly, so a
  live `Human` refuses `human`, though GitHub and `ghw-label-sync` treat
  them as one label (`agent-tooling-uln8`).
