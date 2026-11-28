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
        elif section == "unaxed":
            document["issue_label_schema"]["labels"] = {}
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
    _DECLARED = ("task", "bug", "chore", "P0", "P1", "P4", "area:core",
                 "area:docs", "site:a", "human", "perf", "Needs Triage",
                 "In progress", "Closed")

    def test_reads_the_kinds_the_declared_labels_and_the_required_axes(self):
        self.assertEqual(_RULES.kinds, {"task", "bug", "chore"})
        for name in self._DECLARED:
            with self.subTest(name=name):
                self.assertIs(_RULES.is_declared(name), True)
        self.assertIs(_RULES.is_declared("wontfix"), False)
        self.assertEqual([axis.name for axis in _RULES.required_axes], ["area"])
        self.assertEqual(_RULES.unchecked(), [])

    def test_no_schema_checks_nothing_and_says_so(self):
        rules = labels.LabelRules(fixture.missing())
        self.assertIsNone(rules.kinds)
        self.assertIsNone(rules.is_declared("wontfix"))
        self.assertIsNone(rules.required_axes)
        self.assertEqual(len(rules.unchecked()), 3)

    def test_one_unusable_section_leaves_only_unplaceable_names_unverified(self):
        rules = _rules_without("issue_priorities")
        self.assertEqual(rules.kinds, {"task", "bug", "chore"})
        # A name with a usable axis's prefix is judged on that axis alone.
        self.assertIs(rules.is_declared("area:bogus"), False)
        self.assertIs(rules.is_declared("area:core"), True)
        # A bare name might be a priority, which cannot be read.
        self.assertIsNone(rules.is_declared("stray"))
        self.assertEqual(len(rules.unchecked()), 1)
        self.assertIn("issue_priorities", rules.unchecked()[0])

    def test_unusable_unaxed_labels_do_not_admit_a_bad_axis_label(self):
        rules = _rules_without("unaxed")
        _refused(self, labels.validate_creation_labels, "bug", ["area:bogus"],
                 _REGISTRY | {"area:bogus"}, rules, fragment="'area:bogus'")

    def test_a_label_named_for_an_issue_state_is_declared(self):
        labels.validate_label_addition("Needs Triage", ["bug", "area:core"],
                                       _REGISTRY | {"Needs Triage"}, _RULES)

    def test_a_kind_is_checked_whenever_the_kinds_can_be_read(self):
        rules = _rules_without("axes", "issue_priorities")
        _refused(self, labels.validate_creation_labels, "feature", [],
                 _REGISTRY | {"feature"}, rules, fragment="not an Issue Kind")


class UncarriableNameTest(unittest.TestCase):
    """gh splits label lists on commas and reads a leading '-' as an option,
    so such a name never reaches a gh argument, declared or not."""

    def _declaring(self, name):
        document = fixture.document()
        document["issue_label_schema"]["labels"].append(
            {"name": name, "meaning": "Odd", "color": "ededed"})
        return labels.LabelRules(fixture.loaded(document))

    def test_reasons(self):
        self.assertIn("comma", labels.uncarriable_reason("x,bug"))
        self.assertIn("'-'", labels.uncarriable_reason("-x"))
        self.assertIsNone(labels.uncarriable_reason("area:core"))

    def test_a_declared_comma_name_cannot_smuggle_a_second_kind(self):
        rules = self._declaring("x,bug")
        registry = _REGISTRY | {"x,bug"}
        _refused(self, labels.validate_label_addition, "x,bug",
                 ["task", "area:core"], registry, rules, fragment="comma")
        _refused(self, labels.validate_creation_labels, "task",
                 ["area:core", "x,bug"], registry, rules, fragment="comma")

    def test_a_leading_dash_is_refused_on_every_path(self):
        rules = self._declaring("-x")
        registry = _REGISTRY | {"-x"}
        _refused(self, labels.validate_label_addition, "-x", ["bug"],
                 registry, rules, fragment="'-'")
        _refused(self, labels.validate_label_removal, "-x", ["bug", "-x"],
                 rules, fragment="'-'")
        _refused(self, labels.validate_creation_labels, "-x", ["area:core"],
                 registry, labels.LabelRules(fixture.missing()), fragment="'-'")


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
                 fragment="duplicates the Kind Label")

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
