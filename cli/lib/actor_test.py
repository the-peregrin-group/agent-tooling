"""Unit tests for lib.actor (the session actor derivation).

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

if __package__ in (None, ""):  # direct invocation: python3 lib/actor_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.actor import derive_actor


class DeriveActorTest(unittest.TestCase):
    def test_job_dir_gives_the_job_actor(self):
        environ = {
            "CLAUDE_JOB_DIR": "/Users/x/.claude/jobs/ae218998",
            "USER": "someone",
        }
        self.assertEqual(derive_actor(environ), "claude-job-ae218998")

    def test_trailing_slashes_on_the_job_dir_are_stripped(self):
        for job_dir in ("/Users/x/.claude/jobs/ae218998/",
                        "/Users/x/.claude/jobs/ae218998//"):
            with self.subTest(job_dir=job_dir):
                self.assertEqual(
                    derive_actor({"CLAUDE_JOB_DIR": job_dir}),
                    "claude-job-ae218998",
                )

    def test_job_basename_with_disallowed_characters_falls_through(self):
        for job_dir in ("/jobs/ae 218", "/jobs/ae$218", "/jobs/a:b",
                        "/jobs/..", "/jobs/.", "/", "/x/jobs/ae1\n"):
            with self.subTest(job_dir=job_dir):
                self.assertEqual(
                    derive_actor({"CLAUDE_JOB_DIR": job_dir, "USER": "dan"}),
                    "attended-dan",
                )

    def test_empty_job_dir_falls_through(self):
        self.assertEqual(
            derive_actor({"CLAUDE_JOB_DIR": "", "USER": "dan"}),
            "attended-dan",
        )

    def test_no_job_dir_uses_user(self):
        self.assertEqual(derive_actor({"USER": "dan.o_1-x"}), "attended-dan.o_1-x")

    def test_no_job_dir_and_no_usable_user_is_unknown(self):
        for environ in ({}, {"USER": ""}, {"USER": "bad user"},
                        {"USER": "dan\n"}):
            with self.subTest(environ=environ):
                self.assertEqual(derive_actor(environ), "attended-unknown")

    def test_never_returns_blank(self):
        for environ in ({}, {"CLAUDE_JOB_DIR": ""}, {"CLAUDE_JOB_DIR": "/"},
                        {"USER": ""}, {"CLAUDE_JOB_DIR": "//", "USER": " "}):
            with self.subTest(environ=environ):
                actor = derive_actor(environ)
                self.assertTrue(actor.strip())
                self.assertEqual(actor, actor.strip())


if __name__ == "__main__":
    unittest.main()
