"""Unit tests for board_schema.py: the colour rule, the fields a Tracker
Schema asks for, conformance, and the option and migration plans. Pure
functions; no network.

The schema is tracker_schema_test_support's fixture, whose states and
priorities are not the shipped default's, so nothing here leans on a name
ghw used to hold as a constant.

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
from lib.github import board_schema
from lib.github.repo_schema import RepoSchema

_DEFAULT = (Path(__file__).resolve().parents[3]
            / "skills" / "setup-issue-tracker" / "TRACKER.default.md")

STATES = ("Needs Triage", "In progress", "Closed")
PRIORITIES = ("P0", "P1", "P4")
SIZES = ("XS", "S", "M", "L", "XL")


def _field(names, colors=None, data_type="SINGLE_SELECT", field_id="F"):
    """A live board field as lib.github.boards builds one."""
    colors = colors or {}
    return {
        "id": field_id, "data_type": data_type,
        "options": {name: f"o_{name}" for name in names},
        "option_details": [
            {"id": f"o_{name}", "name": name, "color": colors.get(name, "GRAY"),
             "description": f"about {name}"}
            for name in names
        ],
    }


def _board(status=STATES, priority=PRIORITIES, size=SIZES, last_triaged=True,
           status_colors=None, priority_colors=None):
    fields = {}
    if priority is not None:
        fields["Priority"] = _field(priority, priority_colors or {
            "P0": "RED", "P1": "ORANGE", "P4": "GRAY"}, field_id="F_priority")
    if status is not None:
        fields["Status"] = _field(status, status_colors or {
            "Needs Triage": "RED", "In progress": "PURPLE", "Closed": "GRAY"},
            field_id="F_status")
    if size is not None:
        fields["Size"] = _field(size, field_id="F_size")
    if last_triaged:
        fields["Last Triaged"] = {"id": "F_date", "data_type": "DATE",
                                  "options": {}, "option_details": []}
    return {"number": 1, "title": "Board", "node_id": "PVT_1", "fields": fields}


def _fields(document=None):
    return board_schema.desired_fields(fixture.loaded(document))


def _spec(name, document=None):
    return next(spec for spec in _fields(document) if spec.name == name)


class NamedColorTest(unittest.TestCase):
    def test_the_shipped_defaults_colours_land_on_the_board_colours(self):
        # The default's colours were chosen to read as the names the board
        # options carried before the board followed the schema. Closed is
        # new (it replaces Done and Rejected) and P4 is not in the default.
        schema = tracker_schema.load(_DEFAULT)
        expected = {
            "Needs Triage": "RED", "Needs Scope": "ORANGE",
            "Needs Eng Design": "YELLOW", "Needs Impl": "BLUE",
            "In progress": "PURPLE", "In review": "PINK", "Closed": "GRAY",
            "P0": "RED", "P1": "ORANGE", "P2": "YELLOW", "P3": "GREEN",
        }
        got = {entry.name: board_schema.named_color(entry.color)
               for entry in schema.issue_states + schema.issue_priorities}
        self.assertEqual(got, expected)

    def test_low_chroma_is_gray_whatever_its_lightness(self):
        for color in ("000000", "ffffff", "6a737d", "cfd3d7", "808080"):
            with self.subTest(color=color):
                self.assertEqual(board_schema.named_color(color), "GRAY")

    def test_very_pale_and_very_dark_tints_are_gray(self):
        # Chroma is the absolute channel spread, so a tint near white or
        # black has too little of it to name, whatever its hue.
        for color, name in {"ffdddd": "GRAY", "ddffdd": "GRAY",
                            "e0e0ff": "GRAY", "c2e0c6": "GRAY",
                            "1a0000": "GRAY", "e99695": "RED",
                            "330000": "RED"}.items():
            with self.subTest(color=color):
                self.assertEqual(board_schema.named_color(color), name)

    def test_hue_picks_the_nearest_name_around_the_wheel(self):
        cases = {"ff0000": "RED", "ff1a00": "RED", "ff00e6": "PINK",
                 "ffa500": "ORANGE", "ffff00": "YELLOW", "00ff00": "GREEN",
                 "0000ff": "BLUE", "8000ff": "PURPLE", "D73A4A": "RED"}
        for color, name in cases.items():
            with self.subTest(color=color):
                self.assertEqual(board_schema.named_color(color), name)

    def test_every_result_is_one_of_the_eight(self):
        for value in range(0, 0xffffff, 0x0f0f0f):
            self.assertIn(board_schema.named_color(f"{value:06x}"),
                          board_schema.NAMED_COLORS)

    def test_no_colour_maps_to_none(self):
        for color in (None, "", "#d73a4a", "red", "12345"):
            with self.subTest(color=color):
                self.assertIsNone(board_schema.named_color(color))


class DesiredFieldsTest(unittest.TestCase):
    def test_options_are_the_schemas_states_and_priorities_in_order(self):
        self.assertEqual([option.name for option in _spec("Status").options],
                         list(STATES))
        self.assertEqual([option.name for option in _spec("Priority").options],
                         list(PRIORITIES))
        self.assertEqual([option.color for option in _spec("Priority").options],
                         ["RED", "ORANGE", "GRAY"])

    def test_size_and_last_triaged_are_fixed(self):
        self.assertEqual([option.name for option in _spec("Size").options],
                         list(SIZES))
        self.assertIsNone(_spec("Size").section)
        self.assertEqual(_spec("Last Triaged").options, ())

    def test_an_unusable_section_leaves_its_options_unknown(self):
        document = fixture.document()
        document["issue_states"] = "none"
        self.assertIsNone(_spec("Status", document).options)
        self.assertIsNotNone(_spec("Priority", document).options)

    def test_no_schema_leaves_both_unknown(self):
        fields = board_schema.desired_fields(fixture.missing())
        by_name = {spec.name: spec for spec in fields}
        self.assertIsNone(by_name["Status"].options)
        self.assertIsNone(by_name["Priority"].options)

    def test_any_state_name_and_a_missing_colour_are_fine(self):
        # Nothing is checked at import time, so a name ghw has never seen,
        # or a state with no colour, is simply an option.
        document = fixture.document()
        document["issue_states"][1] = {"name": "Blocked on vendor", "open": True}
        options = _spec("Status", document).options
        self.assertEqual(options[1], board_schema.DesiredOption(
            "Blocked on vendor", None))


class ConformanceTest(unittest.TestCase):
    def _verdict(self, board, document=None, loaded: RepoSchema = None):
        fields = board_schema.desired_fields(loaded or fixture.loaded(document))
        return board_schema.evaluate_conformance(board, fields)

    def test_a_board_holding_exactly_the_schema_conforms(self):
        verdict = self._verdict(_board())
        self.assertIs(verdict["conforms"], True)
        self.assertEqual(verdict["gaps"], [])
        self.assertEqual(verdict["color_drift"], [])

    def test_a_missing_declared_option_is_a_gap(self):
        verdict = self._verdict(_board(status=("Needs Triage", "Closed")))
        self.assertIs(verdict["conforms"], False)
        self.assertIn("'Status' is missing options: In progress", verdict["gaps"][0])

    def test_an_undeclared_option_is_a_gap(self):
        verdict = self._verdict(_board(status=(*STATES, "Done", "Rejected")))
        self.assertIs(verdict["conforms"], False)
        self.assertIn("does not declare: Done, Rejected", " ".join(verdict["gaps"]))

    def test_options_out_of_order_are_a_gap(self):
        verdict = self._verdict(_board(priority=("P1", "P0", "P4")))
        self.assertIn("out of the Tracker Schema's order", " ".join(verdict["gaps"]))

    def test_colour_drift_is_listed_but_does_not_clear_the_verdict(self):
        verdict = self._verdict(_board(priority_colors={
            "P0": "RED", "P1": "YELLOW", "P4": "GRAY"}))
        self.assertIs(verdict["conforms"], True)
        self.assertIn("'P1' is YELLOW", verdict["color_drift"][0])

    def test_size_is_tolerated_missing_and_its_extras_are_advisory(self):
        verdict = self._verdict(_board(size=None))
        self.assertIs(verdict["conforms"], True)
        self.assertIn("'Size' is missing", verdict["tolerated_gaps"][0])
        verdict = self._verdict(_board(size=(*SIZES, "XXL")))
        self.assertIs(verdict["conforms"], True)
        self.assertIn("XXL", verdict["extra_options"][0])

    def test_a_missing_field_and_a_wrong_type_are_gaps(self):
        board = _board(last_triaged=False)
        board["fields"]["Priority"]["data_type"] = "TEXT"
        gaps = " ".join(self._verdict(board)["gaps"])
        self.assertIn("'Last Triaged' is missing", gaps)
        self.assertIn("'Priority' is TEXT", gaps)

    def test_unknown_options_are_unchecked_and_the_verdict_unknown(self):
        verdict = self._verdict(_board(status=("Anything",)),
                                loaded=fixture.missing())
        self.assertIsNone(verdict["conforms"])
        self.assertEqual(len(verdict["unchecked"]), 2)

    def test_a_gap_outweighs_an_unchecked_field(self):
        verdict = self._verdict(_board(last_triaged=False),
                                loaded=fixture.missing())
        self.assertIs(verdict["conforms"], False)

    def test_a_board_without_option_details_is_still_judged(self):
        board = _board()
        for field in board["fields"].values():
            field.pop("option_details")
        self.assertIs(self._verdict(board)["conforms"], True)


class DuplicateConformanceTest(unittest.TestCase):
    def test_two_options_of_one_name_are_a_gap(self):
        board = _board()
        board["fields"]["Status"]["option_details"].append(
            {"id": "o_dup", "name": "Closed", "color": "GRAY", "description": ""})
        verdict = board_schema.evaluate_conformance(board, _fields())
        self.assertFalse(verdict["conforms"])
        self.assertIn("more than one option named: Closed",
                      " ".join(verdict["gaps"]))


class FieldsToCreateTest(unittest.TestCase):
    def test_existing_board_leaves_size_to_a_person(self):
        board = _board(priority=None, size=None, last_triaged=False)
        created = board_schema.fields_to_create(board, _fields(), new_board=False)
        self.assertEqual([spec.name for spec in created],
                         ["Priority", "Last Triaged"])

    def test_new_board_gets_size(self):
        board = _board(priority=None, size=None, last_triaged=False)
        created = board_schema.fields_to_create(board, _fields(), new_board=True)
        self.assertEqual([spec.name for spec in created],
                         ["Priority", "Size", "Last Triaged"])

    def test_a_field_whose_options_are_unknown_is_not_created(self):
        board = _board(priority=None, status=None)
        fields = board_schema.desired_fields(fixture.missing())
        self.assertEqual(
            board_schema.fields_to_create(board, fields, new_board=True), [])

    def test_creation_options_fall_back_to_the_neutral_colour(self):
        document = fixture.document()
        del document["issue_priorities"][1]["color"]
        options = board_schema.creation_options(_spec("Priority", document))
        self.assertEqual(options, [
            {"name": "P0", "color": "RED", "description": ""},
            {"name": "P1", "color": board_schema.NEUTRAL_COLOR, "description": ""},
            {"name": "P4", "color": "GRAY", "description": ""},
        ])


class PlanFieldTest(unittest.TestCase):
    def _plan(self, live, name="Status", document=None):
        return board_schema.plan_field(_spec(name, document), live)

    def test_a_converged_field_plans_nothing(self):
        plan = self._plan(_board()["fields"]["Status"])
        self.assertIsNone(plan.additive)
        self.assertEqual((plan.add, plan.remove, plan.recolor, plan.reorder),
                         ([], [], [], False))
        self.assertFalse(plan.destructive)

    def test_the_additive_list_keeps_every_live_option_by_id(self):
        live = _field(("Done", "In progress", "Needs Triage", "Rejected"),
                      {"Done": "GREEN", "In progress": "PURPLE",
                       "Needs Triage": "RED", "Rejected": "GRAY"})
        plan = self._plan(live)
        self.assertEqual(plan.add, ["Closed"])
        self.assertEqual(plan.remove, ["Done", "Rejected"])
        self.assertTrue(plan.reorder)
        # Declared first, in the schema's order, the new one without an id;
        # then every undeclared live option, untouched, in board order.
        self.assertEqual(plan.additive, [
            {"id": "o_Needs Triage", "name": "Needs Triage", "color": "RED",
             "description": "about Needs Triage"},
            {"id": "o_In progress", "name": "In progress", "color": "PURPLE",
             "description": "about In progress"},
            {"name": "Closed", "color": "GRAY", "description": ""},
            {"id": "o_Done", "name": "Done", "color": "GREEN",
             "description": "about Done"},
            {"id": "o_Rejected", "name": "Rejected", "color": "GRAY",
             "description": "about Rejected"},
        ])
        self.assertEqual([entry["name"] for entry in plan.final], list(STATES))
        self.assertTrue(plan.destructive)
        live_ids = set(live["options"].values())
        self.assertTrue(live_ids <= {entry.get("id") for entry in plan.additive})

    def test_recolouring_keeps_the_id_and_description(self):
        live = _field(PRIORITIES, {"P0": "RED", "P1": "YELLOW", "P4": "GRAY"})
        plan = self._plan(live, "Priority")
        self.assertEqual(plan.recolor, [{"option": "P1", "from": "YELLOW",
                                         "to": "ORANGE"}])
        self.assertEqual(plan.additive[1], {"id": "o_P1", "name": "P1",
                                            "color": "ORANGE",
                                            "description": "about P1"})

    def test_a_missing_schema_colour_keeps_the_live_one(self):
        document = fixture.document()
        del document["issue_priorities"][1]["color"]
        live = _field(PRIORITIES, {"P0": "RED", "P1": "PINK", "P4": "GRAY"})
        plan = self._plan(live, "Priority", document)
        self.assertEqual(plan.recolor, [])
        self.assertIsNone(plan.additive)

    def test_a_second_option_of_a_declared_name_is_kept_by_id_and_removed_last(self):
        live = _field(STATES)
        live["option_details"].append({"id": "o_dup", "name": "Closed",
                                       "color": "GRAY", "description": ""})
        plan = self._plan(live)
        self.assertEqual(plan.removed, [{"id": "o_dup", "name": "Closed"}])
        self.assertEqual({entry["id"] for entry in plan.final},
                         {"o_Needs Triage", "o_In progress", "o_Closed"})
        # The additive list holds both copies, each by its own id.
        self.assertEqual([entry["id"] for entry in plan.additive][-2:],
                         ["o_Closed", "o_dup"])
        self.assertTrue(plan.destructive)

    def test_a_case_or_whitespace_variant_is_renamed_in_place(self):
        live = _field(("needs triage", "In progress", "Closed "))
        plan = self._plan(live)
        self.assertEqual(plan.add, [])
        self.assertEqual(plan.remove, [])
        self.assertEqual(plan.rename, [{"from": "needs triage", "to": "Needs Triage"},
                                       {"from": "Closed ", "to": "Closed"}])
        self.assertEqual([(entry["id"], entry["name"]) for entry in plan.additive],
                         [("o_needs triage", "Needs Triage"),
                          ("o_In progress", "In progress"),
                          ("o_Closed ", "Closed")])

    def test_an_exact_name_wins_over_a_variant(self):
        live = _field(("closed", "Needs Triage", "In progress", "Closed"))
        plan = self._plan(live)
        self.assertEqual(plan.rename, [])
        self.assertEqual(plan.remove, ["closed"])

    def test_nothing_is_planned_without_known_options_or_a_field(self):
        live = _board()["fields"]["Status"]
        loaded = fixture.missing()
        spec = next(spec for spec in board_schema.desired_fields(loaded)
                    if spec.name == "Status")
        self.assertIsNone(board_schema.plan_field(spec, live))
        self.assertIsNone(self._plan(None))
        self.assertIsNone(self._plan(_board()["fields"]["Size"], "Size"))


def _item(item_id, option, field_id="F_status", type_="Issue", state="CLOSED",
          number=1):
    return {"item_id": item_id, "archived": False,
            "content": {"type": type_, "number": number, "title": "t",
                        "url": f"https://github.com/o/r/issues/{number}",
                        "state": state},
            "values": {field_id: option} if option else {}}


class PlanMovesTest(unittest.TestCase):
    def setUp(self):
        self.live = _field((*STATES, "Done"), field_id="F_status")
        self.plan = board_schema.plan_field(_spec("Status"), self.live)
        self.states = fixture.loaded().schema.issue_states

    def _moves(self, items, moves=None, states=None):
        return board_schema.plan_moves(
            self.plan, self.live, items, moves or {},
            self.states if states is None else states)

    def test_a_closed_issue_moves_to_the_one_closed_state(self):
        result = self._moves([_item("I_1", "o_Done")])
        self.assertEqual(result[0]["option"], "Done")
        self.assertEqual(result[0]["items"][0]["to"], "Closed")
        self.assertEqual(result[0]["items"][0]["by"], "issue state")

    def test_a_merged_or_closed_pull_request_moves_the_same_way(self):
        for state in ("MERGED", "CLOSED"):
            with self.subTest(state=state):
                result = self._moves([_item("I_1", "o_Done", type_="PullRequest",
                                            state=state)])
                self.assertEqual(result[0]["items"][0]["to"], "Closed")

    def test_an_open_issue_has_no_target_among_several_open_states(self):
        result = self._moves([_item("I_1", "o_Done", state="OPEN")])
        self.assertIsNone(result[0]["items"][0]["to"])
        self.assertEqual(len(board_schema.unmoved(result)), 1)

    def test_a_draft_or_hidden_item_has_no_target(self):
        for type_ in ("DraftIssue", None):
            with self.subTest(type_=type_):
                result = self._moves([_item("I_1", "o_Done", type_=type_,
                                            state=None)])
                self.assertIsNone(result[0]["items"][0]["to"])

    def test_two_closed_states_give_no_target(self):
        document = fixture.document()
        document["issue_states"].append(
            {"name": "Wontfix", "open": False, "color": "ffffff"})
        states = fixture.loaded(document).schema.issue_states
        result = self._moves([_item("I_1", "o_Done")], states=states)
        self.assertIsNone(result[0]["items"][0]["to"])

    def test_a_single_open_state_takes_open_issues(self):
        document = fixture.document()
        del document["issue_states"][1]
        states = fixture.loaded(document).schema.issue_states
        result = self._moves([_item("I_1", "o_Done", state="OPEN")], states=states)
        self.assertEqual(result[0]["items"][0]["to"], "Needs Triage")

    def test_a_named_move_wins_for_every_item_on_the_option(self):
        result = self._moves([_item("I_1", "o_Done"),
                              _item("I_2", "o_Done", state="OPEN")],
                             moves={"Done": "In progress"})
        self.assertEqual([item["to"] for item in result[0]["items"]],
                         ["In progress", "In progress"])
        self.assertEqual(result[0]["items"][0]["by"], "named")

    def test_items_on_kept_options_or_no_option_are_not_moved(self):
        result = self._moves([_item("I_1", "o_Closed"), _item("I_2", None),
                              _item("I_3", "o_Done", field_id="F_other")])
        self.assertEqual(result, [{"option": "Done", "option_id": "o_Done",
                                   "items": []}])

    def test_items_on_a_second_option_of_a_declared_name_move_to_it(self):
        live = _field(PRIORITIES, field_id="F_priority")
        live["option_details"].append({"id": "o_dup", "name": "P1",
                                       "color": "GRAY", "description": ""})
        plan = board_schema.plan_field(_spec("Priority"), live)
        result = board_schema.plan_moves(
            plan, live, [_item("I_1", "o_dup", field_id="F_priority"),
                         _item("I_2", "o_P1", field_id="F_priority")], {},
            self.states)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["option_id"], "o_dup")
        self.assertEqual([(item["item_id"], item["to"], item["by"])
                          for item in result[0]["items"]],
                         [("I_1", "P1", "same name")])

    def test_priority_has_no_issue_state_rule(self):
        live = _field((*PRIORITIES, "P2"), field_id="F_priority")
        plan = board_schema.plan_field(_spec("Priority"), live)
        result = board_schema.plan_moves(
            plan, live, [_item("I_1", "o_P2", field_id="F_priority")], {},
            self.states)
        self.assertIsNone(result[0]["items"][0]["to"])


if __name__ == "__main__":
    unittest.main()
