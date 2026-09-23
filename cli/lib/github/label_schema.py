"""ghw-label-sync's desired-state model: schema-file parsing and the label diff.

The canonical type labels (and, for repos in the P0-P3 label regime, the
priority labels) come from lib.schema and are never redeclared in a schema
file. The file supplies only the two repo-specific families
setup-github-issues defines: the prefixed `area:` family and the unprefixed
multi-site scope family.

File shape (JSON, never YAML -- the wrappers are stdlib-only):

    {
      "priority_labels": false,
      "area": [
        {"name": "core", "description": "Core engine and runtime"},
        {"name": "docs", "description": "Documentation"}
      ],
      "scope": [
        {"name": "site-a", "description": "The Site A deployment",
         "color": "c5def5"}
      ]
    }

  - `area` names are written bare; the wrapper adds the `area:` prefix, so a
    name that already carries it is a usage error rather than a silent
    `area:area:core`.
  - `color` is optional per entry (family defaults apply) and is 6 hex digits,
    with or without a leading `#`.
  - `description` is required: a label whose meaning is not written down stops
    being a shared contract.
  - `priority_labels` selects the P0-P3 label regime for repos with no linked
    board. It defaults to false, and it exists because the desired state is
    authoritative for deletion: without it, apply-delete on a label-regime repo
    would strip the very P0-P3 labels that repo tracks priority with.

Everything the file does not declare is a deletion candidate, which is what
makes the sync declarative -- including GitHub's nine stock labels.
"""

from __future__ import annotations

import json
import re
from typing import Iterable

from lib.schema import (
    AREA_LABEL_COLOR,
    AREA_LABEL_PREFIX,
    PRIORITY_LABELS,
    SCOPE_LABEL_COLOR,
    TYPE_LABELS,
)

_COLOR_PATTERN = re.compile(r"^#?[0-9A-Fa-f]{6}$")
_FAMILY_KEYS = ("area", "scope")
_TOP_LEVEL_KEYS = (*_FAMILY_KEYS, "priority_labels")
_ENTRY_KEYS = ("name", "description", "color")


class SchemaFileError(Exception):
    """Raised when a schema file is unparseable or violates the file shape."""


def parse_schema(text: str) -> dict:
    """Parse a schema file's text into {"priority_labels", "area", "scope"}.

    Both families come back as lists of {"name", "description", "color"} with
    colors normalized and defaults filled in; `name` is still the bare,
    unprefixed name. Raises SchemaFileError, with a message an agent can
    self-correct from, for anything that is not the documented shape.
    """
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        # Position only, never the offending text: a schema file's content is
        # published to GitHub, so error output stays content-free by habit.
        raise SchemaFileError(
            f"schema file is not valid JSON (line {error.lineno}, column "
            f"{error.colno}): {error.msg}"
        )
    if not isinstance(document, dict):
        raise SchemaFileError(
            "schema file must be a JSON object with 'area' and optional "
            "'scope' / 'priority_labels' keys"
        )
    unknown = sorted(set(document) - set(_TOP_LEVEL_KEYS))
    if unknown:
        raise SchemaFileError(
            f"unknown top-level key(s): {', '.join(unknown)}. Allowed: "
            f"{', '.join(_TOP_LEVEL_KEYS)}"
        )
    priority_labels = document.get("priority_labels", False)
    if not isinstance(priority_labels, bool):
        raise SchemaFileError("'priority_labels' must be true or false")

    schema = {"priority_labels": priority_labels}
    for family in _FAMILY_KEYS:
        default_color = AREA_LABEL_COLOR if family == "area" else SCOPE_LABEL_COLOR
        schema[family] = _parse_family(document.get(family, []), family, default_color)
    if not schema["area"]:
        raise SchemaFileError(
            "'area' must declare at least one label: every issue carries an "
            "'area:' label, so a repo with none cannot pass ghw-issue-create"
        )
    _refuse_duplicate_names(schema)
    return schema


def desired_labels(schema: dict) -> dict[str, dict[str, str]]:
    """The full desired label registry: {name: {"color", "description"}}.

    Merges the shared canonical families (type labels always, priority labels
    when the schema selects the label regime) with the schema file's `area:`
    and scope families.
    """
    desired: dict[str, dict[str, str]] = {}
    for name, attributes in TYPE_LABELS.items():
        desired[name] = dict(attributes)
    if schema["priority_labels"]:
        for name, attributes in PRIORITY_LABELS.items():
            desired[name] = dict(attributes)
    for entry in schema["area"]:
        desired[AREA_LABEL_PREFIX + entry["name"]] = {
            "color": entry["color"], "description": entry["description"],
        }
    for entry in schema["scope"]:
        desired[entry["name"]] = {
            "color": entry["color"], "description": entry["description"],
        }
    return desired


def diff_labels(desired: dict[str, dict[str, str]],
                existing: Iterable[dict]) -> dict[str, list]:
    """Compare the desired registry against the repo's live one.

    `existing` is lib.boards.fetch_labels() output. Returns
    {"create": [{"name", "color", "description"}],
     "update": [{"name", "color", "description", "from": {"color", "description"}}],
     "delete": [name, ...], "unchanged": [name, ...],
     "case_mismatch": [{"live", "desired"}]}, each list sorted by name. A
    converged repo yields empty create/update/delete lists.

    Names match case-insensitively, because GitHub's label namespace is: a
    live `Bug` against a desired `bug` is the same label, and matching it
    exactly would plan a create the API then rejects as already-existing --
    an unrecoverable failure on every run. Such a pair is reported under
    `case_mismatch` and otherwise treated as matched; renaming it is a human
    act (this wrapper never renames). Updates carry the *live* spelling in
    `name`, since that is what a `gh label edit` has to target.
    """
    live = {
        label["name"].lower(): {
            "name": label["name"],
            "color": normalize_color(label.get("color")),
            "description": label.get("description") or "",
        }
        for label in existing
    }
    create, update, unchanged, case_mismatch = [], [], [], []
    for name in sorted(desired):
        wanted = {
            "color": normalize_color(desired[name]["color"]),
            "description": desired[name].get("description") or "",
        }
        current = live.get(name.lower())
        if current is None:
            create.append({"name": name, **wanted})
            continue
        if current["name"] != name:
            case_mismatch.append({"live": current["name"], "desired": name})
        attributes = {"color": current["color"],
                      "description": current["description"]}
        if attributes == wanted:
            unchanged.append(current["name"])
        else:
            update.append({"name": current["name"], **wanted, "from": attributes})
    undeclared = set(live) - {name.lower() for name in desired}
    return {
        "create": create,
        "update": update,
        "delete": sorted(live[key]["name"] for key in undeclared),
        "unchanged": unchanged,
        "case_mismatch": case_mismatch,
    }


def normalize_color(color: str | None) -> str:
    """A label color as 6 lowercase hex digits, with any leading '#' dropped.

    GitHub accepts '#a2eeef' and 'A2EEEF' on input and reports 'a2eeef', so
    normalizing both sides keeps a cosmetic difference from looking like drift.
    """
    return (color or "").lstrip("#").lower()


def _parse_family(value: object, family: str, default_color: str) -> list[dict]:
    """Validate and normalize one label family from the parsed document."""
    if not isinstance(value, list):
        raise SchemaFileError(
            f"'{family}' must be a list of "
            '{"name": ..., "description": ...} objects'
        )
    entries = []
    for position, raw in enumerate(value, start=1):
        entries.append(_parse_entry(raw, family, position, default_color))
    return entries


def _parse_entry(raw: object, family: str, position: int,
                 default_color: str) -> dict:
    """Validate and normalize one label entry; `position` names it in errors
    when its own name is unusable."""
    where = f"'{family}' entry {position}"
    if not isinstance(raw, dict):
        raise SchemaFileError(f'{where} must be an object, e.g. {{"name": '
                              '"core", "description": "Core engine"}')
    unknown = sorted(set(raw) - set(_ENTRY_KEYS))
    if unknown:
        raise SchemaFileError(
            f"{where} has unknown key(s): {', '.join(unknown)}. Allowed: "
            f"{', '.join(_ENTRY_KEYS)}"
        )
    name = raw.get("name")
    if not isinstance(name, str) or not name or name != name.strip():
        raise SchemaFileError(
            f"{where}: 'name' must be a non-empty string with no surrounding "
            "whitespace"
        )
    if "," in name:
        raise SchemaFileError(
            f"{where}: label names cannot contain a comma ({name!r}). "
            "ghw-issue-create and ghw-issue-edit attach labels through gh "
            "flags that split on commas, so this label could never be "
            "attached."
        )
    if name.startswith("-"):
        raise SchemaFileError(
            f"{where}: label names cannot start with '-' ({name!r}); it "
            "reaches gh as a flag-looking argument and fails confusingly"
        )
    if name.startswith(AREA_LABEL_PREFIX):
        bare = name[len(AREA_LABEL_PREFIX):]
        if family == "area":
            raise SchemaFileError(
                f"{where}: write the bare name ({bare!r}); ghw-label-sync adds "
                f"the {AREA_LABEL_PREFIX!r} prefix to 'area' entries"
            )
        raise SchemaFileError(
            f"{where}: scope labels carry no prefix; {name!r} belongs in the "
            f"'area' family as {bare!r}"
        )
    if name in TYPE_LABELS or name in PRIORITY_LABELS:
        raise SchemaFileError(
            f"{where}: {name!r} is a canonical label owned by the shared schema; "
            "remove it from the file (type labels are always synced, and "
            "P0-P3 come from \"priority_labels\": true)"
        )
    description = raw.get("description")
    if not isinstance(description, str) or not description.strip():
        raise SchemaFileError(f"{where} ({name}): 'description' is required")
    color = raw.get("color", default_color)
    if not isinstance(color, str) or not _COLOR_PATTERN.match(color):
        raise SchemaFileError(
            f"{where} ({name}): 'color' must be 6 hex digits, e.g. "
            f"{default_color!r}"
        )
    return {
        "name": name,
        "description": description,
        "color": normalize_color(color),
    }


def _refuse_duplicate_names(schema: dict) -> None:
    """Refuse a file that declares the same final label name twice, within a
    family or across the two."""
    seen: dict[str, str] = {}
    for family in _FAMILY_KEYS:
        prefix = AREA_LABEL_PREFIX if family == "area" else ""
        for entry in schema[family]:
            final = prefix + entry["name"]
            if final in seen:
                raise SchemaFileError(
                    f"label {final!r} is declared twice (in '{seen[final]}' and "
                    f"'{family}')"
                )
            seen[final] = family
