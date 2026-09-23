"""The gitw repo roster: ~/.config/gitw/repos.toml.

The novel gitw invariant made concrete: in ghw/fjw a `-R <owner/repo>`
argument prevents cwd from redirecting a write, but for git cwd *is* the
repo -- so every verb takes a leading repo *label* resolved here, and the
roster pins not just "which project" but "which blessed working copy". A
rogue second clone is refused even with the right URL. Wrappers only read
this file; registration is an attended user-blessed ceremony
(`gitw-repo-register`, ask-ruled), and removal is a hand-edit.

One TOML table per label:

    [field-notes]                       # the allowlist literal
    checkout = "/abs/path/to/checkout"  # required: the blessed working copy
    remote_url = "ssh://..."            # omit for a machine-local repo
    remote = "origin"                   # authoritative remote name
    default_branch = "main"             # the authoritative default branch
    operable_from = ["/abs/path", ...]  # extra cwd roots for ref-and-remote
                                        # verbs (cross-repo interlock)

`remote` and `default_branch` default to "origin" and "main"; `remote` is
meaningful only alongside `remote_url` (a machine-local entry with a remote
name is a contradiction and fails loud). Unknown keys fail loud too -- this
is a hand-editable policy file, and a typo'd key silently ignored would be
a policy hole.

Roster problems exit with the auth code (5), the fjw config precedent: to
an unattended caller a missing or malformed roster is a deployment problem
-- abort and flag it, never retry. The file should be mode 0600 (it maps
the machine's repo topology); like fjw, a looser mode warns but proceeds.

The TOML-subset parser below knowingly duplicates the flat one in
lib/forgejo/config.py (this one adds tables and arrays) so the gitw branch
does not touch fjw config; if a third subset appears, extract a shared
lib/toml_subset.py.
"""

from __future__ import annotations

import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

from lib import plan
from lib.git import arguments

DEFAULT_PATH = Path("~/.config/gitw/repos.toml")

_ENTRY_KEYS = ("checkout", "remote_url", "remote", "default_branch", "operable_from")
_REMOTE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


class RosterError(Exception):
    """Raised when the roster file is missing, unreadable, or malformed."""


class _TOMLSubsetError(ValueError):
    """Raised by _parse_toml_subset on anything outside the tabled subset."""


_HEADER = re.compile(r"^\[([^\]]*)\]\s*(?:#.*)?$")
_KEY_VALUE = re.compile(r"^([A-Za-z0-9_-]+)\s*=\s*(.+)$")


def _parse_string(raw: str, number: int) -> tuple[str, str]:
    """Parse one basic-quoted string at the start of `raw` (opening quote
    included). Returns (value, remainder-after-closing-quote). Escape
    sequences are outside the subset, as in the fjw parser."""
    end = raw.find('"', 1)
    if end < 0:
        raise _TOMLSubsetError(f"line {number}: unterminated string")
    value = raw[1:end]
    if "\\" in value:
        raise _TOMLSubsetError(
            f"line {number}: escape sequences are outside the supported "
            "TOML subset"
        )
    return value, raw[end + 1 :]


def _parse_value(raw_value: str, number: int):
    """Parse a value: a quoted string or a single-line array of quoted
    strings. Anything richer raises -- fail loud, never guess."""
    if raw_value.startswith('"'):
        value, trailer = _parse_string(raw_value, number)
        trailer = trailer.strip()
        if trailer and not trailer.startswith("#"):
            raise _TOMLSubsetError(f"line {number}: unexpected content after string")
        return value
    if raw_value.startswith("["):
        items: list = []
        rest = raw_value[1:].lstrip()
        while True:
            if not rest:
                raise _TOMLSubsetError(f"line {number}: unterminated array")
            if rest.startswith("]"):
                trailer = rest[1:].strip()
                if trailer and not trailer.startswith("#"):
                    raise _TOMLSubsetError(
                        f"line {number}: unexpected content after array"
                    )
                return items
            if not rest.startswith('"'):
                raise _TOMLSubsetError(
                    f"line {number}: arrays may hold only quoted strings"
                )
            value, rest = _parse_string(rest, number)
            items.append(value)
            rest = rest.lstrip()
            if rest.startswith(","):
                rest = rest[1:].lstrip()
            elif not rest.startswith("]"):
                raise _TOMLSubsetError(
                    f"line {number}: expected ',' or ']' in array"
                )
    raise _TOMLSubsetError(
        f"line {number}: value {raw_value!r} is outside the supported TOML "
        "subset (quoted string or array of quoted strings)"
    )


def _parse_toml_subset(text: str) -> dict:
    """Parse the tabled `[label]` / `key = value` subset of TOML the roster
    uses. Stands in for tomllib (3.11+), absent from Apple's
    /usr/bin/python3 (3.9) -- the interpreter the entry points pin to (see
    lib/forgejo/config.py for the Local Network rationale)."""
    tables: dict = {}
    current = None
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        header = _HEADER.match(line)
        if header is not None:
            label = header.group(1).strip()
            if not label:
                raise _TOMLSubsetError(f"line {number}: empty table name")
            if label in tables:
                raise _TOMLSubsetError(f"line {number}: duplicate table {label!r}")
            tables[label] = {}
            current = tables[label]
            continue
        match = _KEY_VALUE.match(line)
        if match is None:
            raise _TOMLSubsetError(
                f"line {number}: expected '[label]' or 'key = value'"
            )
        if current is None:
            raise _TOMLSubsetError(
                f"line {number}: key outside any [label] table"
            )
        key, raw_value = match.group(1), match.group(2).strip()
        if key in current:
            raise _TOMLSubsetError(f"line {number}: duplicate key {key!r}")
        current[key] = _parse_value(raw_value, number)
    return tables


@dataclass(frozen=True)
class Entry:
    """One rostered repo. `remote` is None exactly when `remote_url` is
    (machine-local: the local default branch *is* the authoritative
    instance, and freshness rules degrade accordingly)."""

    label: str
    checkout: Path
    remote_url: str | None = None
    remote: str | None = None
    default_branch: str = "main"
    operable_from: tuple = ()

    @property
    def machine_local(self) -> bool:
        return self.remote_url is None


def _absolute_path(value, label: str, key: str, path: Path) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise RosterError(f"{path}: [{label}] {key!r} must be a non-empty string")
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        raise RosterError(
            f"{path}: [{label}] {key!r} must be an absolute path, got {value!r}"
        )
    return candidate


def _build_entry(label: str, raw: dict, path: Path) -> Entry:
    if not arguments.is_valid_label(label):
        raise RosterError(
            f"{path}: label {label!r} is not a valid roster label (lowercase "
            "alphanumerics plus ._- only)"
        )
    for key in raw:
        if key not in _ENTRY_KEYS:
            raise RosterError(
                f"{path}: [{label}] unknown key {key!r} (allowed: "
                f"{', '.join(_ENTRY_KEYS)})"
            )
    if "checkout" not in raw:
        raise RosterError(f"{path}: [{label}] is missing required key 'checkout'")
    checkout = _absolute_path(raw["checkout"], label, "checkout", path)

    remote_url = raw.get("remote_url")
    if remote_url is not None and (
        not isinstance(remote_url, str) or not remote_url.strip()
    ):
        raise RosterError(
            f"{path}: [{label}] 'remote_url' must be a non-empty string"
        )
    remote = raw.get("remote")
    if remote_url is None:
        if remote is not None:
            raise RosterError(
                f"{path}: [{label}] has 'remote' but no 'remote_url' -- a "
                "machine-local entry names no remote"
            )
    else:
        if remote is None:
            remote = "origin"
        if not isinstance(remote, str) or not _REMOTE_NAME_PATTERN.match(remote):
            raise RosterError(
                f"{path}: [{label}] 'remote' must be a plain remote name, "
                f"got {remote!r}"
            )

    default_branch = raw.get("default_branch", "main")
    if not isinstance(default_branch, str) or not _BRANCH_PATTERN.match(
        default_branch
    ):
        raise RosterError(
            f"{path}: [{label}] 'default_branch' must be a branch name, "
            f"got {default_branch!r}"
        )

    operable_raw = raw.get("operable_from", [])
    if not isinstance(operable_raw, list):
        raise RosterError(
            f"{path}: [{label}] 'operable_from' must be an array of "
            "absolute paths"
        )
    operable_from = tuple(
        _absolute_path(item, label, "operable_from", path) for item in operable_raw
    )

    return Entry(
        label=label,
        checkout=checkout,
        remote_url=remote_url.strip() if remote_url else None,
        remote=remote,
        default_branch=default_branch,
        operable_from=operable_from,
    )


def load(path_for_testing: Path | None = None) -> dict:
    """Load and validate the roster; returns {label: Entry}.

    Raises RosterError on a missing file, unparseable TOML, or an invalid
    entry. Warns on stderr (but proceeds) when the file is readable by
    group/other -- it should be mode 0600, per the fjw config precedent.

    `path_for_testing` substitutes the roster path in unit tests;
    production callers must never pass it.
    """
    path = (path_for_testing or DEFAULT_PATH).expanduser()
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise RosterError(
            f"cannot read {path}: {error.strerror or error}; gitw requires "
            "the repo roster -- create it there (format documented in "
            "lib/git/roster.py)"
        )
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError:
        mode = 0  # vanished between read and stat; the content is in hand
    if mode & 0o077:
        print(
            f"warning: {path} is mode {mode:o}; it maps this machine's repo "
            "topology and should be 0600",
            file=sys.stderr,
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RosterError(f"cannot parse {path}: {error}")
    return validate_text(text, path)


def validate_text(text: str, path: Path) -> dict:
    """Parse and validate roster-shaped TOML text; returns {label: Entry}.

    The shared back half of load() -- gitw-repo-register also runs its
    candidate roster (existing text plus the appended delta) through this
    before writing, so nothing unloadable ever lands on disk. `path` only
    names the source in error messages. Raises RosterError.
    """
    try:
        tables = _parse_toml_subset(text)
    except _TOMLSubsetError as error:
        raise RosterError(f"cannot parse {path}: {error}")
    return {
        label: _build_entry(label, table, path) for label, table in tables.items()
    }


def resolve_or_die(label: str, usage: str) -> Entry:
    """Validate `label`, load the roster, and return its entry -- the
    shared front half of every gitw verb. Exits on each failure: a
    malformed label is a usage error (2), roster problems are deployment
    problems (5, fjw precedent), an unknown label is not-found (3) with
    the known labels named so the caller can self-correct."""
    if not arguments.is_valid_label(label):
        plan.usage_die(
            f"repo label must be lowercase alphanumerics plus ._- , got "
            f"{label!r}",
            usage,
        )
    try:
        entries = load()
    except RosterError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(plan.EXIT_AUTH)
    entry = entries.get(label)
    if entry is None:
        print(
            f"error: label {label!r} is not in the roster; known labels: "
            f"{', '.join(sorted(entries)) or '(none)'}",
            file=sys.stderr,
        )
        sys.exit(plan.EXIT_NOT_FOUND)
    return entry
