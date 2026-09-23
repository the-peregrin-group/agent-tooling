"""Tests for the fjw-pr-list executable.

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

_SCRIPT = Path(__file__).resolve().parent / "fjw-pr-list"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)
_CONFIG = Config(api_url="https://forge.example.com", token="t")


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class FjwPrListArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: fjw-pr-list", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("fjw-pr-list <owner/repo>", result.stdout)


class FjwPrListBehaviorTest(unittest.TestCase):
    def test_emits_the_raw_pr_array(self):
        prs = [{"number": 1, "head": {"ref": "b"}}]
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "list_open_prs",
                                  return_value=prs) as listing, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r"]), 0)
        listing.assert_called_once_with(_CONFIG, "o/r")
        self.assertEqual(json.loads(stdout.getvalue()), prs)

    def test_empty_repo_emits_an_empty_array_with_success(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "list_open_prs", return_value=[]), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r"]), 0)
        self.assertEqual(json.loads(stdout.getvalue()), [])

    def test_api_error_exits_with_its_class(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(
                    _MODULE.pulls, "list_open_prs",
                    side_effect=_MODULE.api.ApiError("no repo", 3, 404),
                ), \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r"])
        self.assertEqual(caught.exception.code, 3)
        self.assertIn("no repo", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
