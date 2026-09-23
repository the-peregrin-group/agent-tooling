"""Tests for the ghw-board-sync executable.

Argument tests run the script as a subprocess with arguments that fail before
any network I/O. Behavior tests load the script as a module and mock the lib
boards seam. Either way, no `gh` calls are made.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

import ghw_test_support

_SCRIPT = Path(__file__).resolve().parent / "ghw-board-sync"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)


def _stock_board(number: int = 1) -> dict:
    """A freshly created ProjectV2: a stock Status field and nothing else."""
    return {
        "number": number, "title": "r", "node_id": "PVT_1",
        "url": f"https://github.com/users/o/projects/{number}",
        "fields": {"Status": {"id": "F_status", "data_type": "SINGLE_SELECT",
                              "options": {"Todo": "o1", "In Progress": "o2",
                                          "Done": "o3"}}},
    }


class GhwBoardSyncArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("o/r",), ("o/r", "3", "extra")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: ghw-board-sync", result.stderr)

    def test_malformed_repo_is_usage_error(self):
        result = _run("not-a-repo", "3")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owner/name", result.stderr)

    def test_non_numeric_target_names_both_accepted_forms(self):
        result = _run("o/r", "roadmap")
        self.assertEqual(result.returncode, 2)
        self.assertIn("project number or the literal 'new'", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("ghw-board-sync <repo>", result.stdout)


class GhwBoardSyncExistingBoardTest(unittest.TestCase):
    @contextlib.contextmanager
    def _seam(self, board, after=None):
        """Mock the boards seam: `board` is linked to the repo, and `after` is
        what a post-mutation re-read returns (defaults to `board`)."""
        with mock.patch.object(_MODULE.boards, "fetch_boards",
                               return_value=[board]), \
                mock.patch.object(_MODULE.boards, "fetch_board_by_node_id",
                                  return_value=after or board), \
                mock.patch.object(_MODULE.boards, "create_field") as create, \
                mock.patch.object(_MODULE.boards,
                                  "replace_single_select_options") as replace, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            yield {"create": create, "replace": replace, "stdout": stdout}

    def test_missing_fields_are_created_except_size(self):
        # Size stays a human decision on an existing board; triage tolerates
        # boards without it.
        with self._seam(_stock_board()) as seam:
            self.assertEqual(_MODULE.main(["o/r", "1"]), 0)
        created = [call.args[1] for call in seam["create"].call_args_list]
        self.assertEqual(created, ["Priority", "Last Triaged"])
        payload = json.loads(seam["stdout"].getvalue())
        self.assertEqual(payload["created_fields"], ["Priority", "Last Triaged"])
        self.assertTrue(payload["changed"])
        self.assertFalse(payload["created_board"])

    def test_existing_status_drift_is_reported_never_edited(self):
        with self._seam(_stock_board()) as seam:
            _MODULE.main(["o/r", "1"])
        seam["replace"].assert_not_called()
        payload = json.loads(seam["stdout"].getvalue())
        self.assertFalse(payload["status_options_replaced"])
        self.assertFalse(payload["conformance"]["conforms"])
        self.assertTrue(
            any("Needs Triage" in gap for gap in payload["conformance"]["gaps"])
        )

    def test_date_field_is_created_without_options(self):
        with self._seam(_stock_board()) as seam:
            _MODULE.main(["o/r", "1"])
        last_triaged = seam["create"].call_args_list[-1]
        self.assertEqual(last_triaged.args[1:], ("Last Triaged", "DATE", None))

    def test_single_select_creation_carries_the_canonical_options(self):
        with self._seam(_stock_board()) as seam:
            _MODULE.main(["o/r", "1"])
        priority = seam["create"].call_args_list[0]
        self.assertEqual([option["name"] for option in priority.args[3]],
                         ["P0", "P1", "P2", "P3"])

    def test_conforming_board_is_a_no_op(self):
        board = _stock_board()
        board["fields"] = {
            "Priority": {"id": "F", "data_type": "SINGLE_SELECT",
                         "options": dict.fromkeys(["P0", "P1", "P2", "P3"], "o")},
            "Status": {"id": "F", "data_type": "SINGLE_SELECT",
                       "options": dict.fromkeys(_MODULE.board_schema.FIELD_SPECS
                                                ["Status"]["options"], "o")},
            "Last Triaged": {"id": "F", "data_type": "DATE", "options": {}},
        }
        with self._seam(board) as seam:
            self.assertEqual(_MODULE.main(["o/r", "1"]), 0)
        seam["create"].assert_not_called()
        payload = json.loads(seam["stdout"].getvalue())
        self.assertFalse(payload["changed"])
        self.assertTrue(payload["conformance"]["conforms"])

    def test_the_emitted_verdict_comes_from_the_post_mutation_re_read(self):
        # The pre-state is missing Priority and Last Triaged; the board is
        # re-read after they are created, so the verdict must reflect that
        # rather than the state the wrapper started from.
        after = _stock_board()
        after["fields"] = {
            "Priority": {"id": "F", "data_type": "SINGLE_SELECT",
                         "options": dict.fromkeys(["P0", "P1", "P2", "P3"], "o")},
            "Status": {"id": "F", "data_type": "SINGLE_SELECT",
                       "options": dict.fromkeys(
                           _MODULE.board_schema.FIELD_SPECS["Status"]["options"], "o")},
            "Last Triaged": {"id": "F", "data_type": "DATE", "options": {}},
        }
        with self._seam(_stock_board(), after=after) as seam:
            _MODULE.main(["o/r", "1"])
        self.assertTrue(
            json.loads(seam["stdout"].getvalue())["conformance"]["conforms"]
        )

    def test_a_failure_mid_provision_reports_the_fields_already_created(self):
        with self._seam(_stock_board()) as seam:
            seam["create"].side_effect = [None, _MODULE.gh.GhError("HTTP 500")]
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as caught:
                    _MODULE.main(["o/r", "1"])
        self.assertEqual(caught.exception.code, 1)
        self.assertIn("HTTP 500", stderr.getvalue())
        self.assertIn("Priority", stderr.getvalue())

    def test_board_not_linked_to_the_repo_is_refused_listing_candidates(self):
        # The project number is a scope claim about an existing object, so the
        # wrapper verifies it rather than trusting it.
        with mock.patch.object(_MODULE.boards, "fetch_boards",
                               return_value=[_stock_board(3)]), \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "9"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("#3", stderr.getvalue())


class GhwBoardSyncCreateTest(unittest.TestCase):
    @contextlib.contextmanager
    def _seam(self, existing_boards=()):
        provisioned = _stock_board(7)
        with mock.patch.object(_MODULE.boards, "fetch_boards",
                               return_value=list(existing_boards)), \
                mock.patch.object(_MODULE.boards, "fetch_repository_identity",
                                  return_value={"node_id": "R_1",
                                                "owner_node_id": "U_1"}), \
                mock.patch.object(_MODULE.boards, "create_project",
                                  return_value={"node_id": "PVT_1", "number": 7,
                                                "title": "r",
                                                "url": provisioned["url"]}) as create_project, \
                mock.patch.object(_MODULE.boards,
                                  "link_project_to_repository") as link, \
                mock.patch.object(_MODULE.boards, "fetch_board_by_node_id",
                                  return_value=provisioned), \
                mock.patch.object(_MODULE.boards, "create_field") as create, \
                mock.patch.object(_MODULE.boards,
                                  "replace_single_select_options") as replace, \
                contextlib.redirect_stdout(io.StringIO()) as stdout, \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            yield {"create_project": create_project, "link": link,
                   "create": create, "replace": replace,
                   "stdout": stdout, "stderr": stderr}

    def test_creates_links_and_provisions_the_full_schema(self):
        with self._seam() as seam:
            self.assertEqual(_MODULE.main(["o/r", "new"]), 0)
        seam["create_project"].assert_called_once_with("U_1", "r")
        seam["link"].assert_called_once_with("PVT_1", "R_1")
        created = [call.args[1] for call in seam["create"].call_args_list]
        self.assertEqual(created, ["Priority", "Size", "Last Triaged"])
        payload = json.loads(seam["stdout"].getvalue())
        self.assertTrue(payload["created_board"])
        self.assertEqual(payload["board"], 7)
        self.assertIn("projects/7", payload["board_url"])

    def test_stock_status_options_are_replaced_on_the_new_board(self):
        # The one sanctioned Status edit: a board seconds old has no items to
        # orphan.
        with self._seam() as seam:
            _MODULE.main(["o/r", "new"])
        seam["replace"].assert_called_once()
        field_id, options = seam["replace"].call_args.args
        self.assertEqual(field_id, "F_status")
        self.assertEqual([option["name"] for option in options],
                         list(_MODULE.board_schema.FIELD_SPECS["Status"]["options"]))
        self.assertTrue(
            json.loads(seam["stdout"].getvalue())["status_options_replaced"]
        )

    def test_a_failure_after_creation_names_the_orphaned_project(self):
        # The board exists but is not linked yet, so fetch_boards can no
        # longer find it: the error is the only thing standing between the
        # user and an invisible project plus a second one on the next run.
        with self._seam() as seam:
            seam["link"].side_effect = _MODULE.gh.GhError("HTTP 403")
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "new"])
        self.assertEqual(caught.exception.code, 1)
        message = seam["stderr"].getvalue()
        self.assertIn("HTTP 403", message)
        self.assertIn("#7", message)
        self.assertIn("projects/7", message)          # the URL, to find it by
        self.assertIn("ghw-board-sync o/r 7", message)  # how to finish it

    def test_a_failure_provisioning_fields_also_names_the_project(self):
        with self._seam() as seam:
            seam["create"].side_effect = [None, _MODULE.gh.GhError("HTTP 500")]
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "new"])
        self.assertEqual(caught.exception.code, 1)
        message = seam["stderr"].getvalue()
        self.assertIn("#7", message)
        self.assertIn("Priority", message)  # what did land

    def test_refuses_when_the_repo_already_has_a_linked_board(self):
        # 'new' is inherently non-idempotent; refusing keeps a repeated
        # bootstrap from silently producing a second board.
        with self._seam([_stock_board(3)]) as seam:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(["o/r", "new"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("#3", seam["stderr"].getvalue())
        seam["create_project"].assert_not_called()


if __name__ == "__main__":
    unittest.main()
