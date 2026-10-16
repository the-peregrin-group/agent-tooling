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

from lib.actor import derive_actor, session_id


_SESSION = "ae218998-349e-47c7-a5c8-8073c15ef975"


class DeriveActorTest(unittest.TestCase):
    def test_session_id_in_a_job_gives_the_job_shape(self):
        environ = {
            "CLAUDE_CODE_SESSION_ID": _SESSION,
            "CLAUDE_JOB_DIR": "/Users/x/.claude/jobs/ae218998",
            "USER": "someone",
        }
        self.assertEqual(derive_actor(environ), "claude-job-" + _SESSION)

    def test_job_derived_actor_is_a_prefix_of_the_session_derived_one(self):
        job_only = {"CLAUDE_JOB_DIR": "/Users/x/.claude/jobs/ae218998"}
        with_session = {**job_only, "CLAUDE_CODE_SESSION_ID": _SESSION}
        self.assertTrue(
            derive_actor(with_session).startswith(derive_actor(job_only))
        )

    def test_session_id_without_a_job_gives_the_session_shape(self):
        for environ in (
            {"CLAUDE_CODE_SESSION_ID": _SESSION, "USER": "dan"},
            {"CLAUDE_CODE_SESSION_ID": _SESSION, "CLAUDE_JOB_DIR": "",
             "USER": "dan"},
            {"CLAUDE_CODE_SESSION_ID": _SESSION, "CLAUDE_JOB_DIR": "/jobs/a b"},
        ):
            with self.subTest(environ=environ):
                self.assertEqual(
                    derive_actor(environ), "claude-session-" + _SESSION
                )

    def test_unsafe_session_id_falls_through(self):
        for value in ("", "a b", "a$b", "..", ".", "x\n", "a/b"):
            with self.subTest(value=value):
                self.assertEqual(
                    derive_actor({"CLAUDE_CODE_SESSION_ID": value,
                                  "CLAUDE_JOB_DIR": "/jobs/ae218998"}),
                    "claude-job-ae218998",
                )
                self.assertEqual(
                    derive_actor({"CLAUDE_CODE_SESSION_ID": value,
                                  "USER": "dan"}),
                    "attended-dan",
                )

    def test_session_id_is_the_safe_token_or_none(self):
        self.assertEqual(session_id({"CLAUDE_CODE_SESSION_ID": _SESSION}),
                         _SESSION)
        for environ in ({}, {"CLAUDE_CODE_SESSION_ID": ""},
                        {"CLAUDE_CODE_SESSION_ID": "a b"},
                        {"CLAUDE_CODE_SESSION_ID": ".."}):
            with self.subTest(environ=environ):
                self.assertIsNone(session_id(environ))

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
