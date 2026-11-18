# `triage-issues` reference: the GitHub scripts

This directory holds the GitHub mechanics of a triage pass: six scripts
that do a pass's bulk reads and its unattended writes. The discipline of a
pass is in `../SKILL.md`, which is written against no platform; its
"Platform mechanics" section says how its steps map onto these scripts and
what the scripts still assume. `DEPLOYMENT.md` covers running a recurring
unattended pass safely.

## The scripts

All are stdlib-only Python 3 (no venv, no pip). Invoke each by full path as
`python3 <path>/<script> …`, spelled exactly as the allowlist in
`DEPLOYMENT.md` spells it. Each reads the project profile via `--profile
PATH`, the `TRIAGE_PROFILE` env var, or a `TRIAGE.md` found upward from cwd,
and each prints its arguments with `--help`.

| Script | Kind | Bound by | Output |
|---|---|---|---|
| `triage-inventory` | read | (read-only) | board-anchored inventory, and the open issues missing from the board (JSON) |
| `triage-timeline <issue#>… [--since <time>]` | read | (read-only) | per issue: latest meaningful activity, closing pull requests, linkage events (JSON) |
| `triage-apply-sync <issue#>` | write | **policy**: derives the correction itself; cannot be told a target | the correction derived or applied |
| `triage-fix-label <issue#> --add <label> --remove <label>` | write | **schema**: refuses labels outside the profile's lists | the label change |
| `triage-bump-triaged <issue#>` | write | **value**: writes only the `Last Triaged` date | the date written |
| `triage-update-ledger --body-file <path> --comment-file <path>` | write | **target**: writes only to the profile's ledger issue | body and comment written |

Every write script accepts `--dry-run` (print the plan, mutate nothing).

`triage-apply-sync` makes an issue's open-or-closed and its board `Status`
agree, and nothing else. Its output's `rule` field and its comments name
its two corrections by the labels an earlier edition of the skill gave
them: `R-SYNC-2` is a closed issue whose `Status` is not Done or Rejected
(it writes Done, or Rejected when the issue was closed as not planned), and
`R-SYNC-1` is an open issue whose `Status` is Done or Rejected (it writes
Needs Scope). Other labels of that kind in the scripts' comments (`R-LABEL`,
`R-LEDG`, `L-LINK`, `R-PARENT`, `R-BLOCK`) point at rules the skill no
longer carries.

**No script moves an issue between open states, sets a priority, rewrites a
body, comments on an issue, closes, or reparents.** A deployment that
grants only these six scripts under a deny-by-default permission mode
therefore cannot do those things: the calls are denied. That is a property
of the deployment's Permission rules, described in `DEPLOYMENT.md`, and not
a rule of the skill.

## Shared modules (imported, never invoked directly, not allowlisted)

- `lib_profile.py`: the only parser of the profile config block, a fenced,
  marker-delimited JSON block in `TRIAGE.md`. JSON, not YAML, so the scripts
  import cleanly on any Python with no dependency to bootstrap for a
  headless run.
- `lib_gh.py`: a thin subprocess layer over `gh` (GraphQL, REST, and a few
  issue helpers). The scripts call `gh` only through here.
