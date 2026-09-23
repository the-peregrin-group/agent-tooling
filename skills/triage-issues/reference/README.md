# `triage-issues` — reference (wrappers + deployment)

This directory holds the skill's **GitHub-I/O wrapper layer**: the only commands
the agent is allowed to run against GitHub. See `../SKILL.md` (`## Cadence &
autonomous operation` → R-CAD-5) for the policy and `DEPLOYMENT.md` for how to run
recurring/unattended passes safely.

## The wrappers

All are stdlib-only Python 3 (no venv / pip). Invoke by full path as
`python3 <path>/<wrapper> …`, spelled exactly as the allowlist in
`DEPLOYMENT.md` spells it. Each reads the project profile via `--profile
PATH`, the `TRIAGE_PROFILE` env var, or a `TRIAGE.md` found upward from cwd.

| Wrapper | Kind | Bound by | Output |
|---|---|---|---|
| `triage-inventory` | read | — | board-anchored inventory + board↔open reconciliation (JSON) |
| `triage-timeline` | read | — | per-issue meaningful-activity + closing-PR + linkage signals (JSON) |
| `triage-apply-sync` | write (autonomous) | **policy** — derives the R-SYNC-1/2 correction; can't be told a target | the applied/derived correction |
| `triage-fix-label` | write (autonomous) | **schema** — refuses labels outside the profile set | the label change |
| `triage-bump-triaged` | write (autonomous) | **value** — writes only the Last Triaged date | the date written |
| `triage-update-ledger` | write (autonomous) | **target** — writes only to the profile's ledger issue | body/comment written |

Every write wrapper accepts `--dry-run` (print the plan, mutate nothing).

**There is deliberately no wrapper for proposed mutations** (status/priority/size
*transitions*, scope-body rewrites, closes, reparenting). Those have no allowlisted
path and fail closed under a deny-by-default permission mode — that is the autonomy
boundary, enforced by the permission layer. See `DEPLOYMENT.md`.

## Shared modules (imported, never invoked directly — not allowlisted)

- `lib_profile.py` — the *only* parser of the profile config block. The config is a
  fenced, marker-delimited JSON block in `TRIAGE.md`. JSON (not YAML) is deliberate:
  stdlib-only parsing means the wrappers import cleanly on any Python with no
  dependency to bootstrap for a headless run. Swapping the on-disk format later
  touches this file alone.
- `lib_gh.py` — thin subprocess layer over `gh` (GraphQL + REST + a few issue
  helpers). The wrappers call `gh` only through here; the agent never calls `gh`.
