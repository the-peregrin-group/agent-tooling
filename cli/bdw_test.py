"""Tests for the bdw executable (the Beads wrapper).

Each test builds a throwaway directory holding a fake `bd` shell script and
a fake Beads workspace (`ws/.beads/metadata.json`), and runs the real
`cli/bdw` as a subprocess with a fully controlled environment whose PATH is
only that directory -- so no test depends on, or reaches, a real `bd` or
the developer's environment. bdw's shebang pins /usr/bin/python3 and the
fake bd's pins /bin/sh, both by absolute path, so PATH needs nothing else.

The fake bd answers bdw's two probes (`where --json` from FAKE_BEADS_DIR,
`version --json` from FAKE_BD_VERSION), logs every invocation to
FAKE_BD_LOG, and otherwise prints BD_ACTOR, BEADS_ACTOR, and
CLAUDE_SESSION_ID, then its arguments one per line, then its stdin when
FAKE_BD_ECHO_STDIN is set, sleeps FAKE_BD_SLEEP seconds when it is set,
writes FAKE_BD_STDERR to stderr, and exits FAKE_BD_EXIT, or kills itself
with signal FAKE_BD_SELF_SIGNAL.

The tests of live relaying and signal forwarding use a second fake,
_SLOW_BD, which reports on stderr that it is running and then waits.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import fcntl
import importlib.machinery
import importlib.util
import io
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import bdw_push  # noqa: E402

_SCRIPT = Path(__file__).resolve().parent / "bdw"

_HELP_LINE = "Agents, load /use-bd immediately."

_FAKE_BD = """#!/bin/sh
printf '%s\\n' "$*" >> "${FAKE_BD_LOG:-/dev/null}"
if [ "$1" = where ] && [ "$2" = --json ] && [ "$#" -eq 2 ]; then
    if [ -n "${FAKE_BEADS_DIR-}" ]; then
        printf '{"path": "%s", "schema_version": 1}\\n' "$FAKE_BEADS_DIR"
        exit 0
    fi
    printf '%s\\n' '{"error": "no_beads_directory", "message": "No active beads workspace found."}'
    exit 1
fi
if [ "$1" = version ] && [ "$2" = --json ] && [ "$#" -eq 2 ] \\
        && [ -n "${FAKE_BD_VERSION-}" ]; then
    printf '{"version": "%s"}\\n' "$FAKE_BD_VERSION"
    exit 0
fi
if [ "$1" = dolt ] && [ "$2" = push ]; then
    printf '%s\\n' "BD_NO_REMOTE_ADOPT=${BD_NO_REMOTE_ADOPT-<unset>}" \\
        >> "${FAKE_BD_LOG:-/dev/null}"
    exit "${FAKE_BD_PUSH_EXIT:-0}"
fi
printf '%s\\n' "BD_ACTOR=${BD_ACTOR-<unset>}"
printf '%s\\n' "BEADS_ACTOR=${BEADS_ACTOR-<unset>}"
printf '%s\\n' "CLAUDE_SESSION_ID=${CLAUDE_SESSION_ID-<unset>}"
for argument in "$@"; do
    printf '%s\\n' "$argument"
done
if [ -n "${FAKE_BD_ECHO_STDIN-}" ]; then
    /bin/cat
fi
if [ -n "${FAKE_BD_SLEEP-}" ]; then
    /bin/sleep "$FAKE_BD_SLEEP"
fi
if [ -n "${FAKE_BD_STDERR-}" ]; then
    printf '%s\\n' "$FAKE_BD_STDERR" >&2
fi
if [ -n "${FAKE_BD_SELF_SIGNAL-}" ]; then
    kill -"$FAKE_BD_SELF_SIGNAL" $$
fi
exit "${FAKE_BD_EXIT:-0}"
"""

# Answers the probes, then: writes `running` on stderr, records SIGTERM in
# FAKE_BD_TRAP and exits 143 on it, and otherwise exits 0 once
# FAKE_BD_RELEASE exists.
_SLOW_BD = """#!/bin/sh
if [ "$1" = where ]; then
    printf '{"path": "%s"}\\n' "$FAKE_BEADS_DIR"
    exit 0
fi
if [ "$1" = version ]; then
    printf '%s\\n' '{"version": "1.3.0"}'
    exit 0
fi
trap 'echo trapped > "$FAKE_BD_TRAP"; exit 143' TERM
echo running >&2
while [ ! -e "$FAKE_BD_RELEASE" ]; do
    /bin/sleep 0.05
done
echo released >&2
exit 0
"""

_HEADER_LINES = 3
_SESSION = "ae218998-349e-47c7-a5c8-8073c15ef975"
_PRIVATE_REMOTE = "git+ssh://git@forge.example:2299/someone/the-repo-dolt.git"


class BdwTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp, ignore_errors=True)
        root = Path(temp).resolve()
        self.bin = root / "bin"
        self.bin.mkdir()
        self.beads = root / "ws" / ".beads"
        self.beads.mkdir(parents=True)
        # A realistic embedded database with no Dolt remote: every write
        # still starts a push worker, which finds nothing to push to and
        # stays silent, without calling bd.
        (self.beads / "metadata.json").write_text(
            '{"dolt_mode": "embedded", "dolt_database": "db"}\n')
        self.dolt = self.beads / "embeddeddolt" / "db" / ".dolt"
        self.dolt.mkdir(parents=True)
        (self.dolt / "repo_state.json").write_text('{"remotes": {}}\n')
        self.log = root / "bd.log"
        # Every bdw run gets a temporary state root, so no test can reach
        # the real ~/.local/state.
        self.state_home = root / "state"
        # Cleanups run last-registered first: let any detached worker a
        # write started finish before the directory above is removed.
        self.addCleanup(self.settle_workers)

    def settle_workers(self) -> None:
        if (self.state_home / "agent-tooling" / "bdw" / "push").is_dir():
            self.wait_for_worker()

    def install_fake_bd(self, script: str = _FAKE_BD) -> None:
        fake = self.bin / "bd"
        fake.write_text(script)
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def bdw_environment(self, **environment: str) -> dict:
        env = {
            "PATH": str(self.bin),
            "FAKE_BEADS_DIR": str(self.beads),
            "FAKE_BD_VERSION": "1.3.0",
            "FAKE_BD_LOG": str(self.log),
            "XDG_STATE_HOME": str(self.state_home),
            **environment,
        }
        return {name: value for name, value in env.items() if value is not None}

    def run_bdw(self, *arguments: str, stdin_text: str | None = None,
                **environment: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(_SCRIPT), *arguments],
            env=self.bdw_environment(**environment),
            input=stdin_text,
            stdin=subprocess.DEVNULL if stdin_text is None else None,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def start_slow_bdw(self, *arguments: str) -> tuple:
        """Start bdw over _SLOW_BD and wait until bd reports it is
        running; return the bdw process, the trap file, and the release
        file."""
        self.install_fake_bd(_SLOW_BD)
        trap = self.bin.parent / "trap"
        release = self.bin.parent / "release"
        process = subprocess.Popen(
            [str(_SCRIPT), *arguments],
            env=self.bdw_environment(USER="dan", FAKE_BD_TRAP=str(trap),
                                     FAKE_BD_RELEASE=str(release)),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(process.kill)
        self.addCleanup(process.stderr.close)
        self.addCleanup(release.touch)
        # readline blocks until bd's first stderr line has been relayed;
        # the subprocess timeout above does not apply here, so a hang
        # shows up as the suite's own timeout.
        self.assertEqual(process.stderr.readline(), "running\n")
        return process, trap, release

    def bd_calls(self) -> list:
        if not self.log.exists():
            return []
        return self.log.read_text().splitlines()

    def assert_refused(self, result, message_part: str,
                       code: int = 4) -> None:
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertIn(message_part, result.stderr)
        self.assertEqual(result.stderr.splitlines()[-1], _HELP_LINE)
        self.assertEqual(result.stdout, "")

    # Actor and session.

    def test_session_id_actor_and_closing_session_are_exported(self):
        self.install_fake_bd()
        result = self.run_bdw("list", CLAUDE_CODE_SESSION_ID=_SESSION, USER="dan")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines()[:_HEADER_LINES],
            ["BD_ACTOR=claude-session-" + _SESSION,
             "BEADS_ACTOR=claude-session-" + _SESSION,
             "CLAUDE_SESSION_ID=" + _SESSION],
        )

    def test_job_session_keeps_the_job_shape(self):
        self.install_fake_bd()
        result = self.run_bdw(
            "list", CLAUDE_CODE_SESSION_ID=_SESSION,
            CLAUDE_JOB_DIR="/Users/x/.claude/jobs/ae218998", USER="dan",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[0],
                         "BD_ACTOR=claude-job-" + _SESSION)

    def test_job_dir_actor_without_a_session_id(self):
        self.install_fake_bd()
        result = self.run_bdw(
            "list", CLAUDE_JOB_DIR="/Users/x/.claude/jobs/ae218998", USER="dan"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "BD_ACTOR=claude-job-ae218998")
        self.assertEqual(lines[1], "BEADS_ACTOR=claude-job-ae218998")
        self.assertEqual(lines[2], "CLAUDE_SESSION_ID=<unset>")

    def test_attended_fallback_is_exported(self):
        self.install_fake_bd()
        result = self.run_bdw("list", USER="dan")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "BD_ACTOR=attended-dan")
        self.assertEqual(lines[1], "BEADS_ACTOR=attended-dan")

    def test_caller_supplied_identity_is_overridden(self):
        self.install_fake_bd()
        result = self.run_bdw(
            "list", USER="dan", BD_ACTOR="impostor", BEADS_ACTOR="impostor",
            CLAUDE_SESSION_ID="impostor",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("impostor", result.stdout)
        self.assertEqual(
            result.stdout.splitlines()[:_HEADER_LINES],
            ["BD_ACTOR=attended-dan", "BEADS_ACTOR=attended-dan",
             "CLAUDE_SESSION_ID=<unset>"],
        )
        result = self.run_bdw(
            "list", CLAUDE_CODE_SESSION_ID=_SESSION,
            CLAUDE_SESSION_ID="impostor",
        )
        self.assertNotIn("impostor", result.stdout)

    # The child process.

    def test_arguments_pass_through_unchanged(self):
        self.install_fake_bd()
        arguments = ["create", "--title", "two words", "-p", "1",
                     "--", "--not-a-flag", "", "  padded  "]
        result = self.run_bdw(*arguments, USER="dan")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[_HEADER_LINES:], arguments)

    def test_bd_exit_code_and_stderr_are_relayed(self):
        self.install_fake_bd()
        result = self.run_bdw("show", "x-1", USER="dan", FAKE_BD_EXIT="7",
                              FAKE_BD_STDERR="Issue x-1 not found")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stderr, "Issue x-1 not found\n")
        self.assertEqual(result.stdout.splitlines()[_HEADER_LINES:],
                         ["show", "x-1"])

    def test_a_signal_exit_maps_to_128_plus_the_signal(self):
        self.install_fake_bd()
        result = self.run_bdw("show", "x-1", USER="dan",
                              FAKE_BD_SELF_SIGNAL="KILL")
        self.assertEqual(result.returncode, 137, result.stderr)

    def test_bd_exit_code_survives_a_closed_stderr(self):
        # The caller closes its end of bdw's stderr before bd writes to
        # it; bdw must still drain bd and return bd's own exit code, not
        # Python's 120 from a failed flush at exit.
        self.install_fake_bd()
        cases = (
            (("show", "x-1"), "boom", "7", 7),
            (("frobnicate",), "Error: unknown command \"frobnicate\" for \"bd\"",
             "1", 1),
            (("--help",), "", "0", 0),
            (("create", "x"), "", "0", 5),  # refused: unverified version
        )
        for arguments, stderr_line, bd_exit, expected in cases:
            with self.subTest(arguments=arguments):
                process = subprocess.Popen(
                    [str(_SCRIPT), *arguments],
                    env=self.bdw_environment(
                        USER="dan", FAKE_BD_SLEEP="0.5",
                        FAKE_BD_STDERR=stderr_line, FAKE_BD_EXIT=bd_exit,
                        FAKE_BD_VERSION="1.4.0" if expected == 5 else "1.3.0"),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                self.addCleanup(process.kill)
                process.stderr.close()
                self.assertEqual(process.wait(timeout=30), expected)

    def test_stdin_reaches_bd(self):
        self.install_fake_bd()
        result = self.run_bdw("create", "x", USER="dan",
                              FAKE_BD_ECHO_STDIN="1",
                              stdin_text="line one\nline two\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[_HEADER_LINES + 2:],
                         ["line one", "line two"])

    def test_stderr_is_relayed_while_bd_runs(self):
        process, _trap, release = self.start_slow_bdw("list")
        # bd is still waiting for the release file, so `running` reached
        # us before bd exited.
        self.assertIsNone(process.poll())
        release.touch()
        self.assertEqual(process.stderr.read(), "released\n")
        self.assertEqual(process.wait(timeout=30), 0)

    def test_sigterm_to_bdw_is_forwarded_to_bd(self):
        process, trap, _release = self.start_slow_bdw("list")
        process.send_signal(signal.SIGTERM)
        self.assertEqual(process.wait(timeout=30), 143)
        self.assertEqual(trap.read_text(), "trapped\n")

    def test_bdw_returns_after_bd_and_probes_run_first(self):
        self.install_fake_bd()
        result = self.run_bdw("list", USER="dan")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.bd_calls(),
                         ["where --json", "version --json", "list"])

    def test_missing_bd_exits_3_with_the_not_found_line(self):
        result = self.run_bdw("list", USER="dan")
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stderr.splitlines(),
                         ["bdw: bd not found on PATH", _HELP_LINE])
        self.assertEqual(result.stdout, "")

    def test_start_failure_exits_1(self):
        broken = self.bin / "bd"
        broken.write_text("#!/nonexistent/interp\n")
        broken.chmod(0o755)
        result = self.run_bdw("version", USER="dan")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot run", result.stderr)

    def test_a_bd_that_is_this_script_is_treated_as_absent(self):
        os.symlink(str(_SCRIPT), str(self.bin / "bd"))
        result = self.run_bdw("list", USER="dan")
        self.assertEqual(result.returncode, 3)
        self.assertIn("bd not found on PATH", result.stderr)

    # The help line.

    def test_help_calls_print_the_help_line_and_skip_the_probes(self):
        self.install_fake_bd()
        for arguments in ((), ("help",), ("help", "close"), ("--help",),
                          ("-h",)):
            with self.subTest(arguments=arguments):
                self.log.write_text("")
                result = self.run_bdw(*arguments, USER="dan",
                                      FAKE_BEADS_DIR=None)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, _HELP_LINE + "\n")
                self.assertEqual(result.stdout.splitlines()[_HEADER_LINES:],
                                 list(arguments))
                self.assertEqual(self.bd_calls(), [" ".join(arguments)])

    def test_help_flag_after_the_verb_prints_the_help_line(self):
        self.install_fake_bd()
        result = self.run_bdw("show", "--help", USER="dan")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, _HELP_LINE + "\n")
        result = self.run_bdw("create", "--", "--help", USER="dan")
        self.assertEqual(result.stderr, "")

    def test_bd_usage_errors_get_the_help_line(self):
        self.install_fake_bd()
        for message in ('Error: unknown command "lsit" for "bd"',
                        "Error: unknown flag: --bogus",
                        "Error: unknown shorthand flag: 'Z' in -Z",
                        "Run 'bd --help' for usage."):
            with self.subTest(message=message):
                result = self.run_bdw("show", "x", USER="dan",
                                      FAKE_BD_EXIT="1", FAKE_BD_STDERR=message)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stderr.splitlines(),
                                 [message, _HELP_LINE])

    def test_other_bd_failures_do_not_get_the_help_line(self):
        self.install_fake_bd()
        result = self.run_bdw("show", "x", USER="dan", FAKE_BD_EXIT="1",
                              FAKE_BD_STDERR="Issue x not found")
        self.assertNotIn(_HELP_LINE, result.stderr)

    # Argument refusals.

    def test_actor_flag_is_refused_in_any_position(self):
        self.install_fake_bd()
        for arguments in (
            ("--actor", "impostor", "create", "x"),
            ("--actor=impostor", "create", "x"),
            ("create", "x", "--actor", "impostor"),
            ("create", "--", "--actor=impostor"),
            ("create", "--", "--actor", "impostor"),
        ):
            with self.subTest(arguments=arguments):
                result = self.run_bdw(*arguments, USER="dan")
                self.assert_refused(
                    result,
                    "bdw: refusing --actor: the actor comes from the "
                    "session environment",
                )
                self.assertEqual(self.bd_calls(), [])  # bd never ran

    def test_database_flags_are_refused_in_any_position(self):
        self.install_fake_bd()
        for arguments in (
            ("list", "-C", "/elsewhere"),
            ("list", "-C/elsewhere"),
            ("list", "-qC", "/elsewhere"),
            ("list", "--directory", "/elsewhere"),
            ("list", "--directory=/elsewhere"),
            ("list", "--db", "x.db"),
            ("list", "--db=x.db"),
            ("list", "--database", "other"),
            ("list", "--database=other"),
            ("list", "--global"),
            ("list", "--global=true"),
            ("create", "x", "--", "--db=x.db"),
            ("create", "x", "--", "-C", "/elsewhere"),
        ):
            with self.subTest(arguments=arguments):
                result = self.run_bdw(*arguments, USER="dan")
                self.assert_refused(result, "workspace's own database")
                self.assertEqual(self.bd_calls(), [])

    def test_flag_first_is_refused_except_help_and_version(self):
        self.install_fake_bd()
        for arguments in (("--json", "ready"), ("-q", "list"),
                          ("--readonly", "list"), ("-", "list")):
            with self.subTest(arguments=arguments):
                result = self.run_bdw(*arguments, USER="dan")
                self.assert_refused(result, "put the verb first")
                self.assertEqual(self.bd_calls(), [])
        for arguments in (("--help",), ("-h",), ("--version",), ("-V",),
                          ("version",)):
            with self.subTest(arguments=arguments):
                result = self.run_bdw(*arguments, USER="dan")
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_look_alike_arguments_still_pass_through(self):
        self.install_fake_bd()
        arguments = ["create", "--actors", "--title", "--actor is a flag",
                     "x--actor=y", "--dbx", "--globally", "x-C"]
        result = self.run_bdw(*arguments, USER="dan")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[_HEADER_LINES:], arguments)

    # Workspace config.

    def test_no_workspace_is_refused(self):
        self.install_fake_bd()
        result = self.run_bdw("list", USER="dan", FAKE_BEADS_DIR=None)
        self.assert_refused(result, "no Beads workspace config found", 5)
        self.assertIn("No active beads workspace found.", result.stderr)
        self.assertEqual(self.bd_calls(), ["where --json"])

    def test_missing_metadata_json_is_refused(self):
        self.install_fake_bd()
        (self.beads / "metadata.json").unlink()
        result = self.run_bdw("list", USER="dan")
        self.assert_refused(result, "has no metadata.json", 5)
        self.assertEqual(self.bd_calls(), ["where --json"])

    def test_version_runs_without_a_workspace(self):
        self.install_fake_bd()
        result = self.run_bdw("version", USER="dan", FAKE_BEADS_DIR=None)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.bd_calls(), ["version"])

    # Verified versions.

    def test_unverified_version_refuses_writes(self):
        self.install_fake_bd()
        for arguments in (("create", "x"), ("close", "x-1"),
                          ("update", "x-1", "--claim"), ("ready", "--claim"),
                          ("dep", "add", "a", "b"), ("dep",)):
            with self.subTest(arguments=arguments):
                self.log.write_text("")
                result = self.run_bdw(*arguments, USER="dan",
                                      FAKE_BD_VERSION="1.4.0")
                self.assert_refused(
                    result, "refusing a write: bd version 1.4.0 is not "
                    "verified (verified: 1.3.0)", 5)
                self.assertEqual(self.bd_calls(),
                                 ["where --json", "version --json"])

    def test_unverified_version_warns_on_reads(self):
        self.install_fake_bd()
        for arguments in (("list",), ("show", "x-1"), ("ready", "--json"),
                          ("dep", "list", "x-1"), ("label", "list-all")):
            with self.subTest(arguments=arguments):
                result = self.run_bdw(*arguments, USER="dan",
                                      FAKE_BD_VERSION="1.4.0")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    result.stderr,
                    "bdw: warning: bd version 1.4.0 is not verified "
                    "(verified: 1.3.0); reading anyway\n",
                )
                self.assertEqual(result.stdout.splitlines()[_HEADER_LINES:],
                                 list(arguments))

    def test_read_and_write_classification_on_an_unverified_version(self):
        self.install_fake_bd()
        reads = (
            ("blocked",), ("children", "x-1"), ("list", "--all"),
            ("list", "--desc-contains=words", "--all"),
            ("list", "--desc-contains", "words", "--limit", "5"),
            ("prime",), ("ready",), ("ready", "--json"), ("search", "words"),
            ("show", "x-1", "--children"), ("types",), ("where",),
            ("config", "get", "k"), ("config", "list"), ("dep", "tree", "x"),
            ("epic", "status", "--eligible-only"), ("gate", "list"),
            ("gate", "show", "g"), ("human", "list"), ("label", "list", "x"),
            ("label", "list-all"),
        )
        writes = (
            ("ready", "--claim"), ("ready", "--claim=true"),
            ("ready", "--json", "--claim=x"), ("list", "--fix"),
            ("lint", "--fix"), ("find-duplicates", "--merge"),
            ("show", "x-1", "-q"), ("list", "--", "--claim"),
            ("config", "set", "k", "v"), ("config",),
            ("label", "add", "x", "l"), ("gate", "resolve", "g"),
            ("gate", "create"), ("epic", "close-eligible"), ("dep", "add"),
            ("human", "respond", "x"), ("close", "x-1"), ("update", "x-1"),
            ("note", "x-1"), ("unknown-verb",),
        )
        for arguments in reads:
            with self.subTest(read=arguments):
                result = self.run_bdw(*arguments, USER="dan",
                                      FAKE_BD_VERSION="1.4.0")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("reading anyway", result.stderr)
        for arguments in writes:
            with self.subTest(write=arguments):
                result = self.run_bdw(*arguments, USER="dan",
                                      FAKE_BD_VERSION="1.4.0")
                self.assert_refused(result, "refusing a write", 5)

    def test_unreadable_version_counts_as_unverified(self):
        self.install_fake_bd()
        # Without FAKE_BD_VERSION the fake answers `version --json` with
        # its ordinary non-JSON output.
        result = self.run_bdw("create", "x", USER="dan", FAKE_BD_VERSION=None)
        self.assert_refused(result, "bd version unknown is not verified",
                            5)

    def test_verified_version_runs_writes_silently(self):
        self.install_fake_bd()
        result = self.run_bdw("create", "x", USER="dan")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    # The push to the Dolt remote after writes.

    def setup_push(self, dolt_url: str = _PRIVATE_REMOTE) -> dict:
        """A fake Dolt remote, a fake git with a public origin, and a
        state directory; return the environment that enables the push."""
        self.install_fake_bd()
        (self.dolt / "repo_state.json").write_text(
            '{"remotes": {"origin": {"name": "origin", "url": "%s"}}}\n'
            % dolt_url)
        fake_git = self.bin / "git"
        fake_git.write_text(
            "#!/bin/sh\nprintf 'remote.origin.url %s\\n' "
            "'git@github.com:the-org/the-repo.git'\n")
        fake_git.chmod(0o755)
        return {"USER": "dan"}

    def state(self) -> Path:
        (state,) = (self.state_home / "agent-tooling" / "bdw" / "push").iterdir()
        return state

    def wait_for_worker(self) -> None:
        """Wait until the detached worker has released its state: the dirty
        mark gone and the lock free."""
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            state_root = self.state_home / "agent-tooling" / "bdw" / "push"
            states = list(state_root.iterdir()) if state_root.exists() else []
            if states and not (states[0] / "dirty").exists():
                with open(states[0] / "lock", "a") as handle:
                    try:
                        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        return
                    except OSError:
                        pass
            time.sleep(0.05)
        self.fail("the push worker did not finish")

    def pushes(self) -> list:
        return [call for call in self.bd_calls()
                if call.startswith("dolt push")]

    def test_a_write_pushes_in_the_background_without_adoption(self):
        environment = self.setup_push()
        result = self.run_bdw("create", "x", **environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.wait_for_worker()
        self.assertEqual(self.pushes(), ["dolt push --no-adopt"])
        self.assertIn("BD_NO_REMOTE_ADOPT=1", self.bd_calls())
        self.assertIn("pushed", (self.state() / "push.log").read_text())

    def test_reads_failures_and_opt_outs_do_not_push(self):
        environment = self.setup_push()
        cases = (
            (("show", "x-1"), {}),
            (("list", "--status=open"), {}),
            (("dolt", "push"), {}),
            (("create", "x"), {"FAKE_BD_EXIT": "1"}),
            (("create", "x"), {"BD_NO_PUSH": "1"}),
            (("create", "x"), {"BD_NO_PUSH": "yes"}),
            (("help",), {}),
        )
        for arguments, extra in cases:
            with self.subTest(arguments=arguments, extra=extra):
                self.run_bdw(*arguments, **environment, **extra)
                self.assertFalse(
                    (self.state_home / "agent-tooling").exists())
        self.assertEqual([c for c in self.bd_calls()
                          if c == "dolt push --no-adopt"], [])

    def test_a_dolt_remote_on_the_git_origin_is_refused_and_warned(self):
        environment = self.setup_push(
            "git+ssh://git@github.com/the-org/the-repo.git")
        self.assertEqual(self.run_bdw("create", "x", **environment)
                         .returncode, 0)
        self.wait_for_worker()
        self.assertEqual(self.pushes(), [])
        result = self.run_bdw("show", "x-1", **environment)
        self.assertEqual(result.returncode, 0)
        (warning,) = result.stderr.splitlines()
        self.assertTrue(warning.startswith(
            "bdw: warning: the last push of this Beads database to its Dolt "
            "remote failed ("), warning)
        self.assertIn("same repository", warning)
        self.assertNotIn("github", warning)

    def test_a_failed_push_warns_until_one_succeeds(self):
        environment = self.setup_push()
        self.run_bdw("create", "x", FAKE_BD_PUSH_EXIT="1", **environment)
        self.wait_for_worker()
        warned = self.run_bdw("show", "x-1", **environment)
        self.assertIn("bd dolt push exited 1", warned.stderr)
        self.assertEqual(warned.returncode, 0)
        self.run_bdw("create", "y", **environment)
        self.wait_for_worker()
        self.assertEqual(self.run_bdw("show", "x-1", **environment).stderr,
                         "")

    def test_a_workspace_without_a_dolt_remote_pushes_nothing(self):
        self.install_fake_bd()
        result = self.run_bdw("create", "x", USER="dan")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.wait_for_worker()
        self.assertEqual(self.pushes(), [])
        self.assertIsNone(bdw_push.last_failure(self.state()))

    def test_stdout_is_byte_identical_with_a_push_requested(self):
        environment = self.setup_push()
        pushed = subprocess.run(
            [str(_SCRIPT), "create", "x", "--json"],
            env=self.bdw_environment(**environment),
            stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
        self.wait_for_worker()
        self.assertEqual(self.pushes(), ["dolt push --no-adopt"])
        unpushed = subprocess.run(
            [str(_SCRIPT), "create", "x", "--json"],
            env=self.bdw_environment(BD_NO_PUSH="1", **environment),
            stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
        self.assertEqual(pushed.returncode, 0, pushed.stderr)
        self.assertEqual(pushed.stdout, unpushed.stdout)
        self.assertEqual(pushed.stderr, b"")

    def test_an_opted_out_call_does_not_repeat_an_old_warning(self):
        environment = self.setup_push()
        self.run_bdw("create", "x", FAKE_BD_PUSH_EXIT="1", **environment)
        self.wait_for_worker()
        self.assertIn("bd dolt push exited 1",
                      self.run_bdw("show", "x-1", **environment).stderr)
        for value in ("1", "yes"):
            with self.subTest(BD_NO_PUSH=value):
                result = self.run_bdw("show", "x-1", BD_NO_PUSH=value,
                                      **environment)
                self.assertEqual(result.stderr, "")
                self.assertEqual(result.returncode, 0)

    def test_an_unwritable_state_directory_is_warned_about(self):
        environment = self.setup_push()
        self.state_home.write_text("a file where the state root should be")
        result = self.run_bdw("create", "x", **environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        (warning,) = result.stderr.splitlines()
        self.assertTrue(warning.startswith(
            "bdw: warning: cannot request a push:"), warning)
        self.assertIn("not pushed to the Dolt remote", warning)

    def test_an_exception_in_the_push_setup_never_changes_the_exit(self):
        loader = importlib.machinery.SourceFileLoader("bdw_under_test",
                                                      str(_SCRIPT))
        spec = importlib.util.spec_from_file_location(
            loader.name, str(_SCRIPT), loader=loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        stderr = io.StringIO()

        def explode(*_):
            raise RuntimeError("boom")

        with mock.patch.object(module.bdw_push, "request_push", explode), \
                contextlib.redirect_stderr(stderr):
            module._after_call(self.beads, "bd", ["create", "x"], 0, False,
                               {"XDG_STATE_HOME": str(self.state_home)})
        self.assertEqual(
            stderr.getvalue(),
            "bdw: warning: the push step failed: boom\n")


if __name__ == "__main__":
    unittest.main()
