"""Tests for the fjw-pr-view executable.

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

_SCRIPT = Path(__file__).resolve().parent / "fjw-pr-view"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)
_CONFIG = Config(api_url="https://forge.example.com", token="t")


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class FjwPrViewArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r",), ("o/r", "5", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: fjw-pr-view", result.stderr)

    def test_bad_pr_number_is_usage_error(self):
        for bad_number in ("0", "-1", "abc", "4.2"):
            with self.subTest(number=bad_number):
                result = _run("o/r", bad_number)
                self.assertEqual(result.returncode, 2)
                self.assertIn("positive integer", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("fjw-pr-view <owner/repo>", result.stdout)


class FjwPrViewBehaviorTest(unittest.TestCase):
    def test_emits_the_raw_pr_object(self):
        pr = {"number": 7, "state": "open", "head": {"ref": "b"}}
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "get_pr", return_value=pr) as get, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "7"]), 0)
        get.assert_called_once_with(_CONFIG, "o/r", 7)
        self.assertEqual(json.loads(stdout.getvalue()), pr)

    def test_hash_prefixed_number_is_tolerated(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "get_pr", return_value={}) as get, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(_MODULE.main(["o/r", "#7"]), 0)
        self.assertEqual(get.call_args.args[2], 7)

    def test_no_such_pr_exits_not_found(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(
                    _MODULE.pulls, "get_pr",
                    side_effect=_MODULE.api.ApiError("HTTP 404", 3, 404),
                ), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "7"])
        self.assertEqual(caught.exception.code, 3)


if __name__ == "__main__":
    unittest.main()
