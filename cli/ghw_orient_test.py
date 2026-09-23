"""Tests for the ghw-orient executable.

Argument tests run the script as a subprocess with arguments that fail before
any network I/O. Behavior tests load the script as a module and mock the lib
boards seam. Either way, no `gh` calls are made.

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

    def _orient(self, boards: list[dict]) -> dict:
        orientation = {
            "repo": {"name_with_owner": "o/r", "node_id": "R_1",
                     "default_branch": "main", "is_private": True},
            "labels": [],
            "boards": boards,
        }
        with mock.patch.object(_MODULE.boards, "fetch_orientation",
                               return_value=orientation), \
                mock.patch.object(_MODULE.boards, "find_triage_profile",
                                  return_value=None), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r"]), 0)
        return json.loads(stdout.getvalue())

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
        # A stock 'Todo' is drift to report, not a shortfall: it is reported
        # apart from the gaps and does not itself clear the verdict.
        self.assertIn("Todo", " ".join(verdict["extra_options"]))
        self.assertNotIn("Todo", gaps)

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


if __name__ == "__main__":
    unittest.main()
