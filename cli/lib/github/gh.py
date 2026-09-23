"""Thin subprocess wrapper over the `gh` CLI, shared by all ghw-* wrappers.

All GitHub I/O a wrapper performs goes through this module. Wrapper-internal
`gh` subprocesses never produce a Bash command string, so settings.json
ask/deny rules for `gh api` do not apply to them -- the validation inside each
wrapper is the only guard, so every wrapper validates its own arguments
before they reach `gh`.

Lifted from triage-issues' lib_gh.py, then deliberately hardened; the triage
wrappers are meant to move onto this copy later and inherit the hardening.
Deltas from the original:
  - every subprocess gets a timeout (GH_TIMEOUT_SECONDS) and, when no input
    is being piped, stdin closed off -- a `gh` subcommand that prompts or a
    stalled connection fails loudly instead of hanging an unattended run
  - non-JSON output and a missing `data` object raise GhError instead of
    escaping as JSONDecodeError/KeyError tracebacks
  - rest() sends booleans as JSON true/false (bool is checked before int,
    as graphql() always did)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from typing import NoReturn

# Generous: covers slow API responses without masking a genuine hang.
GH_TIMEOUT_SECONDS = 120


class GhError(Exception):
    """Raised when the `gh` CLI is missing, exits nonzero, or returns GraphQL errors."""


def graphql(query: str, variables: dict | None = None) -> dict:
    """Run a GraphQL query or mutation and return the response's `data` object.

    Variables are passed as typed fields: booleans and integers keep their
    types; everything else is sent as a raw string. GraphQL nullable variables
    that are omitted default to null server-side, so callers may simply leave
    a variable out of `variables` to send null.

    Raises GhError on any `gh` failure or if the response carries GraphQL
    errors.
    """
    arguments = ["api", "graphql", "-f", f"query={query}"]
    for name, value in (variables or {}).items():
        if value is None:
            continue
        if isinstance(value, bool):
            arguments += ["-F", f"{name}={'true' if value else 'false'}"]
        elif isinstance(value, int):
            arguments += ["-F", f"{name}={value}"]
        else:
            arguments += ["-f", f"{name}={value}"]
    output = _run(arguments)
    try:
        response = json.loads(output)
    except json.JSONDecodeError:
        raise GhError(f"gh api graphql returned non-JSON output:\n{output[:500]}")
    if not isinstance(response, dict):
        raise GhError(f"gh api graphql returned a non-object response:\n{output[:500]}")
    if response.get("errors"):
        raise GhError("GraphQL errors: " + json.dumps(response["errors"], indent=2))
    if "data" not in response:
        raise GhError(f"GraphQL response carries no data object:\n{output[:500]}")
    return response["data"]


def rest(
    method: str,
    path: str,
    fields: dict | None = None,
    *,
    accept: str | None = None,
) -> dict | list:
    """Call a REST endpoint and return the parsed JSON response.

    Boolean and integer fields are sent typed; everything else as strings.
    `accept` sets the request's Accept header for endpoints needing a
    non-default media type. Returns an empty dict for endpoints that respond
    with no body. Raises GhError on any `gh` failure.
    """
    arguments = ["api", "-X", method, path]
    if accept:
        arguments += ["-H", f"Accept: {accept}"]
    for name, value in (fields or {}).items():
        if isinstance(value, bool):
            arguments += ["-F", f"{name}={'true' if value else 'false'}"]
        elif isinstance(value, int):
            arguments += ["-F", f"{name}={value}"]
        else:
            arguments += ["-f", f"{name}={value}"]
    output = _run(arguments)
    if not output.strip():
        return {}
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        raise GhError(f"gh api returned non-JSON output:\n{output[:500]}")


def version() -> tuple[int, int, int]:
    """The local `gh` CLI's version as (major, minor, patch).

    Wrappers whose features have a `gh` version floor check this and fail
    clearly below it. Raises GhError if `gh` is missing or its version banner
    cannot be parsed.
    """
    output = _run(["--version"])
    match = re.search(r"gh version (\d+)\.(\d+)\.(\d+)", output)
    if not match:
        raise GhError(f"cannot parse gh version from:\n{output[:200]}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def issue_list_open(repository: str, limit: int = 500) -> list[dict]:
    """Return the repository's open issues as [{"number": ..., "title": ...}].

    Returns at most `limit` issues; any beyond that are silently omitted.
    Raises GhError on any `gh` failure.
    """
    output = _run(["issue", "list", "--repo", repository, "--state", "open",
                   "--limit", str(limit), "--json", "number,title"])
    return _parse_json(output, "gh issue list")


def issue_edit_labels(repository: str, number: int, add: list[str], remove: list[str]) -> None:
    """Add and remove the given labels on one issue in a single `gh` call.

    Raises GhError on any `gh` failure (including unknown label names).
    """
    arguments = ["issue", "edit", str(number), "--repo", repository]
    for label in add:
        arguments += ["--add-label", label]
    for label in remove:
        arguments += ["--remove-label", label]
    _run(arguments)


def issue_edit_body(repository: str, number: int, body: str) -> None:
    """Replace an issue's body. Raises GhError on any `gh` failure."""
    # The body travels over stdin via `--body-file -` to avoid shell quoting.
    _run(["issue", "edit", str(number), "--repo", repository, "--body-file", "-"],
         input_text=body)


def issue_comment(repository: str, number: int, body: str) -> None:
    """Post a comment on an issue. Raises GhError on any `gh` failure."""
    _run(["issue", "comment", str(number), "--repo", repository, "--body-file", "-"],
         input_text=body)


def issue_view(repository: str, number: int, json_fields: list[str]) -> dict:
    """Return the requested --json fields of one issue.

    Raises GhError on any `gh` failure (including a nonexistent issue).
    """
    output = _run(["issue", "view", str(number), "--repo", repository,
                   "--json", ",".join(json_fields)])
    return _parse_json(output, "gh issue view")


def issue_create(repository: str, title: str, body: str, labels: list[str]) -> str:
    """Create an issue and return its URL (gh's stdout, stripped).

    Raises GhError on any `gh` failure (including unknown label names).
    """
    arguments = ["issue", "create", "--repo", repository, "--title", title,
                 "--body-file", "-"]
    for label in labels:
        arguments += ["--label", label]
    return _run(arguments, input_text=body).strip()


def issue_edit_title(repository: str, number: int, title: str) -> None:
    """Retitle an issue. Raises GhError on any `gh` failure."""
    _run(["issue", "edit", str(number), "--repo", repository, "--title", title])


def issue_close(repository: str, number: int, comment: str | None = None) -> None:
    """Close an issue, optionally carrying its reason as a comment in the same
    call. Raises GhError on any `gh` failure.
    """
    arguments = ["issue", "close", str(number), "--repo", repository]
    if comment is not None:
        arguments += ["--comment", comment]
    _run(arguments)


# The four sub-issue/dependency edits ghw-issue-link exposes. "X blocks Y" is
# expressed as "Y blocked-by X", so gh's --add-blocking/--remove-blocking are
# deliberately absent.
DEPENDENCY_FLAGS: dict[str, str] = {
    "add-sub": "--add-sub-issue",
    "remove-sub": "--remove-sub-issue",
    "add-blocked-by": "--add-blocked-by",
    "remove-blocked-by": "--remove-blocked-by",
}


def issue_edit_dependency(repository: str, number: int, subverb: str,
                          other_number: int) -> None:
    """Add or remove one sub-issue/dependency edge on `number`.

    `subverb` is a key of DEPENDENCY_FLAGS; `number` is always the subject
    (the parent, or the blocked issue). Requires gh >= 2.94.0 -- callers check
    the floor first, since below it gh rejects the flag as unknown. Raises
    GhError on any `gh` failure, ValueError on an unknown subverb.
    """
    flag = DEPENDENCY_FLAGS.get(subverb)
    if flag is None:
        raise ValueError(f"unknown dependency subverb {subverb!r}")
    _run(["issue", "edit", str(number), "--repo", repository,
          flag, str(other_number)])


def label_create(repository: str, name: str, color: str, description: str) -> None:
    """Create one label. Raises GhError on any `gh` failure, including a name
    that already exists (callers create only labels they know are missing).
    """
    _run(["label", "create", name, "--repo", repository,
          "--color", color, "--description", description])


def label_edit(repository: str, name: str, color: str, description: str) -> None:
    """Set an existing label's color and description (never its name --
    renaming would silently retarget every attachment). Raises GhError on any
    `gh` failure.
    """
    _run(["label", "edit", name, "--repo", repository,
          "--color", color, "--description", description])


def label_delete(repository: str, name: str) -> None:
    """Delete one label, detaching it from every issue that carries it.

    --yes suppresses gh's interactive confirmation; the wrapper's own
    apply-delete mode is the gate. Raises GhError on any `gh` failure.
    """
    _run(["label", "delete", name, "--repo", repository, "--yes"])


def pr_view(repository: str, number: int, json_fields: list[str]) -> dict:
    """Return the requested --json fields of one pull request.

    Raises GhError on any `gh` failure (including a nonexistent PR).
    """
    output = _run(["pr", "view", str(number), "--repo", repository,
                   "--json", ",".join(json_fields)])
    return _parse_json(output, "gh pr view")


def pr_comment(repository: str, number: int, body: str) -> None:
    """Post a comment on a pull request. Raises GhError on any `gh` failure.

    Its own function because `gh issue comment` refuses PR numbers, so
    issue_comment() cannot cover them.
    """
    _run(["pr", "comment", str(number), "--repo", repository, "--body-file", "-"],
         input_text=body)


def pr_create(repository: str, base: str, head: str, title: str, body: str,
              draft: bool) -> dict:
    """Open a pull request and return the created PR object; callers read
    `number` and `html_url` from it. Raises GhError on any failure.
    """
    # NOTE: This goes straight to POST /repos/{owner}/{repo}/pulls rather
    # than `gh pr create`, which wants a local git context; the REST
    # endpoint is the deliberate choice for exactly this case.
    response = rest("POST", f"repos/{repository}/pulls", {
        "title": title, "head": head, "base": base, "body": body, "draft": draft,
    })
    if not isinstance(response, dict):
        raise GhError(f"unexpected response creating PR: {response!r}")
    return response


def pr_merge(
    repository: str, number: int, strategy: str, expected_head_oid: str | None = None
) -> None:
    """Merge a pull request with the given strategy ("merge" | "squash").

    `expected_head_oid` pins the merge to the head commit the caller just
    verified (--match-head-commit): a push landing between the green-checks
    read and the merge fails loudly instead of merging unchecked code. Never
    passes --delete-branch (worktree hazard). Raises GhError on any `gh`
    failure, ValueError on an unknown strategy (callers validate first).
    """
    if strategy not in ("merge", "squash"):
        raise ValueError(
            f"merge strategy must be 'merge' or 'squash', got {strategy!r}"
        )
    arguments = ["pr", "merge", str(number), "--repo", repository, f"--{strategy}"]
    if expected_head_oid:
        arguments += ["--match-head-commit", expected_head_oid]
    _run(arguments)


def die(message: str, exit_code: int = 1) -> NoReturn:
    """Print `message` to stderr and exit the process with `exit_code`."""
    print(message, file=sys.stderr)
    sys.exit(exit_code)


def _run(arguments: list[str], *, input_text: str | None = None) -> str:
    """Execute `gh` with the given arguments and return its stdout.

    Raises GhError if `gh` is not on PATH, exits nonzero, or exceeds
    GH_TIMEOUT_SECONDS. With no input to pipe, stdin is closed off so a
    subcommand that unexpectedly prompts fails instead of hanging.
    """
    try:
        process = subprocess.run(
            ["gh", *arguments],
            input=input_text,
            stdin=subprocess.DEVNULL if input_text is None else None,
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        raise GhError("gh CLI not found on PATH")
    except OSError as error:
        # E.g. E2BIG from an argv near ARG_MAX; never a raw traceback.
        raise GhError(f"gh {' '.join(arguments[:2])} failed to launch: {error}")
    except subprocess.TimeoutExpired:
        raise GhError(
            f"gh {' '.join(arguments)} timed out after {GH_TIMEOUT_SECONDS}s"
        )
    if process.returncode != 0:
        raise GhError(
            f"gh {' '.join(arguments)} failed (exit {process.returncode}):\n"
            f"{process.stderr.strip()}"
        )
    return process.stdout


def _parse_json(output: str, description: str) -> dict | list:
    """Parse `gh --json`-style output, raising GhError (not a traceback) on
    garbage -- e.g. a killed subprocess that still exited 0."""
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        raise GhError(f"{description} returned non-JSON output:\n{output[:500]}")
