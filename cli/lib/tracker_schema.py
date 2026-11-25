"""The reader for a repo's Tracker Schema: its one JSON block, parsed and checked.

A Tracker Schema is a Markdown file (`TRACKER.md` at a repo's root, copied
from `skills/setup-issue-tracker/TRACKER.default.md`) whose one JSON block
holds what tooling reads: the Issue Kinds, the Issue Priorities, the Issue
Label Schema, each Issue State's name and open flag, and the provenance. The
prose around it holds the state meanings and transition conditions, which
are for agents and people, so this module reads none of it.

The file itself is the contract this module implements: the rule under its
"How the block is delimited" finds the block, and "What each key holds" is
the shape the block is checked against. Anything else raises
TrackerSchemaError with a message that names the line or the key at fault,
so an agent can fix the file in one round trip. The reader never guesses:
it does not search for a second-best block, fill in a missing key, skip an
unknown one, or keep either value of a key written twice.

What this module leaves to its callers: where a repo's Tracker Schema is
found (a Verb names its repo, and the cwd never decides that), and what
happens when a repo has none. It takes text, or a path for convenience.

How a Wrapper maps a failure to the Exit-code contract
(docs/index.md#exit-code-contract):

  - TrackerSchemaError: exit 2. The repo's file is state the caller must
    change, through the repo's normal review, before the call can work.
  - A missing file (FileNotFoundError from `load`): the caller decides,
    since what a Verb does when a repo has no Tracker Schema is not yet
    settled (docs/projects/use-issues/design.md, "The reader").
  - Any other OSError: exit 1.

Standard library only, Python 3.9.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Optional, Tuple, Union

BEGIN_MARKER = "<!-- BEGIN tracker-schema -->"
END_MARKER = "<!-- END tracker-schema -->"
OPENING_FENCE = "```json"
CLOSING_FENCE = "```"

_TOP_LEVEL_KEYS = (
    "provenance", "issue_kinds", "issue_priorities", "issue_label_schema",
    "issue_states",
)
_PROVENANCE_KEYS = ("source_repo", "source_commit", "default_path")
_KIND_KEYS = ("name", "meaning")
_PRIORITY_KEYS = ("name", "meaning", "stale_after_days")
_LABEL_SCHEMA_KEYS = ("axes", "labels")
_AXIS_KEYS = (
    "name", "prefix", "meaning", "every_issue_carries_at_least_one", "labels",
)
_LABEL_KEYS = ("name", "meaning")
_STATE_KEYS = ("name", "open")
_FULL_COMMIT = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
# The longest staleness a datetime.timedelta can hold, so a caller adding it
# to a timestamp cannot overflow on a value the reader accepted.
_MAX_STALE_DAYS = timedelta.max.days


class TrackerSchemaError(Exception):
    """Raised when a Tracker Schema is malformed: its block cannot be found
    by the delimiting rule, does not parse, or is not the documented shape."""


@dataclass(frozen=True)
class Provenance:
    """Which revision of the shipped default a copy was taken from. All three
    fields are None in the shipped default itself."""

    source_repo: Optional[str]
    source_commit: Optional[str]
    default_path: Optional[str]

    @property
    def is_original(self) -> bool:
        """True for the shipped default: every field is null."""
        return (self.source_repo is None and self.source_commit is None
                and self.default_path is None)

    @property
    def is_complete(self) -> bool:
        """True for a copy that kept its provenance: every field is set. A
        file that is neither original nor complete has lost its provenance."""
        return (self.source_repo is not None and self.source_commit is not None
                and self.default_path is not None)


@dataclass(frozen=True)
class IssueKind:
    name: str
    meaning: str


@dataclass(frozen=True)
class IssuePriority:
    name: str
    meaning: str
    stale_after_days: int


@dataclass(frozen=True)
class IssueLabel:
    """A declared Issue Label, its name written in full as on an Issue."""

    name: str
    meaning: str


@dataclass(frozen=True)
class LabelAxis:
    """An axis of the Issue Label Schema. `required` is the file's
    `every_issue_carries_at_least_one`."""

    name: str
    prefix: str
    meaning: str
    required: bool
    labels: Tuple[IssueLabel, ...]


@dataclass(frozen=True)
class IssueLabelSchema:
    axes: Tuple[LabelAxis, ...]
    labels: Tuple[IssueLabel, ...]  # the labels that belong to no axis

    def all_labels(self) -> Tuple[IssueLabel, ...]:
        """Every declared label: each axis's in file order, then the unaxed."""
        return tuple(
            label for axis in self.axes for label in axis.labels
        ) + self.labels

    def label(self, name: str) -> Optional[IssueLabel]:
        """The declared label with this exact name, or None.

        Only the axes' labels and the unaxed labels are here. Where a tracker
        has no field for kind, priority, or state, the file says a label
        named for one carries it and is declared by it, so None from here
        does not by itself make such a label unknown."""
        for candidate in self.all_labels():
            if candidate.name == name:
                return candidate
        return None

    def axis(self, name: str) -> Optional[LabelAxis]:
        """The axis with this name, or None."""
        for candidate in self.axes:
            if candidate.name == name:
                return candidate
        return None

    def axis_of(self, label_name: str) -> Optional[LabelAxis]:
        """The axis whose prefix the label name begins with, or None. This
        answers by prefix, so it also places a label the axis does not list."""
        for candidate in self.axes:
            if label_name.startswith(candidate.prefix):
                return candidate
        return None


@dataclass(frozen=True)
class IssueState:
    name: str
    open: bool


@dataclass(frozen=True)
class TrackerSchema:
    """A parsed, checked Tracker Schema. Read-only: every collection is a
    tuple in file order, and the priorities run from highest to lowest."""

    provenance: Provenance
    issue_kinds: Tuple[IssueKind, ...]
    issue_priorities: Tuple[IssuePriority, ...]
    issue_label_schema: IssueLabelSchema
    issue_states: Tuple[IssueState, ...]

    def kind(self, name: str) -> Optional[IssueKind]:
        return _by_name(self.issue_kinds, name)

    def priority(self, name: str) -> Optional[IssuePriority]:
        return _by_name(self.issue_priorities, name)

    def state(self, name: str) -> Optional[IssueState]:
        return _by_name(self.issue_states, name)

    @property
    def open_states(self) -> Tuple[IssueState, ...]:
        return tuple(state for state in self.issue_states if state.open)

    @property
    def closed_states(self) -> Tuple[IssueState, ...]:
        return tuple(state for state in self.issue_states if not state.open)


def load(path: Union[str, Path]) -> TrackerSchema:
    """Read and parse the Tracker Schema at `path`.

    A missing or unreadable file raises the OSError unchanged, since what it
    means is the caller's to decide; a file that is not UTF-8, or is
    malformed, raises TrackerSchemaError with the path in its message.
    """
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise TrackerSchemaError(f"{path}: not UTF-8 text ({error.reason})")
    try:
        return parse(text)
    except TrackerSchemaError as error:
        raise TrackerSchemaError(f"{path}: {error}") from None


def parse(text: str) -> TrackerSchema:
    """Extract, parse, and check the JSON block of a Tracker Schema's text."""
    block, first_line = _extract(text)
    try:
        document = json.loads(block, object_pairs_hook=_refuse_duplicate_keys)
    except json.JSONDecodeError as error:
        # The position is reported as a line of the whole file, so the agent
        # fixing it need not count from the fence.
        raise TrackerSchemaError(
            f"the JSON block does not parse (line {first_line + error.lineno - 1}, "
            f"column {error.colno}): {error.msg}"
        ) from None
    except RecursionError:
        raise TrackerSchemaError(
            "the JSON block nests too deeply to read; no key in it nests more "
            "than a few levels"
        ) from None
    return _schema(document)


def extract_block(text: str) -> str:
    """The text strictly inside the JSON block's fence, by the delimiting
    rule, unparsed, with "\\n" line endings whatever the file uses. Raises
    TrackerSchemaError when the rule is not met."""
    return _extract(text)[0]


def _extract(text: str) -> Tuple[str, int]:
    """The block's text and the file line number of its first line."""
    lines = text.split("\n")
    begins, ends = [], []
    for number, line in enumerate(lines, start=1):
        trimmed = line.rstrip()
        if trimmed == BEGIN_MARKER:
            begins.append(number)
        elif trimmed == END_MARKER:
            ends.append(number)
        elif trimmed.strip() in (BEGIN_MARKER, END_MARKER):
            raise TrackerSchemaError(
                f"line {number}: a marker line must start at the line's first "
                "character; remove the indentation"
            )
    for marker, found in ((BEGIN_MARKER, begins), (END_MARKER, ends)):
        if not found:
            raise TrackerSchemaError(
                f"no {marker} line: the JSON block must sit between "
                f"{BEGIN_MARKER} and {END_MARKER}, each alone on its line"
            )
        if len(found) > 1:
            raise TrackerSchemaError(
                f"{marker} appears on {len(found)} lines "
                f"({', '.join(str(n) for n in found)}); the file must have "
                "exactly one. Keep any example of it off a line of its own"
            )
    begin, end = begins[0], ends[0]
    if end < begin:
        raise TrackerSchemaError(
            f"{END_MARKER} (line {end}) comes before {BEGIN_MARKER} "
            f"(line {begin})"
        )

    opening = closing = None
    for number in range(begin + 1, end):
        trimmed = lines[number - 1].rstrip()
        if not trimmed:
            continue
        is_fence = trimmed.lstrip().startswith(("```", "~~~"))
        if opening is None:
            if not is_fence:
                raise TrackerSchemaError(
                    f"line {number}: only blank lines may sit between "
                    f"{BEGIN_MARKER} and the opening {OPENING_FENCE} line"
                )
            if trimmed != OPENING_FENCE:
                raise TrackerSchemaError(
                    f"line {number}: the block's fence must open with a line "
                    f"that is exactly {OPENING_FENCE} (tagged json, not "
                    "indented)"
                )
            opening = number
        elif closing is None:
            if is_fence:
                if trimmed != CLOSING_FENCE:
                    raise TrackerSchemaError(
                        f"line {number}: the fence must close with a line that "
                        f"is exactly {CLOSING_FENCE}"
                    )
                closing = number
        else:
            if is_fence:
                raise TrackerSchemaError(
                    f"line {number}: a second fenced block between the markers; "
                    "there must be exactly one, and other code blocks belong "
                    "outside the markers"
                )
            raise TrackerSchemaError(
                f"line {number}: only blank lines may sit between the closing "
                f"fence and {END_MARKER}"
            )
    if opening is None:
        raise TrackerSchemaError(
            f"no fenced block between {BEGIN_MARKER} (line {begin}) and "
            f"{END_MARKER} (line {end}); the JSON goes in one {OPENING_FENCE} "
            "fence there"
        )
    if closing is None:
        raise TrackerSchemaError(
            f"the {OPENING_FENCE} fence opened on line {opening} is not closed "
            f"by a {CLOSING_FENCE} line before {END_MARKER} (line {end})"
        )
    inside = (line[:-1] if line.endswith("\r") else line
              for line in lines[opening:closing - 1])
    return "\n".join(inside), opening + 1


def _refuse_duplicate_keys(pairs: list) -> dict:
    """json's object hook: a key written twice in one object is refused,
    since keeping either value would be a guess."""
    document = {}
    for key, value in pairs:
        if key in document:
            raise TrackerSchemaError(
                f"the JSON block writes the key {key!r} twice in one object"
            )
        document[key] = value
    return document


def _schema(document: object) -> TrackerSchema:
    _require_object(document, "the JSON block", _TOP_LEVEL_KEYS)
    return TrackerSchema(
        provenance=_provenance(document["provenance"]),
        issue_kinds=_kinds(document["issue_kinds"]),
        issue_priorities=_priorities(document["issue_priorities"]),
        issue_label_schema=_label_schema(document["issue_label_schema"]),
        issue_states=_states(document["issue_states"]),
    )


def _provenance(value: object) -> Provenance:
    where = "provenance"
    _require_object(value, where, _PROVENANCE_KEYS)
    for key in _PROVENANCE_KEYS:
        field = value[key]
        if field is not None:
            _require_text(field, f"{where}.{key}", "a string or null")
    commit = value["source_commit"]
    if commit is not None and not _FULL_COMMIT.fullmatch(commit):
        raise TrackerSchemaError(
            f"{where}.source_commit must be a full commit (40 or 64 lowercase "
            "hex digits) or null"
        )
    return Provenance(value["source_repo"], commit, value["default_path"])


def _kinds(value: object) -> Tuple[IssueKind, ...]:
    entries = _require_list(value, "issue_kinds", nonempty=True)
    kinds = []
    for position, raw in enumerate(entries):
        where = f"issue_kinds[{position}]"
        _require_object(raw, where, _KIND_KEYS)
        kinds.append(IssueKind(_name(raw, where), _meaning(raw, where)))
    _refuse_duplicates(kinds, "issue_kinds")
    return tuple(kinds)


def _priorities(value: object) -> Tuple[IssuePriority, ...]:
    entries = _require_list(value, "issue_priorities", nonempty=True)
    priorities = []
    for position, raw in enumerate(entries):
        where = f"issue_priorities[{position}]"
        _require_object(raw, where, _PRIORITY_KEYS)
        days = raw["stale_after_days"]
        if (isinstance(days, bool) or not isinstance(days, int)
                or not 1 <= days <= _MAX_STALE_DAYS):
            raise TrackerSchemaError(
                f"{where}.stale_after_days must be a whole number of days, "
                f"from 1 to {_MAX_STALE_DAYS}"
            )
        priorities.append(
            IssuePriority(_name(raw, where), _meaning(raw, where), days)
        )
    _refuse_duplicates(priorities, "issue_priorities")
    return tuple(priorities)


def _label_schema(value: object) -> IssueLabelSchema:
    where = "issue_label_schema"
    _require_object(value, where, _LABEL_SCHEMA_KEYS)
    axes = []
    for position, raw in enumerate(_require_list(value["axes"], f"{where}.axes")):
        axes.append(_axis(raw, f"{where}.axes[{position}]"))
    _refuse_duplicates(axes, f"{where}.axes")
    # One prefix that begins another would put a label on both axes, so
    # which axis a label is on would depend on the order they are listed in.
    for first, axis in enumerate(axes):
        for other in axes[first + 1:]:
            if (_folded(axis.prefix).startswith(_folded(other.prefix))
                    or _folded(other.prefix).startswith(_folded(axis.prefix))):
                raise TrackerSchemaError(
                    f"{where}.axes: the prefixes {axis.prefix!r} and "
                    f"{other.prefix!r} overlap; no axis's prefix may begin "
                    "another's, so every label belongs to at most one axis"
                )
    labels = _labels(value["labels"], f"{where}.labels")
    for position, label in enumerate(labels):
        for axis in axes:
            if _folded(label.name).startswith(_folded(axis.prefix)):
                raise TrackerSchemaError(
                    f"{where}.labels[{position}]: {label.name!r} begins with "
                    f"the prefix of the {axis.name!r} axis, so it belongs in "
                    "that axis's labels; this list is for labels on no axis"
                )
    schema = IssueLabelSchema(tuple(axes), labels)
    _refuse_duplicates(list(schema.all_labels()), f"{where} (all labels)")
    return schema


def _axis(raw: object, where: str) -> LabelAxis:
    _require_object(raw, where, _AXIS_KEYS)
    prefix = _require_name(raw["prefix"], f"{where}.prefix")
    required = raw["every_issue_carries_at_least_one"]
    if not isinstance(required, bool):
        raise TrackerSchemaError(
            f"{where}.every_issue_carries_at_least_one must be true or false"
        )
    labels = _labels(raw["labels"], f"{where}.labels")
    for position, label in enumerate(labels):
        if not label.name.startswith(prefix) or label.name == prefix:
            raise TrackerSchemaError(
                f"{where}.labels[{position}]: every label on this axis is "
                f"written in full, beginning with its prefix {prefix!r}"
            )
    return LabelAxis(_name(raw, where), prefix, _meaning(raw, where), required,
                     labels)


def _labels(value: object, where: str) -> Tuple[IssueLabel, ...]:
    labels = []
    for position, raw in enumerate(_require_list(value, where)):
        at = f"{where}[{position}]"
        _require_object(raw, at, _LABEL_KEYS)
        labels.append(IssueLabel(_name(raw, at), _meaning(raw, at)))
    return tuple(labels)


def _states(value: object) -> Tuple[IssueState, ...]:
    entries = _require_list(value, "issue_states", nonempty=True)
    states = []
    for position, raw in enumerate(entries):
        where = f"issue_states[{position}]"
        _require_object(raw, where, _STATE_KEYS)
        if not isinstance(raw["open"], bool):
            raise TrackerSchemaError(f"{where}.open must be true or false")
        states.append(IssueState(_name(raw, where), raw["open"]))
    _refuse_duplicates(states, "issue_states")
    if not any(state.open for state in states):
        raise TrackerSchemaError("issue_states: no state is open")
    if all(state.open for state in states):
        raise TrackerSchemaError("issue_states: no state is closed")
    return tuple(states)


def _require_object(value: object, where: str, keys: Tuple[str, ...]) -> None:
    if not isinstance(value, dict):
        raise TrackerSchemaError(
            f"{where} must be a JSON object with the keys {', '.join(keys)}"
        )
    missing = [key for key in keys if key not in value]
    if missing:
        raise TrackerSchemaError(
            f"{where} is missing {', '.join(missing)}; it takes exactly "
            f"{', '.join(keys)}"
        )
    unknown = sorted(set(value) - set(keys))
    if unknown:
        _on_unknown_keys(where, unknown, keys)


def _on_unknown_keys(where: str, unknown: list, keys: Tuple[str, ...]) -> None:
    """The whole policy for a key the file does not document, at any level:
    today it is refused. Nothing reads an undocumented key, so returning
    here instead (with a warning to the caller, say) would ignore it."""
    raise TrackerSchemaError(
        f"{where} has unknown key(s) {', '.join(unknown)}; it takes exactly "
        f"{', '.join(keys)}"
    )


def _require_list(value: object, where: str, nonempty: bool = False) -> list:
    if not isinstance(value, list):
        raise TrackerSchemaError(f"{where} must be a JSON list")
    if nonempty and not value:
        raise TrackerSchemaError(f"{where} must list at least one entry")
    return value


def _require_text(value: object, where: str, wanted: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise TrackerSchemaError(
            f"{where} must be {wanted}, with no surrounding whitespace"
        )


def _name(raw: dict, where: str) -> str:
    return _require_name(raw["name"], f"{where}.name")


def _require_name(value: object, where: str) -> str:
    """A name or prefix: text with no control or invisible formatting
    characters, since it is matched against what a tracker holds."""
    _require_text(value, where, "a non-empty string")
    if not value.isprintable():
        raise TrackerSchemaError(
            f"{where} must hold no control or invisible formatting characters "
            "(a newline or a zero-width space, say)"
        )
    return value


def _meaning(raw: dict, where: str) -> str:
    _require_text(raw["meaning"], f"{where}.meaning", "a non-empty string")
    return raw["meaning"]


def _refuse_duplicates(entries: list, where: str) -> None:
    """Refuse two entries whose names differ at most in case: a tracker may
    match names case-insensitively, as GitHub does for labels, and then two
    such entries would be one."""
    seen = {}
    for entry in entries:
        key = _folded(entry.name)
        if key in seen:
            if seen[key] == entry.name:
                raise TrackerSchemaError(
                    f"{where}: {entry.name!r} is declared twice"
                )
            raise TrackerSchemaError(
                f"{where}: {seen[key]!r} and {entry.name!r} differ only in "
                "case; names must differ by more than case"
            )
        seen[key] = entry.name


def _folded(name: str) -> str:
    return name.casefold()


def _by_name(entries: tuple, name: str):
    for entry in entries:
        if entry.name == name:
            return entry
    return None
