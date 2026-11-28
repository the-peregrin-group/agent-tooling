"""Unit tests for lib.github.repo_schema (a repo's TRACKER.md, fetched from
its default branch). gh.graphql is mocked, so no `gh` runs.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from unittest import mock

if __package__ in (None, ""):  # direct invocation
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import tracker_schema_test_support as fixture
from lib import tracker_schema
from lib.github import gh, repo_schema


def _fetch(response=None, error=None):
    with mock.patch.object(gh, "graphql", return_value=response,
                           side_effect=error) as graphql:
        result = repo_schema.fetch("o/r")
    return result, graphql


class FetchTest(unittest.TestCase):
    def test_reads_the_file_on_the_default_branch_in_one_request(self):
        result, graphql = _fetch(fixture.graphql_response(fixture.text()))
        graphql.assert_called_once()
        self.assertEqual(graphql.call_args.args[1],
                         {"owner": "o", "name": "r", "path": "TRACKER.md"})
        self.assertIn("defaultBranchRef", graphql.call_args.args[0])
        self.assertEqual(result.branch, "main")
        self.assertIsNone(result.failure)
        self.assertEqual([kind.name for kind in result.schema.issue_kinds],
                         ["task", "bug", "chore"])
        self.assertEqual(result.warning_lines(), ())

    def test_a_missing_file_gives_no_schema_and_one_warning(self):
        result, _ = _fetch(fixture.graphql_response(None, branch="trunk"))
        self.assertIsNone(result.schema)
        self.assertEqual(result.warning_lines(), (
            "warning: o/r@trunk:TRACKER.md: not found on the default branch",
        ))

    def test_an_empty_repo_has_no_default_branch(self):
        result, _ = _fetch({"repository": {"defaultBranchRef": None}})
        self.assertIsNone(result.schema)
        self.assertIsNone(result.branch)
        self.assertIn("no default branch", result.warning_lines()[0])

    def test_a_directory_binary_or_truncated_file_is_unreadable(self):
        cases = {
            "not a file": {},
            "not text": {"text": None, "isBinary": True, "isTruncated": False},
            "too large": {"text": "x", "isBinary": False, "isTruncated": True},
        }
        for words, blob in cases.items():
            with self.subTest(words=words):
                response = fixture.graphql_response("")
                response["repository"]["defaultBranchRef"]["target"]["file"] = {
                    "object": blob}
                result, _ = _fetch(response)
                self.assertIsNone(result.schema)
                self.assertIn(words, result.warning_lines()[0])

    def test_a_block_the_reader_cannot_read_is_a_failure_not_an_exception(self):
        result, _ = _fetch(fixture.graphql_response("# no block here\n"))
        self.assertIsNone(result.schema)
        self.assertIsInstance(result.failure, tracker_schema.TrackerSchemaError)
        self.assertEqual(len(result.warning_lines()), 1)

    def test_a_failed_fetch_degrades_to_no_schema(self):
        result, _ = _fetch(error=gh.GhError("dial tcp: no such host\nmore",
                                            exit_code=6))
        self.assertIsNone(result.schema)
        self.assertEqual(result.warning_lines(), (
            "warning: o/r@default-branch:TRACKER.md: could not be fetched "
            "(dial tcp: no such host)",
        ))

    def test_every_reader_problem_is_a_warning_line(self):
        document = fixture.document()
        del document["issue_kinds"][0]["color"]
        document["surprise"] = 1
        result, _ = _fetch(fixture.graphql_response(fixture.text(document)))
        lines = result.warning_lines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(line.startswith("warning: o/r@main:TRACKER.md: ")
                            for line in lines))


class LoadTest(unittest.TestCase):
    def test_prints_the_warnings_and_returns_the_result(self):
        stream = io.StringIO()
        with mock.patch.object(gh, "graphql",
                               return_value=fixture.graphql_response(None)):
            result = repo_schema.load("o/r", stream)
        self.assertIsNone(result.schema)
        self.assertEqual(stream.getvalue(),
                         "warning: o/r@main:TRACKER.md: not found on the "
                         "default branch\n")

    def test_prints_nothing_for_a_sound_file(self):
        stream = io.StringIO()
        with mock.patch.object(gh, "graphql",
                               return_value=fixture.graphql_response(fixture.text())):
            repo_schema.load("o/r", stream)
        self.assertEqual(stream.getvalue(), "")


class SectionsTest(unittest.TestCase):
    def test_section_gives_a_usable_section_and_none_otherwise(self):
        document = fixture.document()
        document["issue_kinds"] = "task"
        loaded = fixture.loaded(document)
        self.assertIsNone(loaded.section(tracker_schema.ISSUE_KINDS))
        self.assertEqual(len(loaded.section(tracker_schema.LABEL_AXES)), 2)
        self.assertIsNone(fixture.missing().section(tracker_schema.LABEL_AXES))

    def test_require_complete_passes_a_complete_schema(self):
        fixture.loaded().require_complete(*tracker_schema.SECTIONS)

    def test_require_complete_names_the_incomplete_section(self):
        document = fixture.document()
        del document["issue_label_schema"]["labels"][0]["color"]
        loaded = fixture.loaded(document)
        loaded.require_complete(tracker_schema.ISSUE_KINDS)
        with self.assertRaises(repo_schema.SchemaIncomplete) as caught:
            loaded.require_complete(tracker_schema.ISSUE_KINDS,
                                    tracker_schema.UNAXED_LABELS)
        self.assertIn("o/r@main:TRACKER.md", str(caught.exception))
        self.assertIn("issue_label_schema.labels is incomplete",
                      str(caught.exception))

    def test_require_complete_without_a_schema_says_why(self):
        with self.assertRaises(repo_schema.SchemaIncomplete) as caught:
            fixture.missing().require_complete(tracker_schema.ISSUE_KINDS)
        self.assertEqual(
            str(caught.exception),
            "o/r@main:TRACKER.md: not found on the default branch, so "
            "issue_kinds cannot be checked",
        )


if __name__ == "__main__":
    unittest.main()
