"""Leaf validators for the gitw positional grammar.

Parsing itself stays hand-rolled in each executable (the same deliberate
departure from argparse as the ghw/fjw verbs); these are the per-argument
checks every gitw verb would otherwise repeat. All three tokens are allowlist material -- a rule's
literal prefix is the grant -- so the charsets are deliberately tight.
"""

from __future__ import annotations

import re

from lib import arguments as shared

# Repo labels are the short stable literals allowlist rules pin
# (`Bash(gitw-commit <label> <prefix> *)`). Single token, lowercase, no
# slash: the slash is the branch-prefix terminator, and keeping it out of
# labels keeps the two token kinds visually unmistakable in a rule.
_LABEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

# Branch names (the part after the prefix): a conservative slice of what
# git permits. No slash -- single-level is the prefix grammar's job, and a
# slash in the name would nest beyond it.
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

# Full branch names (gitw-integrate's <base-branch>): slashes allowed,
# same conservative charset otherwise.
_BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")

# First components that make a multi-level branch name collide with git's
# own ref namespaces when written as a short name. Compared casefolded, so
# "head" also catches HEAD.
_REF_NAMESPACES = ("refs", "heads", "remotes", "tags", "head")


def is_valid_label(label: str) -> bool:
    """True for a plausible roster label: lowercase alphanumerics plus
    dot/underscore/hyphen, never leading with punctuation."""
    return bool(_LABEL_PATTERN.match(label))


# The branch-prefix grammar lives in lib.arguments, shared with fjw.
NO_BRANCH_PREFIX = shared.NO_BRANCH_PREFIX
is_valid_branch_prefix = shared.is_valid_branch_prefix
branch_matches_prefix = shared.branch_matches_prefix
prefixed_branch = shared.prefixed_branch


def is_valid_branch_name(name: str) -> bool:
    """True for a safe branch-name tail: alphanumerics plus
    dot/underscore/hyphen, no leading punctuation, and none of the
    ref-syntax traps ('..', a trailing '.', a '.lock' suffix) git itself
    rejects -- caught here so they surface as usage errors (exit 2), not
    as a misclassified git failure downstream."""
    if not _NAME_PATTERN.match(name):
        return False
    return (".." not in name and not name.endswith(".")
            and not name.endswith(".lock"))


def is_valid_name_for_prefix(prefix: str, name: str) -> bool:
    """True for a name tail valid under `prefix`: single-level under a
    real prefix, but a full branch name, slashes allowed, under
    NO_BRANCH_PREFIX, since there the name is the whole branch."""
    if prefix == NO_BRANCH_PREFIX:
        return is_valid_branch(name)
    return is_valid_branch_name(name)


def shadows_ref_namespace(branch: str) -> bool:
    """True when a full branch name's first level is one of git's ref
    namespaces ('tags/v1', 'refs/x'): as a short name it would collide
    with git's own refs. Judged on the composed name, so a real prefix
    like 'tags/' is caught exactly as the bare slash is."""
    head, _, tail = branch.partition("/")
    return bool(tail) and head.casefold() in _REF_NAMESPACES


def is_valid_branch(branch: str) -> bool:
    """True for a safe full branch name (e.g. gitw-integrate's base):
    like is_valid_branch_name but with slash-separated levels allowed."""
    if not _BRANCH_PATTERN.match(branch):
        return False
    if ".." in branch or "//" in branch:
        return False
    return not branch.endswith(("/", ".lock", "."))
