"""Thin subprocess wrapper over the `gh` CLI, shared by the triage wrappers.

All GitHub I/O the agent is allowed to perform autonomously goes through a
wrapper script; those wrappers call `gh` only via this module. The agent never
invokes `gh` directly (it is not on the headless allowlist), so the autonomy
boundary and the permission boundary are the same line: a proposed mutation has
no wrapper, hence no allowlisted path, hence fails closed.
"""

from __future__ import annotations

import json
import subprocess
import sys


class GhError(Exception):
    pass


def _run(args: list[str], *, input_text: str | None = None) -> str:
    try:
        proc = subprocess.run(
            ["gh", *args],
            input=input_text,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise GhError("gh CLI not found on PATH")
    if proc.returncode != 0:
        raise GhError(
            f"gh {' '.join(args)} failed (exit {proc.returncode}):\n{proc.stderr.strip()}"
        )
    return proc.stdout


def graphql(query: str, variables: dict | None = None) -> dict:
    """Run a GraphQL query/mutation. Variables are passed as typed -F/-f fields.

    GraphQL nullable variables that are omitted default to null server-side, so
    callers may simply leave a variable out of `variables` to send null.
    """
    args = ["api", "graphql", "-f", f"query={query}"]
    for k, v in (variables or {}).items():
        if v is None:
            continue
        if isinstance(v, bool):
            args += ["-F", f"{k}={'true' if v else 'false'}"]
        elif isinstance(v, int):
            args += ["-F", f"{k}={v}"]  # -F = typed (number)
        else:
            args += ["-f", f"{k}={v}"]  # -f = raw string
    out = _run(args)
    data = json.loads(out)
    if "errors" in data and data["errors"]:
        raise GhError("GraphQL errors: " + json.dumps(data["errors"], indent=2))
    return data["data"]


def rest(method: str, path: str, fields: dict | None = None, *, accept: str | None = None) -> dict | list:
    args = ["api", "-X", method, path]
    if accept:
        args += ["-H", f"Accept: {accept}"]
    for k, v in (fields or {}).items():
        if isinstance(v, int):
            args += ["-F", f"{k}={v}"]
        else:
            args += ["-f", f"{k}={v}"]
    out = _run(args)
    return json.loads(out) if out.strip() else {}


def issue_list_open(repo: str, limit: int = 500) -> list[dict]:
    out = _run(["issue", "list", "--repo", repo, "--state", "open",
                "--limit", str(limit), "--json", "number,title"])
    return json.loads(out)


def issue_edit_labels(repo: str, number: int, add: list[str], remove: list[str]) -> None:
    args = ["issue", "edit", str(number), "--repo", repo]
    for label in add:
        args += ["--add-label", label]
    for label in remove:
        args += ["--remove-label", label]
    _run(args)


def issue_edit_body(repo: str, number: int, body: str) -> None:
    # Reads body from stdin via --body-file - to avoid shell-quoting issues.
    _run(["issue", "edit", str(number), "--repo", repo, "--body-file", "-"], input_text=body)


def issue_comment(repo: str, number: int, body: str) -> None:
    _run(["issue", "comment", str(number), "--repo", repo, "--body-file", "-"], input_text=body)


def die(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)
