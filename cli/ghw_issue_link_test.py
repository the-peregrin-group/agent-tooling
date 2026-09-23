"""Tests for the ghw-issue-link executable.

Argument tests run the script as a subprocess with arguments that fail before
any network I/O. Behavior tests load the script as a module and mock the lib
gh seam. Either way, no `gh` calls are made.

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

_SCRIPT = Path(__file__).resolve().parent / "ghw-issue-link"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


@contextlib.contextmanager
def _linked(numbers: list[int], total: int | None = None):
    """Mock the gh seam: `numbers` are already linked to the subject issue.

    `total` overrides the server-side count, so a value above len(numbers)
    stands for edges gh paged away.
    """
    payload = {"nodes": [{"number": number} for number in numbers],
               "totalCount": len(numbers) if total is None else total}
    with mock.patch.object(_MODULE.gh, "version", return_value=(2, 97, 0)), \
            mock.patch.object(_MODULE.gh, "issue_view",
                              return_value={"subIssues": payload,
                                            "blockedBy": payload}), \
            mock.patch.object(_MODULE.gh, "issue_edit_dependency") as edit, \
            contextlib.redirect_stdout(io.StringIO()) as stdout:
        yield edit, stdout


class GhwIssueLinkArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r",), ("o/r", "add-sub", "1"),
                          ("o/r", "add-sub", "1", "2", "3")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: ghw-issue-link", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "add-sub", "1", "2")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_unknown_subverb_teaches_the_blocked_by_spelling(self):
        # "X blocks Y" has exactly one spelling; the error must say which.
        result = _run("o/r", "add-blocking", "1", "2")
        self.assertEqual(result.returncode, 2)
        self.assertIn("add-blocked-by Y X", result.stderr)

    def test_non_numeric_issue_is_usage_error(self):
        for arguments in (("o/r", "add-sub", "one", "2"),
                          ("o/r", "add-sub", "1", "two")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("positive integers", result.stderr)

    def test_self_link_is_refused(self):
        result = _run("o/r", "add-sub", "7", "#7")
        self.assertEqual(result.returncode, 2)
        self.assertIn("itself", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ghw-issue-link <repo>", result.stdout)


class GhwIssueLinkBehaviorTest(unittest.TestCase):
    def test_adding_a_new_edge_writes_it(self):
        with _linked([]) as (edit, stdout):
            self.assertEqual(_MODULE.main(["o/r", "add-sub", "7", "8"]), 0)
        edit.assert_called_once_with("o/r", 7, "add-sub", 8)
        self.assertTrue(json.loads(stdout.getvalue())["changed"])

    def test_adding_an_existing_edge_is_a_no_op(self):
        with _linked([8]) as (edit, stdout):
            self.assertEqual(_MODULE.main(["o/r", "add-sub", "7", "8"]), 0)
        edit.assert_not_called()
        self.assertFalse(json.loads(stdout.getvalue())["changed"])

    def test_removing_an_existing_edge_writes_it(self):
        with _linked([8]) as (edit, stdout):
            self.assertEqual(_MODULE.main(["o/r", "remove-blocked-by", "7", "8"]), 0)
        edit.assert_called_once_with("o/r", 7, "remove-blocked-by", 8)
        self.assertTrue(json.loads(stdout.getvalue())["changed"])

    def test_removing_an_absent_edge_is_a_no_op(self):
        with _linked([9]) as (edit, stdout):
            self.assertEqual(_MODULE.main(["o/r", "remove-blocked-by", "7", "8"]), 0)
        edit.assert_not_called()
        self.assertFalse(json.loads(stdout.getvalue())["changed"])

    def test_truncated_edges_refuse_to_claim_a_no_op(self):
        # gh returns only the first page of edges (100 sub-issues, 50
        # dependencies). Reporting "already unlinked" for a target that could
        # be sitting on an unread page would leave the edge in place while
        # claiming success.
        with _linked([9], total=120) as (edit, _):
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as caught:
                    _MODULE.main(["o/r", "remove-sub", "7", "8"])
        self.assertEqual(caught.exception.code, 1)
        self.assertIn("120", stderr.getvalue())
        self.assertIn("gh issue edit", stderr.getvalue())
        edit.assert_not_called()

    def test_truncation_also_refuses_an_unverifiable_add(self):
        with _linked([9], total=120) as (edit, _):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    _MODULE.main(["o/r", "add-sub", "7", "8"])
        self.assertEqual(caught.exception.code, 1)
        edit.assert_not_called()

    def test_a_target_found_on_the_first_page_is_actionable_despite_truncation(self):
        with _linked([8, 9], total=120) as (edit, stdout):
            self.assertEqual(_MODULE.main(["o/r", "remove-sub", "7", "8"]), 0)
        edit.assert_called_once_with("o/r", 7, "remove-sub", 8)
        self.assertTrue(json.loads(stdout.getvalue())["changed"])

    def test_gh_below_the_floor_fails_before_any_write(self):
        with mock.patch.object(_MODULE.gh, "version", return_value=(2, 93, 9)), \
                mock.patch.object(_MODULE.gh, "issue_edit_dependency") as edit, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "add-sub", "7", "8"])
        self.assertEqual(caught.exception.code, 1)
        self.assertIn("2.94.0", stderr.getvalue())
        self.assertIn("2.93.9", stderr.getvalue())
        edit.assert_not_called()


class LinkedIssueNumbersTest(unittest.TestCase):
    def test_reads_ghs_nodes_envelope(self):
        payload = {"nodes": [{"number": 3}, {"number": 4}], "totalCount": 2}
        self.assertEqual(
            _MODULE._linked_issue_numbers(payload, "o/r"), {3, 4}
        )

    def test_accepts_a_bare_list_too(self):
        # Shape insurance: a future gh could drop the envelope, and a crash
        # here would be worse than one redundant idempotent edit.
        self.assertEqual(
            _MODULE._linked_issue_numbers([{"number": 3}], "o/r"), {3}
        )

    def test_empty_and_null_payloads_are_empty(self):
        for payload in (None, [], {"nodes": [], "totalCount": 0}):
            with self.subTest(payload=payload):
                self.assertEqual(_MODULE._linked_issue_numbers(payload, "o/r"), set())

    def test_foreign_repo_entry_with_the_same_number_is_dropped(self):
        # Dependencies may cross repos; this wrapper's numbers never do.
        payload = {"nodes": [
            {"number": 3, "url": "https://github.com/other/repo/issues/3"},
            {"number": 4, "url": "https://github.com/o/r/issues/4"},
        ]}
        self.assertEqual(_MODULE._linked_issue_numbers(payload, "o/r"), {4})

    def test_repository_object_is_honored_when_present(self):
        payload = {"nodes": [
            {"number": 3, "repository": {"name": "repo",
                                         "owner": {"login": "other"}}},
            {"number": 4, "repository": {"name": "r", "owner": {"login": "o"}}},
        ]}
        self.assertEqual(_MODULE._linked_issue_numbers(payload, "o/r"), {4})

    def test_entries_without_a_usable_number_are_skipped(self):
        payload = {"nodes": [{"title": "no number"}, "junk", {"number": "5"}]}
        self.assertEqual(_MODULE._linked_issue_numbers(payload, "o/r"), set())


if __name__ == "__main__":
    unittest.main()
