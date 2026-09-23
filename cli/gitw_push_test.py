"""Tests for the gitw-push executable.

Argument tests run the script as a subprocess with arguments that fail
before the roster is ever read. Behavior tests load the script as a module,
mock the roster seam, and run against throwaway file-path git fixtures --
fully offline (the "remote" is a bare repository on disk), never touching
the real roster or any real repo.

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

_SCRIPT = Path(__file__).resolve().parent / "gitw-push"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class GitwPushArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("proj",), ("proj", "fix/", "name", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: gitw-push", result.stderr)

    def test_invalid_prefix_is_usage_error(self):
        result = _run("proj", "Fix/")
        self.assertEqual(result.returncode, 2)
        self.assertIn("prefix", result.stderr)

    def test_invalid_target_name_is_usage_error(self):
        # "nested/name" matters most: a slash in the name would let the
        # target escape the single-level prefix the allowlist row pins.
        for name in ("-current", "a..b", "current.lock", "nested/name"):
            with self.subTest(name=name):
                result = _run("proj", "fix/", name)
                self.assertEqual(result.returncode, 2)
                self.assertIn("target name", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("gitw-push <repo>", result.stdout)


class _PushFixtureTest(unittest.TestCase):
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
        gitw_test_support.commit_on(self.clone, "work.txt", "w\n", "work")
        config = gitw_test_support.isolated_git_config()
        config.__enter__()
        self.addCleanup(config.__exit__, None, None, None)

    def push(self, *arguments: str, cwd: Path | None = None,
             entries: dict | None = None) -> dict:
        entries = {"proj": self.entry} if entries is None else entries
        with mock.patch.object(_MODULE.roster, "load", return_value=entries), \
                gitw_test_support.chdir(cwd or self.clone), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            code = _MODULE.main(list(arguments))
        self.assertEqual(code, 0)
        return json.loads(stdout.getvalue())

    def push_expecting_exit(self, code: int, *arguments: str,
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

    def remote_tip(self, branch: str) -> str | None:
        result = gitw_test_support.git(
            self.remote, "rev-parse", "--verify", "--quiet",
            f"refs/heads/{branch}", check=False,
        )
        return result.stdout.strip() or None


class GitwPushBehaviorTest(_PushFixtureTest):
    def test_first_push_creates_the_remote_branch_and_sets_upstream(self):
        payload = self.push("proj", "fix/")
        self.assertEqual(payload["action"], "applied")
        self.assertEqual(payload["branch"], "fix/topic")
        self.assertEqual(payload["upstream"], "origin/fix/topic")
        self.assertEqual(self.remote_tip("fix/topic"), payload["commit"])
        self.assertEqual(
            repo.upstream_of(self.clone, "fix/topic"), "origin/fix/topic"
        )

    def test_non_fast_forward_own_branch_push_is_routine(self):
        self.push("proj", "fix/")
        gitw_test_support.git(
            self.clone, "commit", "--amend", "-m", "amended work"
        )
        payload = self.push("proj", "fix/")
        self.assertEqual(self.remote_tip("fix/topic"), payload["commit"])

    def test_lease_failure_when_another_actor_moved_the_branch(self):
        self.push("proj", "fix/")
        gitw_test_support.git(self.seed, "fetch", "origin")
        gitw_test_support.git(self.seed, "switch", "fix/topic")
        gitw_test_support.commit_on(
            self.seed, "their.txt", "t\n", "their work"
        )
        gitw_test_support.git(self.seed, "push", "origin", "fix/topic")
        gitw_test_support.commit_on(self.clone, "mine.txt", "m\n", "my work")
        stderr = self.push_expecting_exit(4, "proj", "fix/")
        self.assertIn("Fetch and reconcile", stderr)
        # The remote still holds the other actor's tip, untouched.
        self.assertEqual(
            self.remote_tip("fix/topic"),
            gitw_test_support.git(
                self.seed, "rev-parse", "fix/topic"
            ).stdout.strip(),
        )

    def test_force_if_includes_rejects_a_fetched_but_unintegrated_tip(self):
        # The lease alone is satisfied here (the remote-tracking ref is
        # fresh); --force-if-includes is what catches "you fetched their
        # tip but never integrated it".
        self.push("proj", "fix/")
        gitw_test_support.git(self.seed, "fetch", "origin")
        gitw_test_support.git(self.seed, "switch", "fix/topic")
        gitw_test_support.commit_on(
            self.seed, "their.txt", "t\n", "their work"
        )
        gitw_test_support.git(self.seed, "push", "origin", "fix/topic")
        gitw_test_support.git(self.clone, "fetch", "origin")
        gitw_test_support.commit_on(self.clone, "mine.txt", "m\n", "my work")
        stderr = self.push_expecting_exit(4, "proj", "fix/")
        self.assertIn("Fetch and reconcile", stderr)
        self.assertEqual(
            self.remote_tip("fix/topic"),
            gitw_test_support.git(
                self.seed, "rev-parse", "fix/topic"
            ).stdout.strip(),
        )

    def test_default_branch_push_is_refused_even_with_matching_prefix(self):
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            default_branch="fix/trunk",
        )
        gitw_test_support.git(self.clone, "switch", "-c", "fix/trunk")
        stderr = self.push_expecting_exit(
            4, "proj", "fix/", entries={"proj": entry}
        )
        self.assertIn("authoritative default branch", stderr)

    def test_prefix_mismatch_is_refused(self):
        gitw_test_support.git(self.clone, "switch", "main")
        stderr = self.push_expecting_exit(4, "proj", "fix/")
        self.assertIn("does not match the pinned prefix", stderr)

    def test_detached_head_is_refused(self):
        gitw_test_support.git(self.clone, "switch", "--detach")
        stderr = self.push_expecting_exit(4, "proj", "fix/")
        self.assertIn("detached HEAD", stderr)

    def test_machine_local_repo_is_refused(self):
        local = self.base / "local"
        local.mkdir()
        gitw_test_support.git(local, "init", "--initial-branch=main", ".")
        gitw_test_support.commit_on(local, "a.txt", "a\n", "seed")
        gitw_test_support.git(local, "switch", "-c", "fix/topic")
        entry = Entry(label="scratch", checkout=local)
        stderr = self.push_expecting_exit(
            4, "scratch", "fix/", cwd=local, entries={"scratch": entry}
        )
        self.assertIn("machine-local", stderr)

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
        stderr = self.push_expecting_exit(
            4, "proj", "fix/", cwd=elsewhere, entries={"proj": entry}
        )
        self.assertIn("worktree of", stderr)


class GitwPushNamedTargetTest(_PushFixtureTest):
    """The pointer-move form: `gitw-push <repo> <prefix> <name>` pushes the
    current branch's tip to `<prefix><name>` under an explicit lease."""

    def sibling_branch(self, name: str, filename: str) -> str:
        """Cut a fresh branch from main (a sibling of fix/topic, sharing no
        commits with it beyond main) and commit on it; returns its tip."""
        gitw_test_support.git(self.clone, "switch", "-c", name, "main")
        gitw_test_support.commit_on(
            self.clone, filename, "s\n", f"work on {name}"
        )
        return gitw_test_support.git(
            self.clone, "rev-parse", "HEAD"
        ).stdout.strip()

    def test_first_named_push_creates_target_and_sets_upstream_to_it(self):
        payload = self.push("proj", "fix/", "current")
        self.assertEqual(payload["action"], "applied")
        self.assertEqual(payload["branch"], "fix/topic")
        self.assertEqual(payload["target"], "fix/current")
        self.assertIsNone(payload["previous_target"])
        self.assertEqual(self.remote_tip("fix/current"), payload["commit"])
        # The dated branch itself never reaches the remote.
        self.assertIsNone(self.remote_tip("fix/topic"))
        # Upstream points at the target, so the branch reads as pushed.
        self.assertEqual(payload["upstream"], "origin/fix/current")
        self.assertEqual(
            repo.upstream_of(self.clone, "fix/topic"), "origin/fix/current"
        )

    def test_named_push_moves_the_pointer_from_a_sibling_branch(self):
        first = self.push("proj", "fix/", "current")
        tip = self.sibling_branch("fix/topic2", "second.txt")
        payload = self.push("proj", "fix/", "current")
        self.assertEqual(payload["branch"], "fix/topic2")
        self.assertEqual(payload["previous_target"], first["commit"])
        self.assertEqual(self.remote_tip("fix/current"), tip)
        # A genuine pointer move, not a fast-forward: the old tip is not an
        # ancestor of the new one, so only the explicit lease admitted it.
        result = gitw_test_support.git(
            self.clone, "merge-base", "--is-ancestor", first["commit"], tip,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_named_push_is_refused_when_target_moved_since_last_fetch(self):
        first = self.push("proj", "fix/", "current")
        # Another actor (or the human) advances the target on the remote.
        gitw_test_support.git(self.seed, "fetch", "origin")
        gitw_test_support.commit_on(
            self.seed, "their.txt", "t\n", "their work"
        )
        gitw_test_support.git(
            self.seed, "push", "--force", "origin",
            "HEAD:refs/heads/fix/current",
        )
        theirs = gitw_test_support.git(
            self.seed, "rev-parse", "HEAD"
        ).stdout.strip()
        self.assertNotEqual(theirs, first["commit"])
        # Our remote-tracking value is stale, so the lease must refuse.
        self.sibling_branch("fix/topic2", "second.txt")
        stderr = self.push_expecting_exit(4, "proj", "fix/", "current")
        self.assertIn("rejected by the lease", stderr)
        self.assertEqual(self.remote_tip("fix/current"), theirs)

    def test_named_push_is_refused_when_unfetched_target_already_exists(self):
        # Never fetched the target: the lease says "must not exist yet",
        # so a target that appeared on the remote in the meantime is kept.
        gitw_test_support.git(
            self.seed, "push", "origin", "main:refs/heads/fix/current"
        )
        theirs = self.remote_tip("fix/current")
        stderr = self.push_expecting_exit(4, "proj", "fix/", "current")
        self.assertIn("rejected by the lease", stderr)
        self.assertEqual(self.remote_tip("fix/current"), theirs)

    def test_named_push_after_a_fetch_moves_a_target_created_elsewhere(self):
        gitw_test_support.git(
            self.seed, "push", "origin", "main:refs/heads/fix/current"
        )
        theirs = self.remote_tip("fix/current")
        gitw_test_support.git(self.clone, "fetch", "origin")
        payload = self.push("proj", "fix/", "current")
        # The fetched value is what the lease was taken against.
        self.assertEqual(payload["previous_target"], theirs)
        self.assertEqual(self.remote_tip("fix/current"), payload["commit"])

    def test_named_push_after_remote_deletion_needs_a_pruning_fetch(self):
        # A target deleted on the remote (a human ticking "delete branch"
        # on merge) leaves a stale remote-tracking ref behind a plain
        # fetch; the lease then refuses and names deletion as a cause. The
        # wrappers' own fetch prunes, after which the move goes through as
        # a first push.
        self.push("proj", "fix/", "current")
        gitw_test_support.git(
            self.seed, "push", "origin", ":refs/heads/fix/current"
        )
        self.assertIsNone(self.remote_tip("fix/current"))
        self.sibling_branch("fix/topic2", "second.txt")
        gitw_test_support.git(self.clone, "fetch", "origin")
        stderr = self.push_expecting_exit(4, "proj", "fix/", "current")
        self.assertIn("moved or was deleted", stderr)
        _MODULE.run.fetch("origin", self.clone)
        payload = self.push("proj", "fix/", "current")
        self.assertIsNone(payload["previous_target"])
        self.assertEqual(self.remote_tip("fix/current"), payload["commit"])

    def test_named_target_equal_to_current_branch_is_the_bare_form(self):
        payload = self.push("proj", "fix/", "topic")
        self.assertNotIn("target", payload)
        self.assertEqual(self.remote_tip("fix/topic"), payload["commit"])
        self.assertEqual(payload["upstream"], "origin/fix/topic")

    def test_named_target_equal_to_default_branch_is_refused(self):
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            default_branch="fix/current",
        )
        stderr = self.push_expecting_exit(
            4, "proj", "fix/", "current", entries={"proj": entry}
        )
        self.assertIn("authoritative default branch", stderr)
        self.assertIsNone(self.remote_tip("fix/current"))

    def test_named_push_still_requires_the_prefix_on_the_current_branch(self):
        gitw_test_support.git(self.clone, "switch", "main")
        stderr = self.push_expecting_exit(4, "proj", "fix/", "current")
        self.assertIn("does not match the pinned prefix", stderr)


if __name__ == "__main__":
    unittest.main()
