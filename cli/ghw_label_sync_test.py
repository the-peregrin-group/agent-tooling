"""Tests for the ghw-label-sync executable.

Argument tests run the script as a subprocess with arguments that fail before
any network I/O. Behavior tests load the script as a module and mock the lib
gh/boards seams, the Tracker Schema fetch, and the priority regime, so no
`gh` calls are made. The schema is tracker_schema_test_support's fixture.

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

_SCRIPT = Path(__file__).resolve().parent / "ghw-label-sync"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


def _label(entry) -> dict:
    return {"name": entry["name"], "color": entry["color"],
            "description": entry["meaning"]}


# Every label the fixture declares outside its priorities, as GitHub would
# report it once synced, so a test's own changes are the only diff.
_CONVERGED = [
    *(_label(kind) for kind in fixture.DOCUMENT["issue_kinds"]),
    *(_label(label) for axis in fixture.DOCUMENT["issue_label_schema"]["axes"]
      for label in axis["labels"]),
    *(_label(label) for label in fixture.DOCUMENT["issue_label_schema"]["labels"]),
]
_PRIORITIES = [_label(p) for p in fixture.DOCUMENT["issue_priorities"]]
_STRAY = {"name": "wontfix", "color": "ffffff", "description": ""}
_ISSUE = {"number": 12, "title": "Old thing",
          "url": "https://github.com/o/r/issues/12"}


def _without(name: str) -> list:
    return [entry for entry in _CONVERGED if entry["name"] != name]


class GhwLabelSyncArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r",), ("o/r", "plan", "f.json")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: ghw-label-sync", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "plan")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_unknown_mode_is_usage_error_listing_the_modes(self):
        result = _run("o/r", "apply-all")
        self.assertEqual(result.returncode, 2)
        self.assertIn("plan|apply|apply-delete", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ghw-label-sync <repo>", result.stdout)


class _SyncSeam:
    """The mocked seams, shared by the behavior test classes. Holds no tests
    of its own."""

    @contextlib.contextmanager
    def _synced(self, registry, open_issues=(), total=None, calls=None,
                schema=None, regime="board-field"):
        """Mock the seams: `registry` is the repo's live label list, every
        deletion candidate is attached to `open_issues` (`total` sets a
        server-side count above what is listed), `schema` is what the
        TRACKER.md fetch gives (the fixture by default), and `regime` the
        priority regime.

        Passing `calls` records every write into that list in the order it
        happened, which is how the ordering guarantees get asserted.
        """
        attached = {"total": len(open_issues) if total is None else total,
                    "issues": list(open_issues)}

        def _record(verb):
            def _call(_repository, name, *_rest):
                if calls is not None:
                    calls.append(f"{verb} {name}")
            return _call

        with mock.patch.object(_MODULE.repo_schema, "fetch",
                               return_value=schema or fixture.loaded()), \
                mock.patch.object(_MODULE, "_priority_regime",
                                  return_value=regime), \
                mock.patch.object(_MODULE.boards, "fetch_labels",
                                  return_value=list(registry)), \
                mock.patch.object(_MODULE.boards, "fetch_open_issues_with_label",
                                  return_value=attached), \
                mock.patch.object(_MODULE.gh, "label_create",
                                  side_effect=_record("create")) as create, \
                mock.patch.object(_MODULE.gh, "label_edit",
                                  side_effect=_record("edit")) as edit, \
                mock.patch.object(_MODULE.gh, "label_delete",
                                  side_effect=_record("delete")) as delete, \
                contextlib.redirect_stderr(io.StringIO()) as stderr, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            yield {"create": create, "edit": edit, "delete": delete,
                   "stdout": stdout, "stderr": stderr}

    def _main(self, seam_arguments: dict, mode: str):
        """Run main under the seams; returns (exit code, seam)."""
        with self._synced(**seam_arguments) as seam:
            try:
                code = _MODULE.main(["o/r", mode])
            except SystemExit as stop:
                code = stop.code
        return code, seam


class GhwLabelSyncBehaviorTest(_SyncSeam, unittest.TestCase):

    def test_plan_mode_writes_nothing_and_reports_the_full_diff(self):
        with self._synced([]) as seam:
            self.assertEqual(_MODULE.main(["o/r", "plan"]), 0)
        seam["create"].assert_not_called()
        seam["edit"].assert_not_called()
        seam["delete"].assert_not_called()
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["action"], "plan")
        self.assertFalse(payload["changed"])
        self.assertEqual(payload["tracker_schema"], "o/r@main:TRACKER.md")
        self.assertEqual(
            sorted(label["name"] for label in payload["create"]),
            sorted(entry["name"] for entry in _CONVERGED),
        )

    def test_the_desired_set_is_exactly_what_the_schema_declares(self):
        # Kinds as Kind Labels, every axis's labels with their prefix, and
        # the labels on no axis; nothing ghw holds of its own.
        with self._synced([]) as seam:
            _MODULE.main(["o/r", "plan"])
        created = {label["name"]: label
                   for label in json.loads(seam["stdout"].getvalue())["create"]}
        self.assertEqual(
            set(created),
            {"task", "bug", "chore", "area:core", "area:docs", "site:a",
             "human", "perf"},
        )
        self.assertEqual(created["chore"],
                         {"name": "chore", "color": "fbca04",
                          "description": "Maintenance"})

    def test_apply_creates_missing_labels_and_fixes_drift(self):
        registry = [*_without("area:core"),
                    {"name": "area:core", "color": "000000",
                     "description": "stale"}]
        with self._synced(registry) as seam:
            self.assertEqual(_MODULE.main(["o/r", "apply"]), 0)
        seam["create"].assert_not_called()
        seam["edit"].assert_called_once_with(
            "o/r", "area:core", "bfdadc", "Core engine"
        )
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["action"], "applied")
        self.assertTrue(payload["changed"])

    def test_a_colour_alone_is_drift(self):
        registry = [*_without("human"),
                    {"name": "human", "color": "ededed",
                     "description": "Waiting on a person"}]
        with self._synced(registry) as seam:
            _MODULE.main(["o/r", "apply"])
        seam["edit"].assert_called_once_with(
            "o/r", "human", "d876e3", "Waiting on a person")

    def test_apply_computes_deletes_but_never_executes_them(self):
        with self._synced([*_CONVERGED, _STRAY]) as seam:
            self.assertEqual(_MODULE.main(["o/r", "apply"]), 0)
        seam["delete"].assert_not_called()
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual([entry["name"] for entry in payload["delete"]],
                         ["wontfix"])
        self.assertIsNone(payload["delete_refused"])
        self.assertFalse(payload["deletes_executed"])
        self.assertFalse(payload["changed"])

    def test_apply_delete_executes_the_deletes(self):
        with self._synced([*_CONVERGED, _STRAY]) as seam:
            self.assertEqual(_MODULE.main(["o/r", "apply-delete"]), 0)
        seam["delete"].assert_called_once_with("o/r", "wontfix")
        payload = json.loads(seam["stdout"].getvalue())
        self.assertTrue(payload["deletes_executed"])
        self.assertTrue(payload["changed"])

    def test_converged_repo_is_a_no_op(self):
        with self._synced(_CONVERGED) as seam:
            self.assertEqual(_MODULE.main(["o/r", "apply-delete"]), 0)
        for verb in ("create", "edit", "delete"):
            seam[verb].assert_not_called()
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["create"], [])
        self.assertEqual(payload["update"], [])
        self.assertEqual(payload["delete"], [])
        self.assertFalse(payload["changed"])
        self.assertEqual(seam["stderr"].getvalue(), "")

    def test_a_label_the_schema_no_longer_declares_is_a_deletion_candidate(self):
        # A repo on the old fixed kind labels whose schema declares others:
        # no special case, so plan lists the old one and warns where it is
        # still attached, apply keeps it, and apply-delete deletes it.
        improvement = {"name": "improvement", "color": "0075ca",
                       "description": "Enhancement"}
        code, seam = self._main({"registry": [*_CONVERGED, improvement],
                                 "open_issues": [_ISSUE]}, "plan")
        self.assertEqual(code, 0)
        self.assertIn("improvement", seam["stderr"].getvalue())
        code, seam = self._main({"registry": [*_CONVERGED, improvement]},
                                "apply-delete")
        seam["delete"].assert_called_once_with("o/r", "improvement")

    def test_plan_warns_about_labels_attached_to_open_issues(self):
        # plan is where a human decides whether to grant deletion, so the
        # warning has to land there, not only in the applying modes.
        with self._synced([*_CONVERGED, _STRAY], [_ISSUE]) as seam:
            _MODULE.main(["o/r", "plan"])
        warning = seam["stderr"].getvalue()
        self.assertIn("the following labels are attached to open issues:", warning)
        self.assertIn("wontfix", warning)
        self.assertIn("https://github.com/o/r/issues/12", warning)
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["delete"][0]["open_issues"][0]["number"], 12)

    def test_apply_warning_names_the_mode_that_would_execute_the_deletes(self):
        with self._synced([*_CONVERGED, _STRAY], [_ISSUE]) as seam:
            _MODULE.main(["o/r", "apply"])
        self.assertIn("apply-delete", seam["stderr"].getvalue())

    def test_no_warning_when_no_deletion_candidate_has_open_issues(self):
        with self._synced([*_CONVERGED, _STRAY], []) as seam:
            _MODULE.main(["o/r", "plan"])
        self.assertEqual(seam["stderr"].getvalue(), "")

    def test_creates_run_before_deletes(self):
        # A rename-shaped schema change must never leave the repo holding
        # neither the old label nor the new one.
        calls = []
        with self._synced([*_without("area:core"), _STRAY], calls=calls):
            _MODULE.main(["o/r", "apply-delete"])
        self.assertEqual(calls, ["create area:core", "delete wontfix"])

    def test_the_warning_prints_before_the_first_delete_runs(self):
        # In apply-delete the warning is the only record of what a delete
        # detached, so it must survive a failure mid-loop.
        printed_when_deleting = []
        with self._synced([*_CONVERGED, _STRAY], [_ISSUE]) as seam:
            seam["delete"].side_effect = lambda *_: printed_when_deleting.append(
                seam["stderr"].getvalue()
            )
            _MODULE.main(["o/r", "apply-delete"])
        self.assertIn("attached to open issues:", printed_when_deleting[0])

    def test_apply_delete_warning_is_prospective_not_past_tense(self):
        # It prints before the deletes run; claiming they happened would be a
        # lie if one then failed.
        with self._synced([*_CONVERGED, _STRAY], [_ISSUE]) as seam:
            _MODULE.main(["o/r", "apply-delete"])
        self.assertIn("about to be executed", seam["stderr"].getvalue())

    def test_a_truncated_issue_list_says_how_many_were_hidden(self):
        with self._synced([*_CONVERGED, _STRAY], [_ISSUE], total=250) as seam:
            _MODULE.main(["o/r", "plan"])
        self.assertIn("showing 1 of 250", seam["stderr"].getvalue())

    def test_a_failure_mid_apply_reports_what_already_landed(self):
        # A bare exit 1 with empty stdout would leave the repo's state unknown.
        registry = [entry for entry in _CONVERGED
                    if not entry["name"].startswith("area:")]
        with self._synced(registry) as seam:
            seam["create"].side_effect = [None, _MODULE.gh.GhError("HTTP 500")]
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "apply"])
        self.assertEqual(caught.exception.code, 1)
        message = seam["stderr"].getvalue()
        self.assertIn("HTTP 500", message)
        self.assertIn("created area:core", message)

    def test_a_classified_failure_mid_apply_keeps_its_exit_code(self):
        registry = [entry for entry in _CONVERGED
                    if not entry["name"].startswith("area:")]
        for code in (3, 5, 6):
            with self.subTest(code=code):
                with self._synced(registry) as seam:
                    seam["create"].side_effect = [
                        None, _MODULE.gh.GhError("boom", code)]
                    with self.assertRaises(SystemExit) as caught:
                        _MODULE.main(["o/r", "apply"])
                self.assertEqual(caught.exception.code, code)
                self.assertIn("created area:core", seam["stderr"].getvalue())

    def test_case_only_registry_difference_is_reported_not_recreated(self):
        # GitHub's label namespace is case-insensitive: planning a create for
        # 'bug' against a live 'Bug' would fail as already-existing forever.
        registry = [*_without("bug"),
                    {"name": "Bug", "color": "d73a4a",
                     "description": "Something is broken"}]
        with self._synced(registry) as seam:
            _MODULE.main(["o/r", "apply-delete"])
        seam["create"].assert_not_called()
        seam["delete"].assert_not_called()
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["case_mismatch"],
                         [{"live": "Bug", "desired": "bug"}])

    def test_a_case_only_twin_drifting_is_edited_under_its_live_name(self):
        registry = [*_without("human"),
                    {"name": "Human", "color": "ededed",
                     "description": "Waiting on a person"}]
        with self._synced(registry) as seam:
            _MODULE.main(["o/r", "apply-delete"])
        seam["edit"].assert_called_once_with(
            "o/r", "Human", "d876e3", "Waiting on a person")
        seam["delete"].assert_not_called()


class GhwLabelSyncPriorityTest(_SyncSeam, unittest.TestCase):
    """Priorities are labels only in the p-labels regime."""

    def test_the_regime_is_judged_from_the_linked_boards_as_orient_does(self):
        with mock.patch.object(_MODULE.boards, "fetch_boards",
                               return_value=[]) as fetch:
            self.assertEqual(_MODULE._priority_regime("o/r"), "p-labels")
        fetch.assert_called_once_with("o/r")

    def test_p_labels_regime_syncs_every_declared_priority(self):
        code, seam = self._main({"registry": _CONVERGED,
                                 "regime": "p-labels"}, "plan")
        created = [label["name"]
                   for label in json.loads(seam["stdout"].getvalue())["create"]]
        self.assertEqual(created, ["P0", "P1", "P4"])

    def test_board_field_regime_makes_priority_labels_deletion_candidates(self):
        code, seam = self._main({"registry": [*_CONVERGED, *_PRIORITIES]},
                                "apply-delete")
        self.assertEqual(sorted(call.args[1] for call in
                                seam["delete"].call_args_list),
                         ["P0", "P1", "P4"])

    def test_unknown_regime_neither_creates_nor_deletes_priority_labels(self):
        code, seam = self._main({"registry": [*_CONVERGED, _PRIORITIES[0]],
                                 "regime": "unknown"}, "apply-delete")
        self.assertEqual(code, 0)
        seam["create"].assert_not_called()
        seam["delete"].assert_not_called()
        self.assertIn("priority regime is unknown", seam["stderr"].getvalue())


class GhwLabelSyncDegradedSchemaTest(_SyncSeam, unittest.TestCase):
    """What sync does when TRACKER.md is missing or partly unusable."""

    def test_no_tracker_md_plans_nothing_and_refuses_apply_delete(self):
        for mode in ("plan", "apply"):
            with self.subTest(mode=mode):
                code, seam = self._main({"registry": [_STRAY],
                                         "schema": fixture.missing()}, mode)
                self.assertEqual(code, 0)
                payload = json.loads(seam["stdout"].getvalue())
                self.assertEqual((payload["create"], payload["delete"]), ([], []))
                self.assertIn("not found on the default branch",
                              payload["delete_refused"])
                self.assertIn("warning: o/r@main:TRACKER.md: not found",
                              seam["stderr"].getvalue())
        code, seam = self._main({"registry": [_STRAY],
                                 "schema": fixture.missing()}, "apply-delete")
        self.assertEqual(code, 4)
        self.assertIn("apply-delete refused", seam["stderr"].getvalue())
        for verb in ("create", "edit", "delete"):
            seam[verb].assert_not_called()

    def test_an_unusable_section_adds_nothing_and_blocks_deletion(self):
        document = fixture.document()
        document["issue_kinds"] = "task"
        schema = fixture.loaded(document)
        code, seam = self._main({"registry": [_STRAY], "schema": schema},
                                "apply")
        self.assertEqual(code, 0)
        created = [call.args[1] for call in seam["create"].call_args_list]
        self.assertNotIn("task", created)
        self.assertIn("area:core", created)
        self.assertIn("issue_kinds", seam["stderr"].getvalue())
        code, seam = self._main({"registry": [_STRAY], "schema": schema},
                                "apply-delete")
        self.assertEqual(code, 4)
        self.assertIn("issue_kinds cannot be used", seam["stderr"].getvalue())
        seam["create"].assert_not_called()
        seam["delete"].assert_not_called()

    def test_a_lost_entry_blocks_deletion_so_it_cannot_read_as_one_to_delete(self):
        document = fixture.document()
        document["issue_label_schema"]["labels"][1]["name"] = 7  # perf is lost
        schema = fixture.loaded(document)
        code, seam = self._main({"registry": _CONVERGED, "schema": schema},
                                "plan")
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["delete"], [])
        self.assertIn("issue_label_schema.labels is incomplete",
                      payload["delete_refused"])
        code, seam = self._main({"registry": _CONVERGED, "schema": schema},
                                "apply-delete")
        self.assertEqual(code, 4)

    def test_a_missing_colour_leaves_the_live_one_and_creates_with_a_neutral_one(self):
        document = fixture.document()
        del document["issue_label_schema"]["labels"][0]["color"]  # human
        schema = fixture.loaded(document)
        live = {"name": "human", "color": "123456",
                "description": "Waiting on a person"}
        code, seam = self._main({"registry": [*_without("human"), live],
                                 "schema": schema}, "apply")
        seam["edit"].assert_not_called()
        code, seam = self._main({"registry": _without("human"),
                                 "schema": schema}, "apply")
        seam["create"].assert_called_once_with(
            "o/r", "human", "ededed", "Waiting on a person")

    def test_a_meaning_too_long_for_github_is_shortened_and_converges(self):
        document = fixture.document()
        document["issue_kinds"][2]["meaning"] = " ".join(["word"] * 40)
        schema = fixture.loaded(document)
        code, seam = self._main({"registry": _without("chore"),
                                 "schema": schema}, "apply")
        description = seam["create"].call_args.args[3]
        self.assertLessEqual(len(description), 100)
        self.assertTrue(description.endswith("..."))
        live = {"name": "chore", "color": "fbca04", "description": description}
        code, seam = self._main({"registry": [*_without("chore"), live],
                                 "schema": schema}, "apply")
        seam["edit"].assert_not_called()


class GhwLabelSyncArgumentContractTest(
    ghw_test_support.ArgumentContractTests, unittest.TestCase
):
    SCRIPT = _SCRIPT
    LONGEST = ("o/r", "plan")


if __name__ == "__main__":
    unittest.main()
