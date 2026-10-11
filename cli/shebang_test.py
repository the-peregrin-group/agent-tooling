"""Every extensionless executable in cli/ pins the system interpreter.

One rule, no PATH lookup: macOS grants OS-level privacy permissions to the
Apple-signed /usr/bin/python3 only (see README, Bootstrap on a fresh machine).
"""

import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parent


class ShebangTest(unittest.TestCase):
    def test_every_executable_pins_system_python(self):
        files = sorted(p for p in CLI.iterdir() if p.is_file() and not p.suffix)
        self.assertTrue(files)
        for path in files:
            with path.open("rb") as fh:
                first = fh.readline().rstrip(b"\n")
            self.assertEqual(first, b"#!/usr/bin/python3", path.name)


if __name__ == "__main__":
    unittest.main()
