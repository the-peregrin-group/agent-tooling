"""The reader for a repo's Tracker Schema: its one JSON block, read section by section.

A Tracker Schema is a Markdown file (`TRACKER.md` at a repo's root, copied
from `skills/setup-issue-tracker/TRACKER.default.md`) whose one JSON block
holds what tooling reads: the Issue Kinds, the Issue Priorities, the Issue
Label Schema, each Issue State's name and open flag, and the provenance. The
prose around it holds the state meanings and transition conditions, which
are for agents and people, so this module reads none of it.

The file itself is the contract this module implements: the rule under its
"How the block is delimited" finds the block, and "What each key holds" is
the shape each part of the block is read against.

The reader degrades gracefully. A flaw in one part of the block never stops
a caller from using the parts that are sound:

  - The whole file fails, with TrackerSchemaError, only when no block can be
    found by the delimiting rule or its JSON does not parse. The rule stays
    exact, since an ambiguous block has nothing in it worth salvaging.
  - Otherwise `parse` always returns a TrackerSchema. Each section
    (provenance, kinds, priorities, label axes, unaxed labels, states) is
    read on its own. A section that cannot be read safely is unusable, and
    asking for it raises UnusableSectionError for that section alone; a
    caller that never asks is unaffected.
  - Within a section, a bad entry is left out and the rest kept, and a bad
    field on an entry whose name is sound reads as None, wherever that
    cannot mislead. Where a partial section would mislead, the whole
    section is unusable instead; each such case says why where it is made.
  - A key the reader does not know, at any level, is ignored. A key it
    needs and does not find makes that field or section absent. So a copy
    written for a newer reader, and one written for an older reader, both
    keep everything else working.
  - Everything the reader left out, ignored, or could not use is a Problem
    in `TrackerSchema.problems`, worded so an agent can fix the file, and
    `warning_lines` turns them into the warnings every Verb prints, so a
    defect is visible even to a Verb that did not need the part at fault.

The library reports; it makes no exit-code decisions. What a missing file,
an unusable section, or a list of problems means for a Verb is the caller's
call, under the Exit-code contract (docs/index.md#exit-code-contract) and
the rule in docs/projects/use-issues/design.md, "The reader".

The ghw and fjw Verbs read the schema from the repo's default branch on the
forge and bdw from the workspace it stands in, so `parse(text)` is the main
entry; `load(path)` reads a file, for bdw and for tests.

Standard library only, Python 3.9.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

BEGIN_MARKER = "<!-- BEGIN tracker-schema -->"
END_MARKER = "<!-- END tracker-schema -->"
OPENING_FENCE = "```json"
CLOSING_FENCE = "```"

# The sections, named as each Problem names them.
PROVENANCE = "provenance"
ISSUE_KINDS = "issue_kinds"
ISSUE_PRIORITIES = "issue_priorities"
LABEL_AXES = "issue_label_schema.axes"
UNAXED_LABELS = "issue_label_schema.labels"
ISSUE_STATES = "issue_states"
SECTIONS = (PROVENANCE, ISSUE_KINDS, ISSUE_PRIORITIES, LABEL_AXES,
            UNAXED_LABELS, ISSUE_STATES)

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
    """The file as a whole cannot be read: no block can be found by the
    delimiting rule, or its JSON does not parse."""


class UnusableSectionError(TrackerSchemaError):
    """A caller asked for a section the reader could not use. `section` names
    it and `problems` says why."""

    def __init__(self, section: str, problems: Tuple["Problem", ...]):
        self.section = section
        self.problems = problems
        reasons = "; ".join(f"{p.where}: {p.message}" for p in problems)
        super().__init__(
            f"the Tracker Schema's {section} cannot be used: {reasons}"
        )


@dataclass(frozen=True)
class Problem:
    """One thing the reader left out, ignored, or could not use.

    `section` is one of SECTIONS, or None for the block as a whole; `where`
    is the key path at fault; `message` says what is wrong and what was done
    about it."""

    section: Optional[str]
    where: str
    message: str


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
    meaning: Optional[str]  # None when the file's meaning is missing or bad


@dataclass(frozen=True)
class IssuePriority:
    name: str
    meaning: Optional[str]
    stale_after_days: Optional[int]  # None when missing or bad


@dataclass(frozen=True)
class IssueLabel:
    """A declared Issue Label, its name written in full as on an Issue."""

    name: str
    meaning: Optional[str]


@dataclass(frozen=True)
class LabelAxis:
    """An axis of the Issue Label Schema. `required` is the file's
    `every_issue_carries_at_least_one`, None when missing or bad."""

    name: str
    prefix: str
    meaning: Optional[str]
    required: Optional[bool]
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
        return _by_name(self.all_labels(), name)

    def axis(self, name: str) -> Optional[LabelAxis]:
        """The axis with this name, or None."""
        return _by_name(self.axes, name)

    def axis_of(self, label_name: str) -> Optional[LabelAxis]:
        """The axis whose prefix the label name begins with, or None. This
        answers by prefix, so it also places a label the axis does not list.
        No two prefixes overlap in a usable axes section, so the answer does
        not depend on the order of the axes."""
        for candidate in self.axes:
            if label_name.startswith(candidate.prefix):
                return candidate
        return None


@dataclass(frozen=True)
class IssueState:
    name: str
    open: Optional[bool]  # None when the file's flag is missing or bad


@dataclass(frozen=True)
class TrackerSchema:
    """What the reader could use of a Tracker Schema, and what it could not.

    Each section is a property that raises UnusableSectionError when the
    section is unusable. Every collection is a tuple in file order, and the
    priorities run from highest to lowest."""

    problems: Tuple[Problem, ...]
    _sections: Dict[str, object] = field(repr=False)

    def usable(self, section: str) -> bool:
        return self._sections.get(section) is not None

    def problems_in(self, section: Optional[str]) -> Tuple[Problem, ...]:
        return tuple(p for p in self.problems if p.section == section)

    def _section(self, section: str):
        value = self._sections.get(section)
        if value is None:
            raise UnusableSectionError(section, self.problems_in(section))
        return value

    @property
    def provenance(self) -> Provenance:
        return self._section(PROVENANCE)

    @property
    def issue_kinds(self) -> Tuple[IssueKind, ...]:
        return self._section(ISSUE_KINDS)

    @property
    def issue_priorities(self) -> Tuple[IssuePriority, ...]:
        return self._section(ISSUE_PRIORITIES)

    @property
    def label_axes(self) -> Tuple[LabelAxis, ...]:
        return self._section(LABEL_AXES)

    @property
    def unaxed_labels(self) -> Tuple[IssueLabel, ...]:
        return self._section(UNAXED_LABELS)

    @property
    def issue_label_schema(self) -> IssueLabelSchema:
        """Both label sections together; unusable if either is."""
        return IssueLabelSchema(self.label_axes, self.unaxed_labels)

    @property
    def issue_states(self) -> Tuple[IssueState, ...]:
        return self._section(ISSUE_STATES)

    def kind(self, name: str) -> Optional[IssueKind]:
        return _by_name(self.issue_kinds, name)

    def priority(self, name: str) -> Optional[IssuePriority]:
        return _by_name(self.issue_priorities, name)

    def state(self, name: str) -> Optional[IssueState]:
        return _by_name(self.issue_states, name)

    @property
    def open_states(self) -> Tuple[IssueState, ...]:
        """The states the file flags open; a state with no usable flag is in
        neither this nor closed_states."""
        return tuple(state for state in self.issue_states if state.open is True)

    @property
    def closed_states(self) -> Tuple[IssueState, ...]:
        return tuple(state for state in self.issue_states if state.open is False)


def warning_lines(result: Union[TrackerSchema, TrackerSchemaError],
                  source: str = "TRACKER.md") -> Tuple[str, ...]:
    """One warning line per problem, for stderr, so every Wrapper warns about
    a Tracker Schema in the same words, whether or not the Verb needed the
    part at fault.

    `result` is what `parse` returned, or the TrackerSchemaError it raised;
    `source` names the file (the repo's TRACKER.md, say). Each line names
    the file, the section, and what is wrong; a section that cannot be used
    says so."""
    if isinstance(result, TrackerSchemaError):
        return (f"warning: {source}: {result}",)
    lines = []
    for problem in result.problems:
        if problem.section is None:
            label = "the JSON block"
        elif result.usable(problem.section):
            label = problem.section
        else:
            label = f"{problem.section} (unusable)"
        detail = (problem.message if problem.where == problem.section
                  else f"{problem.where}: {problem.message}")
        lines.append(f"warning: {source}: {label}: {detail}")
    return tuple(lines)


def load(path: Union[str, Path]) -> TrackerSchema:
    """Read and parse the Tracker Schema at `path`.

    A missing or unreadable file raises the OSError unchanged, for the caller
    to decide what it means; a file that is not UTF-8, or whose block cannot
    be read at all, raises TrackerSchemaError with the path in its message.
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
    """Read a Tracker Schema's text. Raises TrackerSchemaError only when no
    block can be found or its JSON does not parse; every other flaw is a
    Problem on the result."""
    block, first_line = _extract(text)
    try:
        document = json.loads(block, object_pairs_hook=_JsonObject.from_pairs)
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
    return _Reader().read(document)


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


class _JsonObject(dict):
    """A JSON object that remembers the keys written in it more than once.

    Keeping either value of such a key would be a guess, so the reader
    treats the key as unreadable rather than refusing the whole file."""

    duplicate_keys: frozenset = frozenset()

    @classmethod
    def from_pairs(cls, pairs: list) -> "_JsonObject":
        document, duplicates = cls(), set()
        for key, value in pairs:
            if key in document:
                duplicates.add(key)
            document[key] = value
        for key in duplicates:
            del document[key]
        document.duplicate_keys = frozenset(duplicates)
        return document


class _Reader:
    """Reads a parsed block section by section, collecting Problems."""

    def __init__(self):
        self.problems: List[Problem] = []

    def problem(self, section: Optional[str], where: str, message: str) -> None:
        self.problems.append(Problem(section, where, message))

    def read(self, document: object) -> TrackerSchema:
        sections: Dict[str, object] = {}
        top = self.fields(document, None, "", _TOP_LEVEL_KEYS)
        if top is None:
            for section in SECTIONS:
                self.problem(section, section, "absent, since the JSON block is "
                             "not an object")
            return TrackerSchema(tuple(self.problems), sections)

        sections[PROVENANCE] = self.section(top, "provenance", PROVENANCE,
                                            self.provenance)
        sections[ISSUE_KINDS] = self.section(top, "issue_kinds", ISSUE_KINDS,
                                             self.kinds)
        sections[ISSUE_PRIORITIES] = self.section(
            top, "issue_priorities", ISSUE_PRIORITIES, self.priorities
        )
        sections[ISSUE_STATES] = self.section(top, "issue_states", ISSUE_STATES,
                                              self.states)
        axes, labels = self.label_schema(top)
        sections[LABEL_AXES], sections[UNAXED_LABELS] = axes, labels
        return TrackerSchema(tuple(self.problems), sections)

    def section(self, top: dict, key: str, section: str, reader):
        if key not in top:
            self.missing(top, section, key)
            return None
        return reader(top[key])

    def missing(self, container: dict, section: str, where: str) -> None:
        written_twice = _key_of(where) in getattr(container, "duplicate_keys", ())
        self.problem(section, where, "written twice in one object, so neither "
                     "value is used" if written_twice else "missing")

    # -- objects and plain values ---------------------------------------

    def fields(self, value: object, section: Optional[str], where: str,
               keys: Tuple[str, ...]) -> Optional[dict]:
        """`value` as an object, with unknown keys reported and ignored and
        keys written twice reported and dropped; None if it is no object."""
        if not isinstance(value, dict):
            self.problem(section, where or "the JSON block", "must be a JSON "
                         f"object with the keys {', '.join(keys)}")
            return None
        for key in sorted(set(value) - set(keys)):
            self.problem(section, _at(where, key),
                         f"unknown key, ignored (this reader knows "
                         f"{', '.join(keys)})")
        for key in sorted(getattr(value, "duplicate_keys", ())):
            if key not in keys:
                self.problem(section, _at(where, key),
                             "unknown key written twice, ignored")
        return value

    def text(self, raw: dict, key: str, section: str, where: str,
             name: bool = False) -> Optional[str]:
        """A string field, or None with a Problem. A name must also hold no
        control or invisible characters, since it is matched against what a
        tracker holds."""
        at = f"{where}.{key}"
        if key not in raw:
            self.missing(raw, section, at)
            return None
        value = raw[key]
        if not isinstance(value, str) or not value or value != value.strip():
            self.problem(section, at, "must be a non-empty string with no "
                         "surrounding whitespace")
            return None
        if name and not value.isprintable():
            self.problem(section, at, "must hold no control or invisible "
                         "formatting characters (a newline or a zero-width "
                         "space, say)")
            return None
        return value

    def flag(self, raw: dict, key: str, section: str,
             where: str) -> Optional[bool]:
        at = f"{where}.{key}"
        if key not in raw:
            self.missing(raw, section, at)
            return None
        if not isinstance(raw[key], bool):
            self.problem(section, at, "must be true or false")
            return None
        return raw[key]

    def entries(self, value: object, section: str) -> Optional[list]:
        """A section's list, or None (unusable) with a Problem."""
        if not isinstance(value, list):
            self.problem(section, section, "must be a JSON list; the section "
                         "is unusable")
            return None
        return value

    def unusable_if_empty(self, items: list, section: str):
        """An empty section reads as unusable rather than as "none declared":
        no kind, priority, or state at all would make every Issue
        nonconforming, which is a broken file, not a repo's choice."""
        if not items:
            self.problem(section, section, "declares no usable entry; the "
                         "section is unusable")
            return None
        return tuple(items)

    # -- sections ---------------------------------------------------------

    def provenance(self, value: object) -> Optional[Provenance]:
        # All or nothing: provenance is used as one diff target, and a
        # repo, commit, or path read alone would point at the wrong thing.
        raw = self.fields(value, PROVENANCE, PROVENANCE, _PROVENANCE_KEYS)
        if raw is None:
            return None
        values, sound = {}, True
        for key in _PROVENANCE_KEYS:
            at = f"{PROVENANCE}.{key}"
            if key not in raw:
                self.missing(raw, PROVENANCE, at)
                sound = False
            elif raw[key] is not None and (
                    not isinstance(raw[key], str) or not raw[key]
                    or raw[key] != raw[key].strip()):
                self.problem(PROVENANCE, at, "must be a non-empty string with "
                             "no surrounding whitespace, or null")
                sound = False
            else:
                values[key] = raw[key]
        commit = values.get("source_commit")
        if commit is not None and not _FULL_COMMIT.fullmatch(commit):
            self.problem(PROVENANCE, f"{PROVENANCE}.source_commit",
                         "must be a full commit (40 or 64 lowercase hex "
                         "digits) or null")
            sound = False
        if not sound:
            self.problem(PROVENANCE, PROVENANCE, "the section is unusable, "
                         "since its fields are only meaningful together")
            return None
        return Provenance(values["source_repo"], values["source_commit"],
                          values["default_path"])

    def kinds(self, value: object) -> Optional[Tuple[IssueKind, ...]]:
        entries = self.entries(value, ISSUE_KINDS)
        if entries is None:
            return None
        kinds = []
        for position, raw in enumerate(entries):
            where = f"{ISSUE_KINDS}[{position}]"
            raw = self.fields(raw, ISSUE_KINDS, where, _KIND_KEYS)
            name = raw and self.text(raw, "name", ISSUE_KINDS, where, name=True)
            if not name:
                self.problem(ISSUE_KINDS, where, "left out, since it has no "
                             "usable name")
                continue
            kinds.append(IssueKind(name, self.text(raw, "meaning", ISSUE_KINDS,
                                                   where)))
        return self.unusable_if_empty(self.first_of_each(kinds, ISSUE_KINDS),
                                      ISSUE_KINDS)

    def priorities(self, value: object) -> Optional[Tuple[IssuePriority, ...]]:
        entries = self.entries(value, ISSUE_PRIORITIES)
        if entries is None:
            return None
        priorities = []
        for position, raw in enumerate(entries):
            where = f"{ISSUE_PRIORITIES}[{position}]"
            raw = self.fields(raw, ISSUE_PRIORITIES, where, _PRIORITY_KEYS)
            name = raw and self.text(raw, "name", ISSUE_PRIORITIES, where,
                                     name=True)
            if not name:
                # Leaving it out keeps the others' order relative to each
                # other, which is all the order means.
                self.problem(ISSUE_PRIORITIES, where, "left out, since it has "
                             "no usable name")
                continue
            priorities.append(IssuePriority(
                name, self.text(raw, "meaning", ISSUE_PRIORITIES, where),
                self.days(raw, where),
            ))
        # A name listed twice has two ranks, and which one it holds would be
        # a guess, so the order cannot be trusted at all.
        if self.duplicated(priorities, ISSUE_PRIORITIES):
            self.problem(ISSUE_PRIORITIES, ISSUE_PRIORITIES, "the section is "
                         "unusable, since a priority listed twice has no one "
                         "rank")
            return None
        return self.unusable_if_empty(priorities, ISSUE_PRIORITIES)

    def days(self, raw: dict, where: str) -> Optional[int]:
        at = f"{where}.stale_after_days"
        if "stale_after_days" not in raw:
            self.missing(raw, ISSUE_PRIORITIES, at)
            return None
        days = raw["stale_after_days"]
        if (isinstance(days, bool) or not isinstance(days, int)
                or not 1 <= days <= _MAX_STALE_DAYS):
            self.problem(ISSUE_PRIORITIES, at, "must be a whole number of "
                         f"days, from 1 to {_MAX_STALE_DAYS}")
            return None
        return days

    def states(self, value: object) -> Optional[Tuple[IssueState, ...]]:
        entries = self.entries(value, ISSUE_STATES)
        if entries is None:
            return None
        states = []
        for position, raw in enumerate(entries):
            where = f"{ISSUE_STATES}[{position}]"
            raw = self.fields(raw, ISSUE_STATES, where, _STATE_KEYS)
            name = raw and self.text(raw, "name", ISSUE_STATES, where, name=True)
            if not name:
                self.problem(ISSUE_STATES, where, "left out, since it has no "
                             "usable name")
                continue
            states.append(IssueState(name, self.flag(raw, "open", ISSUE_STATES,
                                                     where)))
        # A state listed twice with opposite flags leaves open-or-closed a
        # guess for every Issue in it, so the section is unusable; listed
        # twice the same way, the second adds nothing and is dropped.
        flags: Dict[str, set] = {}
        for state in states:
            flags.setdefault(_folded(state.name), set()).add(state.open)
        if any({True, False} <= seen for seen in flags.values()):
            self.duplicated(states, ISSUE_STATES)
            self.problem(ISSUE_STATES, ISSUE_STATES, "the section is unusable, "
                         "since a state listed twice is flagged both open and "
                         "closed")
            return None
        states = self.first_of_each(states, ISSUE_STATES)
        if states and not any(state.open is True for state in states):
            self.problem(ISSUE_STATES, ISSUE_STATES, "no state is flagged open")
        if states and not any(state.open is False for state in states):
            self.problem(ISSUE_STATES, ISSUE_STATES, "no state is flagged "
                         "closed")
        return self.unusable_if_empty(states, ISSUE_STATES)

    def label_schema(self, top: dict):
        where = "issue_label_schema"
        if where not in top:
            self.missing(top, LABEL_AXES, where)
            self.missing(top, UNAXED_LABELS, where)
            return None, None
        raw = self.fields(top[where], LABEL_AXES, where, _LABEL_SCHEMA_KEYS)
        if raw is None:
            self.problem(UNAXED_LABELS, where, "absent, since "
                         "issue_label_schema is not an object")
            return None, None
        axes = self.section(raw, "axes", LABEL_AXES, self.axes)
        labels = self.section(raw, "labels", UNAXED_LABELS,
                              lambda value: self.unaxed(value, axes))
        if axes is not None and labels is not None:
            # A label declared on an axis and again among the unaxed ones:
            # keep the axis's, which is the more specific declaration.
            declared = {_folded(label.name) for axis in axes
                        for label in axis.labels}
            kept = []
            for label in labels:
                if _folded(label.name) in declared:
                    self.problem(UNAXED_LABELS, f"{UNAXED_LABELS}: {label.name!r}",
                                 "also declared on an axis; this one is ignored")
                else:
                    kept.append(label)
            labels = tuple(kept)
        return axes, labels

    def axes(self, value: object) -> Optional[Tuple[LabelAxis, ...]]:
        entries = self.entries(value, LABEL_AXES)
        if entries is None:
            return None
        axes = []
        for position, raw in enumerate(entries):
            where = f"{LABEL_AXES}[{position}]"
            raw = self.fields(raw, LABEL_AXES, where, _AXIS_KEYS)
            name = raw and self.text(raw, "name", LABEL_AXES, where, name=True)
            prefix = raw and self.text(raw, "prefix", LABEL_AXES, where,
                                       name=True)
            if not name or not prefix:
                # With no name or prefix an axis cannot classify anything.
                self.problem(LABEL_AXES, where, "left out, since it has no "
                             "usable name or prefix")
                continue
            axes.append(LabelAxis(
                name, prefix, self.text(raw, "meaning", LABEL_AXES, where),
                self.flag(raw, "every_issue_carries_at_least_one", LABEL_AXES,
                          where),
                self.axis_labels(raw, prefix, where),
            ))
        # Axes that share a name, or prefixes where one begins another, make
        # which axis a label is on depend on the order of the list, so no
        # answer about axes can be trusted.
        if self.duplicated(axes, LABEL_AXES):
            self.problem(LABEL_AXES, LABEL_AXES, "the section is unusable, "
                         "since two axes share a name")
            return None
        for first, axis in enumerate(axes):
            for other in axes[first + 1:]:
                if (_folded(axis.prefix).startswith(_folded(other.prefix))
                        or _folded(other.prefix).startswith(
                            _folded(axis.prefix))):
                    self.problem(LABEL_AXES, LABEL_AXES, "the section is "
                                 f"unusable, since the prefixes {axis.prefix!r} "
                                 f"and {other.prefix!r} overlap: no axis's "
                                 "prefix may begin another's")
                    return None
        # Labels declared on two axes cannot happen once prefixes do not
        # overlap; within one axis a label listed twice keeps its first.
        return tuple(axes)

    def axis_labels(self, raw: dict, prefix: str,
                    where: str) -> Tuple[IssueLabel, ...]:
        at = f"{where}.labels"
        if "labels" not in raw:
            self.missing(raw, LABEL_AXES, at)
            return ()
        kept = []
        for label in self.labels(raw["labels"], LABEL_AXES, at):
            if not label.name.startswith(prefix) or label.name == prefix:
                self.problem(LABEL_AXES, f"{at}: {label.name!r}", "left out: "
                             "every label on this axis is written in full, "
                             f"beginning with its prefix {prefix!r}")
            else:
                kept.append(label)
        return tuple(self.first_of_each(kept, LABEL_AXES))

    def unaxed(self, value: object,
               axes: Optional[Tuple[LabelAxis, ...]]) -> Optional[Tuple[IssueLabel, ...]]:
        if not isinstance(value, list):
            self.problem(UNAXED_LABELS, UNAXED_LABELS, "must be a JSON list; "
                         "the section is unusable")
            return None
        kept = []
        for label in self.labels(value, UNAXED_LABELS, UNAXED_LABELS):
            axis = next((axis for axis in axes or ()
                         if _folded(label.name).startswith(_folded(axis.prefix))),
                        None)
            if axis is not None:
                self.problem(UNAXED_LABELS, f"{UNAXED_LABELS}: {label.name!r}",
                             f"left out: it begins with the prefix of the "
                             f"{axis.name!r} axis, so it belongs in that axis's "
                             "labels")
            else:
                kept.append(label)
        # An empty list is a real choice here: a repo may have no label
        # outside its axes.
        return tuple(self.first_of_each(kept, UNAXED_LABELS))

    def labels(self, value: object, section: str, where: str) -> List[IssueLabel]:
        if not isinstance(value, list):
            self.problem(section, where, "must be a JSON list; its labels are "
                         "left out")
            return []
        labels = []
        for position, raw in enumerate(value):
            at = f"{where}[{position}]"
            raw = self.fields(raw, section, at, _LABEL_KEYS)
            name = raw and self.text(raw, "name", section, at, name=True)
            if not name:
                self.problem(section, at, "left out, since it has no usable "
                             "name")
                continue
            labels.append(IssueLabel(name, self.text(raw, "meaning", section,
                                                     at)))
        return labels

    # -- names --------------------------------------------------------------

    def duplicated(self, entries: list, section: str) -> bool:
        """Report every name declared twice (names that differ only in case
        count, since a tracker may match them case-insensitively, as GitHub
        does for labels); True if there was any."""
        seen: Dict[str, str] = {}
        found = False
        for entry in entries:
            key = _folded(entry.name)
            if key in seen:
                found = True
                self.problem(section, f"{section}: {entry.name!r}",
                             "declared twice" if seen[key] == entry.name else
                             f"differs from {seen[key]!r} only in case; names "
                             "must differ by more than case")
            else:
                seen[key] = entry.name
        return found

    def first_of_each(self, entries: list, section: str) -> list:
        """Keep the first entry of each name and drop the rest, reporting
        them: where order and flags do not hang on which one is kept, the
        first is as good a reading as any and the others stay usable."""
        if not self.duplicated(entries, section):
            return entries
        seen, kept = set(), []
        for entry in entries:
            if _folded(entry.name) not in seen:
                seen.add(_folded(entry.name))
                kept.append(entry)
        self.problem(section, section, "each name declared more than once "
                     "keeps its first entry; the others are ignored")
        return kept


def _key_of(where: str) -> str:
    """The last key of a key path."""
    return where.rsplit(".", 1)[-1]


def _at(where: str, key: str) -> str:
    """The key path of `key` inside the object at `where` ("" for the top)."""
    return f"{where}.{key}" if where else key


def _folded(name: str) -> str:
    return name.casefold()


def _by_name(entries: tuple, name: str):
    for entry in entries:
        if entry.name == name:
            return entry
    return None
