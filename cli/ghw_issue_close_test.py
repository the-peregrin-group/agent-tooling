"""Tests for the ghw-issue-close executable.

Argument tests run the script as a subprocess with arguments that fail before
any network I/O. Behavior tests load the script as a module and mock the lib
gh seam. Either way, no `gh` calls are made.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ghw_test_support

_SCRIPT = Path(__file__).resolve().parent / "ghw-issue-close"
_MISSING_COMMENT = "/tmp/claude/ghw-issue-close-test-missing-comment.md"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


class GhwIssueCloseArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r",), ("o/r", "5", "c", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: ghw-issue-close", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "5")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_bad_issue_number_is_usage_error(self):
        result = _run("o/r", "issue-five")
        self.assertEqual(result.returncode, 2)
        self.assertIn("positive integer", result.stderr)

    def test_missing_comment_file_is_refused(self):
        result = _run("o/r", "5", _MISSING_COMMENT)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing body file", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ghw-issue-close <repo>", result.stdout)


class GhwIssueCloseBehaviorTest(unittest.TestCase):
    def setUp(self):
        os.makedirs("/tmp/claude", exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w", dir="/tmp/claude", suffix=".md", delete=False
        )
        handle.write("closing reason")
        handle.close()
        self._comment_path = handle.name
        self.addCleanup(os.unlink, self._comment_path)

    def test_already_closed_is_a_no_op_and_suppresses_the_comment(self):
        # The close the comment was meant to explain did not happen here, so
        # the comment must not post.
        with mock.patch.object(_MODULE.gh, "issue_view",
                               return_value={"state": "CLOSED"}), \
                mock.patch.object(_MODULE.gh, "issue_close") as close, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "5", self._comment_path]), 0)
        close.assert_not_called()
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["changed"])
        self.assertIn("comment not posted", payload["note"])

    def test_open_issue_closes_with_the_comment(self):
        with mock.patch.object(_MODULE.gh, "issue_view",
                               return_value={"state": "OPEN"}), \
                mock.patch.object(_MODULE.gh, "issue_close") as close, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "5", self._comment_path]), 0)
        close.assert_called_once_with("o/r", 5, "closing reason")
        self.assertTrue(json.loads(stdout.getvalue())["changed"])


if __name__ == "__main__":
    unittest.main()
