"""Tests for the fjw-pr-close executable: comment-then-close ordering, the
mandatory comment, the already-closed no-op, and honest partial failure.

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
from lib.forgejo.config import Config

_SCRIPT = Path(__file__).resolve().parent / "fjw-pr-close"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)
_MISSING_COMMENT = "/tmp/claude/fjw-pr-close-test-missing-comment.md"
_CONFIG = Config(api_url="https://forge.example.com", token="t")


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class FjwPrCloseArgumentsTest(unittest.TestCase):
    def test_the_comment_argument_is_not_optional(self):
        # A silent unattended close must not be expressible.
        result = _run("o/r", "5")
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: fjw-pr-close", result.stderr)

    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r", "5", "c", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)

    def test_missing_comment_file_is_refused(self):
        result = _run("o/r", "5", _MISSING_COMMENT)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing comment file", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("fjw-pr-close <owner/repo>", result.stdout)


class FjwPrCloseBehaviorTest(unittest.TestCase):
    def setUp(self):
        os.makedirs("/tmp/claude", exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w", dir="/tmp/claude", suffix=".md", delete=False
        )
        handle.write("superseded by #13")
        handle.close()
        self._comment_path = handle.name
        self.addCleanup(os.unlink, self._comment_path)

    def test_comment_posts_before_the_close(self):
        calls = []
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "get_pr",
                                  return_value={"number": 5, "state": "open"}), \
                mock.patch.object(
                    _MODULE.pulls, "create_comment",
                    side_effect=lambda *a: calls.append("comment") or {"id": 9},
                ) as comment, \
                mock.patch.object(
                    _MODULE.pulls, "close_pr",
                    side_effect=lambda *a: calls.append("close") or
                    {"state": "closed", "html_url": "u"},
                ), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "5", self._comment_path]), 0)
        self.assertEqual(calls, ["comment", "close"])
        comment.assert_called_once_with(_CONFIG, "o/r", 5, "superseded by #13")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["action"], "applied")
        self.assertTrue(payload["closed"])
        self.assertEqual(payload["comment"], 9)

    def test_already_closed_is_a_noop_and_posts_nothing(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "get_pr",
                                  return_value={"number": 5, "state": "closed"}), \
                mock.patch.object(_MODULE.pulls, "create_comment") as comment, \
                mock.patch.object(_MODULE.pulls, "close_pr") as close, \
                contextlib.redirect_stdout(io.StringIO()) as stdout, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(_MODULE.main(["o/r", "5", self._comment_path]), 0)
        comment.assert_not_called()
        close.assert_not_called()
        self.assertTrue(json.loads(stdout.getvalue())["noop"])
        self.assertIn("already closed", stderr.getvalue())

    def test_comment_failure_leaves_the_pr_open(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "get_pr",
                                  return_value={"number": 5, "state": "open"}), \
                mock.patch.object(
                    _MODULE.pulls, "create_comment",
                    side_effect=_MODULE.api.ApiError("net down", 6),
                ), \
                mock.patch.object(_MODULE.pulls, "close_pr") as close, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "5", self._comment_path])
        self.assertEqual(caught.exception.code, 6)
        close.assert_not_called()
        self.assertIn("PR left open", stderr.getvalue())

    def test_partial_failure_is_reported_loudly(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "get_pr",
                                  return_value={"number": 5, "state": "open"}), \
                mock.patch.object(_MODULE.pulls, "create_comment",
                                  return_value={"id": 9}), \
                mock.patch.object(
                    _MODULE.pulls, "close_pr",
                    side_effect=_MODULE.api.ApiError("HTTP 500", 1, 500),
                ), \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "5", self._comment_path])
        self.assertEqual(caught.exception.code, 1)
        self.assertIn("PARTIAL", stderr.getvalue())
        self.assertIn("duplicate comment", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
