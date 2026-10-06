"""Tests for the gitw-rebase executable.

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
from lib.git import repo
from lib.git.roster import Entry

_SCRIPT = Path(__file__).resolve().parent / "gitw-rebase"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class GitwRebaseArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("proj",), ("proj", "fix/", "continue", "x")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: gitw-rebase", result.stderr)

    def test_skip_is_deliberately_not_a_mode(self):
        result = _run("proj", "fix/", "skip")
        self.assertEqual(result.returncode, 2)
        self.assertIn("deliberately no 'skip'", result.stderr)

    def test_invalid_prefix_is_usage_error(self):
        result = _run("proj", "fix", "continue")
        self.assertEqual(result.returncode, 2)
        self.assertIn("prefix", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("gitw-rebase <repo>", result.stdout)


class _RebaseFixtureTest(unittest.TestCase):
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
        gitw_test_support.git(self.clone, "switch", "-c", "fix/topic")
        config = gitw_test_support.isolated_git_config()
        config.__enter__()
        self.addCleanup(config.__exit__, None, None, None)

    def rebase(self, *arguments: str, cwd: Path | None = None,
               entries: dict | None = None) -> dict:
        payload, code = self.rebase_raw(*arguments, cwd=cwd, entries=entries)
        self.assertEqual(code, 0)
        return payload

    def rebase_raw(self, *arguments: str, cwd: Path | None = None,
                   entries: dict | None = None):
        """Runs the verb; returns (stdout-JSON-or-None, exit code) whether
        main returned or exited (the conflict stop emits JSON *and* exits
        4, so both channels matter)."""
        entries = {"proj": self.entry} if entries is None else entries
        with mock.patch.object(_MODULE.roster, "load", return_value=entries), \
                gitw_test_support.chdir(cwd or self.clone), \
                contextlib.redirect_stdout(io.StringIO()) as stdout, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            try:
                code = _MODULE.main(list(arguments))
            except SystemExit as caught:
                code = caught.code
        self.last_stderr = stderr.getvalue()
        raw = stdout.getvalue().strip()
        return (json.loads(raw) if raw else None), code

    def make_conflict(self) -> None:
        """A branch commit and a remote main commit that collide on
        conflict.txt; the fixture branch has not fetched yet."""
        gitw_test_support.commit_on(
            self.clone, "conflict.txt", "branch side\n", "branch change"
        )
        gitw_test_support.commit_on(
            self.seed, "conflict.txt", "main side\n", "main change"
        )
        gitw_test_support.git(self.seed, "push", "origin", "main")


class GitwRebaseBareTest(_RebaseFixtureTest):
    def test_clean_rebase_lands_on_the_fetched_default(self):
        gitw_test_support.commit_on(self.clone, "work.txt", "w\n", "work")
        gitw_test_support.advance_remote(self.seed)
        payload = self.rebase("proj", "fix/")
        self.assertEqual(payload["action"], "applied")
        self.assertEqual(payload["mode"], "rebase")
        self.assertEqual(payload["onto"], "origin/main")
        self.assertEqual(payload["commits_atop"], 1)
        self.assertEqual(
            repo.ahead_behind(
                self.clone, "HEAD", "refs/remotes/origin/main"
            ),
            (1, 0),
        )

    def test_already_current_branch_rebases_as_a_no_op(self):
        gitw_test_support.commit_on(self.clone, "work.txt", "w\n", "work")
        payload = self.rebase("proj", "fix/")
        self.assertEqual(payload["commits_atop"], 1)

    def test_conflict_leaves_state_and_exits_4_with_the_listing(self):
        self.make_conflict()
        payload, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        self.assertEqual(payload["action"], "conflict")
        self.assertEqual(payload["conflicts"], ["conflict.txt"])
        self.assertEqual(payload["onto"], "origin/main")
        # The hint is the exact runnable command, not a placeholder.
        self.assertIn("gitw-rebase proj fix/ continue", payload["hint"])
        self.assertIn("gitw-rebase proj fix/ abort", payload["hint"])
        # The conflict state is the work product: still in progress.
        self.assertEqual(repo.rebase_head_branch(self.clone), "fix/topic")

    def test_prefix_mismatch_is_refused(self):
        gitw_test_support.git(self.clone, "switch", "main")
        _, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        self.assertIn("does not match the pinned prefix", self.last_stderr)

    def test_dirty_worktree_is_refused(self):
        (self.clone / "README.md").write_text("modified\n")
        _, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        self.assertIn("commit or discard explicitly", self.last_stderr)

    def test_bare_form_with_rebase_in_progress_is_refused(self):
        self.make_conflict()
        _, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        _, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        self.assertIn("already in progress", self.last_stderr)

    def test_default_branch_matching_the_prefix_is_still_refused(self):
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            default_branch="fix/trunk",
        )
        gitw_test_support.git(self.clone, "switch", "-c", "fix/trunk")
        _, code = self.rebase_raw(
            "proj", "fix/", entries={"proj": entry}
        )
        self.assertEqual(code, 4)
        self.assertIn("authoritative default branch", self.last_stderr)

    def test_machine_local_rebases_onto_the_local_default(self):
        local = self.base / "local"
        local.mkdir()
        gitw_test_support.git(local, "init", "--initial-branch=main", ".")
        gitw_test_support.commit_on(local, "a.txt", "a\n", "seed")
        gitw_test_support.git(local, "switch", "-c", "fix/topic")
        gitw_test_support.commit_on(local, "b.txt", "b\n", "branch work")
        gitw_test_support.git(local, "switch", "main")
        gitw_test_support.commit_on(local, "c.txt", "c\n", "main advance")
        gitw_test_support.git(local, "switch", "fix/topic")
        entry = Entry(label="scratch", checkout=local)
        payload = self.rebase(
            "scratch", "fix/", cwd=local, entries={"scratch": entry}
        )
        self.assertEqual(payload["onto"], "main")
        self.assertEqual(
            repo.ahead_behind(local, "HEAD", "refs/heads/main"), (1, 0)
        )


class GitwRebaseContinueTest(_RebaseFixtureTest):
    def test_continue_after_resolution_completes_the_rebase(self):
        self.make_conflict()
        _, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        (self.clone / "conflict.txt").write_text("resolved\n")
        payload = self.rebase("proj", "fix/", "continue")
        self.assertEqual(payload["mode"], "continue")
        self.assertIsNone(repo.rebase_head_branch(self.clone))
        # Linear on top of the fetched default: exactly one commit atop.
        self.assertEqual(
            repo.ahead_behind(
                self.clone, "HEAD", "refs/remotes/origin/main"
            ),
            (1, 0),
        )

    def test_continue_with_leftover_markers_is_refused(self):
        self.make_conflict()
        _, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        _, code = self.rebase_raw("proj", "fix/", "continue")
        self.assertEqual(code, 4)
        self.assertIn("conflict markers still present", self.last_stderr)
        self.assertIn("conflict.txt", self.last_stderr)

    def test_continue_with_a_lone_marker_string_in_content_proceeds(self):
        # Legitimate content containing one marker-shaped line must not
        # make the rebase permanently un-continuable: only the full
        # <<<<<<< / ======= / >>>>>>> triple counts as unresolved.
        self.make_conflict()
        _, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        (self.clone / "conflict.txt").write_text(
            "resolved\n<<<<<<< this is a heredoc marker in prose\n"
        )
        payload = self.rebase("proj", "fix/", "continue")
        self.assertEqual(payload["mode"], "continue")

    def test_continue_stages_only_the_resolutions(self):
        self.make_conflict()
        _, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        (self.clone / "conflict.txt").write_text("resolved\n")
        (self.clone / "stray.txt").write_text("dropped in meanwhile\n")
        self.rebase("proj", "fix/", "continue")
        # The stray file was not swept into the rebased commit.
        self.assertEqual(
            repo.status_counts(self.clone),
            {"staged": 0, "unstaged": 0, "untracked": 1},
        )

    def test_continue_refuses_a_local_only_conflicted_path(self):
        gitw_test_support.commit_on(
            self.clone, ".env", "branch side\n", "branch env"
        )
        gitw_test_support.commit_on(
            self.seed, ".env", "main side\n", "main env"
        )
        gitw_test_support.git(self.seed, "push", "origin", "main")
        _, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        (self.clone / ".env").write_text("resolved\n")
        _, code = self.rebase_raw("proj", "fix/", "continue")
        self.assertEqual(code, 4)
        self.assertIn("local-only", self.last_stderr)
        # The verb-specific remedy seam: rebase advises hand-resolution,
        # not commit's pathspec advice.
        self.assertIn("resolve the rebase by hand", self.last_stderr)

    def test_continue_with_mismatched_prefix_is_refused(self):
        self.make_conflict()
        _, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        _, code = self.rebase_raw("proj", "docs/", "continue")
        self.assertEqual(code, 4)
        self.assertIn("does not match the pinned prefix", self.last_stderr)

    def test_continue_without_a_rebase_is_refused(self):
        _, code = self.rebase_raw("proj", "fix/", "continue")
        self.assertEqual(code, 4)
        self.assertIn("no rebase is in progress", self.last_stderr)

    def test_conflict_cycle_repeats_per_conflicted_commit(self):
        gitw_test_support.commit_on(
            self.clone, "conflict.txt", "branch one\n", "branch change 1"
        )
        gitw_test_support.commit_on(
            self.clone, "conflict.txt", "branch two\n", "branch change 2"
        )
        gitw_test_support.commit_on(
            self.seed, "conflict.txt", "main side\n", "main change"
        )
        gitw_test_support.git(self.seed, "push", "origin", "main")
        payload, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        (self.clone / "conflict.txt").write_text("resolved one\n")
        payload, code = self.rebase_raw("proj", "fix/", "continue")
        self.assertEqual(code, 4)  # the second commit conflicts in turn
        self.assertEqual(payload["action"], "conflict")
        (self.clone / "conflict.txt").write_text("resolved two\n")
        payload = self.rebase("proj", "fix/", "continue")
        self.assertIsNone(repo.rebase_head_branch(self.clone))
        self.assertEqual(
            repo.ahead_behind(
                self.clone, "HEAD", "refs/remotes/origin/main"
            ),
            (2, 0),
        )


class GitwRebaseAbortTest(_RebaseFixtureTest):
    def test_abort_restores_the_pre_rebase_branch(self):
        self.make_conflict()
        before = repo.head_commit(self.clone)
        _, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        payload = self.rebase("proj", "fix/", "abort")
        self.assertEqual(payload["mode"], "abort")
        self.assertEqual(payload["commit"], before)
        self.assertIsNone(repo.rebase_head_branch(self.clone))
        self.assertEqual(repo.current_branch(self.clone), "fix/topic")

    def test_abort_without_a_rebase_is_refused(self):
        _, code = self.rebase_raw("proj", "fix/", "abort")
        self.assertEqual(code, 4)
        self.assertIn("no rebase is in progress", self.last_stderr)

    def test_abort_with_mismatched_prefix_is_refused(self):
        self.make_conflict()
        _, code = self.rebase_raw("proj", "fix/")
        self.assertEqual(code, 4)
        _, code = self.rebase_raw("proj", "docs/", "abort")
        self.assertEqual(code, 4)
        self.assertIn("does not match the pinned prefix", self.last_stderr)
        # Refused means untouched: the conflict state is still there.
        self.assertEqual(repo.rebase_head_branch(self.clone), "fix/topic")


class GitwRebaseBareSlashTest(_RebaseFixtureTest):
    def test_rebases_an_unprefixed_branch(self):
        gitw_test_support.git(self.clone, "branch", "-m", "foo-bar")
        gitw_test_support.commit_on(self.clone, "work.txt", "w\n", "work")
        gitw_test_support.advance_remote(self.seed)
        payload = self.rebase("proj", "/")
        self.assertEqual(payload["commits_atop"], 1)

    def test_refuses_the_default_branch(self):
        gitw_test_support.git(self.clone, "switch", "main")
        payload, code = self.rebase_raw("proj", "/")
        self.assertEqual(code, 4)
        self.assertIn("default branch", self.last_stderr)

    def test_conflict_hint_repeats_the_bare_slash(self):
        gitw_test_support.git(self.clone, "branch", "-m", "foo-bar")
        self.make_conflict()
        payload, code = self.rebase_raw("proj", "/")
        self.assertEqual(code, 4)
        self.assertIn("gitw-rebase proj / continue", payload["hint"])
        payload = self.rebase("proj", "/", "abort")
        self.assertEqual(payload["branch"], "foo-bar")


if __name__ == "__main__":
    unittest.main()
