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

# A registry holding every canonical type label already correct, so a test's
# own additions are the only diff.
_CANONICAL_REGISTRY = [
    {"name": name, "color": attributes["color"],
     "description": attributes["description"]}
    for name, attributes in _MODULE.label_schema.TYPE_LABELS.items()
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


class GhwLabelSyncBehaviorTest(unittest.TestCase):
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

    def test_case_only_registry_difference_is_reported_not_recreated(self):
        # GitHub's label namespace is case-insensitive: planning a create for
        # 'bug' against a live 'Bug' would fail as already-existing forever.
        registry = [{"name": name.capitalize(), "color": attributes["color"],
                     "description": attributes["description"]}
                    for name, attributes in _MODULE.label_schema.TYPE_LABELS.items()]
        registry.append({"name": "area:core", "color": "bfdadc",
                         "description": "Core engine"})
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


if __name__ == "__main__":
    unittest.main()
