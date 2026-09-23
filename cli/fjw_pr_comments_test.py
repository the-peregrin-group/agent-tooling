"""Tests for the fjw-pr-comments executable.

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
from lib.forgejo.config import Config

_SCRIPT = Path(__file__).resolve().parent / "fjw-pr-comments"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)
_CONFIG = Config(api_url="https://forge.example.com", token="t")


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class FjwPrCommentsArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r",), ("o/r", "5", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: fjw-pr-comments", result.stderr)

    def test_bad_pr_number_is_usage_error(self):
        result = _run("o/r", "zero")
        self.assertEqual(result.returncode, 2)
        self.assertIn("positive integer", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("fjw-pr-comments <owner/repo>", result.stdout)


class FjwPrCommentsBehaviorTest(unittest.TestCase):
    def test_emits_the_raw_comment_array(self):
        comments = [{"id": 1, "body": "hi"}]
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "get_pr", return_value={"number": 5}), \
                mock.patch.object(_MODULE.pulls, "list_comments",
                                  return_value=comments) as listing, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "5"]), 0)
        listing.assert_called_once_with(_CONFIG, "o/r", 5)
        self.assertEqual(json.loads(stdout.getvalue()), comments)

    def test_the_prness_gate_blocks_issue_indices(self):
        # Comments ride the shared issue routes; an index that 404s on
        # /pulls (an issue, or nothing) must exit 3 without reading them.
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(
                    _MODULE.pulls, "get_pr",
                    side_effect=_MODULE.api.ApiError("HTTP 404", 3, 404),
                ), \
                mock.patch.object(_MODULE.pulls, "list_comments") as listing, \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "5"])
        self.assertEqual(caught.exception.code, 3)
        listing.assert_not_called()


if __name__ == "__main__":
    unittest.main()
