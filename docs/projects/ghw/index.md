# ghw: the GitHub Wrapper and its Skills

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
through the Verbs. `setup-github-issues` bootstraps a repo's label schema and
board. `triage-issues` runs repeatable backlog triage, with six `triage-*`
reference wrappers as the only write path an unattended pass has.

How and why it works: [design.md](design.md).

## Status

| Capability | State | Where |
|---|---|---|
| Orientation: repo identity, labels, linked boards, priority regime, board conformance | shipped | `ghw-orient` |
| Issue filing under the label contract | shipped | `ghw-issue-create` |
| Issue comment, label edit, retitle, body rewrite | shipped | `ghw-issue-comment`, `ghw-issue-edit` |
| Issue close with an optional reason | shipped | `ghw-issue-close` |
| Issue relationships: sub-issues and blocked-by | shipped | `ghw-issue-link` |
| Board field writes (Priority, Status, other single-selects) | shipped | `ghw-board-set` |
| Label schema sync, with deletion as a separate grantable mode | shipped | `ghw-label-sync` |
| Board schema sync and new-board creation | shipped | `ghw-board-sync` |
| PR create, comment, and gated merge | shipped | `ghw-pr-create`, `ghw-pr-comment`, `ghw-pr-merge` |
| Day-to-day issue and PR conventions | shipped | `use-github` |
| Repo tracking bootstrap: labels, board, backlog import | shipped | `setup-github-issues` |
| Backlog triage and grooming, with autonomous writes through dedicated wrappers | shipped | `triage-issues`, `triage-*` |
| Scheduled unattended triage via a guard-script background job | shipped | [DEPLOYMENT.md](../../../skills/triage-issues/reference/DEPLOYMENT.md) |
| Mandatory closing comment on every issue close | planned | `ghw-issue-close`, `setup-github-issues`; [fjw issue-verbs proposal](../fjw/issue-verbs.md); `agent-tooling-75z` |
| Full Exit-code contract (codes 3 to 6) for ghw | planned | [Exit-code contract](../../index.md#exit-code-contract); `agent-tooling-9qe` |
| `triage-*` wrappers rebased onto the shared library | planned | [triage-library-rebase.md](triage-library-rebase.md); `agent-tooling-t7y` |

### Known gaps

- `ghw-pr-merge` still accepts a `squash` strategy token, although squash is
  banned in every repo (`agent-tooling-589`).
- The triage Skill and `DEPLOYMENT.md` still document launch forms besides
  the guard-script background job, and scope the ghw-grant caveat to project
  settings only, omitting local settings (`agent-tooling-za1`).
- Unattended triage cannot run in a repo whose project or local settings
  grant ghw write Verbs; no mechanism isolates the pass from those grants
  (`agent-tooling-ys3`).
- The triage bootstrap (R-CAD-6 and `DEPLOYMENT.md` §6) creates the ledger
  issue with raw `gh issue create` instead of a Verb; needs a decision first
  on whether the triage-excluded ledger issue takes the type and `area:`
  labels `ghw-issue-create` requires (`agent-tooling-5kf`).
- `triage-inventory` silently omits open issues beyond the first 500
  (`agent-tooling-lo7`).
- `ghw-label-sync` and `label_schema.py` docstrings say all nine GitHub stock
  labels become deletions; it is eight, since stock `bug` is a canonical type
  label (`agent-tooling-ln2`).
- `ghw-board-sync`'s write path, including `new`, has never run against the
  live GitHub API; it is verified by schema introspection and unit tests only
  (`agent-tooling-2ul`).
- The ghw Verbs and `triage-*` run the first `python3` on PATH rather than
  the system interpreter the other Wrappers pin
  (`agent-tooling-1790288520721-1-86415521`).
