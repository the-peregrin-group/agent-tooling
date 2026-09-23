"""Argument-validation tests for the ghw-issue-comment executable.

Each test runs the script as a subprocess with arguments that fail before any
network I/O; no `gh` calls are made.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent / "ghw-issue-comment"
_MISSING_BODY = "/tmp/claude/ghw-issue-comment-test-missing-body.md"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class GhwIssueCommentArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r",), ("o/r", "5"), ("o/r", "5", "b", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: ghw-issue-comment", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "5", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_bad_issue_number_is_usage_error(self):
        for bad_number in ("0", "-1", "abc", "4.2"):
            with self.subTest(number=bad_number):
                result = _run("o/r", bad_number, _MISSING_BODY)
                self.assertEqual(result.returncode, 2)
                self.assertIn("positive integer", result.stderr)

    def test_missing_body_file_is_refused(self):
        result = _run("o/r", "5", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing body file", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ghw-issue-comment <repo>", result.stdout)


if __name__ == "__main__":
    unittest.main()
