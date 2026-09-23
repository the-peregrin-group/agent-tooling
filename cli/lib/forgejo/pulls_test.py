"""Tests for the Forgejo PR operations, especially the quad-state query.
All API traffic is mocked at lib.forgejo.api.request.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import unittest
from unittest import mock

from lib import plan
from lib.forgejo import api, pulls
from lib.forgejo.config import Config

_CONFIG = Config(api_url="https://forge.example.com", token="t")


def _pr(number: int, head: str, *, draft=False, mergeable=True, state="open"):
    return {
        "number": number,
        "state": state,
        "draft": draft,
        "mergeable": mergeable,
        "head": {"ref": head, "label": head},
    }


class IsValidRepositoryTest(unittest.TestCase):
    def test_forgejo_charset_admits_underscore_and_dot_owners(self):
        for repository in ("octo-org/widgets", "some_bot/repo.name", "a/b"):
            with self.subTest(repository=repository):
                self.assertTrue(pulls.is_valid_repository(repository))

    def test_traversal_and_shape_violations_are_refused(self):
        for repository in ("", "noslash", "a/b/c", "o/..", "../r", "o/", "/r",
                           "bad repo/x", "o/r?x"):
            with self.subTest(repository=repository):
                self.assertFalse(pulls.is_valid_repository(repository))


@mock.patch("lib.forgejo.pulls.api.fetch_swagger", return_value=None)
class FindOpenPrsByHeadTest(unittest.TestCase):
    @mock.patch("lib.forgejo.pulls.api.supports_head_filter", return_value=True)
    @mock.patch("lib.forgejo.pulls.api.request")
    def test_server_filter_used_when_swagger_advertises_it(
        self, request, _supports, _swagger
    ):
        request.return_value = [_pr(4, "reconcile/a")]
        matches = pulls.find_open_prs_by_head(_CONFIG, "o/r", "reconcile/a")
        self.assertEqual([pr["number"] for pr in matches], [4])
        query = request.call_args.kwargs["query"]
        self.assertEqual(query["head"], "reconcile/a")
        self.assertEqual(query["state"], "open")

    @mock.patch("lib.forgejo.pulls.api.supports_head_filter", return_value=True)
    @mock.patch("lib.forgejo.pulls.api.request")
    def test_server_filter_results_are_reverified_client_side(
        self, request, _supports, _swagger
    ):
        # Trust but verify: a server bug (or a label-vs-ref mismatch) must not
        # let a foreign PR through.
        request.return_value = [_pr(4, "reconcile/a"), _pr(5, "other/branch")]
        matches = pulls.find_open_prs_by_head(_CONFIG, "o/r", "reconcile/a")
        self.assertEqual([pr["number"] for pr in matches], [4])

    @mock.patch("lib.forgejo.pulls.api.supports_head_filter", return_value=False)
    @mock.patch("lib.forgejo.pulls.api.request")
    def test_fallback_lists_and_filters_client_side(
        self, request, _supports, _swagger
    ):
        request.return_value = [
            _pr(1, "feature-x"), _pr(2, "reconcile/a"), _pr(3, "reconcile/ab"),
        ]
        matches = pulls.find_open_prs_by_head(_CONFIG, "o/r", "reconcile/a")
        # Exact match only -- "reconcile/ab" is a different branch.
        self.assertEqual([pr["number"] for pr in matches], [2])

    @mock.patch("lib.forgejo.pulls.api.supports_head_filter", return_value=True)
    @mock.patch("lib.forgejo.pulls.api.request")
    def test_newest_pr_sorts_first(self, request, _supports, _swagger):
        request.return_value = [_pr(4, "b"), _pr(9, "b")]
        matches = pulls.find_open_prs_by_head(_CONFIG, "o/r", "b")
        self.assertEqual([pr["number"] for pr in matches], [9, 4])


@mock.patch("lib.forgejo.pulls.find_open_prs_by_head")
class QueryStateTest(unittest.TestCase):
    def test_no_open_pr_is_none(self, find):
        find.return_value = []
        self.assertEqual(
            pulls.query_state(_CONFIG, "o/r", "b", sleep=self.fail),
            ("none", None),
        )

    def test_draft_reports_before_mergeable_is_consulted(self, find):
        find.return_value = [_pr(4, "b", draft=True, mergeable=False)]
        state, pr = pulls.query_state(_CONFIG, "o/r", "b", sleep=self.fail)
        self.assertEqual(state, "draft")
        self.assertEqual(pr["number"], 4)

    def test_immediately_mergeable_needs_no_poll(self, find):
        find.return_value = [_pr(4, "b", mergeable=True)]
        state, _ = pulls.query_state(_CONFIG, "o/r", "b", sleep=self.fail)
        self.assertEqual(state, "mergeable")

    @mock.patch("lib.forgejo.pulls.get_pr")
    def test_mergeable_flipping_true_during_poll_wins(self, get_pr, find):
        find.return_value = [_pr(4, "b", mergeable=False)]
        get_pr.side_effect = [
            _pr(4, "b", mergeable=False), _pr(4, "b", mergeable=True),
        ]
        slept = []
        state, _ = pulls.query_state(_CONFIG, "o/r", "b", sleep=slept.append)
        self.assertEqual(state, "mergeable")
        self.assertEqual(slept, [1, 2])

    @mock.patch("lib.forgejo.pulls.get_pr")
    def test_mergeable_false_through_backoff_is_conflicted(self, get_pr, find):
        find.return_value = [_pr(4, "b", mergeable=False)]
        get_pr.return_value = _pr(4, "b", mergeable=False)
        slept = []
        state, _ = pulls.query_state(_CONFIG, "o/r", "b", sleep=slept.append)
        self.assertEqual(state, "conflicted")
        self.assertEqual(slept, list(pulls._POLL_DELAYS_SECONDS))


class CreatePrTest(unittest.TestCase):
    @mock.patch("lib.forgejo.pulls.api.request")
    def test_duplicate_pr_conflict_reclassifies_to_refused(self, request):
        request.side_effect = api.ApiError("HTTP 409", plan.EXIT_RUNTIME, 409)
        with self.assertRaises(api.ApiError) as caught:
            pulls.create_pr(_CONFIG, "o/r", "main", "b", "T", "body")
        self.assertEqual(caught.exception.exit_code, plan.EXIT_REFUSED)
        self.assertIn("already exists", str(caught.exception))

    @mock.patch("lib.forgejo.pulls.api.request")
    def test_other_failures_pass_through_unreclassified(self, request):
        request.side_effect = api.ApiError("HTTP 500", plan.EXIT_RUNTIME, 500)
        with self.assertRaises(api.ApiError) as caught:
            pulls.create_pr(_CONFIG, "o/r", "main", "b", "T", "body")
        self.assertEqual(caught.exception.exit_code, plan.EXIT_RUNTIME)

    @mock.patch("lib.forgejo.pulls.api.request")
    def test_posts_the_four_creation_fields(self, request):
        request.return_value = {"number": 8}
        pulls.create_pr(_CONFIG, "o/r", "main", "b", "T", "body text")
        self.assertEqual(
            request.call_args.kwargs["body"],
            {"base": "main", "head": "b", "title": "T", "body": "body text"},
        )


class BranchExistsTest(unittest.TestCase):
    @mock.patch("lib.forgejo.pulls.api.request")
    def test_not_found_is_false_other_errors_raise(self, request):
        request.side_effect = api.ApiError("gone", plan.EXIT_NOT_FOUND, 404)
        self.assertFalse(pulls.branch_exists(_CONFIG, "o/r", "b"))
        request.side_effect = api.ApiError("boom", plan.EXIT_RUNTIME, 500)
        with self.assertRaises(api.ApiError):
            pulls.branch_exists(_CONFIG, "o/r", "b")
        request.side_effect = None
        request.return_value = {"name": "b"}
        self.assertTrue(pulls.branch_exists(_CONFIG, "o/r", "b"))


class PaginationTest(unittest.TestCase):
    @mock.patch("lib.forgejo.pulls.api.request")
    def test_list_open_prs_paginates_to_exhaustion(self, request):
        full_page = [_pr(n, f"b{n}") for n in range(pulls._PAGE_SIZE)]
        request.side_effect = [full_page, [_pr(999, "last")]]
        prs = pulls.list_open_prs(_CONFIG, "o/r")
        self.assertEqual(len(prs), pulls._PAGE_SIZE + 1)
        pages = [c.kwargs["query"]["page"] for c in request.call_args_list]
        self.assertEqual(pages, ["1", "2"])

    @mock.patch("lib.forgejo.pulls.api.request")
    def test_list_comments_paginates_and_tolerates_null_page(self, request):
        request.side_effect = [[{"id": 1}], None]
        comments = pulls.list_comments(_CONFIG, "o/r", 5)
        self.assertEqual(comments, [{"id": 1}])
        # One call: the short first page already ended pagination.
        self.assertEqual(request.call_count, 1)


class ClosePrTest(unittest.TestCase):
    @mock.patch("lib.forgejo.pulls.api.request")
    def test_patches_state_closed(self, request):
        request.return_value = {"state": "closed"}
        pulls.close_pr(_CONFIG, "o/r", 5)
        self.assertEqual(request.call_args.args[1:], ("PATCH", "/repos/o/r/pulls/5"))
        self.assertEqual(request.call_args.kwargs["body"], {"state": "closed"})


if __name__ == "__main__":
    unittest.main()
