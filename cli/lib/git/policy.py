"""Machine-checkable local-file policy shared by the mutating gitw verbs.

The local-only patterns name files that must never be swept into history:
machine-local wiring and secrets. The wrapper layer is the second line of
defense -- repo hygiene says these files should be gitignored in the first
place -- so a staged set touching one refuses loudly (exit 4 upstream),
forcing a gitignore fix or a narrower pathspec.

Matching is per path *component* and case-folded: a directory named like
a pattern (.env/creds.json) hides its contents just as effectively as the
file itself, and the default APFS volume is case-insensitive, so `.ENV`
is `.env` on disk.

One exemption: exactly `.env.example` (case-folded) is committable --
it is the single sanctioned bootstrap-guide name, deliberately narrow
(`.env.sample` and `.env.template` still refuse). The exemption applies
to the FINAL path component only: a *directory* named `.env.example`
would otherwise smuggle its whole subtree past the guard. Broadening
the exemption is a design act, not a code tweak.
"""

from __future__ import annotations

import fnmatch

LOCAL_ONLY_PATTERNS = ("settings.local.json", ".env*")

# The single committable exception (see module docstring). Compared
# case-folded, like the patterns.
COMMITTABLE_EXCEPTION = ".env.example"


def _matching_pattern(path: str) -> str | None:
    components = path.rstrip("/").split("/")
    for position, component in enumerate(components):
        folded = component.lower()
        if folded == COMMITTABLE_EXCEPTION and position == len(components) - 1:
            continue  # the exemption is for the file itself, never a dir
        for pattern in LOCAL_ONLY_PATTERNS:
            if fnmatch.fnmatchcase(folded, pattern):
                return pattern
    return None


def is_local_only(path: str) -> bool:
    """True when any component of `path` matches a local-only pattern,
    case-folded -- except the sanctioned `.env.example`."""
    return _matching_pattern(path) is not None


def local_only_matches(paths) -> list:
    """The sorted, de-duplicated (path, matched-pattern) pairs from
    `paths` that the local-only policy refuses to let into history."""
    matches = {}
    for path in paths:
        pattern = _matching_pattern(path)
        if pattern is not None:
            matches[path] = pattern
    return sorted(matches.items())


def refusal_message(matches, remedy: str) -> str:
    """The loud, self-explanatory sweep refusal (exit 4 upstream): which
    path matched which pattern, why the policy exists, the one sanctioned
    exception, and the verb-specific `remedy` -- a complete sentence
    ending in a period, because the closing authority sentence is
    appended right after it. An agent hitting this cold should need zero
    archaeology."""
    listed = "; ".join(
        f"{path} (matches {pattern})" for path, pattern in matches
    )
    return (
        f"refusing to sweep local-only files into history: {listed}.\n"
        "By policy these names are machine-local wiring or secret-bearing "
        "and never enter history through gitw.\n"
        "The one sanctioned committable exception is '.env.example': "
        "a bootstrap-guide file must use exactly that "
        "name -- not .env.sample, not .env.template.\n"
        f"{remedy} Anything beyond that is the user's call, not yours."
    )
