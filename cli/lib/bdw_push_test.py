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
import shutil
import tempfile
import unittest
from pathlib import Path

from lib import bdw_push

_PUBLIC = "git@github.com:the-org/the-repo.git"
_PRIVATE = "git+ssh://git@forge.example:2222/someone/the-repo-dolt.git"


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

    def test_not_embedded_or_unreadable(self):
        self.write({"dolt_mode": "server", "dolt_database": "db"},
                   {"origin": {"url": _PRIVATE}})
        self.assertIsNone(bdw_push.dolt_remote_urls(self.beads))
        (self.beads / "metadata.json").write_text(json.dumps(
            {"dolt_mode": "embedded", "dolt_database": "missing"}))
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
        return bdw_push.push_once(self.beads, self.state, "/bin/bd",
                                  {"PATH": "/bin"}, runner=runner,
                                  remotes=lambda _: list(urls))

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

    def test_a_held_lock_leaves_the_work_to_its_holder(self):
        (self.state / "dirty").touch()
        with open(self.state / "lock", "a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            self.assertEqual(self.run_worker(lambda: "pushed"), [])
        self.assertTrue((self.state / "dirty").exists())


class RequestPushTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.beads = self.root / ".beads"

    def test_marks_dirty_and_spawns_the_worker(self):
        spawned = []
        state = bdw_push.request_push(
            self.beads, "/bin/bd", {"XDG_STATE_HOME": str(self.root / "s")},
            spawn=lambda argv, environ: spawned.append(list(argv)))
        self.assertTrue((state / "dirty").exists())
        self.assertTrue(str(state).startswith(
            str(self.root / "s" / "agent-tooling" / "bdw-push")))
        (argv,) = spawned
        self.assertTrue(argv[1].endswith("bdw_push.py"))
        self.assertEqual(argv[2:], [str(self.beads), "/bin/bd"])

    def test_home_fallback_and_no_state_dir(self):
        state = bdw_push.state_dir(self.beads, {"HOME": "/h"})
        self.assertEqual(state.parent, Path("/h/.local/state/agent-tooling/"
                                            "bdw-push"))
        self.assertIsNone(bdw_push.request_push(
            self.beads, "bd", {}, spawn=lambda *_: None))

    def test_spawn_failure_is_recorded(self):
        def fail(argv, environ):
            raise OSError("no python")

        state = bdw_push.request_push(
            self.beads, "bd", {"XDG_STATE_HOME": str(self.root / "s")},
            spawn=fail)
        self.assertIn("cannot start", bdw_push.last_failure(state)["reason"])


if __name__ == "__main__":
    unittest.main()
