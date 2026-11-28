"""Unit tests for label_schema.py (ghw-label-sync's desired state and diff),
against tracker_schema_test_support's fixture.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

if __package__ in (None, ""):  # direct invocation
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import tracker_schema_test_support as fixture
from lib import tracker_schema
from lib.github import label_schema

_ALL_BUT_PRIORITIES = ("issue_kinds", "issue_label_schema.axes",
                       "issue_label_schema.labels")


def _desired(document=None, regime="board-field"):
    loaded = fixture.loaded(document) if document is not False else fixture.missing()
    return label_schema.desired_labels(loaded, regime)


class DesiredLabelsTest(unittest.TestCase):
    def test_kinds_axis_labels_and_unaxed_labels_with_their_values(self):
        desired = _desired()
        self.assertEqual(
            list(desired.labels),
            ["task", "bug", "chore", "area:core", "area:docs", "site:a",
             "human", "perf"],
        )
        self.assertEqual(desired.labels["site:a"],
                         {"color": "c5def5",
                          "description": "The Site A deployment"})
        self.assertEqual(desired.sections, _ALL_BUT_PRIORITIES)
        self.assertEqual(desired.notes, [])

    def test_priorities_are_labels_only_in_the_p_labels_regime(self):
        self.assertIn("P4", _desired(regime="p-labels").labels)
        self.assertIn(tracker_schema.ISSUE_PRIORITIES,
                      _desired(regime="p-labels").sections)
        self.assertNotIn("P4", _desired(regime="board-field").labels)

    def test_an_unknown_regime_keeps_priority_labels_without_syncing_them(self):
        desired = _desired(regime="unknown")
        self.assertNotIn("P0", desired.labels)
        self.assertEqual(desired.keep, {"P0", "P1", "P4"})
        self.assertIn(tracker_schema.ISSUE_PRIORITIES, desired.sections)
        self.assertIn("priority regime is unknown", desired.notes[0])

    def test_no_schema_declares_nothing_but_still_names_its_sections(self):
        desired = _desired(False)
        self.assertEqual(desired.labels, {})
        self.assertEqual(desired.sections, _ALL_BUT_PRIORITIES)

    def test_an_unusable_section_contributes_nothing(self):
        document = fixture.document()
        document["issue_label_schema"]["axes"] = {}
        desired = _desired(document)
        self.assertEqual(list(desired.labels),
                         ["task", "bug", "chore", "human", "perf"])

    def test_a_missing_meaning_or_colour_reads_as_none(self):
        document = fixture.document()
        del document["issue_kinds"][0]["meaning"]
        del document["issue_kinds"][1]["color"]
        desired = _desired(document)
        self.assertIsNone(desired.labels["task"]["description"])
        self.assertIsNone(desired.labels["bug"]["color"])

    def test_one_name_in_two_sections_is_synced_once_with_a_warning(self):
        document = fixture.document()
        document["issue_label_schema"]["labels"].append(
            {"name": "Bug", "meaning": "Another bug", "color": "000000"})
        desired = _desired(document)
        self.assertEqual(desired.labels["bug"]["description"],
                         "Something is broken")
        self.assertNotIn("Bug", desired.labels)
        self.assertIn("same GitHub label", desired.notes[0])

    def test_a_long_meaning_is_shortened_to_githubs_limit_at_a_word(self):
        meaning = " ".join(["meaningful"] * 20)
        fitted = label_schema._fitted(meaning)
        self.assertLessEqual(len(fitted), label_schema.DESCRIPTION_LIMIT)
        self.assertTrue(fitted.endswith("meaningful..."))
        self.assertEqual(label_schema._fitted("short"), "short")
        exact = "x" * label_schema.DESCRIPTION_LIMIT
        self.assertEqual(label_schema._fitted(exact), exact)


def _wanted(**labels) -> label_schema.DesiredLabels:
    return label_schema.DesiredLabels(labels=dict(labels))


class DiffLabelsTest(unittest.TestCase):
    def setUp(self):
        self.desired = label_schema.DesiredLabels(labels={
            "bug": {"color": "d73a4a", "description": "Broken"},
            "area:core": {"color": "bfdadc", "description": "Core engine"},
        })

    def test_converged_registry_yields_an_empty_diff(self):
        existing = [{"name": "bug", "color": "d73a4a", "description": "Broken"},
                    {"name": "area:core", "color": "bfdadc",
                     "description": "Core engine"}]
        difference = label_schema.diff_labels(self.desired, existing)
        self.assertEqual(difference["create"], [])
        self.assertEqual(difference["update"], [])
        self.assertEqual(difference["delete"], [])
        self.assertEqual(difference["unchanged"], ["area:core", "bug"])

    def test_missing_labels_are_creates(self):
        difference = label_schema.diff_labels(self.desired, [])
        self.assertEqual([label["name"] for label in difference["create"]],
                         ["area:core", "bug"])

    def test_color_drift_is_an_update_carrying_the_previous_values(self):
        existing = [{"name": "bug", "color": "000000", "description": "Broken"}]
        update = label_schema.diff_labels(self.desired, existing)["update"][0]
        self.assertEqual(update["name"], "bug")
        self.assertEqual(update["color"], "d73a4a")
        self.assertEqual(update["from"], {"color": "000000",
                                          "description": "Broken"})

    def test_description_drift_is_an_update(self):
        existing = [{"name": "bug", "color": "d73a4a", "description": "stale"}]
        self.assertEqual(
            len(label_schema.diff_labels(self.desired, existing)["update"]), 1
        )

    def test_case_and_hash_differences_are_not_drift(self):
        existing = [{"name": "bug", "color": "#D73A4A", "description": "Broken"}]
        self.assertEqual(
            label_schema.diff_labels(self.desired, existing)["update"], []
        )

    def test_null_description_compares_as_empty(self):
        desired = _wanted(x={"color": "ffffff", "description": ""})
        existing = [{"name": "x", "color": "ffffff", "description": None}]
        self.assertEqual(label_schema.diff_labels(desired, existing)["update"], [])

    def test_an_absent_value_keeps_the_live_one(self):
        desired = _wanted(x={"color": None, "description": None})
        existing = [{"name": "x", "color": "123456", "description": "live"}]
        difference = label_schema.diff_labels(desired, existing)
        self.assertEqual(difference["update"], [])
        self.assertEqual(difference["unchanged"], ["x"])

    def test_an_absent_value_on_a_create_takes_the_neutral_default(self):
        desired = _wanted(x={"color": None, "description": None})
        self.assertEqual(label_schema.diff_labels(desired, [])["create"],
                         [{"name": "x", "color": label_schema.NEUTRAL_COLOR,
                           "description": ""}])

    def test_undeclared_labels_are_deletion_candidates(self):
        existing = [{"name": "wontfix", "color": "ffffff", "description": ""},
                    {"name": "duplicate", "color": "cfd3d7", "description": ""}]
        self.assertEqual(
            label_schema.diff_labels(self.desired, existing)["delete"],
            ["duplicate", "wontfix"],
        )

    def test_a_kept_label_is_never_a_deletion_candidate(self):
        self.desired.keep = {"p0"}
        existing = [{"name": "P0", "color": "b60205", "description": ""}]
        self.assertEqual(
            label_schema.diff_labels(self.desired, existing)["delete"], [])

    def test_case_only_difference_is_never_create_plus_delete(self):
        # GitHub's label namespace is case-insensitive, so planning a create
        # for 'bug' against a live 'Bug' would 422 as already-existing on
        # every single run.
        existing = [{"name": "Bug", "color": "d73a4a", "description": "Broken"}]
        difference = label_schema.diff_labels(
            _wanted(bug=self.desired.labels["bug"]), existing)
        self.assertEqual(difference["create"], [])
        self.assertEqual(difference["delete"], [])
        self.assertEqual(difference["unchanged"], ["Bug"])

    def test_case_only_difference_is_reported(self):
        existing = [{"name": "Bug", "color": "d73a4a", "description": "Broken"}]
        difference = label_schema.diff_labels(
            _wanted(bug=self.desired.labels["bug"]), existing)
        self.assertEqual(difference["case_mismatch"],
                         [{"live": "Bug", "desired": "bug"}])

    def test_matching_names_exactly_report_no_case_mismatch(self):
        existing = [{"name": "bug", "color": "d73a4a", "description": "Broken"}]
        self.assertEqual(
            label_schema.diff_labels(_wanted(bug=self.desired.labels["bug"]),
                                     existing)["case_mismatch"],
            [],
        )

    def test_update_targets_the_live_spelling(self):
        # `gh label edit` has to name the label as it actually exists.
        existing = [{"name": "Bug", "color": "000000", "description": "Broken"}]
        update = label_schema.diff_labels(
            _wanted(bug=self.desired.labels["bug"]), existing)["update"][0]
        self.assertEqual(update["name"], "Bug")
        self.assertEqual(update["color"], "d73a4a")


if __name__ == "__main__":
    unittest.main()
