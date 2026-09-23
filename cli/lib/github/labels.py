"""The label attachment contract, as enforced by ghw-issue-create and
ghw-issue-edit add-label.

The repo's live label registry is the attachment authority: a label may be
attached only if it already exists, and ghw-label-sync is the sole
label-creation path. On top of existence, every issue carries exactly one
canonical type label, and creation additionally requires at least one 'area:'
label. TRIAGE.md plays no part in day-to-day label validation.
"""

from __future__ import annotations

from typing import Iterable

from lib.schema import AREA_LABEL_PREFIX, TYPE_LABELS


class LabelContractError(Exception):
    """Raised when a label attachment would violate the ecosystem contract."""


def type_labels_among(names: Iterable[str]) -> list[str]:
    """The subset of `names` that are canonical type labels, order preserved."""
    return [name for name in names if name in TYPE_LABELS]


def validate_creation_labels(
    type_label: str, extra_labels: list[str], registry_names: set[str]
) -> None:
    """Validate the full label set for a new issue.

    Raises LabelContractError unless: `type_label` is one of the five canonical
    type labels, `type_label` is not repeated among `extra_labels`, no second
    type label hides among `extra_labels`, at least one
    extra label is an 'area:' label, and every label already exists in the
    repo's live registry.
    """
    if type_label not in TYPE_LABELS:
        raise LabelContractError(
            f"type label must be one of {'|'.join(TYPE_LABELS)}, got {type_label!r}"
        )
    if type_label in extra_labels:
        raise LabelContractError(
            f"{type_label!r} duplicates the type label; list it once, as the "
            "type-label argument"
        )
    second_types = type_labels_among(extra_labels)
    if second_types:
        raise LabelContractError(
            f"{second_types[0]!r} is a second type label; every issue carries "
            f"exactly one, and this issue's is {type_label!r}"
        )
    if not any(label.startswith(AREA_LABEL_PREFIX) for label in extra_labels):
        raise LabelContractError("at least one 'area:' label is required at creation")
    missing = [
        label for label in (type_label, *extra_labels) if label not in registry_names
    ]
    if missing:
        raise LabelContractError(
            "label(s) not in the repo's label registry: "
            + ", ".join(repr(label) for label in missing)
            + ". The registry is the attachment authority; create labels with "
            "ghw-label-sync first."
        )


def validate_label_addition(
    label: str, current_label_names: Iterable[str], registry_names: set[str]
) -> None:
    """Validate adding one label to an existing issue.

    Raises LabelContractError if the label is absent from the live registry,
    or if it is a type label and the issue already carries a different one
    (reclassifying is two visible calls: remove-label, then add-label).
    """
    if label not in registry_names:
        raise LabelContractError(
            f"label {label!r} is not in the repo's label registry. The registry "
            "is the attachment authority; create labels with ghw-label-sync first."
        )
    if label in TYPE_LABELS:
        incumbents = [
            name for name in type_labels_among(current_label_names) if name != label
        ]
        if incumbents:
            raise LabelContractError(
                f"issue already carries type label {incumbents[0]!r}; every issue "
                f"carries exactly one. Reclassify with remove-label "
                f"{incumbents[0]!r} first, then add-label {label!r}."
            )
