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

The reader degrades gracefully. A flaw in one part of the file never stops
a caller from using the parts that are sound:

  - The whole file fails, with TrackerSchemaError, only when it is unclear
    which block is meant (a marker missing or repeated, no fence or two, a
    fence never closed) or its JSON does not parse. A file that strays from
    the delimiting rule but whose block is plain to see (an indented copy of
    a marker in the prose, a fence spelled another way, a stray line beside
    the fence) is read anyway, with a Problem.
  - Otherwise `parse` always returns a TrackerSchema. Each section
    (provenance, kinds, priorities, label axes, unaxed labels, states) is
    read on its own. A section with nothing safe to read is unusable, and
    asking for it raises UnusableSectionError for that section alone; a
    caller that never asks is unaffected.
  - Within a section, a bad entry is left out and the rest kept, and so is
    every entry of a name declared in conflicting ways. A bad descriptive
    field (a meaning, a staleness threshold) reads as None. A flag a caller
    acts on (a state's open flag, an axis's required flag) is never None:
    an entry whose flag is bad is left out instead, so `if state.open:` is
    always a real answer.
  - A key the reader does not know, at any level, is ignored. A key it
    needs and does not find makes that field or section absent. So a copy
    written for a newer reader, and one written for an older reader, both
    keep everything else working.
  - Everything the reader left out, ignored, or doubted is a Problem in
    `TrackerSchema.problems`, worded so an agent can fix the file, and
    `warning_lines` turns them into the warnings every Verb prints, so a
    defect is visible even to a Verb that did not need the part at fault.

Usable is not complete. A Problem is `lossy` when the reader dropped or
doubted data the file meant to declare, and not when it only ignored an
unknown key or noticed something odd that cost nothing. `usable(section)`
says a section can be read; `complete(section)` says it can be read and
lost nothing, which is what a destructive write (a label sync deleting
labels the schema does not declare, say) needs, since a dropped entry
would otherwise read as one to delete. `require_complete` raises when it
is not.

The library reports; it makes no exit-code decisions. What a missing file,
an unusable or incomplete section, or a list of problems means for a Verb
is the caller's call, under the Exit-code contract
(docs/index.md#exit-code-contract) and the rule in
docs/projects/use-issues/design.md, "How a Wrapper uses the schema".

The ghw and fjw Verbs read the schema from the repo's default branch on the
forge and bdw from the workspace it stands in, so `parse(text)` is the main
entry; `load(path)` reads a file, for bdw and for tests.

Standard library only, Python 3.9.
"""

from __future__ import annotations

import dataclasses
import json
import re
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Dict, List, Mapping, Optional, Tuple, Union

BEGIN_MARKER = "<!-- BEGIN tracker-schema -->"
END_MARKER = "<!-- END tracker-schema -->"
OPENING_FENCE = "```json"
CLOSING_FENCE = "```"

# The sections, named by their key paths in the block.
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
# A line that opens a fenced code block in Markdown, and one that can close it.
_FENCE_OPENING = re.compile(r"(`{3,}|~{3,})")
_FENCE_CLOSING = re.compile(r"`{3,}|~{3,}")
# The longest staleness a datetime.timedelta can hold, so a caller adding it
# to a timestamp cannot overflow on a value the reader accepted.
_MAX_STALE_DAYS = timedelta.max.days

_LEFT_OUT = "; the entry is left out"
_ABSENT = "; read as absent"
_UNUSABLE = "; the section is unusable"


class TrackerSchemaError(Exception):
    """The file as a whole cannot be read: it is unclear which block is
    meant, or its JSON does not parse. `detail` says what is wrong and
    `path` is the file `load` read, if any."""

    def __init__(self, detail: str, path: Optional[Path] = None):
        self.detail = detail
        self.path = path
        super().__init__(f"{path}: {detail}" if path is not None else detail)


class SectionError(Exception):
    """A caller asked for a section in a way the reader cannot honour.
    `section` names it and `problems` says why."""

    def __init__(self, section: str, problems: Tuple["Problem", ...],
                 what: str):
        self.section = section
        self.problems = problems
        reasons = "; ".join(f"{p.where}: {p.message}" for p in problems)
        super().__init__(_printable(
            f"the Tracker Schema's {section} {what}: {reasons}"
        ))


class UnusableSectionError(SectionError):
    """The section has nothing the reader could use safely."""

    def __init__(self, section: str, problems: Tuple["Problem", ...]):
        super().__init__(section, problems, "cannot be used")


class IncompleteSectionError(SectionError):
    """The section is usable, but the reader dropped or doubted some of it,
    so it cannot back a destructive write."""

    def __init__(self, section: str, problems: Tuple["Problem", ...]):
        super().__init__(section, problems, "is incomplete")


@dataclass(frozen=True)
class Problem:
    """One thing the reader left out, ignored, or doubted.

    `section` is one of SECTIONS, or None for the file or block as a whole
    (or the `issue_label_schema` object holding two sections); `where` is
    the key path at fault, or the file line for a delimiting flaw; `message`
    says what is wrong and what was done about it. `lossy` is True when the
    reader dropped or doubted data the file meant to declare, and False when
    it lost nothing (an unknown key ignored, say)."""

    section: Optional[str]
    where: str
    message: str
    lossy: bool


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
    `every_issue_carries_at_least_one`; an axis whose flag is bad is left
    out, so it is always a real bool."""

    name: str
    prefix: str
    meaning: Optional[str]
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
        return _by_name(self.all_labels(), name)

    def axis(self, name: str) -> Optional[LabelAxis]:
        """The axis with this name, or None."""
        return _by_name(self.axes, name)

    def axis_of(self, label_name: str) -> Optional[LabelAxis]:
        """The axis whose prefix the label name begins with, or None. This
        answers by prefix, so it also places a label the axis does not list.
        No two prefixes overlap among the axes read, so the answer does not
        depend on the order of the axes."""
        for candidate in self.axes:
            if label_name.startswith(candidate.prefix):
                return candidate
        return None


@dataclass(frozen=True)
class IssueState:
    """An Issue State. A state whose open flag is bad is left out, so `open`
    is always a real bool."""

    name: str
    open: bool


@dataclass(frozen=True)
class TrackerSchema:
    """What the reader could use of a Tracker Schema, and what it could not.

    Each section is a property that raises UnusableSectionError when the
    section is unusable. Every collection is a tuple in file order, and the
    priorities run from highest to lowest. A destructive write calls
    `require_complete` on every section it derives from first."""

    problems: Tuple[Problem, ...]
    _sections: Mapping[str, object] = field(repr=False, hash=False)

    def usable(self, section: str) -> bool:
        """True if the section can be read, perhaps with entries left out."""
        return self._sections.get(_known(section)) is not None

    def complete(self, section: str) -> bool:
        """True if the section can be read and the reader lost nothing of
        it: no entry or field dropped or doubted. Only a complete section
        may back a destructive write."""
        return self.usable(section) and not self._lossy(section)

    def require_complete(self, *sections: str) -> None:
        """Raise UnusableSectionError or IncompleteSectionError for the
        first of `sections` that is not complete."""
        for section in sections:
            self._section(section)
            lossy = self._lossy(section)
            if lossy:
                raise IncompleteSectionError(section, lossy)

    def problems_in(self, section: Optional[str]) -> Tuple[Problem, ...]:
        """The problems filed under `section`, or under the block as a whole
        for None."""
        if section is not None:
            _known(section)
        return tuple(p for p in self.problems if p.section == section)

    def _lossy(self, section: str) -> Tuple[Problem, ...]:
        return tuple(p for p in self.problems_in(section) if p.lossy)

    def _section(self, section: str):
        value = self._sections.get(_known(section))
        if value is None:
            # A section lost to a flaw above it (a block that is not an
            # object, say) has no problem of its own; that flaw is the why.
            raise UnusableSectionError(section, self.problems_in(section) or tuple(
                p for p in self.problems if p.section is None and p.lossy
            ))
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
        return tuple(state for state in self.issue_states if state.open)

    @property
    def closed_states(self) -> Tuple[IssueState, ...]:
        return tuple(state for state in self.issue_states if not state.open)


def warning_lines(result: Union[TrackerSchema, TrackerSchemaError],
                  source: str = "TRACKER.md") -> Tuple[str, ...]:
    """One warning line per problem, for stderr, so every Wrapper warns about
    a Tracker Schema in the same words, whether or not the Verb needed the
    part at fault.

    `result` is what `parse` or `load` returned, or the TrackerSchemaError
    it raised; `source` names the file (the repo's TRACKER.md, say), and
    replaces the path a `load` error carries. Each line names the file, the
    key path at fault (which begins with the section), and what is wrong and
    what was done about it. Nothing from the file reaches a line unescaped,
    so a line is always one printable line."""
    if isinstance(result, TrackerSchemaError):
        return (_printable(f"warning: {source}: {result.detail}"),)
    return tuple(_printable(f"warning: {source}: {p.where}: {p.message}")
                 for p in result.problems)


def load(path: Union[str, Path]) -> TrackerSchema:
    """Read and parse the Tracker Schema at `path`.

    A missing or unreadable file raises the OSError unchanged, for the caller
    to decide what it means; a file that is not UTF-8, or whose block cannot
    be read at all, raises TrackerSchemaError carrying the path.
    """
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise TrackerSchemaError(f"not UTF-8 text ({error.reason})", path)
    try:
        return parse(text)
    except TrackerSchemaError as error:
        raise TrackerSchemaError(error.detail, path) from None


def parse(text: str) -> TrackerSchema:
    """Read a Tracker Schema's text. Raises TrackerSchemaError only when it
    is unclear which block is meant or its JSON does not parse; every other
    flaw is a Problem on the result."""
    block, first_line, problems = _extract(text)
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
    return _Reader(problems).read(document)


def extract_block(text: str) -> str:
    """The text inside the JSON block's fence, unparsed, with "\\n" line
    endings whatever the file uses. Tolerates what `parse` tolerates, and
    raises TrackerSchemaError where it does."""
    return _extract(text)[0]


def _extract(text: str) -> Tuple[str, int, List[Problem]]:
    """The block's text, the file line number of its first line, and the
    problems with how it is delimited."""
    lines = [line[:-1] if line.endswith("\r") else line
             for line in text.split("\n")]
    problems: List[Problem] = []

    def strayed(number: int, message: str) -> None:
        problems.append(Problem(None, f"line {number}", message, False))

    begins, ends = [], []
    for number, line in enumerate(lines, start=1):
        trimmed = line.rstrip()
        if trimmed == BEGIN_MARKER:
            begins.append(number)
        elif trimmed == END_MARKER:
            ends.append(number)
        elif trimmed.strip() in (BEGIN_MARKER, END_MARKER):
            # Indentation makes a line a code block or part of a list item
            # in Markdown, so this is an example, not the marker.
            strayed(number, "an indented marker line is not a marker, so it "
                    "is ignored; keep any example of a marker off a line of "
                    "its own")
    for marker, found in ((BEGIN_MARKER, begins), (END_MARKER, ends)):
        if not found:
            raise TrackerSchemaError(
                f"no {marker} line: the JSON block must sit between "
                f"{BEGIN_MARKER} and {END_MARKER}, each alone on its line"
            )
        if len(found) > 1:
            raise TrackerSchemaError(
                f"{marker} appears on {len(found)} lines "
                f"({', '.join(str(n) for n in found)}), so which block is "
                "meant is unclear; the file must have exactly one. Keep any "
                "example of it off a line of its own"
            )
    begin, end = begins[0], ends[0]
    if end < begin:
        raise TrackerSchemaError(
            f"{END_MARKER} (line {end}) comes before {BEGIN_MARKER} "
            f"(line {begin})"
        )

    fences: List[Tuple[int, int]] = []
    stray: List[int] = []
    opening = None
    for number in range(begin + 1, end):
        trimmed = lines[number - 1].strip()
        if opening is not None:
            if _FENCE_CLOSING.fullmatch(trimmed):
                fences.append((opening, number))
                opening = None
        elif _FENCE_OPENING.match(trimmed):
            opening = number
        elif trimmed:
            stray.append(number)
    if opening is not None:
        raise TrackerSchemaError(
            f"the fence opened on line {opening} is not closed before "
            f"{END_MARKER} (line {end})"
        )
    if not fences:
        raise TrackerSchemaError(
            f"no fenced block between {BEGIN_MARKER} (line {begin}) and "
            f"{END_MARKER} (line {end}); the JSON goes in one {OPENING_FENCE} "
            "fence there"
        )
    if len(fences) > 1:
        raise TrackerSchemaError(
            f"fenced blocks open on lines {', '.join(str(o) for o, _ in fences)} "
            "between the markers, so which one is the schema is unclear; there "
            "must be exactly one, and other code blocks belong outside the "
            "markers"
        )
    opening, closing = fences[0]
    for number in stray:
        strayed(number, "ignored: only blank lines belong between a marker "
                "and the fence")
    if lines[opening - 1].rstrip() != OPENING_FENCE:
        strayed(opening, f"read as the opening fence, though the rule asks "
                f"for a line that is exactly {OPENING_FENCE}")
    if lines[closing - 1].rstrip() != CLOSING_FENCE:
        strayed(closing, f"read as the closing fence, though the rule asks "
                f"for a line that is exactly {CLOSING_FENCE}")
    return "\n".join(lines[opening:closing - 1]), opening + 1, problems


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

    def __init__(self, problems: List[Problem]):
        self.problems: List[Problem] = list(problems)

    def problem(self, section: Optional[str], where: str, message: str,
                lossy: bool = True) -> None:
        self.problems.append(Problem(section, where, message, lossy))

    def read(self, document: object) -> TrackerSchema:
        sections: Dict[str, object] = {}
        top = self.fields(document, None, "", _TOP_LEVEL_KEYS,
                          then="; no section is usable")
        if top is not None:
            sections[PROVENANCE] = self.section(top, "provenance", PROVENANCE,
                                                self.provenance)
            sections[ISSUE_KINDS] = self.section(top, "issue_kinds",
                                                 ISSUE_KINDS, self.kinds)
            sections[ISSUE_PRIORITIES] = self.section(
                top, "issue_priorities", ISSUE_PRIORITIES, self.priorities
            )
            sections[LABEL_AXES], sections[UNAXED_LABELS] = (
                self.label_schema(top)
            )
            sections[ISSUE_STATES] = self.section(top, "issue_states",
                                                  ISSUE_STATES, self.states)
        return TrackerSchema(tuple(self.problems), MappingProxyType(sections))

    def section(self, container: dict, key: str, section: str, reader):
        if key not in container:
            self.missing(container, section, section, then=_UNUSABLE)
            return None
        return reader(container[key])

    def missing(self, container: dict, section: Optional[str], where: str,
                then: str = "") -> None:
        written_twice = _key_of(where) in getattr(container, "duplicate_keys", ())
        self.problem(section, where, ("written twice in one object, so neither "
                                      "value is used" if written_twice
                                      else "missing") + then)

    # -- objects and plain values ---------------------------------------

    def fields(self, value: object, section: Optional[str], where: str,
               keys: Tuple[str, ...], then: str) -> Optional[dict]:
        """`value` as an object, with unknown keys reported and ignored and
        keys written twice reported and dropped; None if it is no object."""
        if not isinstance(value, dict):
            self.problem(section, where or "the JSON block", "must be a JSON "
                         f"object with the keys {', '.join(keys)}{then}")
            return None
        unknown = sorted(set(value) - set(keys)) + sorted(
            key for key in getattr(value, "duplicate_keys", ()) if key not in keys
        )
        for key in unknown:
            # Losing nothing the reader knows of: the file may be written
            # for a newer reader.
            self.problem(section, _at(where, key), "unknown key, ignored (this "
                         f"reader knows {', '.join(keys)}; the file may be "
                         "newer than the tool reading it)", lossy=False)
        return value

    def text(self, raw: dict, key: str, section: str, where: str, then: str,
             name: bool = False) -> Optional[str]:
        """A string field, or None with a Problem. A name must also hold no
        control or invisible characters, since it is matched against what a
        tracker holds."""
        at = f"{where}.{key}"
        if key not in raw:
            self.missing(raw, section, at, then)
            return None
        value = raw[key]
        if not isinstance(value, str) or not value or value != value.strip():
            self.problem(section, at, "must be a non-empty string with no "
                         f"surrounding whitespace{then}")
            return None
        if name and not value.isprintable():
            self.problem(section, at, "must hold no control or invisible "
                         "formatting characters (a newline or a zero-width "
                         f"space, say){then}")
            return None
        return value

    def flag(self, raw: dict, key: str, section: str, where: str,
             then: str) -> Optional[bool]:
        at = f"{where}.{key}"
        if key not in raw:
            self.missing(raw, section, at, then)
            return None
        if not isinstance(raw[key], bool):
            self.problem(section, at, f"must be true or false{then}")
            return None
        return raw[key]

    def entry(self, value: object, section: str, where: str,
              keys: Tuple[str, ...]) -> Tuple[Optional[dict], Optional[str]]:
        """An entry of a list, and its name; the name is None, with a
        Problem, when the entry is left out for want of one."""
        raw = self.fields(value, section, where, keys, then=_LEFT_OUT)
        if raw is None:
            return None, None
        return raw, self.text(raw, "name", section, where, _LEFT_OUT,
                              name=True)

    def entries(self, value: object, section: str) -> Optional[list]:
        """A section's list, or None (unusable) with a Problem."""
        if not isinstance(value, list):
            self.problem(section, section, f"must be a JSON list{_UNUSABLE}")
            return None
        return value

    def unusable_if_empty(self, items: list, section: str):
        """An empty section reads as unusable rather than as "none declared":
        no kind, priority, or state at all would make every Issue
        nonconforming, which is a broken file, not a repo's choice."""
        if not items:
            self.problem(section, section, f"declares no usable entry{_UNUSABLE}")
            return None
        return tuple(items)

    # -- sections ---------------------------------------------------------

    def provenance(self, value: object) -> Optional[Provenance]:
        # All or nothing: provenance is used as one diff target, and a
        # repo, commit, or path read alone would point at the wrong thing.
        then = (f"{_UNUSABLE}, since its fields are only meaningful "
                "together")
        raw = self.fields(value, PROVENANCE, PROVENANCE, _PROVENANCE_KEYS,
                          then=then)
        if raw is None:
            return None
        values, sound = {}, True
        for key in _PROVENANCE_KEYS:
            at = f"{PROVENANCE}.{key}"
            value = raw.get(key)
            if key not in raw:
                self.missing(raw, PROVENANCE, at, then)
                sound = False
            elif value is not None and (not isinstance(value, str) or not value
                                        or value != value.strip()):
                self.problem(PROVENANCE, at, "must be a non-empty string with "
                             f"no surrounding whitespace, or null{then}")
                sound = False
            elif key == "source_commit" and value is not None and (
                    not _FULL_COMMIT.fullmatch(value)):
                self.problem(PROVENANCE, at, "must be a full commit (40 or 64 "
                             f"lowercase hex digits) or null{then}")
                sound = False
            else:
                values[key] = value
        if not sound:
            return None
        provenance = Provenance(values["source_repo"], values["source_commit"],
                                values["default_path"])
        if not provenance.is_original and not provenance.is_complete:
            # Read as written, losing nothing, but worth fixing.
            self.problem(PROVENANCE, PROVENANCE, "some fields are null and "
                         "some set: a copy sets all three and only the shipped "
                         "default sets none, so this copy has lost its "
                         "provenance", lossy=False)
        return provenance

    def kinds(self, value: object) -> Optional[Tuple[IssueKind, ...]]:
        entries = self.entries(value, ISSUE_KINDS)
        if entries is None:
            return None
        kinds = []
        for position, item in enumerate(entries):
            where = f"{ISSUE_KINDS}[{position}]"
            raw, name = self.entry(item, ISSUE_KINDS, where, _KIND_KEYS)
            if name is None:
                continue
            kinds.append(IssueKind(name, self.text(raw, "meaning", ISSUE_KINDS,
                                                   where, _ABSENT)))
        return self.unusable_if_empty(
            self.one_of_each(kinds, ISSUE_KINDS, "kind"), ISSUE_KINDS
        )

    def priorities(self, value: object) -> Optional[Tuple[IssuePriority, ...]]:
        entries = self.entries(value, ISSUE_PRIORITIES)
        if entries is None:
            return None
        priorities = []
        for position, item in enumerate(entries):
            where = f"{ISSUE_PRIORITIES}[{position}]"
            raw, name = self.entry(item, ISSUE_PRIORITIES, where,
                                   _PRIORITY_KEYS)
            if name is None:
                # Leaving it out keeps the others' order relative to each
                # other, which is all the order means.
                continue
            priorities.append(IssuePriority(
                name, self.text(raw, "meaning", ISSUE_PRIORITIES, where,
                                _ABSENT),
                self.days(raw, where),
            ))
        # A name listed twice has two ranks, and which one it holds would be
        # a guess; leaving out every entry of it keeps the rest in order.
        priorities = self.none_of_any_repeated(
            priorities, ISSUE_PRIORITIES, "priority",
            "since which rank it holds would be a guess",
        )
        return self.unusable_if_empty(priorities, ISSUE_PRIORITIES)

    def days(self, raw: dict, where: str) -> Optional[int]:
        at = f"{where}.stale_after_days"
        if "stale_after_days" not in raw:
            self.missing(raw, ISSUE_PRIORITIES, at, _ABSENT)
            return None
        days = raw["stale_after_days"]
        if (isinstance(days, bool) or not isinstance(days, int)
                or not 1 <= days <= _MAX_STALE_DAYS):
            self.problem(ISSUE_PRIORITIES, at, "must be a whole number of "
                         f"days, from 1 to {_MAX_STALE_DAYS}{_ABSENT}")
            return None
        return days

    def states(self, value: object) -> Optional[Tuple[IssueState, ...]]:
        entries = self.entries(value, ISSUE_STATES)
        if entries is None:
            return None
        states = []
        for position, item in enumerate(entries):
            where = f"{ISSUE_STATES}[{position}]"
            raw, name = self.entry(item, ISSUE_STATES, where, _STATE_KEYS)
            if name is None:
                continue
            # A state with no usable flag is left out rather than kept with
            # None, so no caller can read an unknown flag as closed.
            flag = self.flag(raw, "open", ISSUE_STATES, where,
                             f"{_LEFT_OUT}, since whether its Issues are "
                             "open would be a guess")
            if flag is not None:
                states.append(IssueState(name, flag))
        # Listed twice the same way, the second adds nothing; listed twice
        # with opposite flags, whether its Issues are open would be a guess.
        kept = []
        for group in _groups(states):
            if len(group) == 1:
                kept.append(group[0])
            elif len({state.open for state in group}) > 1:
                self.problem(ISSUE_STATES, ISSUE_STATES,
                             f"{_declared(group, 'state')}; it is flagged "
                             "both open and closed, so every entry of it is "
                             "left out")
            else:
                self.problem(ISSUE_STATES, ISSUE_STATES,
                             f"{_declared(group, 'state')}; the first entry "
                             "is kept and the others ignored")
                kept.append(group[0])
        if kept and not any(state.open for state in kept):
            self.problem(ISSUE_STATES, ISSUE_STATES, "no state is flagged "
                         "open", lossy=False)
        if kept and all(state.open for state in kept):
            self.problem(ISSUE_STATES, ISSUE_STATES, "no state is flagged "
                         "closed", lossy=False)
        return self.unusable_if_empty(kept, ISSUE_STATES)

    def label_schema(self, top: dict):
        key = "issue_label_schema"
        both = "; the label axes and unaxed labels are unusable"
        if key not in top:
            self.missing(top, None, key, both)
            return None, None
        raw = self.fields(top[key], None, key, _LABEL_SCHEMA_KEYS, then=both)
        if raw is None:
            return None, None
        axes, prefixes, all_known = None, (), False
        if "axes" not in raw:
            self.missing(raw, LABEL_AXES, LABEL_AXES, _UNUSABLE)
        else:
            axes, prefixes, all_known = self.axes(raw["axes"])
        if "labels" not in raw:
            self.missing(raw, UNAXED_LABELS, UNAXED_LABELS, _UNUSABLE)
            return axes, None
        return axes, self.unaxed(raw["labels"], axes, prefixes, all_known)

    def axes(self, value: object):
        """The axes read, every prefix the file declares that is usable as
        one (including those of axes left out, so the unaxed labels are
        still checked against them), and whether every axis had one."""
        entries = self.entries(value, LABEL_AXES)
        if entries is None:
            return None, (), False
        read: List[Tuple[int, LabelAxis]] = []
        prefixes: List[str] = []
        all_known = True
        for position, item in enumerate(entries):
            where = f"{LABEL_AXES}[{position}]"
            raw, name = self.entry(item, LABEL_AXES, where, _AXIS_KEYS)
            prefix = None if raw is None else self.text(
                raw, "prefix", LABEL_AXES, where, _LEFT_OUT, name=True
            )
            if prefix is None:
                all_known = False
                continue
            prefixes.append(prefix)
            required = self.flag(raw, "every_issue_carries_at_least_one",
                                 LABEL_AXES, where,
                                 f"{_LEFT_OUT}, since whether every Issue "
                                 "carries one of its labels would be a guess")
            if name is None or required is None:
                continue
            read.append((len(prefixes) - 1, LabelAxis(
                name, prefix,
                self.text(raw, "meaning", LABEL_AXES, where, _ABSENT),
                required, self.axis_labels(raw, prefix, where),
            )))
        # Prefixes where one begins another, or axes that share a name,
        # leave which axis a label is on a guess, so every axis involved is
        # left out; the others are kept.
        overlapping = set()
        for first, prefix in enumerate(prefixes):
            for second in range(first + 1, len(prefixes)):
                other = prefixes[second]
                if (_folded(prefix).startswith(_folded(other))
                        or _folded(other).startswith(_folded(prefix))):
                    overlapping.update((first, second))
                    self.problem(LABEL_AXES, LABEL_AXES, f"the prefixes "
                                 f"{prefix!r} and {other!r} overlap, and no "
                                 "axis's prefix may begin another's; both "
                                 "axes are left out")
        axes = self.none_of_any_repeated(
            [axis for index, axis in read if index not in overlapping],
            LABEL_AXES, "axis", "since which axis a label is on would be a "
            "guess",
        )
        return tuple(axes), tuple(prefixes), all_known

    def axis_labels(self, raw: dict, prefix: str,
                    where: str) -> Tuple[IssueLabel, ...]:
        at = f"{where}.labels"
        if "labels" not in raw:
            self.missing(raw, LABEL_AXES, at, "; the axis is read with no "
                         "labels")
            return ()
        kept = []
        for label in self.labels(raw["labels"], LABEL_AXES, at):
            if not label.name.startswith(prefix) or label.name == prefix:
                self.problem(LABEL_AXES, at, f"{label.name!r} does not begin "
                             f"with the axis's prefix {prefix!r}, as every "
                             "label on an axis is written in full; it is left "
                             "out")
            else:
                kept.append(label)
        return tuple(self.one_of_each(kept, LABEL_AXES, "label"))

    def unaxed(self, value: object, axes: Optional[Tuple[LabelAxis, ...]],
               prefixes: Tuple[str, ...],
               all_known: bool) -> Optional[Tuple[IssueLabel, ...]]:
        if not isinstance(value, list):
            self.problem(UNAXED_LABELS, UNAXED_LABELS,
                         f"must be a JSON list{_UNUSABLE}")
            return None
        kept = []
        for label in self.labels(value, UNAXED_LABELS, UNAXED_LABELS):
            prefix = next((prefix for prefix in prefixes
                           if _folded(label.name).startswith(_folded(prefix))),
                          None)
            if prefix is not None:
                self.problem(UNAXED_LABELS, UNAXED_LABELS, f"{label.name!r} "
                             f"begins with the axis prefix {prefix!r}, so it "
                             "belongs in that axis's labels; it is left out")
            else:
                kept.append(label)
        if kept and not all_known:
            # A label here may still belong on an axis whose prefix could
            # not be read, so what is kept is in doubt.
            self.problem(UNAXED_LABELS, UNAXED_LABELS, "could not be checked "
                         "against every axis's prefix, since the axes, or one "
                         "of their prefixes, could not be read; a label here "
                         "may belong on an axis")
        kept = self.one_of_each(kept, UNAXED_LABELS, "label")
        # A label declared on an axis and again among the unaxed ones: keep
        # the axis's, which is the more specific declaration.
        declared = {_folded(label.name) for axis in axes or ()
                    for label in axis.labels}
        for label in kept:
            if _folded(label.name) in declared:
                self.problem(UNAXED_LABELS, UNAXED_LABELS, f"{label.name!r} is "
                             "also declared on an axis; this one is ignored")
        # An empty list is a real choice here: a repo may have no label
        # outside its axes.
        return tuple(label for label in kept
                     if _folded(label.name) not in declared)

    def labels(self, value: object, section: str, where: str) -> List[IssueLabel]:
        if not isinstance(value, list):
            self.problem(section, where, "must be a JSON list; its labels are "
                         "left out")
            return []
        labels = []
        for position, item in enumerate(value):
            at = f"{where}[{position}]"
            raw, name = self.entry(item, section, at, _LABEL_KEYS)
            if name is not None:
                labels.append(IssueLabel(name, self.text(raw, "meaning",
                                                         section, at, _ABSENT)))
        return labels

    # -- names declared more than once -----------------------------------
    #
    # Names that differ only in case count as one, since a tracker may match
    # them case-insensitively, as GitHub does for labels.

    def one_of_each(self, entries: list, section: str, thing: str) -> list:
        """One entry of each name, where nothing hangs on which is kept: the
        first whose fields all read, else the first. Each name declared
        more than once is reported."""
        kept = []
        for group in _groups(entries):
            if len(group) > 1:
                self.problem(section, section, f"{_declared(group, thing)}; "
                             "one entry is kept and the others ignored")
            kept.append(next((entry for entry in group if _sound(entry)),
                             group[0]))
        return kept

    def none_of_any_repeated(self, entries: list, section: str, thing: str,
                             why: str) -> list:
        """The entries whose names are declared once; every entry of a name
        declared more than once is left out and reported."""
        kept = []
        for group in _groups(entries):
            if len(group) > 1:
                self.problem(section, section, f"{_declared(group, thing)}; "
                             f"every entry of it is left out, {why}")
            else:
                kept.append(group[0])
        return kept


def _known(section: str) -> str:
    if section not in SECTIONS:
        raise ValueError(f"{section!r} is not a Tracker Schema section; the "
                         f"sections are {', '.join(SECTIONS)}")
    return section


def _groups(entries: list) -> List[list]:
    """The entries grouped by case-folded name, in order of first appearance."""
    groups: Dict[str, list] = {}
    for entry in entries:
        groups.setdefault(_folded(entry.name), []).append(entry)
    return list(groups.values())


def _declared(group: list, thing: str) -> str:
    """How a name declared more than once is described in a Problem."""
    names = list(dict.fromkeys(entry.name for entry in group))
    if len(names) == 1:
        return f"the {thing} {names[0]!r} is declared {len(group)} times"
    return (f"{' and '.join(repr(name) for name in names)} name one {thing}, "
            "since names that differ only in case count as one")


def _sound(entry) -> bool:
    """True if every field of the entry was read."""
    return all(getattr(entry, item.name) is not None
               for item in dataclasses.fields(entry))


def _key_of(where: str) -> str:
    """The last key of a key path."""
    return where.rsplit(".", 1)[-1]


def _at(where: str, key: str) -> str:
    """The key path of `key` inside the object at `where` ("" for the top).
    A key that is not a plain name is quoted, so a key path stays one
    printable line whatever the file holds."""
    shown = key if key.isidentifier() else repr(key)
    return f"{where}.{shown}" if where else shown


def _printable(text: str) -> str:
    """`text` with every non-printable character escaped, as repr would."""
    return "".join(character if character.isprintable()
                   else repr(character)[1:-1] for character in text)


def _folded(name: str) -> str:
    return name.casefold()


def _by_name(entries: tuple, name: str):
    for entry in entries:
        if entry.name == name:
            return entry
    return None
