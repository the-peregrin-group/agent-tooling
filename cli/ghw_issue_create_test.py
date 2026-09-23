"""Argument-validation tests for the ghw-issue-create executable.

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

_SCRIPT = Path(__file__).resolve().parent / "ghw-issue-create"
_MISSING_BODY = "/tmp/claude/ghw-issue-create-test-missing-body.md"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class GhwIssueCreateArgumentsTest(unittest.TestCase):
    def test_no_arguments_is_usage_error(self):
        result = _run()
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: ghw-issue-create", result.stderr)

    def test_three_arguments_is_usage_error(self):
        result = _run("o/r", "bug", "title only")
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "bug", "Title", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_unknown_type_label_is_refused(self):
        result = _run("o/r", "task", "Title", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("feature|improvement|bug|debt|meta", result.stderr)

    def test_empty_title_is_usage_error(self):
        result = _run("o/r", "bug", "   ", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("title", result.stderr)

    def test_missing_body_file_is_refused(self):
        result = _run("o/r", "bug", "Title", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing body file", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        for flag in ("-h", "--help"):
            with self.subTest(flag=flag):
                result = _run(flag)
                self.assertEqual(result.returncode, 0)
                self.assertIn("ghw-issue-create <repo>", result.stdout)


if __name__ == "__main__":
    unittest.main()
