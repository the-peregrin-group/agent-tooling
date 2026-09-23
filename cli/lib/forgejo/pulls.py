"""PR operations for the fjw-* wrappers: raw Forgejo API objects end to end.

The one piece of interpretation this module adds is the quad-state head
query. The API's `mergeable` field is a plain boolean that conflates
check-running / conflict / check-error / draft (the internal status enum is
not exposed), so `query_state` reports:

    none       -- no open PR with that head branch
    draft      -- open, but a draft (mergeable is meaningless for drafts)
    mergeable  -- open and the conflict check has it clean
    conflicted -- open, not a draft, and mergeable stayed false through a
                  short backoff poll

"Conflicted" is the best-available heuristic, not ground truth: no
"check finished" signal exists, so a slow conflict check can misreport as
conflicted. Checks settle in seconds on a healthy instance; the poll waits
~7s total before concluding.
"""

from __future__ import annotations

import re
import time
from typing import Any, Callable

from lib.forgejo import api
from lib.forgejo.config import Config
from lib import plan

_PAGE_SIZE = 50
# Backoff between mergeable re-fetches; ~7s total. See module docstring.
_POLL_DELAYS_SECONDS = (1, 2, 4)

# Forgejo's AlphaDashDot charset for both owner and repo name (unlike
# GitHub, owners may contain underscores and dots). The value is spliced
# into REST paths, so the charset is load-bearing.
_REPOSITORY_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$"
)


def is_valid_repository(repository: str) -> bool:
    """True for a plausible Forgejo 'owner/name'. The path-traversal names
    '.' and '..' are excluded for both halves."""
    if not _REPOSITORY_PATTERN.match(repository):
        return False
    owner, name = repository.split("/", 1)
    return owner not in (".", "..") and name not in (".", "..")


def get_pr(config: Config, repository: str, index: int) -> dict:
    """The raw PR object; ApiError exit 3 when no such PR exists (including
    when `index` names an issue, not a PR -- the /pulls route 404s there)."""
    return api.request(config, "GET", f"/repos/{repository}/pulls/{index}")


def list_open_prs(config: Config, repository: str) -> list[dict]:
    """Every open PR, paginated to exhaustion."""
    prs: list[dict] = []
    page = 1
    while True:
        batch = api.request(
            config,
            "GET",
            f"/repos/{repository}/pulls",
            query={"state": "open", "limit": str(_PAGE_SIZE), "page": str(page)},
        ) or []
        prs.extend(batch)
        if len(batch) < _PAGE_SIZE:
            return prs
        page += 1


def find_open_prs_by_head(
    config: Config, repository: str, head: str
) -> list[dict]:
    """Open PRs whose head branch is exactly `head`, newest first.

    Uses the server-side `?head=` filter when the instance's swagger
    advertises it (Forgejo v16.0+), falling back to listing all open PRs and
    filtering here. The head match is re-verified client-side either way
    (trust but verify). The state-blind /pulls/{base}/{head} endpoint is
    never used for existence checks (known upstream bug).
    """
    if api.supports_head_filter(api.fetch_swagger(config)):
        candidates = api.request(
            config,
            "GET",
            f"/repos/{repository}/pulls",
            query={"state": "open", "head": head, "limit": str(_PAGE_SIZE)},
        ) or []
    else:
        candidates = list_open_prs(config, repository)
    matches = [
        pr for pr in candidates if (pr.get("head") or {}).get("ref") == head
    ]
    return sorted(matches, key=lambda pr: pr.get("number", 0), reverse=True)


def query_state(
    config: Config,
    repository: str,
    head: str,
    *,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[str, dict | None]:
    """The quad-state answer for `head` (see module docstring) and the raw
    PR object it was judged from (None for state "none"). When several open
    PRs share the head branch -- possible with distinct base branches -- the
    newest is judged."""
    matches = find_open_prs_by_head(config, repository, head)
    if not matches:
        return "none", None
    pr = matches[0]
    if pr.get("draft"):
        return "draft", pr
    if pr.get("mergeable"):
        return "mergeable", pr
    for delay in _POLL_DELAYS_SECONDS:
        sleep(delay)
        pr = get_pr(config, repository, pr["number"])
        if pr.get("draft"):
            return "draft", pr
        if pr.get("mergeable"):
            return "mergeable", pr
    return "conflicted", pr


def branch_exists(config: Config, repository: str, branch: str) -> bool:
    try:
        api.request(config, "GET", f"/repos/{repository}/branches/{branch}")
    except api.ApiError as error:
        if error.exit_code == plan.EXIT_NOT_FOUND:
            return False
        raise
    return True


def create_pr(
    config: Config,
    repository: str,
    base: str,
    head: str,
    title: str,
    body: str,
) -> dict:
    """POST the PR; the raw PR object back. A 409 (an open PR for this
    head/base already exists) reclassifies to exit 4: the consumer queries
    before creating, so a duplicate create is a caller bug, never a retry."""
    try:
        return api.request(
            config,
            "POST",
            f"/repos/{repository}/pulls",
            body={"base": base, "head": head, "title": title, "body": body},
        )
    except api.ApiError as error:
        if error.status == 409:
            raise api.ApiError(
                f"an open PR for {head!r} -> {base!r} already exists on "
                f"{repository}: {error}",
                plan.EXIT_REFUSED,
                409,
            )
        raise


def create_comment(
    config: Config, repository: str, index: int, body: str
) -> dict:
    """Comment on PR `index` (PR comments ride the issue routes)."""
    return api.request(
        config,
        "POST",
        f"/repos/{repository}/issues/{index}/comments",
        body={"body": body},
    )


def list_comments(config: Config, repository: str, index: int) -> list[dict]:
    """Every comment on PR `index`, paginated to exhaustion."""
    comments: list[dict] = []
    page = 1
    while True:
        batch = api.request(
            config,
            "GET",
            f"/repos/{repository}/issues/{index}/comments",
            query={"limit": str(_PAGE_SIZE), "page": str(page)},
        ) or []
        comments.extend(batch)
        if len(batch) < _PAGE_SIZE:
            return comments
        page += 1


def close_pr(config: Config, repository: str, index: int) -> dict:
    """PATCH the PR closed; the raw updated PR object back."""
    return api.request(
        config,
        "PATCH",
        f"/repos/{repository}/pulls/{index}",
        body={"state": "closed"},
    )
