"""ghw-label-sync's desired-state model: the labels a repo's Tracker Schema
declares, and their diff against the repo's live labels.

The desired set is exactly what the schema declares, each label's name,
description, and colour taken from it:

  - every Issue Kind, as its Kind Label, since GitHub has no kind field
    ghw uses;
  - every Issue Priority, where the repo carries priority as labels (the
    `p-labels` priority regime, which ghw-orient reports from the board);
  - every label on every axis, its name written in full with the prefix;
  - every label on no axis.

A label named for an Issue State is declared by that state, so it is never
a deletion candidate, but the sync does not create one: where a forge with
no board records an Issue's state is still open (agent-tooling-vb2v). The
same holds for the priorities when the priority regime is unknown, and
when it is board-field but the board's Priority field does not hold every
declared priority, since only then is it verified that priority lives on
the board and not in the labels. A
declared name that gh cannot pass whole (labels.uncarriable_reason) is
neither created nor deleted, with a warning, and so is a live label with
such a name.

A section the reader could not use contributes nothing, and a label it
would have declared is not created. A section that is usable but
incomplete contributes what it has. Deletion is the one place either
matters: every live label the desired set lacks is a deletion candidate,
so a deletion is trusted only when every section the set derives from is
complete (`DesiredLabels.sections`, for RepoSchema.require_complete).

Where the schema's meaning or colour for a label is missing or bad, the
live value is left as it is, and a label that has to be created gets an
empty description or NEUTRAL_COLOR. GitHub refuses a label description over
DESCRIPTION_LIMIT characters, so a longer meaning is shortened to fit, the
same way on every run, so the sync still converges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from lib import tracker_schema
from lib.github import labels as label_contract
from lib.github.repo_schema import RepoSchema

# The priority regime that keeps priority on the board, not on labels.
BOARD_FIELD = "board-field"
# The regime that carries priority as labels.
P_LABELS = "p-labels"

# GitHub's own default label colour, for a label created without one.
NEUTRAL_COLOR = "ededed"
# The longest description GitHub accepts on a label.
DESCRIPTION_LIMIT = 100
_ELLIPSIS = "..."


@dataclass
class DesiredLabels:
    """The labels a sync makes exist, and what a deletion must trust.

    `labels` maps each name to {"color", "description"}, either None where
    the schema's value is missing or bad. `keep` holds names that are
    neither synced nor ever deleted (a label named for an Issue State, a
    declared priority when the regime is unknown, a declared name gh cannot
    pass whole). `sections` are the schema sections the set derives from.
    `notes` are warnings for stderr."""

    labels: Dict[str, Dict[str, Optional[str]]] = field(default_factory=dict)
    keep: set = field(default_factory=set)
    sections: Tuple[str, ...] = ()
    notes: List[str] = field(default_factory=list)


def desired_labels(loaded: RepoSchema, priority_regime: str,
                   board_priorities: Optional[Iterable[str]] = None
                   ) -> DesiredLabels:
    """The labels `loaded`'s schema declares for a repo in `priority_regime`
    ("board-field", "p-labels", or "unknown").

    `board_priorities` are the option names of the canonical board's
    `Priority` field, for "board-field". The priority labels are deletion
    candidates there only on verified ground: when that field holds every
    Issue Priority the schema declares. A board whose `Priority` field
    lacks some (a hand-made High, Medium, Low, say, or None given) keeps
    them, neither created nor deleted, with a warning naming the
    mismatch. The Issue Priorities are always among the sections a
    deletion derives from, so a deletion also needs them complete."""
    desired = DesiredLabels()
    sections = [tracker_schema.ISSUE_KINDS, tracker_schema.ISSUE_PRIORITIES]
    groups = [(tracker_schema.ISSUE_KINDS, loaded.section(tracker_schema.ISSUE_KINDS))]
    priorities = loaded.section(tracker_schema.ISSUE_PRIORITIES)
    if priority_regime == P_LABELS:
        groups.append((tracker_schema.ISSUE_PRIORITIES, priorities))
    elif priority_regime == BOARD_FIELD:
        held = set(board_priorities or ())
        lacking = [p.name for p in priorities or () if p.name not in held]
        if lacking:
            desired.keep.update(priority.name for priority in priorities)
            holds = ", ".join(board_priorities or ()) or "nothing"
            desired.notes.append(
                "warning: the board's Priority field lacks the Issue "
                f"Priorities {', '.join(lacking)} (it holds: {holds}), so "
                "priority labels are neither created nor deleted: "
                + ", ".join(p.name for p in priorities)
            )
    elif priorities:
        # Whether the repo carries priority as labels is unknown, so its
        # priority labels are neither created nor deleted.
        desired.keep.update(priority.name for priority in priorities)
        desired.notes.append(
            "warning: the priority regime is unknown (see ghw-orient's "
            "priority_regime), so priority labels are neither created "
            "nor deleted: " + ", ".join(p.name for p in priorities)
        )
    sections += [tracker_schema.LABEL_AXES, tracker_schema.UNAXED_LABELS]
    axes = loaded.section(tracker_schema.LABEL_AXES)
    groups.append((tracker_schema.LABEL_AXES,
                   None if axes is None else
                   tuple(label for axis in axes for label in axis.labels)))
    groups.append((tracker_schema.UNAXED_LABELS,
                   loaded.section(tracker_schema.UNAXED_LABELS)))
    # A label named for an Issue State is declared by it, so it is kept.
    sections.append(tracker_schema.ISSUE_STATES)
    states = loaded.section(tracker_schema.ISSUE_STATES)
    desired.keep.update(state.name for state in states or ())
    desired.sections = tuple(sections)

    folded: Dict[str, Tuple[str, str]] = {}
    for section, entries in groups:
        for entry in entries or ():
            reason = label_contract.uncarriable_reason(entry.name)
            if reason is not None:
                desired.keep.add(entry.name)
                desired.notes.append(
                    f"warning: {section} declares {entry.name!r}, which "
                    f"{reason}, so it cannot be carried on GitHub and is "
                    "neither created nor deleted"
                )
                continue
            key = entry.name.lower()
            if key in folded:
                # GitHub matches label names without regard to case, so two
                # entries that fold together are one label; the first wins.
                first, where = folded[key]
                desired.notes.append(
                    f"warning: {section} declares {entry.name!r}, which is "
                    f"the same GitHub label as {first!r} in {where}; the "
                    f"first is synced"
                )
                continue
            folded[key] = (entry.name, section)
            desired.labels[entry.name] = {
                "color": entry.color,
                "description": _fitted(entry.meaning),
            }
    return desired


def diff_labels(desired: DesiredLabels,
                existing: Iterable[dict]) -> Dict[str, list]:
    """Compare the desired labels against the repo's live ones.

    `existing` is lib.boards.fetch_labels() output. Returns
    {"create": [{"name", "color", "description"}],
     "update": [{"name", "color", "description", "from": {"color", "description"}}],
     "delete": [name, ...], "unchanged": [name, ...],
     "case_mismatch": [{"live", "desired"}], "uncarriable": [name, ...]},
    each list sorted by name. A converged repo yields empty
    create/update/delete lists. `uncarriable` holds the live labels the
    schema does not declare but gh cannot pass whole as a name, so they are
    left for a person to delete by hand.

    Names match case-insensitively, because GitHub's label namespace is: a
    live `Bug` against a desired `bug` is the same label, and matching it
    exactly would plan a create the API then rejects as already-existing --
    an unrecoverable failure on every run. Such a pair is reported under
    `case_mismatch` and otherwise treated as matched; renaming it is a human
    act (this wrapper never renames). Updates carry the *live* spelling in
    `name`, since that is what a `gh label edit` has to target. A live label
    in `desired.keep` is never a deletion candidate.
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
    for name in sorted(desired.labels):
        attributes = desired.labels[name]
        current = live.get(name.lower())
        if current is None:
            create.append({
                "name": name,
                "color": normalize_color(attributes["color"] or NEUTRAL_COLOR),
                "description": attributes["description"] or "",
            })
            continue
        if current["name"] != name:
            case_mismatch.append({"live": current["name"], "desired": name})
        now = {"color": current["color"], "description": current["description"]}
        wanted = {
            "color": (normalize_color(attributes["color"])
                      if attributes["color"] is not None else now["color"]),
            "description": (attributes["description"]
                            if attributes["description"] is not None
                            else now["description"]),
        }
        if wanted == now:
            unchanged.append(current["name"])
        else:
            update.append({"name": current["name"], **wanted, "from": now})
    declared = {name.lower() for name in desired.labels}
    declared |= {name.lower() for name in desired.keep}
    candidates = sorted(live[key]["name"] for key in set(live) - declared)
    return {
        "create": create,
        "update": update,
        "delete": [name for name in candidates
                   if label_contract.uncarriable_reason(name) is None],
        "unchanged": unchanged,
        "case_mismatch": case_mismatch,
        "uncarriable": [name for name in candidates
                        if label_contract.uncarriable_reason(name) is not None],
    }


def normalize_color(color: Optional[str]) -> str:
    """A label color as 6 lowercase hex digits, with any leading '#' dropped.

    GitHub accepts '#a2eeef' and 'A2EEEF' on input and reports 'a2eeef', so
    normalizing both sides keeps a cosmetic difference from looking like drift.
    """
    return (color or "").lstrip("#").lower()


def _fitted(meaning: Optional[str]) -> Optional[str]:
    """A meaning as a GitHub label description: unchanged when it fits,
    otherwise cut at a word boundary and ended with an ellipsis."""
    if meaning is None or len(meaning) <= DESCRIPTION_LIMIT:
        return meaning
    room = DESCRIPTION_LIMIT - len(_ELLIPSIS)
    cut = meaning[:room]
    if " " in cut and not meaning[room].isspace():
        cut = cut[:cut.rindex(" ")]
    return cut.rstrip(" ,;:") + _ELLIPSIS
