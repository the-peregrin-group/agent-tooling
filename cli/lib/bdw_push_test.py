"""Tests for lib.bdw_push, the coalesced Dolt push bdw starts after writes.

The push runner, the remote lookup, and the worker's spawn are injected, so
no test runs bd, git, or a network push; state goes to a temporary
directory.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import errno
import fcntl
import json
import os
import shutil
import subprocess
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

    def __call__(self, argv, environ, cwd, pass_fds=()):
        self.calls.append((list(argv), dict(environ)))
        self.fds = [os.fstat(fd).st_ino for fd in pass_fds]
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

    def test_no_marker_means_no_push(self):
        self.assertEqual(self.run_worker(lambda: "pushed"), [])

    def test_one_marker_means_one_push(self):
        (self.state / "pending").touch()
        self.assertEqual(self.run_worker(lambda: "pushed"), ["pushed"])
        self.assertFalse((self.state / "pending").exists())
        self.assertFalse((self.state / "pushing").exists())

    def test_the_write_is_pushing_until_its_outcome_is_recorded(self):
        (self.state / "pending").touch()
        seen = []

        def push():
            seen.append(((self.state / "pending").exists(),
                         (self.state / "pushing").exists()))
            return "failed"

        self.assertEqual(self.run_worker(push), ["failed"])
        self.assertEqual(seen, [(False, True)])
        self.assertFalse((self.state / "pushing").exists())

    def test_a_leftover_pushing_is_pushed_and_folds_in_pending(self):
        for markers in (("pushing",), ("pushing", "pending")):
            with self.subTest(markers=markers):
                for marker in markers:
                    (self.state / marker).touch()
                self.assertEqual(self.run_worker(lambda: "pushed"),
                                 ["pushed"])
                self.assertFalse((self.state / "pending").exists())
                self.assertFalse((self.state / "pushing").exists())

    def test_writes_during_a_push_get_one_more_push(self):
        (self.state / "pending").touch()
        marks = [True, True, False]

        def push():
            if marks.pop(0):
                (self.state / "pending").touch()  # a write landed meanwhile
            return "pushed"

        self.assertEqual(self.run_worker(push), ["pushed"] * 3)

    def test_a_long_run_of_writes_is_pushed_to_the_end(self):
        # Writes keep landing during each push, more passes in a row than
        # any cap would allow; the mark set during the last push still
        # gets its push, and no marker is left.
        (self.state / "pending").touch()
        writes_during_pushes = 60
        pushes = []

        def push():
            pushes.append(1)
            if len(pushes) <= writes_during_pushes:
                (self.state / "pending").touch()
            return "pushed"

        self.assertEqual(self.run_worker(push),
                         ["pushed"] * (writes_during_pushes + 1))
        self.assertFalse((self.state / "pending").exists())

    def test_a_mark_set_after_the_last_check_is_pushed_after_unlock(self):
        # A write lands after the worker's last check for a mark but before
        # it releases the lock, so that write's own request found the lock
        # held; the re-check after the release must push it.
        (self.state / "pending").touch()
        has_mark = bdw_push._has_mark
        empty_checks = []

        def check_then_write(state):
            found = has_mark(state)
            if not found and not empty_checks:
                empty_checks.append(1)
                (state / "pending").touch()
            return found

        with mock.patch.object(bdw_push, "_has_mark", check_then_write):
            outcomes = self.run_worker(lambda: "pushed")
        self.assertEqual(outcomes, ["pushed", "pushed"])
        self.assertFalse((self.state / "pending").exists())

    def test_exit_code_follows_the_last_push(self):
        cases = (([], 0), (["pushed"], 0), (["no-remote"], 0),
                 (["opted-out"], 0), (["pushed", "failed"], 1),
                 (["failed", "pushed"], 0), (["refused"], 4))
        for outcomes, code in cases:
            with self.subTest(outcomes=outcomes):
                self.assertEqual(bdw_push.exit_code(outcomes), code)

    def test_a_held_lock_leaves_the_work_to_its_holder(self):
        (self.state / "pending").touch()
        with open(self.state / "lock", "a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            self.assertEqual(self.run_worker(lambda: "pushed"), [])
        self.assertTrue((self.state / "pending").exists())

    def test_no_push_is_asked_once_per_run(self):
        (self.state / "pending").touch()
        runner = FakeRunner()
        pushes_left = [3]
        real_call = runner.__call__

        def runner_with_writes(argv, environ, cwd, pass_fds=()):
            result = real_call(argv, environ, cwd, pass_fds=pass_fds)
            if argv[1:2] == ["dolt"] and pushes_left[0]:
                pushes_left[0] -= 1
                (self.state / "pending").touch()  # a write during the push
            return result

        outcomes = bdw_push.run_worker(
            self.beads, self.state, "/bin/bd", {}, runner=runner_with_writes,
            remotes=lambda _: [_PRIVATE])
        self.assertEqual(outcomes, ["pushed"] * 4)
        config_calls = [call for call in runner.calls
                        if call[0][1:] == ["config", "get", "no-push"]]
        self.assertEqual(len(config_calls), 1)

    def test_the_inflight_fd_reaches_only_bd_dolt_push(self):
        (self.state / "pending").touch()
        seen = {}

        def runner(argv, environ, cwd, pass_fds=()):
            seen[" ".join(argv[1:3])] = [os.fstat(fd).st_ino
                                          for fd in pass_fds]
            # The worker holds the push-in-flight lock for the whole pass.
            self.assertIsNone(bdw_push._try_lock(self.state, "inflight"))
            return (1, "", "") if argv[0] == "git" else (0, "false\n", "")

        outcomes = bdw_push.run_worker(
            self.beads, self.state, "/bin/bd", {}, runner=runner,
            remotes=lambda _: [_PRIVATE])
        self.assertEqual(outcomes, ["pushed"])
        inflight = (self.state / "inflight").stat().st_ino
        self.assertNotEqual(inflight, (self.state / "lock").stat().st_ino)
        self.assertEqual(seen, {"-C " + str(self.beads.parent): [],
                                "config get": [],
                                "dolt push": [inflight]})
        # Released after the pass.
        handle = bdw_push._try_lock(self.state, "inflight")
        self.assertIsNotNone(handle)
        handle.close()

    def test_a_held_inflight_lock_keeps_the_mark_and_stops(self):
        (self.state / "pending").touch()
        runner = FakeRunner()
        with open(self.state / "inflight", "a") as orphan:
            fcntl.flock(orphan, fcntl.LOCK_EX)
            outcomes = bdw_push.run_worker(
                self.beads, self.state, "/bin/bd", {}, runner=runner,
                remotes=lambda _: [_PRIVATE], inflight_timeout=0.3)
        self.assertEqual(outcomes, ["failed"])
        self.assertEqual(runner.calls, [])
        self.assertTrue((self.state / "pending").exists())
        reason = bdw_push.last_failure(self.state)["reason"]
        self.assertIn("push-in-flight lock", reason)
        self.assertIn(str(self.state / "inflight"), reason)
        self.assertEqual(bdw_push.exit_code(outcomes), 1)

    def test_an_unexpected_error_before_the_claim_is_recorded(self):
        # The push-in-flight lock path cannot be opened (the reviewer's
        # repro): recorded, the mark kept, the worker stopped.
        (self.state / "inflight").mkdir()
        (self.state / "pending").touch()
        outcomes = bdw_push.run_worker(
            self.beads, self.state, "/bin/bd", {}, runner=FakeRunner(),
            remotes=lambda _: [_PRIVATE])
        self.assertEqual(outcomes, ["failed"])
        self.assertTrue((self.state / "pending").exists())
        self.assertIn("the push worker failed",
                      bdw_push.last_failure(self.state)["reason"])

    def test_an_unexpected_error_inside_a_push_is_recorded(self):
        (self.state / "pending").touch()

        def explode():
            raise RuntimeError("boom")

        self.assertEqual(self.run_worker(explode), ["failed"])
        self.assertEqual(bdw_push.last_failure(self.state)["reason"],
                         "the push worker failed: boom")

    def test_main_records_an_error_outside_any_pass(self):
        environ = {"XDG_STATE_HOME": str(self.state.parent / "xdg")}
        state = bdw_push.state_dir(self.beads, environ)
        state.mkdir(parents=True)
        (state / "lock").mkdir()  # the coordination lock cannot be opened
        with mock.patch.dict(os.environ, environ, clear=True):
            self.assertEqual(bdw_push.main([str(self.beads), "bd"]), 1)
        self.assertIn("the push worker failed",
                      bdw_push.last_failure(state)["reason"])


# A bd stand-in whose push leaves a detached (setsid) sleeper behind, as
# git's background gc or a credential daemon would: the sleeper inherits
# every fd bd had, the inflight lock included.
_ORPHANING_BD = """#!/bin/sh
case "$1 $2" in
"config get") echo false; exit 0 ;;
"dolt push")
    echo push >> "$PUSH_LOG"
    /usr/bin/python3 -c 'import os, time; os.setsid(); \\
time.sleep(float(os.environ["SLEEPER_SECONDS"]))' &
    exit 0 ;;
esac
exit 0
"""


class OrphanedDescendantTest(unittest.TestCase):
    """End to end, with the real run_command: a write after a push whose
    descendant outlived it is pushed or warned about, never stranded."""

    def setUp(self):
        root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        self.beads = root / "ws" / ".beads"
        self.beads.mkdir(parents=True)
        self.state = root / "state"
        self.state.mkdir()
        bin_dir = root / "bin"
        bin_dir.mkdir()
        self.bd = bin_dir / "bd"
        self.bd.write_text(_ORPHANING_BD)
        self.bd.chmod(0o755)
        git = bin_dir / "git"
        git.write_text("#!/bin/sh\nexit 1\n")  # no git remotes
        git.chmod(0o755)
        self.push_log = root / "pushes"
        self.environ = {"PATH": str(bin_dir), "PUSH_LOG": str(self.push_log),
                        "SLEEPER_SECONDS": "2"}

    def worker(self, inflight_timeout):
        (self.state / "pending").touch()  # a write
        return bdw_push.run_worker(
            self.beads, self.state, str(self.bd), self.environ,
            remotes=lambda _: [_PRIVATE], inflight_timeout=inflight_timeout)

    def pushes(self):
        if not self.push_log.exists():
            return 0
        return len(self.push_log.read_text().splitlines())

    def test_a_write_after_an_orphaning_push_is_warned_or_pushed(self):
        self.assertEqual(self.worker(inflight_timeout=5), ["pushed"])
        # The worker is gone and the coordination lock is free at once, so
        # the next write starts a worker...
        handle = bdw_push._try_lock(self.state)
        self.assertIsNotNone(handle)
        handle.close()
        # ...which, while the orphan lives, waits, then warns, keeping the
        # write...
        self.assertEqual(self.worker(inflight_timeout=0.3), ["failed"])
        self.assertIn("push-in-flight lock",
                      bdw_push.last_failure(self.state)["reason"])
        self.assertTrue((self.state / "pending").exists())
        self.assertEqual(self.pushes(), 1)
        # ...and once the orphan exits within the wait, pushes.
        self.assertEqual(self.worker(inflight_timeout=10), ["pushed"])
        self.assertEqual(self.pushes(), 2)
        self.assertIsNone(bdw_push.last_failure(self.state))


class KilledWorkerTest(unittest.TestCase):
    """A real worker process, SIGKILLed while it waits for a held
    push-in-flight lock, leaves the write's mark for the next worker."""

    def setUp(self):
        root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        self.beads = root / "ws" / ".beads"
        dolt = self.beads / "embeddeddolt" / "db" / ".dolt"
        dolt.mkdir(parents=True)
        (self.beads / "metadata.json").write_text(
            json.dumps({"dolt_mode": "embedded", "dolt_database": "db"}))
        (dolt / "repo_state.json").write_text(
            json.dumps({"remotes": {"origin": {"url": _PRIVATE}}}))
        bin_dir = root / "bin"
        bin_dir.mkdir()
        self.bd = bin_dir / "bd"
        self.bd.write_text(_ORPHANING_BD)
        self.bd.chmod(0o755)
        git = bin_dir / "git"
        git.write_text("#!/bin/sh\nexit 1\n")
        git.chmod(0o755)
        self.push_log = root / "pushes"
        self.environ = {"PATH": str(bin_dir), "PUSH_LOG": str(self.push_log),
                        "SLEEPER_SECONDS": "0",
                        "XDG_STATE_HOME": str(root / "xdg")}
        self.state = bdw_push.state_dir(self.beads, self.environ)
        self.state.mkdir(parents=True)

    def test_a_worker_killed_while_waiting_leaves_the_mark(self):
        (self.state / "pending").touch()  # a write
        with open(self.state / "inflight", "a") as orphan:
            fcntl.flock(orphan, fcntl.LOCK_EX)  # an earlier push's orphan
            worker = subprocess.Popen(
                ["/usr/bin/python3", bdw_push.__file__, str(self.beads),
                 str(self.bd)], env=self.environ)
            time.sleep(1)  # the worker is polling the held lock
            worker.kill()
            worker.wait()
        self.assertTrue((self.state / "pending").exists())
        self.assertFalse(self.push_log.exists())
        # The next bdw call of any kind, a read included, starts a worker
        # that pushes the kept write.
        self.assertIsNone(self.next_call())
        self.assertEqual(self.pushes(), 1)
        self.assertNoMarkers()

    def test_a_worker_killed_mid_push_is_pushed_again_on_the_next_call(self):
        self.bd.write_text(_FAILS_FIRST_BD)
        (self.state / "pending").touch()  # a write
        worker = subprocess.Popen(
            ["/usr/bin/python3", bdw_push.__file__, str(self.beads),
             str(self.bd)], env=self.environ)
        deadline = time.monotonic() + 10
        while self.pushes() < 1 and time.monotonic() < deadline:
            time.sleep(0.05)  # until bd's push is under way
        self.assertTrue((self.state / "pushing").exists())
        worker.kill()
        worker.wait()
        # The orphaned push goes on and fails (exit 7), and nothing records
        # that; but the write's `pushing` marker survives, so the next call
        # waits for the orphan, then pushes again and records the outcome.
        self.assertTrue((self.state / "pushing").exists())
        self.assertIsNone(self.next_call())
        self.assertEqual(self.pushes(), 2)
        self.assertIsNone(bdw_push.last_failure(self.state))
        self.assertNoMarkers()

    def next_call(self):
        """What bdw does on a call that leaves no write, with the worker
        run to completion in the foreground."""
        return bdw_push.resume_push(
            self.beads, str(self.bd), self.environ,
            spawn=lambda argv, environ: subprocess.run(
                list(argv), env=dict(environ), timeout=60))

    def pushes(self):
        if not self.push_log.exists():
            return 0
        return len(self.push_log.read_text().splitlines())

    def assertNoMarkers(self):
        self.assertFalse((self.state / "pending").exists())
        self.assertFalse((self.state / "pushing").exists())


# A bd stand-in whose first push hangs for 2 s and fails (exit 7), and
# whose later pushes succeed at once.
_FAILS_FIRST_BD = """#!/bin/sh
case "$1 $2" in
"config get") echo false; exit 0 ;;
"dolt push")
    echo push >> "$PUSH_LOG"
    n=$(/usr/bin/wc -l < "$PUSH_LOG")
    if [ "$n" -eq 1 ]; then /bin/sleep 2; exit 7; fi
    exit 0 ;;
esac
exit 0
"""


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

    def test_a_detached_descendant_holding_output_does_not_stretch_a_timeout(
            self):
        # sh blocks; its child calls setsid (escaping the group kill) and
        # keeps sh's stdout and stderr open for 8 s.
        script = ("/usr/bin/python3 -c 'import os, time; os.setsid(); "
                  "time.sleep(8)' & /bin/sleep 100")
        started = time.monotonic()
        code, _, _ = bdw_push.run_command(
            ["/bin/sh", "-c", script], {"PATH": "/bin"}, self.root,
            timeout=1)
        self.assertEqual(code, 124)
        self.assertLess(time.monotonic() - started, 4)

    def test_a_finished_command_is_not_held_by_its_detached_descendant(self):
        script = ("/usr/bin/python3 -c 'import os, time; os.setsid(); "
                  "time.sleep(8)' & echo done; exit 3")
        started = time.monotonic()
        code, out, _ = bdw_push.run_command(
            ["/bin/sh", "-c", script], {"PATH": "/bin"}, self.root,
            timeout=6)
        self.assertEqual((code, out), (3, "done\n"))
        self.assertLess(time.monotonic() - started, 4)

    def test_a_timeout_keeps_what_the_command_said_first(self):
        code, _, err = bdw_push.run_command(
            ["/bin/sh", "-c", "echo 'Host key verification pending' >&2; "
             "/bin/sleep 30"], {"PATH": "/bin"}, self.root, timeout=1)
        self.assertEqual(code, 124)
        self.assertTrue(err.startswith("timed out after 1s\n"), err)
        self.assertIn("Host key verification pending", err)

    def test_only_the_tail_of_the_output_is_read(self):
        script = ("/usr/bin/python3 -c \"import sys; "
                  "sys.stderr.write('x' * 50000 + 'END')\"")
        code, _, err = bdw_push.run_command(
            ["/bin/sh", "-c", script], {"PATH": "/bin"}, self.root)
        self.assertEqual(code, 0)
        self.assertEqual(len(err), bdw_push.STDERR_TAIL)
        self.assertTrue(err.endswith("END"))

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

    def test_leaves_pending_and_spawns_the_system_interpreter(self):
        spawned = []
        self.assertIsNone(bdw_push.request_push(
            self.beads, "/bin/bd", self.environ,
            spawn=lambda argv, environ: spawned.append(list(argv))))
        state = self.state()
        self.assertTrue((state / "pending").exists())
        self.assertTrue(str(state).startswith(
            str(self.root / "s" / "agent-tooling" / "bdw" / "push")))
        (argv,) = spawned
        self.assertEqual(argv[0], "/usr/bin/python3")
        self.assertTrue(argv[1].endswith("bdw_push.py"))
        self.assertEqual(argv[2:], [str(self.beads), "/bin/bd"])

    def test_the_state_directory_is_private(self):
        bdw_push.request_push(self.beads, "bd", self.environ,
                              spawn=lambda *_: None)
        self.assertEqual(self.state().stat().st_mode & 0o777, 0o700)

    def test_an_existing_state_directory_keeps_its_mode(self):
        # ADR 0015 (three places for machine-specific files): tightening a
        # directory that already exists is the user's call.
        self.state().mkdir(parents=True)
        os.chmod(self.state(), 0o755)
        bdw_push.request_push(self.beads, "bd", self.environ,
                              spawn=lambda *_: None)
        self.assertEqual(self.state().stat().st_mode & 0o777, 0o755)

    def test_a_lock_error_is_reported_as_one(self):
        def no_locks(*_):
            raise OSError(errno.ENOLCK, "No locks available")

        with mock.patch.object(bdw_push.fcntl, "flock", no_locks):
            problem = bdw_push.request_push(self.beads, "bd", self.environ,
                                            spawn=lambda *_: None)
        self.assertIn("cannot lock", problem)
        self.assertIn("No locks available", problem)
        self.assertNotIn("not writable", problem)

    def test_resume_starts_a_worker_only_when_a_push_is_owed(self):
        spawned = []

        def spawn(argv, environ):
            spawned.append(argv)

        # No state at all: nothing owed, nothing created.
        self.assertIsNone(bdw_push.resume_push(self.beads, "bd", self.environ,
                                               spawn=spawn))
        self.assertFalse((self.root / "s").exists())
        state = self.state()
        state.mkdir(parents=True)
        self.assertIsNone(bdw_push.resume_push(self.beads, "bd", self.environ,
                                               spawn=spawn))
        self.assertEqual(spawned, [])
        for marker in ("pending", "pushing"):
            with self.subTest(marker=marker):
                spawned.clear()
                (state / marker).touch()
                bdw_push.resume_push(self.beads, "bd", self.environ,
                                     spawn=spawn)
                self.assertEqual(len(spawned), 1)
                # A running worker (the lock held) means no second one.
                spawned.clear()
                with open(state / "lock", "a") as handle:
                    fcntl.flock(handle, fcntl.LOCK_EX)
                    bdw_push.resume_push(self.beads, "bd", self.environ,
                                         spawn=spawn)
                self.assertEqual(spawned, [])
                os.unlink(state / marker)

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
        self.assertTrue((state / "pending").exists())

    def test_home_fallback_and_no_state_dir(self):
        state = bdw_push.state_dir(self.beads, {"HOME": "/h"})
        self.assertEqual(state.parent,
                         Path("/h/.local/state/agent-tooling/bdw/push"))
        self.assertIsNone(bdw_push.state_dir(
            self.beads, {"XDG_STATE_HOME": "relative", "HOME": "relative"}))
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
        for value in ("1", "t", "T", "true", "True", "TRUE", " yes\n", "on"):
            self.assertTrue(bdw_push.is_truthy(value), value)
        for value in (None, "", "0", "f", "false", "no", "off", "2"):
            self.assertFalse(bdw_push.is_truthy(value), value)


if __name__ == "__main__":
    unittest.main()
