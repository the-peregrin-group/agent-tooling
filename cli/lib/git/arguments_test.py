"""Tests for lib.git.arguments: the gitw positional-grammar validators.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import unittest

from lib.git import arguments


class IsValidLabelTest(unittest.TestCase):
    def test_accepts_plausible_labels(self):
        for label in ("proj", "field-notes", "a.b", "x_y", "2fa", "p2p.local"):
            with self.subTest(label=label):
                self.assertTrue(arguments.is_valid_label(label))

    def test_rejects_everything_else(self):
        for label in ("", "Upper", "-lead", ".lead", "_lead", "has space",
                      "has/slash", "trailing "):
            with self.subTest(label=label):
                self.assertFalse(arguments.is_valid_label(label))


class IsValidBranchPrefixTest(unittest.TestCase):
    def test_accepts_grammar_conforming_prefixes(self):
        for prefix in ("fix/", "reconcile/", "a2/", "long-name/"):
            with self.subTest(prefix=prefix):
                self.assertTrue(arguments.is_valid_branch_prefix(prefix))

    def test_rejects_everything_else(self):
        # No missing slash, no uppercase, no multi-level, no leading
        # digit/hyphen, no underscore -- the prefix is allowlist material.
        for prefix in ("", "fix", "Fix/", "a/b/", "-x/", "2fix/",
                       "fix_a/", "fix /", "//", " /", "/ "):
            with self.subTest(prefix=prefix):
                self.assertFalse(arguments.is_valid_branch_prefix(prefix))

    def test_accepts_the_bare_slash(self):
        self.assertTrue(arguments.is_valid_branch_prefix("/"))


class IsValidNameForPrefixTest(unittest.TestCase):
    def test_a_real_prefix_takes_a_single_level_name(self):
        self.assertTrue(arguments.is_valid_name_for_prefix("fix/", "topic"))
        self.assertFalse(arguments.is_valid_name_for_prefix("fix/", "a/b"))

    def test_the_bare_slash_takes_a_full_branch_name(self):
        for name in ("foo-bar", "someone/topic", "a/b/c"):
            with self.subTest(name=name):
                self.assertTrue(arguments.is_valid_name_for_prefix("/", name))
        for name in ("", "/x", "x/", "a//b", "a..b", "x.lock"):
            with self.subTest(name=name):
                self.assertFalse(arguments.is_valid_name_for_prefix("/", name))

    def test_prefixed_branch_drops_the_bare_slash(self):
        self.assertEqual(arguments.prefixed_branch("fix/", "a"), "fix/a")
        self.assertEqual(arguments.prefixed_branch("/", "foo-bar"), "foo-bar")


class IsValidBranchTest(unittest.TestCase):
    def test_accepts_full_branch_names_with_levels(self):
        for branch in ("main", "develop", "fix/trunk", "a/b/c", "v1.2"):
            with self.subTest(branch=branch):
                self.assertTrue(arguments.is_valid_branch(branch))

    def test_rejects_ref_syntax_traps(self):
        for branch in ("", "-lead", "a..b", "a//b", "end/", "x.lock",
                       "dot.", "has space"):
            with self.subTest(branch=branch):
                self.assertFalse(arguments.is_valid_branch(branch))


class IsValidBranchNameTest(unittest.TestCase):
    def test_accepts_safe_name_tails(self):
        for name in ("topic", "2001-02-03", "a.b", "UPPER", "x_y", "v1.2.3"):
            with self.subTest(name=name):
                self.assertTrue(arguments.is_valid_branch_name(name))

    def test_rejects_ref_syntax_traps_and_junk(self):
        for name in ("", "a b", "a/b", ".lead", "-lead", "_lead", "a..b",
                     "x.lock", "trailing."):
            with self.subTest(name=name):
                self.assertFalse(arguments.is_valid_branch_name(name))


if __name__ == "__main__":
    unittest.main()
