"""Tests for the bdw executable (the Beads shim).

Each test builds a throwaway directory holding a fake `bd` shell script that
prints BD_ACTOR, BEADS_ACTOR, and then its arguments one per line, and runs
the real `cli/bdw` as a subprocess with a fully controlled environment whose
PATH is only that directory -- so no test depends on, or reaches, a real
`bd` or the developer's environment. The shim's shebang pins
/usr/bin/python3 by absolute path, so PATH needs nothing else.

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

_FAKE_BD = """#!/bin/sh
printf '%s\\n' "BD_ACTOR=${BD_ACTOR-<unset>}"
printf '%s\\n' "BEADS_ACTOR=${BEADS_ACTOR-<unset>}"
for argument in "$@"; do
    printf '%s\\n' "$argument"
done
exit "${FAKE_BD_EXIT:-0}"
"""


class BdwTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp, ignore_errors=True)
        self.bin = Path(temp).resolve() / "bin"
        self.bin.mkdir()

    def install_fake_bd(self) -> None:
        fake = self.bin / "bd"
        fake.write_text(_FAKE_BD)
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def run_bdw(self, *arguments: str, **environment: str) -> subprocess.CompletedProcess:
        env = {"PATH": str(self.bin), **environment}
        return subprocess.run(
            [str(_SCRIPT), *arguments],
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_job_dir_actor_is_exported_to_both_variables(self):
        self.install_fake_bd()
        result = self.run_bdw(
            "list", CLAUDE_JOB_DIR="/Users/x/.claude/jobs/ae218998", USER="dan"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "BD_ACTOR=claude-job-ae218998")
        self.assertEqual(lines[1], "BEADS_ACTOR=claude-job-ae218998")

    def test_attended_fallback_is_exported(self):
        self.install_fake_bd()
        result = self.run_bdw("list", USER="dan")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "BD_ACTOR=attended-dan")
        self.assertEqual(lines[1], "BEADS_ACTOR=attended-dan")

    def test_caller_supplied_actor_is_overridden(self):
        self.install_fake_bd()
        result = self.run_bdw(
            "list", USER="dan", BD_ACTOR="impostor", BEADS_ACTOR="impostor"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("impostor", result.stdout)
        self.assertEqual(
            result.stdout.splitlines()[:2],
            ["BD_ACTOR=attended-dan", "BEADS_ACTOR=attended-dan"],
        )

    def test_arguments_pass_through_untouched(self):
        self.install_fake_bd()
        arguments = ["create", "--title", "two words", "-p", "1",
                     "--", "--not-a-flag", "", "  padded  "]
        result = self.run_bdw(*arguments, USER="dan")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[2:], arguments)

    def test_missing_bd_exits_3_with_the_not_found_line(self):
        result = self.run_bdw("list", USER="dan")
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stderr.strip(), "bdw: bd not found on PATH")
        self.assertEqual(result.stdout, "")

    def test_bd_exit_code_propagates(self):
        self.install_fake_bd()
        result = self.run_bdw("list", USER="dan", FAKE_BD_EXIT="7")
        self.assertEqual(result.returncode, 7)

    def test_a_bd_that_is_this_script_is_treated_as_absent(self):
        os.symlink(str(_SCRIPT), str(self.bin / "bd"))
        result = self.run_bdw("list", USER="dan")
        self.assertEqual(result.returncode, 3)
        self.assertIn("bd not found on PATH", result.stderr)


if __name__ == "__main__":
    unittest.main()
