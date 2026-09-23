"""Tests for the fjw deployment-config loader.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from lib.forgejo import config


def _write_config(text: str, mode: int = 0o600) -> Path:
    os.makedirs("/tmp/claude", exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w", dir="/tmp/claude", suffix=".toml", delete=False
    )
    handle.write(text)
    handle.close()
    os.chmod(handle.name, mode)
    return Path(handle.name)


_VALID = 'api_url = "https://forge.example.com"\ntoken = "sekrit"\n'


class LoadTest(unittest.TestCase):
    def _load(self, text: str, mode: int = 0o600) -> config.Config:
        path = _write_config(text, mode)
        self.addCleanup(os.unlink, path)
        return config.load(path_for_testing=path)

    def test_valid_config_loads(self):
        loaded = self._load(_VALID)
        self.assertEqual(loaded.api_url, "https://forge.example.com")
        self.assertEqual(loaded.token, "sekrit")
        self.assertIsNone(loaded.ssh_host)
        self.assertIsNone(loaded.ssh_port)

    def test_ssh_pair_loads(self):
        loaded = self._load(_VALID + 'ssh_host = "git.example.com"\nssh_port = 2222\n')
        self.assertEqual(loaded.ssh_host, "git.example.com")
        self.assertEqual(loaded.ssh_port, 2222)

    def test_api_url_trailing_slash_and_api_v1_suffix_normalize_away(self):
        for url in (
            "https://forge.example.com/",
            "https://forge.example.com/api/v1",
            "https://forge.example.com/api/v1/",
        ):
            with self.subTest(url=url):
                loaded = self._load(f'api_url = "{url}"\ntoken = "t"\n')
                self.assertEqual(loaded.api_url, "https://forge.example.com")

    def test_subpath_instance_url_survives_normalization(self):
        loaded = self._load('api_url = "https://example.com/forgejo/"\ntoken = "t"\n')
        self.assertEqual(loaded.api_url, "https://example.com/forgejo")

    def test_missing_file_is_config_error(self):
        with self.assertRaises(config.ConfigError) as caught:
            config.load(path_for_testing=Path("/tmp/claude/fjw-no-such-config.toml"))
        self.assertIn("cannot read", str(caught.exception))

    def test_unparseable_toml_is_config_error(self):
        with self.assertRaises(config.ConfigError):
            self._load("api_url = https://unquoted\n")

    def test_missing_required_keys_are_config_errors(self):
        for text in ('token = "t"\n', 'api_url = "https://x.example"\n'):
            with self.subTest(text=text):
                with self.assertRaises(config.ConfigError):
                    self._load(text)

    def test_http_url_is_refused(self):
        # The token rides every request; plaintext transport is never OK.
        with self.assertRaises(config.ConfigError) as caught:
            self._load('api_url = "http://forge.example.com"\ntoken = "t"\n')
        self.assertIn("https", str(caught.exception))

    def test_non_integer_ssh_port_is_config_error(self):
        for port in ('"2222"', "true"):
            with self.subTest(port=port):
                with self.assertRaises(config.ConfigError):
                    self._load(_VALID + f"ssh_port = {port}\n")

    def test_group_readable_file_warns_but_loads(self):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            loaded = self._load(_VALID, mode=0o640)
        self.assertEqual(loaded.token, "sekrit")
        self.assertIn("0600", stderr.getvalue())

    def test_tight_mode_does_not_warn(self):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            self._load(_VALID, mode=0o600)
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
