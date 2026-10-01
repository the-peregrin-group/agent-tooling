# gitw

gitw is the Wrapper over git, paired with the `use-git` Skill. The Skill
carries git discipline for agents: never act on unverified-fresh state,
work on your own branch in your own worktree, keep history semi-linear
with integration bubbles. The Wrapper carries every mutating git operation
as a Verb with a rigid positional form that a Permission rule can pin by
Roster label and Branch prefix, so no consumer needs raw mutating `git`.
Reads stay raw git under a curated, audited set of Permission rules.

Code: the `cli/gitw-*` Verbs over `cli/lib/git/` and the shared
`cli/lib/`, and `skills/use-git/SKILL.md`. How and why:
[design.md](design.md). Dated docs beside it:
[trunk-sync.md](trunk-sync.md) (proposal) and
[read-allowlist-audit.md](read-allowlist-audit.md) (audit).

## Status

| Capability | State | Where |
| --- | --- | --- |
| Orient: identity check, fetch, branch/dirt/ahead-behind report | shipped | `gitw-orient` |
| Start or resume a branch from the authoritative default | shipped | `gitw-branch-start` |
| Commit all or by pathspec, with sweep guard and `Executed-By` trailer | shipped | `gitw-commit` |
| Rebase own branch onto the default branch, with conflict stop, continue, abort | shipped | `gitw-rebase` |
| Push own branch under lease, or move a named pointer ref | shipped | `gitw-push` |
| Direct integration: bubble onto a base branch under an exact lease | shipped | `gitw-integrate` |
| Roster registration ceremony | shipped | `gitw-repo-register` |
| Git discipline for agents (hygiene, modes, history policy, Verb usage) | shipped | `use-git` Skill |
| Fast-forward the primary checkout's local default branch | planned | `gitw-trunk-sync`; [trunk-sync.md](trunk-sync.md); `agent-tooling-1790288521317-5-34a5f7c2` |

### Known gaps

- A push rejected by the remote's own hooks reports exit 6 (retryable)
  instead of a refusal (`agent-tooling-h3c`).
- A hung local pre-push hook times out as exit 6, inviting a retry
  (`agent-tooling-bl4`).
- Mutating Verbs refuse a cwd admitted only by `operable_from` (exit 4),
  while `use-git` still promises cross-repo writes under that interlock
  (`agent-tooling-1790288522193-11-242cbfe6`).
- `gitw-rebase` rebases only onto the default branch, so integrating
  into a designated non-default base has no rebase step
  (`agent-tooling-ndt`).
- `use-git` still describes the retired third operating mode (work
  directly on the default branch) and lacks the session-start ceremony
  (Issue to be filed).
- `use-git` attributes the Permission-rule token boundary to the Branch
  prefix's trailing slash; the boundary is the space before the star
  (`agent-tooling-4zo`).
- `use-git` cites the repo's policy spec for exact gitw deny rules it does
  not carry (Issue to be filed).
