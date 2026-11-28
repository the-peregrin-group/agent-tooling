"""Tests for the ghw-issue-edit executable.

Argument tests run the script as a subprocess with arguments that fail before
any network I/O. Behavior tests load the script as a module and mock the lib
gh/boards seams and the Tracker Schema fetch (tracker_schema_test_support's
fixture). Either way, no `gh` calls are made.

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
import tracker_schema_test_support as fixture

_SCRIPT = Path(__file__).resolve().parent / "ghw-issue-edit"
_MISSING_BODY = "/tmp/claude/ghw-issue-edit-test-missing-body.md"

# The fixture's labels, all live, plus one live label it does not declare.
_REGISTRY = ("task", "bug", "chore", "area:core", "area:docs", "site:a",
             "human", "perf", "wontfix")


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


class GhwIssueEditArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r", "retitle", "5"),
                          ("o/r", "retitle", "5", "New", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: ghw-issue-edit", result.stderr)

    def test_unknown_subverb_is_usage_error(self):
        result = _run("o/r", "close", "5", "value")
        self.assertEqual(result.returncode, 2)
        self.assertIn("add-label|remove-label|retitle|set-body", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "retitle", "5", "New title")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_bad_issue_number_is_usage_error(self):
        result = _run("o/r", "retitle", "zero", "New title")
        self.assertEqual(result.returncode, 2)
        self.assertIn("positive integer", result.stderr)

    def test_empty_value_is_usage_error(self):
        for subverb in ("add-label", "remove-label", "retitle"):
            with self.subTest(subverb=subverb):
                result = _run("o/r", subverb, "5", "   ")
                self.assertEqual(result.returncode, 2)
                self.assertIn("non-empty value", result.stderr)

    def test_set_body_value_must_be_a_staged_file(self):
        result = _run("o/r", "set-body", "5", _MISSING_BODY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing body file", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ghw-issue-edit <repo>", result.stdout)


class GhwIssueEditBehaviorTest(unittest.TestCase):

    def _edit(self, subverb, label, attached, schema=None):
        """Run one label edit on issue 5 carrying `attached`; returns (exit
        code, the issue_edit_labels mock, stdout, stderr)."""
        with mock.patch.object(_MODULE.repo_schema, "fetch",
                               return_value=schema or fixture.loaded()), \
                mock.patch.object(_MODULE.boards, "fetch_labels",
                                  return_value=[{"name": name}
                                                for name in _REGISTRY]), \
                mock.patch.object(_MODULE.gh, "issue_view", return_value={
                    "labels": [{"name": name} for name in attached]}), \
                mock.patch.object(_MODULE.gh, "issue_edit_labels") as edit, \
                contextlib.redirect_stdout(io.StringIO()) as stdout, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            try:
                code = _MODULE.main(["o/r", subverb, "5", label])
            except SystemExit as stop:
                code = stop.code
        return code, edit, stdout.getvalue(), stderr.getvalue()

    def test_re_adding_a_present_label_is_a_no_op(self):
        code, edit, stdout, _ = self._edit("add-label", "perf", ["perf"])
        self.assertEqual(code, 0)
        edit.assert_not_called()
        self.assertFalse(json.loads(stdout)["changed"])

    def test_second_kind_label_is_a_policy_refusal_naming_the_incumbent(self):
        code, edit, _, stderr = self._edit("add-label", "chore", ["bug"])
        self.assertEqual(code, 4)
        edit.assert_not_called()
        self.assertIn("'bug'", stderr)

    def test_an_undeclared_live_label_is_a_policy_refusal(self):
        code, edit, _, stderr = self._edit("add-label", "wontfix", ["bug"])
        self.assertEqual(code, 4)
        edit.assert_not_called()
        self.assertIn("not declared", stderr)

    def test_a_declared_label_missing_from_the_registry_is_a_policy_refusal(self):
        code, edit, _, stderr = self._edit("add-label", "P1", ["bug"])
        self.assertEqual(code, 4)
        edit.assert_not_called()
        self.assertIn("label registry", stderr)

    def test_the_human_label_adds_and_removes_as_an_ordinary_label(self):
        for subverb, attached, add, remove in (
                ("add-label", ["bug", "area:core"], ["human"], []),
                ("remove-label", ["bug", "area:core", "human"], [], ["human"])):
            with self.subTest(subverb=subverb):
                code, edit, stdout, _ = self._edit(subverb, "human", attached)
                self.assertEqual(code, 0)
                edit.assert_called_once_with("o/r", 5, add=add, remove=remove)
                self.assertTrue(json.loads(stdout)["changed"])

    def test_removing_an_absent_label_is_a_no_op(self):
        code, edit, stdout, _ = self._edit("remove-label", "perf", ["bug"])
        self.assertEqual(code, 0)
        edit.assert_not_called()
        self.assertFalse(json.loads(stdout)["changed"])

    def test_the_last_label_of_a_required_axis_cannot_be_removed(self):
        code, edit, _, stderr = self._edit("remove-label", "area:core",
                                           ["bug", "area:core"])
        self.assertEqual(code, 4)
        edit.assert_not_called()
        self.assertIn("last 'area:' label", stderr)
        code, edit, _, _ = self._edit("remove-label", "area:core",
                                      ["bug", "area:core", "area:docs"])
        self.assertEqual(code, 0)
        edit.assert_called_once()

    def test_without_tracker_md_label_edits_go_ahead_on_the_registry(self):
        code, edit, _, stderr = self._edit("add-label", "wontfix", ["bug"],
                                           schema=fixture.missing())
        self.assertEqual(code, 0)
        edit.assert_called_once()
        self.assertIn("warning: o/r@main:TRACKER.md: not found", stderr)
        code, edit, _, _ = self._edit("remove-label", "area:core",
                                      ["bug", "area:core"],
                                      schema=fixture.missing())
        self.assertEqual(code, 0)
        edit.assert_called_once()

    def test_retitle_does_not_read_the_schema(self):
        with mock.patch.object(_MODULE.repo_schema, "fetch") as fetch, \
                mock.patch.object(_MODULE.gh, "issue_view",
                                  return_value={"title": "Same"}), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(_MODULE.main(["o/r", "retitle", "5", "Same"]), 0)
        fetch.assert_not_called()


class GhwIssueEditArgumentContractTest(
    ghw_test_support.ArgumentContractTests, unittest.TestCase
):
    SCRIPT = _SCRIPT
    LONGEST = ("o/r", "retitle", "5", "New")


if __name__ == "__main__":
    unittest.main()
