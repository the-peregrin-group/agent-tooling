"""The canonical board schema constants the ghw board Verbs still hold.

Labels are not here: their kinds, priorities, axes, names, descriptions,
and colours come from the repo's Tracker Schema (`TRACKER.md`, read through
lib.github.repo_schema). The board's fields and options below are the last
values ghw holds of its own; moving them onto the Tracker Schema too is
agent-tooling-u9n.21 (ghw board Verbs follow the schema).
"""

from __future__ import annotations

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
