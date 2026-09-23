"""Shared leaf validators for the wrappers' hand-rolled positional parsing.

Parsing itself stays hand-rolled in each executable (a deliberate departure
from argparse, which accepts flags intermixed with positionals and so cuts
against the rule "no scope-relevant flags after the positional block");
these are only the per-argument checks every wrapper would otherwise repeat.
"""

from __future__ import annotations

import re

# GitHub's actual charsets: owners are alphanumeric-and-hyphen (never leading
# with a hyphen), repo names allow dot/underscore/hyphen on top. Shape-only
# validation ("one slash, both halves non-empty") would admit ?, #, spaces,
# and .. -- and this value gets spliced into REST paths like
# repos/{repository}/pulls, so the charset is load-bearing (wrapper-internal
# validation is the only guard: settings rules never see these calls).
_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+$")


def is_valid_repository(repository: str) -> bool:
    """True for a plausible GitHub 'owner/name': the owner is alphanumerics
    and hyphens (never leading with a hyphen); the name is alphanumerics,
    dots, underscores, and hyphens.

    The path-traversal names '.' and '..' are excluded explicitly; dots inside
    a name ('a..b') are harmless and allowed.
    """
    if not _REPOSITORY_PATTERN.match(repository):
        return False
    return repository.split("/", 1)[1] not in (".", "..")


def parse_issue_number(value: str) -> int | None:
    """Parse an issue/PR/project number: a positive decimal integer, with an
    optional leading '#' tolerated. Returns None for anything else."""
    digits = value[1:] if value.startswith("#") else value
    # isdecimal(), not isdigit(): superscripts pass isdigit() but crash int().
    if not digits.isdecimal():
        return None
    number = int(digits)
    return number if number > 0 else None
