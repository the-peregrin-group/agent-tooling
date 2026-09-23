"""Tests for the fjw-pr-create executable.

Argument tests run the script as a subprocess with arguments that fail before
any config read or network I/O. Behavior tests load the script as a module
and mock the config/pulls seams.

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

_SCRIPT = Path(__file__).resolve().parent / "fjw-pr-create"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)
_MISSING_BODY = "/tmp/claude/fjw-pr-create-test-missing-body.md"
_CONFIG = Config(api_url="https://forge.example.com", token="t")


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class FjwPrCreateArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r",), ("o/r", "main", "b", "T"),
                          ("o/r", "main", "b", "T", "f", "--draft", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: fjw-pr-create", result.stderr)

    def test_unknown_trailing_flag_is_usage_error(self):
        result = _run("o/r", "main", "b", "T", _MISSING_BODY, "--force")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--draft", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "main", "b", "T", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_head_equal_to_base_is_refused(self):
        result = _run("o/r", "main", "main", "T", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("must differ", result.stderr)

    def test_empty_title_is_usage_error(self):
        result = _run("o/r", "main", "b", "   ", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("title", result.stderr)

    def test_missing_body_file_is_refused_before_config_is_touched(self):
        result = _run("o/r", "main", "b", "T", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing body file", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("fjw-pr-create <owner/repo>", result.stdout)


class FjwPrCreateBehaviorTest(unittest.TestCase):
    def setUp(self):
        os.makedirs("/tmp/claude", exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w", dir="/tmp/claude", suffix=".md", delete=False
        )
        handle.write("pr body")
        handle.close()
        self._body_path = handle.name
        self.addCleanup(os.unlink, self._body_path)

    def test_config_error_exits_with_auth_code(self):
        with mock.patch.object(
            _MODULE.fjw_config, "load",
            side_effect=_MODULE.fjw_config.ConfigError("no config"),
        ), contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "main", "b", "T", self._body_path])
        self.assertEqual(caught.exception.code, 5)
        self.assertIn("no config", stderr.getvalue())

    def test_nonexistent_head_branch_is_a_policy_refusal(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "branch_exists",
                                  side_effect=lambda c, r, b: b == "main"), \
                mock.patch.object(_MODULE.pulls, "create_pr") as create, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "main", "b", "T", self._body_path])
        self.assertEqual(caught.exception.code, 2)
        create.assert_not_called()
        self.assertIn("push it first", stderr.getvalue())

    def test_created_pr_emits_applied_with_the_number(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "branch_exists", return_value=True), \
                mock.patch.object(
                    _MODULE.pulls, "create_pr",
                    return_value={"number": 12, "html_url": "u", "draft": False},
                ) as create, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(
                _MODULE.main(["o/r", "main", "b", "T", self._body_path]), 0
            )
        create.assert_called_once_with(_CONFIG, "o/r", "main", "b", "T", "pr body")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["action"], "applied")
        self.assertEqual(payload["pr"], 12)
        self.assertFalse(payload["draft"])

    def test_draft_applies_the_wip_title_prefix(self):
        # Forgejo's create API has no draft field; the WIP prefix is the
        # documented mechanism (the created PR then reports draft=true).
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "branch_exists", return_value=True), \
                mock.patch.object(
                    _MODULE.pulls, "create_pr",
                    return_value={"number": 12, "html_url": "u", "draft": True},
                ) as create, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(
                _MODULE.main(["o/r", "main", "b", "T", self._body_path, "--draft"]), 0
            )
        self.assertEqual(create.call_args.args[4], "WIP: T")
        self.assertTrue(json.loads(stdout.getvalue())["draft"])

    def test_duplicate_pr_refusal_propagates_exit_4(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "branch_exists", return_value=True), \
                mock.patch.object(
                    _MODULE.pulls, "create_pr",
                    side_effect=_MODULE.api.ApiError("already exists", 4, 409),
                ), \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "main", "b", "T", self._body_path])
        self.assertEqual(caught.exception.code, 4)
        self.assertIn("already exists", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
