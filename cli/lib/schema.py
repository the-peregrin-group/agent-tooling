"""The single home for the shared GitHub-ecosystem schema constants.

Both the ghw-* wrappers and the rebased triage-* wrappers import these;
nothing redeclares them. Sources of record before consolidation here:
setup-github-issues SKILL.md (labels), triage-issues SKILL.md (states).
"""

from __future__ import annotations

# --- Labels ------------------------------------------------------------------

# The five canonical type labels; every issue carries exactly one.
TYPE_LABELS: dict[str, dict[str, str]] = {
    "feature": {
        "color": "a2eeef",
        "description": "New feature, system, or capability",
    },
    "improvement": {
        "color": "0075ca",
        "description": "Enhancement or refinement of existing functionality",
    },
    "bug": {
        "color": "d73a4a",
        "description": "Something is broken or performs incorrectly",
    },
    "debt": {
        "color": "fbca04",
        "description": "Code quality, refactoring, documentation",
    },
    "meta": {
        "color": "7057ff",
        "description": "Design documents, planning artifacts, and non-code project work",
    },
}

# Priority-as-labels regime (repos with no linked board only). On board-field
# repos these exist as Priority option names instead, with the same meanings.
PRIORITY_LABELS: dict[str, dict[str, str]] = {
    "P0": {"color": "b60205", "description": "Drop-everything and address now"},
    "P1": {"color": "d93f0b", "description": "Most important non-emergency work"},
    "P2": {"color": "fbca04", "description": "Standard backlog work"},
    "P3": {"color": "0e8a16", "description": "Nice-to-have; opportunistic"},
}

AREA_LABEL_PREFIX = "area:"
AREA_LABEL_COLOR = "bfdadc"

# The unprefixed scope-label family setup-github-issues defines for repos
# spanning several sites, environments, or deployment targets. Members are
# repo-specific (they come from ghw-label-sync's schema file); only the family
# default color is shared.
SCOPE_LABEL_COLOR = "c5def5"

# --- Canonical board schema --------------------------------------------------

FIELD_STATUS = "Status"
FIELD_PRIORITY = "Priority"
FIELD_SIZE = "Size"
FIELD_LAST_TRIAGED = "Last Triaged"

# The ProjectV2 field data types this ecosystem uses (values of the API's
# ProjectV2CustomFieldType enum, and of the dataType every field reports).
SINGLE_SELECT = "SINGLE_SELECT"
DATE = "DATE"

# Size is canonical on new boards; on existing boards a missing Size is
# reported, never created (matches triage's "not used" tolerance).
CANONICAL_FIELDS = (FIELD_PRIORITY, FIELD_STATUS, FIELD_SIZE, FIELD_LAST_TRIAGED)

# The eight canonical Status states, in graph order. Casing is exact and
# deliberately mixed: title case for the Needs-* queue states, sentence case
# for In progress / In review.
STATUS_STATES: tuple[str, ...] = (
    "Needs Triage",
    "Needs Scope",
    "Needs Eng Design",
    "Needs Impl",
    "In progress",
    "In review",
    "Done",
    "Rejected",
)

TERMINAL_STATES = frozenset({"Done", "Rejected"})

PRIORITY_OPTIONS: tuple[str, ...] = ("P0", "P1", "P2", "P3")
SIZE_OPTIONS: tuple[str, ...] = ("XS", "S", "M", "L", "XL")
