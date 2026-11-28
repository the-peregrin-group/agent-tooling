"""The label attachment contract, as enforced by ghw-issue-create and
ghw-issue-edit add-label and remove-label.

The contract comes from the repo's Tracker Schema (LabelRules, built from
what lib.github.repo_schema loaded):

  - an issue's kind is one of the schema's Issue Kinds, carried as its Kind
    Label, and an issue is filed with exactly one and never given a second
    (removing it is allowed, so that reclassifying is remove-label then
    add-label, which leaves the issue without one in between);
  - a label the schema does not declare is refused, whether or not it
    exists on GitHub ("an unknown label is a mistake to fix, not a new
    label"); the declared labels are the kinds, the priorities, every
    axis's labels, the labels on no axis, and a label named for an Issue
    State (which the schema says that state declares);
  - every axis the schema marks as carried by every Issue needs one of its
    labels at creation, and the last one cannot be removed.

On top of that, a label must already exist in the repo's live registry,
since ghw-label-sync is the sole label-creation path, and its name must be
one gh can pass whole (`uncarriable_reason`). Attaching a label is an
additive write, so a check is skipped only where the part of the schema it
needs is missing or unusable; everything that can still be checked is, and
`LabelRules.unchecked` says what was skipped. TRIAGE.md plays no part.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple

from lib import tracker_schema
from lib.github.repo_schema import RepoSchema

# Every section a label's name could be declared in.
_DECLARING = (
    tracker_schema.ISSUE_KINDS, tracker_schema.ISSUE_PRIORITIES,
    tracker_schema.LABEL_AXES, tracker_schema.UNAXED_LABELS,
    tracker_schema.ISSUE_STATES,
)


class LabelContractError(Exception):
    """Raised when a label attachment would violate the ecosystem contract."""


def uncarriable_reason(name: str) -> Optional[str]:
    """Why gh cannot pass `name` as one label, or None when it can.

    gh splits `--label` and `--add-label` values on commas, so `x,bug`
    would attach `x` and `bug`; and a name starting with `-` reads as an
    option where a label name is a positional argument. Such a name cannot
    be carried on GitHub through ghw, so it never reaches a gh argument."""
    if "," in name:
        return "contains a comma, which gh splits a label list on"
    if name.startswith("-"):
        return "starts with '-', which gh reads as an option"
    return None


class LabelRules:
    """What the repo's Tracker Schema lets ghw check about labels.

    `kinds` is the set of Issue Kind names, or None when the kinds are
    unusable. `required_axes` are the axes every Issue carries a label
    from, or None when the axes are unusable. Whether a name is declared is
    `is_declared`, answered from whichever sections can be read."""

    def __init__(self, loaded: RepoSchema):
        self.source = loaded.source
        kinds = loaded.section(tracker_schema.ISSUE_KINDS)
        axes = loaded.section(tracker_schema.LABEL_AXES)
        self.kinds: Optional[FrozenSet[str]] = (
            None if kinds is None else frozenset(k.name for k in kinds))
        self.axes: Optional[Tuple[tracker_schema.LabelAxis, ...]] = axes
        self.required_axes: Optional[Tuple[tracker_schema.LabelAxis, ...]] = (
            None if axes is None else tuple(axis for axis in axes if axis.required)
        )
        # The names each usable section declares; an unusable one is absent.
        self._names: Dict[str, FrozenSet[str]] = {}
        for section in _DECLARING:
            entries = loaded.section(section)
            if entries is None:
                continue
            if section == tracker_schema.LABEL_AXES:
                names = [label.name for axis in entries for label in axis.labels]
            else:
                names = [entry.name for entry in entries]
            self._names[section] = frozenset(names)

    def unchecked(self) -> List[str]:
        """A stderr warning for each rule the schema could not back."""
        lines = []
        if self.kinds is None:
            lines.append(f"warning: {self.source}: the Issue Kinds cannot be "
                         "read, so the kind and the one-kind rule are not checked")
        unread = [section for section in _DECLARING if section not in self._names]
        if unread:
            lines.append(
                f"warning: {self.source}: {', '.join(unread)} cannot be read, "
                "so a label on no usable axis that no usable section declares "
                "is checked only against the live registry")
        if self.required_axes is None:
            lines.append(f"warning: {self.source}: the label axes cannot be "
                         "read, so no axis is required")
        return lines

    def is_declared(self, name: str) -> Optional[bool]:
        """True if a usable section declares `name`; False if the schema
        shows it does not; None when that cannot be known.

        A name with a usable axis's prefix can belong only to that axis, so
        the axis alone decides it. Any other name is undeclared only when
        every section it could belong to can be read."""
        if any(name in names for names in self._names.values()):
            return True
        if self.axes is not None and any(
                name.startswith(axis.prefix) for axis in self.axes):
            return False
        if len(self._names) == len(_DECLARING):
            return False
        return None

    def kinds_among(self, names: Iterable[str]) -> List[str]:
        """The subset of `names` that are kinds, order preserved; empty when
        the kinds are unknown."""
        return [name for name in names if self.kinds and name in self.kinds]

    def undeclared(self, names: Iterable[str]) -> List[str]:
        """The names the schema shows it does not declare."""
        return [name for name in names if self.is_declared(name) is False]


def validate_creation_labels(kind: str, extra_labels: List[str],
                             registry_names: set, rules: LabelRules) -> None:
    """Validate the full label set for a new issue.

    Raises LabelContractError unless every name is one gh can pass whole,
    and, as far as the schema can be read: `kind` is one of its Issue Kinds
    and is not repeated among `extra_labels`, no second kind hides among
    them, every label is declared, every required axis has one of its
    labels among them, and every label already exists in the repo's live
    registry.
    """
    _refuse_uncarriable([kind, *extra_labels], rules)
    if rules.kinds is not None and kind not in rules.kinds:
        raise LabelContractError(
            f"{kind!r} is not an Issue Kind in {rules.source}; the kinds are "
            f"{'|'.join(sorted(rules.kinds))}"
        )
    if kind in extra_labels:
        raise LabelContractError(
            f"{kind!r} duplicates the Kind Label; list it once, as the "
            "kind-label argument"
        )
    second_kinds = rules.kinds_among(extra_labels)
    if second_kinds:
        raise LabelContractError(
            f"{second_kinds[0]!r} is a second Kind Label; every issue carries "
            f"exactly one, and this issue's is {kind!r}"
        )
    _refuse_undeclared([kind, *extra_labels], rules)
    for axis in rules.required_axes or ():
        if not any(label.startswith(axis.prefix) for label in extra_labels):
            raise LabelContractError(
                f"every issue carries at least one {axis.prefix!r} label "
                f"({axis.name} axis, {rules.source}); none was given"
            )
    missing = [
        label for label in (kind, *extra_labels) if label not in registry_names
    ]
    if missing:
        raise LabelContractError(
            "label(s) not in the repo's label registry: "
            + ", ".join(repr(label) for label in missing)
            + ". The registry is the attachment authority; create labels with "
            "ghw-label-sync first."
        )


def validate_label_addition(label: str, current_label_names: Iterable[str],
                            registry_names: set, rules: LabelRules) -> None:
    """Validate adding one label to an existing issue.

    Raises LabelContractError if gh cannot pass the name whole, if the
    schema does not declare the label, if it is absent from the live
    registry, or if it is a kind and the issue already carries a different
    one (reclassifying is two visible calls: remove-label, then add-label).
    """
    _refuse_uncarriable([label], rules)
    _refuse_undeclared([label], rules)
    if label not in registry_names:
        raise LabelContractError(
            f"label {label!r} is not in the repo's label registry. The registry "
            "is the attachment authority; create labels with ghw-label-sync first."
        )
    if rules.kinds_among([label]):
        incumbents = [
            name for name in rules.kinds_among(current_label_names) if name != label
        ]
        if incumbents:
            raise LabelContractError(
                f"issue already carries Kind Label {incumbents[0]!r}; every issue "
                f"carries exactly one. Reclassify with remove-label "
                f"{incumbents[0]!r} first, then add-label {label!r}."
            )


def validate_label_removal(label: str, current_label_names: Iterable[str],
                           rules: LabelRules) -> None:
    """Validate removing one attached label from an issue.

    Raises LabelContractError if gh cannot pass the name whole, or if it is
    the issue's last label on an axis every Issue carries one of. Removing
    the Kind Label is allowed: it is the first of reclassifying's two
    calls."""
    _refuse_uncarriable([label], rules)
    current = list(current_label_names)
    for axis in rules.required_axes or ():
        if not label.startswith(axis.prefix):
            continue
        remaining = [name for name in current
                     if name != label and name.startswith(axis.prefix)]
        if not remaining:
            raise LabelContractError(
                f"{label!r} is the issue's last {axis.prefix!r} label, and "
                f"every issue carries at least one ({axis.name} axis, "
                f"{rules.source}); add-label another first"
            )


def _refuse_uncarriable(names: List[str], rules: LabelRules) -> None:
    for name in names:
        reason = uncarriable_reason(name)
        if reason is not None:
            raise LabelContractError(
                f"label {name!r} {reason}, so ghw cannot carry it on GitHub; "
                f"name it without one in {rules.source}"
            )


def _refuse_undeclared(names: List[str], rules: LabelRules) -> None:
    undeclared = rules.undeclared(names)
    if undeclared:
        raise LabelContractError(
            "label(s) not declared in the repo's Tracker Schema: "
            + ", ".join(repr(name) for name in undeclared)
            + f". An unknown label is a mistake to fix, not a new label; "
            f"declare it in {rules.source} and run ghw-label-sync, or use a "
            "declared one."
        )
