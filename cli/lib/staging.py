"""Staged-file path validation: free text reaches a wrapper only as a file
the agent wrote into its own staging directory, never inline.

Every wrapper that takes a file-path argument -- <body-file>, <comment-file>,
or ghw-label-sync's <schema-file> -- accepts only paths inside the agent's own
staging directories:

    /tmp/claude/...
    ~/.claude/jobs/<job-id>/tmp/...

Anything else is refused with exit 2. Rationale: an allowlisted write wrapper
that will read an arbitrary path is a promptless exfiltration channel -- the
Read tool's deny rules do not reach a wrapper subprocess's own file reads.
Restricted to the staging directories, a wrapper can never read anything the
agent could not already read, and every staged file first passes through a
visible, permission-mediated Write.

`description` only names the argument in error messages ("body file", "schema
file"); the policy itself is identical for every file a wrapper reads.
"""

from __future__ import annotations

import sys
from pathlib import Path


class StagingPathError(Exception):
    """Raised when a staged-file path violates the staging-directory policy."""


def validate_staging_path(
    path: str,
    *,
    description: str = "body file",
    tmp_root_for_testing: Path | None = None,
    jobs_root_for_testing: Path | None = None,
) -> Path:
    """Validate `path` against the staging-directory policy.

    Returns the fully resolved path of an existing regular file inside one of
    the staging directories. Raises StagingPathError for anything else: a
    missing file, a non-file, a path outside the staging directories, or a
    symlink that escapes them.

    The `*_for_testing` roots substitute the policy's directory roots in unit
    tests; production callers must never pass them.
    """
    # Resolve fully (symlinks included) before checking, so a symlink planted
    # inside a staging directory cannot smuggle in an outside file.
    try:
        resolved = Path(path).expanduser().resolve(strict=True)
    except OSError:
        raise StagingPathError(f"refusing {description} {path!r}: file does not exist")
    if not resolved.is_file():
        raise StagingPathError(f"refusing {description} {path!r}: not a regular file")

    # /tmp is a symlink on macOS, so the roots get the same resolution.
    tmp_root = (tmp_root_for_testing or Path("/tmp/claude")).resolve()
    if resolved.is_relative_to(tmp_root):
        return resolved

    jobs_root = (jobs_root_for_testing or Path.home() / ".claude" / "jobs").resolve()
    if resolved.is_relative_to(jobs_root):
        # Only a job's tmp/ subtree is staging: ~/.claude/jobs/<job-id>/tmp/...
        # The rest of a job directory (transcripts, etc.) is off-limits.
        relative_parts = resolved.relative_to(jobs_root).parts
        if len(relative_parts) >= 3 and relative_parts[1] == "tmp":
            return resolved

    raise StagingPathError(
        f"refusing {description} {path!r}: outside the staging directories"
    )


def resolve_staging_path(path: str, *, description: str = "body file") -> Path:
    """Validate `path` like validate_staging_path(), exiting 2 on refusal.

    The exit path prints a self-correction hint: where staging files belong
    and to type the literal job path rather than $CLAUDE_JOB_DIR (which the
    harness blocks as shell expansion).
    """
    try:
        return validate_staging_path(path, description=description)
    except StagingPathError as error:
        print(
            f"{error}\n"
            f"{description.capitalize()}s must live in your own staging "
            "directories: /tmp/claude/ or ~/.claude/jobs/<job-id>/tmp/ (type the "
            "literal job path, not $CLAUDE_JOB_DIR). Write the file there first, "
            "then re-run.",
            file=sys.stderr,
        )
        sys.exit(2)


def read_staged_body(path: str, *, description: str = "body file") -> str:
    """Validate `path` like resolve_staging_path(), then return the file's text.

    A file that is not valid UTF-8, or that cannot be read, is refused with
    exit 2 like any other unusable staged file.
    """
    resolved = resolve_staging_path(path, description=description)
    return read_body(resolved, description=description)


def read_body(resolved: Path, *, description: str = "body file") -> str:
    """Read an already-validated staging path (a resolve_staging_path()
    result) with the same refusal behavior as read_staged_body() -- for
    callers that need both the path and the text without validating
    twice."""
    try:
        return resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(
            f"refusing {description} {str(resolved)!r}: not valid UTF-8. "
            "Re-write it as plain UTF-8 text, then re-run.",
            file=sys.stderr,
        )
        sys.exit(2)
    except OSError as error:
        # E.g. deleted or chmod'd between validation and the read.
        print(
            f"refusing {description} {str(resolved)!r}: unreadable ({error})",
            file=sys.stderr,
        )
        sys.exit(2)
