"""Argument-validation tests for the ghw-issue-create executable.

Most tests run the script as a subprocess with arguments that fail before
any network I/O; the label-tail tests load it as a module with the `gh`
seams mocked. No `gh` calls are made.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ghw_test_support

_SCRIPT = Path(__file__).resolve().parent / "ghw-issue-create"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)
_CONTRACT_BODY = "/tmp/claude/argument-contract-body.md"
_MISSING_BODY = "/tmp/claude/ghw-issue-create-test-missing-body.md"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class GhwIssueCreateArgumentsTest(unittest.TestCase):
    def test_no_arguments_is_usage_error(self):
        result = _run()
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: ghw-issue-create", result.stderr)

    def test_three_arguments_is_usage_error(self):
        result = _run("o/r", "bug", "title only")
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "bug", "Title", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_unknown_type_label_is_refused(self):
        result = _run("o/r", "task", "Title", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("feature|improvement|bug|debt|meta", result.stderr)

    def test_empty_title_is_usage_error(self):
        result = _run("o/r", "bug", "   ", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("title", result.stderr)

    def test_missing_body_file_is_refused(self):
        result = _run("o/r", "bug", "Title", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing body file", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        for flag in ("-h", "--help"):
            with self.subTest(flag=flag):
                result = _run(flag)
                self.assertEqual(result.returncode, 0)
                self.assertIn("ghw-issue-create <repo>", result.stdout)


class GhwIssueCreateArgumentContractTest(
    ghw_test_support.ArgumentContractTests, unittest.TestCase
):
    SCRIPT = _SCRIPT
    LONGEST = ("o/r", "bug", "Title", _CONTRACT_BODY, "area:cli")
    FLAG_SLOT_FORMS = (
        ("o/r", "bug", "Title", _CONTRACT_BODY, "--bogus"),
    )
    VARIADIC = True


class GhwIssueCreateLabelTailTest(unittest.TestCase):
    """The variadic label tail consumes every element: a surplus positional
    is one more label, held to the live registry, and a flag-shaped one is
    refused before the registry is fetched. The `gh` seams are mocked."""

    def setUp(self):
        os.makedirs("/tmp/claude", exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w", dir="/tmp/claude", suffix=".md", delete=False
        )
        handle.write("Body.\n")
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        self.body = handle.name

    def _main_expecting_exit(self, *labels: str):
        registry = [{"name": "bug"}, {"name": "area:cli"}]
        stderr = io.StringIO()
        with mock.patch.object(_MODULE.boards, "fetch_labels",
                               return_value=registry) as fetch, \
                mock.patch.object(_MODULE.gh, "issue_create") as create, \
                contextlib.redirect_stderr(stderr), \
                self.assertRaises(SystemExit) as raised:
            _MODULE.main(["o/r", "bug", "Title", self.body, *labels])
        create.assert_not_called()
        return raised.exception.code, fetch, stderr.getvalue()

    def test_surplus_label_outside_the_registry_is_usage_error(self):
        code, _, stderr = self._main_expecting_exit("area:cli", "surplus")
        self.assertEqual(code, 2)
        self.assertIn("'surplus'", stderr)

    def test_flag_shaped_label_is_refused_before_the_registry_fetch(self):
        code, fetch, stderr = self._main_expecting_exit("area:cli", "--bogus")
        self.assertEqual(code, 2)
        self.assertIn("takes no flags", stderr)
        fetch.assert_not_called()


class GhwIssueCreateWriteFailureTest(unittest.TestCase):
    def test_failure_exit_codes_route_through_write_exit_code(self):
        ghw_test_support.assert_write_failure_codes(
            self, _MODULE, ["o/r", "bug", "a title", _MISSING_BODY], "issue_create",
            extra_patches=(
                (_MODULE.boards, "fetch_labels",
                 {"return_value": [{"name": "bug"}]}),
                (_MODULE.labels, "validate_creation_labels", {"return_value": None}),
            ))


if __name__ == "__main__":
    unittest.main()
