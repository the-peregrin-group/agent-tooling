"""Tests for lib.bdw_push, the coalesced Dolt push bdw starts after writes.

The push runner, the remote lookup, and the worker's spawn are injected, so
no test runs bd, git, or a network push; state goes to a temporary
directory.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from lib import bdw_push

_PUBLIC = "git@github.com:the-org/the-repo.git"
_PRIVATE = "git+ssh://git@forge.example:2299/someone/the-repo-dolt.git"


class RepositoryKeyTest(unittest.TestCase):
    def test_forms_of_one_repository_agree(self):
        forms = (
            "git@github.com:The-Org/the-repo.git",
            "git+ssh://git@github.com/the-org/the-repo.git",
            "ssh://git@github.com:22/the-org/the-repo",
            "https://github.com/the-org/the-repo.git/",
            "https://user@github.com/the-org/the-repo",
        )
        for form in forms:
            with self.subTest(form=form):
                self.assertTrue(bdw_push.same_repository(form, _PUBLIC))

    def test_different_repositories_differ(self):
        self.assertFalse(bdw_push.same_repository(_PRIVATE, _PUBLIC))
        self.assertFalse(bdw_push.same_repository(
            "git@github.com:the-org/other.git", _PUBLIC))
        self.assertFalse(bdw_push.same_repository(
            "git@gitlab.com:the-org/the-repo.git", _PUBLIC))

    def test_file_urls_and_paths(self):
        self.assertTrue(bdw_push.same_repository(
            "file:///srv/repo.git", "/srv/repo"))
        self.assertIsNone(bdw_push.repository_key(""))
        self.assertIsNone(bdw_push.repository_key("not a url"))


class DoltRemoteUrlsTest(unittest.TestCase):
    def setUp(self):
        self.beads = Path(tempfile.mkdtemp()).resolve() / ".beads"
        self.addCleanup(shutil.rmtree, self.beads.parent, ignore_errors=True)
        self.beads.mkdir()

    def write(self, metadata: dict, remotes: dict | None) -> None:
        (self.beads / "metadata.json").write_text(json.dumps(metadata))
        if remotes is not None:
            dolt = self.beads / "embeddeddolt" / "db" / ".dolt"
            dolt.mkdir(parents=True)
            (dolt / "repo_state.json").write_text(json.dumps(
                {"remotes": remotes, "backups": {
                    "default": {"url": "file:///backup"}}}))

    def test_reads_remote_urls_and_ignores_backups(self):
        self.write({"dolt_mode": "embedded", "dolt_database": "db"},
                   {"origin": {"name": "origin", "url": _PRIVATE}})
        self.assertEqual(bdw_push.dolt_remote_urls(self.beads), [_PRIVATE])

    def test_no_remotes(self):
        self.write({"dolt_mode": "embedded", "dolt_database": "db"}, {})
        self.assertEqual(bdw_push.dolt_remote_urls(self.beads), [])

    def test_not_embedded_means_no_remote_to_push_to(self):
        self.write({"dolt_mode": "server", "dolt_database": "db"},
                   {"origin": {"url": _PRIVATE}})
        self.assertEqual(bdw_push.dolt_remote_urls(self.beads), [])

    def test_unreadable_state_is_none_not_empty(self):
        self.write({"dolt_mode": "embedded", "dolt_database": "missing"},
                   None)
        self.assertIsNone(bdw_push.dolt_remote_urls(self.beads))
        (self.beads / "metadata.json").write_text("not json")
        self.assertIsNone(bdw_push.dolt_remote_urls(self.beads))


class FakeRunner:
    """Answers git's remote listing and bd's config and push calls."""

    def __init__(self, git_urls=(_PUBLIC,), git_code=0, no_push="false",
                 push_code=0, push_stderr=""):
        self.git_urls, self.git_code = git_urls, git_code
        self.no_push, self.push_code = no_push, push_code
        self.push_stderr = push_stderr
        self.calls = []

    def __call__(self, argv, environ, cwd):
        self.calls.append((list(argv), dict(environ)))
        if argv[0] == "git":
            out = "".join(f"remote.r{i}.url {url}\n"
                          for i, url in enumerate(self.git_urls))
            return self.git_code, out, ""
        if argv[1:] == ["config", "get", "no-push"]:
            return 0, f"{self.no_push}\n", ""
        if argv[1:] == ["dolt", "push", "--no-adopt"]:
            return self.push_code, "", self.push_stderr
        raise AssertionError(f"unexpected call {argv}")

    def pushes(self):
        return [call for call in self.calls if call[0][1:2] == ["dolt"]]


class PushOnceTest(unittest.TestCase):
    def setUp(self):
        root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        self.beads = root / "ws" / ".beads"
        self.beads.mkdir(parents=True)
        self.state = root / "state"
        self.state.mkdir()

    def push(self, runner, urls=(_PRIVATE,)):
        return bdw_push.push_once(
            self.beads, self.state, "/bin/bd", {"PATH": "/bin"},
            runner=runner,
            remotes=lambda _: None if urls is None else list(urls))

    def test_unreadable_remotes_record_a_failure_instead_of_clearing(self):
        runner = FakeRunner()
        self.assertEqual(self.push(runner, urls=None), "failed")
        self.assertEqual(runner.calls, [])
        self.assertIn("cannot read", bdw_push.last_failure(
            self.state)["reason"])

    def test_no_remote_clears_an_old_failure(self):
        (self.state / "last-failure.json").write_text('{"reason": "x"}')
        self.assertEqual(self.push(FakeRunner(), urls=()), "no-remote")
        self.assertIsNone(bdw_push.last_failure(self.state))

    def test_no_push_raw_values_opt_out_and_clear_the_failure(self):
        for value in ("1", "yes", "true", "ON"):
            with self.subTest(value=value):
                (self.state / "last-failure.json").write_text(
                    '{"reason": "x"}')
                runner = FakeRunner(no_push=value)
                self.assertEqual(self.push(runner), "opted-out")
                self.assertEqual(runner.pushes(), [])
                self.assertIsNone(bdw_push.last_failure(self.state))
        for value in ("false", "0", "", "no-push (not set in config.yaml)"):
            with self.subTest(value=value):
                self.assertEqual(self.push(FakeRunner(no_push=value)),
                                 "pushed")

    def test_failure_record_is_replaced_atomically(self):
        bdw_push._record_failure(self.state, "first")
        bdw_push._record_failure(self.state, "second")
        self.assertEqual(bdw_push.last_failure(self.state)["reason"],
                         "second")
        self.assertEqual(sorted(p.name for p in self.state.iterdir()),
                         ["last-failure.json", "push.log"])

    def test_pushes_without_adopting_and_clears_a_failure(self):
        (self.state / "last-failure.json").write_text('{"reason": "x"}')
        runner = FakeRunner()
        self.assertEqual(self.push(runner), "pushed")
        (argv, environ), = runner.pushes()
        self.assertEqual(argv, ["/bin/bd", "dolt", "push", "--no-adopt"])
        self.assertEqual(environ["BD_NO_REMOTE_ADOPT"], "1")
        self.assertIsNone(bdw_push.last_failure(self.state))

    def test_no_remote_does_nothing(self):
        runner = FakeRunner()
        self.assertEqual(self.push(runner, urls=()), "no-remote")
        self.assertEqual(runner.calls, [])

    def test_remote_matching_a_git_remote_is_refused(self):
        for dolt_url in ("git+ssh://git@github.com/the-org/the-repo.git",
                         "https://github.com/The-Org/the-repo"):
            with self.subTest(dolt_url=dolt_url):
                runner = FakeRunner()
                self.assertEqual(self.push(runner, urls=(_PRIVATE, dolt_url)),
                                 "refused")
                self.assertEqual(runner.pushes(), [])
                failure = bdw_push.last_failure(self.state)
                self.assertIn("same repository", failure["reason"])
                self.assertNotIn("github", json.dumps(failure))

    def test_unreadable_git_remotes_refuse(self):
        runner = FakeRunner(git_code=128)
        self.assertEqual(self.push(runner), "refused")
        self.assertEqual(runner.pushes(), [])

    def test_no_git_remotes_at_all_allows_the_push(self):
        runner = FakeRunner(git_urls=(), git_code=1)
        self.assertEqual(self.push(runner), "pushed")

    def test_no_push_config_opts_out(self):
        runner = FakeRunner(no_push="true")
        self.assertEqual(self.push(runner), "opted-out")
        self.assertEqual(runner.pushes(), [])

    def test_failed_push_is_recorded(self):
        runner = FakeRunner(push_code=1, push_stderr="network down")
        self.assertEqual(self.push(runner), "failed")
        failure = bdw_push.last_failure(self.state)
        self.assertEqual(failure["reason"], "bd dolt push exited 1")
        self.assertIn("network down", (self.state / "push.log").read_text())


class WorkerTest(unittest.TestCase):
    def setUp(self):
        root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        self.beads = root / ".beads"
        self.state = root / "state"
        self.state.mkdir()

    def run_worker(self, push):
        return bdw_push.run_worker(self.beads, self.state, "bd", {},
                                   push=push)

    def test_nothing_dirty_means_no_push(self):
        self.assertEqual(self.run_worker(lambda: "pushed"), [])

    def test_one_dirty_mark_means_one_push(self):
        (self.state / "dirty").touch()
        self.assertEqual(self.run_worker(lambda: "pushed"), ["pushed"])
        self.assertFalse((self.state / "dirty").exists())

    def test_writes_during_a_push_get_one_more_push(self):
        (self.state / "dirty").touch()
        marks = [True, True, False]

        def push():
            if marks.pop(0):
                (self.state / "dirty").touch()  # a write landed meanwhile
            return "pushed"

        self.assertEqual(self.run_worker(push), ["pushed"] * 3)

    def test_a_long_run_of_writes_is_pushed_to_the_end(self):
        # Writes keep landing during each push, more passes in a row than
        # any cap would allow; the mark set during the last push still
        # gets its push, and nothing is left dirty.
        (self.state / "dirty").touch()
        writes_during_pushes = 60
        pushes = []

        def push():
            pushes.append(1)
            if len(pushes) <= writes_during_pushes:
                (self.state / "dirty").touch()
            return "pushed"

        self.assertEqual(self.run_worker(push),
                         ["pushed"] * (writes_during_pushes + 1))
        self.assertFalse((self.state / "dirty").exists())

    def test_a_mark_set_after_the_last_take_is_pushed_after_unlock(self):
        # A write lands after the worker's last take but before it releases
        # the lock, so that write's own worker found the lock held and
        # left; the re-check after the release must push it.
        (self.state / "dirty").touch()
        take = bdw_push._take_dirty
        empty_takes = []

        def take_then_write(state):
            taken = take(state)
            if not taken and not empty_takes:
                empty_takes.append(1)
                (state / "dirty").touch()
            return taken

        with mock.patch.object(bdw_push, "_take_dirty", take_then_write):
            outcomes = self.run_worker(lambda: "pushed")
        self.assertEqual(outcomes, ["pushed", "pushed"])
        self.assertFalse((self.state / "dirty").exists())

    def test_exit_code_follows_the_last_push(self):
        cases = (([], 0), (["pushed"], 0), (["no-remote"], 0),
                 (["opted-out"], 0), (["pushed", "failed"], 1),
                 (["failed", "pushed"], 0), (["refused"], 4))
        for outcomes, code in cases:
            with self.subTest(outcomes=outcomes):
                self.assertEqual(bdw_push.exit_code(outcomes), code)

    def test_a_held_lock_leaves_the_work_to_its_holder(self):
        (self.state / "dirty").touch()
        with open(self.state / "lock", "a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            self.assertEqual(self.run_worker(lambda: "pushed"), [])
        self.assertTrue((self.state / "dirty").exists())

    def test_no_push_is_asked_once_per_run(self):
        (self.state / "dirty").touch()
        runner = FakeRunner()
        pushes_left = [3]
        real_call = runner.__call__

        def runner_with_writes(argv, environ, cwd):
            result = real_call(argv, environ, cwd)
            if argv[1:2] == ["dolt"] and pushes_left[0]:
                pushes_left[0] -= 1
                (self.state / "dirty").touch()  # a write during the push
            return result

        outcomes = bdw_push.run_worker(
            self.beads, self.state, "/bin/bd", {}, runner=runner_with_writes,
            remotes=lambda _: [_PRIVATE])
        self.assertEqual(outcomes, ["pushed"] * 4)
        config_calls = [call for call in runner.calls
                        if call[0][1:] == ["config", "get", "no-push"]]
        self.assertEqual(len(config_calls), 1)

    def test_the_lock_is_handed_to_every_command_of_a_push(self):
        (self.state / "dirty").touch()
        seen = []

        def runner(argv, environ, cwd, timeout=None, pass_fds=()):
            seen.append(tuple(pass_fds))
            return 0, "false\n", ""

        with mock.patch.object(bdw_push, "run_command", runner):
            outcomes = bdw_push.run_worker(
                self.beads, self.state, "/bin/bd", {},
                remotes=lambda _: [_PRIVATE])
        self.assertEqual(outcomes, ["pushed"])
        self.assertTrue(seen)
        for fds in seen:
            self.assertEqual(len(fds), 1)


class RunCommandTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_a_timeout_kills_the_whole_process_group(self):
        pid_file = self.root / "grandchild"
        script = f"/bin/sleep 30 & echo $! > {pid_file}; wait"
        code, _, err = bdw_push.run_command(
            ["/bin/sh", "-c", script], {"PATH": "/bin"}, self.root,
            timeout=1)
        self.assertEqual(code, 124)
        self.assertIn("timed out", err)
        grandchild = int(pid_file.read_text())
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                os.kill(grandchild, 0)
            except ProcessLookupError:
                return
            time.sleep(0.05)
        self.fail("the grandchild outlived the timeout")

    def test_passed_fds_reach_the_child(self):
        with open(self.root / "lock", "a") as handle:
            fd = handle.fileno()
            code, _, _ = bdw_push.run_command(
                ["/bin/sh", "-c", f"test -e /dev/fd/{fd}"], {"PATH": "/bin"},
                self.root, pass_fds=(fd,))
            self.assertEqual(code, 0)
            code, _, _ = bdw_push.run_command(
                ["/bin/sh", "-c", f"test -e /dev/fd/{fd}"], {"PATH": "/bin"},
                self.root)
            self.assertNotEqual(code, 0)


class RequestPushTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.beads = self.root / ".beads"
        self.environ = {"XDG_STATE_HOME": str(self.root / "s")}

    def state(self) -> Path:
        return bdw_push.state_dir(self.beads, self.environ)

    def test_marks_dirty_and_spawns_the_system_interpreter(self):
        spawned = []
        self.assertIsNone(bdw_push.request_push(
            self.beads, "/bin/bd", self.environ,
            spawn=lambda argv, environ: spawned.append(list(argv))))
        state = self.state()
        self.assertTrue((state / "dirty").exists())
        self.assertTrue(str(state).startswith(
            str(self.root / "s" / "agent-tooling" / "bdw-push")))
        (argv,) = spawned
        self.assertEqual(argv[0], "/usr/bin/python3")
        self.assertTrue(argv[1].endswith("bdw_push.py"))
        self.assertEqual(argv[2:], [str(self.beads), "/bin/bd"])

    def test_the_state_directory_is_private(self):
        bdw_push.request_push(self.beads, "bd", self.environ,
                              spawn=lambda *_: None)
        self.assertEqual(self.state().stat().st_mode & 0o777, 0o700)

    def test_a_held_lock_means_no_new_worker(self):
        state = self.state()
        state.mkdir(parents=True)
        spawned = []
        with open(state / "lock", "a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            self.assertIsNone(bdw_push.request_push(
                self.beads, "bd", self.environ,
                spawn=lambda *args: spawned.append(args)))
        self.assertEqual(spawned, [])
        self.assertTrue((state / "dirty").exists())

    def test_home_fallback_and_no_state_dir(self):
        state = bdw_push.state_dir(self.beads, {"HOME": "/h"})
        self.assertEqual(state.parent, Path("/h/.local/state/agent-tooling/"
                                            "bdw-push"))
        self.assertIsNone(bdw_push.request_push(
            self.beads, "bd", {}, spawn=lambda *_: None))

    def test_an_unwritable_state_directory_is_reported(self):
        blocker = self.root / "s"
        blocker.write_text("a file where the state root should be")
        problem = bdw_push.request_push(self.beads, "bd", self.environ,
                                        spawn=lambda *_: None)
        self.assertIsNotNone(problem)
        self.assertIn("not writable", problem)

    def test_spawn_failure_is_recorded_and_reported(self):
        def fail(argv, environ):
            raise OSError("no python")

        problem = bdw_push.request_push(self.beads, "bd", self.environ,
                                        spawn=fail)
        self.assertIn("cannot start", problem)
        self.assertIn("cannot start",
                      bdw_push.last_failure(self.state())["reason"])


class TruthyTest(unittest.TestCase):
    def test_raw_config_values(self):
        for value in ("1", "true", "TRUE", " yes\n", "on"):
            self.assertTrue(bdw_push.is_truthy(value), value)
        for value in (None, "", "0", "false", "no", "off", "2"):
            self.assertFalse(bdw_push.is_truthy(value), value)


if __name__ == "__main__":
    unittest.main()
