"""Tests for the ghw-board-set executable.

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

_SCRIPT = Path(__file__).resolve().parent / "ghw-board-set"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


def _linked_board() -> dict:
    """Fake the board dict produced by lib.boards fetches, with one
    single-select Priority field."""
    return {"number": 3, "title": "Roadmap", "node_id": "PVT_1",
            "fields": {"Priority": {"id": "F1", "data_type": "SINGLE_SELECT",
                                    "options": {"P1": "opt_p1", "P2": "opt_p2"}}}}


class GhwBoardSetArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r", "Priority", "P1"),
                          ("o/r", "Priority", "P1", "7", "--project")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: ghw-board-set", result.stderr)

    def test_tail_flag_other_than_project_is_usage_error(self):
        result = _run("o/r", "Priority", "P1", "7", "--board", "3")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--project", result.stderr)

    def test_non_integer_project_override_is_usage_error(self):
        result = _run("o/r", "Priority", "P1", "7", "--project", "roadmap")
        self.assertEqual(result.returncode, 2)
        self.assertIn("positive integer", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "Priority", "P1", "7")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_bad_issue_number_is_usage_error(self):
        result = _run("o/r", "Priority", "P1", "seven")
        self.assertEqual(result.returncode, 2)
        self.assertIn("positive integer", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ghw-board-set <repo>", result.stdout)


class GhwBoardSetBehaviorTest(unittest.TestCase):
    def test_converged_value_is_a_no_op(self):
        # Idempotency contract: field already holds the option -> no writes,
        # exit 0, changed: false.
        state = {"issue_node_id": "I_1",
                 "items": {"PVT_1": {"item_id": "IT_1", "option_id": "opt_p1"}}}
        with mock.patch.object(_MODULE.boards, "fetch_boards",
                               return_value=[_linked_board()]), \
                mock.patch.object(_MODULE.boards, "fetch_issue_item_state",
                                  return_value=state), \
                mock.patch.object(_MODULE.boards, "add_item_to_board") as add, \
                mock.patch.object(_MODULE.boards, "set_single_select_value") as set_value, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "Priority", "P1", "7"]), 0)
        add.assert_not_called()
        set_value.assert_not_called()
        self.assertFalse(json.loads(stdout.getvalue())["changed"])

    def test_missing_item_is_added_then_set(self):
        state = {"issue_node_id": "I_1", "items": {}}
        with mock.patch.object(_MODULE.boards, "fetch_boards",
                               return_value=[_linked_board()]), \
                mock.patch.object(_MODULE.boards, "fetch_issue_item_state",
                                  return_value=state), \
                mock.patch.object(_MODULE.boards, "add_item_to_board",
                                  return_value="IT_new") as add, \
                mock.patch.object(_MODULE.boards, "set_single_select_value") as set_value, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "Priority", "P1", "7"]), 0)
        add.assert_called_once_with("PVT_1", "I_1")
        set_value.assert_called_once_with("PVT_1", "IT_new", "F1", "opt_p1")
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["changed"])
        self.assertTrue(payload["added_to_board"])

    def test_unknown_option_is_a_policy_refusal_listing_the_options(self):
        with mock.patch.object(_MODULE.boards, "fetch_boards",
                               return_value=[_linked_board()]), \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "Priority", "P9", "7"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("P1", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
