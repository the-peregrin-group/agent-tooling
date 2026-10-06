"""Unit tests for lib.arguments (leaf validators for positional parsing).

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

if __package__ in (None, ""):  # direct invocation: python3 lib/arguments_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import arguments


class BranchMatchesPrefixTest(unittest.TestCase):
    def test_a_real_prefix_needs_a_non_empty_tail(self):
        self.assertTrue(arguments.branch_matches_prefix("fix/topic", "fix/"))
        for branch in ("fix/", "fix", "fixture", "main", ""):
            with self.subTest(branch=branch):
                self.assertFalse(arguments.branch_matches_prefix(branch, "fix/"))

    def test_the_bare_slash_matches_any_non_empty_branch(self):
        # Including the default branch: refusing it is the caller's job.
        for branch in ("foo-bar", "fix/topic", "a/b/c", "main"):
            with self.subTest(branch=branch):
                self.assertTrue(arguments.branch_matches_prefix(branch, "/"))
        self.assertFalse(arguments.branch_matches_prefix("", "/"))


class IsValidRepositoryTest(unittest.TestCase):
    def test_accepts_owner_slash_name(self):
        for repository in ("a/b", "octo-org/widgets", "own-er/na.me",
                           "o/r_1", "o/a..b", "0day/x"):
            with self.subTest(repository=repository):
                self.assertTrue(arguments.is_valid_repository(repository))

    def test_rejects_other_shapes(self):
        for repository in ("plain", "a/b/c", "/", "a/", "/b", ""):
            with self.subTest(repository=repository):
                self.assertFalse(arguments.is_valid_repository(repository))

    def test_rejects_path_and_url_metacharacters(self):
        # These reach REST paths like repos/{repository}/pulls, so the
        # charset -- not just the shape -- is load-bearing.
        for repository in ("o/r?x=1", "o/r#frag", "o/..", "o/.", "-o/r",
                           "_o/r", "o o/r", "o/r name", "o/r/../x"):
            with self.subTest(repository=repository):
                self.assertFalse(arguments.is_valid_repository(repository))


class ParseIssueNumberTest(unittest.TestCase):
    def test_parses_positive_integers(self):
        self.assertEqual(arguments.parse_issue_number("42"), 42)
        self.assertEqual(arguments.parse_issue_number("007"), 7)

    def test_tolerates_one_leading_hash(self):
        self.assertEqual(arguments.parse_issue_number("#42"), 42)
        self.assertIsNone(arguments.parse_issue_number("##42"))

    def test_rejects_everything_else(self):
        for value in ("0", "-1", "abc", "4.2", "", "#", "1e3", "+5", "4 2"):
            with self.subTest(value=value):
                self.assertIsNone(arguments.parse_issue_number(value))


if __name__ == "__main__":
    unittest.main()
