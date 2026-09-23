"""Unit tests for lib.labels (the label attachment contract).

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

if __package__ in (None, ""):  # direct invocation: python3 lib/labels_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.github import labels

_REGISTRY = {
    "feature", "improvement", "bug", "debt", "meta",
    "area:core", "area:docs", "site-a", "perf",
}


class ValidateCreationLabelsTest(unittest.TestCase):
    def test_happy_paths_pass(self):
        labels.validate_creation_labels("bug", ["area:core"], _REGISTRY)
        labels.validate_creation_labels("meta", ["area:docs", "site-a"], _REGISTRY)

    def test_unknown_type_label_is_refused(self):
        with self.assertRaises(labels.LabelContractError) as caught:
            labels.validate_creation_labels("task", ["area:core"], _REGISTRY)
        self.assertIn("feature|improvement|bug|debt|meta", str(caught.exception))

    def test_type_label_duplicated_among_extras_gets_a_clear_message(self):
        with self.assertRaises(labels.LabelContractError) as caught:
            labels.validate_creation_labels("bug", ["area:core", "bug"], _REGISTRY)
        self.assertIn("duplicates the type label", str(caught.exception))

    def test_second_type_label_among_extras_is_refused(self):
        with self.assertRaises(labels.LabelContractError) as caught:
            labels.validate_creation_labels("bug", ["area:core", "debt"], _REGISTRY)
        self.assertIn("'debt'", str(caught.exception))
        self.assertIn("'bug'", str(caught.exception))

    def test_missing_area_label_is_refused(self):
        with self.assertRaises(labels.LabelContractError) as caught:
            labels.validate_creation_labels("bug", ["perf"], _REGISTRY)
        self.assertIn("area:", str(caught.exception))

    def test_no_extra_labels_at_all_is_refused(self):
        with self.assertRaises(labels.LabelContractError):
            labels.validate_creation_labels("bug", [], _REGISTRY)

    def test_label_absent_from_registry_is_refused_naming_the_sync_path(self):
        with self.assertRaises(labels.LabelContractError) as caught:
            labels.validate_creation_labels("bug", ["area:core", "nope"], _REGISTRY)
        self.assertIn("'nope'", str(caught.exception))
        self.assertIn("ghw-label-sync", str(caught.exception))

    def test_type_label_absent_from_registry_is_refused(self):
        registry = {"area:core"}  # repo not bootstrapped: no type labels yet
        with self.assertRaises(labels.LabelContractError) as caught:
            labels.validate_creation_labels("bug", ["area:core"], registry)
        self.assertIn("'bug'", str(caught.exception))


class ValidateLabelAdditionTest(unittest.TestCase):
    def test_label_absent_from_registry_is_refused_naming_the_sync_path(self):
        with self.assertRaises(labels.LabelContractError) as caught:
            labels.validate_label_addition("nope", ["bug"], _REGISTRY)
        self.assertIn("ghw-label-sync", str(caught.exception))

    def test_second_type_label_names_the_incumbent(self):
        with self.assertRaises(labels.LabelContractError) as caught:
            labels.validate_label_addition("debt", ["bug", "area:core"], _REGISTRY)
        self.assertIn("'bug'", str(caught.exception))
        self.assertIn("remove-label", str(caught.exception))

    def test_re_adding_the_incumbent_type_label_passes(self):
        labels.validate_label_addition("bug", ["bug", "area:core"], _REGISTRY)

    def test_first_type_label_passes(self):
        labels.validate_label_addition("bug", ["area:core"], _REGISTRY)

    def test_non_type_label_passes_alongside_a_type_label(self):
        labels.validate_label_addition("perf", ["bug"], _REGISTRY)


class TypeLabelsAmongTest(unittest.TestCase):
    def test_filters_and_preserves_order(self):
        self.assertEqual(
            labels.type_labels_among(["area:core", "debt", "bug"]), ["debt", "bug"]
        )


if __name__ == "__main__":
    unittest.main()
