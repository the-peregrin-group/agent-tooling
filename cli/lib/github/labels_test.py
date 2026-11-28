"""Unit tests for lib.github.labels (the label attachment contract), against
tracker_schema_test_support's fixture.

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
from lib.github import labels

# The fixture's labels, all live, plus one live label it does not declare.
_REGISTRY = {
    "task", "bug", "chore", "P0", "area:core", "area:docs", "site:a",
    "human", "perf", "wontfix",
}
_RULES = labels.LabelRules(fixture.loaded())


def _rules_without(*sections) -> labels.LabelRules:
    document = fixture.document()
    for section in sections:
        if section == "axes":
            document["issue_label_schema"]["axes"] = {}
        else:
            document[section] = {}
    return labels.LabelRules(fixture.loaded(document))


def _refused(test, call, *arguments, fragment=None):
    with test.assertRaises(labels.LabelContractError) as caught:
        call(*arguments)
    if fragment is not None:
        test.assertIn(fragment, str(caught.exception))
    return str(caught.exception)


class LabelRulesTest(unittest.TestCase):
    def test_reads_the_kinds_the_declared_labels_and_the_required_axes(self):
        self.assertEqual(_RULES.kinds, {"task", "bug", "chore"})
        self.assertEqual(
            _RULES.declared,
            {"task", "bug", "chore", "P0", "P1", "P4", "area:core",
             "area:docs", "site:a", "human", "perf"},
        )
        self.assertEqual([axis.name for axis in _RULES.required_axes], ["area"])
        self.assertEqual(_RULES.unchecked(), [])

    def test_no_schema_checks_nothing_and_says_so(self):
        rules = labels.LabelRules(fixture.missing())
        self.assertIsNone(rules.kinds)
        self.assertIsNone(rules.declared)
        self.assertIsNone(rules.required_axes)
        self.assertEqual(len(rules.unchecked()), 3)

    def test_one_unusable_label_section_leaves_labels_unverified(self):
        rules = _rules_without("issue_priorities")
        self.assertIsNone(rules.declared)
        self.assertEqual(rules.kinds, {"task", "bug", "chore"})
        self.assertEqual(len(rules.unchecked()), 1)


class ValidateCreationLabelsTest(unittest.TestCase):
    def _validate(self, kind, extras, registry=_REGISTRY, rules=_RULES):
        labels.validate_creation_labels(kind, list(extras), registry, rules)

    def test_happy_paths_pass(self):
        self._validate("bug", ["area:core"])
        self._validate("chore", ["area:docs", "site:a", "human", "P0"])

    def test_a_kind_outside_the_schema_is_refused_listing_the_kinds(self):
        message = _refused(self, self._validate, "feature", ["area:core"])
        self.assertIn("bug|chore|task", message)
        self.assertIn("o/r@main:TRACKER.md", message)

    def test_kind_duplicated_among_extras_gets_a_clear_message(self):
        _refused(self, self._validate, "bug", ["area:core", "bug"],
                 fragment="duplicates the kind label")

    def test_second_kind_among_extras_is_refused(self):
        message = _refused(self, self._validate, "bug", ["area:core", "chore"])
        self.assertIn("'chore'", message)
        self.assertIn("'bug'", message)

    def test_a_live_label_the_schema_does_not_declare_is_refused(self):
        _refused(self, self._validate, "bug", ["area:core", "wontfix"],
                 fragment="not declared in the repo's Tracker Schema")

    def test_an_undeclared_label_on_an_axis_prefix_is_refused(self):
        _refused(self, self._validate, "bug", ["area:ghost"],
                 fragment="'area:ghost'")

    def test_a_label_from_every_required_axis_is_needed(self):
        for extras in ([], ["perf"], ["site:a", "human"]):
            with self.subTest(extras=extras):
                _refused(self, self._validate, "bug", extras,
                         fragment="'area:' label")

    def test_label_absent_from_registry_is_refused_naming_the_sync_path(self):
        _refused(self, self._validate, "bug", ["area:core"], {"bug"},
                 fragment="ghw-label-sync")

    def test_without_kinds_any_live_kind_label_passes(self):
        rules = _rules_without("issue_kinds")
        self._validate("wontfix", ["area:core", "bug"], rules=rules)

    def test_without_axes_no_axis_is_required(self):
        rules = _rules_without("axes")
        self._validate("bug", ["perf"], rules=rules)

    def test_without_a_schema_only_the_registry_is_checked(self):
        rules = labels.LabelRules(fixture.missing())
        self._validate("wontfix", [], rules=rules)
        _refused(self, self._validate, "ghost", [], _REGISTRY, rules,
                 fragment="registry")


class ValidateLabelAdditionTest(unittest.TestCase):
    def _validate(self, label, current, rules=_RULES):
        labels.validate_label_addition(label, current, _REGISTRY, rules)

    def test_label_absent_from_registry_is_refused_naming_the_sync_path(self):
        rules = _rules_without("issue_priorities")  # so only the registry decides
        _refused(self, self._validate, "nope", ["bug"], rules,
                 fragment="ghw-label-sync")

    def test_an_undeclared_live_label_is_refused(self):
        _refused(self, self._validate, "wontfix", ["bug"],
                 fragment="not declared")

    def test_second_kind_names_the_incumbent(self):
        message = _refused(self, self._validate, "chore", ["bug", "area:core"])
        self.assertIn("'bug'", message)
        self.assertIn("remove-label", message)

    def test_re_adding_the_incumbent_kind_passes(self):
        self._validate("bug", ["bug", "area:core"])

    def test_first_kind_passes(self):
        self._validate("bug", ["area:core"])

    def test_non_kind_label_passes_alongside_a_kind(self):
        self._validate("perf", ["bug"])


class ValidateLabelRemovalTest(unittest.TestCase):
    def test_the_last_label_of_a_required_axis_cannot_be_removed(self):
        _refused(self, labels.validate_label_removal, "area:core",
                 ["bug", "area:core", "site:a"], _RULES,
                 fragment="last 'area:' label")

    def test_one_of_several_on_a_required_axis_can_be_removed(self):
        labels.validate_label_removal("area:core",
                                      ["bug", "area:core", "area:docs"], _RULES)

    def test_labels_off_a_required_axis_and_the_kind_can_be_removed(self):
        for label in ("site:a", "perf", "bug"):
            with self.subTest(label=label):
                labels.validate_label_removal(
                    label, ["bug", "area:core", "site:a", "perf"], _RULES)

    def test_without_axes_any_label_can_be_removed(self):
        labels.validate_label_removal("area:core", ["area:core"],
                                      _rules_without("axes"))


if __name__ == "__main__":
    unittest.main()
