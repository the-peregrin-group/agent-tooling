"""Tests for the ghw-issue-edit executable.

Argument tests run the script as a subprocess with arguments that fail before
any network I/O. Behavior tests load the script as a module and mock the lib
gh/boards seams. Either way, no `gh` calls are made.

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

_SCRIPT = Path(__file__).resolve().parent / "ghw-issue-edit"
_MISSING_BODY = "/tmp/claude/ghw-issue-edit-test-missing-body.md"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


class GhwIssueEditArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r", "retitle", "5"),
                          ("o/r", "retitle", "5", "New", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: ghw-issue-edit", result.stderr)

    def test_unknown_subverb_is_usage_error(self):
        result = _run("o/r", "close", "5", "value")
        self.assertEqual(result.returncode, 2)
        self.assertIn("add-label|remove-label|retitle|set-body", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "retitle", "5", "New title")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_bad_issue_number_is_usage_error(self):
        result = _run("o/r", "retitle", "zero", "New title")
        self.assertEqual(result.returncode, 2)
        self.assertIn("positive integer", result.stderr)

    def test_empty_value_is_usage_error(self):
        for subverb in ("add-label", "remove-label", "retitle"):
            with self.subTest(subverb=subverb):
                result = _run("o/r", subverb, "5", "   ")
                self.assertEqual(result.returncode, 2)
                self.assertIn("non-empty value", result.stderr)

    def test_set_body_value_must_be_a_staged_file(self):
        result = _run("o/r", "set-body", "5", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing body file", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ghw-issue-edit <repo>", result.stdout)


class GhwIssueEditBehaviorTest(unittest.TestCase):
    def test_re_adding_a_present_label_is_a_no_op(self):
        with mock.patch.object(_MODULE.boards, "fetch_labels",
                               return_value=[{"name": "perf"}, {"name": "bug"}]), \
                mock.patch.object(_MODULE.gh, "issue_view",
                                  return_value={"labels": [{"name": "perf"}]}), \
                mock.patch.object(_MODULE.gh, "issue_edit_labels") as edit, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "add-label", "5", "perf"]), 0)
        edit.assert_not_called()
        self.assertFalse(json.loads(stdout.getvalue())["changed"])

    def test_second_type_label_is_a_policy_refusal_naming_the_incumbent(self):
        with mock.patch.object(_MODULE.boards, "fetch_labels",
                               return_value=[{"name": "bug"}, {"name": "debt"}]), \
                mock.patch.object(_MODULE.gh, "issue_view",
                                  return_value={"labels": [{"name": "bug"}]}), \
                mock.patch.object(_MODULE.gh, "issue_edit_labels") as edit, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "add-label", "5", "debt"])
        self.assertEqual(caught.exception.code, 2)
        edit.assert_not_called()
        self.assertIn("'bug'", stderr.getvalue())

    def test_removing_an_absent_label_is_a_no_op(self):
        with mock.patch.object(_MODULE.gh, "issue_view",
                               return_value={"labels": [{"name": "bug"}]}), \
                mock.patch.object(_MODULE.gh, "issue_edit_labels") as edit, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "remove-label", "5", "perf"]), 0)
        edit.assert_not_called()
        self.assertFalse(json.loads(stdout.getvalue())["changed"])


if __name__ == "__main__":
    unittest.main()
