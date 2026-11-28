"""Tests for the ghw-board-sync executable.

Argument tests run the script as a subprocess with arguments that fail before
any network I/O. Behavior tests load the script as a module and replace the
lib boards seam with FakeBoard, which keeps a board's options and items the
way GitHub's reference says updateProjectV2Field does: an option sent with
its id keeps its identity and its items' values, one sent without an id is
created, and one left out is removed and cleared from every item that held
it. The Tracker Schema is tracker_schema_test_support's fixture, or the
shipped default where a test says so. No `gh` calls are made.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

import ghw_test_support
import tracker_schema_test_support as fixture
from lib import tracker_schema
from lib.github import repo_schema

_SCRIPT = Path(__file__).resolve().parent / "ghw-board-sync"
_DEFAULT = (Path(__file__).resolve().parent.parent / "skills"
            / "setup-issue-tracker" / "TRACKER.default.md")
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)

STATES = ("Needs Triage", "In progress", "Closed")
PRIORITIES = ("P0", "P1", "P4")


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


def _default_schema() -> repo_schema.RepoSchema:
    return repo_schema.RepoSchema(
        "o/r", "main", tracker_schema.parse(_DEFAULT.read_text(encoding="utf-8")))


class FakeBoard:
    """One board with fields and items, behaving as GitHub's reference
    describes, and a log of every write in order.

    `fields` maps a name to (data_type, [(option, color)]); `items` are
    (item_id, issue state or None for a draft, {field: option}).
    `fail` maps a write's name to the call number (1-based) that raises a
    GhError instead of writing."""

    def __init__(self, fields, items=(), number=1):
        self.number = number
        self.node_id = f"PVT_{number}"
        self.serial = 0
        self.fields = {}
        for name, (data_type, options) in fields.items():
            self._add_field(name, data_type,
                            [{"name": option, "color": color, "description": ""}
                             for option, color in options])
        self.items = []
        for index, (item_id, state, values) in enumerate(items, start=1):
            self.items.append({
                "item_id": item_id,
                "archived": False,
                "content": {
                    "type": "Issue" if state else "DraftIssue",
                    "number": index if state else None,
                    "title": f"issue {item_id}",
                    "url": f"https://github.com/o/r/issues/{index}" if state else None,
                    "state": state,
                },
                "values": {self.fields[field]["id"]: self._option_id(field, option)
                           for field, option in values.items()},
            })
        self.log = []
        self.cleared = []   # (item_id, field, option) lost to a removal
        self.fail = {}
        self.calls = {}

    # --- what the tests look at ---------------------------------------------

    def option_names(self, field):
        return [option["name"] for option in self.fields[field]["options"]]

    def value(self, item_id, field):
        """The option name an item holds in `field`, or None."""
        item = next(item for item in self.items if item["item_id"] == item_id)
        option_id = item["values"].get(self.fields[field]["id"])
        for option in self.fields[field]["options"]:
            if option["id"] == option_id:
                return option["name"]
        return None

    # --- the seam -------------------------------------------------------------

    def fetch_boards(self, repository):
        return [self._board()]

    def fetch_board_by_node_id(self, node_id):
        assert node_id == self.node_id
        return {**self._board(), "url": f"https://github.com/orgs/o/projects/{self.number}"}

    def fetch_board_items(self, node_id):
        return copy.deepcopy(self.items)

    def create_field(self, node_id, name, data_type, options=None):
        self._maybe_fail("create_field")
        self._add_field(name, data_type, [dict(option) for option in options or ()])
        self.log.append(("create_field", name))
        return self.fields[name]["id"]

    def update_single_select_options(self, field_id, options):
        self._maybe_fail("update_single_select_options")
        name = next(name for name, field in self.fields.items()
                    if field["id"] == field_id)
        field = self.fields[name]
        live_ids = {option["id"] for option in field["options"]}
        result = []
        for option in options:
            if option.get("id") in live_ids:
                result.append(dict(option))
            else:
                result.append({**option, "id": self._new_id()})
        kept = {option["id"] for option in result}
        for item in self.items:
            option_id = item["values"].get(field_id)
            if option_id is not None and option_id not in kept:
                lost = next(o["name"] for o in field["options"] if o["id"] == option_id)
                self.cleared.append((item["item_id"], name, lost))
                del item["values"][field_id]
        field["options"] = result
        self.log.append(("update", name, [option["name"] for option in result]))

    def set_single_select_value(self, node_id, item_id, field_id, option_id):
        self._maybe_fail("set_single_select_value")
        field = next(field for field in self.fields.values() if field["id"] == field_id)
        assert option_id in {option["id"] for option in field["options"]}
        item = next(item for item in self.items if item["item_id"] == item_id)
        item["values"][field_id] = option_id
        self.log.append(("set", item_id))

    @contextlib.contextmanager
    def seam(self, loaded=None):
        loaded = loaded or fixture.loaded()
        names = ("fetch_boards", "fetch_board_by_node_id", "fetch_board_items",
                 "create_field", "update_single_select_options",
                 "set_single_select_value")
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(
                _MODULE.repo_schema, "fetch", return_value=loaded))
            for name in names:
                stack.enter_context(mock.patch.object(
                    _MODULE.boards, name, side_effect=getattr(self, name)))
            yield

    # --- internals ------------------------------------------------------------

    def _board(self):
        return {"number": self.number, "title": "r", "node_id": self.node_id,
                "fields": {
                    name: {"id": field["id"], "data_type": field["data_type"],
                           "options": {o["name"]: o["id"] for o in field["options"]},
                           "option_details": copy.deepcopy(field["options"])}
                    for name, field in self.fields.items()}}

    def _add_field(self, name, data_type, options):
        self.fields[name] = {"id": f"F_{name}", "data_type": data_type,
                             "options": [{**option, "id": self._new_id()}
                                         for option in options]}

    def _option_id(self, field, name):
        return next(option["id"] for option in self.fields[field]["options"]
                    if option["name"] == name)

    def _new_id(self):
        self.serial += 1
        return f"o{self.serial}"

    def _maybe_fail(self, name):
        self.calls[name] = self.calls.get(name, 0) + 1
        if self.fail.get(name) == self.calls[name]:
            raise _MODULE.gh.GhError(f"{name} failed", 6)


def _single(options):
    return ("SINGLE_SELECT", list(options))


def _converged_fields():
    return {
        "Priority": _single([("P0", "RED"), ("P1", "ORANGE"), ("P4", "GRAY")]),
        "Status": _single([("Needs Triage", "RED"), ("In progress", "PURPLE"),
                           ("Closed", "GRAY")]),
        "Size": _single([("XS", "GRAY"), ("S", "BLUE"), ("M", "GREEN"),
                         ("L", "YELLOW"), ("XL", "ORANGE")]),
        "Last Triaged": ("DATE", []),
    }


def _legacy_fields():
    """A board from before the board followed the schema: the eight fixed
    states and P0 to P3."""
    fields = _converged_fields()
    fields["Status"] = _single([
        ("Needs Triage", "RED"), ("In progress", "PURPLE"),
        ("Done", "GREEN"), ("Rejected", "GRAY")])
    fields["Priority"] = _single([("P0", "RED"), ("P1", "ORANGE"),
                                  ("P2", "YELLOW"), ("P3", "GREEN")])
    return fields


def _main(argv, board, loaded=None):
    """Run main against `board`; returns (exit code, payload or None, stderr)."""
    with board.seam(loaded), \
            contextlib.redirect_stdout(io.StringIO()) as stdout, \
            contextlib.redirect_stderr(io.StringIO()) as stderr:
        try:
            code = _MODULE.main(argv)
        except SystemExit as stop:
            code = stop.code
    output = stdout.getvalue()
    return code, (json.loads(output) if output else None), stderr.getvalue()


class GhwBoardSyncArgumentsTest(unittest.TestCase):
    def test_wrong_shapes_are_usage_errors(self):
        for arguments in ((), ("o/r",), ("o/r", "new", "3"), ("o/r", "plan"),
                          ("o/r", "plan", "x"), ("o/r", "sync", "3"),
                          ("o/r", "plan", "3", "--move", "Status", "Done"),
                          ("o/r", "plan", "3", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: ghw-board-sync", result.stderr)

    def test_the_old_two_argument_form_says_to_name_a_mode(self):
        result = _run("o/r", "3")
        self.assertEqual(result.returncode, 2)
        self.assertIn("ghw-board-sync o/r plan 3", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "plan", "3")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_apply_takes_no_move(self):
        result = _run("o/r", "apply", "3", "--move", "Status", "Done", "Closed")
        self.assertEqual(result.returncode, 2)
        self.assertIn("apply removes nothing", result.stderr)

    def test_a_move_names_a_schema_field_once(self):
        result = _run("o/r", "migrate", "3", "--move", "Size", "XL", "L")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Status, Priority", result.stderr)
        result = _run("o/r", "migrate", "3", "--move", "Status", "Done", "Closed",
                      "--move", "Status", "Done", "Needs Triage")
        self.assertEqual(result.returncode, 2)
        self.assertIn("twice", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ghw-board-sync <repo>", result.stdout)


class GhwBoardSyncPlanTest(unittest.TestCase):
    def test_plan_writes_nothing_and_lists_every_change(self):
        board = FakeBoard(_legacy_fields(), [
            ("I_done", "CLOSED", {"Status": "Done", "Priority": "P2"}),
            ("I_open", "OPEN", {"Status": "Rejected"}),
        ])
        code, payload, _ = _main(["o/r", "plan", "1"], board)
        self.assertEqual(code, 0)
        self.assertEqual(board.log, [])
        self.assertEqual(payload["action"], "plan")
        self.assertFalse(payload["changed"])
        options = {entry["field"]: entry for entry in payload["options"]}
        self.assertEqual(options["Status"]["add"], ["Closed"])
        self.assertEqual(options["Status"]["remove"], ["Done", "Rejected"])
        self.assertEqual(options["Priority"]["add"], ["P4"])
        self.assertEqual(options["Priority"]["remove"], ["P2", "P3"])
        status = {entry["option"]: entry["items"]
                  for entry in payload["migration"]["Status"]}
        self.assertEqual(status["Done"][0]["to"], "Closed")
        self.assertIsNone(status["Rejected"][0]["to"])  # an open issue
        priority = {entry["option"]: entry["items"]
                    for entry in payload["migration"]["Priority"]}
        self.assertIsNone(priority["P2"][0]["to"])
        self.assertEqual(priority["P3"], [])
        self.assertIsNone(payload["migrate_refused"])
        self.assertFalse(payload["conformance"]["conforms"])

    def test_plan_previews_named_moves(self):
        board = FakeBoard(_legacy_fields(),
                          [("I_open", "OPEN", {"Status": "Rejected"})])
        code, payload, _ = _main(
            ["o/r", "plan", "1", "--move", "Status", "Rejected", "Needs Triage"],
            board)
        self.assertEqual(code, 0)
        item = payload["migration"]["Status"][1]["items"][0]
        self.assertEqual((item["to"], item["by"]), ("Needs Triage", "named"))

    def test_a_move_must_name_an_option_being_removed_and_a_declared_target(self):
        board = FakeBoard(_legacy_fields())
        code, _, stderr = _main(
            ["o/r", "plan", "1", "--move", "Status", "Closed", "Needs Triage"],
            board)
        self.assertEqual(code, 2)
        self.assertIn("would not remove", stderr)
        code, _, stderr = _main(
            ["o/r", "plan", "1", "--move", "Status", "Done", "Done"], board)
        self.assertEqual(code, 2)
        self.assertIn("does not declare", stderr)

    def test_a_converged_board_reads_no_items(self):
        board = FakeBoard(_converged_fields())
        with mock.patch.object(FakeBoard, "fetch_board_items") as items:
            code, payload, _ = _main(["o/r", "plan", "1"], board)
        self.assertEqual(code, 0)
        items.assert_not_called()
        self.assertEqual(payload["migration"], {})
        self.assertTrue(payload["conformance"]["conforms"])

    def test_plan_says_why_migrate_would_be_refused(self):
        document = fixture.document()
        del document["issue_states"][1]["color"]   # lossy: incomplete
        board = FakeBoard(_legacy_fields())
        code, payload, stderr = _main(["o/r", "plan", "1"], board,
                                      fixture.loaded(document))
        self.assertEqual(code, 0)
        self.assertIn("issue_states", payload["migrate_refused"])
        self.assertIn("warning:", stderr)

    def test_a_board_not_linked_to_the_repo_is_refused(self):
        board = FakeBoard(_converged_fields(), number=3)
        code, _, stderr = _main(["o/r", "plan", "9"], board)
        self.assertEqual(code, 4)
        self.assertIn("#3", stderr)


class GhwBoardSyncApplyTest(unittest.TestCase):
    def test_apply_adds_reorders_and_recolours_but_removes_nothing(self):
        board = FakeBoard(_legacy_fields(), [
            ("I_done", "CLOSED", {"Status": "Done", "Priority": "P2"}),
            ("I_open", "OPEN", {"Status": "In progress", "Priority": "P0"}),
        ])
        code, payload, _ = _main(["o/r", "apply", "1"], board)
        self.assertEqual(code, 0)
        self.assertTrue(payload["changed"])
        self.assertEqual(board.option_names("Status"),
                         ["Needs Triage", "In progress", "Closed", "Done", "Rejected"])
        self.assertEqual(board.option_names("Priority"),
                         ["P0", "P1", "P4", "P2", "P3"])
        self.assertEqual(board.cleared, [])
        self.assertEqual(board.value("I_done", "Status"), "Done")
        self.assertEqual(board.value("I_done", "Priority"), "P2")
        # The undeclared options are still there, so the verdict still says so.
        self.assertFalse(payload["conformance"]["conforms"])

    def test_apply_on_a_converged_board_is_a_no_op(self):
        board = FakeBoard(_converged_fields())
        code, payload, _ = _main(["o/r", "apply", "1"], board)
        self.assertEqual(code, 0)
        self.assertEqual(board.log, [])
        self.assertFalse(payload["changed"])
        self.assertTrue(payload["conformance"]["conforms"])

    def test_apply_creates_missing_fields_except_size(self):
        board = FakeBoard({"Status": _single([("Todo", "GRAY")])})
        code, payload, _ = _main(["o/r", "apply", "1"], board)
        self.assertEqual(code, 0)
        self.assertEqual(payload["create_fields"], ["Priority", "Last Triaged"])
        self.assertEqual(board.option_names("Priority"), list(PRIORITIES))
        self.assertEqual([option["color"] for option in board.fields["Priority"]["options"]],
                         ["RED", "ORANGE", "GRAY"])
        self.assertNotIn("Size", board.fields)
        self.assertEqual(board.option_names("Status"), [*STATES, "Todo"])

    def test_apply_with_unreadable_states_leaves_status_alone(self):
        document = fixture.document()
        document["issue_states"] = "none"
        board = FakeBoard(_legacy_fields())
        code, payload, stderr = _main(["o/r", "apply", "1"], board,
                                      fixture.loaded(document))
        self.assertEqual(code, 0)
        self.assertEqual(board.option_names("Status"),
                         ["Needs Triage", "In progress", "Done", "Rejected"])
        self.assertEqual(board.option_names("Priority"),
                         ["P0", "P1", "P4", "P2", "P3"])
        self.assertIn("warning:", stderr)
        self.assertIn("'Status'", " ".join(payload["conformance"]["unchecked"]))

    def test_apply_with_no_schema_changes_no_option(self):
        board = FakeBoard(_legacy_fields())
        code, payload, stderr = _main(["o/r", "apply", "1"], board,
                                      fixture.missing())
        self.assertEqual(code, 0)
        self.assertEqual(board.log, [])
        self.assertIn("not found on the default branch", stderr)

    def test_a_dropped_option_id_fails_loudly(self):
        board = FakeBoard(_legacy_fields())
        real = board.update_single_select_options

        def forgetful(field_id, options):
            real(field_id, [{k: v for k, v in option.items() if k != "id"}
                            for option in options])
        board.update_single_select_options = forgetful
        code, _, stderr = _main(["o/r", "apply", "1"], board)
        self.assertEqual(code, 1)
        self.assertIn("did not keep options", stderr)

    def test_a_failed_write_names_what_landed_and_keeps_its_code(self):
        board = FakeBoard({"Status": _single([("Todo", "GRAY")])})
        board.fail = {"create_field": 2}
        code, _, stderr = _main(["o/r", "apply", "1"], board)
        self.assertEqual(code, 6)
        self.assertIn("created field Priority", stderr)


class GhwBoardSyncMigrateTest(unittest.TestCase):
    """The destructive mode: every item moves before any option goes."""

    def _legacy(self):
        return FakeBoard(_legacy_fields(), [
            ("I_done", "CLOSED", {"Status": "Done", "Priority": "P2"}),
            ("I_rejected", "CLOSED", {"Status": "Rejected", "Priority": "P3"}),
            ("I_open", "OPEN", {"Status": "In progress", "Priority": "P0"}),
            ("I_bare", "OPEN", {}),
        ])

    _MOVES = ["--move", "Priority", "P2", "P1", "--move", "Priority", "P3", "P4"]

    def test_migrate_moves_every_item_then_removes_the_options(self):
        board = self._legacy()
        code, payload, _ = _main(["o/r", "migrate", "1", *self._MOVES], board)
        self.assertEqual(code, 0, payload)
        self.assertEqual(board.option_names("Status"), list(STATES))
        self.assertEqual(board.option_names("Priority"), list(PRIORITIES))
        self.assertEqual(board.cleared, [])
        self.assertEqual(board.value("I_done", "Status"), "Closed")
        self.assertEqual(board.value("I_rejected", "Status"), "Closed")
        self.assertEqual(board.value("I_done", "Priority"), "P1")
        self.assertEqual(board.value("I_rejected", "Priority"), "P4")
        self.assertEqual(board.value("I_open", "Status"), "In progress")
        self.assertIsNone(board.value("I_bare", "Status"))
        self.assertTrue(payload["conformance"]["conforms"])
        # Order: the additive writes, then every move, then the removals.
        kinds = [entry[0] for entry in board.log]
        last_set = max(i for i, kind in enumerate(kinds) if kind == "set")
        removals = [i for i, entry in enumerate(board.log)
                    if entry[0] == "update"
                    and entry[2] in (list(STATES), list(PRIORITIES))]
        self.assertTrue(all(i > last_set for i in removals))

    def test_a_rerun_converges(self):
        board = self._legacy()
        _main(["o/r", "migrate", "1", *self._MOVES], board)
        board.log.clear()
        code, payload, _ = _main(["o/r", "migrate", "1"], board)
        self.assertEqual(code, 0)
        self.assertEqual(board.log, [])
        self.assertFalse(payload["changed"])

    def test_an_item_with_no_target_refuses_before_any_write(self):
        board = self._legacy()
        code, _, stderr = _main(["o/r", "migrate", "1"], board)
        self.assertEqual(code, 4)
        self.assertEqual(board.log, [])
        self.assertIn("Priority 'P2'", stderr)
        self.assertIn("issues/1", stderr)
        self.assertIn("--move", stderr)

    def test_an_open_issue_on_a_removed_state_needs_a_named_move(self):
        fields = _legacy_fields()
        fields["Priority"] = _converged_fields()["Priority"]
        board = FakeBoard(fields, [("I_open", "OPEN", {"Status": "Done"})])
        code, _, stderr = _main(["o/r", "migrate", "1"], board)
        self.assertEqual(code, 4)
        self.assertIn("(open)", stderr)
        code, _, _ = _main(
            ["o/r", "migrate", "1", "--move", "Status", "Done", "In progress"],
            board)
        self.assertEqual(code, 0)
        self.assertEqual(board.value("I_open", "Status"), "In progress")
        self.assertEqual(board.cleared, [])

    def test_a_failure_midway_leaves_every_value_and_a_rerun_finishes(self):
        board = self._legacy()
        board.fail = {"set_single_select_value": 3}
        code, _, stderr = _main(["o/r", "migrate", "1", *self._MOVES], board)
        self.assertEqual(code, 6)
        self.assertIn("moved", stderr)              # what landed is named
        self.assertEqual(board.cleared, [])
        self.assertIn("Done", board.option_names("Status"))  # nothing removed
        for item_id in ("I_done", "I_rejected", "I_open"):
            self.assertIsNotNone(board.value(item_id, "Status"))
            self.assertIsNotNone(board.value(item_id, "Priority"))
        board.fail = {}
        code, payload, _ = _main(["o/r", "migrate", "1", *self._MOVES], board)
        self.assertEqual(code, 0)
        self.assertEqual(board.cleared, [])
        self.assertTrue(payload["conformance"]["conforms"])

    def test_a_failed_removal_loses_nothing_and_a_rerun_finishes(self):
        board = self._legacy()
        # The first two updates are additive (Priority, Status); the third
        # is the first removal.
        board.fail = {"update_single_select_options": 3}
        code, _, _ = _main(["o/r", "migrate", "1", *self._MOVES], board)
        self.assertEqual(code, 6)
        self.assertEqual(board.cleared, [])
        board.fail = {}
        code, _, _ = _main(["o/r", "migrate", "1"], board)
        self.assertEqual(code, 0)
        self.assertEqual(board.cleared, [])
        self.assertEqual(board.option_names("Priority"), list(PRIORITIES))

    def test_an_item_set_back_onto_a_removed_option_stops_the_removal(self):
        board = self._legacy()
        real = board.fetch_board_items
        reads = []

        def racing(node_id):
            reads.append(node_id)
            if len(reads) == 2:   # the re-read after the moves
                done = board.fields["Status"]
                done_id = next(o["id"] for o in done["options"] if o["name"] == "Done")
                board.items[2]["values"][done["id"]] = done_id
            return real(node_id)
        board.fetch_board_items = racing
        code, _, stderr = _main(["o/r", "migrate", "1", *self._MOVES], board)
        self.assertEqual(code, 4)
        self.assertIn("before removing anything", stderr)
        self.assertEqual(board.cleared, [])
        self.assertIn("Done", board.option_names("Status"))

    def test_an_option_added_by_hand_meanwhile_stops_the_removal(self):
        board = self._legacy()
        real = board.set_single_select_value

        def meddling(*arguments):
            real(*arguments)
            status = board.fields["Status"]
            if not any(o["name"] == "Blocked" for o in status["options"]):
                status["options"].append({"id": "o_hand", "name": "Blocked",
                                          "color": "RED", "description": ""})
        board.set_single_select_value = meddling
        code, _, stderr = _main(["o/r", "migrate", "1", *self._MOVES], board)
        self.assertEqual(code, 4)
        self.assertIn("gained options", stderr)
        self.assertEqual(board.cleared, [])

    def test_migrate_needs_the_states_and_priorities_complete(self):
        broken = fixture.document()
        del broken["issue_priorities"][0]["meaning"]   # lossy
        cases = (
            (fixture.loaded(broken), 4),
            (fixture.missing(), 4),
            (repo_schema.RepoSchema(
                "o/r", None, None,
                tracker_schema.TrackerSchemaError("could not be fetched"), 6), 6),
            (repo_schema.RepoSchema(
                "o/r", None, None,
                tracker_schema.TrackerSchemaError("could not be fetched"), 5), 5),
        )
        for loaded, expected in cases:
            with self.subTest(expected=expected):
                board = self._legacy()
                code, _, stderr = _main(["o/r", "migrate", "1", *self._MOVES],
                                        board, loaded)
                self.assertEqual(code, expected)
                self.assertEqual(board.log, [])
                self.assertIn("migrate refused", stderr)

    def test_the_shipped_default_migrates_done_and_rejected_with_no_moves(self):
        # Under the default schema the general rule covers the old terminal
        # states: closed issues on Done or Rejected go to the one closed
        # state, and P0 to P3 are already the default's priorities.
        fields = _legacy_fields()
        fields["Status"] = _single([
            (name, "GRAY") for name in (
                "Needs Triage", "Needs Scope", "Needs Eng Design", "Needs Impl",
                "In progress", "In review", "Done", "Rejected")])
        board = FakeBoard(fields, [
            ("I_done", "CLOSED", {"Status": "Done"}),
            ("I_rejected", "CLOSED", {"Status": "Rejected"}),
            ("I_review", "OPEN", {"Status": "In review"}),
        ])
        code, payload, _ = _main(["o/r", "migrate", "1"], board, _default_schema())
        self.assertEqual(code, 0, payload)
        self.assertEqual(board.option_names("Status")[-1], "Closed")
        self.assertNotIn("Done", board.option_names("Status"))
        self.assertEqual(board.value("I_done", "Status"), "Closed")
        self.assertEqual(board.value("I_rejected", "Status"), "Closed")
        self.assertEqual(board.value("I_review", "Status"), "In review")
        self.assertEqual(board.cleared, [])
        colors = {o["name"]: o["color"] for o in board.fields["Status"]["options"]}
        self.assertEqual(colors["Needs Scope"], "ORANGE")
        self.assertEqual(colors["Closed"], "GRAY")


class GhwBoardSyncCreateTest(unittest.TestCase):
    def _fakes(self, existing=()):
        board = FakeBoard({"Status": _single([("Todo", "GRAY"),
                                              ("In Progress", "YELLOW"),
                                              ("Done", "GREEN")])}, number=7)
        patches = {
            "fetch_boards": mock.Mock(return_value=list(existing)),
            "fetch_repository_identity": mock.Mock(
                return_value={"node_id": "R_1", "owner_node_id": "U_1"}),
            "create_project": mock.Mock(return_value={
                "node_id": board.node_id, "number": 7, "title": "r",
                "url": "https://github.com/orgs/o/projects/7"}),
            "link_project_to_repository": mock.Mock(),
        }
        return board, patches

    def _main(self, board, patches, loaded=None):
        with contextlib.ExitStack() as stack:
            stack.enter_context(board.seam(loaded))
            for name, value in patches.items():
                stack.enter_context(mock.patch.object(_MODULE.boards, name, value))
            stdout = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stderr = stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
            try:
                code = _MODULE.main(["o/r", "new"])
            except SystemExit as stop:
                code = stop.code
        output = stdout.getvalue()
        return code, (json.loads(output) if output else None), stderr.getvalue()

    def test_creates_links_and_provisions_the_schemas_board(self):
        board, patches = self._fakes()
        code, payload, _ = self._main(board, patches)
        self.assertEqual(code, 0)
        patches["create_project"].assert_called_once_with("U_1", "r")
        patches["link_project_to_repository"].assert_called_once_with("PVT_7", "R_1")
        self.assertEqual(board.option_names("Status"), list(STATES))
        self.assertEqual(board.option_names("Priority"), list(PRIORITIES))
        self.assertIn("Size", board.fields)
        self.assertIn("Last Triaged", board.fields)
        self.assertTrue(payload["created_board"])
        self.assertEqual(payload["board"], 7)
        self.assertTrue(payload["conformance"]["conforms"])

    def test_new_is_refused_before_creating_anything_without_states(self):
        document = fixture.document()
        document["issue_states"] = "none"
        for loaded, expected in ((fixture.loaded(document), 4),
                                 (fixture.missing(), 4),
                                 (repo_schema.RepoSchema(
                                     "o/r", None, None,
                                     tracker_schema.TrackerSchemaError("x"), 6), 6)):
            with self.subTest(expected=expected):
                board, patches = self._fakes()
                code, _, stderr = self._main(board, patches, loaded)
                self.assertEqual(code, expected)
                self.assertIn("new refused before creating anything", stderr)
                patches["create_project"].assert_not_called()

    def test_refuses_when_the_repo_already_has_a_linked_board(self):
        board, patches = self._fakes(existing=[{"number": 3, "title": "x"}])
        code, _, stderr = self._main(board, patches)
        self.assertEqual(code, 4)
        self.assertIn("#3", stderr)
        patches["create_project"].assert_not_called()

    def test_a_failure_after_creation_names_the_project_and_how_to_finish(self):
        for code_in in (3, 5, 6):
            with self.subTest(code=code_in):
                board, patches = self._fakes()
                patches["link_project_to_repository"].side_effect = \
                    _MODULE.gh.GhError("boom", code_in)
                code, _, stderr = self._main(board, patches)
                self.assertEqual(code, 1)
                self.assertIn("#7", stderr)
                self.assertIn("projects/7", stderr)
                self.assertIn("ghw-board-sync o/r apply 7", stderr)

    def test_a_failure_provisioning_fields_names_what_landed(self):
        board, patches = self._fakes()
        board.fail = {"create_field": 2}
        code, _, stderr = self._main(board, patches)
        self.assertEqual(code, 1)
        self.assertIn("created field Priority", stderr)

    def test_create_project_that_may_have_landed_is_not_retryable(self):
        board, patches = self._fakes()
        patches["create_project"].side_effect = _MODULE.gh.GhError(
            "reset", 6, may_have_landed=True)
        self.assertEqual(self._main(board, patches)[0], 1)

    def test_create_project_failing_before_send_stays_retryable(self):
        board, patches = self._fakes()
        patches["create_project"].side_effect = _MODULE.gh.GhError(
            "no such host", 6, may_have_landed=False)
        self.assertEqual(self._main(board, patches)[0], 6)


class GhwBoardSyncArgumentContractTest(
    ghw_test_support.ArgumentContractTests, unittest.TestCase
):
    SCRIPT = _SCRIPT
    LONGEST = ("o/r", "migrate", "3", "--move", "Status", "Done", "Closed")
    FLAG_SLOT_FORMS = (("o/r", "--bogus", "3"),
                       ("o/r", "plan", "3", "--bogus", "Status", "Done", "Closed"))


if __name__ == "__main__":
    unittest.main()
