"""The board field names and the Size options, the GitHub bindings the ghw
board Verbs hold of their own.

Everything else a board holds comes from the repo's Tracker Schema
(`TRACKER.md`, read through lib.github.repo_schema): the `Status` options
are its Issue States and the `Priority` options its Issue Priorities, with
their order and colours (lib.github.board_schema). The field names are not
schema facts: the schema speaks only of "the board's status field", and
GitHub needs a name for it. Size is not in the schema at all, so its
options stay here.
"""

from __future__ import annotations

# --- Board field names ---------------------------------------------------------

FIELD_STATUS = "Status"
FIELD_PRIORITY = "Priority"
FIELD_SIZE = "Size"
FIELD_LAST_TRIAGED = "Last Triaged"

# The ProjectV2 field data types this ecosystem uses (values of the API's
# ProjectV2CustomFieldType enum, and of the dataType every field reports).
SINGLE_SELECT = "SINGLE_SELECT"
DATE = "DATE"

# Size is provisioned on new boards; on existing boards a missing Size is
# reported, never created (matches triage's "not used" tolerance).
CANONICAL_FIELDS = (FIELD_PRIORITY, FIELD_STATUS, FIELD_SIZE, FIELD_LAST_TRIAGED)

SIZE_OPTIONS: tuple[str, ...] = ("XS", "S", "M", "L", "XL")
