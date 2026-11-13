"""Tests for the Forgejo HTTP layer: error classification, request shaping,
and the swagger feature probe. All network I/O is mocked at urlopen.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import email.message
import http.client
import io
import json
import unittest
import urllib.error
from unittest import mock

from lib import plan
from lib.forgejo import api
from lib.forgejo.config import Config

_CONFIG = Config(api_url="https://forge.example.com", token="sekrit")


def _http_error(
    case: unittest.TestCase, code: int, body: bytes = b"", headers=None
) -> urllib.error.HTTPError:
    error = urllib.error.HTTPError(
        "https://forge.example.com/api/v1/x", code, "msg",
        email.message.Message() if headers is None else headers,
        io.BytesIO(body),
    )
    case.addCleanup(error.close)  # silence the ResourceWarning at GC
    return error


def _response(payload, status: int = 200):
    """A minimal urlopen context-manager stand-in."""
    reply = mock.MagicMock()
    reply.read.return_value = json.dumps(payload).encode()
    reply.status = status
    context = mock.MagicMock()
    context.__enter__.return_value = reply
    return context


class RequestTest(unittest.TestCase):
    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_success_returns_parsed_json(self, urlopen):
        urlopen.return_value = _response({"number": 7})
        self.assertEqual(
            api.request(_CONFIG, "GET", "/repos/o/r/pulls/7"), {"number": 7}
        )

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_request_carries_token_and_user_agent(self, urlopen):
        urlopen.return_value = _response([])
        api.request(_CONFIG, "GET", "/repos/o/r/pulls")
        request = urlopen.call_args[0][0]
        self.assertEqual(request.get_header("Authorization"), "token sekrit")
        self.assertEqual(request.get_header("User-agent"), api.USER_AGENT)
        self.assertEqual(
            request.full_url, "https://forge.example.com/api/v1/repos/o/r/pulls"
        )

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_query_values_are_url_encoded(self, urlopen):
        urlopen.return_value = _response([])
        api.request(
            _CONFIG, "GET", "/repos/o/r/pulls", query={"head": "bot/a b"}
        )
        self.assertIn(
            "?head=bot%2Fa+b", urlopen.call_args[0][0].full_url
        )

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_body_is_posted_as_json(self, urlopen):
        urlopen.return_value = _response({})
        api.request(_CONFIG, "POST", "/repos/o/r/pulls", body={"base": "main"})
        request = urlopen.call_args[0][0]
        self.assertEqual(json.loads(request.data), {"base": "main"})
        self.assertEqual(request.get_header("Content-type"), "application/json")

    def test_relative_path_is_a_programming_error(self):
        with self.assertRaises(ValueError):
            api.request(_CONFIG, "GET", "repos/o/r/pulls")

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_http_statuses_classify_into_the_contract(self, urlopen):
        for status, expected in (
            (401, plan.EXIT_BROKEN),  # credentials: the deployment's to fix
            (403, plan.EXIT_FORBIDDEN),  # a grant too weak for the action
            (404, plan.EXIT_NOT_FOUND),
            (409, plan.EXIT_BROKEN),  # Verb-specific meaning is the caller's
            (429, plan.EXIT_BROKEN),  # rate limiting
            (500, plan.EXIT_BROKEN),
        ):
            with self.subTest(status=status):
                urlopen.side_effect = _http_error(self, status)
                with self.assertRaises(api.ApiError) as caught:
                    api.request(_CONFIG, "GET", "/x")
                self.assertEqual(caught.exception.exit_code, expected)
                self.assertEqual(caught.exception.status, status)

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_rate_limit_403_is_broken_not_forbidden(self, urlopen):
        # Retry-After marks a 403 as rate limiting, which is not the
        # caller's grant.
        headers = email.message.Message()
        headers["Retry-After"] = "30"
        urlopen.side_effect = _http_error(self, 403, headers=headers)
        with self.assertRaises(api.ApiError) as caught:
            api.request(_CONFIG, "GET", "/x")
        self.assertEqual(caught.exception.exit_code, plan.EXIT_BROKEN)
        self.assertIn("rate limited", str(caught.exception))

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_forbidden_403_says_to_ask_a_human(self, urlopen):
        urlopen.side_effect = _http_error(self, 403)
        with self.assertRaises(api.ApiError) as caught:
            api.request(_CONFIG, "PATCH", "/x")
        self.assertIn("grant is too weak", str(caught.exception))

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_server_message_is_surfaced(self, urlopen):
        urlopen.side_effect = _http_error(self, 409, b'{"message": "pull exists"}')
        with self.assertRaises(api.ApiError) as caught:
            api.request(_CONFIG, "POST", "/x")
        self.assertIn("pull exists", str(caught.exception))

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_connection_failure_is_broken(self, urlopen):
        urlopen.side_effect = urllib.error.URLError("refused")
        with self.assertRaises(api.ApiError) as caught:
            api.request(_CONFIG, "GET", "/x")
        self.assertEqual(caught.exception.exit_code, plan.EXIT_BROKEN)
        self.assertNotIn("may or may not have landed", str(caught.exception))

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_transport_failure_on_a_write_says_it_may_have_landed(self, urlopen):
        for method in ("POST", "PATCH"):
            with self.subTest(method=method):
                urlopen.side_effect = urllib.error.URLError("reset")
                with self.assertRaises(api.ApiError) as caught:
                    api.request(_CONFIG, method, "/x", body={})
                self.assertEqual(caught.exception.exit_code, plan.EXIT_BROKEN)
                self.assertIn("may or may not have landed", str(caught.exception))

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_truncated_response_is_broken(self, urlopen):
        urlopen.side_effect = http.client.IncompleteRead(b"par")
        with self.assertRaises(api.ApiError) as caught:
            api.request(_CONFIG, "POST", "/x", body={})
        self.assertEqual(caught.exception.exit_code, plan.EXIT_BROKEN)
        self.assertIn("may or may not have landed", str(caught.exception))

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_timeout_is_broken(self, urlopen):
        urlopen.side_effect = TimeoutError("timed out")
        with self.assertRaises(api.ApiError) as caught:
            api.request(_CONFIG, "GET", "/x")
        self.assertEqual(caught.exception.exit_code, plan.EXIT_BROKEN)

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_non_json_success_body_is_broken(self, urlopen):
        reply = mock.MagicMock()
        reply.read.return_value = b"<html>gateway</html>"
        reply.status = 200
        context = mock.MagicMock()
        context.__enter__.return_value = reply
        urlopen.return_value = context
        with self.assertRaises(api.ApiError) as caught:
            api.request(_CONFIG, "GET", "/x")
        self.assertEqual(caught.exception.exit_code, plan.EXIT_BROKEN)

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_empty_body_returns_none(self, urlopen):
        reply = mock.MagicMock()
        reply.read.return_value = b""
        reply.status = 204
        context = mock.MagicMock()
        context.__enter__.return_value = reply
        urlopen.return_value = context
        self.assertIsNone(api.request(_CONFIG, "DELETE", "/x"))


def _swagger_with_pull_list_parameters(parameters: list) -> dict:
    return {
        "paths": {
            "/repos/{owner}/{repo}/pulls": {"get": {"parameters": parameters}}
        }
    }


class SupportsHeadFilterTest(unittest.TestCase):
    def test_head_query_parameter_means_supported(self):
        swagger = _swagger_with_pull_list_parameters(
            [{"name": "state", "in": "query"}, {"name": "head", "in": "query"}]
        )
        self.assertTrue(api.supports_head_filter(swagger))

    def test_absent_head_parameter_means_unsupported(self):
        swagger = _swagger_with_pull_list_parameters(
            [{"name": "state", "in": "query"}]
        )
        self.assertFalse(api.supports_head_filter(swagger))

    def test_head_elsewhere_than_query_does_not_count(self):
        swagger = _swagger_with_pull_list_parameters(
            [{"name": "head", "in": "path"}]
        )
        self.assertFalse(api.supports_head_filter(swagger))

    def test_missing_or_malformed_swagger_means_unsupported(self):
        for swagger in (None, {}, {"paths": {}}, {"paths": "bogus"}, 42):
            with self.subTest(swagger=swagger):
                self.assertFalse(api.supports_head_filter(swagger))


class FetchSwaggerTest(unittest.TestCase):
    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_fetch_failure_returns_none(self, urlopen):
        urlopen.side_effect = urllib.error.URLError("down")
        self.assertIsNone(api.fetch_swagger(_CONFIG))

    @mock.patch("lib.forgejo.api.urllib.request.urlopen")
    def test_fetches_the_instances_own_description(self, urlopen):
        urlopen.return_value = _response({"paths": {}})
        self.assertEqual(api.fetch_swagger(_CONFIG), {"paths": {}})
        self.assertEqual(
            urlopen.call_args[0][0].full_url,
            "https://forge.example.com/swagger.v1.json",
        )


if __name__ == "__main__":
    unittest.main()
