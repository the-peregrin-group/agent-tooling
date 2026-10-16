"""Every extensionless executable in cli/ pins the system interpreter.

One rule, no PATH lookup: macOS grants OS-level privacy permissions to the
Apple-signed /usr/bin/python3 only (see README, Bootstrap on a fresh machine).
"""

import os
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parent


class ShebangTest(unittest.TestCase):
    def test_every_executable_pins_system_python(self):
        files = sorted(
            p
            for p in CLI.iterdir()
            if p.is_file()
            and not p.suffix
            and not p.name.startswith(".")
            and not p.name.endswith("~")
        )
        self.assertTrue(files)
        bad = []
        for path in files:
            with path.open("rb") as fh:
                first = fh.readline().rstrip(b"\r\n")
            if first != b"#!/usr/bin/python3":
                bad.append("%s: %r" % (path.name, first))
            elif not os.access(path, os.X_OK):
                bad.append("%s: not executable" % path.name)
        self.assertEqual(bad, [], "executables not pinning /usr/bin/python3")


if __name__ == "__main__":
    unittest.main()
