"""Unit tests for tracker_schema.py, and the validity test for the Tracker
Schemas this repo ships and keeps: the shipped default and its own copy.

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
from lib.tracker_schema import TrackerSchemaError

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


class ExtractionTest(unittest.TestCase):
    """The delimiting rule: whole-line markers, one of each, one json fence."""

    def _refuses(self, text: str, fragment: str) -> None:
        with self.assertRaises(TrackerSchemaError) as caught:
            tracker_schema.parse(text)
        self.assertIn(fragment, str(caught.exception))

    def test_a_well_formed_file_parses(self):
        schema = tracker_schema.parse(_file(_fenced(_DOCUMENT)))
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
        tracker_schema.parse(text)
        tracker_schema.parse(text.replace("\n", "\r\n"))

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
        tracker_schema.parse(text)

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

    def test_a_key_written_twice_is_refused(self):
        block = '```json\n{"provenance": {}, "provenance": {}}\n```\n'
        self._refuses(_file(block), "the key 'provenance' twice")

    def test_json_nested_too_deeply_is_refused(self):
        block = "```json\n" + "[" * 100000 + "\n```\n"
        self._refuses(_file(block), "nests too deeply")


class ShapeTest(unittest.TestCase):
    """The block's shape, as the file's "What each key holds" documents it."""

    def _refuses(self, document: object, fragment: str) -> None:
        with self.assertRaises(TrackerSchemaError) as caught:
            tracker_schema.parse(_file(_fenced(document)))
        self.assertIn(fragment, str(caught.exception))

    def test_a_list_is_not_a_schema(self):
        self._refuses([], "the JSON block must be a JSON object")

    def test_a_missing_top_level_key_is_refused(self):
        document = copy.deepcopy(_DOCUMENT)
        del document["issue_states"]
        self._refuses(document, "the JSON block is missing issue_states")

    def test_an_unknown_key_is_refused(self):
        self._refuses(_with(issue_kind=[]), "unknown key(s) issue_kind")

    def test_an_unknown_nested_key_is_refused(self):
        kinds = [{"name": "bug", "meaning": "Broken", "color": "d73a4a"}]
        self._refuses(_with(issue_kinds=kinds),
                      "issue_kinds[0] has unknown key(s) color")

    def test_a_name_with_a_control_or_invisible_character_is_refused(self):
        for name in ("b\nug", chr(0x200B)):  # a newline; a zero-width space
            with self.subTest(name=name):
                self._refuses(
                    _with(issue_kinds=[{"name": name, "meaning": "x"}]),
                    "issue_kinds[0].name must hold no control",
                )

    def test_provenance_fields_are_strings_or_null(self):
        provenance = {"source_repo": 7, "source_commit": None,
                      "default_path": None}
        self._refuses(_with(provenance=provenance),
                      "provenance.source_repo must be a string or null")

    def test_source_commit_must_be_a_full_commit(self):
        provenance = {"source_repo": "o/r", "source_commit": "4f8a840",
                      "default_path": "TRACKER.default.md"}
        self._refuses(_with(provenance=provenance), "must be a full commit")

    def test_kinds_must_not_be_empty(self):
        self._refuses(_with(issue_kinds=[]),
                      "issue_kinds must list at least one entry")

    def test_a_kind_needs_a_meaning(self):
        self._refuses(_with(issue_kinds=[{"name": "bug", "meaning": " "}]),
                      "issue_kinds[0].meaning must be a non-empty string")

    def test_a_kind_declared_twice_is_refused(self):
        kind = {"name": "bug", "meaning": "Broken"}
        self._refuses(_with(issue_kinds=[kind, kind]),
                      "issue_kinds: 'bug' is declared twice")

    def test_names_differing_only_in_case_are_refused(self):
        self._refuses(
            _with(issue_kinds=[{"name": "Feature", "meaning": "x"},
                               {"name": "feature", "meaning": "y"}]),
            "'Feature' and 'feature' differ only in case",
        )
        label_schema = copy.deepcopy(_DOCUMENT["issue_label_schema"])
        label_schema["labels"].append({"name": "Human", "meaning": "x"})
        self._refuses(_with(issue_label_schema=label_schema),
                      "'human' and 'Human' differ only in case")

    def test_a_priority_declared_twice_is_refused(self):
        priority = {"name": "P0", "meaning": "Now", "stale_after_days": 1}
        self._refuses(_with(issue_priorities=[priority, priority]),
                      "issue_priorities: 'P0' is declared twice")

    def test_a_state_declared_twice_is_refused(self):
        states = [{"name": "Open", "open": True}, {"name": "Open", "open": True},
                  {"name": "Closed", "open": False}]
        self._refuses(_with(issue_states=states),
                      "issue_states: 'Open' is declared twice")

    def test_the_same_label_twice_on_an_axis_is_refused(self):
        label_schema = copy.deepcopy(_DOCUMENT["issue_label_schema"])
        label_schema["axes"][0]["labels"].append(
            {"name": "area:core", "meaning": "Again"}
        )
        self._refuses(_with(issue_label_schema=label_schema),
                      "(all labels): 'area:core' is declared twice")

    def test_staleness_is_a_positive_whole_number_of_days(self):
        for days in (0, 1.5, "7", True, 10 ** 500):
            with self.subTest(days=days):
                self._refuses(
                    _with(issue_priorities=[
                        {"name": "P0", "meaning": "Now", "stale_after_days": days}
                    ]),
                    "issue_priorities[0].stale_after_days must be a whole number",
                )

    def test_an_axis_label_must_begin_with_its_prefix(self):
        label_schema = copy.deepcopy(_DOCUMENT["issue_label_schema"])
        label_schema["axes"][0]["labels"] = [{"name": "core", "meaning": "x"}]
        self._refuses(_with(issue_label_schema=label_schema),
                      "beginning with its prefix 'area:'")

    def test_an_axis_must_say_whether_it_is_required(self):
        label_schema = copy.deepcopy(_DOCUMENT["issue_label_schema"])
        label_schema["axes"][0]["every_issue_carries_at_least_one"] = "yes"
        self._refuses(_with(issue_label_schema=label_schema),
                      "every_issue_carries_at_least_one must be true or false")

    def test_an_unaxed_label_with_an_axis_prefix_is_refused(self):
        label_schema = copy.deepcopy(_DOCUMENT["issue_label_schema"])
        label_schema["labels"].append({"name": "area:docs", "meaning": "Docs"})
        self._refuses(_with(issue_label_schema=label_schema),
                      "belongs in that axis's labels")

    def test_overlapping_axis_prefixes_are_refused(self):
        for prefix in ("area:", "a", "area:sub:", "AREA:"):
            with self.subTest(prefix=prefix):
                label_schema = copy.deepcopy(_DOCUMENT["issue_label_schema"])
                label_schema["axes"][1]["prefix"] = prefix
                self._refuses(_with(issue_label_schema=label_schema),
                              f"the prefixes 'area:' and {prefix!r} overlap")

    def test_a_state_flag_must_be_a_boolean(self):
        self._refuses(
            _with(issue_states=[{"name": "Open", "open": "yes"},
                                {"name": "Closed", "open": False}]),
            "issue_states[0].open must be true or false",
        )

    def test_states_need_an_open_and_a_closed_one(self):
        self._refuses(_with(issue_states=[{"name": "Closed", "open": False}]),
                      "no state is open")
        self._refuses(_with(issue_states=[{"name": "Open", "open": True}]),
                      "no state is closed")


class AccessorTest(unittest.TestCase):

    def setUp(self):
        self.schema = tracker_schema.parse(_file(_fenced(_DOCUMENT)))

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
            self.schema.issue_kinds = ()
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
    """The shipped default and this repo's own copy are well formed, and in
    each the block's state names and the prose's state sections agree."""

    def _check_states_agree(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        states = [state.name for state in tracker_schema.parse(text).issue_states]
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

    def test_the_shipped_default_is_well_formed(self):
        schema = tracker_schema.load(_SHIPPED_DEFAULT)
        self.assertTrue(schema.provenance.is_original,
                        "the shipped default's provenance fields must be null")
        self._check_states_agree(_SHIPPED_DEFAULT)

    def test_this_repos_copy_is_well_formed(self):
        schema = tracker_schema.load(_THIS_REPOS_COPY)
        self.assertTrue(schema.provenance.is_complete,
                        "this repo's copy must record its provenance")
        self._check_states_agree(_THIS_REPOS_COPY)


if __name__ == "__main__":
    unittest.main()
