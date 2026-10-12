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
CLAUDE_SESSION_ID, then its arguments one per line, writes FAKE_BD_STDERR
to stderr, and exits FAKE_BD_EXIT.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

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
printf '%s\\n' "BD_ACTOR=${BD_ACTOR-<unset>}"
printf '%s\\n' "BEADS_ACTOR=${BEADS_ACTOR-<unset>}"
printf '%s\\n' "CLAUDE_SESSION_ID=${CLAUDE_SESSION_ID-<unset>}"
for argument in "$@"; do
    printf '%s\\n' "$argument"
done
if [ -n "${FAKE_BD_STDERR-}" ]; then
    printf '%s\\n' "$FAKE_BD_STDERR" >&2
fi
exit "${FAKE_BD_EXIT:-0}"
"""

_HEADER_LINES = 3
_SESSION = "ae218998-349e-47c7-a5c8-8073c15ef975"


class BdwTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp, ignore_errors=True)
        root = Path(temp).resolve()
        self.bin = root / "bin"
        self.bin.mkdir()
        self.beads = root / "ws" / ".beads"
        self.beads.mkdir(parents=True)
        (self.beads / "metadata.json").write_text("{}\n")
        self.log = root / "bd.log"

    def install_fake_bd(self) -> None:
        fake = self.bin / "bd"
        fake.write_text(_FAKE_BD)
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def run_bdw(self, *arguments: str, **environment: str) -> subprocess.CompletedProcess:
        env = {
            "PATH": str(self.bin),
            "FAKE_BEADS_DIR": str(self.beads),
            "FAKE_BD_VERSION": "1.3.0",
            "FAKE_BD_LOG": str(self.log),
            **environment,
        }
        env = {name: value for name, value in env.items() if value is not None}
        return subprocess.run(
            [str(_SCRIPT), *arguments],
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def bd_calls(self) -> list:
        if not self.log.exists():
            return []
        return self.log.read_text().splitlines()

    def assert_refused(self, result, message_part: str) -> None:
        self.assertEqual(result.returncode, 4, result.stderr)
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
        self.assert_refused(result, "no Beads workspace config found")
        self.assertIn("No active beads workspace found.", result.stderr)
        self.assertEqual(self.bd_calls(), ["where --json"])

    def test_missing_metadata_json_is_refused(self):
        self.install_fake_bd()
        (self.beads / "metadata.json").unlink()
        result = self.run_bdw("list", USER="dan")
        self.assert_refused(result, "has no metadata.json")
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
                    "verified (verified: 1.3.0)")
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

    def test_unreadable_version_counts_as_unverified(self):
        self.install_fake_bd()
        # Without FAKE_BD_VERSION the fake answers `version --json` with
        # its ordinary non-JSON output.
        result = self.run_bdw("create", "x", USER="dan", FAKE_BD_VERSION=None)
        self.assert_refused(result, "bd version unknown is not verified")

    def test_verified_version_runs_writes_silently(self):
        self.install_fake_bd()
        result = self.run_bdw("create", "x", USER="dan")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
