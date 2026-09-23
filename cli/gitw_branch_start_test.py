"""Tests for the gitw-branch-start executable.

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
from lib.git.roster import Entry

_SCRIPT = Path(__file__).resolve().parent / "gitw-branch-start"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class GitwBranchStartArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("proj",), ("proj", "fix/"),
                          ("proj", "fix/", "x", "resume", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: gitw-branch-start", result.stderr)

    def test_unknown_positional_mode_is_usage_error(self):
        result = _run("proj", "fix/", "x", "--force")
        self.assertEqual(result.returncode, 2)
        self.assertIn("'resume'", result.stderr)

    def test_invalid_label_is_usage_error(self):
        result = _run("Not-Valid", "fix/", "x")
        self.assertEqual(result.returncode, 2)
        self.assertIn("label", result.stderr)

    def test_invalid_prefix_is_usage_error(self):
        for prefix in ("fix", "Fix/", "a/b/", "/", "-x/", "fix_a/"):
            with self.subTest(prefix=prefix):
                result = _run("proj", prefix, "x")
                self.assertEqual(result.returncode, 2)
                self.assertIn("prefix", result.stderr)

    def test_invalid_name_is_usage_error(self):
        for name in ("", "a b", "a/b", ".lead", "-lead", "a..b", "x.lock"):
            with self.subTest(name=name):
                result = _run("proj", "fix/", name)
                self.assertEqual(result.returncode, 2)
                self.assertIn("branch name", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("gitw-branch-start <repo>", result.stdout)


class _BranchStartFixtureTest(unittest.TestCase):
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

    def start(self, *arguments: str, cwd: Path | None = None,
              entries: dict | None = None) -> dict:
        entries = {"proj": self.entry} if entries is None else entries
        with mock.patch.object(_MODULE.roster, "load", return_value=entries), \
                gitw_test_support.chdir(cwd or self.clone), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            code = _MODULE.main(list(arguments))
        self.assertEqual(code, 0)
        return json.loads(stdout.getvalue())

    def start_expecting_exit(self, code: int, *arguments: str,
                             cwd: Path | None = None,
                             entries: dict | None = None) -> str:
        entries = {"proj": self.entry} if entries is None else entries
        with mock.patch.object(_MODULE.roster, "load", return_value=entries), \
                gitw_test_support.chdir(cwd or self.clone), \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(list(arguments))
        self.assertEqual(caught.exception.code, code)
        return stderr.getvalue()

    def push_remote_branch(self, branch: str) -> None:
        """Create `branch` on the remote (with one commit) via the seed
        clone, leaving the wrapper's clone unaware until it fetches."""
        gitw_test_support.git(self.seed, "switch", "-c", branch)
        gitw_test_support.commit_on(
            self.seed, "remote-work.txt", "w\n", f"work on {branch}"
        )
        gitw_test_support.git(self.seed, "push", "-u", "origin", branch)
        gitw_test_support.git(self.seed, "switch", "main")


class GitwBranchStartCreateTest(_BranchStartFixtureTest):
    def test_create_branches_from_fetched_default_and_switches(self):
        gitw_test_support.advance_remote(self.seed)  # clone is now stale
        payload = self.start("proj", "fix/", "topic")
        self.assertEqual(payload["action"], "applied")
        self.assertEqual(payload["mode"], "create")
        self.assertEqual(payload["branch"], "fix/topic")
        self.assertEqual(payload["start_point"], "origin/main")
        current = gitw_test_support.git(
            self.clone, "branch", "--show-current"
        ).stdout.strip()
        self.assertEqual(current, "fix/topic")
        # The freshness precondition: the new branch starts at the remote
        # tip pushed above, not at the clone's stale local main.
        remote_tip = gitw_test_support.git(
            self.seed, "rev-parse", "main"
        ).stdout.strip()
        self.assertEqual(payload["commit"], remote_tip)

    def test_create_sets_no_upstream(self):
        self.start("proj", "fix/", "topic")
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "fix/topic@{upstream}"],
            cwd=str(self.clone), capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_existing_local_branch_is_refused(self):
        gitw_test_support.git(self.clone, "branch", "fix/topic")
        stderr = self.start_expecting_exit(4, "proj", "fix/", "topic")
        self.assertIn("already exists locally", stderr)

    def test_remote_branch_unknown_to_stale_clone_is_refused(self):
        # The clone has never fetched fix/topic; the wrapper's own fetch
        # is what surfaces the collision.
        self.push_remote_branch("fix/topic")
        stderr = self.start_expecting_exit(4, "proj", "fix/", "topic")
        self.assertIn("already exists on origin", stderr)

    def test_dirty_worktree_is_refused(self):
        (self.clone / "README.md").write_text("modified\n")
        stderr = self.start_expecting_exit(4, "proj", "fix/", "topic")
        self.assertIn("commit or discard explicitly", stderr)

    def test_untracked_files_also_count_as_dirty(self):
        (self.clone / "droppings.txt").write_text("d\n")
        self.start_expecting_exit(4, "proj", "fix/", "topic")

    def test_file_written_during_the_fetch_is_refused_before_switch(self):
        # The dirty check runs before the fetch; the re-check at the
        # switch choke point is what closes the fetch-window race.
        def racing_fetch(remote, cwd):
            (self.clone / "raced.txt").write_text("r\n")
        with mock.patch.object(_MODULE.run, "fetch", side_effect=racing_fetch):
            stderr = self.start_expecting_exit(4, "proj", "fix/", "topic")
        self.assertIn("commit or discard explicitly", stderr)

    def test_operable_from_cwd_is_refused_for_branch_start(self):
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            operable_from=(elsewhere,),
        )
        stderr = self.start_expecting_exit(
            4, "proj", "fix/", "topic", cwd=elsewhere,
            entries={"proj": entry},
        )
        self.assertIn("worktree at cwd", stderr)

    def test_machine_local_creates_from_local_default(self):
        local = self.base / "local"
        local.mkdir()
        gitw_test_support.git(local, "init", "--initial-branch=main", ".")
        gitw_test_support.commit_on(local, "a.txt", "a\n", "seed")
        entry = Entry(label="scratch", checkout=local)
        payload = self.start(
            "scratch", "fix/", "topic", cwd=local,
            entries={"scratch": entry},
        )
        self.assertEqual(payload["start_point"], "main")
        current = gitw_test_support.git(
            local, "branch", "--show-current"
        ).stdout.strip()
        self.assertEqual(current, "fix/topic")

    def test_missing_authoritative_default_is_not_found(self):
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            default_branch="trunk",
        )
        stderr = self.start_expecting_exit(
            3, "proj", "fix/", "topic", entries={"proj": entry}
        )
        self.assertIn("origin/trunk", stderr)

    def test_create_in_linked_worktree_switches_that_worktree_only(self):
        worktree = self.base / "wt"
        gitw_test_support.git(
            self.clone, "worktree", "add", str(worktree), "-b", "worktree-x"
        )
        payload = self.start("proj", "fix/", "topic", cwd=worktree)
        self.assertEqual(payload["worktree"], str(worktree.resolve()))
        self.assertEqual(
            gitw_test_support.git(
                worktree, "branch", "--show-current"
            ).stdout.strip(),
            "fix/topic",
        )
        self.assertEqual(
            gitw_test_support.git(
                self.clone, "branch", "--show-current"
            ).stdout.strip(),
            "main",
        )


class GitwBranchStartResumeTest(_BranchStartFixtureTest):
    def test_resume_local_branch_switches_and_reports(self):
        gitw_test_support.git(self.clone, "switch", "-c", "fix/topic")
        gitw_test_support.commit_on(self.clone, "w.txt", "w\n", "work")
        gitw_test_support.git(self.clone, "push", "-u", "origin", "fix/topic")
        gitw_test_support.git(self.clone, "switch", "main")
        gitw_test_support.advance_remote(self.seed)
        payload = self.start("proj", "fix/", "topic", "resume")
        self.assertEqual(payload["mode"], "resume")
        self.assertEqual(payload["branch"], "fix/topic")
        self.assertEqual(payload["upstream"], "origin/fix/topic")
        self.assertEqual(
            (payload["upstream_ahead"], payload["upstream_behind"]), (0, 0)
        )
        # One commit of branch work ahead of trunk; trunk advanced once
        # since the branch was cut.
        self.assertEqual((payload["ahead"], payload["behind"]), (1, 1))

    def test_resume_remote_only_branch_creates_local_tracking_branch(self):
        self.push_remote_branch("fix/topic")
        payload = self.start("proj", "fix/", "topic", "resume")
        self.assertEqual(payload["upstream"], "origin/fix/topic")
        self.assertEqual(
            gitw_test_support.git(
                self.clone, "branch", "--show-current"
            ).stdout.strip(),
            "fix/topic",
        )

    def test_resume_missing_branch_is_not_found(self):
        stderr = self.start_expecting_exit(3, "proj", "fix/", "ghost", "resume")
        self.assertIn("nothing to resume", stderr)

    def test_resume_branch_held_by_another_worktree_is_refused(self):
        gitw_test_support.git(
            self.clone, "worktree", "add", str(self.base / "wt"),
            "-b", "fix/topic",
        )
        stderr = self.start_expecting_exit(4, "proj", "fix/", "topic", "resume")
        self.assertIn("another worktree", stderr)

    def test_resume_branch_already_current_in_this_worktree_reports(self):
        gitw_test_support.git(self.clone, "switch", "-c", "fix/topic")
        payload = self.start("proj", "fix/", "topic", "resume")
        self.assertEqual(payload["branch"], "fix/topic")
        self.assertIsNone(payload["upstream"])

    def test_resume_dirty_worktree_is_refused(self):
        gitw_test_support.git(self.clone, "branch", "fix/topic")
        (self.clone / "README.md").write_text("modified\n")
        self.start_expecting_exit(4, "proj", "fix/", "topic", "resume")


if __name__ == "__main__":
    unittest.main()
