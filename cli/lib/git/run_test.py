"""Tests for lib.git.run: the non-interactive environment and remote
failure classification.

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
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import gitw_test_support
from lib import plan
from lib.git import repo, run


class EnvironmentTest(unittest.TestCase):
    def test_base_environment_neuters_prompts(self):
        environment = run.base_environment()
        self.assertEqual(environment["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(environment["GIT_EDITOR"], "true")
        self.assertEqual(environment["GIT_PAGER"], "cat")
        self.assertEqual(environment["GIT_ASKPASS"], "/usr/bin/false")
        self.assertEqual(environment["SSH_ASKPASS"], "/usr/bin/false")
        self.assertEqual(environment["GIT_OPTIONAL_LOCKS"], "0")
        self.assertEqual(environment["LC_ALL"], "C")

    def test_remote_environment_batches_ssh_by_default(self):
        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp)
        gitw_test_support.git(Path(temp), "init", ".")
        cleaned = {
            key: value
            for key, value in os.environ.items()
            if key not in ("GIT_SSH_COMMAND", "GIT_SSH")
        }
        with mock.patch.dict(os.environ, cleaned, clear=True), \
                gitw_test_support.isolated_git_config():
            environment = run.remote_environment(Path(temp))
        self.assertEqual(environment["GIT_SSH_COMMAND"], "ssh -oBatchMode=yes")

    def test_remote_environment_respects_user_ssh_variable(self):
        with mock.patch.dict(os.environ, {"GIT_SSH_COMMAND": "my-ssh"}):
            environment = run.remote_environment(Path("."))
        self.assertEqual(environment["GIT_SSH_COMMAND"], "my-ssh")

    def test_remote_environment_respects_configured_ssh_command(self):
        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp)
        gitw_test_support.git(Path(temp), "init", ".")
        gitw_test_support.git(
            Path(temp), "config", "core.sshCommand", "custom-ssh"
        )
        cleaned = {
            key: value
            for key, value in os.environ.items()
            if key not in ("GIT_SSH_COMMAND", "GIT_SSH")
        }
        with mock.patch.dict(os.environ, cleaned, clear=True), \
                gitw_test_support.isolated_git_config():
            environment = run.remote_environment(Path(temp))
        self.assertNotIn("GIT_SSH_COMMAND", environment)


class ClassifyRemoteFailureTest(unittest.TestCase):
    def test_auth_markers(self):
        for detail in (
            "git@forge.example.com: Permission denied (publickey).",
            "fatal: Authentication failed for 'https://forge.example.com/'",
            "fatal: could not read Username for 'https://x': terminal "
            "prompts disabled",
        ):
            with self.subTest(detail=detail):
                self.assertEqual(
                    run.classify_remote_failure(detail), plan.EXIT_AUTH
                )

    def test_missing_repository_markers(self):
        for detail in (
            "remote: Repository not found.",
            "fatal: '/x/y' does not appear to be a git repository",
        ):
            with self.subTest(detail=detail):
                self.assertEqual(
                    run.classify_remote_failure(detail), plan.EXIT_NOT_FOUND
                )

    def test_remote_rejection_status_line(self):
        for detail in (
            " ! [remote rejected] topic -> topic (pre-receive hook declined)",
            "remote: permission denied by policy\n"
            " ! [remote rejected] topic -> topic (hook declined)",
        ):
            with self.subTest(detail=detail):
                self.assertTrue(run.is_remote_rejection(detail))

    def test_ref_update_race_reasons(self):
        for reason in (
            "failed to update ref",
            "failed to lock",
            "cannot lock ref 'refs/heads/main'",
        ):
            detail = f" ! [remote rejected] main -> main ({reason})"
            with self.subTest(reason=reason):
                self.assertTrue(run.is_remote_rejection(detail))
                self.assertTrue(run.is_ref_update_race(detail))

    def test_hook_declines_are_not_ref_update_races(self):
        for detail in (
            " ! [remote rejected] main -> main (pre-receive hook declined)",
            "remote: failed to update ref\n"
            " ! [remote rejected] main -> main (hook declined)",
            " ! [rejected] main -> main (stale info)",
        ):
            with self.subTest(detail=detail):
                self.assertFalse(run.is_ref_update_race(detail))

    def test_lease_and_transport_failures_are_not_remote_rejections(self):
        for detail in (
            " ! [rejected] topic -> topic (stale info)",
            " ! [rejected] main -> main (non-fast-forward)",
            "fatal: unable to access 'https://x/': Connection timed out",
            "",
        ):
            with self.subTest(detail=detail):
                self.assertFalse(run.is_remote_rejection(detail))

    def test_everything_else_is_network(self):
        for detail in (
            "ssh: Could not resolve hostname forge.example.com",
            "fatal: unable to access 'https://x/': Connection timed out",
            "",
        ):
            with self.subTest(detail=detail):
                self.assertEqual(
                    run.classify_remote_failure(detail), plan.EXIT_NETWORK
                )


class TimeoutClassificationTest(unittest.TestCase):
    def _timeout(self):
        return mock.patch.object(
            run.subprocess, "run",
            side_effect=subprocess.TimeoutExpired(cmd=["git"], timeout=300),
        )

    def test_local_timeout_is_unclassified_runtime(self):
        # A stalled local command (hung hook, fsmonitor) must not classify
        # as network -- exit 6 is the retryable class, and an unattended
        # retry loop would re-run the hung command.
        with self._timeout():
            with self.assertRaises(run.GitError) as caught:
                run.run(["status"], Path("."))
        self.assertEqual(caught.exception.exit_code, plan.EXIT_RUNTIME)

    def test_remote_timeout_is_network(self):
        with self._timeout():
            with self.assertRaises(run.GitError) as caught:
                run.run(["fetch", "origin"], Path("."), remote=True)
        self.assertEqual(caught.exception.exit_code, plan.EXIT_NETWORK)


class RunHelpersTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp)
        self.repository = Path(temp)
        gitw_test_support.git(self.repository, "init", ".")

    def test_output_returns_none_on_failure(self):
        self.assertIsNone(
            run.output(["rev-parse", "--verify", "--quiet", "nope"], self.repository)
        )

    def test_must_raises_unclassified_git_error(self):
        with self.assertRaises(run.GitError) as caught:
            run.must(["rev-parse", "--verify", "no-such-ref"], self.repository)
        self.assertEqual(caught.exception.exit_code, plan.EXIT_RUNTIME)

    def test_fetch_prunes_remote_tracking_refs_deleted_on_the_remote(self):
        # gitw-push's named-target lease reads its expectation from the
        # remote-tracking ref; a ref deleted on the remote must not linger
        # locally or every later pointer move refuses as "moved".
        base = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, base, ignore_errors=True)
        remote, seed, clone = gitw_test_support.make_remote_and_clone(base)
        gitw_test_support.git(seed, "push", "origin", "main:refs/heads/x/gone")
        gitw_test_support.git(clone, "fetch", "origin")
        gitw_test_support.git(seed, "push", "origin", ":refs/heads/x/gone")
        with gitw_test_support.isolated_git_config():
            run.fetch("origin", clone)
        self.assertFalse(repo.ref_exists(clone, "refs/remotes/origin/x/gone"))

    def test_fetch_failure_is_classified(self):
        gitw_test_support.git(
            self.repository, "remote", "add", "origin", "/nonexistent/remote.git"
        )
        with gitw_test_support.isolated_git_config():
            with self.assertRaises(run.GitError) as caught:
                run.fetch("origin", self.repository)
        self.assertEqual(caught.exception.exit_code, plan.EXIT_NOT_FOUND)


def _trace(*events: dict) -> str:
    return "".join(json.dumps(event) + "\n" for event in events)


_VERSION = {"event": "version", "sid": "a", "evt": "3", "exe": "2.43.0"}
_PRE_PUSH_START = {"event": "child_start", "sid": "a", "child_id": 0,
                   "child_class": "hook", "hook_name": "pre-push"}


class RelayTest(unittest.TestCase):
    def test_relay_passes_text_through_newline_terminated(self):
        cases = (("", ""), ("a", "a\n"), ("a\n", "a\n"), ("a\nb", "a\nb\n"))
        for text, expected in cases:
            with self.subTest(text=text):
                with contextlib.redirect_stderr(io.StringIO()) as stderr:
                    run.relay(text)
                self.assertEqual(stderr.getvalue(), expected)


class ParsePushTraceTest(unittest.TestCase):
    """Direct calls on run.parse_push_trace, the trace2 half of
    traced_push."""

    def test_matches_only_a_failing_pre_push_hook_in_its_own_session(self):
        text = _trace(
            _VERSION,
            _PRE_PUSH_START,
            {"event": "child_exit", "sid": "a", "child_id": 0, "code": 0},
            {"event": "child_start", "sid": "a", "child_id": 1,
             "child_class": "hook", "hook_name": "reference-transaction"},
            {"event": "child_exit", "sid": "a", "child_id": 1, "code": 1},
            # Same child_id in another process's session is a different
            # child: this failing transport must not match sid a's hook.
            {"event": "child_exit", "sid": "b", "child_id": 0, "code": 128},
        ) + "not json\n"
        self.assertEqual(run.parse_push_trace(text), (True, None))
        failing = _trace(
            _VERSION,
            _PRE_PUSH_START,
            {"event": "child_exit", "sid": "a", "child_id": 0, "code": 7},
        )
        self.assertEqual(run.parse_push_trace(failing), (True, 7))

    def test_nested_session_hook_is_ignored(self):
        nested = [
            {"event": "child_start", "sid": "a/b", "child_id": 0,
             "child_class": "hook", "hook_name": "pre-push"},
            {"event": "child_exit", "sid": "a/b", "child_id": 0, "code": 1},
        ]
        text = _trace(
            _VERSION, _PRE_PUSH_START,
            {"event": "child_exit", "sid": "a", "child_id": 0, "code": 0},
            *nested,
        )
        self.assertEqual(run.parse_push_trace(text), (True, None))
        # The root hook's own refusal is still reported.
        failing = _trace(
            _VERSION, _PRE_PUSH_START, *nested,
            {"event": "child_exit", "sid": "a", "child_id": 0, "code": 7},
        )
        self.assertEqual(run.parse_push_trace(failing), (True, 7))

    def test_hook_without_a_string_sid_is_ignored(self):
        text = _trace(
            _VERSION,
            {"event": "child_start", "child_id": 0, "child_class": "hook",
             "hook_name": "pre-push"},
            {"event": "child_exit", "child_id": 0, "code": 1},
        )
        self.assertEqual(run.parse_push_trace(text), (True, None))

    def test_non_integer_exit_code_is_no_signal(self):
        for code in (None, "1", 1.0, True):
            with self.subTest(code=code):
                exit_event = {"event": "child_exit", "sid": "a",
                              "child_id": 0}
                if code is not None:
                    exit_event["code"] = code
                text = _trace(_VERSION, _PRE_PUSH_START, exit_event)
                self.assertEqual(run.parse_push_trace(text), (True, None))

    def test_empty_trace_reports_trace2_unavailable(self):
        # traced_push reads a missing or unwritable trace file as "".
        self.assertEqual(run.parse_push_trace(""), (False, None))


class HungPrePushHookTest(unittest.TestCase):
    def test_started_without_exit_is_hung(self):
        text = _trace(_VERSION, _PRE_PUSH_START) + '{"event": "chi'
        self.assertTrue(run.hung_pre_push_hook(text))

    def test_completed_hook_is_not_hung(self):
        text = _trace(
            _VERSION, _PRE_PUSH_START,
            {"event": "child_exit", "sid": "a", "child_id": 0, "code": 0},
        )
        self.assertFalse(run.hung_pre_push_hook(text))

    def test_exit_in_another_session_does_not_complete_the_hook(self):
        text = _trace(
            _VERSION, _PRE_PUSH_START,
            {"event": "child_exit", "sid": "b", "child_id": 0, "code": 0},
        )
        self.assertTrue(run.hung_pre_push_hook(text))

    def test_other_children_and_empty_trace_are_not_hung(self):
        text = _trace(
            _VERSION,
            {"event": "child_start", "sid": "a", "child_id": 0,
             "child_class": "transport/ssh"},
        )
        self.assertFalse(run.hung_pre_push_hook(text))
        self.assertFalse(run.hung_pre_push_hook(""))


class TracedPushTimeoutTest(unittest.TestCase):
    def _timeout_after(self, trace_events, stdout=None, stderr=None):
        def fake_run(command, **kwargs):
            trace = Path(kwargs["env"]["GIT_TRACE2_EVENT"])
            trace.write_text(_trace(*trace_events), encoding="utf-8")
            raise subprocess.TimeoutExpired(
                cmd=command, timeout=300, output=stdout, stderr=stderr
            )
        return mock.patch.object(run.subprocess, "run", side_effect=fake_run)

    def test_timeout_with_a_hung_hook_is_a_hook_verdict(self):
        with self._timeout_after(
            [_VERSION, _PRE_PUSH_START], b"out\n", b"hook said hi\n"
        ):
            pushed = run.traced_push(["push"], Path("."), {})
        self.assertTrue(pushed.hook_hung)
        self.assertIsNone(pushed.hook_code)
        self.assertNotEqual(pushed.result.returncode, 0)
        self.assertEqual(pushed.result.stdout, "out\n")
        self.assertEqual(pushed.result.stderr, "hook said hi\n")

    def test_timeout_without_output_decodes_to_empty(self):
        with self._timeout_after([_VERSION, _PRE_PUSH_START]):
            pushed = run.traced_push(["push"], Path("."), {})
        self.assertEqual((pushed.result.stdout, pushed.result.stderr), ("", ""))

    def test_timeout_without_a_hook_stays_network(self):
        with self._timeout_after([_VERSION]):
            with self.assertRaises(run.GitError) as caught:
                run.traced_push(["push"], Path("."), {})
        self.assertEqual(caught.exception.exit_code, plan.EXIT_NETWORK)

    def test_timeout_after_the_hook_exited_stays_network(self):
        events = [
            _VERSION, _PRE_PUSH_START,
            {"event": "child_exit", "sid": "a", "child_id": 0, "code": 0},
        ]
        with self._timeout_after(events):
            with self.assertRaises(run.GitError) as caught:
                run.traced_push(["push"], Path("."), {})
        self.assertEqual(caught.exception.exit_code, plan.EXIT_NETWORK)


if __name__ == "__main__":
    unittest.main()
