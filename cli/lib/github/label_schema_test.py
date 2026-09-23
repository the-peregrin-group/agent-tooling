"""Unit tests for label_schema.py (ghw-label-sync's desired state and diff).

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

if __package__ in (None, ""):  # direct invocation: python3 lib/label_schema_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.github import label_schema
from lib.schema import AREA_LABEL_COLOR, SCOPE_LABEL_COLOR, TYPE_LABELS

_MINIMAL = {"area": [{"name": "core", "description": "Core engine"}]}


def _parse(document: dict) -> dict:
    return label_schema.parse_schema(json.dumps(document))


def _refuses(test: unittest.TestCase, document: dict, why_fragment: str):
    with test.assertRaises(label_schema.SchemaFileError) as caught:
        _parse(document)
    test.assertIn(why_fragment, str(caught.exception))


class ParseSchemaTest(unittest.TestCase):
    def test_minimal_file_fills_in_defaults(self):
        schema = _parse(_MINIMAL)
        self.assertFalse(schema["priority_labels"])
        self.assertEqual(schema["scope"], [])
        self.assertEqual(schema["area"][0]["color"], AREA_LABEL_COLOR)

    def test_scope_family_defaults_to_its_own_color(self):
        schema = _parse({**_MINIMAL,
                         "scope": [{"name": "site-a", "description": "Site A"}]})
        self.assertEqual(schema["scope"][0]["color"], SCOPE_LABEL_COLOR)

    def test_explicit_color_is_normalized(self):
        schema = _parse({"area": [{"name": "core", "description": "Core",
                                   "color": "#A2EEEF"}]})
        self.assertEqual(schema["area"][0]["color"], "a2eeef")

    def test_invalid_json_reports_position_without_echoing_content(self):
        with self.assertRaises(label_schema.SchemaFileError) as caught:
            label_schema.parse_schema('{"area": [ "secret-token",,')
        message = str(caught.exception)
        self.assertIn("not valid JSON", message)
        self.assertNotIn("secret-token", message)

    def test_non_object_document_is_refused(self):
        with self.assertRaises(label_schema.SchemaFileError):
            label_schema.parse_schema("[]")

    def test_unknown_top_level_key_is_refused_listing_the_allowed_ones(self):
        _refuses(self, {**_MINIMAL, "areas": []}, "unknown top-level key")

    def test_unknown_entry_key_is_refused(self):
        _refuses(self, {"area": [{"name": "core", "description": "C",
                                  "colour": "bfdadc"}]}, "unknown key")

    def test_area_family_is_required_and_non_empty(self):
        _refuses(self, {"scope": [{"name": "site-a", "description": "A"}]},
                 "at least one")

    def test_prefixed_area_name_is_refused_with_the_bare_name(self):
        _refuses(self, {"area": [{"name": "area:core", "description": "C"}]},
                 "'core'")

    def test_canonical_type_label_in_a_family_is_refused(self):
        _refuses(self, {**_MINIMAL,
                        "scope": [{"name": "bug", "description": "no"}]},
                 "canonical label")

    def test_priority_label_in_a_family_points_at_the_flag(self):
        _refuses(self, {**_MINIMAL,
                        "scope": [{"name": "P0", "description": "no"}]},
                 "priority_labels")

    def test_missing_description_is_refused(self):
        _refuses(self, {"area": [{"name": "core"}]}, "'description' is required")

    def test_blank_description_is_refused(self):
        _refuses(self, {"area": [{"name": "core", "description": "  "}]},
                 "'description' is required")

    def test_bad_color_is_refused_with_an_example(self):
        _refuses(self, {"area": [{"name": "core", "description": "C",
                                  "color": "red"}]}, "6 hex digits")

    def test_name_with_surrounding_whitespace_is_refused(self):
        _refuses(self, {"area": [{"name": " core ", "description": "C"}]},
                 "whitespace")

    def test_comma_in_a_name_is_refused(self):
        # gh's --label/--add-label flags split on commas, so a comma label
        # could never be attached by ghw-issue-create or ghw-issue-edit.
        _refuses(self, {"area": [{"name": "core, extra", "description": "C"}]},
                 "comma")

    def test_leading_dash_in_a_name_is_refused(self):
        # It reaches `gh label create` as a flag-looking positional.
        _refuses(self, {"area": [{"name": "-core", "description": "C"}]},
                 "start with '-'")

    def test_entry_that_is_not_an_object_is_refused_by_position(self):
        _refuses(self, {"area": ["core"]}, "entry 1")

    def test_family_that_is_not_a_list_is_refused(self):
        _refuses(self, {"area": {"core": "Core"}}, "must be a list")

    def test_non_boolean_priority_flag_is_refused(self):
        _refuses(self, {**_MINIMAL, "priority_labels": "yes"}, "true or false")

    def test_duplicate_name_within_a_family_is_refused(self):
        _refuses(self, {"area": [{"name": "core", "description": "C"},
                                 {"name": "core", "description": "C again"}]},
                 "declared twice")

    def test_area_and_scope_cannot_collide_after_prefixing(self):
        # 'area:core' vs a scope label literally named 'area:core' -- the
        # prefixed form is what lands on the repo, so the clash is real.
        _refuses(self, {"area": [{"name": "core", "description": "C"}],
                        "scope": [{"name": "area:core", "description": "C"}]},
                 "prefix")


class DesiredLabelsTest(unittest.TestCase):
    def test_type_labels_are_always_present_from_the_shared_constants(self):
        desired = label_schema.desired_labels(_parse(_MINIMAL))
        for name, attributes in TYPE_LABELS.items():
            self.assertEqual(desired[name]["color"], attributes["color"])

    def test_area_names_are_prefixed_and_scope_names_are_not(self):
        desired = label_schema.desired_labels(_parse(
            {**_MINIMAL, "scope": [{"name": "site-a", "description": "Site A"}]}
        ))
        self.assertIn("area:core", desired)
        self.assertIn("site-a", desired)
        self.assertNotIn("core", desired)

    def test_priority_labels_are_omitted_by_default(self):
        self.assertNotIn("P0", label_schema.desired_labels(_parse(_MINIMAL)))

    def test_priority_labels_flag_adds_the_canonical_four(self):
        desired = label_schema.desired_labels(
            _parse({**_MINIMAL, "priority_labels": True})
        )
        for name in ("P0", "P1", "P2", "P3"):
            self.assertIn(name, desired)


class DiffLabelsTest(unittest.TestCase):
    def setUp(self):
        self.desired = {
            "bug": {"color": "d73a4a", "description": "Broken"},
            "area:core": {"color": "bfdadc", "description": "Core engine"},
        }

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
        desired = {"x": {"color": "ffffff", "description": ""}}
        existing = [{"name": "x", "color": "ffffff", "description": None}]
        self.assertEqual(label_schema.diff_labels(desired, existing)["update"], [])

    def test_undeclared_labels_are_deletion_candidates(self):
        existing = [{"name": "wontfix", "color": "ffffff", "description": ""},
                    {"name": "duplicate", "color": "cfd3d7", "description": ""}]
        self.assertEqual(
            label_schema.diff_labels(self.desired, existing)["delete"],
            ["duplicate", "wontfix"],
        )

    def test_case_only_difference_is_never_create_plus_delete(self):
        # GitHub's label namespace is case-insensitive, so planning a create
        # for 'bug' against a live 'Bug' would 422 as already-existing on
        # every single run.
        existing = [{"name": "Bug", "color": "d73a4a", "description": "Broken"}]
        difference = label_schema.diff_labels({"bug": self.desired["bug"]},
                                              existing)
        self.assertEqual(difference["create"], [])
        self.assertEqual(difference["delete"], [])
        self.assertEqual(difference["unchanged"], ["Bug"])

    def test_case_only_difference_is_reported(self):
        existing = [{"name": "Bug", "color": "d73a4a", "description": "Broken"}]
        difference = label_schema.diff_labels({"bug": self.desired["bug"]},
                                              existing)
        self.assertEqual(difference["case_mismatch"],
                         [{"live": "Bug", "desired": "bug"}])

    def test_matching_names_exactly_report_no_case_mismatch(self):
        existing = [{"name": "bug", "color": "d73a4a", "description": "Broken"}]
        self.assertEqual(
            label_schema.diff_labels({"bug": self.desired["bug"]},
                                     existing)["case_mismatch"],
            [],
        )

    def test_update_targets_the_live_spelling(self):
        # `gh label edit` has to name the label as it actually exists.
        existing = [{"name": "Bug", "color": "000000", "description": "Broken"}]
        update = label_schema.diff_labels({"bug": self.desired["bug"]},
                                          existing)["update"][0]
        self.assertEqual(update["name"], "Bug")
        self.assertEqual(update["color"], "d73a4a")


if __name__ == "__main__":
    unittest.main()
