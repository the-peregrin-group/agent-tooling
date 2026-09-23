"""Tests for the gitw-repo-register executable.

Argument tests run the script as a subprocess with arguments that fail
before anything is derived or read. Behavior tests load the script as a
module and point roster.DEFAULT_PATH at a throwaway file -- the real
roster is never read or written; fixture repos are file-path throwaways.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ghw_test_support
import gitw_test_support
from lib.git import roster

_SCRIPT = Path(__file__).resolve().parent / "gitw-repo-register"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class GitwRepoRegisterArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("proj",), ("proj", "/a", "origin", "apply", "x")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: gitw-repo-register", result.stderr)

    def test_invalid_label_is_usage_error(self):
        result = _run("Not-Valid", "/somewhere")
        self.assertEqual(result.returncode, 2)
        self.assertIn("label", result.stderr)

    def test_relative_checkout_is_usage_error(self):
        result = _run("proj", "relative/path")
        self.assertEqual(result.returncode, 2)
        self.assertIn("absolute", result.stderr)

    def test_unknown_positional_mode_is_usage_error(self):
        result = _run("proj", "/somewhere", "origin", "--force")
        self.assertEqual(result.returncode, 2)
        self.assertIn("'apply'", result.stderr)

    def test_nonexistent_checkout_path_is_a_clean_usage_error(self):
        # The likely user error in this ceremony: a typo'd path must not
        # surface as a subprocess traceback.
        result = _run("proj", "/nonexistent/gitw-register-test-path")
        self.assertEqual(result.returncode, 2)
        self.assertIn("/nonexistent/gitw-register-test-path", result.stderr)
        self.assertIn("does not exist", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("gitw-repo-register <label>", result.stdout)


class _RegisterFixtureTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp, ignore_errors=True)
        self.base = Path(temp).resolve()
        self.remote, self.seed, self.clone = (
            gitw_test_support.make_remote_and_clone(self.base)
        )
        self.roster_path = self.base / "config" / "repos.toml"
        patcher = mock.patch.object(
            roster, "DEFAULT_PATH", self.roster_path
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        config = gitw_test_support.isolated_git_config()
        config.__enter__()
        self.addCleanup(config.__exit__, None, None, None)

    def register(self, *arguments: str) -> dict:
        with contextlib.redirect_stdout(io.StringIO()) as stdout, \
                contextlib.redirect_stderr(io.StringIO()):
            code = _MODULE.main(list(arguments))
        self.assertEqual(code, 0)
        return json.loads(stdout.getvalue())

    def register_expecting_exit(self, code: int, *arguments: str) -> str:
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(list(arguments))
        self.assertEqual(caught.exception.code, code)
        return stderr.getvalue()


class GitwRepoRegisterPlanTest(_RegisterFixtureTest):
    def test_plan_derives_the_entry_and_writes_nothing(self):
        payload = self.register("proj", str(self.clone))
        self.assertEqual(payload["action"], "plan")
        self.assertFalse(payload["changed"])
        # The delta is a list of TOML lines, one per row, so the human in
        # the ask ceremony can ratify it at a glance.
        self.assertIsInstance(payload["delta"], list)
        self.assertIn("[proj]", payload["delta"])
        self.assertIn(f'checkout = "{self.clone}"', payload["delta"])
        self.assertIn(f'remote_url = "{self.remote}"', payload["delta"])
        self.assertIn('remote = "origin"', payload["delta"])
        self.assertIn('default_branch = "main"', payload["delta"])
        self.assertFalse(self.roster_path.exists())

    def test_default_branch_falls_back_to_main_without_remote_head(self):
        gitw_test_support.git(self.clone, "remote", "set-head", "origin", "-d")
        payload = self.register("proj", str(self.clone))
        self.assertIn('default_branch = "main"', payload["delta"])

    def test_default_branch_falls_back_to_master_when_that_is_the_trunk(self):
        remote = self.base / "master-remote.git"
        remote.mkdir()
        gitw_test_support.git(
            remote, "init", "--bare", "--initial-branch=master", "."
        )
        gitw_test_support.git(self.base, "clone", str(remote), "master-seed")
        seed = self.base / "master-seed"
        gitw_test_support.commit_on(seed, "a.txt", "a\n", "seed")
        gitw_test_support.git(seed, "push", "origin", "master")
        gitw_test_support.git(self.base, "clone", str(remote), "master-clone")
        clone = self.base / "master-clone"
        gitw_test_support.git(clone, "remote", "set-head", "origin", "-d")
        payload = self.register("legacy", str(clone))
        self.assertIn('default_branch = "master"', payload["delta"])

    def test_machine_local_repo_registers_path_only(self):
        local = self.base / "local"
        local.mkdir()
        gitw_test_support.git(local, "init", "--initial-branch=trunk", ".")
        gitw_test_support.commit_on(local, "a.txt", "a\n", "seed")
        payload = self.register("scratch", str(local))
        delta_text = "\n".join(payload["delta"])
        self.assertNotIn("remote_url", delta_text)
        self.assertIn('default_branch = "trunk"', payload["delta"])


class GitwRepoRegisterApplyTest(_RegisterFixtureTest):
    def test_apply_creates_the_roster_0600_and_loads_back(self):
        payload = self.register("proj", str(self.clone), "apply")
        self.assertEqual(payload["action"], "applied")
        self.assertTrue(payload["changed"])
        mode = stat.S_IMODE(self.roster_path.stat().st_mode)
        self.assertEqual(mode, 0o600)
        entries = roster.load(path_for_testing=self.roster_path)
        entry = entries["proj"]
        self.assertEqual(entry.checkout, self.clone)
        self.assertEqual(entry.remote, "origin")
        self.assertEqual(entry.remote_url, str(self.remote))
        self.assertEqual(entry.default_branch, "main")

    def test_apply_appends_preserving_existing_text_and_comments(self):
        self.roster_path.parent.mkdir(parents=True)
        self.roster_path.write_text(
            "# hand-written header\n"
            "[existing]\n"
            'checkout = "/repos/existing"  # keep me\n'
        )
        self.roster_path.chmod(0o600)
        self.register("proj", str(self.clone), "apply")
        text = self.roster_path.read_text()
        self.assertIn("# hand-written header", text)
        self.assertIn("# keep me", text)
        entries = roster.load(path_for_testing=self.roster_path)
        self.assertEqual(sorted(entries), ["existing", "proj"])

    def test_reregistering_identically_is_a_converged_no_op(self):
        self.register("proj", str(self.clone), "apply")
        before = self.roster_path.read_text()
        payload = self.register("proj", str(self.clone), "apply")
        self.assertEqual(payload["action"], "applied")
        self.assertFalse(payload["changed"])
        self.assertIsNone(payload["delta"])
        self.assertEqual(self.roster_path.read_text(), before)

    def test_reregistering_ignores_hand_added_operable_from(self):
        self.register("proj", str(self.clone), "apply")
        with self.roster_path.open("a") as handle:
            handle.write(f'operable_from = ["{self.base}/elsewhere"]\n')
        payload = self.register("proj", str(self.clone), "apply")
        self.assertFalse(payload["changed"])


class GitwRepoRegisterRefusalTest(_RegisterFixtureTest):
    def test_conflicting_label_registration_is_refused(self):
        self.register("proj", str(self.clone), "apply")
        rogue = self.base / "rogue"
        gitw_test_support.git(self.base, "clone", str(self.remote), "rogue")
        stderr = self.register_expecting_exit(4, "proj", str(rogue), "apply")
        self.assertIn("already registered with different data", stderr)

    def test_second_label_for_the_same_checkout_is_refused(self):
        self.register("proj", str(self.clone), "apply")
        stderr = self.register_expecting_exit(
            4, "alias", str(self.clone), "apply"
        )
        self.assertIn("one blessed checkout carries one label", stderr)

    def test_non_repo_path_is_refused(self):
        empty = self.base / "empty"
        empty.mkdir()
        stderr = self.register_expecting_exit(4, "proj", str(empty))
        self.assertIn("not inside a git working tree", stderr)

    def test_subdirectory_path_is_refused_naming_the_root(self):
        nested = self.clone / "nested"
        nested.mkdir()
        stderr = self.register_expecting_exit(4, "proj", str(nested))
        self.assertIn("primary checkout root", stderr)
        self.assertIn(str(self.clone), stderr)

    def test_linked_worktree_path_is_refused(self):
        worktree = self.base / "wt"
        gitw_test_support.git(
            self.clone, "worktree", "add", str(worktree), "-b", "fix/wt"
        )
        stderr = self.register_expecting_exit(4, "proj", str(worktree))
        self.assertIn("primary checkout root", stderr)

    def test_several_remotes_require_an_explicit_name(self):
        gitw_test_support.git(
            self.clone, "remote", "add", "mirror", str(self.remote)
        )
        stderr = self.register_expecting_exit(4, "proj", str(self.clone))
        self.assertIn("several remotes", stderr)
        payload = self.register("proj", str(self.clone), "origin")
        self.assertIn('remote = "origin"', payload["delta"])

    def test_unknown_remote_name_is_refused(self):
        stderr = self.register_expecting_exit(
            4, "proj", str(self.clone), "upstream"
        )
        self.assertIn("no remote named 'upstream'", stderr)

    def test_machine_local_on_a_prefix_shaped_branch_is_refused(self):
        # Silently pinning fix/topic as default_branch would poison
        # later trunk refusals; trunks are single-level in this model.
        local = self.base / "local"
        local.mkdir()
        gitw_test_support.git(local, "init", "--initial-branch=main", ".")
        gitw_test_support.commit_on(local, "a.txt", "a\n", "seed")
        gitw_test_support.git(local, "switch", "-c", "fix/topic")
        stderr = self.register_expecting_exit(4, "scratch", str(local))
        self.assertIn("prefix-shaped feature branch", stderr)
        self.assertIn("intended default branch", stderr)

    def test_machine_local_detached_head_is_refused(self):
        local = self.base / "local"
        local.mkdir()
        gitw_test_support.git(local, "init", "--initial-branch=main", ".")
        gitw_test_support.commit_on(local, "a.txt", "a\n", "seed")
        gitw_test_support.git(local, "switch", "--detach")
        stderr = self.register_expecting_exit(4, "scratch", str(local))
        self.assertIn("detached", stderr)

    def test_underivable_default_branch_gets_the_set_head_hint(self):
        remote = self.base / "trunk-remote.git"
        remote.mkdir()
        gitw_test_support.git(
            remote, "init", "--bare", "--initial-branch=trunk", "."
        )
        gitw_test_support.git(self.base, "clone", str(remote), "trunk-seed")
        seed = self.base / "trunk-seed"
        gitw_test_support.commit_on(seed, "a.txt", "a\n", "seed")
        gitw_test_support.git(seed, "push", "origin", "trunk")
        gitw_test_support.git(self.base, "clone", str(remote), "trunk-clone")
        clone = self.base / "trunk-clone"
        gitw_test_support.git(clone, "remote", "set-head", "origin", "-d")
        stderr = self.register_expecting_exit(4, "trunked", str(clone))
        self.assertIn("cannot derive", stderr)
        self.assertIn("set-head", stderr)

    def test_a_quote_in_the_checkout_path_is_refused(self):
        # Legal on APFS, unrepresentable in the roster's TOML subset.
        odd = self.base / 'we"ird'
        odd.mkdir()
        gitw_test_support.git(odd, "init", "--initial-branch=main", ".")
        gitw_test_support.commit_on(odd, "a.txt", "a\n", "seed")
        stderr = self.register_expecting_exit(4, "odd", str(odd))
        self.assertIn("cannot be represented", stderr)

    def test_malformed_existing_roster_exits_with_auth_code(self):
        self.roster_path.parent.mkdir(parents=True)
        self.roster_path.write_text("not = toml = at all\n")
        self.roster_path.chmod(0o600)
        stderr = self.register_expecting_exit(5, "proj", str(self.clone))
        self.assertIn("cannot parse", stderr)


if __name__ == "__main__":
    unittest.main()
