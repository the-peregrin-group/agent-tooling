"""The session actor: who is executing a wrapper, derived from the environment.

`derive_actor(environ)` returns one of four shapes, never blank, taking
the first that applies:

    claude-job-<session-id>   CLAUDE_CODE_SESSION_ID is a safe token and
                              CLAUDE_JOB_DIR's basename is a safe token (a
                              background job).
    claude-session-<session-id>
                              CLAUDE_CODE_SESSION_ID is a safe token and
                              there is no usable job directory (an attended
                              session).
    claude-job-<job-id>       no usable session ID, but CLAUDE_JOB_DIR's
                              basename is a safe token; <job-id> is that
                              basename.
    attended-<user>           otherwise; <user> is USER when it is a safe
                              token, else the literal `unknown`.

Why these: the Claude Code harness sets CLAUDE_CODE_SESSION_ID in every
session, attended or not, so a session-derived actor gives each session
its own Actor ID. It also sets CLAUDE_JOB_DIR for background jobs
(`~/.claude/jobs/<job-id>`), and a job's ID is a prefix of its session ID,
so for a job the session-derived actor starts with the actor an older
`bdw` derived from the job ID alone: `claude-job-ae218998` became
`claude-job-ae218998-<rest of the session ID>`, and a reader can match one
to the other. The two lower shapes are fallbacks for an environment
without a usable session ID. `attended-` is deliberately a different shape
rather than a guess: a session whose identity is missing shows up as
`attended-...` in the audit trail, visibly, instead of silently passing
for one. A "safe token" is non-empty, only `[A-Za-z0-9._-]`, and not `.`
or `..`; anything else is treated as absent, so the actor can be spliced
into a git trailer or an environment variable without escaping.

`session_id(environ)` returns the safe-token session ID, or None; `bdw`
passes it to bd as the session that closed an Issue.

The caller passes the mapping (normally `os.environ`); this module never
reads the process environment itself, which keeps it testable and makes
every caller's source of identity explicit.

Consumers: `bdw` (the Beads wrapper) and `gitw-commit` (the `Executed-By:`
trailer). See docs/adr/0002-beads-identity.md.
"""

from __future__ import annotations

import os
import re
from typing import Mapping

# Used with fullmatch: `$` would also match before a final newline.
_SAFE_TOKEN = re.compile(r"[A-Za-z0-9._-]+")

JOB_PREFIX = "claude-job-"
SESSION_PREFIX = "claude-session-"
ATTENDED_PREFIX = "attended-"
UNKNOWN_USER = "unknown"


def _safe_token(value: str | None) -> str | None:
    """`value` if it is a non-empty `[A-Za-z0-9._-]` token other than `.`
    or `..`, else None."""
    if not value or value in (".", ".."):
        return None
    return value if _SAFE_TOKEN.fullmatch(value) else None


def session_id(environ: Mapping[str, str]) -> str | None:
    """The harness's session ID (CLAUDE_CODE_SESSION_ID) when it is a safe
    token, else None."""
    return _safe_token(environ.get("CLAUDE_CODE_SESSION_ID"))


def _job_id(environ: Mapping[str, str]) -> str | None:
    job_dir = environ.get("CLAUDE_JOB_DIR", "")
    return _safe_token(os.path.basename(job_dir.rstrip("/")))


def derive_actor(environ: Mapping[str, str]) -> str:
    """The actor string for the session described by `environ`; the module
    docstring is the contract."""
    session = session_id(environ)
    job_id = _job_id(environ)
    if session is not None:
        return (JOB_PREFIX if job_id is not None else SESSION_PREFIX) + session
    if job_id is not None:
        return JOB_PREFIX + job_id
    user = _safe_token(environ.get("USER"))
    return ATTENDED_PREFIX + (user if user is not None else UNKNOWN_USER)
