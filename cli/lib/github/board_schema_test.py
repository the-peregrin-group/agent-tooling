"""Unit tests for board_schema.py (canonical-schema conformance and provisioning).

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

if __package__ in (None, ""):  # direct invocation: python3 lib/board_schema_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.github import board_schema
from lib.schema import (
    CANONICAL_FIELDS,
    PRIORITY_OPTIONS,
    SINGLE_SELECT,
    SIZE_OPTIONS,
    STATUS_STATES,
)


def _single_select(options) -> dict:
    return {"id": "F", "data_type": "SINGLE_SELECT",
            "options": {option: f"opt_{option}" for option in options}}


_FIELD_NAMES = {"priority": "Priority", "status": "Status", "size": "Size",
                "last_triaged": "Last Triaged"}


def _canonical_board(**overrides) -> dict:
    """A board conforming to the canonical schema, before any overrides.

    Override keys are the lowercased field names in _FIELD_NAMES; a value of
    None drops that field entirely.
    """
    fields = {
        "Priority": _single_select(PRIORITY_OPTIONS),
        "Status": _single_select(STATUS_STATES),
        "Size": _single_select(SIZE_OPTIONS),
        "Last Triaged": {"id": "F", "data_type": "DATE", "options": {}},
    }
    for key, value in overrides.items():
        field_name = _FIELD_NAMES[key]
        if value is None:
            fields.pop(field_name)
        else:
            fields[field_name] = value
    return {"number": 1, "title": "Board", "node_id": "PVT_1", "fields": fields}


class EvaluateConformanceTest(unittest.TestCase):
    def test_canonical_board_conforms_with_no_gaps(self):
        verdict = board_schema.evaluate_conformance(_canonical_board())
        self.assertTrue(verdict["conforms"])
        self.assertEqual(verdict["gaps"], [])
        self.assertEqual(verdict["tolerated_gaps"], [])

    def test_missing_last_triaged_is_a_hard_gap(self):
        verdict = board_schema.evaluate_conformance(_canonical_board(last_triaged=None))
        self.assertFalse(verdict["conforms"])
        self.assertIn("'Last Triaged' is missing", verdict["gaps"][0])

    def test_missing_size_is_tolerated_and_does_not_clear_conformance(self):
        verdict = board_schema.evaluate_conformance(_canonical_board(size=None))
        self.assertTrue(verdict["conforms"])
        self.assertEqual(verdict["gaps"], [])
        self.assertIn("'Size' is missing", verdict["tolerated_gaps"][0])

    def test_missing_status_states_are_named_individually(self):
        # A typical stock board, never triage-provisioned.
        stock = _canonical_board(status=_single_select(["Todo", "In Progress", "Done"]))
        verdict = board_schema.evaluate_conformance(stock)
        self.assertFalse(verdict["conforms"])
        missing = next(gap for gap in verdict["gaps"] if "missing options" in gap)
        self.assertIn("Needs Triage", missing)
        self.assertIn("In progress", missing)  # exact casing: not "In Progress"
        self.assertNotIn("Done", missing)      # Done is canonical and present

    def test_extra_options_are_reported_apart_from_gaps(self):
        stock = _canonical_board(status=_single_select(["Todo", "In Progress", "Done"]))
        verdict = board_schema.evaluate_conformance(stock)
        self.assertEqual(verdict["gaps"],
                         [gap for gap in verdict["gaps"] if "missing" in gap])
        extra = " ".join(verdict["extra_options"])
        self.assertIn("Todo", extra)
        self.assertIn("In Progress", extra)

    def test_a_human_authored_extra_state_does_not_clear_conformance(self):
        # The wrappers only ever write canonical option names, so a board
        # carrying an extra 'Blocked' state still serves triage fine.
        board = _canonical_board(
            status=_single_select([*STATUS_STATES, "Blocked"])
        )
        verdict = board_schema.evaluate_conformance(board)
        self.assertTrue(verdict["conforms"])
        self.assertEqual(verdict["gaps"], [])
        self.assertIn("Blocked", verdict["extra_options"][0])

    def test_wrong_data_type_is_a_gap_and_skips_option_checks(self):
        board = _canonical_board(
            priority={"id": "F", "data_type": "TEXT", "options": {}}
        )
        verdict = board_schema.evaluate_conformance(board)
        priority_gaps = [gap for gap in verdict["gaps"] if "'Priority'" in gap]
        self.assertEqual(len(priority_gaps), 1)
        self.assertIn("is TEXT, not SINGLE_SELECT", priority_gaps[0])

    def test_a_board_with_no_fields_at_all_reports_every_canonical_field(self):
        verdict = board_schema.evaluate_conformance(
            {"number": 1, "title": "Empty", "node_id": "PVT_1", "fields": {}}
        )
        reported = " ".join(verdict["gaps"] + verdict["tolerated_gaps"])
        for field_name in CANONICAL_FIELDS:
            self.assertIn(repr(field_name), reported)


class FieldsToCreateTest(unittest.TestCase):
    def test_conforming_board_needs_nothing(self):
        self.assertEqual(
            board_schema.fields_to_create(_canonical_board(), new_board=False), []
        )

    def test_size_is_never_created_on_an_existing_board(self):
        board = _canonical_board(size=None)
        self.assertEqual(board_schema.fields_to_create(board, new_board=False), [])

    def test_size_is_created_on_a_new_board(self):
        board = _canonical_board(size=None)
        self.assertEqual(
            board_schema.fields_to_create(board, new_board=True), ["Size"]
        )

    def test_absent_fields_come_back_in_canonical_order(self):
        board = {"number": 1, "title": "Empty", "node_id": "PVT_1", "fields": {}}
        self.assertEqual(
            board_schema.fields_to_create(board, new_board=True),
            list(CANONICAL_FIELDS),
        )

    def test_drifted_field_is_never_queued_for_creation(self):
        # Drift is reported, never edited: creating over it would be an edit.
        board = _canonical_board(status=_single_select(["Todo"]))
        self.assertNotIn(
            "Status", board_schema.fields_to_create(board, new_board=True)
        )


class SingleSelectOptionsTest(unittest.TestCase):
    def test_status_options_are_the_canonical_states_in_order(self):
        options = board_schema.single_select_options("Status")
        self.assertEqual([option["name"] for option in options],
                         list(STATUS_STATES))

    def test_every_color_is_a_valid_api_enum_value(self):
        # boards._options_literal refuses anything outside the enum, so a typo
        # here would only surface as a runtime GraphQL failure.
        from lib.github.boards import _OPTION_COLOR_VALUES
        for field_name, specification in board_schema.FIELD_SPECS.items():
            if specification["data_type"] != SINGLE_SELECT:
                continue
            for option in board_schema.single_select_options(field_name):
                with self.subTest(field=field_name, option=option["name"]):
                    self.assertIn(option["color"], _OPTION_COLOR_VALUES)

    def test_a_non_single_select_field_has_no_options(self):
        self.assertEqual(board_schema.single_select_options("Last Triaged"), [])

    def test_descriptions_are_empty_by_design(self):
        for option in board_schema.single_select_options("Priority"):
            self.assertEqual(option["description"], "")


class OptionColorGuardTest(unittest.TestCase):
    """_OPTION_COLORS duplicates lib.schema's option names, so the import-time
    guard is what keeps a rename there from silently degrading the colors
    here. Asserting on the guard directly, since single_select_options()
    indexes the map and would only ever show post-lookup values."""

    def test_the_shipped_map_passes_its_own_guard(self):
        board_schema._check_option_colors()  # no raise

    def test_a_renamed_option_is_caught_as_missing(self):
        doctored = {**board_schema._OPTION_COLORS,
                    "Priority": {"P0": "RED", "P1": "ORANGE", "P2": "YELLOW"}}
        with mock.patch.object(board_schema, "_OPTION_COLORS", doctored):
            with self.assertRaisesRegex(RuntimeError, "P3"):
                board_schema._check_option_colors()

    def test_a_stale_key_is_caught_too(self):
        doctored = {**board_schema._OPTION_COLORS,
                    "Priority": {**board_schema._OPTION_COLORS["Priority"],
                                 "P9": "PINK"}}
        with mock.patch.object(board_schema, "_OPTION_COLORS", doctored):
            with self.assertRaisesRegex(RuntimeError, "P9"):
                board_schema._check_option_colors()


if __name__ == "__main__":
    unittest.main()
