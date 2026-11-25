"""Unit tests for tracker_schema.py, and the validity test for the Tracker
Schemas this repo ships and keeps: the shipped default and its own copy.

The reader degrades gracefully; the validity test is where strictness
lives: it demands that both files read with no Problem at all.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import copy
import dataclasses
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

if __package__ in (None, ""):  # direct invocation: python3 lib/tracker_schema_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import tracker_schema
from lib.tracker_schema import TrackerSchemaError, UnusableSectionError

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SHIPPED_DEFAULT = _REPO_ROOT / "skills" / "setup-issue-tracker" / "TRACKER.default.md"
_THIS_REPOS_COPY = _REPO_ROOT / "TRACKER.md"

_DOCUMENT = {
    "provenance": {
        "source_repo": None, "source_commit": None, "default_path": None,
    },
    "issue_kinds": [
        {"name": "bug", "meaning": "Something is broken"},
        {"name": "feature", "meaning": "Something new"},
    ],
    "issue_priorities": [
        {"name": "P0", "meaning": "Drop everything", "stale_after_days": 1},
        {"name": "P1", "meaning": "Next", "stale_after_days": 7},
    ],
    "issue_label_schema": {
        "axes": [
            {
                "name": "area", "prefix": "area:", "meaning": "Part concerned",
                "every_issue_carries_at_least_one": True,
                "labels": [{"name": "area:core", "meaning": "The core"}],
            },
            {
                "name": "scope", "prefix": "scope:", "meaning": "Deployment",
                "every_issue_carries_at_least_one": False,
                "labels": [],
            },
        ],
        "labels": [{"name": "human", "meaning": "Waiting on a person"}],
    },
    "issue_states": [
        {"name": "Needs Triage", "open": True},
        {"name": "Closed", "open": False},
    ],
}

_ALL_SECTIONS = set(tracker_schema.SECTIONS)


def _file(block: str, before: str = "", after: str = "") -> str:
    """A Tracker Schema's text with `block` as the lines between the markers."""
    return (
        "# Tracker Schema\n\nProse.\n\n" + before
        + "<!-- BEGIN tracker-schema -->\n" + block
        + "<!-- END tracker-schema -->\n" + after + "\n## More prose\n"
    )


def _fenced(document: object) -> str:
    return "```json\n" + json.dumps(document, indent=2) + "\n```\n"


def _with(**changes) -> dict:
    """The sample document with the top-level keys in `changes` replaced."""
    document = copy.deepcopy(_DOCUMENT)
    document.update(changes)
    return document


def _read(document: object) -> tracker_schema.TrackerSchema:
    return tracker_schema.parse(_file(_fenced(document)))


def _usable(schema: tracker_schema.TrackerSchema) -> set:
    return {section for section in tracker_schema.SECTIONS
            if schema.usable(section)}


class ExtractionTest(unittest.TestCase):
    """The delimiting rule: whole-line markers, one of each, one json fence.
    A file that fails it is the one whole-file failure, with valid JSON."""

    def _refuses(self, text: str, fragment: str) -> None:
        with self.assertRaises(TrackerSchemaError) as caught:
            tracker_schema.parse(text)
        self.assertNotIsInstance(caught.exception, UnusableSectionError)
        self.assertIn(fragment, str(caught.exception))

    def test_a_well_formed_file_reads_with_no_problem(self):
        schema = _read(_DOCUMENT)
        self.assertEqual(schema.problems, ())
        self.assertEqual(_usable(schema), _ALL_SECTIONS)
        self.assertEqual([kind.name for kind in schema.issue_kinds],
                         ["bug", "feature"])

    def test_extract_block_returns_the_lines_inside_the_fence(self):
        text = _file("\n```json\n{}\n```\n\n")
        self.assertEqual(tracker_schema.extract_block(text), "{}")

    def test_trailing_whitespace_and_crlf_still_match(self):
        text = _file(_fenced(_DOCUMENT)).replace(
            "<!-- BEGIN tracker-schema -->\n", "<!-- BEGIN tracker-schema -->  \t\n"
        ).replace(
            "<!-- END tracker-schema -->\n", "<!-- END tracker-schema --> \n"
        ).replace("```json\n", "```json \n").replace("\n```\n", "\n```\t\n")
        self.assertEqual(tracker_schema.parse(text).problems, ())
        self.assertEqual(
            tracker_schema.parse(text.replace("\n", "\r\n")).problems, ()
        )

    def test_extract_block_drops_crlf(self):
        text = _file("```json\n{\n}\n```\n").replace("\n", "\r\n")
        self.assertEqual(tracker_schema.extract_block(text), "{\n}")

    def test_a_tab_indented_marker_is_refused(self):
        text = _file(_fenced(_DOCUMENT)).replace(
            "<!-- BEGIN tracker-schema -->", "\t<!-- BEGIN tracker-schema -->"
        )
        self._refuses(text, "remove the indentation")

    def test_an_indented_example_of_a_marker_elsewhere_is_refused(self):
        text = _file(_fenced(_DOCUMENT),
                     after="An example:\n\n    <!-- END tracker-schema -->\n")
        self._refuses(text, "remove the indentation")

    def test_a_marker_inside_a_fenced_example_elsewhere_is_refused(self):
        text = _file(_fenced(_DOCUMENT),
                     after="```\n<!-- BEGIN tracker-schema -->\n```\n")
        self._refuses(text, "appears on 2 lines")

    def test_a_marker_mentioned_inside_a_line_is_not_a_marker(self):
        text = _file(
            _fenced(_DOCUMENT),
            before="Prose naming <!-- BEGIN tracker-schema --> in passing.\n",
            after="And `<!-- END tracker-schema -->` in code.\n",
        )
        self.assertEqual(tracker_schema.parse(text).problems, ())

    def test_a_missing_begin_marker_is_refused(self):
        text = _file(_fenced(_DOCUMENT)).replace(
            "<!-- BEGIN tracker-schema -->\n", ""
        )
        self._refuses(text, "no <!-- BEGIN tracker-schema --> line")

    def test_a_missing_end_marker_is_refused(self):
        text = _file(_fenced(_DOCUMENT)).replace(
            "<!-- END tracker-schema -->\n", ""
        )
        self._refuses(text, "no <!-- END tracker-schema --> line")

    def test_a_duplicated_marker_is_refused(self):
        text = _file(_fenced(_DOCUMENT),
                     after="<!-- BEGIN tracker-schema -->\n")
        self._refuses(text, "appears on 2 lines")

    def test_an_indented_marker_is_refused(self):
        text = _file(_fenced(_DOCUMENT)).replace(
            "<!-- END tracker-schema -->", "  <!-- END tracker-schema -->"
        )
        self._refuses(text, "remove the indentation")

    def test_end_before_begin_is_refused(self):
        text = ("<!-- END tracker-schema -->\n" + _fenced(_DOCUMENT)
                + "<!-- BEGIN tracker-schema -->\n")
        self._refuses(text, "comes before")

    def test_no_fence_is_refused(self):
        self._refuses(_file("\n\n"), "no fenced block")

    def test_bare_json_without_a_fence_is_refused(self):
        self._refuses(_file(json.dumps(_DOCUMENT) + "\n"),
                      "only blank lines may sit")

    def test_two_fences_are_refused(self):
        self._refuses(_file(_fenced(_DOCUMENT) + "\n" + _fenced(_DOCUMENT)),
                      "a second fenced block")

    def test_an_untagged_fence_is_refused(self):
        block = _fenced(_DOCUMENT).replace("```json", "```", 1)
        self._refuses(_file(block), "exactly ```json")

    def test_a_fence_tagged_otherwise_is_refused(self):
        block = _fenced(_DOCUMENT).replace("```json", "```jsonc", 1)
        self._refuses(_file(block), "exactly ```json")

    def test_other_spellings_of_a_json_fence_are_refused(self):
        # Each opens a json fenced block in CommonMark; the rule names one.
        for opening in ("~~~json", "````json", "``` json", "```JSON",
                        "```json title"):
            with self.subTest(opening=opening):
                block = _fenced(_DOCUMENT).replace("```json", opening, 1)
                self._refuses(_file(block), "exactly ```json")

    def test_other_closing_fences_are_refused(self):
        for closing in ("~~~", "````"):
            with self.subTest(closing=closing):
                block = _fenced(_DOCUMENT)[:-len("```\n")] + closing + "\n"
                self._refuses(_file(block), "must close with a line that is "
                              "exactly ```")

    def test_an_indented_fence_is_refused(self):
        block = _fenced(_DOCUMENT).replace("```json", "   ```json", 1)
        self._refuses(_file(block), "exactly ```json")

    def test_an_unclosed_fence_is_refused(self):
        block = _fenced(_DOCUMENT).rstrip("\n").rsplit("\n", 1)[0] + "\n"
        self._refuses(_file(block), "is not closed")

    def test_prose_after_the_fence_is_refused(self):
        self._refuses(_file(_fenced(_DOCUMENT) + "A note.\n"),
                      "only blank lines may sit")

    def test_invalid_json_is_refused_with_its_file_line(self):
        text = _file('```json\n{\n  "provenance": ,\n}\n```\n')
        # The block's second line is the file's: the BEGIN marker is line 5
        # and the fence line 6, so the bad line is 8.
        self._refuses(text, "does not parse (line 8,")

    def test_json_nested_too_deeply_is_refused(self):
        block = "```json\n" + "[" * 100000 + "\n```\n"
        self._refuses(_file(block), "nests too deeply")


class DegradationTest(unittest.TestCase):
    """A flaw in one part of the block leaves every other part usable."""

    def _problem(self, schema, section, fragment: str) -> None:
        messages = [f"{p.where}: {p.message}" for p in schema.problems_in(section)]
        self.assertTrue(any(fragment in message for message in messages),
                        f"no problem in {section} mentions {fragment!r}: "
                        f"{messages}")

    def _only_unusable(self, schema, *sections) -> None:
        self.assertEqual(_usable(schema), _ALL_SECTIONS - set(sections))
        for section in sections:
            with self.assertRaises(UnusableSectionError) as caught:
                getattr(schema, {
                    tracker_schema.PROVENANCE: "provenance",
                    tracker_schema.ISSUE_KINDS: "issue_kinds",
                    tracker_schema.ISSUE_PRIORITIES: "issue_priorities",
                    tracker_schema.LABEL_AXES: "label_axes",
                    tracker_schema.UNAXED_LABELS: "unaxed_labels",
                    tracker_schema.ISSUE_STATES: "issue_states",
                }[section])
            self.assertEqual(caught.exception.section, section)
            self.assertTrue(caught.exception.problems)

    # -- keys the reader does not know, and keys it lacks --------------

    def test_an_unknown_top_level_key_is_ignored_and_reported(self):
        schema = _read(_with(entry_state="Needs Triage"))
        self.assertEqual(_usable(schema), _ALL_SECTIONS)
        self._problem(schema, None, "entry_state: unknown key, ignored")

    def test_an_unknown_nested_key_is_ignored_and_reported(self):
        kinds = [{"name": "bug", "meaning": "Broken", "color": "d73a4a"}]
        schema = _read(_with(issue_kinds=kinds))
        self.assertEqual(schema.kind("bug").meaning, "Broken")
        self._problem(schema, tracker_schema.ISSUE_KINDS,
                      "issue_kinds[0].color: unknown key, ignored")

    def test_a_newer_copy_keeps_working_with_this_reader(self):
        # A copy written for a later reader: new top-level keys, and a new
        # key on entries this reader already knows.
        document = _with(entry_state="Needs Triage",
                         close_reasons=[{"name": "done"}])
        document["issue_states"][0]["order"] = 1
        schema = _read(document)
        self.assertEqual(_usable(schema), _ALL_SECTIONS)
        self.assertEqual([s.name for s in schema.open_states], ["Needs Triage"])
        self.assertTrue(all("unknown key, ignored" in p.message
                            for p in schema.problems))

    def test_an_older_copy_keeps_working_with_this_reader(self):
        # A copy written before a section or a field existed: what it lacks
        # is absent, and the rest reads as usual.
        document = copy.deepcopy(_DOCUMENT)
        del document["issue_label_schema"]
        del document["issue_priorities"][1]["stale_after_days"]
        schema = _read(document)
        self._only_unusable(schema, tracker_schema.LABEL_AXES,
                            tracker_schema.UNAXED_LABELS)
        self.assertEqual(schema.priority("P1").stale_after_days, None)
        self.assertEqual(schema.priority("P0").stale_after_days, 1)
        self._problem(schema, tracker_schema.ISSUE_PRIORITIES,
                      "issue_priorities[1].stale_after_days: missing")

    def test_a_missing_section_is_unusable_alone(self):
        document = copy.deepcopy(_DOCUMENT)
        del document["issue_states"]
        schema = _read(document)
        self._only_unusable(schema, tracker_schema.ISSUE_STATES)
        self._problem(schema, tracker_schema.ISSUE_STATES, "missing")
        self.assertEqual(schema.kind("bug").name, "bug")

    def test_a_block_that_is_no_object_leaves_every_section_unusable(self):
        schema = _read([])
        self.assertEqual(_usable(schema), set())
        self._problem(schema, None, "must be a JSON object")

    def test_a_section_key_written_twice_is_unusable_alone(self):
        block = ('```json\n{"issue_kinds": [], "issue_kinds": [],'
                 + _fenced(_DOCUMENT)[len("```json\n{"):])
        document_text = _file(block)
        schema = tracker_schema.parse(document_text)
        self._only_unusable(schema, tracker_schema.ISSUE_KINDS)
        self._problem(schema, tracker_schema.ISSUE_KINDS, "written twice")

    # -- one broken section --------------------------------------------

    def test_one_broken_section_leaves_the_others_usable(self):
        schema = _read(_with(issue_priorities="P0, P1"))
        self._only_unusable(schema, tracker_schema.ISSUE_PRIORITIES)
        self._problem(schema, tracker_schema.ISSUE_PRIORITIES,
                      "must be a JSON list")
        self.assertEqual(len(schema.issue_states), 2)
        self.assertEqual(schema.issue_label_schema.label("human").name, "human")

    def test_an_empty_list_is_unusable(self):
        schema = _read(_with(issue_kinds=[]))
        self._only_unusable(schema, tracker_schema.ISSUE_KINDS)
        self._problem(schema, tracker_schema.ISSUE_KINDS, "declares no usable")

    # -- a bad entry inside a list ---------------------------------------

    def test_a_bad_entry_is_left_out_and_the_rest_kept(self):
        kinds = [{"name": "bug", "meaning": "Broken"}, {"meaning": "No name"},
                 "feature", {"name": "chore", "meaning": "Upkeep"}]
        schema = _read(_with(issue_kinds=kinds))
        self.assertEqual([k.name for k in schema.issue_kinds], ["bug", "chore"])
        self._problem(schema, tracker_schema.ISSUE_KINDS,
                      "issue_kinds[1].name: missing")
        self._problem(schema, tracker_schema.ISSUE_KINDS,
                      "issue_kinds[2]: must be a JSON object")

    def test_a_bad_field_on_a_named_entry_reads_as_none(self):
        schema = _read(_with(
            issue_kinds=[{"name": "bug", "meaning": " "}],
            issue_states=[{"name": "Open", "open": "yes"},
                          {"name": "Closed", "open": False}],
        ))
        self.assertIsNone(schema.kind("bug").meaning)
        self.assertIsNone(schema.state("Open").open)
        self.assertEqual(schema.open_states, ())
        self.assertEqual([s.name for s in schema.closed_states], ["Closed"])
        self._problem(schema, tracker_schema.ISSUE_STATES,
                      "issue_states[0].open: must be true or false")
        self._problem(schema, tracker_schema.ISSUE_STATES,
                      "no state is flagged open")

    def test_a_name_with_a_control_or_invisible_character_is_left_out(self):
        for name in ("b\nug", chr(0x200B)):  # a newline; a zero-width space
            with self.subTest(name=name):
                schema = _read(_with(issue_kinds=[
                    {"name": name, "meaning": "x"}, {"name": "ok", "meaning": "y"}
                ]))
                self.assertEqual([k.name for k in schema.issue_kinds], ["ok"])
                self._problem(schema, tracker_schema.ISSUE_KINDS,
                              "must hold no control")

    def test_staleness_out_of_range_reads_as_none(self):
        for days in (0, 1.5, "7", True, 10 ** 500):
            with self.subTest(days=days):
                schema = _read(_with(issue_priorities=[
                    {"name": "P0", "meaning": "Now", "stale_after_days": days}
                ]))
                self.assertIsNone(schema.priority("P0").stale_after_days)
                self._problem(schema, tracker_schema.ISSUE_PRIORITIES,
                              "must be a whole number of days")

    def test_a_bad_priority_entry_keeps_the_others_in_order(self):
        schema = _read(_with(issue_priorities=[
            {"name": "P0", "meaning": "a", "stale_after_days": 1},
            {"name": "", "meaning": "b", "stale_after_days": 2},
            {"name": "P2", "meaning": "c", "stale_after_days": 3},
        ]))
        self.assertEqual([p.name for p in schema.issue_priorities], ["P0", "P2"])

    def test_an_axis_label_without_its_prefix_is_left_out(self):
        label_schema = copy.deepcopy(_DOCUMENT["issue_label_schema"])
        label_schema["axes"][0]["labels"].append({"name": "core", "meaning": "x"})
        schema = _read(_with(issue_label_schema=label_schema))
        self.assertEqual([l.name for l in schema.label_axes[0].labels],
                         ["area:core"])
        self._problem(schema, tracker_schema.LABEL_AXES,
                      "beginning with its prefix 'area:'")

    def test_an_unaxed_label_with_an_axis_prefix_is_left_out(self):
        label_schema = copy.deepcopy(_DOCUMENT["issue_label_schema"])
        label_schema["labels"].append({"name": "area:docs", "meaning": "Docs"})
        schema = _read(_with(issue_label_schema=label_schema))
        self.assertEqual([l.name for l in schema.unaxed_labels], ["human"])
        self._problem(schema, tracker_schema.UNAXED_LABELS,
                      "belongs in that axis's labels")

    def test_an_axis_with_a_bad_required_flag_keeps_its_labels(self):
        label_schema = copy.deepcopy(_DOCUMENT["issue_label_schema"])
        label_schema["axes"][0]["every_issue_carries_at_least_one"] = "yes"
        schema = _read(_with(issue_label_schema=label_schema))
        area = schema.issue_label_schema.axis("area")
        self.assertIsNone(area.required)
        self.assertEqual([l.name for l in area.labels], ["area:core"])

    # -- names declared twice ----------------------------------------------

    def test_a_kind_or_label_declared_twice_keeps_its_first(self):
        schema = _read(_with(issue_kinds=[
            {"name": "Feature", "meaning": "first"},
            {"name": "feature", "meaning": "second"},
            {"name": "bug", "meaning": "b"},
        ]))
        self.assertEqual([(k.name, k.meaning) for k in schema.issue_kinds],
                         [("Feature", "first"), ("bug", "b")])
        self._problem(schema, tracker_schema.ISSUE_KINDS,
                      "differs from 'Feature' only in case")
        label_schema = copy.deepcopy(_DOCUMENT["issue_label_schema"])
        label_schema["labels"].append({"name": "Human", "meaning": "x"})
        label_schema["axes"][0]["labels"].append(
            {"name": "area:core", "meaning": "again"}
        )
        schema = _read(_with(issue_label_schema=label_schema))
        self.assertEqual([l.name for l in schema.unaxed_labels], ["human"])
        self.assertEqual(schema.issue_label_schema.label("area:core").meaning,
                         "The core")
        self._problem(schema, tracker_schema.LABEL_AXES,
                      "'area:core': declared twice")

    def test_a_priority_declared_twice_makes_priorities_unusable(self):
        priority = {"name": "P0", "meaning": "Now", "stale_after_days": 1}
        schema = _read(_with(issue_priorities=[priority, priority]))
        self._only_unusable(schema, tracker_schema.ISSUE_PRIORITIES)
        self._problem(schema, tracker_schema.ISSUE_PRIORITIES, "no one rank")

    def test_a_state_listed_twice(self):
        same = _read(_with(issue_states=[
            {"name": "Open", "open": True}, {"name": "Open", "open": True},
            {"name": "Closed", "open": False},
        ]))
        self.assertEqual([s.name for s in same.issue_states], ["Open", "Closed"])
        opposite = _read(_with(issue_states=[
            {"name": "Open", "open": True}, {"name": "open", "open": False},
        ]))
        self._only_unusable(opposite, tracker_schema.ISSUE_STATES)
        self._problem(opposite, tracker_schema.ISSUE_STATES,
                      "flagged both open and closed")

    def test_overlapping_axis_prefixes_make_axes_unusable(self):
        for prefix in ("area:", "a", "area:sub:", "AREA:"):
            with self.subTest(prefix=prefix):
                label_schema = copy.deepcopy(_DOCUMENT["issue_label_schema"])
                label_schema["axes"][1]["prefix"] = prefix
                label_schema["axes"][1]["labels"] = []
                schema = _read(_with(issue_label_schema=label_schema))
                self._only_unusable(schema, tracker_schema.LABEL_AXES)
                self._problem(schema, tracker_schema.LABEL_AXES,
                              f"the prefixes 'area:' and {prefix!r} overlap")
                self.assertEqual([l.name for l in schema.unaxed_labels],
                                 ["human"])

    def test_bad_provenance_is_unusable_as_a_whole(self):
        for provenance in (
            {"source_repo": 7, "source_commit": None, "default_path": None},
            {"source_repo": "o/r", "source_commit": "4f8a840",
             "default_path": "T.md"},
            {"source_repo": "o/r", "source_commit": "a" * 40},
        ):
            with self.subTest(provenance=provenance):
                schema = _read(_with(provenance=provenance))
                self._only_unusable(schema, tracker_schema.PROVENANCE)


class WarningLinesTest(unittest.TestCase):

    def test_no_problem_means_no_warning(self):
        self.assertEqual(tracker_schema.warning_lines(_read(_DOCUMENT)), ())

    def test_one_line_per_problem_naming_file_section_and_fault(self):
        document = _with(entry_state="x")
        del document["issue_states"]
        document["issue_kinds"][0]["meaning"] = ""
        lines = tracker_schema.warning_lines(_read(document))
        self.assertEqual(lines, (
            "warning: TRACKER.md: the JSON block: entry_state: unknown key, "
            "ignored (this reader knows provenance, issue_kinds, "
            "issue_priorities, issue_label_schema, issue_states)",
            "warning: TRACKER.md: issue_kinds: issue_kinds[0].meaning: must be "
            "a non-empty string with no surrounding whitespace",
            "warning: TRACKER.md: issue_states (unusable): missing",
        ))

    def test_a_whole_file_failure_is_one_warning(self):
        try:
            tracker_schema.parse("no block\n")
        except TrackerSchemaError as error:
            lines = tracker_schema.warning_lines(error, "owner/repo TRACKER.md")
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith(
            "warning: owner/repo TRACKER.md: no <!-- BEGIN"))


class AccessorTest(unittest.TestCase):

    def setUp(self):
        self.schema = _read(_DOCUMENT)

    def test_kinds_and_lookup(self):
        self.assertEqual(self.schema.kind("bug").meaning, "Something is broken")
        self.assertIsNone(self.schema.kind("chore"))

    def test_priorities_keep_their_order_and_staleness(self):
        self.assertEqual(
            [(p.name, p.stale_after_days) for p in self.schema.issue_priorities],
            [("P0", 1), ("P1", 7)],
        )
        self.assertEqual(self.schema.priority("P1").meaning, "Next")

    def test_label_schema(self):
        labels = self.schema.issue_label_schema
        area = labels.axis("area")
        self.assertEqual((area.prefix, area.required), ("area:", True))
        self.assertFalse(labels.axis("scope").required)
        self.assertEqual([label.name for label in labels.all_labels()],
                         ["area:core", "human"])
        self.assertEqual(labels.label("human").meaning, "Waiting on a person")
        self.assertIsNone(labels.label("area:docs"))
        self.assertIs(labels.axis_of("area:docs"), area)
        self.assertIsNone(labels.axis_of("human"))

    def test_states(self):
        self.assertTrue(self.schema.state("Needs Triage").open)
        self.assertEqual([s.name for s in self.schema.open_states],
                         ["Needs Triage"])
        self.assertEqual([s.name for s in self.schema.closed_states],
                         ["Closed"])

    def test_provenance(self):
        self.assertTrue(self.schema.provenance.is_original)
        self.assertFalse(self.schema.provenance.is_complete)
        copied = tracker_schema.Provenance("o/r", "a" * 40, "T.md")
        self.assertTrue(copied.is_complete)
        self.assertFalse(copied.is_original)
        lost = tracker_schema.Provenance("o/r", None, "T.md")
        self.assertFalse(lost.is_complete or lost.is_original)

    def test_the_schema_is_read_only(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.schema.problems = ()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.schema.issue_kinds[0].name = "x"
        self.assertIsInstance(self.schema.issue_kinds, tuple)

    def test_load_reads_a_path_and_names_it_in_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TRACKER.md"
            path.write_text(_file(_fenced(_DOCUMENT)), encoding="utf-8")
            self.assertEqual(tracker_schema.load(path).kind("bug").name, "bug")
            path.write_text("no block here\n", encoding="utf-8")
            with self.assertRaises(TrackerSchemaError) as caught:
                tracker_schema.load(str(path))
            self.assertTrue(str(caught.exception).startswith(f"{path}: "))
            with self.assertRaises(FileNotFoundError):
                tracker_schema.load(Path(directory) / "missing.md")
            path.write_bytes(b"\xff\xfe not utf-8")
            with self.assertRaises(TrackerSchemaError) as caught:
                tracker_schema.load(path)
            self.assertIn("not UTF-8 text", str(caught.exception))


# The prose is keyed by state name: each state has a meaning section, a
# level-four heading under "What each state means", and a transition section
# headed "Out of <state>" under "When an Issue moves". A heading there that
# names no state ("A Branch Issue in these states", "Into Closed, ...") is
# not keyed by one, so it is listed here and nowhere else.
_NOT_STATE_SECTIONS = {"A Branch Issue in these states"}


def _sections(text: str, parent: str):
    """The level-four headings under the level-three heading `parent`."""
    headings, inside = [], False
    for line in text.split("\n"):
        if line.startswith("### ") or line.startswith("## "):
            inside = line == f"### {parent}"
        elif inside and line.startswith("#### "):
            headings.append(line[len("#### "):].strip())
    return headings


class ShippedSchemaValidityTest(unittest.TestCase):
    """The shipped default and this repo's own copy read with no Problem at
    all (no unknown key, no entry left out, every section usable), and in
    each the block's state names and the prose's state sections agree."""

    def _check(self, path: Path) -> tracker_schema.TrackerSchema:
        text = path.read_text(encoding="utf-8")
        schema = tracker_schema.parse(text)
        self.assertEqual(
            [f"{p.where}: {p.message}" for p in schema.problems], [],
            f"{path.name} must read with no problem",
        )
        states = [state.name for state in schema.issue_states]
        meanings = [name for name in _sections(text, "What each state means")
                    if name not in _NOT_STATE_SECTIONS]
        transitions = [
            match.group(1)
            for match in (re.fullmatch(r"Out of (.+)", heading)
                          for heading in _sections(text, "When an Issue moves"))
            if match
        ]
        self.assertTrue(meanings and transitions,
                        f"{path.name}: no state sections found in the prose")
        self.assertCountEqual(
            states, meanings,
            f"{path.name}: the block's states and the meaning sections differ",
        )
        self.assertCountEqual(
            states, transitions,
            f"{path.name}: the block's states and the 'Out of' sections differ",
        )
        return schema

    def test_the_shipped_default_is_well_formed(self):
        schema = self._check(_SHIPPED_DEFAULT)
        self.assertTrue(schema.provenance.is_original,
                        "the shipped default's provenance fields must be null")

    def test_this_repos_copy_is_well_formed(self):
        schema = self._check(_THIS_REPOS_COPY)
        self.assertTrue(schema.provenance.is_complete,
                        "this repo's copy must record its provenance")


if __name__ == "__main__":
    unittest.main()
