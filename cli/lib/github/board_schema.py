"""The ProjectV2 board a repo's Tracker Schema asks for: its fields and
options, a board's conformance to them, and the plan that brings a board
there.

The `Status` options are exactly the repo's Issue States and the
`Priority` options exactly its Issue Priorities, in the schema's order,
each coloured from the schema. The field names, `Size` and its options,
and `Last Triaged` are GitHub bindings held in lib.schema. Nothing here
fails for a name it has not seen: every state and priority name comes
from the repo's `TRACKER.md` at run time.

A board option takes one of GitHub's eight named colours, not a hex value,
so `named_color` maps each schema colour to one of them by hue and
chroma (the rule is in its docstring and in docs/projects/ghw/design.md, "Colours").

Where a section the options come from cannot be read, that field's options
are unknown: conformance reports them unchecked, and no plan adds or
removes any. A usable section that lost entries gives the options that
were read; only a destructive write needs it complete, and that check is
the Verb's (RepoSchema.require_complete on `DesiredField.section`).

Changing a live single-select's options goes through updateProjectV2Field,
which replaces the whole option list. An option sent with its `id` keeps
its identity, so the items that hold it keep their value; an option left
out is removed, and every item that held it loses its value (GitHub's
GraphQL reference, ProjectV2SingleSelectFieldOptionInput). So a plan has
two lists per field: `additive`, every live option kept with its id plus
the declared ones the board lacks, and `final`, the declared options only,
which is sent only once no item holds an option it leaves out.
"""

from __future__ import annotations

import colorsys
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from lib import tracker_schema
from lib.github.repo_schema import RepoSchema
from lib.schema import (
    CANONICAL_FIELDS,
    DATE,
    FIELD_LAST_TRIAGED,
    FIELD_PRIORITY,
    FIELD_SIZE,
    FIELD_STATUS,
    SINGLE_SELECT,
    SIZE_OPTIONS,
)

# ProjectV2SingleSelectFieldOptionColor's eight values.
NAMED_COLORS = ("GRAY", "BLUE", "GREEN", "YELLOW", "ORANGE", "RED", "PINK",
                "PURPLE")
# The colour an option gets when it must be created and the schema gives
# it no usable colour.
NEUTRAL_COLOR = "GRAY"

# The hue, in degrees, each chromatic name stands for. The order breaks a
# tie between two equally near hues.
_REFERENCE_HUES = (
    ("RED", 350),
    ("ORANGE", 30),
    ("YELLOW", 52),
    ("GREEN", 125),
    ("BLUE", 220),
    ("PURPLE", 268),
    ("PINK", 330),
)
# Below this chroma (the spread between the largest and smallest of the red,
# green, and blue channels, as a fraction of full scale) a colour has too
# little hue to name, and is GRAY.
_GRAY_CHROMA = 0.15
_HEX = re.compile(r"[0-9A-Fa-f]{6}")

# The Tracker Schema section each schema-backed field's options come from.
SECTIONS = {
    FIELD_STATUS: tracker_schema.ISSUE_STATES,
    FIELD_PRIORITY: tracker_schema.ISSUE_PRIORITIES,
}

# Size is not in the Tracker Schema, so its options and colours are fixed.
_SIZE_COLORS = {"XS": "GRAY", "S": "BLUE", "M": "GREEN", "L": "YELLOW",
                "XL": "ORANGE"}


def named_color(hex_color: Optional[str]) -> Optional[str]:
    """The named board colour a six-hex-digit colour maps to, or None when
    there is no colour to map.

    The rule: a colour whose chroma is below 15 percent of full scale is
    GRAY; any other is the name whose reference hue is nearest its own hue
    around the colour wheel (RED 350, ORANGE 30, YELLOW 52, GREEN 125, BLUE
    220, PURPLE 268, PINK 330 degrees), the earlier in that list on a tie.
    Hue, because GitHub publishes no hex value for the names and draws each
    in different shades by theme, so the hue is what a name means; chroma,
    because gray is the one name that means no hue. Lightness is not
    judged on its own, but chroma here is the absolute channel spread, not
    a fraction of the colour's brightness, so a very pale or very dark
    tint is GRAY whatever its hue (ffdddd and c2e0c6 are GRAY; e99695 is
    RED). The result is the nearest name by hue alone, not the name a
    person would call nearest."""
    if hex_color is None or not _HEX.fullmatch(hex_color):
        return None
    red, green, blue = (int(hex_color[index:index + 2], 16) / 255
                        for index in (0, 2, 4))
    if max(red, green, blue) - min(red, green, blue) < _GRAY_CHROMA:
        return "GRAY"
    hue = colorsys.rgb_to_hsv(red, green, blue)[0] * 360
    return min(_REFERENCE_HUES, key=lambda entry: _arc(hue, entry[1]))[0]


@dataclass(frozen=True)
class DesiredOption:
    name: str
    color: Optional[str]  # a named colour, or None where the schema gives none


@dataclass(frozen=True)
class DesiredField:
    """One field the board should carry. `options` is None when the schema
    section it comes from cannot be read, so the options are unknown, and
    empty for a field that is not a single-select. `section` is that
    Tracker Schema section, or None for a field the schema does not
    decide."""

    name: str
    data_type: str
    options: Optional[Tuple[DesiredOption, ...]]
    section: Optional[str] = None


def desired_fields(loaded: RepoSchema) -> Tuple[DesiredField, ...]:
    """The fields `loaded`'s Tracker Schema asks for, in CANONICAL_FIELDS
    order."""
    states = loaded.section(tracker_schema.ISSUE_STATES)
    priorities = loaded.section(tracker_schema.ISSUE_PRIORITIES)
    by_name = {
        FIELD_PRIORITY: DesiredField(
            FIELD_PRIORITY, SINGLE_SELECT, _options(priorities),
            SECTIONS[FIELD_PRIORITY]),
        FIELD_STATUS: DesiredField(
            FIELD_STATUS, SINGLE_SELECT, _options(states),
            SECTIONS[FIELD_STATUS]),
        FIELD_SIZE: DesiredField(
            FIELD_SIZE, SINGLE_SELECT,
            tuple(DesiredOption(name, _SIZE_COLORS[name])
                  for name in SIZE_OPTIONS)),
        FIELD_LAST_TRIAGED: DesiredField(FIELD_LAST_TRIAGED, DATE, ()),
    }
    return tuple(by_name[name] for name in CANONICAL_FIELDS)


def evaluate_conformance(board: dict,
                         fields: Sequence[DesiredField]) -> dict:
    """Judge one board against the fields its repo's Tracker Schema asks
    for. Advisory; never mutates.

    `board` is a lib.github.boards board dict. Returns:

        {"conforms": True | False | None, "gaps": [...],
         "tolerated_gaps": [...], "unchecked": [...],
         "extra_options": [...], "color_drift": [...]}

    `gaps` are the differences: an absent field, a field of the wrong data
    type, two options of one name, a declared option the board lacks, an
    option the schema does not declare, and options out of the schema's
    order. A missing `Size` is
    the one tolerated gap. `unchecked` names a field whose options could
    not be judged because the schema section they come from cannot be
    read. `extra_options` lists options beyond Size's fixed set, which are
    advisory, since Size is not a schema fact. `color_drift` lists options
    whose colour differs from the one the schema's colour maps to; it
    never clears `conforms`. `conforms` is False on any gap, None when
    nothing was found wrong but something went unchecked, and True
    otherwise.
    """
    gaps, tolerated, unchecked, extra, drift = [], [], [], [], []
    for spec in fields:
        live = board["fields"].get(spec.name)
        if live is None:
            message = f"field {spec.name!r} is missing"
            (tolerated if spec.name == FIELD_SIZE else gaps).append(message)
            continue
        if live["data_type"] != spec.data_type:
            gaps.append(f"field {spec.name!r} is {live['data_type']}, not "
                        f"{spec.data_type}")
            continue
        if spec.data_type != SINGLE_SELECT:
            continue
        if spec.options is None:
            unchecked.append(
                f"field {spec.name!r}: options not checked, since the "
                f"Tracker Schema's {spec.section} cannot be read"
            )
            continue
        declared = [option.name for option in spec.options]
        present = live_names(live)
        doubled = sorted({name for name in present if present.count(name) > 1})
        if doubled:
            gaps.append(f"field {spec.name!r} holds more than one option "
                        f"named: {', '.join(doubled)}")
        present = list(dict.fromkeys(present))
        missing = [name for name in declared if name not in present]
        if missing:
            gaps.append(f"field {spec.name!r} is missing options: "
                        f"{', '.join(missing)}")
        undeclared = [name for name in present if name not in declared]
        if spec.section is None:
            if undeclared:
                extra.append(f"field {spec.name!r} also carries: "
                             f"{', '.join(undeclared)}")
            continue
        if undeclared:
            gaps.append(f"field {spec.name!r} carries options the Tracker "
                        f"Schema does not declare: {', '.join(undeclared)}")
        if ([name for name in present if name in declared]
                != [name for name in declared if name in present]):
            gaps.append(f"field {spec.name!r} has its options out of the "
                        "Tracker Schema's order")
        colors = _live_colors(live)
        for option in spec.options:
            now = colors.get(option.name)
            if option.color is not None and now is not None and now != option.color:
                drift.append(f"field {spec.name!r} option {option.name!r} is "
                             f"{now}; the Tracker Schema's colour maps to "
                             f"{option.color}")
    conforms = False if gaps else (None if unchecked else True)
    return {"conforms": conforms, "gaps": gaps, "tolerated_gaps": tolerated,
            "unchecked": unchecked, "extra_options": extra,
            "color_drift": drift}


def fields_to_create(board: dict, fields: Sequence[DesiredField], *,
                     new_board: bool) -> List[DesiredField]:
    """The fields ghw-board-sync should create on `board`, in order.

    On an existing board `Size` is left out (reported instead); on a freshly
    created board it is included. A single-select whose options are
    unknown, or would be empty, is left out too, since GitHub creates no
    single-select without options; conformance reports it. A field that
    exists is never here: its options are `plan_field`'s."""
    return [
        spec for spec in fields
        if spec.name not in board["fields"]
        and (new_board or spec.name != FIELD_SIZE)
        and (spec.data_type != SINGLE_SELECT or spec.options)
    ]


def creation_options(spec: DesiredField) -> List[Dict[str, str]]:
    """A new field's options, as the [{"name", "color", "description"}]
    list the ProjectV2 mutations take: the declared options in order, each
    in its colour or NEUTRAL_COLOR. Descriptions are empty: what a state or
    priority means is the Tracker Schema's, and copying it into option
    help text would make a second source of truth."""
    return [
        {"name": option.name, "color": option.color or NEUTRAL_COLOR,
         "description": ""}
        for option in spec.options or ()
    ]


@dataclass
class FieldPlan:
    """What it takes to bring one schema-backed field's options to the
    schema.

    `add` are declared options the board lacks; `rename` [{"from", "to"}]
    live options that differ from a declared one only in case or
    surrounding whitespace, renamed in place by id; `remove` the names of
    the live options no declared option claims (a second option of a
    declared name included), and `removed` the same as [{"id", "name"}];
    `recolor` [{"option", "from", "to"}]; `reorder` whether the declared
    options are out of order. `additive` is the option list for the write
    that adds, renames, recolours, and reorders while removing nothing
    (every live option, with its id), or None when that write would change
    nothing. `final` is the list with the removals made, the declared
    options only. Every entry is {"name", "color", "description"}, with
    "id" for a live option."""

    field: str
    field_id: str
    section: str
    add: List[str] = field(default_factory=list)
    rename: List[dict] = field(default_factory=list)
    remove: List[str] = field(default_factory=list)
    removed: List[dict] = field(default_factory=list)
    recolor: List[dict] = field(default_factory=list)
    reorder: bool = False
    additive: Optional[List[dict]] = None
    final: List[dict] = field(default_factory=list)

    @property
    def destructive(self) -> bool:
        return bool(self.removed)

    def summary(self) -> dict:
        return {"field": self.field, "add": list(self.add),
                "rename": list(self.rename), "remove": list(self.remove),
                "recolor": list(self.recolor), "reorder": self.reorder}


def plan_field(spec: DesiredField, live: Optional[dict]) -> Optional[FieldPlan]:
    """The plan for one field, or None when there is nothing to plan: the
    field is not schema-backed, its options are unknown, or the board has
    no single-select of that name (fields_to_create and conformance cover
    those).

    `live` is the board dict's entry for the field, with its
    `option_details` [{"id", "name", "color", "description"}] in board
    order. A declared option keeps its live colour where the schema gives
    none, and every live option keeps its description.

    Live options are matched to declared ones by id, never collapsed by
    name: each declared option claims the first unclaimed live option of
    its exact name, then, failing that, the first whose name differs only
    in case or surrounding whitespace (renamed in place, so no value
    moves). Every live option left unclaimed, a second option of a
    declared name included, stays in `additive` with its id and is to be
    emptied and removed by a migration like any other."""
    if (spec.section is None or spec.options is None or live is None
            or live["data_type"] != SINGLE_SELECT):
        return None
    details = list(live.get("option_details") or ())
    plan = FieldPlan(spec.name, live["id"], spec.section)
    claims: Dict[str, dict] = {}
    for loose in (False, True):
        for option in spec.options:
            if option.name in claims:
                continue
            taken = {entry["id"] for entry in claims.values()}
            current = next(
                (entry for entry in details if entry["id"] not in taken
                 and (_fold(entry["name"]) == _fold(option.name) if loose
                      else entry["name"] == option.name)),
                None)
            if current is not None:
                claims[option.name] = current
    kept = []
    for option in spec.options:
        current = claims.get(option.name)
        if current is None:
            plan.add.append(option.name)
            kept.append({"name": option.name,
                         "color": option.color or NEUTRAL_COLOR,
                         "description": ""})
            continue
        if current["name"] != option.name:
            plan.rename.append({"from": current["name"], "to": option.name})
        color = option.color or current["color"]
        if color != current["color"]:
            plan.recolor.append({"option": option.name,
                                 "from": current["color"], "to": color})
        kept.append({"id": current["id"], "name": option.name, "color": color,
                     "description": current.get("description") or ""})
    claimed = {entry["id"] for entry in claims.values()}
    undeclared = [entry for entry in details if entry["id"] not in claimed]
    plan.remove = [entry["name"] for entry in undeclared]
    plan.removed = [{"id": entry["id"], "name": entry["name"]}
                    for entry in undeclared]
    live_order = [entry["id"] for entry in details if entry["id"] in claimed]
    plan.reorder = live_order != [claims[option.name]["id"]
                                  for option in spec.options
                                  if option.name in claims]
    plan.final = kept
    additive = kept + [
        {"id": entry["id"], "name": entry["name"], "color": entry["color"],
         "description": entry.get("description") or ""}
        for entry in undeclared
    ]
    if _shape(additive) != _shape(details):
        plan.additive = additive
    return plan


def plan_moves(plan: FieldPlan, live: dict, items: Sequence[dict],
               moves: Dict[str, str],
               states: Sequence[tracker_schema.IssueState] = ()) -> List[dict]:
    """Where every item on an option `plan` removes would move.

    `items` is lib.github.boards.fetch_board_items output; `moves` maps an
    option being removed to the declared option its items move to, as the
    caller named it. Without a named move, an item on a second option of a
    declared name moves to the declared one ("same name"); otherwise an
    item on a removed `Status` option moves to the one declared state
    whose open flag matches its issue or pull request (open, or closed or
    merged), when exactly one does; `states` are the declared Issue
    States. With the default schema that sends a closed issue on `Done` or
    `Rejected` to its one closed state, `Closed`. Anything else has no
    target and needs a named move.

    Returns, per removed option in board order, {"option", "option_id",
    "items": [{"item_id", "type", "number", "title", "url", "state",
    "archived", "to", "by"}]}, where `to` is the target option or None and
    `by` says which rule chose it ("named", "same name", or "issue
    state", or None)."""
    declared = {_fold(entry["name"]): entry["name"] for entry in plan.final}
    result = []
    for removed in plan.removed:
        name = removed["name"]
        moved = []
        for item in items:
            if item["values"].get(plan.field_id) != removed["id"]:
                continue
            target, by = moves.get(name), "named"
            if target is None:
                target, by = declared.get(_fold(name)), "same name"
            if target is None:
                target = (_state_for(item, states)
                          if plan.field == FIELD_STATUS else None)
                by = "issue state" if target is not None else None
            moved.append({**_item_summary(item), "to": target, "by": by})
        result.append({"option": name, "option_id": removed["id"],
                       "items": moved})
    return result


def unmoved(migration: Sequence[dict]) -> List[dict]:
    """The items in a `plan_moves` result with no target."""
    return [item for entry in migration for item in entry["items"]
            if item["to"] is None]


def _state_for(item: dict,
               states: Sequence[tracker_schema.IssueState]) -> Optional[str]:
    """The one declared state whose open flag matches the item's issue or
    pull request, or None when none or several do, or the item has no
    open or closed state (a draft)."""
    is_open = {"OPEN": True, "CLOSED": False, "MERGED": False}.get(
        item["content"].get("state"))
    if is_open is None:
        return None
    matching = [state.name for state in states if state.open == is_open]
    return matching[0] if len(matching) == 1 else None


def _item_summary(item: dict) -> dict:
    content = item["content"]
    return {"item_id": item["item_id"], "type": content.get("type"),
            "number": content.get("number"), "title": content.get("title"),
            "url": content.get("url"), "state": content.get("state"),
            "archived": item.get("archived", False)}


def _options(entries) -> Optional[Tuple[DesiredOption, ...]]:
    if entries is None:
        return None
    return tuple(DesiredOption(entry.name, named_color(entry.color))
                 for entry in entries)


def _fold(name: str) -> str:
    """A name as compared for a rename: case and surrounding whitespace
    ignored."""
    return name.strip().casefold()


def live_names(live: Optional[dict]) -> List[str]:
    """Every live option's name on a field in board order, a repeated name
    repeated, or [] for no field. The name-to-id map would collapse two
    options of one name, so the detailed list is read where the board dict
    has it."""
    if live is None:
        return []
    details = live.get("option_details")
    if details is not None:
        return [entry["name"] for entry in details]
    return list(live["options"])


def live_option_ids(live: Optional[dict]) -> set:
    """Every live option id on a field, read from the detailed list where
    the board dict has it, so two options of one name both count."""
    if live is None:
        return set()
    details = live.get("option_details")
    if details is not None:
        return {entry["id"] for entry in details}
    return set(live.get("options", {}).values())


def _live_colors(live: dict) -> Dict[str, str]:
    return {entry["name"]: entry["color"]
            for entry in live.get("option_details") or ()}


def _shape(options: Sequence[dict]) -> List[tuple]:
    """What an option list sets, for telling whether a write would change
    anything: each option's identity, name, and colour, in order."""
    return [(entry.get("id"), entry["name"], entry["color"]) for entry in options]


def _arc(first: float, second: float) -> float:
    """The shorter way around the colour wheel between two hues."""
    difference = abs(first - second) % 360
    return min(difference, 360 - difference)
