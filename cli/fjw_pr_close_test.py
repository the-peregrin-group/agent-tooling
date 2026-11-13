"""Tests for the fjw-pr-close executable: comment-then-close ordering, the
mandatory comment, the already-closed no-op, the idempotent re-run that
does not post its comment twice, and partial completion (exit 5).

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
_CONTRACT_BODY = "/tmp/claude/argument-contract-body.md"
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

    def _patches(self, *, state="open", comments=(), comment=None,
                 close=None, reads=None):
        """Patch the config and every pulls call; returns an ExitStack and
        the create_comment and close_pr mocks."""
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG)
        )
        stack.enter_context(mock.patch.object(
            _MODULE.pulls, "get_pr", return_value={"number": 5, "state": state}
        ))
        stack.enter_context(mock.patch.object(
            _MODULE.pulls, "list_comments",
            **(reads or {"return_value": list(comments)}),
        ))
        create = stack.enter_context(mock.patch.object(
            _MODULE.pulls, "create_comment",
            **(comment or {"return_value": {"id": 9, "user": {"login": "fjw-bot"}}}),
        ))
        close_mock = stack.enter_context(mock.patch.object(
            _MODULE.pulls, "close_pr",
            **(close or {"return_value": {"state": "closed", "html_url": "u"}}),
        ))
        return stack, create, close_mock

    def _exit_code(self, stack) -> tuple:
        with stack, contextlib.redirect_stderr(io.StringIO()) as stderr, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "5", self._comment_path])
        return caught.exception.code, stderr.getvalue()

    def test_comment_posts_before_the_close(self):
        calls = []
        stack, create, _close = self._patches(
            comment={"side_effect": lambda *a: calls.append("comment") or {"id": 9}},
            close={"side_effect": lambda *a: calls.append("close") or
                   {"state": "closed", "html_url": "u"}},
        )
        with stack, contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "5", self._comment_path]), 0)
        self.assertEqual(calls, ["comment", "close"])
        create.assert_called_once_with(_CONFIG, "o/r", 5, "superseded by #13")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["action"], "applied")
        self.assertTrue(payload["closed"])
        self.assertEqual(payload["comment"], 9)
        self.assertTrue(payload["comment_posted"])

    def test_already_closed_is_a_noop_and_posts_nothing(self):
        stack, create, close = self._patches(state="closed")
        with stack, contextlib.redirect_stdout(io.StringIO()) as stdout, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(_MODULE.main(["o/r", "5", self._comment_path]), 0)
        create.assert_not_called()
        close.assert_not_called()
        self.assertTrue(json.loads(stdout.getvalue())["noop"])
        self.assertIn("already closed", stderr.getvalue())

    def test_a_matching_last_comment_is_not_posted_again(self):
        # The re-run after a partial failure: the comment already landed.
        comments = [{"id": 2, "user": {"login": "human"}, "body": "hmm"},
                    {"id": 4, "user": {"login": "fjw-bot"},
                     "body": "Superseded by #13\r\n"}]
        stack, create, close = self._patches(comments=comments)
        with stack, contextlib.redirect_stdout(io.StringIO()) as stdout, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(_MODULE.main(["o/r", "5", self._comment_path]), 0)
        create.assert_not_called()
        close.assert_called_once()
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["comment"], 4)
        self.assertFalse(payload["comment_posted"])
        self.assertIn("not posting it again", stderr.getvalue())

    def test_matching_last_comment_by_another_account_counts(self):
        # Accepted trade-off: the author is not checked.
        comments = [{"id": 4, "user": {"login": "human"},
                     "body": "superseded by #13"}]
        stack, create, close = self._patches(comments=comments)
        with stack, contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(_MODULE.main(["o/r", "5", self._comment_path]), 0)
        create.assert_not_called()
        close.assert_called_once()

    def test_a_match_followed_by_another_comment_posts_again(self):
        comments = [{"id": 4, "user": {"login": "fjw-bot"},
                     "body": "superseded by #13"},
                    {"id": 5, "user": {"login": "human"}, "body": "reopening"}]
        stack, create, _close = self._patches(comments=comments)
        with stack, contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "5", self._comment_path]), 0)
        create.assert_called_once()
        self.assertTrue(json.loads(stdout.getvalue())["comment_posted"])

    def test_comment_failure_leaves_the_pr_open(self):
        stack, _create, close = self._patches(
            comment={"side_effect": _MODULE.api.ApiError("net down", 1)}
        )
        code, stderr = self._exit_code(stack)
        self.assertEqual(code, 1)
        close.assert_not_called()
        self.assertIn("PR left open", stderr)
        self.assertIn("will not post the comment twice", stderr)

    def test_close_failure_after_the_comment_is_partial_completion(self):
        stack, _create, _close = self._patches(
            close={"side_effect": _MODULE.api.ApiError("HTTP 500", 1, 500)}
        )
        code, stderr = self._exit_code(stack)
        self.assertEqual(code, 5)
        self.assertIn("PARTIAL", stderr)
        self.assertIn("re-run fjw-pr-close with the same comment file", stderr)

    def test_close_failure_after_a_found_comment_is_partial_completion(self):
        comments = [{"id": 4, "user": {"login": "fjw-bot"},
                     "body": "superseded by #13"}]
        stack, create, _close = self._patches(
            comments=comments,
            close={"side_effect": _MODULE.api.ApiError("HTTP 403", 4, 403)},
        )
        code, stderr = self._exit_code(stack)
        self.assertEqual(code, 5)
        create.assert_not_called()
        self.assertIn("comment 4", stderr)
        self.assertIn("alone, that failure would exit 4", stderr)

    def test_unreadable_comments_post_nothing_and_leave_the_pr_open(self):
        stack, create, close = self._patches(
            reads={"side_effect": _MODULE.api.ApiError("HTTP 500", 1, 500)}
        )
        code, stderr = self._exit_code(stack)
        self.assertEqual(code, 1)
        create.assert_not_called()
        close.assert_not_called()
        self.assertIn("nothing posted, PR left open", stderr)



class FjwPrCloseArgumentContractTest(
    ghw_test_support.ArgumentContractTests, unittest.TestCase
):
    SCRIPT = _SCRIPT
    LONGEST = ("o/r", "5", _CONTRACT_BODY)


if __name__ == "__main__":
    unittest.main()
