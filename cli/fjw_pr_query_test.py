"""Tests for the fjw-pr-query executable (the quad-state logic itself lives
in lib/forgejo/pulls_test.py; here the verb's contract is what's under test).

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

_SCRIPT = Path(__file__).resolve().parent / "fjw-pr-query"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)
_CONFIG = Config(api_url="https://forge.example.com", token="t")


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class FjwPrQueryArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r",), ("o/r", "b", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: fjw-pr-query", result.stderr)

    def test_empty_head_branch_is_usage_error(self):
        result = _run("o/r", "   ")
        self.assertEqual(result.returncode, 2)
        self.assertIn("must not be empty", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("fjw-pr-query <owner/repo>", result.stdout)


class FjwPrQueryBehaviorTest(unittest.TestCase):
    def _query(self, state, pr):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "query_state",
                                  return_value=(state, pr)), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            code = _MODULE.main(["o/r", "reconcile/x"])
        return code, json.loads(stdout.getvalue())

    def test_none_is_an_answer_not_an_error(self):
        code, payload = self._query("none", None)
        self.assertEqual(code, 0)
        self.assertEqual(payload["state"], "none")
        self.assertIsNone(payload["pr"])
        self.assertEqual(payload["head"], "reconcile/x")

    def test_every_determinate_state_exits_zero_with_the_raw_pr(self):
        pr = {"number": 4, "mergeable": False, "head": {"ref": "reconcile/x"}}
        for state in ("draft", "mergeable", "conflicted"):
            with self.subTest(state=state):
                code, payload = self._query(state, pr)
                self.assertEqual(code, 0)
                self.assertEqual(payload["state"], state)
                self.assertEqual(payload["pr"]["number"], 4)

    def test_network_failure_exits_retryable(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(
                    _MODULE.pulls, "query_state",
                    side_effect=_MODULE.api.ApiError("net down", 6),
                ), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "b"])
        self.assertEqual(caught.exception.code, 6)


if __name__ == "__main__":
    unittest.main()
