"""Unit tests for plan.py (output and exit-code conventions).

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

if __package__ in (None, ""):  # direct invocation: python3 lib/plan_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import plan


class EmitTest(unittest.TestCase):
    def test_emit_writes_json_with_trailing_newline(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            plan.emit({"a": 1, "nested": {"b": [2, 3]}})
        text = stdout.getvalue()
        self.assertTrue(text.endswith("\n"))
        self.assertEqual(json.loads(text), {"a": 1, "nested": {"b": [2, 3]}})

    def test_emit_plan_accepts_the_action_vocabulary(self):
        for action in ("plan", "applied", "conflict"):
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                plan.emit_plan(action, detail=1)
            self.assertEqual(json.loads(stdout.getvalue()),
                             {"action": action, "detail": 1})

    def test_emit_plan_rejects_unknown_action(self):
        with self.assertRaisesRegex(ValueError, "dry-run"):
            plan.emit_plan("dry-run")


class UsageDieTest(unittest.TestCase):
    def test_exits_2_with_mistake_and_usage_on_stderr(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            plan.usage_die("expected exactly one argument", "ghw-orient <owner/repo>")
        self.assertEqual(caught.exception.code, plan.EXIT_USAGE)
        self.assertIn("expected exactly one argument", stderr.getvalue())
        self.assertIn("usage: ghw-orient <owner/repo>", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
