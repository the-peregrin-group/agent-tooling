"""The session actor: who is executing a wrapper, derived from the environment.

`derive_actor(environ)` returns one of two shapes, never blank:

    claude-job-<job-id>   CLAUDE_JOB_DIR is set and its basename is a safe
                          token; <job-id> is that basename.
    attended-<user>       otherwise; <user> is USER when it is a safe token,
                          else the literal `unknown`.

Why these two: the Claude Code harness sets CLAUDE_JOB_DIR for
background-job sessions (`~/.claude/jobs/<job-id>`), so a job-derived actor
is the session's own identity, and it travels with every process the job
spawns. The attended fallback is deliberately a different shape rather than
a guess at a job: a session whose job directory is missing shows up as
`attended-...` in the audit trail, visibly, instead of silently passing for
a job. A "safe token" is non-empty, only `[A-Za-z0-9._-]`, and not `.` or
`..`; anything else is treated as absent, so the actor can be spliced into a
git trailer or an environment variable without escaping.

The caller passes the mapping (normally `os.environ`); this module never
reads the process environment itself, which keeps it testable and makes
every caller's source of identity explicit.

Consumers: `bdw` (the Beads shim) and `gitw-commit` (the `Executed-By:`
trailer). See docs/adr/0001-beads-identity.md.
"""

from __future__ import annotations

import os
import re
from typing import Mapping

# Used with fullmatch: `$` would also match before a final newline.
_SAFE_TOKEN = re.compile(r"[A-Za-z0-9._-]+")

JOB_PREFIX = "claude-job-"
ATTENDED_PREFIX = "attended-"
UNKNOWN_USER = "unknown"


def _safe_token(value: str | None) -> str | None:
    """`value` if it is a non-empty `[A-Za-z0-9._-]` token other than `.`
    or `..`, else None."""
    if not value or value in (".", ".."):
        return None
    return value if _SAFE_TOKEN.fullmatch(value) else None


def derive_actor(environ: Mapping[str, str]) -> str:
    """The actor string for the session described by `environ`; the module
    docstring is the contract."""
    job_dir = environ.get("CLAUDE_JOB_DIR", "")
    job_id = _safe_token(os.path.basename(job_dir.rstrip("/")))
    if job_id is not None:
        return JOB_PREFIX + job_id
    user = _safe_token(environ.get("USER"))
    return ATTENDED_PREFIX + (user if user is not None else UNKNOWN_USER)
