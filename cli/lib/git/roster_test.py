"""Tests for lib.git.roster: the TOML-subset parser and entry validation.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lib.git import roster


class _RosterFileTest(unittest.TestCase):
    def write_roster(self, text: str, mode: int = 0o600) -> Path:
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        )
        handle.write(text)
        handle.close()
        os.chmod(handle.name, mode)
        self.addCleanup(os.unlink, handle.name)
        return Path(handle.name)

    def load(self, text: str, mode: int = 0o600) -> dict:
        return roster.load(path_for_testing=self.write_roster(text, mode))


class RosterParseTest(_RosterFileTest):
    def test_full_entry_parses(self):
        entries = self.load(
            "# roster\n"
            "[proj]  # a fixture label\n"
            'checkout = "/repos/proj"\n'
            'remote_url = "ssh://git@forge.example.com/own/proj.git"\n'
            'remote = "upstream"\n'
            'default_branch = "trunk"\n'
            'operable_from = ["/repos/other", "/repos/third"]  # interlock\n'
        )
        entry = entries["proj"]
        self.assertEqual(entry.label, "proj")
        self.assertEqual(entry.checkout, Path("/repos/proj"))
        self.assertEqual(
            entry.remote_url, "ssh://git@forge.example.com/own/proj.git"
        )
        self.assertEqual(entry.remote, "upstream")
        self.assertEqual(entry.default_branch, "trunk")
        self.assertEqual(
            entry.operable_from, (Path("/repos/other"), Path("/repos/third"))
        )
        self.assertFalse(entry.machine_local)

    def test_defaults_apply(self):
        entries = self.load(
            "[proj]\n"
            'checkout = "/repos/proj"\n'
            'remote_url = "ssh://forge.example.com/own/proj"\n'
        )
        entry = entries["proj"]
        self.assertEqual(entry.remote, "origin")
        self.assertEqual(entry.default_branch, "main")
        self.assertEqual(entry.operable_from, ())

    def test_machine_local_entry(self):
        entries = self.load("[scratch]\ncheckout = \"/repos/scratch\"\n")
        entry = entries["scratch"]
        self.assertTrue(entry.machine_local)
        self.assertIsNone(entry.remote_url)
        self.assertIsNone(entry.remote)

    def test_multiple_tables(self):
        entries = self.load(
            "[one]\ncheckout = \"/repos/one\"\n"
            "\n"
            "[two]\ncheckout = \"/repos/two\"\n"
        )
        self.assertEqual(sorted(entries), ["one", "two"])

    def test_empty_array(self):
        entries = self.load(
            "[proj]\ncheckout = \"/repos/proj\"\noperable_from = []\n"
        )
        self.assertEqual(entries["proj"].operable_from, ())

    def test_tilde_checkout_expands(self):
        entries = self.load("[proj]\ncheckout = \"~/repos/proj\"\n")
        self.assertEqual(entries["proj"].checkout, Path.home() / "repos/proj")


class RosterErrorTest(_RosterFileTest):
    def assert_error(self, text: str, fragment: str):
        with self.assertRaises(roster.RosterError) as caught:
            self.load(text)
        self.assertIn(fragment, str(caught.exception))

    def test_missing_file_is_roster_error(self):
        with self.assertRaises(roster.RosterError) as caught:
            roster.load(path_for_testing=Path("/nonexistent/repos.toml"))
        self.assertIn("lib/git/roster.py", str(caught.exception))

    def test_key_outside_table(self):
        self.assert_error('checkout = "/repos/x"\n', "outside any [label]")

    def test_duplicate_table(self):
        self.assert_error(
            "[proj]\ncheckout = \"/a\"\n[proj]\ncheckout = \"/b\"\n",
            "duplicate table",
        )

    def test_duplicate_key(self):
        self.assert_error(
            "[proj]\ncheckout = \"/a\"\ncheckout = \"/b\"\n", "duplicate key"
        )

    def test_unknown_key_fails_loud(self):
        self.assert_error(
            "[proj]\ncheckout = \"/a\"\noperable_form = [\"/b\"]\n",
            "unknown key 'operable_form'",
        )

    def test_missing_checkout(self):
        self.assert_error(
            "[proj]\nremote_url = \"ssh://forge.example.com/x\"\n",
            "missing required key 'checkout'",
        )

    def test_relative_checkout_refused(self):
        self.assert_error(
            "[proj]\ncheckout = \"repos/proj\"\n", "absolute path"
        )

    def test_remote_without_url_is_contradiction(self):
        self.assert_error(
            "[proj]\ncheckout = \"/a\"\nremote = \"origin\"\n",
            "machine-local entry names no remote",
        )

    def test_invalid_label(self):
        self.assert_error("[Proj]\ncheckout = \"/a\"\n", "not a valid roster label")

    def test_unterminated_string(self):
        self.assert_error("[proj]\ncheckout = \"/a\n", "unterminated string")

    def test_escape_sequences_rejected(self):
        self.assert_error(
            '[proj]\ncheckout = "/a\\\\b"\n', "escape sequences"
        )

    def test_bare_value_rejected(self):
        self.assert_error("[proj]\ncheckout = 42\n", "outside the supported")

    def test_array_of_non_strings_rejected(self):
        self.assert_error(
            "[proj]\ncheckout = \"/a\"\noperable_from = [42]\n",
            "only quoted strings",
        )

    def test_unterminated_array(self):
        self.assert_error(
            "[proj]\ncheckout = \"/a\"\noperable_from = [\"/b\",\n",
            "unterminated array",
        )

    def test_trailing_garbage_after_string(self):
        self.assert_error(
            '[proj]\ncheckout = "/a" nonsense\n', "unexpected content"
        )

    def test_default_branch_must_look_like_a_branch(self):
        self.assert_error(
            "[proj]\ncheckout = \"/a\"\ndefault_branch = \"-bad\"\n",
            "'default_branch'",
        )

    def test_remote_name_with_leading_punctuation_rejected(self):
        # `remote = "--all"` would otherwise ride into `git fetch --all`
        # and only fail incidentally downstream.
        self.assert_error(
            "[proj]\ncheckout = \"/a\"\n"
            'remote_url = "ssh://forge.example.com/x"\nremote = "--all"\n',
            "plain remote name",
        )


class ValidateTextTest(unittest.TestCase):
    """validate_text is load()'s back half, exposed so gitw-repo-register
    can vet a candidate roster before writing it."""

    def test_returns_entries_for_valid_text(self):
        entries = roster.validate_text(
            "[proj]\ncheckout = \"/repos/proj\"\n", Path("candidate")
        )
        self.assertEqual(entries["proj"].checkout, Path("/repos/proj"))

    def test_raises_roster_error_naming_the_source(self):
        with self.assertRaises(roster.RosterError) as caught:
            roster.validate_text("junk\n", Path("candidate"))
        self.assertIn("candidate", str(caught.exception))


class ResolveOrDieTest(unittest.TestCase):
    """The shared verb front half: label validation, load, lookup."""

    _ENTRY = roster.Entry(label="proj", checkout=Path("/repos/proj"))

    def test_success_returns_the_entry(self):
        with mock.patch.object(
            roster, "load", return_value={"proj": self._ENTRY}
        ):
            self.assertIs(
                roster.resolve_or_die("proj", "usage-line"), self._ENTRY
            )

    def test_invalid_label_is_usage_error_before_any_load(self):
        with mock.patch.object(roster, "load") as load, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                roster.resolve_or_die("Not Valid", "usage-line")
        self.assertEqual(caught.exception.code, 2)
        load.assert_not_called()
        self.assertIn("usage-line", stderr.getvalue())

    def test_roster_error_exits_with_auth_code(self):
        with mock.patch.object(
            roster, "load", side_effect=roster.RosterError("broken roster")
        ), contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                roster.resolve_or_die("proj", "usage-line")
        self.assertEqual(caught.exception.code, 5)
        self.assertIn("broken roster", stderr.getvalue())

    def test_unknown_label_is_not_found_and_names_known_labels(self):
        with mock.patch.object(
            roster, "load", return_value={"proj": self._ENTRY}
        ), contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                roster.resolve_or_die("ghost", "usage-line")
        self.assertEqual(caught.exception.code, 3)
        self.assertIn("'ghost'", stderr.getvalue())
        self.assertIn("proj", stderr.getvalue())


class RosterModeWarningTest(_RosterFileTest):
    def test_group_readable_warns_but_loads(self):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            entries = self.load("[proj]\ncheckout = \"/a\"\n", mode=0o644)
        self.assertIn("proj", entries)
        self.assertIn("0600", stderr.getvalue())

    def test_strict_mode_stays_silent(self):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.load("[proj]\ncheckout = \"/a\"\n", mode=0o600)
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
