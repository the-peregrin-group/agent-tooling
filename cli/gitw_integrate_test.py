"""Tests for the gitw-integrate executable.

Argument tests run the script as a subprocess with arguments that fail
before the roster is ever read. Behavior tests load the script as a module,
mock the roster seam, and run against throwaway file-path git fixtures --
fully offline (the "trunk" being pushed to is a bare repository on disk),
never touching the real roster or any real repo.

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

_SCRIPT = Path(__file__).resolve().parent / "gitw-integrate"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)
_MISSING_MESSAGE = "/tmp/claude/gitw-integrate-test-missing-message.txt"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class GitwIntegrateArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("proj",), ("proj", "main", "fix/"),
                          ("proj", "main", "fix/", "msg", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: gitw-integrate", result.stderr)

    def test_invalid_base_branch_is_usage_error(self):
        for base in ("", "-lead", "a..b", "x.lock", "end/", "a//b"):
            with self.subTest(base=base):
                result = _run("proj", base, "fix/", _MISSING_MESSAGE)
                self.assertEqual(result.returncode, 2)
                self.assertIn("base branch", result.stderr)

    def test_invalid_prefix_is_usage_error(self):
        result = _run("proj", "main", "Fix/", _MISSING_MESSAGE)
        self.assertEqual(result.returncode, 2)
        self.assertIn("prefix", result.stderr)

    def test_missing_message_file_is_refused_before_roster(self):
        result = _run("proj", "main", "fix/", _MISSING_MESSAGE)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing message file", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("gitw-integrate <repo>", result.stdout)


class _IntegrateFixtureTest(unittest.TestCase):
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
        gitw_test_support.commit_on(self.clone, "work.txt", "w\n", "work one")
        gitw_test_support.commit_on(self.clone, "work.txt", "ww\n", "work two")
        config = gitw_test_support.isolated_git_config()
        config.__enter__()
        self.addCleanup(config.__exit__, None, None, None)
        os.makedirs("/tmp/claude", exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w", dir="/tmp/claude", suffix=".txt", delete=False
        )
        handle.write("Integrate fix/topic\n\nbubble body\n")
        handle.close()
        self.message_path = handle.name
        self.addCleanup(os.unlink, self.message_path)

    def integrate(self, *arguments: str, cwd: Path | None = None,
                  entries: dict | None = None) -> dict:
        entries = {"proj": self.entry} if entries is None else entries
        with mock.patch.object(_MODULE.roster, "load", return_value=entries), \
                gitw_test_support.chdir(cwd or self.clone), \
                contextlib.redirect_stdout(io.StringIO()) as stdout, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            code = _MODULE.main(list(arguments))
        self.assertEqual(code, 0)
        self.last_stderr = stderr.getvalue()
        return json.loads(stdout.getvalue())

    def integrate_expecting_exit(self, code: int, *arguments: str,
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

    def base_moves_after_the_fetch(self):
        """Patch the wrapper's fetch so that, instead of fetching, it
        advances the remote's main from the seed clone: the descendant
        check then passes against the stale tracking ref, and the push
        meets a base that moved. Returns the patcher, for use as a context
        manager."""
        def advance_instead(remote, cwd):
            gitw_test_support.advance_remote(self.seed)
        return mock.patch.object(
            _MODULE.run, "fetch", side_effect=advance_instead
        )

    def remote_git(self, *arguments: str) -> str:
        return gitw_test_support.git(self.remote, *arguments).stdout.strip()


class GitwIntegrateBehaviorTest(_IntegrateFixtureTest):
    def test_integration_builds_the_bubble_and_fast_forwards_trunk(self):
        old_main = self.remote_git("rev-parse", "refs/heads/main")
        branch_tip = gitw_test_support.git(
            self.clone, "rev-parse", "fix/topic"
        ).stdout.strip()
        payload = self.integrate("proj", "main", "fix/", self.message_path)
        self.assertEqual(payload["action"], "applied")
        self.assertEqual(payload["base"], "main")
        self.assertEqual(payload["branch"], "fix/topic")
        self.assertEqual(payload["commits"], 2)
        self.assertEqual(payload["first_parent"], old_main)
        self.assertEqual(payload["second_parent"], branch_tip)
        merge = payload["merge_commit"]
        self.assertEqual(self.remote_git("rev-parse", "refs/heads/main"), merge)
        self.assertEqual(
            self.remote_git("rev-parse", f"{merge}^1"), old_main
        )
        self.assertEqual(
            self.remote_git("rev-parse", f"{merge}^2"), branch_tip
        )
        # The bubble carries the branch tip's tree exactly.
        self.assertEqual(
            self.remote_git("rev-parse", f"{merge}^{{tree}}"),
            self.remote_git("rev-parse", f"{branch_tip}^{{tree}}"),
        )
        self.assertIn(
            "Integrate fix/topic",
            self.remote_git("log", "-1", "--format=%B", merge),
        )

    def test_integration_never_touches_the_local_base_or_worktree(self):
        local_main = gitw_test_support.git(
            self.clone, "rev-parse", "refs/heads/main"
        ).stdout.strip()
        self.integrate("proj", "main", "fix/", self.message_path)
        # The local main branch stays where it was; the worktree stays on
        # the feature branch, clean.
        self.assertEqual(
            gitw_test_support.git(
                self.clone, "rev-parse", "refs/heads/main"
            ).stdout.strip(),
            local_main,
        )
        self.assertEqual(
            gitw_test_support.git(
                self.clone, "branch", "--show-current"
            ).stdout.strip(),
            "fix/topic",
        )

    def test_stale_rebase_is_refused_with_loop_again_guidance(self):
        gitw_test_support.advance_remote(self.seed)
        stderr = self.integrate_expecting_exit(
            4, "proj", "main", "fix/", self.message_path
        )
        self.assertIn("not a descendant", stderr)
        self.assertIn("loop again", stderr)
        # Nothing was pushed.
        self.assertEqual(
            self.remote_git("rev-parse", "refs/heads/main"),
            gitw_test_support.git(
                self.seed, "rev-parse", "main"
            ).stdout.strip(),
        )

    def test_base_moved_between_fetch_and_push_is_refused(self):
        # Freeze the wrapper's fetch, then move the remote: the descendant
        # check passes against the stale tracking ref and the push itself
        # is the non-fast-forward tripwire.
        with self.base_moves_after_the_fetch():
            stderr = self.integrate_expecting_exit(
                4, "proj", "main", "fix/", self.message_path
            )
        self.assertIn("moved during the attempt", stderr)
        self.assertEqual(
            self.remote_git("rev-parse", "refs/heads/main"),
            gitw_test_support.git(
                self.seed, "rev-parse", "main"
            ).stdout.strip(),
        )

    def test_deleted_base_is_not_silently_recreated(self):
        # A plain push of <sha>:refs/heads/develop would quietly CREATE
        # the branch. The wrapper's fetch prunes, so the stale tracking
        # ref is gone by the time the existence check runs and the
        # deletion surfaces as not-found (exit 3), never as a push.
        gitw_test_support.git(self.seed, "switch", "-c", "develop")
        gitw_test_support.git(self.seed, "push", "origin", "develop")
        gitw_test_support.git(self.clone, "fetch", "origin")
        gitw_test_support.git(
            self.seed, "push", "origin", "--delete", "develop"
        )
        stderr = self.integrate_expecting_exit(
            3, "proj", "develop", "fix/", self.message_path
        )
        self.assertIn("not found", stderr)
        result = gitw_test_support.git(
            self.remote, "rev-parse", "--verify", "--quiet",
            "refs/heads/develop", check=False,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_rewound_base_is_not_silently_fast_forwarded(self):
        # The bubble descends from the pre-rewind tip, so a plain push
        # would be a fast-forward that silently reinstates the rewound
        # history; the exact lease rejects instead.
        gitw_test_support.advance_remote(self.seed)
        gitw_test_support.git(self.clone, "fetch", "origin")
        rewound_to = gitw_test_support.git(
            self.clone, "rev-parse", "origin/main~1"
        ).stdout.strip()
        gitw_test_support.git(
            self.clone, "switch", "-C", "fix/topic", "origin/main"
        )
        gitw_test_support.commit_on(
            self.clone, "work.txt", "atop\n", "work atop the new tip"
        )
        gitw_test_support.git(
            self.seed, "push", "origin", f"+{rewound_to}:refs/heads/main"
        )
        with mock.patch.object(_MODULE.run, "fetch", side_effect=lambda *a: None):
            stderr = self.integrate_expecting_exit(
                4, "proj", "main", "fix/", self.message_path
            )
        self.assertIn("moved during the attempt", stderr)
        self.assertEqual(
            self.remote_git("rev-parse", "refs/heads/main"), rewound_to
        )

    def test_nothing_to_integrate_is_refused(self):
        gitw_test_support.git(self.clone, "switch", "-c", "fix/empty", "main")
        stderr = self.integrate_expecting_exit(
            4, "proj", "main", "fix/", self.message_path
        )
        self.assertIn("nothing to integrate", stderr)

    def test_non_default_base_branch_integrates_too(self):
        # The <base-branch> positional names the target; the roster
        # default is deliberately not consulted.
        gitw_test_support.git(self.seed, "switch", "-c", "develop")
        gitw_test_support.git(self.seed, "push", "origin", "develop")
        gitw_test_support.git(self.clone, "fetch", "origin")
        payload = self.integrate("proj", "develop", "fix/", self.message_path)
        self.assertEqual(payload["base"], "develop")
        self.assertEqual(
            self.remote_git("rev-parse", "refs/heads/develop"),
            payload["merge_commit"],
        )

    def test_missing_base_branch_on_the_remote_is_not_found(self):
        stderr = self.integrate_expecting_exit(
            3, "proj", "ghost", "fix/", self.message_path
        )
        self.assertIn("'ghost'", stderr)

    def test_prefix_mismatch_is_refused(self):
        stderr = self.integrate_expecting_exit(
            4, "proj", "main", "docs/", self.message_path
        )
        self.assertIn("does not match the pinned prefix", stderr)

    def test_dirty_worktree_is_refused(self):
        (self.clone / "work.txt").write_text("uncommitted\n")
        stderr = self.integrate_expecting_exit(
            4, "proj", "main", "fix/", self.message_path
        )
        self.assertIn("left behind", stderr)

    def test_branch_equal_to_base_is_refused(self):
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            default_branch="fix/trunk",
        )
        gitw_test_support.git(self.clone, "switch", "-c", "fix/trunk")
        stderr = self.integrate_expecting_exit(
            4, "proj", "fix/trunk", "fix/", self.message_path,
            entries={"proj": entry},
        )
        self.assertIn("nothing to integrate into", stderr)

    def test_machine_local_repo_is_refused(self):
        local = self.base / "local"
        local.mkdir()
        gitw_test_support.git(local, "init", "--initial-branch=main", ".")
        gitw_test_support.commit_on(local, "a.txt", "a\n", "seed")
        gitw_test_support.git(local, "switch", "-c", "fix/topic")
        entry = Entry(label="scratch", checkout=local)
        stderr = self.integrate_expecting_exit(
            4, "scratch", "main", "fix/", self.message_path,
            cwd=local, entries={"scratch": entry},
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
        stderr = self.integrate_expecting_exit(
            4, "proj", "main", "fix/", self.message_path,
            cwd=elsewhere, entries={"proj": entry},
        )
        self.assertIn("checked out at cwd", stderr)


class GitwIntegrateHookTest(_IntegrateFixtureTest):
    """A local pre-push hook on the bubble's push: its output reaches the
    caller whether it passes or refuses, and a refusal is exit 4, never
    the retryable 6."""

    def test_hook_refusal_is_exit_4_with_the_hook_output_verbatim(self):
        # The nested git writes its own trace2 session into the same
        # file, exercising the parser's (sid, child_id) keying.
        old_main = self.remote_git("rev-parse", "refs/heads/main")
        gitw_test_support.add_pre_push_hook(
            self.clone,
            "git rev-parse HEAD >/dev/null\n"
            'echo "pre-push: refused: work.txt line 1 names a secret"\n'
            'echo "pre-push: refused: work.txt line 3 names a path" >&2\n'
            "exit 1\n"
        )
        stderr = self.integrate_expecting_exit(
            4, "proj", "main", "fix/", self.message_path
        )
        self.assertIn(
            "pre-push: refused: work.txt line 1 names a secret\n", stderr
        )
        self.assertIn(
            "pre-push: refused: work.txt line 3 names a path\n", stderr
        )
        self.assertIn("refused by the local pre-push hook (exit 1)", stderr)
        self.assertNotIn("moved during the attempt", stderr)
        self.assertEqual(
            self.remote_git("rev-parse", "refs/heads/main"), old_main
        )

    def test_hook_refusal_keeps_the_hook_exit_code(self):
        old_main = self.remote_git("rev-parse", "refs/heads/main")
        gitw_test_support.add_pre_push_hook(
            self.clone, 'echo "nope"\nexit 7\n'
        )
        stderr = self.integrate_expecting_exit(
            4, "proj", "main", "fix/", self.message_path
        )
        self.assertIn("pre-push hook (exit 7)", stderr)
        self.assertEqual(
            self.remote_git("rev-parse", "refs/heads/main"), old_main
        )

    def test_hook_output_with_a_base_moved_marker_is_still_the_hook(self):
        # A refusing hook ends the push before git prints any ref status,
        # so marker text in the output is the hook's own: reporting it as
        # "base moved" would send the caller looping against the hook.
        gitw_test_support.add_pre_push_hook(
            self.clone,
            'echo "pre-push: refusing: this looks like a non-fast-forward '
            'push, fetch first" >&2\n'
            "exit 1\n"
        )
        stderr = self.integrate_expecting_exit(
            4, "proj", "main", "fix/", self.message_path
        )
        self.assertIn("refused by the local pre-push hook (exit 1)", stderr)
        self.assertNotIn("moved during the attempt", stderr)

    def test_passing_hook_output_reaches_the_caller(self):
        gitw_test_support.add_pre_push_hook(
            self.clone,
            'echo "pre-push: bubble tree clean"\n'
            'echo "pre-push: warning: large file" >&2\n'
            "exit 0\n"
        )
        payload = self.integrate("proj", "main", "fix/", self.message_path)
        self.assertEqual(
            self.remote_git("rev-parse", "refs/heads/main"),
            payload["merge_commit"],
        )
        self.assertIn("pre-push: bubble tree clean\n", self.last_stderr)
        self.assertIn("pre-push: warning: large file\n", self.last_stderr)

    def test_base_moved_with_a_passing_hook_is_still_base_moved(self):
        gitw_test_support.add_pre_push_hook(self.clone, "exit 0\n")
        with self.base_moves_after_the_fetch():
            stderr = self.integrate_expecting_exit(
                4, "proj", "main", "fix/", self.message_path
            )
        self.assertIn("moved during the attempt", stderr)

    def test_base_moved_with_a_refusing_hook_reports_the_hook(self):
        # git still runs the hook after the lease rejection, and the
        # hook's failure leaves no base-moved text: the hook is what is
        # reported, still exit 4. The moved base surfaces on the next try.
        gitw_test_support.add_pre_push_hook(
            self.clone, 'echo "nope"\nexit 1\n'
        )
        with self.base_moves_after_the_fetch():
            stderr = self.integrate_expecting_exit(
                4, "proj", "main", "fix/", self.message_path
            )
        self.assertIn("refused by the local pre-push hook", stderr)

    def test_unreachable_remote_is_still_network(self):
        # Loopback port 9 (discard) with nothing listening: connection
        # refused at once, no traffic leaves the machine. The fetch is
        # frozen so the push itself is what meets the dead remote; the
        # hook never runs, because git runs it only after reaching the
        # remote.
        url = "http://127.0.0.1:9/proj.git"
        gitw_test_support.git(self.clone, "remote", "set-url", "origin", url)
        gitw_test_support.add_pre_push_hook(
            self.clone, 'echo "hook ran"\nexit 1\n'
        )
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=url,
            remote="origin",
            default_branch="main",
        )
        with gitw_test_support.proxies_off(), \
                mock.patch.object(_MODULE.run, "fetch"):
            stderr = self.integrate_expecting_exit(
                6, "proj", "main", "fix/", self.message_path,
                entries={"proj": entry},
            )
        self.assertIn("unable to access", stderr)
        self.assertNotIn("hook ran", stderr)
        self.assertNotIn("trace2 unavailable", stderr)

    def test_hook_refusal_without_trace2_falls_back_visibly(self):
        gitw_test_support.add_pre_push_hook(
            self.clone, 'echo "nope"\nexit 1\n'
        )
        with mock.patch.object(
            _MODULE.run, "parse_push_trace", return_value=(False, None)
        ):
            stderr = self.integrate_expecting_exit(
                6, "proj", "main", "fix/", self.message_path
            )
        self.assertIn("nope\n", stderr)
        self.assertIn(
            "(trace2 unavailable; classification is text-only)", stderr
        )


class GitwIntegrateBareSlashTest(_IntegrateFixtureTest):
    def test_integrates_an_unprefixed_branch(self):
        gitw_test_support.git(self.clone, "branch", "-m", "foo-bar")
        payload = self.integrate("proj", "main", "/", self.message_path)
        self.assertEqual(payload["branch"], "foo-bar")

    def test_refuses_the_default_branch_as_source(self):
        gitw_test_support.git(self.clone, "switch", "main")
        stderr = self.integrate_expecting_exit(
            4, "proj", "develop", "/", self.message_path
        )
        self.assertIn("default branch", stderr)


if __name__ == "__main__":
    unittest.main()
