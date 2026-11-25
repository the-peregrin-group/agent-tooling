"""Tests for the ghw-label-sync executable.

Argument tests run the script as a subprocess with arguments that fail before
any network I/O. Behavior tests load the script as a module and mock the lib
gh/boards seams; schema files are written into a scratch directory under the
real /tmp/claude, since the staging policy applies to them like any other file
a wrapper reads. Either way, no `gh` calls are made.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ghw_test_support

_SCRIPT = Path(__file__).resolve().parent / "ghw-label-sync"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)

_SCHEMA = {"area": [{"name": "core", "description": "Core engine"}]}

_HUMAN = {"name": _MODULE.label_schema.HUMAN_LABEL,
          "color": _MODULE.label_schema.HUMAN_LABEL_COLOR,
          "description": _MODULE.label_schema.HUMAN_LABEL_DESCRIPTION}

# A registry holding every canonical type label and the human label already
# correct, so a test's own additions are the only diff.
_CANONICAL_REGISTRY = [
    *({"name": name, "color": attributes["color"],
       "description": attributes["description"]}
      for name, attributes in _MODULE.label_schema.TYPE_LABELS.items()),
    _HUMAN,
]


class GhwLabelSyncArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r",), ("o/r", "plan"),
                          ("o/r", "plan", "f.json", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: ghw-label-sync", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "plan", "f.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_unknown_mode_is_usage_error_listing_the_modes(self):
        result = _run("o/r", "apply-all", "f.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("plan|apply|apply-delete", result.stderr)

    def test_schema_file_outside_staging_is_refused(self):
        # Same rule as body files: a wrapper that reads arbitrary paths is a
        # promptless exfiltration channel, and this file's content is
        # published to GitHub. The system temp directory stands in for
        # "anywhere else on disk" -- note it cannot be this test file, which
        # may itself sit under /tmp/claude in a scratch checkout.
        outside = Path(tempfile.mkdtemp()) / "labels.json"
        self.addCleanup(shutil.rmtree, outside.parent)
        outside.write_text(json.dumps(_SCHEMA))
        result = _run("o/r", "plan", str(outside))
        self.assertEqual(result.returncode, 2)
        self.assertIn("outside the staging directories", result.stderr)
        self.assertIn("schema file", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ghw-label-sync <repo>", result.stdout)


class _SyncSeam:
    """The scratch schema file and the mocked gh seam, shared by the behavior
    test classes. Holds no tests of its own."""

    def setUp(self):
        os.makedirs("/tmp/claude", exist_ok=True)
        self.scratch = Path(tempfile.mkdtemp(dir="/tmp/claude"))
        self.addCleanup(shutil.rmtree, self.scratch)

    def _schema_file(self, document=None) -> str:
        path = self.scratch / "labels.json"
        path.write_text(json.dumps(document if document is not None else _SCHEMA))
        return str(path)

    @contextlib.contextmanager
    def _synced(self, registry, open_issues=(), total=None, calls=None):
        """Mock the gh seam: `registry` is the repo's live label list, and
        every deletion candidate is attached to `open_issues` (`total` sets a
        server-side count above what is listed).

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

        with mock.patch.object(_MODULE.boards, "fetch_labels",
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


class GhwLabelSyncBehaviorTest(_SyncSeam, unittest.TestCase):

    def test_plan_mode_writes_nothing_and_reports_the_full_diff(self):
        with self._synced([]) as seam:
            self.assertEqual(
                _MODULE.main(["o/r", "plan", self._schema_file()]), 0
            )
        seam["create"].assert_not_called()
        seam["edit"].assert_not_called()
        seam["delete"].assert_not_called()
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["action"], "plan")
        self.assertFalse(payload["changed"])
        created = [label["name"] for label in payload["create"]]
        self.assertIn("area:core", created)
        self.assertIn("bug", created)  # canonical type labels are never declared

    def test_apply_creates_missing_labels_and_fixes_drift(self):
        registry = [*_CANONICAL_REGISTRY,
                    {"name": "area:core", "color": "000000",
                     "description": "stale"}]
        with self._synced(registry) as seam:
            self.assertEqual(
                _MODULE.main(["o/r", "apply", self._schema_file()]), 0
            )
        seam["create"].assert_not_called()
        seam["edit"].assert_called_once_with(
            "o/r", "area:core", "bfdadc", "Core engine"
        )
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["action"], "applied")
        self.assertTrue(payload["changed"])

    def test_apply_computes_deletes_but_never_executes_them(self):
        registry = [*_CANONICAL_REGISTRY,
                    {"name": "area:core", "color": "bfdadc",
                     "description": "Core engine"},
                    {"name": "wontfix", "color": "ffffff", "description": ""}]
        with self._synced(registry) as seam:
            self.assertEqual(
                _MODULE.main(["o/r", "apply", self._schema_file()]), 0
            )
        seam["delete"].assert_not_called()
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual([entry["name"] for entry in payload["delete"]],
                         ["wontfix"])
        self.assertFalse(payload["deletes_executed"])
        self.assertFalse(payload["changed"])

    def test_apply_delete_executes_the_deletes(self):
        registry = [*_CANONICAL_REGISTRY,
                    {"name": "area:core", "color": "bfdadc",
                     "description": "Core engine"},
                    {"name": "wontfix", "color": "ffffff", "description": ""}]
        with self._synced(registry) as seam:
            self.assertEqual(
                _MODULE.main(["o/r", "apply-delete", self._schema_file()]), 0
            )
        seam["delete"].assert_called_once_with("o/r", "wontfix")
        payload = json.loads(seam["stdout"].getvalue())
        self.assertTrue(payload["deletes_executed"])
        self.assertTrue(payload["changed"])

    def test_converged_repo_is_a_no_op(self):
        registry = [*_CANONICAL_REGISTRY,
                    {"name": "area:core", "color": "bfdadc",
                     "description": "Core engine"}]
        with self._synced(registry) as seam:
            self.assertEqual(
                _MODULE.main(["o/r", "apply-delete", self._schema_file()]), 0
            )
        for verb in ("create", "edit", "delete"):
            seam[verb].assert_not_called()
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["create"], [])
        self.assertEqual(payload["update"], [])
        self.assertEqual(payload["delete"], [])
        self.assertFalse(payload["changed"])

    def test_plan_warns_about_labels_attached_to_open_issues(self):
        # plan is where a human decides whether to grant deletion, so the
        # warning has to land there, not only in the applying modes.
        registry = [*_CANONICAL_REGISTRY,
                    {"name": "area:core", "color": "bfdadc",
                     "description": "Core engine"},
                    {"name": "wontfix", "color": "ffffff", "description": ""}]
        issues = [{"number": 12, "title": "Old thing",
                   "url": "https://github.com/o/r/issues/12"}]
        with self._synced(registry, issues) as seam:
            _MODULE.main(["o/r", "plan", self._schema_file()])
        warning = seam["stderr"].getvalue()
        self.assertIn("the following labels are attached to open issues:", warning)
        self.assertIn("wontfix", warning)
        self.assertIn("https://github.com/o/r/issues/12", warning)
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["delete"][0]["open_issues"][0]["number"], 12)

    def test_apply_warning_names_the_mode_that_would_execute_the_deletes(self):
        registry = [*_CANONICAL_REGISTRY,
                    {"name": "area:core", "color": "bfdadc",
                     "description": "Core engine"},
                    {"name": "wontfix", "color": "ffffff", "description": ""}]
        issues = [{"number": 12, "title": "Old thing",
                   "url": "https://github.com/o/r/issues/12"}]
        with self._synced(registry, issues) as seam:
            _MODULE.main(["o/r", "apply", self._schema_file()])
        self.assertIn("apply-delete", seam["stderr"].getvalue())

    def test_no_warning_when_no_deletion_candidate_has_open_issues(self):
        registry = [*_CANONICAL_REGISTRY,
                    {"name": "area:core", "color": "bfdadc",
                     "description": "Core engine"},
                    {"name": "wontfix", "color": "ffffff", "description": ""}]
        with self._synced(registry, []) as seam:
            _MODULE.main(["o/r", "plan", self._schema_file()])
        self.assertEqual(seam["stderr"].getvalue(), "")

    def test_malformed_schema_file_is_a_usage_error_naming_the_file(self):
        path = self.scratch / "labels.json"
        path.write_text('{"area": []}')
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "plan", str(path)])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("labels.json", stderr.getvalue())

    def test_creates_run_before_deletes(self):
        # A rename-shaped schema change must never leave the repo holding
        # neither the old label nor the new one.
        registry = [*_CANONICAL_REGISTRY,
                    {"name": "wontfix", "color": "ffffff", "description": ""}]
        calls = []
        with self._synced(registry, calls=calls):
            _MODULE.main(["o/r", "apply-delete", self._schema_file()])
        self.assertEqual(calls, ["create area:core", "delete wontfix"])

    def test_the_warning_prints_before_the_first_delete_runs(self):
        # In apply-delete the warning is the only record of what a delete
        # detached, so it must survive a failure mid-loop.
        registry = [*_CANONICAL_REGISTRY,
                    {"name": "area:core", "color": "bfdadc",
                     "description": "Core engine"},
                    {"name": "wontfix", "color": "ffffff", "description": ""}]
        issues = [{"number": 12, "title": "Old thing",
                   "url": "https://github.com/o/r/issues/12"}]
        printed_when_deleting = []
        with self._synced(registry, issues) as seam:
            seam["delete"].side_effect = lambda *_: printed_when_deleting.append(
                seam["stderr"].getvalue()
            )
            _MODULE.main(["o/r", "apply-delete", self._schema_file()])
        self.assertIn("attached to open issues:", printed_when_deleting[0])

    def test_apply_delete_warning_is_prospective_not_past_tense(self):
        # It prints before the deletes run; claiming they happened would be a
        # lie if one then failed.
        registry = [*_CANONICAL_REGISTRY,
                    {"name": "area:core", "color": "bfdadc",
                     "description": "Core engine"},
                    {"name": "wontfix", "color": "ffffff", "description": ""}]
        issues = [{"number": 12, "title": "t",
                   "url": "https://github.com/o/r/issues/12"}]
        with self._synced(registry, issues) as seam:
            _MODULE.main(["o/r", "apply-delete", self._schema_file()])
        self.assertIn("about to be executed", seam["stderr"].getvalue())

    def test_a_truncated_issue_list_says_how_many_were_hidden(self):
        registry = [*_CANONICAL_REGISTRY,
                    {"name": "area:core", "color": "bfdadc",
                     "description": "Core engine"},
                    {"name": "wontfix", "color": "ffffff", "description": ""}]
        issues = [{"number": 12, "title": "t",
                   "url": "https://github.com/o/r/issues/12"}]
        with self._synced(registry, issues, total=250) as seam:
            _MODULE.main(["o/r", "plan", self._schema_file()])
        self.assertIn("showing 1 of 250", seam["stderr"].getvalue())

    def test_a_failure_mid_apply_reports_what_already_landed(self):
        # A bare exit 1 with empty stdout would leave the repo's state unknown.
        registry = list(_CANONICAL_REGISTRY)
        schema = {"area": [{"name": "core", "description": "Core engine"},
                           {"name": "docs", "description": "Docs"}]}
        with self._synced(registry) as seam:
            seam["create"].side_effect = [None, _MODULE.gh.GhError("HTTP 500")]
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "apply", self._schema_file(schema)])
        self.assertEqual(caught.exception.code, 1)
        message = seam["stderr"].getvalue()
        self.assertIn("HTTP 500", message)
        self.assertIn("created area:core", message)

    def test_a_classified_failure_mid_apply_keeps_its_exit_code(self):
        registry = list(_CANONICAL_REGISTRY)
        schema = {"area": [{"name": "core", "description": "Core engine"},
                           {"name": "docs", "description": "Docs"}]}
        for code in (3, 5, 6):
            with self.subTest(code=code):
                with self._synced(registry) as seam:
                    seam["create"].side_effect = [
                        None, _MODULE.gh.GhError("boom", code)]
                    with self.assertRaises(SystemExit) as caught:
                        _MODULE.main(["o/r", "apply", self._schema_file(schema)])
                self.assertEqual(caught.exception.code, code)
                self.assertIn("created area:core", seam["stderr"].getvalue())

    def test_case_only_registry_difference_is_reported_not_recreated(self):
        # GitHub's label namespace is case-insensitive: planning a create for
        # 'bug' against a live 'Bug' would fail as already-existing forever.
        registry = [{"name": name.capitalize(), "color": attributes["color"],
                     "description": attributes["description"]}
                    for name, attributes in _MODULE.label_schema.TYPE_LABELS.items()]
        registry.append({"name": "area:core", "color": "bfdadc",
                         "description": "Core engine"})
        registry.append(_HUMAN)
        with self._synced(registry) as seam:
            _MODULE.main(["o/r", "plan", self._schema_file()])
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["create"], [])
        self.assertEqual(payload["delete"], [])
        self.assertIn({"live": "Bug", "desired": "bug"}, payload["case_mismatch"])

    def test_priority_labels_flag_keeps_p_labels_out_of_the_delete_set(self):
        # Without the flag a P0-P3 repo's own priority labels would be
        # deletion candidates.
        registry = [*_CANONICAL_REGISTRY,
                    {"name": "area:core", "color": "bfdadc",
                     "description": "Core engine"},
                    {"name": "P0", "color": "b60205",
                     "description": "Drop-everything and address now"}]
        with self._synced(registry) as seam:
            _MODULE.main(["o/r", "plan",
                          self._schema_file({**_SCHEMA, "priority_labels": True})])
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["delete"], [])
        self.assertIn("P0", payload["unchanged"])


class GhwLabelSyncHumanLabelTest(_SyncSeam, unittest.TestCase):
    """The shipped `human` label on the three kinds of existing repo: none,
    a hand-made one, and one the schema file declared under scope."""

    _AREA = {"name": "area:core", "color": "bfdadc",
             "description": "Core engine"}

    def _types_and_area(self):
        return [entry for entry in _CANONICAL_REGISTRY
                if entry["name"] != "human"] + [self._AREA]

    def test_a_repo_without_human_gets_it_created(self):
        with self._synced(self._types_and_area()) as seam:
            self.assertEqual(
                _MODULE.main(["o/r", "apply-delete", self._schema_file()]), 0
            )
        seam["create"].assert_called_once_with(
            "o/r", "human", _HUMAN["color"], _HUMAN["description"]
        )
        seam["delete"].assert_not_called()
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["create"], [_HUMAN])

    def test_a_hand_made_human_label_is_updated_never_deleted(self):
        hand_made = {"name": "human", "color": "ededed",
                     "description": "Needs a human"}
        with self._synced([*self._types_and_area(), hand_made]) as seam:
            self.assertEqual(
                _MODULE.main(["o/r", "apply-delete", self._schema_file()]), 0
            )
        seam["create"].assert_not_called()
        seam["delete"].assert_not_called()
        seam["edit"].assert_called_once_with(
            "o/r", "human", _HUMAN["color"], _HUMAN["description"]
        )
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["update"][0]["from"],
                         {"color": "ededed", "description": "Needs a human"})

    def test_human_declared_under_scope_converges_with_the_label_intact(self):
        # The file follows the old setup workaround and the live label was
        # created from it, in the scope family's color.
        declared = {"name": "human", "description": "Waiting on a person"}
        live = {"name": "human", "color": "c5def5",
                "description": "Waiting on a person"}
        schema = {**_SCHEMA, "scope": [declared]}
        with self._synced([*self._types_and_area(), live]) as seam:
            self.assertEqual(
                _MODULE.main(["o/r", "apply-delete", self._schema_file(schema)]),
                0,
            )
        seam["create"].assert_not_called()
        seam["delete"].assert_not_called()
        seam["edit"].assert_called_once_with(
            "o/r", "human", _HUMAN["color"], _HUMAN["description"]
        )
        self.assertIn("scope entry 'human' is ignored",
                      seam["stderr"].getvalue())

    def test_a_converged_scope_declaration_is_a_no_op_with_a_note(self):
        schema = {**_SCHEMA, "scope": [
            {"name": "human", "description": "Waiting on a person"}]}
        with self._synced([*self._types_and_area(), _HUMAN]) as seam:
            _MODULE.main(["o/r", "plan", self._schema_file(schema)])
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual((payload["create"], payload["update"],
                          payload["delete"]), ([], [], []))
        self.assertIn("Remove the entry", seam["stderr"].getvalue())

    def test_a_live_label_differing_only_in_case_is_kept_never_recreated(self):
        # GitHub's label namespace is case-insensitive: deleting a live
        # 'Human' and creating 'human' would detach it from every issue, and
        # a create alone would fail as already-existing on every run.
        for spelling in ("Human", "HUMAN"):
            for color, edits in (("ededed", 1), (_HUMAN["color"], 0)):
                live = {"name": spelling, "color": color,
                        "description": _HUMAN["description"]}
                with self.subTest(spelling=spelling, color=color), \
                        self._synced([*self._types_and_area(), live]) as seam:
                    self.assertEqual(_MODULE.main(
                        ["o/r", "apply-delete", self._schema_file()]), 0)
                    seam["create"].assert_not_called()
                    seam["delete"].assert_not_called()
                    self.assertEqual(seam["edit"].call_count, edits)
                    if edits:
                        seam["edit"].assert_called_once_with(
                            "o/r", spelling, _HUMAN["color"],
                            _HUMAN["description"])
                    payload = json.loads(seam["stdout"].getvalue())
                    self.assertEqual(payload["case_mismatch"],
                                     [{"live": spelling, "desired": "human"}])

    def test_a_scope_entry_and_a_live_label_both_capitalized_converge(self):
        schema = {**_SCHEMA, "scope": [
            {"name": "Human", "description": "Waiting on a person"}]}
        live = {"name": "Human", "color": "c5def5",
                "description": "Waiting on a person"}
        with self._synced([*self._types_and_area(), live]) as seam:
            self.assertEqual(_MODULE.main(
                ["o/r", "apply-delete", self._schema_file(schema)]), 0)
        seam["create"].assert_not_called()
        seam["delete"].assert_not_called()
        seam["edit"].assert_called_once_with(
            "o/r", "Human", _HUMAN["color"], _HUMAN["description"])
        self.assertIn("scope entry 'Human' is ignored", seam["stderr"].getvalue())

    def test_no_note_when_the_file_does_not_declare_human(self):
        with self._synced([*self._types_and_area(), _HUMAN]) as seam:
            _MODULE.main(["o/r", "plan", self._schema_file()])
        self.assertEqual(seam["stderr"].getvalue(), "")


class GhwLabelSyncArgumentContractTest(
    ghw_test_support.ArgumentContractTests, unittest.TestCase
):
    SCRIPT = _SCRIPT
    LONGEST = ("o/r", "plan", "f.json")


if __name__ == "__main__":
    unittest.main()
