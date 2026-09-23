"""The canonical ProjectV2 board schema: conformance verdicts and provisioning.

One schema is baked in for every repo in the ecosystem -- `Priority` (P0-P3),
`Status` (the eight canonical triage states), `Size`, and `Last Triaged` --
whose names and option names all come from lib.schema. What this module adds
on top of them is presentation and policy: each option's display color, and
which shortfalls count against conformance.

Two consumers, deliberately asymmetric:
  - ghw-orient and ghw-board-sync *report* conformance. Drift on an existing
    field is never edited: replacing a live single-select's options can orphan
    values already assigned to items, so that stays a human decision.
  - ghw-board-sync *creates* absent fields. On an existing board `Size` is
    reported rather than created, matching triage's profile validator, which
    tolerates `Size` "not used" while hard-requiring `Last Triaged`; on a board
    ghw-board-sync just created, the full schema including `Size` is
    provisioned.

The verdict counts only what is *missing*. Options a human added beyond the
canonical set are reported separately and advisory: the wrappers only ever
write canonical option names, so a board carrying an extra `Blocked` state
still satisfies everything triage needs of it.
"""

from __future__ import annotations

from lib.schema import (
    CANONICAL_FIELDS,
    DATE,
    FIELD_LAST_TRIAGED,
    FIELD_PRIORITY,
    FIELD_SIZE,
    FIELD_STATUS,
    PRIORITY_OPTIONS,
    SINGLE_SELECT,
    SIZE_OPTIONS,
    STATUS_STATES,
)

# The canonical schema, in CANONICAL_FIELDS order. `options` is empty for
# fields that are not single-selects.
FIELD_SPECS: dict[str, dict] = {
    FIELD_PRIORITY: {"data_type": SINGLE_SELECT, "options": PRIORITY_OPTIONS},
    FIELD_STATUS: {"data_type": SINGLE_SELECT, "options": STATUS_STATES},
    FIELD_SIZE: {"data_type": SINGLE_SELECT, "options": SIZE_OPTIONS},
    FIELD_LAST_TRIAGED: {"data_type": DATE, "options": ()},
}

# Option colors, from ProjectV2SingleSelectFieldOptionColor's eight values.
# Presentation only -- the contract is the option *names* in lib.schema. The
# keys duplicate those names, so _check_option_colors() below fails at import
# if lib.schema ever renames one out from under this map.
_OPTION_COLORS: dict[str, dict[str, str]] = {
    FIELD_PRIORITY: {"P0": "RED", "P1": "ORANGE", "P2": "YELLOW", "P3": "GREEN"},
    FIELD_STATUS: {
        "Needs Triage": "RED",
        "Needs Scope": "ORANGE",
        "Needs Eng Design": "YELLOW",
        "Needs Impl": "BLUE",
        "In progress": "PURPLE",
        "In review": "PINK",
        "Done": "GREEN",
        "Rejected": "GRAY",
    },
    FIELD_SIZE: {"XS": "GRAY", "S": "BLUE", "M": "GREEN", "L": "YELLOW",
                 "XL": "ORANGE"},
}


def evaluate_conformance(board: dict) -> dict:
    """Judge one board against the canonical schema. Advisory; never mutates.

    `board` is a lib.boards board dict. Returns:

        {"conforms": bool, "gaps": [...], "tolerated_gaps": [...],
         "extra_options": [...]}

    `gaps` are the shortfalls: an absent field, a field of the wrong data
    type, or missing canonical options. A missing `Size` is the one tolerated
    gap -- triage runs fine without it -- so it is reported separately and does
    not clear `conforms`. `extra_options` lists human-authored options beyond
    the canonical set; they are informational and never clear `conforms`,
    since the wrappers only ever write canonical names.
    """
    gaps, tolerated, extra_options = [], [], []
    for field_name in CANONICAL_FIELDS:
        field = board["fields"].get(field_name)
        if field is None:
            message = f"field {field_name!r} is missing"
            (tolerated if field_name == FIELD_SIZE else gaps).append(message)
            continue
        field_gaps, field_extra = _field_findings(field_name, field)
        gaps.extend(field_gaps)
        extra_options.extend(field_extra)
    return {"conforms": not gaps, "gaps": gaps, "tolerated_gaps": tolerated,
            "extra_options": extra_options}


def fields_to_create(board: dict, *, new_board: bool) -> list[str]:
    """Which canonical fields ghw-board-sync should create on `board`.

    Absent canonical fields, in CANONICAL_FIELDS order. On an existing board
    `Size` is excluded (reported instead); on a freshly created board it is
    included. A field that exists but has drifted is never in this list --
    drift is reported, never edited.
    """
    return [
        field_name
        for field_name in CANONICAL_FIELDS
        if field_name not in board["fields"]
        and (new_board or field_name != FIELD_SIZE)
    ]


def single_select_options(field_name: str) -> list[dict[str, str]]:
    """The canonical options for one single-select field, as the
    [{"name", "color", "description"}] shape the ProjectV2 mutations take.

    Descriptions are deliberately empty: the states' meanings are defined by
    the triage-issues skill, and duplicating them into option help text would
    create a second source of truth. Raises KeyError for a name that is not in
    FIELD_SPECS; a field that is in FIELD_SPECS but is not a single-select
    yields an empty list.
    """
    colors = _OPTION_COLORS.get(field_name, {})
    return [
        {"name": option, "color": colors[option], "description": ""}
        for option in FIELD_SPECS[field_name]["options"]
    ]


def _field_findings(field_name: str, field: dict) -> tuple[list[str], list[str]]:
    """(gaps, extra_options) for one field that is present on the board.

    Gaps are a wrong data type or missing canonical options; extra options are
    reported apart from them because they do not make a board unusable.
    """
    specification = FIELD_SPECS[field_name]
    if field["data_type"] != specification["data_type"]:
        return [
            f"field {field_name!r} is {field['data_type']}, not "
            f"{specification['data_type']}"
        ], []
    if specification["data_type"] != SINGLE_SELECT:
        return [], []
    canonical = specification["options"]
    present = field["options"]
    gaps, extra_options = [], []
    missing = [option for option in canonical if option not in present]
    if missing:
        gaps.append(
            f"field {field_name!r} is missing options: {', '.join(missing)}"
        )
    extra = [option for option in present if option not in canonical]
    if extra:
        extra_options.append(
            f"field {field_name!r} also carries: {', '.join(extra)}"
        )
    return gaps, extra_options


def _check_option_colors() -> None:
    """Fail at import if _OPTION_COLORS has drifted from lib.schema.

    Its keys are copies of the canonical option names, and single_select_options
    indexes them directly, so a rename in lib.schema must not degrade quietly
    into a default color -- it has to stop the wrapper here, where the message
    says exactly what to fix.
    """
    for field_name, specification in FIELD_SPECS.items():
        if specification["data_type"] != SINGLE_SELECT:
            continue
        colors = _OPTION_COLORS.get(field_name, {})
        missing = [option for option in specification["options"]
                   if option not in colors]
        stale = [option for option in colors
                 if option not in specification["options"]]
        if missing or stale:
            raise RuntimeError(
                f"board_schema._OPTION_COLORS is out of step with lib.schema "
                f"for {field_name!r}: missing {missing}, stale {stale}"
            )


_check_option_colors()
