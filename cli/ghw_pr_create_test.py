"""Tests for the ghw-pr-create executable.

Argument tests run the script as a subprocess with arguments that fail before
any network I/O. Behavior tests load the script as a module and mock the lib
gh/boards seams. Either way, no `gh` calls are made.

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

_SCRIPT = Path(__file__).resolve().parent / "ghw-pr-create"
_MISSING_BODY = "/tmp/claude/ghw-pr-create-test-missing-body.md"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


class GhwPrCreateArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r", "main", "feat", "Title"),
                          ("o/r", "main", "feat", "Title", "b", "--draft", "x")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: ghw-pr-create", result.stderr)

    def test_tail_flag_other_than_draft_is_usage_error(self):
        # The --delete lesson: no other trailing flag may ride the tail.
        result = _run("o/r", "main", "feat", "Title", _MISSING_BODY, "--force")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--draft", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "main", "feat", "Title", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_head_equal_to_base_is_refused(self):
        result = _run("o/r", "main", "main", "Title", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("must differ", result.stderr)

    def test_empty_branch_name_is_usage_error(self):
        result = _run("o/r", "  ", "feat", "Title", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("must not be empty", result.stderr)

    def test_empty_title_is_usage_error(self):
        result = _run("o/r", "main", "feat", "   ", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("title", result.stderr)

    def test_missing_body_file_is_refused(self):
        result = _run("o/r", "main", "feat", "Title", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing body file", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ghw-pr-create <repo>", result.stdout)


class GhwPrCreateBehaviorTest(unittest.TestCase):
    def setUp(self):
        os.makedirs("/tmp/claude", exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w", dir="/tmp/claude", suffix=".md", delete=False
        )
        handle.write("pr body")
        handle.close()
        self._body_path = handle.name
        self.addCleanup(os.unlink, self._body_path)

    def test_nonexistent_head_branch_is_a_policy_refusal(self):
        with mock.patch.object(_MODULE, "_current_branch", return_value=None), \
                mock.patch.object(_MODULE.boards, "fetch_branches_exist",
                                  return_value={"main": True, "feat": False}), \
                mock.patch.object(_MODULE.gh, "pr_create") as create, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "main", "feat", "Title", self._body_path])
        self.assertEqual(caught.exception.code, 2)
        create.assert_not_called()
        self.assertIn("push it first", stderr.getvalue())

    def test_created_pr_emits_applied_with_the_number(self):
        with mock.patch.object(_MODULE, "_current_branch", return_value=None), \
                mock.patch.object(_MODULE.boards, "fetch_branches_exist",
                                  return_value={"main": True, "feat": True}), \
                mock.patch.object(_MODULE.gh, "pr_create",
                                  return_value={"number": 12, "html_url": "u"}) as create, \
                contextlib.redirect_stderr(io.StringIO()), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(
                _MODULE.main(["o/r", "main", "feat", "Title", self._body_path]), 0
            )
        create.assert_called_once_with("o/r", "main", "feat", "Title", "pr body", False)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["action"], "applied")
        self.assertEqual(payload["pr"], 12)
        self.assertFalse(payload["draft"])

    def test_cwd_branch_mismatch_warns_but_does_not_refuse(self):
        # The wrapper warns -- never refuses -- when cwd's checked-out branch
        # differs from the stated head: opening a PR for a branch you are not
        # standing on is legitimate.
        with mock.patch.object(_MODULE, "_current_branch", return_value="elsewhere"), \
                mock.patch.object(_MODULE.boards, "fetch_branches_exist",
                                  return_value={"main": True, "feat": True}), \
                mock.patch.object(_MODULE.gh, "pr_create",
                                  return_value={"number": 12, "html_url": "u"}) as create, \
                contextlib.redirect_stderr(io.StringIO()) as stderr, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(
                _MODULE.main(["o/r", "main", "feat", "Title", self._body_path]), 0
            )
        create.assert_called_once()
        self.assertIn("warning:", stderr.getvalue())
        self.assertIn("'elsewhere'", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
