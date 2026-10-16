"""Tests for the gitw-trunk-sync executable.

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
import os
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

_SCRIPT = Path(__file__).resolve().parent / "gitw-trunk-sync"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class GitwTrunkSyncArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("proj", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: gitw-trunk-sync <repo>", result.stderr)

    def test_invalid_label_is_usage_error(self):
        result = _run("Not-Valid")
        self.assertEqual(result.returncode, 2)
        self.assertIn("label", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("gitw-trunk-sync <repo>", result.stdout)


class GitwTrunkSyncTest(unittest.TestCase):
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

    def git(self, cwd: Path, *arguments: str) -> str:
        return gitw_test_support.git(cwd, *arguments).stdout.strip()

    def local_main(self) -> str:
        return self.git(self.clone, "rev-parse", "refs/heads/main")

    def remote_main(self) -> str:
        return self.git(self.seed, "rev-parse", "main")

    def sync(self, cwd: Path | None = None, entry: Entry | None = None) -> dict:
        entries = {"proj": entry or self.entry}
        with mock.patch.object(_MODULE.roster, "load", return_value=entries), \
                gitw_test_support.chdir(cwd or self.clone), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            code = _MODULE.main(["proj"])
        self.assertEqual(code, 0)
        return json.loads(stdout.getvalue())

    def sync_expecting_exit(self, code: int, cwd: Path | None = None,
                            entry: Entry | None = None,
                            label: str = "proj") -> str:
        entries = {"proj": entry or self.entry}
        with mock.patch.object(_MODULE.roster, "load", return_value=entries), \
                gitw_test_support.chdir(cwd or self.clone), \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main([label])
        self.assertEqual(caught.exception.code, code)
        return stderr.getvalue()

    def park_primary_elsewhere(self) -> None:
        """Leave the local main checked out nowhere."""
        self.git(self.clone, "switch", "-c", "parked")

    def test_fast_forwards_in_place_in_a_clean_primary_checkout(self):
        gitw_test_support.advance_remote(self.seed)
        payload = self.sync()
        self.assertEqual(payload["action"], "applied")
        self.assertEqual(payload["result"], "fast-forwarded")
        self.assertEqual(payload["to"], self.remote_main())
        self.assertEqual(self.local_main(), self.remote_main())
        # The working tree moved with the branch, and stayed on it.
        self.assertTrue((self.clone / "advance.txt").is_file())
        self.assertEqual(self.git(self.clone, "branch", "--show-current"), "main")

    def test_runs_from_a_linked_worktree_without_switching_it(self):
        gitw_test_support.advance_remote(self.seed)
        agent = self.base / "agent-wt"
        self.git(self.clone, "worktree", "add", "-b", "fix/topic", str(agent))
        payload = self.sync(cwd=agent)
        self.assertEqual(payload["result"], "fast-forwarded")
        self.assertEqual(self.local_main(), self.remote_main())
        self.assertEqual(
            self.git(agent, "branch", "--show-current"), "fix/topic"
        )
        self.assertTrue((self.clone / "advance.txt").is_file())

    def test_moves_the_ref_when_checked_out_nowhere(self):
        self.park_primary_elsewhere()
        gitw_test_support.advance_remote(self.seed)
        payload = self.sync()
        self.assertEqual(payload["result"], "ref-moved")
        self.assertEqual(self.local_main(), self.remote_main())
        # HEAD and the working tree stayed on the parked branch.
        self.assertEqual(
            self.git(self.clone, "branch", "--show-current"), "parked"
        )
        self.assertFalse((self.clone / "advance.txt").exists())

    def test_ref_move_ignores_dirt_in_the_primary_checkout(self):
        # The dirt guard applies only where main is checked out.
        self.park_primary_elsewhere()
        (self.clone / "README.md").write_text("dirty\n")
        gitw_test_support.advance_remote(self.seed)
        self.assertEqual(self.sync()["result"], "ref-moved")

    def test_already_at_the_fetched_tip_is_a_noop(self):
        payload = self.sync()
        self.assertEqual(payload["result"], "up-to-date")
        self.assertEqual(payload["from"], payload["to"])

    def test_noop_does_not_need_a_clean_tree(self):
        (self.clone / "README.md").write_text("dirty\n")
        self.assertEqual(self.sync()["result"], "up-to-date")

    def test_machine_local_is_a_noop_without_fetching(self):
        entry = Entry(label="proj", checkout=self.clone)
        with mock.patch.object(_MODULE.run, "fetch") as fetch:
            payload = self.sync(entry=entry)
        fetch.assert_not_called()
        self.assertEqual(payload["result"], "machine-local")

    def test_dirty_primary_checkout_is_refused(self):
        gitw_test_support.advance_remote(self.seed)
        before = self.local_main()
        (self.clone / "README.md").write_text("dirty\n")
        stderr = self.sync_expecting_exit(4)
        self.assertIn("dirty", stderr)
        self.assertEqual(self.local_main(), before)

    def test_untracked_file_counts_as_dirty(self):
        gitw_test_support.advance_remote(self.seed)
        (self.clone / "droppings.txt").write_text("d\n")
        self.sync_expecting_exit(4)

    def test_merge_in_progress_is_refused(self):
        gitw_test_support.advance_remote(self.seed)
        before = self.local_main()
        (self.clone / ".git" / "MERGE_HEAD").write_text(before + "\n")
        stderr = self.sync_expecting_exit(4)
        self.assertIn("in progress", stderr)
        self.assertEqual(self.local_main(), before)

    def stop_rebase_of_main(self, cwd: Path) -> None:
        """Stop an interactive rebase of main at an `edit`, over commits
        that are already on the remote (so main stays an ancestor of it)."""
        gitw_test_support.advance_remote(self.seed, "one.txt")
        gitw_test_support.advance_remote(self.seed, "two.txt")
        self.git(cwd, "pull", "--ff-only", "origin", "main")
        env = dict(os.environ, GIT_SEQUENCE_EDITOR="sed -i.bak 's/^pick/edit/'")
        proc = subprocess.run(
            ["git", "rebase", "-i", "HEAD~1"], cwd=cwd, env=env,
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.git(cwd, "branch", "--show-current"), "")

    def test_rebase_of_main_in_primary_checkout_is_refused(self):
        self.stop_rebase_of_main(self.clone)
        gitw_test_support.advance_remote(self.seed, "three.txt")
        before = self.local_main()
        stderr = self.sync_expecting_exit(4)
        self.assertIn("rebase", stderr)
        self.assertEqual(self.local_main(), before)

    def test_rebase_of_main_in_a_linked_worktree_is_refused(self):
        self.park_primary_elsewhere()
        holder = self.base / "rebasing-wt"
        self.git(self.clone, "worktree", "add", str(holder), "main")
        self.stop_rebase_of_main(holder)
        gitw_test_support.advance_remote(self.seed, "three.txt")
        before = self.local_main()
        stderr = self.sync_expecting_exit(4)
        self.assertIn("rebase", stderr)
        self.assertEqual(self.local_main(), before)

    def test_deleted_linked_worktree_directory_does_not_block_a_sync(self):
        gitw_test_support.advance_remote(self.seed)
        gone = self.base / "gone-wt"
        self.git(self.clone, "worktree", "add", "-b", "fix/gone", str(gone))
        shutil.rmtree(gone)
        payload = self.sync()
        self.assertEqual(payload["result"], "fast-forwarded")
        self.assertEqual(self.local_main(), self.remote_main())

    def test_cherry_pick_and_revert_in_progress_are_refused(self):
        for marker in ("CHERRY_PICK_HEAD", "REVERT_HEAD"):
            with self.subTest(marker=marker):
                gitw_test_support.advance_remote(self.seed, marker + ".txt")
                before = self.local_main()
                path = self.clone / ".git" / marker
                path.write_text(before + "\n")
                self.addCleanup(lambda p=path: p.exists() and p.unlink())
                self.sync_expecting_exit(4)
                self.assertEqual(self.local_main(), before)
                path.unlink()

    def test_update_ref_failure_with_unmoved_ref_is_a_git_error(self):
        gitw_test_support.advance_remote(self.seed)
        self.park_primary_elsewhere()
        lock = self.clone / ".git" / "refs" / "heads" / "main.lock"
        lock.write_text("")
        before = self.local_main()
        self.sync_expecting_exit(1)
        self.assertEqual(self.local_main(), before)

    def test_concurrent_move_during_update_is_refused(self):
        gitw_test_support.advance_remote(self.seed)
        self.park_primary_elsewhere()
        real = _MODULE.run.run
        moved = {}

        def racing(args, cwd, *rest, **kwargs):
            if args[:1] == ["update-ref"] and not moved:
                gitw_test_support.commit_on(self.clone, "race.txt", "r\n", "race")
                moved["sha"] = self.git(self.clone, "rev-parse", "HEAD")
                real(["update-ref", "refs/heads/main", moved["sha"]], cwd)
            return real(args, cwd, *rest, **kwargs)

        with mock.patch.object(_MODULE.run, "run", side_effect=racing):
            stderr = self.sync_expecting_exit(4)
        self.assertIn("moved while syncing", stderr)
        self.assertEqual(self.local_main(), moved["sha"])

    def test_diverged_local_default_is_refused(self):
        gitw_test_support.commit_on(self.clone, "mine.txt", "m\n", "local only")
        gitw_test_support.advance_remote(self.seed)
        before = self.local_main()
        stderr = self.sync_expecting_exit(4)
        self.assertIn("not an ancestor", stderr)
        self.assertEqual(self.local_main(), before)

    def test_local_ahead_of_the_tip_is_refused_never_moved_backwards(self):
        gitw_test_support.commit_on(self.clone, "mine.txt", "m\n", "local only")
        before = self.local_main()
        self.sync_expecting_exit(4)
        self.assertEqual(self.local_main(), before)

    def test_diverged_ref_checked_out_nowhere_is_refused(self):
        gitw_test_support.commit_on(self.clone, "mine.txt", "m\n", "local only")
        self.park_primary_elsewhere()
        gitw_test_support.advance_remote(self.seed)
        before = self.local_main()
        self.sync_expecting_exit(4)
        self.assertEqual(self.local_main(), before)

    def test_default_checked_out_in_a_linked_worktree_is_refused(self):
        self.park_primary_elsewhere()
        holder = self.base / "holder-wt"
        self.git(self.clone, "worktree", "add", str(holder), "main")
        gitw_test_support.advance_remote(self.seed)
        before = self.local_main()
        stderr = self.sync_expecting_exit(4)
        self.assertIn("linked worktree", stderr)
        self.assertEqual(self.local_main(), before)

    def test_remote_url_mismatch_is_refused(self):
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.base / "other.git"),
            remote="origin",
        )
        gitw_test_support.advance_remote(self.seed)
        before = self.local_main()
        stderr = self.sync_expecting_exit(4, entry=entry)
        self.assertIn("not the blessed one", stderr)
        self.assertEqual(self.local_main(), before)

    def test_cwd_outside_the_repo_is_refused(self):
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        self.sync_expecting_exit(4, cwd=elsewhere)

    def test_operable_from_cwd_is_refused(self):
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            operable_from=(elsewhere,),
        )
        stderr = self.sync_expecting_exit(4, cwd=elsewhere, entry=entry)
        self.assertIn("operable_from", stderr)

    def test_unknown_label_is_not_found(self):
        stderr = self.sync_expecting_exit(3, label="nope")
        self.assertIn("not in the roster", stderr)

    def test_missing_remote_default_branch_is_not_found(self):
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            default_branch="trunk",
        )
        self.sync_expecting_exit(3, entry=entry)

    def test_missing_local_default_branch_is_not_found(self):
        self.park_primary_elsewhere()
        self.git(self.clone, "branch", "-D", "main")
        self.sync_expecting_exit(3)
        self.assertNotEqual(
            self.git(self.clone, "branch", "--list", "main"), "main"
        )

    def test_fetch_failure_keeps_its_exit_code(self):
        error = _MODULE.run.GitError("network down", 6)
        with mock.patch.object(_MODULE.run, "fetch", side_effect=error):
            self.sync_expecting_exit(6)


class GitwTrunkSyncArgumentContractTest(
    ghw_test_support.ArgumentContractTests, unittest.TestCase
):
    SCRIPT = _SCRIPT
    LONGEST = ("proj",)


if __name__ == "__main__":
    unittest.main()
