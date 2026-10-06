"""Tests for the fjw-pr-comment executable: the head-prefix positional scope
token and its trust-but-verify enforcement.

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

_SCRIPT = Path(__file__).resolve().parent / "fjw-pr-comment"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)
_MISSING_BODY = "/tmp/claude/fjw-pr-comment-test-missing-body.md"
_CONFIG = Config(api_url="https://forge.example.com", token="t")


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class FjwPrCommentArgumentsTest(unittest.TestCase):
    def test_there_is_no_prefix_free_form(self):
        # Three arguments (repo, pr#, body) must not parse: standalone
        # comments on arbitrary PRs are deliberately inexpressible.
        result = _run("o/r", "5", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: fjw-pr-comment", result.stderr)

    def test_non_grammar_head_prefix_is_usage_error(self):
        # Same grammar as gitw's branch prefix; a slashless 'reconcile'
        # would match 'reconciled-elsewhere' too.
        for prefix in ("", "  ", "reconcile", "Fix/", "a/b/", "//"):
            with self.subTest(prefix=prefix):
                result = _run("o/r", prefix, "5", _MISSING_BODY)
                self.assertEqual(result.returncode, 2)
                self.assertIn("head-prefix", result.stderr)

    def test_missing_body_file_is_refused(self):
        result = _run("o/r", "reconcile/", "5", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing body file", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("fjw-pr-comment <owner/repo>", result.stdout)


class FjwPrCommentBehaviorTest(unittest.TestCase):
    def setUp(self):
        os.makedirs("/tmp/claude", exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w", dir="/tmp/claude", suffix=".md", delete=False
        )
        handle.write("status update")
        handle.close()
        self._body_path = handle.name
        self.addCleanup(os.unlink, self._body_path)

    def test_prefix_mismatch_refuses_and_posts_nothing(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(
                    _MODULE.pulls, "get_pr",
                    return_value={"number": 5, "head": {"ref": "feature-x"}},
                ), \
                mock.patch.object(_MODULE.pulls, "create_comment") as comment, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "reconcile/", "5", self._body_path])
        self.assertEqual(caught.exception.code, 4)
        comment.assert_not_called()
        self.assertIn("does not match the claimed prefix", stderr.getvalue())

    def test_matching_prefix_posts_the_staged_body(self):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(
                    _MODULE.pulls, "get_pr",
                    return_value={"number": 5, "head": {"ref": "reconcile/2001-02-03"}},
                ), \
                mock.patch.object(
                    _MODULE.pulls, "create_comment",
                    return_value={"id": 11, "html_url": "u"},
                ) as comment, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(
                _MODULE.main(["o/r", "reconcile/", "5", self._body_path]), 0
            )
        comment.assert_called_once_with(_CONFIG, "o/r", 5, "status update")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["action"], "applied")
        self.assertEqual(payload["head"], "reconcile/2001-02-03")

    def test_missing_head_ref_in_the_pr_object_refuses(self):
        # A malformed PR object must fail closed, not comment anyway.
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(_MODULE.pulls, "get_pr",
                                  return_value={"number": 5, "head": None}), \
                mock.patch.object(_MODULE.pulls, "create_comment") as comment, \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "reconcile/", "5", self._body_path])
        self.assertEqual(caught.exception.code, 4)
        comment.assert_not_called()


    def _comment_with_head(self, prefix, head):
        with mock.patch.object(_MODULE.fjw_config, "load", return_value=_CONFIG), \
                mock.patch.object(
                    _MODULE.pulls, "get_pr",
                    return_value={"number": 5, "head": head},
                ), \
                mock.patch.object(
                    _MODULE.pulls, "create_comment",
                    return_value={"id": 11, "html_url": "u"},
                ) as comment, \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            try:
                code = _MODULE.main(["o/r", prefix, "5", self._body_path])
            except SystemExit as caught:
                code = caught.code
        return code, comment

    def test_bare_slash_comments_on_any_head(self):
        # 'main' included: commenting moves no branch, so fjw's bare
        # slash admits the default too.
        for head in ("foo-bar", "reconcile/2001-02-03", "main"):
            with self.subTest(head=head):
                code, comment = self._comment_with_head("/", {"ref": head})
                self.assertEqual(code, 0)
                comment.assert_called_once()

    def test_bare_slash_still_refuses_a_missing_head_ref(self):
        code, comment = self._comment_with_head("/", None)
        self.assertEqual(code, 4)
        comment.assert_not_called()


if __name__ == "__main__":
    unittest.main()
