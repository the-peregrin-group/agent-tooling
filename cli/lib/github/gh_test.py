"""Unit tests for gh.py's argument construction and error paths.

The subprocess boundary is mocked; no `gh` calls are made. _run itself is
exercised only through the public functions.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

if __package__ in (None, ""):  # direct invocation: python3 lib/gh_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.github import gh


def _completed(stdout: str = "", returncode: int = 0, stderr: str = ""):
    return subprocess.CompletedProcess(
        args=["gh"], returncode=returncode, stdout=stdout, stderr=stderr)


def _flag_pairs(argv: list[str]) -> list[tuple[str, str]]:
    return list(zip(argv, argv[1:]))


class GraphqlVariableTypingTest(unittest.TestCase):
    @mock.patch("lib.github.gh.subprocess.run")
    def test_types_map_to_typed_and_raw_fields(self, run):
        run.return_value = _completed(stdout='{"data": {}}')
        gh.graphql("query { x }",
                   {"s": "text", "n": 7, "yes": True, "no": False, "skip": None})
        pairs = _flag_pairs(run.call_args.args[0])
        self.assertIn(("-f", "s=text"), pairs)
        self.assertIn(("-F", "n=7"), pairs)
        self.assertIn(("-F", "yes=true"), pairs)
        self.assertIn(("-F", "no=false"), pairs)
        self.assertFalse(any("skip" in part for part in run.call_args.args[0]))

    @mock.patch("lib.github.gh.subprocess.run")
    def test_true_serializes_as_json_true_not_integer_one(self, run):
        # bool is an int subclass; without the ordering True would go out as 1.
        run.return_value = _completed(stdout='{"data": {}}')
        gh.graphql("query { x }", {"flag": True})
        pairs = _flag_pairs(run.call_args.args[0])
        self.assertIn(("-F", "flag=true"), pairs)
        self.assertNotIn(("-F", "flag=1"), pairs)

    @mock.patch("lib.github.gh.subprocess.run")
    def test_string_values_use_raw_field_flag(self, run):
        # -f (raw) never interprets a leading @ as a filename; -F would.
        run.return_value = _completed(stdout='{"data": {}}')
        gh.graphql("query { x }", {"owner": "@/etc/passwd"})
        pairs = _flag_pairs(run.call_args.args[0])
        self.assertIn(("-f", "owner=@/etc/passwd"), pairs)


class GraphqlErrorPathTest(unittest.TestCase):
    @mock.patch("lib.github.gh.subprocess.run")
    def test_graphql_errors_raise(self, run):
        run.return_value = _completed(
            stdout='{"data": null, "errors": [{"message": "boom"}]}')
        with self.assertRaisesRegex(gh.GhError, "boom"):
            gh.graphql("query { x }")

    @mock.patch("lib.github.gh.subprocess.run")
    def test_non_json_output_raises_gherror(self, run):
        run.return_value = _completed(stdout="rate limit exceeded")
        with self.assertRaisesRegex(gh.GhError, "non-JSON"):
            gh.graphql("query { x }")

    @mock.patch("lib.github.gh.subprocess.run")
    def test_missing_data_object_raises_gherror(self, run):
        run.return_value = _completed(stdout='{"unexpected": 1}')
        with self.assertRaisesRegex(gh.GhError, "no data object"):
            gh.graphql("query { x }")

    @mock.patch("lib.github.gh.subprocess.run")
    def test_non_object_response_raises_gherror(self, run):
        run.return_value = _completed(stdout='["not", "an", "object"]')
        with self.assertRaisesRegex(gh.GhError, "non-object"):
            gh.graphql("query { x }")

    @mock.patch("lib.github.gh.subprocess.run")
    def test_nonzero_exit_raises_with_stderr(self, run):
        run.return_value = _completed(returncode=1, stderr="HTTP 401 bad credentials")
        with self.assertRaisesRegex(gh.GhError, "bad credentials"):
            gh.graphql("query { x }")

    @mock.patch("lib.github.gh.subprocess.run", side_effect=FileNotFoundError)
    def test_missing_gh_raises(self, run):
        with self.assertRaisesRegex(gh.GhError, "not found on PATH"):
            gh.graphql("query { x }")

    @mock.patch("lib.github.gh.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="gh", timeout=1))
    def test_timeout_raises_gherror(self, run):
        with self.assertRaisesRegex(gh.GhError, "timed out"):
            gh.graphql("query { x }")


class RestTest(unittest.TestCase):
    @mock.patch("lib.github.gh.subprocess.run")
    def test_bool_and_int_fields_sent_typed(self, run):
        run.return_value = _completed(stdout="{}")
        gh.rest("POST", "repos/o/r/pulls",
                {"draft": True, "issue": 3, "title": "hi"})
        pairs = _flag_pairs(run.call_args.args[0])
        self.assertIn(("-F", "draft=true"), pairs)
        self.assertIn(("-F", "issue=3"), pairs)
        self.assertIn(("-f", "title=hi"), pairs)

    @mock.patch("lib.github.gh.subprocess.run")
    def test_empty_body_returns_empty_dict(self, run):
        run.return_value = _completed(stdout="")
        self.assertEqual(gh.rest("DELETE", "repos/o/r/labels/x"), {})

    @mock.patch("lib.github.gh.subprocess.run")
    def test_non_json_body_raises_gherror(self, run):
        run.return_value = _completed(stdout="<html>proxy error</html>")
        with self.assertRaisesRegex(gh.GhError, "non-JSON"):
            gh.rest("GET", "repos/o/r")


class SubprocessPlumbingTest(unittest.TestCase):
    @mock.patch("lib.github.gh.subprocess.run")
    def test_no_input_closes_stdin_and_sets_timeout(self, run):
        run.return_value = _completed(stdout='{"data": {}}')
        gh.graphql("query { x }")
        kwargs = run.call_args.kwargs
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertIsNone(kwargs["input"])
        self.assertEqual(kwargs["timeout"], gh.GH_TIMEOUT_SECONDS)

    @mock.patch("lib.github.gh.subprocess.run")
    def test_piped_input_leaves_stdin_to_subprocess_run(self, run):
        run.return_value = _completed()
        gh.issue_comment("o/r", 5, "hello")
        kwargs = run.call_args.kwargs
        self.assertEqual(kwargs["input"], "hello")
        self.assertIsNone(kwargs["stdin"])


class IssueVerbArgvTest(unittest.TestCase):
    @mock.patch("lib.github.gh.subprocess.run")
    def test_issue_create_repeats_labels_and_pipes_body(self, run):
        run.return_value = _completed(stdout="https://github.com/o/r/issues/7\n")
        url = gh.issue_create("o/r", "Title", "Body", ["bug", "area:core"])
        self.assertEqual(url, "https://github.com/o/r/issues/7")
        argv = run.call_args.args[0]
        self.assertEqual(argv[:3], ["gh", "issue", "create"])
        pairs = _flag_pairs(argv)
        self.assertIn(("--label", "bug"), pairs)
        self.assertIn(("--label", "area:core"), pairs)
        self.assertIn(("--body-file", "-"), pairs)
        self.assertEqual(run.call_args.kwargs["input"], "Body")

    @mock.patch("lib.github.gh.subprocess.run")
    def test_issue_view_joins_json_fields(self, run):
        run.return_value = _completed(stdout='{"title": "t"}')
        self.assertEqual(gh.issue_view("o/r", 5, ["title", "state"]), {"title": "t"})
        pairs = _flag_pairs(run.call_args.args[0])
        self.assertIn(("--json", "title,state"), pairs)
        self.assertIn(("--repo", "o/r"), pairs)

    @mock.patch("lib.github.gh.subprocess.run")
    def test_issue_view_non_json_output_raises_gherror(self, run):
        run.return_value = _completed(stdout="killed mid-write")
        with self.assertRaisesRegex(gh.GhError, "non-JSON"):
            gh.issue_view("o/r", 5, ["title"])

    @mock.patch("lib.github.gh.subprocess.run")
    def test_issue_edit_title_passes_title_flag(self, run):
        run.return_value = _completed()
        gh.issue_edit_title("o/r", 5, "New title")
        pairs = _flag_pairs(run.call_args.args[0])
        self.assertIn(("--title", "New title"), pairs)

    @mock.patch("lib.github.gh.subprocess.run")
    def test_issue_close_without_comment_omits_the_flag(self, run):
        run.return_value = _completed()
        gh.issue_close("o/r", 5)
        self.assertNotIn("--comment", run.call_args.args[0])

    @mock.patch("lib.github.gh.subprocess.run")
    def test_issue_close_with_comment_passes_it_inline(self, run):
        # The comment rides argv, not a shell: subprocess never re-parses it.
        run.return_value = _completed()
        gh.issue_close("o/r", 5, "done via #6")
        pairs = _flag_pairs(run.call_args.args[0])
        self.assertIn(("--comment", "done via #6"), pairs)


class VersionTest(unittest.TestCase):
    @mock.patch("lib.github.gh.subprocess.run")
    def test_parses_the_version_banner(self, run):
        run.return_value = _completed(
            stdout="gh version 2.97.0 (2026-07-31)\nhttps://github.com/cli/cli\n")
        self.assertEqual(gh.version(), (2, 97, 0))

    @mock.patch("lib.github.gh.subprocess.run")
    def test_unparseable_banner_raises_gherror(self, run):
        run.return_value = _completed(stdout="some wrapper script said hello")
        with self.assertRaisesRegex(gh.GhError, "cannot parse gh version"):
            gh.version()


class DependencyVerbArgvTest(unittest.TestCase):
    @mock.patch("lib.github.gh.subprocess.run")
    def test_each_subverb_maps_to_its_gh_flag(self, run):
        run.return_value = _completed()
        for subverb, flag in gh.DEPENDENCY_FLAGS.items():
            with self.subTest(subverb=subverb):
                gh.issue_edit_dependency("o/r", 7, subverb, 8)
                self.assertIn((flag, "8"), _flag_pairs(run.call_args.args[0]))

    def test_blocking_subverbs_are_deliberately_absent(self):
        # "X blocks Y" is spelled "Y blocked-by X"; one relationship, one
        # spelling.
        self.assertNotIn("add-blocking", gh.DEPENDENCY_FLAGS)

    def test_unknown_subverb_raises_before_any_subprocess(self):
        with self.assertRaisesRegex(ValueError, "add-blocking"):
            gh.issue_edit_dependency("o/r", 7, "add-blocking", 8)


class LabelVerbArgvTest(unittest.TestCase):
    @mock.patch("lib.github.gh.subprocess.run")
    def test_create_passes_color_and_description(self, run):
        run.return_value = _completed()
        gh.label_create("o/r", "area:core", "bfdadc", "Core engine")
        argv = run.call_args.args[0]
        self.assertEqual(argv[:4], ["gh", "label", "create", "area:core"])
        pairs = _flag_pairs(argv)
        self.assertIn(("--color", "bfdadc"), pairs)
        self.assertIn(("--description", "Core engine"), pairs)

    @mock.patch("lib.github.gh.subprocess.run")
    def test_edit_never_renames(self, run):
        # Renaming would silently retarget every attachment.
        run.return_value = _completed()
        gh.label_edit("o/r", "bug", "d73a4a", "Broken")
        self.assertNotIn("--name", run.call_args.args[0])

    @mock.patch("lib.github.gh.subprocess.run")
    def test_delete_confirms_non_interactively(self, run):
        run.return_value = _completed()
        gh.label_delete("o/r", "wontfix")
        self.assertIn("--yes", run.call_args.args[0])


class PullVerbArgvTest(unittest.TestCase):
    @mock.patch("lib.github.gh.subprocess.run")
    def test_pr_comment_pipes_body_over_stdin(self, run):
        run.return_value = _completed()
        gh.pr_comment("o/r", 5, "review reply")
        argv = run.call_args.args[0]
        self.assertEqual(argv[:3], ["gh", "pr", "comment"])
        self.assertIn(("--body-file", "-"), _flag_pairs(argv))
        self.assertEqual(run.call_args.kwargs["input"], "review reply")

    @mock.patch("lib.github.gh.subprocess.run")
    def test_pr_view_joins_json_fields(self, run):
        run.return_value = _completed(stdout='{"state": "OPEN"}')
        gh.pr_view("o/r", 5, ["state", "isDraft"])
        self.assertIn(("--json", "state,isDraft"), _flag_pairs(run.call_args.args[0]))

    @mock.patch("lib.github.gh.subprocess.run")
    def test_pr_merge_uses_strategy_flag_and_never_delete_branch(self, run):
        run.return_value = _completed()
        for strategy in ("merge", "squash"):
            with self.subTest(strategy=strategy):
                gh.pr_merge("o/r", 5, strategy)
                argv = run.call_args.args[0]
                self.assertIn(f"--{strategy}", argv)
                self.assertNotIn("--delete-branch", argv)

    @mock.patch("lib.github.gh.subprocess.run")
    def test_pr_merge_pins_the_reviewed_head_commit(self, run):
        # Pinning the head oid closes the race between the caller's
        # green-checks read and the merge itself.
        run.return_value = _completed()
        gh.pr_merge("o/r", 5, "squash", "abc123")
        self.assertIn(
            ("--match-head-commit", "abc123"), _flag_pairs(run.call_args.args[0])
        )

    def test_pr_merge_rejects_unknown_strategy_before_any_subprocess(self):
        with self.assertRaisesRegex(ValueError, "rebase"):
            gh.pr_merge("o/r", 5, "rebase")

    @mock.patch("lib.github.gh.subprocess.run")
    def test_pr_create_posts_rest_fields(self, run):
        run.return_value = _completed(stdout='{"number": 3, "html_url": "u"}')
        response = gh.pr_create("o/r", "main", "feat", "T", "B", False)
        self.assertEqual(response["number"], 3)
        argv = run.call_args.args[0]
        self.assertEqual(argv[:4], ["gh", "api", "-X", "POST"])
        self.assertIn("repos/o/r/pulls", argv)
        pairs = _flag_pairs(argv)
        self.assertIn(("-f", "title=T"), pairs)
        self.assertIn(("-f", "head=feat"), pairs)
        self.assertIn(("-f", "base=main"), pairs)
        self.assertIn(("-F", "draft=false"), pairs)

    @mock.patch("lib.github.gh.subprocess.run")
    def test_pr_create_rejects_a_non_object_response(self, run):
        run.return_value = _completed(stdout='["unexpected"]')
        with self.assertRaisesRegex(gh.GhError, "unexpected response"):
            gh.pr_create("o/r", "main", "feat", "T", "B", False)


if __name__ == "__main__":
    unittest.main()
