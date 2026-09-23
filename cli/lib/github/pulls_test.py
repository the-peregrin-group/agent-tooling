"""Unit tests for lib.pulls (PR-merge gate checks).

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

if __package__ in (None, ""):  # direct invocation: python3 lib/pulls_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.github import pulls


def _pull(**overrides) -> dict:
    """Fake the `gh pr view --json state,isDraft,baseRefName,statusCheckRollup`
    output shape that merge_refusals() consumes."""
    pull = {
        "state": "OPEN",
        "isDraft": False,
        "baseRefName": "main",
        "statusCheckRollup": [],
    }
    pull.update(overrides)
    return pull


def _check_run(name="build", status="COMPLETED", conclusion="SUCCESS") -> dict:
    """Fake one CheckRun entry of a statusCheckRollup list."""
    return {"name": name, "status": status, "conclusion": conclusion}


class FailingChecksTest(unittest.TestCase):
    def test_no_checks_configured_passes(self):
        self.assertEqual(pulls._failing_checks(None), [])
        self.assertEqual(pulls._failing_checks([]), [])

    def test_green_check_runs_pass(self):
        rollup = [
            _check_run(),
            _check_run(conclusion="NEUTRAL"),
            _check_run(conclusion="SKIPPED"),
        ]
        self.assertEqual(pulls._failing_checks(rollup), [])

    def test_failed_check_run_is_named(self):
        failing = pulls._failing_checks([_check_run(name="tests", conclusion="FAILURE")])
        self.assertEqual(failing, ["tests (FAILURE)"])

    def test_in_flight_check_run_blocks(self):
        failing = pulls._failing_checks(
            [_check_run(status="IN_PROGRESS", conclusion=None)]
        )
        self.assertEqual(failing, ["build (IN_PROGRESS)"])

    def test_status_context_success_passes(self):
        rollup = [{"context": "ci/lint", "state": "SUCCESS"}]
        self.assertEqual(pulls._failing_checks(rollup), [])

    def test_status_context_failure_is_named(self):
        failing = pulls._failing_checks([{"context": "ci/lint", "state": "FAILURE"}])
        self.assertEqual(failing, ["ci/lint (FAILURE)"])

    def test_status_context_pending_blocks(self):
        failing = pulls._failing_checks([{"context": "ci/lint", "state": "PENDING"}])
        self.assertEqual(failing, ["ci/lint (PENDING)"])


class MergeRefusalsTest(unittest.TestCase):
    def test_clean_open_pull_has_no_refusals(self):
        self.assertEqual(pulls.merge_refusals(_pull(), "main"), [])

    def test_merged_pull_is_refused(self):
        refusals = pulls.merge_refusals(_pull(state="MERGED"), "main")
        self.assertEqual(len(refusals), 1)
        self.assertIn("MERGED", refusals[0])

    def test_base_mismatch_names_both_branches(self):
        refusals = pulls.merge_refusals(_pull(baseRefName="develop"), "main")
        self.assertEqual(len(refusals), 1)
        self.assertIn("'develop'", refusals[0])
        self.assertIn("'main'", refusals[0])

    def test_draft_is_refused(self):
        refusals = pulls.merge_refusals(_pull(isDraft=True), "main")
        self.assertEqual(refusals, ["PR is a draft"])

    def test_red_checks_are_refused_without_an_override_path(self):
        refusals = pulls.merge_refusals(
            _pull(statusCheckRollup=[_check_run(conclusion="FAILURE")]), "main"
        )
        self.assertEqual(len(refusals), 1)
        self.assertIn("no override path", refusals[0].lower())

    def test_refusals_accumulate(self):
        refusals = pulls.merge_refusals(
            _pull(state="CLOSED", isDraft=True, baseRefName="develop"), "main"
        )
        self.assertEqual(len(refusals), 3)


if __name__ == "__main__":
    unittest.main()
