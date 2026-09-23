"""HTTP layer for the Forgejo REST API (urllib, stdlib-only).

Every request targets the single host in the deployment config -- paths here
are always relative, so the wrappers cannot egress anywhere else by
construction. Auth is `Authorization: token <...>`; responses are parsed
JSON, raw API objects end to end.

Failures classify into the shared exit-code taxonomy (lib.plan): connection
problems and timeouts are network (6, retryable); 401/403 are auth (5);
404 is not-found (3); anything else HTTP is unclassified runtime (1), which
callers may reclassify when a status carries verb-specific meaning (e.g.
409 on create = duplicate PR = caller bug, exit 4).
"""

from __future__ import annotations

import json
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, NoReturn

from lib import plan
from lib.forgejo.config import Config

_TIMEOUT_SECONDS = 30
USER_AGENT = "fjw (agent-tooling wrapper CLI)"


class ApiError(Exception):
    """A classified API failure: `exit_code` is from the shared taxonomy."""

    def __init__(self, message: str, exit_code: int, status: int | None = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.status = status


def die(message: str, code: int) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def request(
    config: Config,
    method: str,
    path: str,
    *,
    query: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    """Perform one API call and return the parsed JSON body (None on 204).

    `path` is relative to /api/v1 (leading slash required); `query` values
    are URL-encoded here, so branch names et al. need no caller escaping.
    Raises ApiError, classified as in the module docstring.
    """
    if not path.startswith("/"):
        raise ValueError(f"api path must start with '/', got {path!r}")
    url = f"{config.api_url}/api/v1{path}"
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = None
    headers = {
        "Authorization": f"token {config.token}",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as response:
            payload = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        detail = _error_detail(error)
        if error.code in (401, 403):
            raise ApiError(
                f"{method} {path}: HTTP {error.code} (auth){detail}",
                plan.EXIT_AUTH,
                error.code,
            )
        if error.code == 404:
            raise ApiError(
                f"{method} {path}: HTTP 404 (not found){detail}",
                plan.EXIT_NOT_FOUND,
                404,
            )
        raise ApiError(
            f"{method} {path}: HTTP {error.code}{detail}",
            plan.EXIT_RUNTIME,
            error.code,
        )
    except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as error:
        reason = getattr(error, "reason", None) or error
        raise ApiError(
            f"{method} {path}: network failure ({reason})", plan.EXIT_NETWORK
        )
    if status == 204 or not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        raise ApiError(
            f"{method} {path}: server returned non-JSON (HTTP {status})",
            plan.EXIT_RUNTIME,
            status,
        )


def _error_detail(error: urllib.error.HTTPError) -> str:
    """The server's error message, if it sent a parseable one."""
    try:
        parsed = json.loads(error.read())
    except (OSError, json.JSONDecodeError, ValueError):
        return ""
    message = parsed.get("message") if isinstance(parsed, dict) else None
    return f": {message}" if message else ""


def fetch_swagger(config: Config) -> dict | None:
    """The instance's own API description (/swagger.v1.json), or None when it
    cannot be fetched or parsed -- feature probes then assume the older API."""
    url = f"{config.api_url}/swagger.v1.json"
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as response:
            return json.loads(response.read())
    except (urllib.error.URLError, OSError, ValueError):
        return None


def supports_head_filter(swagger: dict | None) -> bool:
    """Whether GET /repos/{owner}/{repo}/pulls takes a `head` query filter
    (Forgejo v16.0+), judged from the instance's own swagger. False on any
    doubt -- the caller falls back to client-side filtering, which is always
    correct, just heavier."""
    node = swagger
    for key in ("paths", "/repos/{owner}/{repo}/pulls", "get"):
        if not isinstance(node, dict):
            return False
        node = node.get(key)
    if not isinstance(node, dict) or not isinstance(node.get("parameters"), list):
        return False
    return any(
        parameter.get("name") == "head" and parameter.get("in") == "query"
        for parameter in node["parameters"]
        if isinstance(parameter, dict)
    )
