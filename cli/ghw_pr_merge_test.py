"""Tests for the ghw-pr-merge executable.

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

_SCRIPT = Path(__file__).resolve().parent / "ghw-pr-merge"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


def _pull(**overrides) -> dict:
    """Fake the `gh pr view --json state,isDraft,baseRefName,statusCheckRollup`
    shape the wrapper reads, plus headRefOid."""
    pull = {"number": 5, "state": "OPEN", "isDraft": False, "baseRefName": "main",
            "statusCheckRollup": [], "url": "u", "headRefOid": "abc123"}
    pull.update(overrides)
    return pull


class GhwPrMergeArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r", "main", "merge"),
                          ("o/r", "main", "merge", "5", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: ghw-pr-merge", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "main", "merge", "5")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_unknown_strategy_is_usage_error(self):
        # Rebase is deliberately unsupported; the strategy is a positional mode.
        for strategy in ("rebase", "Merge"):
            with self.subTest(strategy=strategy):
                result = _run("o/r", "main", strategy, "5")
                self.assertEqual(result.returncode, 2)
                self.assertIn("must be 'merge'", result.stderr)

    def test_squash_is_refused_with_a_hint_naming_the_ban(self):
        for strategy in ("squash", "--squash", "Squash"):
            with self.subTest(strategy=strategy):
                result = _run("o/r", "main", strategy, "5")
                self.assertEqual(result.returncode, 2)
                self.assertIn("squash is banned", result.stderr)

    def test_empty_base_branch_is_usage_error(self):
        result = _run("o/r", "  ", "merge", "5")
        self.assertEqual(result.returncode, 2)
        self.assertIn("must not be empty", result.stderr)

    def test_bad_pr_number_is_usage_error(self):
        result = _run("o/r", "main", "merge", "five")
        self.assertEqual(result.returncode, 2)
        self.assertIn("positive integer", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ghw-pr-merge <repo>", result.stdout)


class GhwPrMergeBehaviorTest(unittest.TestCase):
    def test_merge_gate_refusals_exit_4_and_never_merge(self):
        # Exit-code contract: a merge gate failing past parse time is a
        # refusal, exit 4 (never retry unchanged), distinct from a usage
        # error (2) and a gh/runtime failure (1, test_gh_failure_exits_1).
        cases = (
            ({"isDraft": True}, "draft"),
            ({"state": "CLOSED"}, "not OPEN"),
            ({"baseRefName": "develop"}, "actual base branch is 'develop'"),
            ({"statusCheckRollup": [{"name": "ci", "status": "COMPLETED",
                                     "conclusion": "FAILURE"}]},
             "checks are not green"),
        )
        for overrides, message in cases:
            with self.subTest(overrides=overrides):
                with mock.patch.object(_MODULE.gh, "pr_view",
                                       return_value=_pull(**overrides)), \
                        mock.patch.object(_MODULE.gh, "pr_merge") as merge, \
                        contextlib.redirect_stderr(io.StringIO()) as stderr:
                    with self.assertRaises(SystemExit) as caught:
                        _MODULE.main(["o/r", "main", "merge", "5"])
                self.assertEqual(caught.exception.code, 4)
                merge.assert_not_called()
                self.assertIn(message, stderr.getvalue())

    def test_gh_failure_exits_1(self):
        with mock.patch.object(_MODULE.gh, "pr_view",
                               side_effect=_MODULE.gh.GhError("boom")), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "main", "merge", "5"])
        self.assertEqual(caught.exception.code, 1)

    def test_classified_gh_failures_exit_with_their_code(self):
        for code in (3, 5, 6):
            with self.subTest(code=code):
                error = _MODULE.gh.GhError("boom", code)
                with mock.patch.object(_MODULE.gh, "pr_view", side_effect=error), \
                        contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        _MODULE.main(["o/r", "main", "merge", "5"])
                self.assertEqual(caught.exception.code, code)

    def test_clean_merge_pins_the_verified_head_and_emits_applied(self):
        # Pinning the merge to the viewed head oid closes the race between
        # the green-checks read and the merge itself.
        with mock.patch.object(_MODULE.gh, "pr_view", return_value=_pull()), \
                mock.patch.object(_MODULE.gh, "pr_merge") as merge, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(_MODULE.main(["o/r", "main", "merge", "5"]), 0)
        merge.assert_called_once_with("o/r", 5, "merge", "abc123")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["action"], "applied")
        self.assertEqual(payload["strategy"], "merge")


class GhwPrMergeArgumentContractTest(
    ghw_test_support.ArgumentContractTests, unittest.TestCase
):
    SCRIPT = _SCRIPT
    LONGEST = ("o/r", "main", "merge", "5")


if __name__ == "__main__":
    unittest.main()
