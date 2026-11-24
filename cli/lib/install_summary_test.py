"""Unit tests for install_summary.py, over hand-built reports.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'

The end-to-end output is tested through the entry point in install_test.py;
these pin the classification rules, which need report shapes a fixture
install cannot easily produce.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

if __package__ in (None, ""):  # direct invocation: python3 lib/install_summary_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.install_summary import short_commit, summarize  # noqa: E402

SHA = "0123456789abcdef0123456789abcdef01234567"


def cohort(**overrides):
    base = {
        "kind": "bin",
        "target": "/somewhere/bin",
        "status": "in-sync",
        "installed_commit": SHA,
        "ships": 3,
        "only_in_source": [],
        "changed": [],
        "receipt_mismatch": [],
        "only_installed": [],
        "unowned_preserved": [],
        "unowned_replaced": [],
        "foreign_files": [],
        "adoptable": [],
        "conflicting": [],
    }
    base.update(overrides)
    return base


def report(cohorts, **overrides):
    base = {
        "source": "/src",
        "source_repo": "widget-kit",
        "source_commit": SHA,
        "selected_cohorts": sorted(cohorts),
        "cohorts": cohorts,
        "recovery_pending": [],
        "status": "in-sync",
    }
    base.update(overrides)
    return base


class SummarizeTest(unittest.TestCase):
    def test_in_sync_is_a_header_and_one_line_per_cohort(self):
        text = summarize(report({"bin": cohort(), "agents": cohort(kind="agents")}))
        self.assertEqual(
            text.splitlines(),
            [
                "widget-kit @ 0123456: in-sync",
                "bin     in-sync (3 shipped)",
                "agents  in-sync (3 shipped)",
            ],
        )

    def test_inventory_is_counted_not_listed(self):
        text = summarize(
            report({"bin": cohort(foreign_files=["x", "y"], unowned_preserved=["z"])})
        )
        self.assertIn("1 unowned files, 2 foreign files left alone", text)
        for name in ("x", "y", "z"):
            self.assertNotIn(f" {name}", text)
        self.assertTrue(text.endswith("--json lists it)"))

    def test_destructive_lists_are_named_in_capitals(self):
        text = summarize(
            report(
                {
                    "skills": cohort(
                        status="drift",
                        unowned_replaced=["a/x.md"],
                        foreign_replaced=["b/y.md"],
                        conflicting=["c"],
                        only_installed=["d"],
                        receipt_mismatch=["e"],
                    )
                },
                status="drift",
            )
        )
        self.assertIn("  WOULD DELETE unowned: a/x.md", text)
        self.assertIn("  WOULD DELETE foreign: b/y.md", text)
        self.assertIn("  CONFLICTING (apply refuses; adopt takes over): c", text)
        self.assertIn("  WOULD REMOVE (no longer shipped): d", text)
        self.assertIn("  RECEIPT MISMATCH", text)

    def test_unknown_keys_are_shown(self):
        text = summarize(
            report(
                {"bin": cohort(new_list=["n1", "n2"], new_scalar=7)},
                new_top="t",
            )
        )
        self.assertIn("  new_list: n1, n2", text)
        self.assertIn("  new_scalar: 7", text)
        self.assertIn("  new_top: t", text)

    def test_recovery_is_shown(self):
        text = summarize(report({"bin": cohort()}, recovery_pending=["bin.retired-9"]))
        self.assertIn("RECOVERY PENDING", text)
        self.assertIn("bin.retired-9", text)

    def test_installed_commit_shown_only_when_it_differs(self):
        other = "f" * 40
        text = summarize(report({"bin": cohort(installed_commit=other)}))
        self.assertIn("installed @ fffffff", text)

    def test_applied_plan_names_adoption_and_removal(self):
        text = summarize(
            {
                "action": "applied",
                "source": "/src",
                "source_repo": "widget-kit",
                "source_commit": SHA + "-dirty",
                "selected_cohorts": ["skills"],
                "cohorts": {
                    "skills": {
                        "kind": "skills",
                        "target": "/t",
                        "installed": 4,
                        "units": ["a", "b"],
                        "adopted": ["a"],
                        "retired": ["old"],
                        "unowned_replaced": [],
                        "foreign_units": ["f"],
                    }
                },
                "recovered": ["a.retired-1"],
                "supersedes": "old-kit",
            }
        )
        lines = text.splitlines()
        self.assertEqual(
            lines[0], "applied widget-kit @ 0123456-dirty, superseding old-kit"
        )
        self.assertIn("  RECOVERED interrupted swap: a.retired-1", lines)
        self.assertIn(
            "skills  installed 4 files in 2 units; 1 foreign units left alone", lines
        )
        self.assertIn("  adopted: a", lines)
        self.assertIn("  REMOVED (no longer shipped): old", lines)

    def test_short_commit(self):
        self.assertEqual(short_commit(SHA), "0123456")
        self.assertEqual(short_commit(SHA + "-dirty"), "0123456-dirty")
        self.assertEqual(short_commit(None), "None")


if __name__ == "__main__":
    unittest.main()
