"""Leaf validators for the gitw positional grammar.

Parsing itself stays hand-rolled in each executable (the same deliberate
departure from argparse as the ghw/fjw verbs); these are the per-argument
checks every gitw verb would otherwise repeat. All three tokens are allowlist material -- a rule's
literal prefix is the grant -- so the charsets are deliberately tight.
"""

from __future__ import annotations

import re

# Repo labels are the short stable literals allowlist rules pin
# (`Bash(gitw-push <label> <prefix> *)`). Single token, lowercase, no
# slash: the slash is the branch-prefix terminator, and keeping it out of
# labels keeps the two token kinds visually unmistakable in a rule.
_LABEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

# Branch prefixes: lowercase, single-level,
# always ending in '/'. The trailing slash is the token boundary in
# space-star rules, preventing the fix/fix-2 prefix-leak class.
_PREFIX_PATTERN = re.compile(r"^[a-z][a-z0-9-]*/$")

# Branch names (the part after the prefix): a conservative slice of what
# git permits. No slash -- single-level is the prefix grammar's job, and a
# slash in the name would nest beyond it.
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

# Full branch names (gitw-integrate's <base-branch>): slashes allowed,
# same conservative charset otherwise.
_BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


def is_valid_label(label: str) -> bool:
    """True for a plausible roster label: lowercase alphanumerics plus
    dot/underscore/hyphen, never leading with punctuation."""
    return bool(_LABEL_PATTERN.match(label))


def is_valid_branch_prefix(prefix: str) -> bool:
    """True for a grammar-conforming branch prefix: lowercase, single
    level, trailing '/' included (e.g. 'fix/')."""
    return bool(_PREFIX_PATTERN.match(prefix))


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


def is_valid_branch(branch: str) -> bool:
    """True for a safe full branch name (e.g. gitw-integrate's base):
    like is_valid_branch_name but with slash-separated levels allowed."""
    if not _BRANCH_PATTERN.match(branch):
        return False
    if ".." in branch or "//" in branch:
        return False
    return not branch.endswith(("/", ".lock", "."))
