"""The label attachment contract, as enforced by ghw-issue-create and
ghw-issue-edit add-label and remove-label.

The contract comes from the repo's Tracker Schema (LabelRules, built from
what lib.github.repo_schema loaded):

  - an issue's kind is one of the schema's Issue Kinds, carried as its Kind
    Label, and every issue carries exactly one;
  - a label the schema does not declare is refused, whether or not it
    exists on GitHub ("an unknown label is a mistake to fix, not a new
    label"); the declared labels are the kinds, the priorities, every
    axis's labels, and the labels on no axis;
  - every axis the schema marks as carried by every Issue needs one of its
    labels at creation, and the last one cannot be removed.

On top of that, a label must already exist in the repo's live registry,
since ghw-label-sync is the sole label-creation path. Attaching a label is
an additive write, so a rule whose part of the schema is missing or
unusable is skipped, the Verb goes ahead on what can still be checked, and
`LabelRules.unchecked` says what was skipped. TRIAGE.md plays no part.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from lib import tracker_schema
from lib.github.repo_schema import RepoSchema


class LabelContractError(Exception):
    """Raised when a label attachment would violate the ecosystem contract."""


class LabelRules:
    """What the repo's Tracker Schema lets ghw check about labels.

    `kinds` is the set of Issue Kind names, or None when the kinds are
    unusable. `declared` is every label name the schema declares, or None
    unless every section that declares labels is usable, since a label
    could otherwise belong to the unusable one. `required_axes` are the
    axes every Issue carries a label from, or None when the axes are
    unusable."""

    def __init__(self, loaded: RepoSchema):
        self.source = loaded.source
        kinds = loaded.section(tracker_schema.ISSUE_KINDS)
        priorities = loaded.section(tracker_schema.ISSUE_PRIORITIES)
        axes = loaded.section(tracker_schema.LABEL_AXES)
        unaxed = loaded.section(tracker_schema.UNAXED_LABELS)
        self.kinds = None if kinds is None else frozenset(k.name for k in kinds)
        self.required_axes: Optional[Tuple[tracker_schema.LabelAxis, ...]] = (
            None if axes is None else tuple(axis for axis in axes if axis.required)
        )
        if None in (kinds, priorities, axes, unaxed):
            self.declared = None
        else:
            self.declared = frozenset(
                [k.name for k in kinds] + [p.name for p in priorities]
                + [label.name for axis in axes for label in axis.labels]
                + [label.name for label in unaxed]
            )

    def unchecked(self) -> List[str]:
        """A stderr warning for each rule the schema could not back."""
        lines = []
        if self.kinds is None:
            lines.append(f"warning: {self.source}: the Issue Kinds cannot be "
                         "read, so the kind and the one-kind rule are not checked")
        if self.declared is None:
            lines.append(f"warning: {self.source}: not every label section can "
                         "be read, so labels are checked only against the live "
                         "registry")
        if self.required_axes is None:
            lines.append(f"warning: {self.source}: the label axes cannot be "
                         "read, so no axis is required")
        return lines

    def kinds_among(self, names: Iterable[str]) -> List[str]:
        """The subset of `names` that are kinds, order preserved; empty when
        the kinds are unknown."""
        return [name for name in names if self.kinds and name in self.kinds]

    def undeclared(self, names: Iterable[str]) -> List[str]:
        """The names the schema does not declare; empty when that cannot be
        known."""
        if self.declared is None:
            return []
        return [name for name in names if name not in self.declared]


def validate_creation_labels(kind: str, extra_labels: List[str],
                             registry_names: set, rules: LabelRules) -> None:
    """Validate the full label set for a new issue.

    Raises LabelContractError unless, as far as the schema can be read:
    `kind` is one of its Issue Kinds and is not repeated among
    `extra_labels`, no second kind hides among them, every label is
    declared, every required axis has a label among them, and every label
    already exists in the repo's live registry.
    """
    if rules.kinds is not None and kind not in rules.kinds:
        raise LabelContractError(
            f"{kind!r} is not an Issue Kind in {rules.source}; the kinds are "
            f"{'|'.join(sorted(rules.kinds))}"
        )
    if kind in extra_labels:
        raise LabelContractError(
            f"{kind!r} duplicates the kind label; list it once, as the "
            "kind-label argument"
        )
    second_kinds = rules.kinds_among(extra_labels)
    if second_kinds:
        raise LabelContractError(
            f"{second_kinds[0]!r} is a second kind label; every issue carries "
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

    Raises LabelContractError if the schema does not declare the label, if
    it is absent from the live registry, or if it is a kind and the issue
    already carries a different one (reclassifying is two visible calls:
    remove-label, then add-label).
    """
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
                f"issue already carries kind label {incumbents[0]!r}; every issue "
                f"carries exactly one. Reclassify with remove-label "
                f"{incumbents[0]!r} first, then add-label {label!r}."
            )


def validate_label_removal(label: str, current_label_names: Iterable[str],
                           rules: LabelRules) -> None:
    """Validate removing one attached label from an issue.

    Raises LabelContractError if it is the issue's last label on an axis
    every Issue carries one of."""
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
