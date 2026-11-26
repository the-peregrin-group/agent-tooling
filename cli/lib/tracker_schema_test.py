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
from lib.tracker_schema import (
    IncompleteSectionError,
    TrackerSchemaError,
    UnusableSectionError,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SHIPPED_DEFAULT = _REPO_ROOT / "skills" / "setup-issue-tracker" / "TRACKER.default.md"
_THIS_REPOS_COPY = _REPO_ROOT / "TRACKER.md"

_DOCUMENT = {
    "provenance": {
        "source_repo": None, "source_commit": None, "default_path": None,
    },
    "issue_kinds": [
        {"name": "bug", "meaning": "Something is broken", "color": "d73a4a"},
        {"name": "feature", "meaning": "Something new", "color": "a2eeef"},
    ],
    "issue_priorities": [
        {"name": "P0", "meaning": "Drop everything", "color": "b60205",
         "stale_after_days": 1},
        {"name": "P1", "meaning": "Next", "color": "d93f0b",
         "stale_after_days": 7},
    ],
    "issue_label_schema": {
        "axes": [
            {
                "name": "area", "prefix": "area:", "meaning": "Part concerned",
                "every_issue_carries_at_least_one": True,
                "labels": [{"name": "area:core", "meaning": "The core",
                            "color": "bfdadc"}],
            },
            {
                "name": "scope", "prefix": "scope:", "meaning": "Deployment",
                "every_issue_carries_at_least_one": False,
                "labels": [],
            },
        ],
        "labels": [{"name": "human", "meaning": "Waiting on a person",
                    "color": "d876e3"}],
    },
    "issue_states": [
        {"name": "Needs Triage", "open": True, "entry": True,
         "color": "d73a4a"},
        {"name": "In review", "open": True, "color": "db61a2"},
        {"name": "Closed", "open": False, "color": "6a737d"},
    ],
    "close_reasons": [
        {"name": "done", "meaning": "The work is finished"},
        {"name": "rejected", "meaning": "It was decided not to do it"},
    ],
}

_ALL_SECTIONS = set(tracker_schema.SECTIONS)
_PROPERTY = {
    tracker_schema.PROVENANCE: "provenance",
    tracker_schema.ISSUE_KINDS: "issue_kinds",
    tracker_schema.ISSUE_PRIORITIES: "issue_priorities",
    tracker_schema.LABEL_AXES: "label_axes",
    tracker_schema.UNAXED_LABELS: "unaxed_labels",
    tracker_schema.ISSUE_STATES: "issue_states",
    tracker_schema.CLOSE_REASONS: "close_reasons",
}
_FILLER_COLOR = "ededed"


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


def _labels(**changes) -> dict:
    """The sample document with keys of issue_label_schema replaced."""
    label_schema = copy.deepcopy(_DOCUMENT["issue_label_schema"])
    label_schema.update(changes)
    return _with(issue_label_schema=label_schema)


def _filled(document: object) -> object:
    """A copy of `document` with what a test about something else would
    otherwise have to spell out on every entry: a colour on each kind,
    priority, label, and state that has none, and, where no state has an
    entry key, the entry flag on the first state flagged open. Anything
    that is not the expected shape is left as it is."""
    document = copy.deepcopy(document)
    if not isinstance(document, dict):
        return document

    def coloured(entries):
        for entry in entries if isinstance(entries, list) else ():
            if isinstance(entry, dict):
                entry.setdefault("color", _FILLER_COLOR)

    coloured(document.get("issue_kinds"))
    coloured(document.get("issue_priorities"))
    labels = document.get("issue_label_schema")
    if isinstance(labels, dict):
        coloured(labels.get("labels"))
        for axis in labels.get("axes") if isinstance(labels.get("axes"),
                                                     list) else ():
            if isinstance(axis, dict):
                coloured(axis.get("labels"))
    states = document.get("issue_states")
    coloured(states)
    if isinstance(states, list):
        dicts = [state for state in states if isinstance(state, dict)]
        if not any("entry" in state for state in dicts):
            first = next((state for state in dicts
                          if state.get("open") is True), None)
            if first is not None:
                first["entry"] = True
    return document


def _read(document: object, fill: bool = True) -> tracker_schema.TrackerSchema:
    """Parse `document`, filled in as `_filled` says unless `fill` is
    False, which tests of colours and entry flags themselves pass."""
    if fill:
        document = _filled(document)
    return tracker_schema.parse(_file(_fenced(document)))


def _usable(schema: tracker_schema.TrackerSchema) -> set:
    return {section for section in tracker_schema.SECTIONS
            if schema.usable(section)}


def _complete(schema: tracker_schema.TrackerSchema) -> set:
    return {section for section in tracker_schema.SECTIONS
            if schema.complete(section)}


class _Checks(unittest.TestCase):

    def _problem(self, schema, section, fragment: str,
                 lossy: bool = True) -> None:
        found = [p for p in schema.problems_in(section)
                 if fragment in f"{p.where}: {p.message}"]
        self.assertTrue(found, f"no problem in {section} mentions {fragment!r}: "
                        f"{[f'{p.where}: {p.message}' for p in schema.problems]}")
        self.assertTrue(all(p.lossy is lossy for p in found),
                        f"{fragment!r} should have lossy={lossy}")

    def _only_unusable(self, schema, *sections) -> None:
        self.assertEqual(_usable(schema), _ALL_SECTIONS - set(sections))
        for section in sections:
            with self.assertRaises(UnusableSectionError) as caught:
                getattr(schema, _PROPERTY[section])
            self.assertEqual(caught.exception.section, section)
            self.assertTrue(caught.exception.problems)

    def _only_incomplete(self, schema, *sections) -> None:
        """Every section usable, and complete except `sections`."""
        self.assertEqual(_usable(schema), _ALL_SECTIONS)
        self.assertEqual(_complete(schema), _ALL_SECTIONS - set(sections))
        for section in sections:
            with self.assertRaises(IncompleteSectionError) as caught:
                schema.require_complete(section)
            self.assertEqual(caught.exception.section, section)
            self.assertTrue(all(p.lossy for p in caught.exception.problems))


class ExtractionTest(_Checks):
    """The delimiting rule: whole-line markers, one of each, one json fence.
    Where the block is still plain to see, a file that strays from the rule
    is read with a problem; only an unclear block, or JSON that does not
    parse, fails the whole file."""

    def _refuses(self, text: str, fragment: str) -> None:
        with self.assertRaises(TrackerSchemaError) as caught:
            tracker_schema.parse(text)
        self.assertIn(fragment, str(caught.exception))

    def _tolerates(self, text: str, fragment: str) -> None:
        schema = tracker_schema.parse(text)
        self.assertEqual(_complete(schema), _ALL_SECTIONS)
        self.assertTrue(schema.problems)
        self.assertTrue(all(p.section is None and not p.lossy
                            for p in schema.problems))
        self._problem(schema, None, fragment, lossy=False)

    def test_a_well_formed_file_reads_with_no_problem(self):
        schema = _read(_DOCUMENT)
        self.assertEqual(schema.problems, ())
        self.assertEqual(_complete(schema), _ALL_SECTIONS)
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

    def test_an_indented_example_of_a_marker_elsewhere_is_ignored(self):
        for example in ("    <!-- END tracker-schema -->",
                        "  <!-- BEGIN tracker-schema -->",
                        "\t<!-- BEGIN tracker-schema -->"):
            with self.subTest(example=example):
                text = _file(_fenced(_DOCUMENT),
                             after=f"An example:\n\n{example}\n")
                self._tolerates(text, "an indented marker line is not a marker")

    def test_an_indented_marker_is_no_marker(self):
        for marker in ("<!-- BEGIN tracker-schema -->",
                       "<!-- END tracker-schema -->"):
            with self.subTest(marker=marker):
                text = _file(_fenced(_DOCUMENT)).replace(marker, "  " + marker)
                self._refuses(text, f"no {marker} line")

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

    def test_end_before_begin_is_refused(self):
        text = ("<!-- END tracker-schema -->\n" + _fenced(_DOCUMENT)
                + "<!-- BEGIN tracker-schema -->\n")
        self._refuses(text, "comes before")

    def test_no_fence_is_refused(self):
        self._refuses(_file("\n\n"), "no fenced block")

    def test_bare_json_without_a_fence_is_refused(self):
        self._refuses(_file(json.dumps(_DOCUMENT) + "\n"), "no fenced block")

    def test_two_fences_are_refused(self):
        self._refuses(_file(_fenced(_DOCUMENT) + "\n" + _fenced(_DOCUMENT)),
                      "which one is the schema is unclear")

    def test_an_unclosed_fence_is_refused(self):
        block = _fenced(_DOCUMENT).rstrip("\n").rsplit("\n", 1)[0] + "\n"
        self._refuses(_file(block), "is not closed")

    def test_other_opening_fences_are_read_with_a_problem(self):
        for opening in ("```", "```jsonc", "~~~json", "````json", "``` json",
                        "```JSON", "```json title", "   ```json"):
            with self.subTest(opening=opening):
                block = _fenced(_DOCUMENT).replace("```json", opening, 1)
                self._tolerates(_file(block), "read as the opening fence")

    def test_other_closing_fences_are_read_with_a_problem(self):
        for closing in ("~~~", "````", "  ```"):
            with self.subTest(closing=closing):
                block = _fenced(_DOCUMENT)[:-len("```\n")] + closing + "\n"
                self._tolerates(_file(block), "read as the closing fence")

    def test_a_stray_line_beside_the_fence_is_ignored(self):
        for block in ("A note.\n" + _fenced(_DOCUMENT),
                      _fenced(_DOCUMENT) + "A note.\n"):
            with self.subTest(block=block[:10]):
                self._tolerates(_file(block), "only blank lines belong")

    def test_invalid_json_is_refused_with_its_file_line(self):
        text = _file('```json\n{\n  "provenance": ,\n}\n```\n')
        # The block's second line is the file's: the BEGIN marker is line 5
        # and the fence line 6, so the bad line is 8.
        self._refuses(text, "does not parse (line 8,")

    def test_json_nested_too_deeply_is_refused(self):
        block = "```json\n" + "[" * 100000 + "\n```\n"
        self._refuses(_file(block), "nests too deeply")

    def test_a_whole_file_failure_is_not_a_section_error(self):
        self.assertFalse(issubclass(UnusableSectionError, TrackerSchemaError))
        self.assertFalse(issubclass(IncompleteSectionError, TrackerSchemaError))


class DegradationTest(_Checks):
    """A flaw in one part of the block leaves every other part usable, and
    leaves a section complete only when the reader lost nothing of it."""

    # -- keys the reader does not know, and keys it lacks --------------

    def test_an_unknown_top_level_key_is_ignored_and_reported(self):
        schema = _read(_with(board_ids={}))
        self.assertEqual(_complete(schema), _ALL_SECTIONS)
        self._problem(schema, None, "board_ids: unknown key, ignored",
                      lossy=False)

    def test_an_unknown_nested_key_is_ignored_and_reported(self):
        kinds = [{"name": "bug", "meaning": "Broken", "color": "d73a4a",
                  "emoji": "x"}]
        schema = _read(_with(issue_kinds=kinds))
        self.assertEqual(schema.kind("bug").meaning, "Broken")
        self.assertTrue(schema.complete(tracker_schema.ISSUE_KINDS))
        self._problem(schema, tracker_schema.ISSUE_KINDS,
                      "issue_kinds[0].emoji: unknown key, ignored", lossy=False)

    def test_an_unknown_key_in_the_label_schema_belongs_to_neither_section(self):
        schema = _read(_labels(colors={}))
        self.assertEqual(_complete(schema), _ALL_SECTIONS)
        self._problem(schema, None, "issue_label_schema.colors: unknown key",
                      lossy=False)

    def test_a_newer_copy_keeps_working_with_this_reader(self):
        # A copy written for a later reader: new top-level keys, and a new
        # key on entries this reader already knows.
        document = _with(board_ids={}, reopen_reasons=[{"name": "regressed"}])
        document["issue_states"][0]["aliases"] = ["Triage"]
        schema = _read(document)
        self.assertEqual(_complete(schema), _ALL_SECTIONS)
        self.assertEqual(schema.entry_state.name, "Needs Triage")
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
        self.assertFalse(schema.complete(tracker_schema.ISSUE_PRIORITIES))
        self._problem(schema, tracker_schema.ISSUE_PRIORITIES,
                      "issue_priorities[1].stale_after_days: missing")

    def test_a_copy_from_before_entry_order_close_reasons_and_colours(self):
        # The block as it was before the entry flag, the close reasons, and
        # the colours: every older section stays usable, with warnings.
        document = copy.deepcopy(_DOCUMENT)
        del document["close_reasons"]
        for entry in (document["issue_kinds"] + document["issue_priorities"]
                      + document["issue_label_schema"]["labels"]
                      + document["issue_label_schema"]["axes"][0]["labels"]
                      + document["issue_states"]):
            entry.pop("color")
            entry.pop("entry", None)
        schema = _read(document, fill=False)
        self._only_unusable(schema, tracker_schema.CLOSE_REASONS)
        self.assertEqual([s.name for s in schema.issue_states],
                         ["Needs Triage", "In review", "Closed"])
        self.assertEqual(schema.kind("bug").meaning, "Something is broken")
        self.assertIsNone(schema.kind("bug").color)
        self.assertIsNone(schema.entry_state)
        self._problem(schema, tracker_schema.ISSUE_STATES,
                      "no state is flagged \"entry\": true; the entry state "
                      "is unknown")
        self._problem(schema, tracker_schema.ISSUE_KINDS,
                      "issue_kinds[0].color: missing; read as absent")
        self._problem(schema, tracker_schema.CLOSE_REASONS, "missing")
        # Treated like a missing meaning: lossy, so a destructive write
        # waits until the file declares its colours.
        self.assertEqual(_complete(schema), {tracker_schema.PROVENANCE})

    def test_a_missing_section_is_unusable_alone(self):
        document = copy.deepcopy(_DOCUMENT)
        del document["issue_states"]
        schema = _read(document)
        self._only_unusable(schema, tracker_schema.ISSUE_STATES)
        self._problem(schema, tracker_schema.ISSUE_STATES, "missing")
        self.assertEqual(schema.kind("bug").name, "bug")

    def test_a_block_that_is_no_object_is_one_problem(self):
        schema = _read([])
        self.assertEqual(_usable(schema), set())
        self.assertEqual(len(schema.problems), 1)
        self._problem(schema, None, "must be a JSON object")
        with self.assertRaises(UnusableSectionError) as caught:
            schema.issue_kinds
        self.assertEqual(caught.exception.problems, schema.problems)

    def test_a_section_key_written_twice_is_unusable_alone(self):
        block = ('```json\n{"issue_kinds": [], "issue_kinds": [],'
                 + _fenced(_DOCUMENT)[len("```json\n{"):])
        schema = tracker_schema.parse(_file(block))
        self._only_unusable(schema, tracker_schema.ISSUE_KINDS)
        self._problem(schema, tracker_schema.ISSUE_KINDS, "written twice")

    # -- one broken section --------------------------------------------

    def test_one_broken_section_leaves_the_others_complete(self):
        schema = _read(_with(issue_priorities="P0, P1"))
        self._only_unusable(schema, tracker_schema.ISSUE_PRIORITIES)
        self.assertEqual(_complete(schema),
                         _ALL_SECTIONS - {tracker_schema.ISSUE_PRIORITIES})
        self._problem(schema, tracker_schema.ISSUE_PRIORITIES,
                      "must be a JSON list")
        self.assertEqual(len(schema.issue_states), 3)
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
        self._only_incomplete(schema, tracker_schema.ISSUE_KINDS)
        self._problem(schema, tracker_schema.ISSUE_KINDS,
                      "issue_kinds[1].name: missing; the entry is left out")
        self._problem(schema, tracker_schema.ISSUE_KINDS,
                      "issue_kinds[2]: must be a JSON object")
        self.assertEqual(len(schema.problems), 2)

    def test_a_bad_meaning_reads_as_none(self):
        schema = _read(_with(issue_kinds=[{"name": "bug", "meaning": " "}]))
        self.assertIsNone(schema.kind("bug").meaning)
        self._only_incomplete(schema, tracker_schema.ISSUE_KINDS)

    def test_a_state_with_a_bad_flag_is_left_out(self):
        schema = _read(_with(issue_states=[
            {"name": "Open", "open": "yes"}, {"name": "Closed", "open": False},
        ]))
        self.assertIsNone(schema.state("Open"))
        self.assertEqual(schema.open_states, ())
        self.assertEqual([s.name for s in schema.closed_states], ["Closed"])
        self._only_incomplete(schema, tracker_schema.ISSUE_STATES)
        self._problem(schema, tracker_schema.ISSUE_STATES,
                      "issue_states[0].open: must be true or false; the entry "
                      "is left out")
        self._problem(schema, tracker_schema.ISSUE_STATES,
                      "no state is flagged open", lossy=False)

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

    # -- labels --------------------------------------------------------------

    def test_an_axis_label_without_its_prefix_is_left_out(self):
        document = copy.deepcopy(_DOCUMENT)
        document["issue_label_schema"]["axes"][0]["labels"].append(
            {"name": "core", "meaning": "x"})
        schema = _read(document)
        self.assertEqual([l.name for l in schema.label_axes[0].labels],
                         ["area:core"])
        self._problem(schema, tracker_schema.LABEL_AXES,
                      "does not begin with the axis's prefix 'area:'")

    def test_an_unaxed_label_with_an_axis_prefix_is_left_out(self):
        document = copy.deepcopy(_DOCUMENT)
        document["issue_label_schema"]["labels"].append(
            {"name": "area:docs", "meaning": "Docs"})
        schema = _read(document)
        self.assertEqual([l.name for l in schema.unaxed_labels], ["human"])
        self._problem(schema, tracker_schema.UNAXED_LABELS,
                      "belongs in that axis's labels")

    def test_an_axis_whose_labels_are_no_list_is_incomplete(self):
        # A label sync that trusted this axis would delete every area:
        # label on the forge.
        document = copy.deepcopy(_DOCUMENT)
        document["issue_label_schema"]["axes"][0]["labels"] = "area:core"
        schema = _read(document)
        self.assertEqual(schema.issue_label_schema.axis("area").labels, ())
        self._only_incomplete(schema, tracker_schema.LABEL_AXES)

    def test_an_axis_with_a_bad_prefix_is_left_out_and_doubts_the_unaxed(self):
        # A label sync that trusted the axes would delete every scope:
        # label; and an unaxed label may belong on the lost axis.
        document = copy.deepcopy(_DOCUMENT)
        document["issue_label_schema"]["axes"][1]["prefix"] = "scope: "
        document["issue_label_schema"]["labels"].append(
            {"name": "scope:prod", "meaning": "x"})
        schema = _read(document)
        self.assertEqual([a.name for a in schema.label_axes], ["area"])
        self.assertIn("scope:prod",
                      [l.name for l in schema.unaxed_labels])
        self._only_incomplete(schema, tracker_schema.LABEL_AXES,
                              tracker_schema.UNAXED_LABELS)
        self._problem(schema, tracker_schema.UNAXED_LABELS,
                      "could not be checked against every axis's prefix")

    def test_unusable_axes_leave_the_unaxed_labels_in_doubt(self):
        no_list = _labels(axes="area")
        no_axes = _labels()
        del no_axes["issue_label_schema"]["axes"]
        for document in (no_list, no_axes):
            document["issue_label_schema"]["labels"].append(
                {"name": "area:core", "meaning": "x"})
            with self.subTest(axes=document["issue_label_schema"].get("axes")):
                schema = _read(document)
                self.assertFalse(schema.usable(tracker_schema.LABEL_AXES))
                self.assertTrue(schema.usable(tracker_schema.UNAXED_LABELS))
                self.assertFalse(schema.complete(tracker_schema.UNAXED_LABELS))
                self._problem(schema, tracker_schema.UNAXED_LABELS,
                              "could not be checked")

    def test_unaxed_labels_alone_need_no_axis_check(self):
        schema = _read(_labels(axes="area", labels=[]))
        self.assertEqual(schema.unaxed_labels, ())
        self.assertTrue(schema.complete(tracker_schema.UNAXED_LABELS))

    def test_an_axis_with_a_bad_required_flag_is_left_out(self):
        document = copy.deepcopy(_DOCUMENT)
        document["issue_label_schema"]["axes"][0][
            "every_issue_carries_at_least_one"] = "true"
        document["issue_label_schema"]["labels"].append(
            {"name": "area:docs", "meaning": "x"})
        schema = _read(document)
        self.assertIsNone(schema.issue_label_schema.axis("area"))
        self.assertIs(schema.issue_label_schema.axis("scope").required, False)
        # Its prefix still keeps its labels out of the unaxed ones.
        self.assertEqual([l.name for l in schema.unaxed_labels], ["human"])
        self.assertFalse(schema.complete(tracker_schema.LABEL_AXES))

    # -- names declared more than once ---------------------------------------

    def test_a_kind_or_label_declared_twice_keeps_one(self):
        schema = _read(_with(issue_kinds=[
            {"name": "Feature", "meaning": "first"},
            {"name": "feature", "meaning": "second"},
            {"name": "bug", "meaning": "b"},
        ]))
        self.assertEqual([(k.name, k.meaning) for k in schema.issue_kinds],
                         [("Feature", "first"), ("bug", "b")])
        self._only_incomplete(schema, tracker_schema.ISSUE_KINDS)
        self._problem(schema, tracker_schema.ISSUE_KINDS,
                      "'Feature' and 'feature' name one kind")
        document = copy.deepcopy(_DOCUMENT)
        document["issue_label_schema"]["labels"].append(
            {"name": "Human", "meaning": "x"})
        document["issue_label_schema"]["axes"][0]["labels"].append(
            {"name": "area:core", "meaning": "again"})
        schema = _read(document)
        self.assertEqual([l.name for l in schema.unaxed_labels], ["human"])
        self.assertEqual(schema.issue_label_schema.label("area:core").meaning,
                         "The core")
        self._problem(schema, tracker_schema.LABEL_AXES,
                      "the label 'area:core' is declared 2 times")

    def test_a_duplicate_prefers_the_entry_that_reads(self):
        schema = _read(_with(issue_kinds=[
            {"name": "bug", "meaning": ""}, {"name": "bug", "meaning": "Broken"},
        ]))
        self.assertEqual(schema.kind("bug").meaning, "Broken")
        schema = _read(_with(issue_states=[
            {"name": "Open", "open": True},
            {"name": "Closed", "open": "no"}, {"name": "Closed", "open": False},
        ]))
        self.assertEqual([s.name for s in schema.closed_states], ["Closed"])

    def test_a_priority_declared_twice_is_left_out_and_the_rest_kept(self):
        def entry(name):
            return {"name": name, "meaning": "m", "stale_after_days": 1}
        schema = _read(_with(issue_priorities=[
            entry("P0"), entry("P1"), entry("P1"), entry("P2"),
        ]))
        self.assertEqual([p.name for p in schema.issue_priorities], ["P0", "P2"])
        self._only_incomplete(schema, tracker_schema.ISSUE_PRIORITIES)
        self._problem(schema, tracker_schema.ISSUE_PRIORITIES,
                      "every entry of it is left out")
        schema = _read(_with(issue_priorities=[entry("P0"), entry("P0")]))
        self._only_unusable(schema, tracker_schema.ISSUE_PRIORITIES)

    def test_a_state_listed_twice(self):
        same = _read(_with(issue_states=[
            {"name": "Open", "open": True}, {"name": "Open", "open": True},
            {"name": "Closed", "open": False},
        ]))
        self.assertEqual([s.name for s in same.issue_states], ["Open", "Closed"])
        # Flagged both ways, only that state is lost.
        states = copy.deepcopy(_DOCUMENT["issue_states"]) + [
            {"name": "closed", "open": True}]
        opposite = _read(_with(issue_states=states))
        self.assertEqual([s.name for s in opposite.issue_states],
                         ["Needs Triage", "In review"])
        self._only_incomplete(opposite, tracker_schema.ISSUE_STATES)
        self._problem(opposite, tracker_schema.ISSUE_STATES,
                      "flagged both open and closed")

    # -- the entry state ------------------------------------------------------
    #
    # Whatever is wrong with the entry flags, every state is kept and only
    # the entry state is unknown, so only a caller that needs it stops.

    def _entry_unknown(self, states, fragment: str) -> None:
        schema = _read(_with(issue_states=states), fill=False)
        self.assertIsNone(schema.entry_state)
        self.assertEqual(_usable(schema), _ALL_SECTIONS)
        self._only_incomplete(schema, tracker_schema.ISSUE_STATES)
        self._problem(schema, tracker_schema.ISSUE_STATES, fragment)
        return schema

    def test_no_entry_state_leaves_it_unknown(self):
        states = copy.deepcopy(_DOCUMENT["issue_states"])
        del states[0]["entry"]
        schema = self._entry_unknown(states, "no state is flagged")
        self.assertEqual(len(schema.issue_states), 3)

    def test_two_entry_states_leave_it_unknown(self):
        states = copy.deepcopy(_DOCUMENT["issue_states"])
        states[1]["entry"] = True
        self._entry_unknown(states, "more than one state is flagged "
                            "\"entry\": true ('Needs Triage', 'In review')")

    def test_a_bad_entry_flag_leaves_it_unknown(self):
        for flag in ("yes", None, 1):
            with self.subTest(flag=flag):
                states = copy.deepcopy(_DOCUMENT["issue_states"])
                states[1]["entry"] = flag
                self._entry_unknown(states, "issue_states[1].entry: must be "
                                    "true or false; the entry state is unknown")

    def test_an_entry_flag_written_twice_leaves_it_unknown(self):
        block = _fenced(_DOCUMENT).replace('"entry": true',
                                           '"entry": true, "entry": false')
        schema = tracker_schema.parse(_file(block))
        self.assertIsNone(schema.entry_state)
        self._problem(schema, tracker_schema.ISSUE_STATES,
                      "issue_states[0].entry: written twice")

    def test_an_entry_state_left_out_leaves_it_unknown(self):
        states = copy.deepcopy(_DOCUMENT["issue_states"])
        states[0]["open"] = "yes"
        self._entry_unknown(states, "'Needs Triage', is left out")
        states = copy.deepcopy(_DOCUMENT["issue_states"])
        del states[0]["name"]
        self._entry_unknown(states, "left out for want of a name")

    def test_a_closed_entry_state_leaves_it_unknown(self):
        states = copy.deepcopy(_DOCUMENT["issue_states"])
        del states[0]["entry"]
        states[2]["entry"] = True
        self._entry_unknown(states, "'Closed', is flagged closed")

    def test_entry_false_is_no_problem(self):
        states = copy.deepcopy(_DOCUMENT["issue_states"])
        states[1]["entry"] = False
        schema = _read(_with(issue_states=states), fill=False)
        self.assertEqual(schema.problems, ())
        self.assertEqual(schema.entry_state.name, "Needs Triage")

    def test_unusable_states_have_no_entry_state_to_ask_for(self):
        schema = _read(_with(issue_states="Needs Triage"), fill=False)
        with self.assertRaises(UnusableSectionError):
            schema.entry_state
        self.assertFalse([p for p in schema.problems if "entry" in p.message])

    # -- colours --------------------------------------------------------------

    def test_a_colour_is_read_in_either_case_and_kept_in_lowercase(self):
        kinds = [{"name": "bug", "meaning": "Broken", "color": "D73A4A"}]
        schema = _read(_with(issue_kinds=kinds), fill=False)
        self.assertEqual(schema.kind("bug").color, "d73a4a")
        self.assertTrue(schema.complete(tracker_schema.ISSUE_KINDS))

    def test_a_bad_colour_reads_as_none_and_keeps_the_entry(self):
        for color in ("#d73a4a", "d73a4", "red", "RED", 0xd73a4a, None, " d73a4a"):
            with self.subTest(color=color):
                document = copy.deepcopy(_DOCUMENT)
                document["issue_states"][1]["color"] = color
                schema = _read(document, fill=False)
                self.assertEqual(schema.state("In review").open, True)
                self.assertIsNone(schema.state("In review").color)
                self._only_incomplete(schema, tracker_schema.ISSUE_STATES)
                self._problem(schema, tracker_schema.ISSUE_STATES,
                              "issue_states[1].color: must be six hex digits "
                              "with no leading #, such as d73a4a; read as "
                              "absent")

    def test_a_missing_colour_reads_as_none_in_every_section(self):
        document = copy.deepcopy(_DOCUMENT)
        del document["issue_kinds"][0]["color"]
        del document["issue_priorities"][0]["color"]
        del document["issue_label_schema"]["axes"][0]["labels"][0]["color"]
        del document["issue_label_schema"]["labels"][0]["color"]
        del document["issue_states"][0]["color"]
        schema = _read(document, fill=False)
        self.assertIsNone(schema.kind("bug").color)
        self.assertIsNone(schema.priority("P0").color)
        self.assertIsNone(schema.issue_label_schema.label("area:core").color)
        self.assertIsNone(schema.issue_label_schema.label("human").color)
        self.assertIsNone(schema.entry_state.color)
        self._only_incomplete(schema, tracker_schema.ISSUE_KINDS,
                              tracker_schema.ISSUE_PRIORITIES,
                              tracker_schema.LABEL_AXES,
                              tracker_schema.UNAXED_LABELS,
                              tracker_schema.ISSUE_STATES)

    # -- close reasons --------------------------------------------------------

    def test_close_reasons_degrade_like_kinds(self):
        reasons = [{"name": "done", "meaning": "Finished"}, {"meaning": "x"},
                   {"name": "done", "meaning": "again"},
                   {"name": "rejected", "meaning": ""}]
        schema = _read(_with(close_reasons=reasons))
        self.assertEqual([(r.name, r.meaning) for r in schema.close_reasons],
                         [("done", "Finished"), ("rejected", None)])
        self._only_incomplete(schema, tracker_schema.CLOSE_REASONS)
        self._problem(schema, tracker_schema.CLOSE_REASONS,
                      "close_reasons[1].name: missing; the entry is left out")
        self._problem(schema, tracker_schema.CLOSE_REASONS,
                      "the close reason 'done' is declared 2 times")

    def test_close_reasons_unusable_alone(self):
        for reasons in ([], "done", [{"meaning": "x"}]):
            with self.subTest(reasons=reasons):
                schema = _read(_with(close_reasons=reasons))
                self._only_unusable(schema, tracker_schema.CLOSE_REASONS)
                self.assertEqual(schema.entry_state.name, "Needs Triage")

    def test_overlapping_axis_prefixes_leave_out_both_axes(self):
        for prefix in ("area:", "a", "area:sub:", "AREA:"):
            with self.subTest(prefix=prefix):
                document = copy.deepcopy(_DOCUMENT)
                document["issue_label_schema"]["axes"][1]["prefix"] = prefix
                document["issue_label_schema"]["labels"].append(
                    {"name": "area:docs", "meaning": "x"})
                schema = _read(document)
                self.assertEqual(schema.label_axes, ())
                self._only_incomplete(schema, tracker_schema.LABEL_AXES,
                                      tracker_schema.UNAXED_LABELS)
                self._problem(schema, tracker_schema.LABEL_AXES,
                              f"the prefixes 'area:' and {prefix!r} overlap")
                # The prefixes still keep their labels out of the unaxed.
                self.assertEqual([l.name for l in schema.unaxed_labels],
                                 ["human"])

    def test_axes_sharing_a_name_are_left_out(self):
        document = copy.deepcopy(_DOCUMENT)
        document["issue_label_schema"]["axes"][1]["name"] = "Area"
        document["issue_label_schema"]["labels"].append(
            {"name": "scope:prod", "meaning": "x"})
        schema = _read(document)
        self.assertEqual(schema.label_axes, ())
        self.assertEqual([l.name for l in schema.unaxed_labels], ["human"])
        self._problem(schema, tracker_schema.LABEL_AXES, "differ only in case")

    # -- provenance -----------------------------------------------------------

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

    def test_partly_null_provenance_is_read_and_reported(self):
        schema = _read(_with(provenance={
            "source_repo": "o/r", "source_commit": None, "default_path": None,
        }))
        self.assertEqual(schema.provenance.source_repo, "o/r")
        self.assertEqual(_complete(schema), _ALL_SECTIONS)
        self._problem(schema, tracker_schema.PROVENANCE,
                      "has lost its provenance", lossy=False)


class WarningLinesTest(unittest.TestCase):

    def test_no_problem_means_no_warning(self):
        self.assertEqual(tracker_schema.warning_lines(_read(_DOCUMENT)), ())

    def test_one_line_per_problem_naming_file_place_and_fault(self):
        document = _with(board_ids="x")
        del document["issue_states"]
        document["issue_kinds"][0]["meaning"] = ""
        document["issue_kinds"].append({"name": "feature", "meaning": "again"})
        lines = tracker_schema.warning_lines(_read(document))
        self.assertEqual(lines, (
            "warning: TRACKER.md: board_ids: unknown key, ignored (this "
            "reader knows provenance, issue_kinds, issue_priorities, "
            "issue_label_schema, issue_states, close_reasons; the file may be "
            "newer than the tool reading it)",
            "warning: TRACKER.md: issue_kinds[0].meaning: must be a non-empty "
            "string with no surrounding whitespace; read as absent",
            "warning: TRACKER.md: issue_kinds: the kind 'feature' is declared 2 "
            "times; one entry is kept and the others ignored",
            "warning: TRACKER.md: issue_states: missing; the section is unusable",
        ))

    def test_a_block_that_is_no_object_is_one_warning(self):
        lines = tracker_schema.warning_lines(_read([]))
        self.assertEqual(lines, (
            "warning: TRACKER.md: the JSON block: must be a JSON object with "
            "the keys provenance, issue_kinds, issue_priorities, "
            "issue_label_schema, issue_states, close_reasons; no section is "
            "usable",
        ))

    def test_nothing_from_the_file_reaches_a_line_unescaped(self):
        document = _with(**{"x\nwarning: TRACKER.md: forged": 1,
                            "\x1b[31mred": 2})
        document["issue_kinds"].append({"name": "a\x1bb", "meaning": "m"})
        lines = tracker_schema.warning_lines(_read(document))
        self.assertEqual(len(lines), 3)
        for line in lines:
            self.assertTrue(line.isprintable(), line)
        self.assertTrue(any("'x\\nwarning: TRACKER.md: forged'" in line
                            for line in lines))
        self.assertTrue(any("\\x1b[31mred" in line for line in lines))

    def test_a_whole_file_failure_is_one_warning(self):
        try:
            tracker_schema.parse("no block\n")
        except TrackerSchemaError as error:
            lines = tracker_schema.warning_lines(error, "owner/repo TRACKER.md")
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith(
            "warning: owner/repo TRACKER.md: no <!-- BEGIN"))

    def test_a_load_failure_names_the_file_once(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TRACKER.md"
            path.write_text("no block here\n", encoding="utf-8")
            with self.assertRaises(TrackerSchemaError) as caught:
                tracker_schema.load(path)
        (line,) = tracker_schema.warning_lines(caught.exception, str(path))
        self.assertEqual(line.count(str(path)), 1)


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
        self.assertIs(labels.axis("scope").required, False)
        self.assertEqual([label.name for label in labels.all_labels()],
                         ["area:core", "human"])
        self.assertEqual(labels.label("human").meaning, "Waiting on a person")
        self.assertEqual(labels.label("human").color, "d876e3")
        self.assertEqual(labels.label("area:core").color, "bfdadc")
        self.assertIsNone(labels.label("area:docs"))
        self.assertIs(labels.axis_of("area:docs"), area)
        self.assertIsNone(labels.axis_of("human"))

    def test_states_in_diagram_order(self):
        self.assertIs(self.schema.state("Needs Triage").open, True)
        self.assertEqual([s.name for s in self.schema.issue_states],
                         ["Needs Triage", "In review", "Closed"])
        self.assertEqual([s.name for s in self.schema.open_states],
                         ["Needs Triage", "In review"])
        self.assertEqual([s.name for s in self.schema.closed_states],
                         ["Closed"])
        self.assertIs(self.schema.entry_state,
                      self.schema.state("Needs Triage"))
        self.assertEqual(self.schema.state("Closed").color, "6a737d")

    def test_colours(self):
        self.assertEqual(self.schema.kind("bug").color, "d73a4a")
        self.assertEqual(self.schema.priority("P1").color, "d93f0b")

    def test_close_reasons(self):
        self.assertEqual([r.name for r in self.schema.close_reasons],
                         ["done", "rejected"])
        self.assertEqual(self.schema.close_reason("done").meaning,
                         "The work is finished")
        self.assertIsNone(self.schema.close_reason("wontfix"))

    def test_provenance(self):
        self.assertTrue(self.schema.provenance.is_original)
        self.assertFalse(self.schema.provenance.is_complete)
        copied = tracker_schema.Provenance("o/r", "a" * 40, "T.md")
        self.assertTrue(copied.is_complete)
        self.assertFalse(copied.is_original)
        lost = tracker_schema.Provenance("o/r", None, "T.md")
        self.assertFalse(lost.is_complete or lost.is_original)

    def test_require_complete(self):
        self.schema.require_complete(*tracker_schema.SECTIONS)
        schema = _read(_with(issue_kinds="bug"))
        with self.assertRaises(UnusableSectionError):
            schema.require_complete(tracker_schema.ISSUE_STATES,
                                    tracker_schema.ISSUE_KINDS)

    def test_an_unknown_section_name_is_a_caller_error(self):
        for call in (self.schema.usable, self.schema.complete,
                     self.schema.require_complete, self.schema.problems_in):
            with self.subTest(call=call.__name__):
                with self.assertRaises(ValueError):
                    call("issue_label_schema")

    def test_the_schema_is_read_only_and_hashable(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.schema.problems = ()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.schema.issue_kinds[0].name = "x"
        with self.assertRaises(TypeError):
            self.schema._sections[tracker_schema.ISSUE_KINDS] = None
        self.assertIsInstance(self.schema.issue_kinds, tuple)
        self.assertEqual(hash(self.schema), hash(_read(_DOCUMENT)))
        self.assertEqual(self.schema, _read(_DOCUMENT))

    def test_load_reads_a_path_and_names_it_in_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TRACKER.md"
            path.write_text(_file(_fenced(_DOCUMENT)), encoding="utf-8")
            self.assertEqual(tracker_schema.load(path).kind("bug").name, "bug")
            path.write_text("no block here\n", encoding="utf-8")
            with self.assertRaises(TrackerSchemaError) as caught:
                tracker_schema.load(str(path))
            self.assertTrue(str(caught.exception).startswith(f"{path}: "))
            self.assertEqual(caught.exception.path, path)
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


def _close_reason_conditions(text: str):
    """The close reasons the prose keys a condition by: each bullet under
    the "Into Closed" heading that begins with a name in backticks."""
    names, inside = [], False
    for line in text.split("\n"):
        if line.startswith("#"):
            inside = line.startswith("#### Into Closed")
        elif inside:
            match = re.match(r"- `([^`]+)`:", line)
            if match:
                names.append(match.group(1))
    return names


class ShippedSchemaValidityTest(unittest.TestCase):
    """The shipped default and this repo's own copy read with no Problem at
    all (no stray from the delimiting rule, no unknown key, no entry left
    out, every section complete, so exactly one entry state and a colour on
    everything that takes one), and in each the block and the prose agree:
    the prose's state sections are the block's states in the block's order,
    and its close-reason conditions are keyed by the block's close
    reasons."""

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
        # The block's list is the order; the prose follows it.
        self.assertEqual(
            states, meanings,
            f"{path.name}: the meaning sections are not the block's states "
            "in the block's order",
        )
        self.assertEqual(
            states, transitions,
            f"{path.name}: the 'Out of' sections are not the block's states "
            "in the block's order",
        )
        self.assertIsNotNone(schema.entry_state)
        self.assertEqual(
            [reason.name for reason in schema.close_reasons],
            _close_reason_conditions(text),
            f"{path.name}: the block's close reasons and those the 'Into "
            "Closed' prose keys a condition by differ",
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
