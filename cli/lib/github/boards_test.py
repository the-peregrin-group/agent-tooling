"""Unit tests for boards.py: the pure resolution logic, plus the query and
mutation builders with the gh seam mocked. No network either way.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

if __package__ in (None, ""):  # direct invocation: python3 lib/boards_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.github import boards, gh


def _board(number: int, title: str = "Board", fields: dict | None = None) -> dict:
    return {"number": number, "title": title, "node_id": f"PVT_{number}",
            "fields": fields if fields is not None else {}}


def _profile(repo: str, project_number: int) -> dict:
    return {"repo": repo, "project_number": project_number, "path": "/x/TRIAGE.md"}


_TRIAGE_MD_TEMPLATE = """# Triage profile
<!-- BEGIN triage-config -->
```json
{"repo": "%s", "project_number": %d}
```
<!-- END triage-config -->
"""


class ResolveCanonicalBoardTest(unittest.TestCase):
    def test_no_boards(self):
        board, rule, note = boards.resolve_canonical_board("o/r", [], None)
        self.assertIsNone(board)
        self.assertEqual(rule, "none-linked")
        self.assertIsNone(note)

    def test_single_board_wins_without_profile(self):
        only = _board(3)
        board, rule, _ = boards.resolve_canonical_board("o/r", [only], None)
        self.assertEqual(board, only)
        self.assertEqual(rule, "only-linked")

    def test_multiple_boards_without_profile_is_ambiguous(self):
        board, rule, note = boards.resolve_canonical_board(
            "o/r", [_board(1), _board(2)], None)
        self.assertIsNone(board)
        self.assertEqual(rule, "ambiguous")
        self.assertIn("#1", note)
        self.assertIn("#2", note)

    def test_matching_profile_decides(self):
        second = _board(2)
        board, rule, note = boards.resolve_canonical_board(
            "o/r", [_board(1), second], _profile("o/r", 2))
        self.assertEqual(board, second)
        self.assertEqual(rule, "triage-md")
        self.assertIn("TRIAGE.md", note)

    def test_profile_for_other_repo_is_ignored(self):
        # Trust-but-verify: a TRIAGE.md declaring a different repo must not
        # decide, or a session launched from an unrelated directory would
        # silently apply some other repo's profile.
        board, rule, note = boards.resolve_canonical_board(
            "o/r", [_board(1), _board(2)], _profile("other/repo", 1))
        self.assertIsNone(board)
        self.assertEqual(rule, "ambiguous")
        self.assertIn("other/repo", note)

    def test_profile_naming_unlinked_board_is_ambiguous(self):
        board, rule, note = boards.resolve_canonical_board(
            "o/r", [_board(1), _board(2)], _profile("o/r", 9))
        self.assertIsNone(board)
        self.assertEqual(rule, "ambiguous")
        self.assertIn("#9", note)

    def test_single_board_notes_a_disagreeing_profile(self):
        only = _board(3)
        board, rule, note = boards.resolve_canonical_board(
            "o/r", [only], _profile("o/r", 9))
        self.assertEqual(board, only)
        self.assertEqual(rule, "only-linked")
        self.assertIn("#9", note)
        self.assertIn("only-linked", note)

    def test_single_board_with_agreeing_profile_has_no_note(self):
        only = _board(3)
        board, rule, note = boards.resolve_canonical_board(
            "o/r", [only], _profile("o/r", 3))
        self.assertEqual(board, only)
        self.assertEqual(rule, "only-linked")
        self.assertIsNone(note)


def _priority_field(data_type: str = "SINGLE_SELECT",
                    options: tuple[str, ...] = ("P0", "P1", "P2", "P3")) -> dict:
    return {"id": "F", "data_type": data_type,
            "options": {name: f"opt_{name}" for name in options}}


class DeterminePriorityRegimeTest(unittest.TestCase):
    def test_canonical_board_with_conforming_priority_field(self):
        canonical = _board(1, fields={"Priority": _priority_field()})
        self.assertEqual(
            boards.determine_priority_regime(canonical, [canonical]), "board-field")

    def test_canonical_board_without_priority_field(self):
        canonical = _board(1)
        self.assertEqual(
            boards.determine_priority_regime(canonical, [canonical]), "unknown")

    def test_priority_field_of_wrong_type_is_not_board_field(self):
        # A text field merely *named* Priority: a single-select write against
        # it would fail, so the regime must not claim "board-field".
        canonical = _board(1, fields={"Priority": _priority_field(data_type="TEXT")})
        self.assertEqual(
            boards.determine_priority_regime(canonical, [canonical]), "unknown")

    def test_priority_field_missing_canonical_options_is_not_board_field(self):
        canonical = _board(1, fields={"Priority": _priority_field(options=("P0", "P1"))})
        self.assertEqual(
            boards.determine_priority_regime(canonical, [canonical]), "unknown")

    def test_no_boards_at_all(self):
        self.assertEqual(boards.determine_priority_regime(None, []), "p-labels")

    def test_unresolved_ambiguity(self):
        self.assertEqual(
            boards.determine_priority_regime(None, [_board(1), _board(2)]), "unknown")


class PriorityLabelsPresentTest(unittest.TestCase):
    def test_reports_only_priority_labels_in_order(self):
        labels = [{"name": "P3"}, {"name": "bug"}, {"name": "P0"}]
        self.assertEqual(boards.priority_labels_present(labels), ["P0", "P3"])


class BuildBoardTest(unittest.TestCase):
    @staticmethod
    def _node(field_nodes: list[dict], has_next_page: bool = False) -> dict:
        return {
            "id": "PVT_x", "number": 7, "title": "Roadmap", "closed": False,
            "fields": {"pageInfo": {"hasNextPage": has_next_page},
                       "nodes": field_nodes},
        }

    def test_reshapes_graphql_node(self):
        node = self._node([
            {"id": "F1", "name": "Status", "dataType": "SINGLE_SELECT",
             "options": [{"id": "o1", "name": "Needs Triage"}]},
            {"id": "F2", "name": "Last Triaged", "dataType": "DATE"},
            {},  # Defensive: should not occur (see _build_board).
        ])
        board = boards._build_board(node)
        self.assertEqual(board["number"], 7)
        self.assertEqual(board["node_id"], "PVT_x")
        self.assertEqual(board["fields"]["Status"]["options"], {"Needs Triage": "o1"})
        self.assertEqual(board["fields"]["Last Triaged"]["data_type"], "DATE")
        self.assertNotIn("", board["fields"])

    def test_truncated_field_page_fails_loudly(self):
        node = self._node([], has_next_page=True)
        with self.assertRaisesRegex(gh.GhError, "more than 100 fields"):
            boards._build_board(node)


class OptionsLiteralTest(unittest.TestCase):
    """Single-select options are inlined into the mutation document because
    gh's `-f` variables carry scalars only; they are baked-in constants, never
    caller input, and the color enum is checked rather than interpolated
    blind."""

    def test_renders_names_and_descriptions_as_graphql_strings(self):
        literal = boards._options_literal(
            [{"name": "P0", "color": "RED", "description": "urgent"}]
        )
        self.assertEqual(
            literal, '[{name: "P0", color: RED, description: "urgent"}]'
        )

    def test_escapes_quotes_in_names(self):
        literal = boards._options_literal(
            [{"name": 'a "quoted" state', "color": "GRAY", "description": ""}]
        )
        self.assertIn(r'name: "a \"quoted\" state"', literal)

    def test_color_outside_the_api_enum_is_refused(self):
        # GhError, not ValueError: a constants typo should exit 1 like any
        # other wrapper failure rather than surfacing as a traceback.
        with self.assertRaisesRegex(gh.GhError, "MAUVE"):
            boards._options_literal(
                [{"name": "P0", "color": "MAUVE", "description": ""}]
            )


class FetchBoardByNodeIdTest(unittest.TestCase):
    _NODE = {"id": "PVT_1", "number": 7, "title": "Roadmap",
             "url": "https://github.com/users/o/projects/7",
             "fields": {"pageInfo": {"hasNextPage": False}, "nodes": []}}

    @mock.patch("lib.github.boards.gh.graphql")
    def test_returns_a_board_dict_with_its_url(self, graphql):
        graphql.return_value = {"node": self._NODE}
        board = boards.fetch_board_by_node_id("PVT_1")
        self.assertEqual(board["number"], 7)
        self.assertEqual(board["url"], self._NODE["url"])

    @mock.patch("lib.github.boards.gh.graphql")
    def test_a_node_that_is_not_a_board_fails_loudly(self, graphql):
        # An id belonging to some other type resolves to an empty fragment.
        graphql.return_value = {"node": {}}
        with self.assertRaisesRegex(gh.GhError, "not a ProjectV2"):
            boards.fetch_board_by_node_id("I_1")


class FetchOpenIssuesWithLabelTest(unittest.TestCase):
    @staticmethod
    def _response(nodes, total=None):
        return {"repository": {"label": {"issues": {
            "totalCount": total if total is not None else len(nodes),
            "nodes": nodes,
        }}}}

    @mock.patch("lib.github.boards.gh.graphql")
    def test_label_name_travels_as_a_typed_variable(self, graphql):
        # The whole point: `gh issue list --label` splits on commas, so a
        # label named "needs-design, blocked" would query as two ANDed labels,
        # match nothing, and let a delete look unattached. An exact-name
        # GraphQL variable cannot split.
        graphql.return_value = self._response(
            [{"number": 4, "title": "t", "url": "u"}]
        )
        result = boards.fetch_open_issues_with_label("o/r", "needs-design, blocked")
        self.assertEqual(graphql.call_args.args[1]["label"],
                         "needs-design, blocked")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["issues"][0]["number"], 4)

    @mock.patch("lib.github.boards.gh.graphql")
    def test_missing_label_is_empty_not_an_error(self, graphql):
        graphql.return_value = {"repository": {"label": None}}
        self.assertEqual(boards.fetch_open_issues_with_label("o/r", "gone"),
                         {"total": 0, "issues": []})

    @mock.patch("lib.github.boards.gh.graphql")
    def test_server_side_total_survives_a_truncated_page(self, graphql):
        graphql.return_value = self._response(
            [{"number": 1, "title": "t", "url": "u"}], total=250
        )
        result = boards.fetch_open_issues_with_label("o/r", "wontfix")
        self.assertEqual(result["total"], 250)
        self.assertEqual(len(result["issues"]), 1)


class CreateFieldTest(unittest.TestCase):
    @mock.patch("lib.github.boards.gh.graphql")
    def test_single_select_field_carries_its_options(self, graphql):
        graphql.return_value = {
            "createProjectV2Field": {"projectV2Field": {"id": "F_1"}}
        }
        field_id = boards.create_field(
            "PVT_1", "Priority", "SINGLE_SELECT",
            [{"name": "P0", "color": "RED", "description": ""}],
        )
        self.assertEqual(field_id, "F_1")
        query, variables = graphql.call_args.args
        self.assertIn("singleSelectOptions:", query)
        self.assertIn('name: "P0"', query)
        self.assertEqual(variables["dataType"], "SINGLE_SELECT")
        self.assertEqual(variables["name"], "Priority")

    @mock.patch("lib.github.boards.gh.graphql")
    def test_date_field_omits_the_options_input(self, graphql):
        graphql.return_value = {
            "createProjectV2Field": {"projectV2Field": {"id": "F_2"}}
        }
        boards.create_field("PVT_1", "Last Triaged", "DATE")
        self.assertNotIn("singleSelectOptions", graphql.call_args.args[0])


class ParseTriageConfigTest(unittest.TestCase):
    def test_parses_fenced_block(self):
        config = boards._parse_triage_config(_TRIAGE_MD_TEMPLATE % ("o/r", 4))
        self.assertEqual(config, {"repo": "o/r", "project_number": 4})

    def test_missing_markers(self):
        self.assertIsNone(boards._parse_triage_config("# just prose"))

    def test_malformed_json(self):
        text = ("<!-- BEGIN triage-config -->\nnot json\n"
                "<!-- END triage-config -->")
        self.assertIsNone(boards._parse_triage_config(text))


class FindTriageProfileTest(unittest.TestCase):
    def setUp(self):
        os.makedirs("/tmp/claude", exist_ok=True)
        self.root = Path(tempfile.mkdtemp(dir="/tmp/claude"))
        self.addCleanup(shutil.rmtree, self.root)
        # The scratch root doubles as the git work-tree root bounding the walk.
        (self.root / ".git").mkdir()

    def test_finds_profile_in_ancestor(self):
        (self.root / "TRIAGE.md").write_text(_TRIAGE_MD_TEMPLATE % ("o/r", 5))
        start = self.root / "a" / "b"
        start.mkdir(parents=True)
        profile = boards.find_triage_profile(start)
        self.assertEqual(profile["repo"], "o/r")
        self.assertEqual(profile["project_number"], 5)
        self.assertEqual(profile["path"], str(self.root / "TRIAGE.md"))

    def test_nearest_profile_wins(self):
        (self.root / "TRIAGE.md").write_text(_TRIAGE_MD_TEMPLATE % ("outer/r", 1))
        inner = self.root / "inner"
        inner.mkdir()
        (inner / "TRIAGE.md").write_text(_TRIAGE_MD_TEMPLATE % ("inner/r", 2))
        self.assertEqual(boards.find_triage_profile(inner)["repo"], "inner/r")

    def test_malformed_profile_is_skipped_and_search_continues(self):
        (self.root / "TRIAGE.md").write_text(_TRIAGE_MD_TEMPLATE % ("o/r", 5))
        inner = self.root / "inner"
        inner.mkdir()
        (inner / "TRIAGE.md").write_text("# no config block here")
        self.assertEqual(boards.find_triage_profile(inner)["repo"], "o/r")

    def test_no_profile_anywhere(self):
        start = self.root / "empty"
        start.mkdir()
        self.assertIsNone(boards.find_triage_profile(start))

    def test_walk_stops_at_git_root(self):
        # A TRIAGE.md above the work-tree root (e.g. a squatter in /tmp or a
        # parent checkout) must never decide.
        (self.root / "TRIAGE.md").write_text(_TRIAGE_MD_TEMPLATE % ("outer/r", 1))
        repo = self.root / "nested-repo"
        start = repo / "src"
        start.mkdir(parents=True)
        (repo / ".git").write_text("gitdir: elsewhere")  # worktree-style file
        self.assertIsNone(boards.find_triage_profile(start))

    def test_outside_any_git_tree_finds_nothing(self):
        loose = Path(tempfile.mkdtemp(dir="/tmp/claude"))
        self.addCleanup(shutil.rmtree, loose)
        (loose / "TRIAGE.md").write_text(_TRIAGE_MD_TEMPLATE % ("o/r", 5))
        start = loose / "sub"
        start.mkdir()
        self.assertIsNone(boards.find_triage_profile(start))

    def _skips(self, content: str):
        """Write `content` as the root TRIAGE.md and assert it is skipped."""
        (self.root / "TRIAGE.md").write_text(content)
        self.assertIsNone(boards.find_triage_profile(self.root))

    def test_non_numeric_project_number_is_skipped(self):
        self._skips('<!-- BEGIN triage-config -->\n'
                    '{"repo": "o/r", "project_number": "seven"}\n'
                    '<!-- END triage-config -->')

    def test_json_string_config_is_skipped(self):
        # A JSON string containing both key names would pass a naive
        # substring-style guard; it must still be skipped.
        self._skips('<!-- BEGIN triage-config -->\n'
                    '"repo project_number"\n'
                    '<!-- END triage-config -->')

    def test_json_list_config_is_skipped(self):
        self._skips('<!-- BEGIN triage-config -->\n'
                    '["repo", "project_number"]\n'
                    '<!-- END triage-config -->')

    def test_non_utf8_file_is_skipped(self):
        (self.root / "TRIAGE.md").write_bytes(b"\xff\xfe not text")
        self.assertIsNone(boards.find_triage_profile(self.root))

    @unittest.skipIf(os.geteuid() == 0, "root ignores file permissions")
    def test_unreadable_file_is_skipped(self):
        candidate = self.root / "TRIAGE.md"
        candidate.write_text(_TRIAGE_MD_TEMPLATE % ("o/r", 5))
        candidate.chmod(0)
        self.addCleanup(candidate.chmod, 0o644)
        self.assertIsNone(boards.find_triage_profile(self.root))


class BuildIssueItemStateTest(unittest.TestCase):
    @staticmethod
    def _issue_node(item_nodes: list[dict]) -> dict:
        """Fake the issue/projectItems GraphQL node the reshape consumes."""
        return {"id": "I_1",
                "projectItems": {"pageInfo": {"hasNextPage": False},
                                 "nodes": item_nodes}}

    def test_reshapes_items_by_project_node_id(self):
        state = boards._build_issue_item_state(self._issue_node([
            {"id": "ITEM_a", "project": {"id": "PVT_1"},
             "fieldValueByName": {"optionId": "opt_x"}},
            {"id": "ITEM_b", "project": {"id": "PVT_2"},
             "fieldValueByName": None},  # field unset on this board's item
        ]))
        self.assertEqual(state["issue_node_id"], "I_1")
        self.assertEqual(state["items"]["PVT_1"],
                         {"item_id": "ITEM_a", "option_id": "opt_x"})
        self.assertEqual(state["items"]["PVT_2"],
                         {"item_id": "ITEM_b", "option_id": None})

    def test_non_single_select_value_reads_as_unset(self):
        # A non-matching union member comes back as an empty object.
        state = boards._build_issue_item_state(self._issue_node([
            {"id": "ITEM_a", "project": {"id": "PVT_1"}, "fieldValueByName": {}},
        ]))
        self.assertIsNone(state["items"]["PVT_1"]["option_id"])

    def test_issue_on_no_boards(self):
        state = boards._build_issue_item_state(self._issue_node([]))
        self.assertEqual(state["items"], {})


class BuildRefsQueryTest(unittest.TestCase):
    def test_declares_and_selects_one_alias_per_branch(self):
        query = boards._build_refs_query(2)
        self.assertIn("$ref0: String!", query)
        self.assertIn("$ref1: String!", query)
        self.assertIn("ref0: ref(qualifiedName: $ref0) { name }", query)
        self.assertIn("ref1: ref(qualifiedName: $ref1) { name }", query)
        self.assertNotIn("ref2", query)


if __name__ == "__main__":
    unittest.main()
