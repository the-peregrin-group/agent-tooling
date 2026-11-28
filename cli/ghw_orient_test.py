"""Tests for the ghw-orient executable.

Argument tests run the script as a subprocess with arguments that fail before
any network I/O. Behavior tests load the script as a module and mock the lib
boards seam and the Tracker Schema fetch. Either way, no `gh` calls are made.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

import ghw_test_support
import tracker_schema_test_support as fixture

_SCRIPT = Path(__file__).resolve().parent / "ghw-orient"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class GhwOrientArgumentsTest(unittest.TestCase):
    def test_no_arguments_is_usage_error(self):
        result = _run()
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: ghw-orient <owner/repo>", result.stderr)

    def test_two_arguments_is_usage_error(self):
        result = _run("a/b", "c/d")
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        for bad_repo in ("plain", "a/b/c", "/", "a/", "/b", ""):
            with self.subTest(repo=bad_repo):
                result = _run(bad_repo)
                self.assertEqual(result.returncode, 2)
                self.assertIn("owner/name", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        for flag in ("-h", "--help"):
            with self.subTest(flag=flag):
                result = _run(flag)
                self.assertEqual(result.returncode, 0)
                self.assertIn("ghw-orient <repo>", result.stdout)


class GhwOrientConformanceVerdictTest(unittest.TestCase):
    """Orient publishes a canonical-schema verdict per linked board. Advisory
    only: it reports, and ghw-board-sync is what acts."""

    def _orient(self, boards: list[dict], labels=(), schema=None,
                stderr=None) -> dict:
        orientation = {
            "repo": {"name_with_owner": "o/r", "node_id": "R_1",
                     "default_branch": "main", "is_private": True},
            "labels": list(labels),
            "boards": boards,
        }
        with mock.patch.object(_MODULE.boards, "fetch_orientation",
                               return_value=orientation), \
                mock.patch.object(_MODULE.boards, "find_triage_profile",
                                  return_value=None), \
                mock.patch.object(_MODULE.repo_schema, "fetch",
                                  return_value=schema or fixture.loaded()), \
                contextlib.redirect_stderr(stderr or io.StringIO()), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r"]), 0)
        return json.loads(stdout.getvalue())

    def test_a_sound_tracker_md_is_reported_with_no_warnings(self):
        stderr = io.StringIO()
        payload = self._orient([], stderr=stderr)
        self.assertEqual(payload["tracker_schema"],
                         {"source": "o/r@main:TRACKER.md", "readable": True,
                          "warnings": 0})
        self.assertEqual(stderr.getvalue(), "")

    def test_a_missing_or_broken_tracker_md_warns_and_never_fails(self):
        document = fixture.document()
        document["issue_kinds"] = "task"
        for schema, readable in ((fixture.missing(), False),
                                 (fixture.loaded(document), True)):
            with self.subTest(readable=readable):
                stderr = io.StringIO()
                payload = self._orient([], schema=schema, stderr=stderr)
                self.assertEqual(payload["tracker_schema"]["readable"], readable)
                self.assertEqual(payload["tracker_schema"]["warnings"], 1)
                self.assertTrue(stderr.getvalue().startswith(
                    "warning: o/r@main:TRACKER.md: "))

    def test_stock_board_verdict_names_the_specific_gaps(self):
        # A typical unprovisioned board: stock Status options, no Last Triaged.
        payload = self._orient([{
            "number": 1, "title": "Board", "node_id": "PVT_1",
            "fields": {"Status": {"id": "F", "data_type": "SINGLE_SELECT",
                                  "options": {"Todo": "o1", "Done": "o2"}}},
        }])
        verdict = payload["boards"][0]["conformance"]
        self.assertFalse(verdict["conforms"])
        gaps = " ".join(verdict["gaps"])
        self.assertIn("Needs Triage", gaps)
        self.assertIn("'Last Triaged' is missing", gaps)
        self.assertIn("'Priority' is missing", gaps)
        self.assertIn("'Size' is missing", " ".join(verdict["tolerated_gaps"]))
        # The Status options are exactly the schema's Issue States, so a
        # stock 'Todo' the schema does not declare is a gap too.
        self.assertIn("does not declare: Todo, Done", gaps)

    def _board(self, status, priority) -> dict:
        def field(names):
            return {"id": "F", "data_type": "SINGLE_SELECT",
                    "options": {name: f"o_{name}" for name in names}}
        return {"number": 1, "title": "Board", "node_id": "PVT_1",
                "fields": {"Status": field(status), "Priority": field(priority),
                           "Size": field(["XS", "S", "M", "L", "XL"]),
                           "Last Triaged": {"id": "F", "data_type": "DATE",
                                            "options": {}}}}

    def test_a_board_holding_the_schemas_options_conforms(self):
        # The fixture declares P0, P1, and P4, not the old fixed P0 to P3.
        payload = self._orient([self._board(
            ["Needs Triage", "In progress", "Closed"], ["P0", "P1", "P4"])])
        self.assertTrue(payload["boards"][0]["conformance"]["conforms"])
        self.assertEqual(payload["priority_regime"], "board-field")

    def test_a_board_whose_priorities_differ_names_them_and_keeps_the_regime(self):
        payload = self._orient([self._board(
            ["Needs Triage", "In progress", "Closed"], ["P0", "P1", "P2", "P3"])])
        verdict = payload["boards"][0]["conformance"]
        self.assertFalse(verdict["conforms"])
        gaps = " ".join(verdict["gaps"])
        self.assertIn("'Priority' is missing options: P4", gaps)
        self.assertIn("does not declare: P2, P3", gaps)
        # Differing options are a conformance gap, never an unknown regime.
        self.assertEqual(payload["priority_regime"], "board-field")

    def test_unreadable_states_leave_the_status_options_unchecked(self):
        document = fixture.document()
        document["issue_states"] = "none"
        payload = self._orient(
            [self._board(["Anything"], ["P0", "P1", "P4"])],
            schema=fixture.loaded(document))
        verdict = payload["boards"][0]["conformance"]
        self.assertIsNone(verdict["conforms"])
        self.assertIn("'Status'", " ".join(verdict["unchecked"]))

    def test_priority_labels_present_follows_the_schemas_priorities(self):
        labels = [{"name": name, "color": "ededed", "description": ""}
                  for name in ("P4", "P2", "P0")]
        payload = self._orient([], labels=labels)
        self.assertEqual(payload["priority_labels_present"], ["P0", "P4"])
        payload = self._orient([], labels=labels, schema=fixture.missing())
        self.assertIsNone(payload["priority_labels_present"])

    def test_every_linked_board_gets_its_own_verdict(self):
        payload = self._orient([
            {"number": 1, "title": "A", "node_id": "PVT_1", "fields": {}},
            {"number": 2, "title": "B", "node_id": "PVT_2", "fields": {}},
        ])
        self.assertEqual(len(payload["boards"]), 2)
        for board in payload["boards"]:
            self.assertIn("conformance", board)

    def test_a_repo_with_no_boards_still_orients(self):
        payload = self._orient([])
        self.assertEqual(payload["boards"], [])
        self.assertIsNone(payload["canonical_board"])

    def test_a_synced_human_label_is_reported_in_the_live_labels(self):
        # Orient reports the shipped human label through the live registry,
        # as it does every label; it is not a priority label.
        human = {"name": "human", "color": "d876e3",
                 "description": "Waiting on a person"}
        registry = [{"name": "bug", "color": "d73a4a", "description": "Broken"},
                    human]
        payload = self._orient([], labels=registry)
        self.assertIn(human, payload["labels"])
        self.assertEqual(payload["priority_labels_present"], [])


class GhwOrientArgumentContractTest(
    ghw_test_support.ArgumentContractTests, unittest.TestCase
):
    SCRIPT = _SCRIPT
    LONGEST = ("o/r",)


if __name__ == "__main__":
    unittest.main()
