"""The fjw deployment-config file: ~/.config/fjw/config.toml.

This file is the stable interface between the wrappers and the deployment
(your deployment tooling provisions and rotates the machine-account token by
rewriting it; no consumer-side change is ever needed). Calling agents never see the
token: user-level deny rules cover ~/.config/fjw/** wholesale, and no fjw
verb ever prints it.

Keys:
    api_url  -- base URL of the Forgejo instance (https://host[:port][/path]);
                a trailing /api/v1 is tolerated and normalized away
    token    -- the machine-account API token (scopes: write:repository +
                write:issue)
    ssh_host -- optional: the git-over-SSH host, which differs from the API
                host (hostname reconciliation is deployment config, never a
                caller concern)
    ssh_port -- optional: the git-over-SSH port

Config problems exit with the auth code (5): to an unattended caller a
missing or malformed config is indistinguishable from revoked credentials --
abort and flag the deployment, never retry.
"""

from __future__ import annotations

import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATH = Path("~/.config/fjw/config.toml")


class ConfigError(Exception):
    """Raised when the config file is missing, unreadable, or malformed."""


class _TOMLSubsetError(ValueError):
    """Raised by _parse_toml_subset on anything outside the flat subset."""


_KEY_VALUE = re.compile(r"^([A-Za-z0-9_-]+)\s*=\s*(.+)$")
_INTEGER = re.compile(r"^[+-]?[0-9](?:_?[0-9])*$")


def _parse_toml_subset(text: str) -> dict:
    """Parse the flat `key = value` subset of TOML this config uses.

    Stands in for tomllib (3.11+), absent from Apple's /usr/bin/python3
    (3.9) -- the interpreter the fjw entry points pin to because macOS
    Local Network privacy silently denies non-Apple binaries in
    background-agent contexts (no responsible app to hold the grant), and
    Apple platform binaries are exempt. Supported: blank lines, comments,
    basic-quoted strings without escapes, integers, booleans. Anything
    richer raises -- fail loud (exit 5 upstream), never guess.
    """
    data: dict = {}
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _KEY_VALUE.match(line)
        if match is None:
            raise _TOMLSubsetError(f"line {number}: expected 'key = value'")
        key, raw_value = match.group(1), match.group(2).strip()
        if key in data:
            raise _TOMLSubsetError(f"line {number}: duplicate key {key!r}")
        if raw_value.startswith('"'):
            end = raw_value.find('"', 1)
            if end < 0:
                raise _TOMLSubsetError(f"line {number}: unterminated string")
            value = raw_value[1:end]
            trailer = raw_value[end + 1 :].strip()
            if "\\" in value:
                raise _TOMLSubsetError(
                    f"line {number}: escape sequences are outside the "
                    "supported TOML subset"
                )
            if trailer and not trailer.startswith("#"):
                raise _TOMLSubsetError(
                    f"line {number}: unexpected content after string"
                )
        else:
            bare = raw_value.split("#", 1)[0].strip()
            if bare == "true":
                value = True
            elif bare == "false":
                value = False
            elif _INTEGER.match(bare):
                value = int(bare.replace("_", ""))
            else:
                raise _TOMLSubsetError(
                    f"line {number}: value {bare!r} is outside the supported "
                    "TOML subset (quoted string, integer, or boolean)"
                )
        data[key] = value
    return data


@dataclass(frozen=True)
class Config:
    api_url: str
    token: str
    ssh_host: str | None = None
    ssh_port: int | None = None


def load(path_for_testing: Path | None = None) -> Config:
    """Load and validate the config file.

    Raises ConfigError on a missing file, unparseable TOML, missing required
    keys, or wrongly-typed values. Warns on stderr (but proceeds) when the
    file is readable by group/other -- it should be mode 0600.

    `path_for_testing` substitutes the config path in unit tests; production
    callers must never pass it.
    """
    path = (path_for_testing or DEFAULT_PATH).expanduser()
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ConfigError(
            f"cannot read {path}: {error.strerror or error}; "
            "fjw requires the deployment config described in its header"
        )
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        print(
            f"warning: {path} is mode {mode:o}; it holds a credential and "
            "should be 0600",
            file=sys.stderr,
        )
    try:
        data = _parse_toml_subset(raw.decode("utf-8"))
    except (_TOMLSubsetError, UnicodeDecodeError) as error:
        raise ConfigError(f"cannot parse {path}: {error}")

    api_url = data.get("api_url")
    token = data.get("token")
    if not isinstance(api_url, str) or not api_url.strip():
        raise ConfigError(f"{path}: 'api_url' must be a non-empty string")
    if not isinstance(token, str) or not token.strip():
        raise ConfigError(f"{path}: 'token' must be a non-empty string")
    if not api_url.startswith("https://"):
        raise ConfigError(
            f"{path}: 'api_url' must be https:// -- the token rides every "
            "request"
        )
    ssh_host = data.get("ssh_host")
    if ssh_host is not None and not isinstance(ssh_host, str):
        raise ConfigError(f"{path}: 'ssh_host' must be a string")
    ssh_port = data.get("ssh_port")
    if ssh_port is not None and (isinstance(ssh_port, bool) or not isinstance(ssh_port, int)):
        raise ConfigError(f"{path}: 'ssh_port' must be an integer")

    normalized = api_url.strip().rstrip("/")
    if normalized.endswith("/api/v1"):
        normalized = normalized[: -len("/api/v1")]
    return Config(
        api_url=normalized,
        token=token.strip(),
        ssh_host=ssh_host,
        ssh_port=ssh_port,
    )
