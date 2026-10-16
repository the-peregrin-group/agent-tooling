"""Tests for the fjw-pr-reviews executable.

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

_SCRIPT = Path(__file__).resolve().parent / "fjw-pr-reviews"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)
_CONFIG = Config(api_url="https://forge.example.com", token="t")


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class FjwPrReviewsArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r",), ("o/r", "5", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: fjw-pr-reviews", result.stderr)

    def test_bad_repository_is_usage_error(self):
        self.assertEqual(_run("nope", "5").returncode, 2)

    def test_bad_pr_number_is_usage_error(self):
        result = _run("o/r", "zero")
        self.assertEqual(result.returncode, 2)
        self.assertIn("positive integer", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("fjw-pr-reviews <owner/repo>", result.stdout)


class FjwPrReviewsBehaviorTest(unittest.TestCase):
    def _patches(self, **overrides):
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG))
        mocks = {}
        defaults = {"get_pr": {"number": 5}, "list_reviews": [],
                    "list_review_comments": []}
        defaults.update(overrides)
        for name, value in defaults.items():
            kwargs = ({"side_effect": value}
                      if isinstance(value, Exception) else {"return_value": value})
            mocks[name] = stack.enter_context(
                mock.patch.object(_MODULE.pulls, name, **kwargs))
        return stack, mocks

    def test_nests_each_reviews_comments_untouched(self):
        reviews = [
            {"id": 10, "state": "REQUEST_CHANGES", "body": "see inline"},
            {"id": 11, "state": "APPROVED", "body": "ok"},
        ]
        inline = [{"id": 1, "path": "a.py", "line": 3, "position": 3,
                   "pull_request_review_id": 10, "body": "nit"}]
        stack, mocks = self._patches(list_reviews=reviews)
        mocks["list_review_comments"].side_effect = [inline, []]
        with stack, contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "5"]), 0)
        output = json.loads(stdout.getvalue())
        self.assertEqual(output[0]["comments"], inline)
        self.assertEqual(output[0]["state"], "REQUEST_CHANGES")
        self.assertEqual(output[1]["comments"], [])  # review kept with no inline
        mocks["list_review_comments"].assert_any_call(_CONFIG, "o/r", 5, 10)
        mocks["list_review_comments"].assert_any_call(_CONFIG, "o/r", 5, 11)

    def test_no_reviews_is_an_empty_array(self):
        stack, _ = self._patches()
        with stack, contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "5"]), 0)
        self.assertEqual(json.loads(stdout.getvalue()), [])

    def test_the_prness_gate_blocks_issue_indices(self):
        stack, mocks = self._patches(
            get_pr=_MODULE.api.ApiError("HTTP 404", 3, 404))
        with stack, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "5"])
        self.assertEqual(caught.exception.code, 3)
        mocks["list_reviews"].assert_not_called()
        mocks["list_review_comments"].assert_not_called()

    def test_api_error_exit_code_propagates(self):
        for code in (1, 6):
            with self.subTest(code=code):
                stack, _ = self._patches(
                    list_reviews=_MODULE.api.ApiError("boom", code, None))
                with stack, contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        _MODULE.main(["o/r", "5"])
                self.assertEqual(caught.exception.code, code)

    def test_config_failure_is_exit_5(self):
        with mock.patch.object(
                _MODULE.fjw_config, "load",
                side_effect=_MODULE.fjw_config.ConfigError("no config")), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "5"])
        self.assertEqual(caught.exception.code, 5)


class FjwPrReviewsArgumentContractTest(
    ghw_test_support.ArgumentContractTests, unittest.TestCase
):
    SCRIPT = _SCRIPT
    LONGEST = ("o/r", "5")


if __name__ == "__main__":
    unittest.main()
