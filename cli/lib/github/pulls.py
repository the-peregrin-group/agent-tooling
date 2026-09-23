"""Pure PR-merge gate checks for ghw-pr-merge: the PR's actual base branch
must equal the stated one (trust-but-verify), plus the draft and
green-checks gates.

Many repos carry no branch protection, so `gh pr merge` on its own
enforces nothing; these checks are the wrapper's teeth. There is no force or
override path -- merging over a red gate stays raw `gh` with a human at the
prompt.
"""

from __future__ import annotations

# A CheckRun is green only when finished with one of these conclusions;
# failures, cancellations, and runs still in flight all block a merge.
_GREEN_CONCLUSIONS = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})


def _failing_checks(status_check_rollup: list[dict] | None) -> list[str]:
    """Describe the rollup entries that are not green.

    An empty or absent rollup means no checks are configured, which passes
    (returns []). Entries are the objects `gh pr view --json
    statusCheckRollup` emits: CheckRun nodes carry status/conclusion,
    StatusContext (commit status) nodes carry state.
    """
    failing = []
    for entry in status_check_rollup or []:
        if "state" in entry:  # StatusContext
            if entry["state"] != "SUCCESS":
                failing.append(f"{entry.get('context', '<status>')} ({entry['state']})")
        else:  # CheckRun
            status = entry.get("status")
            conclusion = entry.get("conclusion")
            if status != "COMPLETED" or conclusion not in _GREEN_CONCLUSIONS:
                detail = conclusion or status or "UNKNOWN"
                failing.append(f"{entry.get('name', '<check>')} ({detail})")
    return failing


def merge_refusals(pull: dict, base_branch: str) -> list[str]:
    """Every reason this PR must not be merged right now; empty when clear.

    `pull` is `gh pr view --json state,isDraft,baseRefName,statusCheckRollup`.
    Gates: the PR is open, its actual base matches the stated `base_branch`
    (trust-but-verify: the scope argument is a claim about an existing
    object), it is not a draft, and its checks are green or absent.
    """
    refusals = []
    if pull["state"] != "OPEN":
        refusals.append(f"PR is {pull['state']}, not OPEN")
    if pull["baseRefName"] != base_branch:
        refusals.append(
            f"PR's actual base branch is {pull['baseRefName']!r}, not "
            f"{base_branch!r} -- the stated scope does not match the object"
        )
    if pull.get("isDraft"):
        refusals.append("PR is a draft")
    red = _failing_checks(pull.get("statusCheckRollup"))
    if red:
        refusals.append(
            "checks are not green: " + ", ".join(red)
            + ". There is no override path here; merging over red checks is a "
            "human decision at a raw gh prompt"
        )
    return refusals
