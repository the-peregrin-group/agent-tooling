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
import tracker_schema_test_support as fixture

# The fixture's labels, all live, plus one live label it does not declare.
_REGISTRY = ("task", "bug", "chore", "P0", "area:core", "area:docs",
             "site:a", "human", "perf", "wontfix")

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

    def test_empty_kind_label_is_usage_error(self):
        result = _run("o/r", " ", "Title", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("kind label", result.stderr)

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
    is one more label, held to the repo's Tracker Schema and the live
    registry, and a flag-shaped one is refused before anything is fetched.
    The schema fetch and the `gh` seams are mocked."""

    def setUp(self):
        os.makedirs("/tmp/claude", exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w", dir="/tmp/claude", suffix=".md", delete=False
        )
        handle.write("Body.\n")
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        self.body = handle.name

    def _seams(self, schema=None, registry=_REGISTRY):
        """The schema fetch, the registry, and the create, mocked."""
        stack = contextlib.ExitStack()
        fetch_schema = stack.enter_context(mock.patch.object(
            _MODULE.repo_schema, "fetch",
            return_value=schema or fixture.loaded()))
        fetch = stack.enter_context(mock.patch.object(
            _MODULE.boards, "fetch_labels",
            return_value=[{"name": name} for name in registry]))
        create = stack.enter_context(mock.patch.object(
            _MODULE.gh, "issue_create",
            return_value="https://github.com/o/r/issues/7"))
        stderr = stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        return stack, {"fetch_schema": fetch_schema, "fetch": fetch,
                       "create": create, "stderr": stderr}

    def _main_expecting_exit(self, *labels: str, kind="bug", schema=None):
        stack, seam = self._seams(schema)
        with stack, self.assertRaises(SystemExit) as raised:
            _MODULE.main(["o/r", kind, "Title", self.body, *labels])
        seam["create"].assert_not_called()
        return raised.exception.code, seam["fetch"], seam["stderr"].getvalue()

    def _main_filing(self, *labels: str, kind="bug", schema=None):
        stack, seam = self._seams(schema)
        with stack:
            self.assertEqual(
                _MODULE.main(["o/r", kind, "Title", self.body, *labels]), 0)
        return seam["create"].call_args[0][3], seam["stderr"].getvalue()

    def test_surplus_label_outside_the_schema_is_a_policy_refusal(self):
        code, _, stderr = self._main_expecting_exit("area:core", "surplus")
        self.assertEqual(code, 4)
        self.assertIn("'surplus'", stderr)

    def test_label_contract_violations_are_policy_refusals(self):
        # Each passes argument parsing and is refused by the label attachment
        # contract after the schema and registry fetches: exit 4, never 2.
        cases = (
            ("feature", ("area:core",), "not an Issue Kind"),
            ("bug", ("area:core", "chore"), "second kind label"),
            ("bug", ("area:core", "bug"), "duplicates the kind label"),
            ("bug", ("area:core", "wontfix"), "not declared"),
            ("bug", (), "'area:' label"),
            ("bug", ("human",), "'area:' label"),
        )
        for kind, labels, message in cases:
            with self.subTest(kind=kind, labels=labels):
                code, _, stderr = self._main_expecting_exit(*labels, kind=kind)
                self.assertEqual(code, 4)
                self.assertIn(message, stderr)

    def test_flag_shaped_label_is_refused_before_any_fetch(self):
        code, fetch, stderr = self._main_expecting_exit("area:core", "--bogus")
        self.assertEqual(code, 2)
        self.assertIn("takes no flags", stderr)
        fetch.assert_not_called()

    def test_a_kind_and_labels_the_schema_declares_are_filed(self):
        filed, stderr = self._main_filing("area:core", "human", "P0",
                                          kind="chore")
        self.assertEqual(filed, ["chore", "area:core", "human", "P0"])
        self.assertEqual(stderr, "")

    def test_without_tracker_md_filing_goes_ahead_on_the_registry_alone(self):
        filed, stderr = self._main_filing("wontfix", kind="bug",
                                          schema=fixture.missing())
        self.assertEqual(filed, ["bug", "wontfix"])
        self.assertIn("warning: o/r@main:TRACKER.md: not found", stderr)
        self.assertIn("checked only against the live registry", stderr)
        code, _, _ = self._main_expecting_exit("ghost", schema=fixture.missing())
        self.assertEqual(code, 4)

    def test_an_unusable_axes_section_requires_no_axis_and_warns(self):
        document = fixture.document()
        document["issue_label_schema"]["axes"] = {}
        filed, stderr = self._main_filing("perf",
                                          schema=fixture.loaded(document))
        self.assertEqual(filed, ["bug", "perf"])
        self.assertIn("no axis is required", stderr)


class GhwIssueCreateWriteFailureTest(unittest.TestCase):
    def test_failure_exit_codes_route_through_write_exit_code(self):
        ghw_test_support.assert_write_failure_codes(
            self, _MODULE, ["o/r", "bug", "a title", _MISSING_BODY], "issue_create",
            extra_patches=(
                (_MODULE.repo_schema, "fetch",
                 {"return_value": fixture.loaded()}),
                (_MODULE.boards, "fetch_labels",
                 {"return_value": [{"name": "bug"}]}),
                (_MODULE.labels, "validate_creation_labels", {"return_value": None}),
            ))


if __name__ == "__main__":
    unittest.main()
