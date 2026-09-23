"""Tests for lib.git.policy: the local-only sweep patterns.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import unittest

from lib.git import policy


class LocalOnlyTest(unittest.TestCase):
    def test_matches_the_patterns_in_any_directory(self):
        for path in (
            "settings.local.json",
            ".claude/settings.local.json",
            ".env",
            ".env.local",
            "deploy/.env.production",
        ):
            with self.subTest(path=path):
                self.assertTrue(policy.is_local_only(path))

    def test_matches_every_path_component_not_just_the_basename(self):
        # A directory named like a pattern hides its contents just as
        # effectively as the file itself.
        for path in (".env/creds.json", "conf/.env/deep/nested.txt"):
            with self.subTest(path=path):
                self.assertTrue(policy.is_local_only(path))

    def test_matches_case_folded(self):
        # The default APFS volume is case-insensitive: `.ENV` is `.env`.
        for path in (".ENV", ".Env.local", "Settings.Local.JSON"):
            with self.subTest(path=path):
                self.assertTrue(policy.is_local_only(path))

    def test_leaves_lookalikes_alone(self):
        for path in (
            "env",
            "settings.json",
            "my.env",
            "x.settings.local.json",
            "environment.md",
            "envelope/.gitkeep",
        ):
            with self.subTest(path=path):
                self.assertFalse(policy.is_local_only(path))

    def test_env_example_is_the_one_sanctioned_exception(self):
        # Exactly .env.example (case-folded, any
        # directory); .env.sample and .env.template deliberately still
        # refuse -- broadening is a design act.
        for path in (".env.example", "docs/.env.example", ".ENV.EXAMPLE"):
            with self.subTest(path=path):
                self.assertFalse(policy.is_local_only(path))
        for path in (".env.sample", ".env.template", "conf/.env.sample"):
            with self.subTest(path=path):
                self.assertTrue(policy.is_local_only(path))

    def test_a_directory_named_env_example_is_not_exempt(self):
        # The exemption is for the bootstrap-guide FILE: a directory of
        # that name would smuggle its whole subtree past the guard.
        for path in (".env.example/creds.json", "a/.env.example/deep.txt"):
            with self.subTest(path=path):
                self.assertTrue(policy.is_local_only(path))

    def test_local_only_matches_pair_paths_with_their_pattern(self):
        self.assertEqual(
            policy.local_only_matches(
                [".env", "work.txt", ".env", "a/settings.local.json"]
            ),
            [(".env", ".env*"), ("a/settings.local.json", "settings.local.json")],
        )

    def test_refusal_message_explains_itself(self):
        message = policy.refusal_message(
            [(".env.local", ".env*")], "Gitignore them."
        )
        self.assertIn(".env.local (matches .env*)", message)
        self.assertIn("never enter history", message)
        self.assertIn(".env.example", message)
        self.assertIn("sanctioned committable exception", message)
        self.assertIn("Gitignore them.", message)
        self.assertIn("user's call", message)


if __name__ == "__main__":
    unittest.main()
