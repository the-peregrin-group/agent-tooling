"""Tests for the gitw-orient executable.

Argument tests run the script as a subprocess with arguments that fail
before the roster is ever read. Behavior tests load the script as a module,
mock the roster seam, and run against throwaway file-path git fixtures --
fully offline, never touching the real roster or any real repo.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ghw_test_support
import gitw_test_support
from lib.git.roster import Entry, RosterError

_SCRIPT = Path(__file__).resolve().parent / "gitw-orient"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class GitwOrientArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("one", "two")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: gitw-orient", result.stderr)

    def test_invalid_label_is_usage_error(self):
        for label in ("Upper", "has space", "has/slash", "-lead", ""):
            with self.subTest(label=label):
                result = _run(label)
                self.assertEqual(result.returncode, 2)
                self.assertIn("label", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("gitw-orient <repo>", result.stdout)


class _OrientFixtureTest(unittest.TestCase):
    """Shared fixture: a bare remote, a seed clone to advance it, and the
    registered clone the wrapper operates in."""

    def setUp(self):
        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp, ignore_errors=True)
        self.base = Path(temp).resolve()
        self.remote, self.seed, self.clone = (
            gitw_test_support.make_remote_and_clone(self.base)
        )
        self.entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            default_branch="main",
        )
        config = gitw_test_support.isolated_git_config()
        config.__enter__()
        self.addCleanup(config.__exit__, None, None, None)

    def orient(self, label: str = "proj", cwd: Path | None = None,
               entries: dict | None = None) -> dict:
        payload, code = self.orient_raw(label, cwd, entries)
        self.assertEqual(code, 0)
        return payload

    def orient_raw(self, label: str = "proj", cwd: Path | None = None,
                   entries: dict | None = None):
        entries = {"proj": self.entry} if entries is None else entries
        with mock.patch.object(_MODULE.roster, "load", return_value=entries), \
                gitw_test_support.chdir(cwd or self.clone), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            code = _MODULE.main([label])
        return json.loads(stdout.getvalue()), code

    def orient_expecting_exit(self, code: int, label: str = "proj",
                              cwd: Path | None = None,
                              entries: dict | None = None) -> str:
        entries = {"proj": self.entry} if entries is None else entries
        with mock.patch.object(_MODULE.roster, "load", return_value=entries), \
                gitw_test_support.chdir(cwd or self.clone), \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main([label])
        self.assertEqual(caught.exception.code, code)
        return stderr.getvalue()


class GitwOrientBehaviorTest(_OrientFixtureTest):
    def test_clean_current_checkout_orients_quietly(self):
        payload = self.orient()
        self.assertEqual(payload["repo"], "proj")
        self.assertEqual(payload["branch"], "main")
        self.assertEqual(payload["authoritative"], "origin/main")
        self.assertTrue(payload["fetched"])
        self.assertTrue(payload["clean"])
        self.assertTrue(payload["cwd_in_repo"])
        self.assertEqual((payload["ahead"], payload["behind"]), (0, 0))
        self.assertEqual(payload["upstream"], "origin/main")
        self.assertFalse(payload["detached"])
        self.assertEqual(len(payload["commit"]), 40)

    def test_orient_fetches_so_remote_advance_shows_as_behind(self):
        gitw_test_support.advance_remote(self.seed)
        payload = self.orient()
        self.assertEqual((payload["ahead"], payload["behind"]), (0, 1))

    def test_local_commit_shows_as_ahead(self):
        gitw_test_support.commit_on(
            self.clone, "local.txt", "local\n", "local work"
        )
        payload = self.orient()
        self.assertEqual((payload["ahead"], payload["behind"]), (1, 0))

    def test_dirty_state_is_tallied(self):
        (self.clone / "untracked.txt").write_text("u\n")
        (self.clone / "README.md").write_text("modified\n")
        payload = self.orient()
        self.assertFalse(payload["clean"])
        self.assertEqual(
            payload["dirty"], {"staged": 0, "unstaged": 1, "untracked": 1}
        )

    def test_detached_head_is_reported(self):
        gitw_test_support.git(self.clone, "switch", "--detach")
        payload = self.orient()
        self.assertIsNone(payload["branch"])
        self.assertTrue(payload["detached"])
        self.assertIsNotNone(payload["commit"])

    def test_machine_local_entry_skips_fetch_and_uses_local_default(self):
        local = self.base / "local"
        local.mkdir()
        gitw_test_support.git(local, "init", "--initial-branch=main", ".")
        gitw_test_support.commit_on(local, "a.txt", "a\n", "seed")
        gitw_test_support.git(local, "switch", "-c", "fix/topic")
        gitw_test_support.commit_on(local, "b.txt", "b\n", "topic work")
        entry = Entry(label="scratch", checkout=local)
        payload = self.orient(
            "scratch", cwd=local, entries={"scratch": entry}
        )
        self.assertFalse(payload["fetched"])
        self.assertIsNone(payload["remote"])
        self.assertEqual(payload["authoritative"], "main")
        self.assertEqual((payload["ahead"], payload["behind"]), (1, 0))

    def test_unborn_repository_orients_with_null_commit(self):
        fresh = self.base / "fresh"
        fresh.mkdir()
        gitw_test_support.git(fresh, "init", "--initial-branch=main", ".")
        entry = Entry(label="fresh", checkout=fresh)
        payload = self.orient("fresh", cwd=fresh, entries={"fresh": entry})
        self.assertEqual(payload["branch"], "main")
        self.assertIsNone(payload["commit"])
        self.assertFalse(payload["detached"])
        self.assertIsNone(payload["ahead"])
        self.assertTrue(payload["clean"])

    def test_mid_rebase_conflict_state_still_orients(self):
        gitw_test_support.commit_on(
            self.clone, "conflict.txt", "local\n", "local change"
        )
        gitw_test_support.commit_on(
            self.seed, "conflict.txt", "remote\n", "remote change"
        )
        gitw_test_support.git(self.seed, "push", "origin", "main")
        gitw_test_support.git(self.clone, "fetch", "origin")
        result = gitw_test_support.git(
            self.clone, "rebase", "origin/main", check=False
        )
        self.assertNotEqual(result.returncode, 0)  # conflicted, mid-rebase
        payload = self.orient()
        self.assertTrue(payload["detached"])
        self.assertFalse(payload["clean"])

    def test_operable_from_cwd_reports_the_primary_checkout(self):
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            operable_from=(elsewhere,),
        )
        payload = self.orient(cwd=elsewhere, entries={"proj": entry})
        self.assertFalse(payload["cwd_in_repo"])
        self.assertEqual(payload["worktree"], str(self.clone.resolve()))
        self.assertEqual(payload["branch"], "main")


class GitwOrientRefusalTest(_OrientFixtureTest):
    def test_unknown_label_is_not_found_and_names_known_labels(self):
        stderr = self.orient_expecting_exit(3, label="ghost")
        self.assertIn("'ghost'", stderr)
        self.assertIn("proj", stderr)

    def test_roster_error_exits_with_auth_code(self):
        with mock.patch.object(
            _MODULE.roster, "load", side_effect=RosterError("no roster")
        ), contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["proj"])
        self.assertEqual(caught.exception.code, 5)
        self.assertIn("no roster", stderr.getvalue())

    def test_cwd_outside_the_registered_checkout_is_refused(self):
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        stderr = self.orient_expecting_exit(4, cwd=elsewhere)
        self.assertIn("not inside the registered checkout", stderr)

    def test_second_clone_with_matching_url_is_refused(self):
        gitw_test_support.git(self.base, "clone", str(self.remote), "rogue")
        self.orient_expecting_exit(4, cwd=self.base / "rogue")

    def test_remote_url_mismatch_is_refused(self):
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url="ssh://forge.example.com/own/other.git",
            remote="origin",
        )
        stderr = self.orient_expecting_exit(4, entries={"proj": entry})
        self.assertIn("not the blessed one", stderr)

    def test_deleted_remote_repository_classifies_as_not_found(self):
        broken = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
        )
        shutil.rmtree(self.remote)
        self.orient_expecting_exit(3, entries={"proj": broken})


if __name__ == "__main__":
    unittest.main()
