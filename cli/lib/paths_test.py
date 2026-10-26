"""Unit tests for lib.paths (the config and state directories).

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'

Every case passes its own environment mapping, and the creation cases work
under a temporary directory, so no test touches the real config or state
roots.
"""

from __future__ import annotations

import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

if __package__ in (None, ""):  # direct invocation: python3 lib/paths_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.paths import config_dir, ensure_private_dir, state_dir


RESOLVERS = (
    ("config", config_dir, "XDG_CONFIG_HOME", Path("/home/u/.config")),
    ("state", state_dir, "XDG_STATE_HOME", Path("/home/u/.local/state")),
)


class ResolveTest(unittest.TestCase):
    def test_xdg_set_is_the_root(self):
        for kind, resolve, variable, _ in RESOLVERS:
            with self.subTest(kind):
                environ = {variable: "/xdg/root", "HOME": "/home/u"}
                self.assertEqual(resolve("bdw", environ),
                                 Path("/xdg/root/agent-tooling/bdw"))

    def test_xdg_unset_falls_back_under_home(self):
        for kind, resolve, _, default in RESOLVERS:
            with self.subTest(kind):
                self.assertEqual(resolve("bdw", {"HOME": "/home/u"}),
                                 default / "agent-tooling" / "bdw")

    def test_xdg_empty_counts_as_unset(self):
        for kind, resolve, variable, default in RESOLVERS:
            with self.subTest(kind):
                environ = {variable: "", "HOME": "/home/u"}
                self.assertEqual(resolve("bdw", environ),
                                 default / "agent-tooling" / "bdw")

    def test_relative_xdg_is_ignored(self):
        for kind, resolve, variable, default in RESOLVERS:
            with self.subTest(kind):
                environ = {variable: "relative/root", "HOME": "/home/u"}
                self.assertEqual(resolve("bdw", environ),
                                 default / "agent-tooling" / "bdw")

    def test_the_other_kinds_variable_is_not_used(self):
        environ = {"XDG_STATE_HOME": "/state", "HOME": "/home/u"}
        self.assertEqual(config_dir("bdw", environ),
                         Path("/home/u/.config/agent-tooling/bdw"))
        environ = {"XDG_CONFIG_HOME": "/config", "HOME": "/home/u"}
        self.assertEqual(state_dir("bdw", environ),
                         Path("/home/u/.local/state/agent-tooling/bdw"))

    def test_xdg_set_needs_no_home(self):
        for kind, resolve, variable, _ in RESOLVERS:
            with self.subTest(kind):
                self.assertEqual(resolve("bdw", {variable: "/xdg"}),
                                 Path("/xdg/agent-tooling/bdw"))

    def test_no_usable_home_resolves_to_none(self):
        for kind, resolve, variable, _ in RESOLVERS:
            for environ in ({}, {"HOME": ""}, {"HOME": "relative/home"},
                            {variable: "relative", "HOME": ""}):
                with self.subTest(kind, environ=environ):
                    self.assertIsNone(resolve("bdw", environ))

    def test_each_tool_gets_its_own_subdirectory(self):
        for kind, resolve, _, default in RESOLVERS:
            with self.subTest(kind):
                environ = {"HOME": "/home/u"}
                self.assertEqual(resolve("triage-issues", environ),
                                 default / "agent-tooling" / "triage-issues")
                self.assertNotEqual(resolve("gitw", environ),
                                    resolve("fjw", environ))

    def test_a_tool_name_that_is_not_one_segment_is_refused(self):
        for kind, resolve, _, _ in RESOLVERS:
            for tool in ("", ".", "..", "../x", "a/b", "/abs", "Gitw",
                         "-x", "x-", "a--b", "gitw\n", None):
                with self.subTest(kind, tool=tool):
                    with self.assertRaises(ValueError):
                        resolve(tool, {"HOME": "/home/u"})

    def test_only_the_injected_mapping_is_read(self):
        real = {"HOME": "/real/home", "XDG_CONFIG_HOME": "/real/config",
                "XDG_STATE_HOME": "/real/state"}
        with mock.patch.dict(os.environ, real), \
                mock.patch.object(Path, "home",
                                  side_effect=AssertionError("Path.home")), \
                mock.patch.object(Path, "expanduser",
                                  side_effect=AssertionError("expanduser")):
            self.assertIsNone(config_dir("bdw", {}))
            self.assertIsNone(state_dir("bdw", {}))
            self.assertEqual(config_dir("bdw", {"HOME": "/injected"}),
                             Path("/injected/.config/agent-tooling/bdw"))

    def test_resolving_creates_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            for _, resolve, variable, _ in RESOLVERS:
                resolve("bdw", {variable: tmp})
            self.assertEqual(os.listdir(tmp), [])

    def test_an_absolute_root_that_is_not_a_directory_is_honored(self):
        # gitw_test_support points XDG_CONFIG_HOME at os.devnull for git
        # subprocesses; the resolver does not second-guess it.
        environ = {"XDG_CONFIG_HOME": os.devnull, "HOME": "/home/u"}
        path = config_dir("gitw", environ)
        self.assertEqual(path, Path(os.devnull) / "agent-tooling" / "gitw")
        self.assertFalse(path.exists())
        with self.assertRaises(OSError):
            ensure_private_dir(path)


class EnsurePrivateDirTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _mode(self, path: Path) -> int:
        return stat.S_IMODE(path.stat().st_mode)

    def test_creates_the_directory_and_missing_parents_0700(self):
        path = state_dir("bdw", {"XDG_STATE_HOME": str(self.root / "state")})
        old_umask = os.umask(0o022)
        try:
            ensure_private_dir(path)
        finally:
            os.umask(old_umask)
        for directory in (path, path.parent, path.parent.parent):
            with self.subTest(directory=directory):
                self.assertTrue(directory.is_dir())
                self.assertEqual(self._mode(directory), 0o700)

    def test_the_umask_cannot_loosen_or_strip_the_mode(self):
        for umask in (0o000, 0o077, 0o700):
            with self.subTest(umask=oct(umask)):
                path = self.root / f"u{umask:o}" / "agent-tooling" / "bdw"
                old_umask = os.umask(umask)
                try:
                    ensure_private_dir(path)
                finally:
                    os.umask(old_umask)
                self.assertEqual(self._mode(path), 0o700)

    def test_existing_directories_keep_their_mode(self):
        existing = self.root / "agent-tooling"
        existing.mkdir()
        os.chmod(existing, 0o755)
        ensure_private_dir(existing / "bdw")
        self.assertEqual(self._mode(existing), 0o755)
        self.assertEqual(self._mode(existing / "bdw"), 0o700)

    def test_an_existing_directory_is_a_no_op(self):
        path = self.root / "bdw"
        path.mkdir()
        os.chmod(path, 0o750)
        ensure_private_dir(path)
        self.assertEqual(self._mode(path), 0o750)

    def test_a_file_in_the_way_raises(self):
        (self.root / "agent-tooling").write_text("")
        with self.assertRaises(OSError):
            ensure_private_dir(self.root / "agent-tooling" / "bdw")


if __name__ == "__main__":
    unittest.main()
