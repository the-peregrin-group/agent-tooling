"""Shared profile reader for the triage-issues wrapper scripts.

The per-project profile (`TRIAGE.md`) carries one machine-readable config block,
fenced and marker-delimited so it can be extracted from the surrounding prose:

    <!-- BEGIN triage-config -->
    ```json
    { ... }
    ```
    <!-- END triage-config -->

This module is the *only* place the config format is parsed. Everything
project-specific (opaque field/option/node IDs, label schema, tuning) lives in
that block and is read exclusively through here, so:
  - no opaque ID ever appears in a shell command, settings file, or allowlist;
  - the wrapper allowlist stays project-agnostic (wrapper *names* only);
  - swapping the on-disk format (e.g. JSON -> YAML) touches this file alone.

Format choice (JSON over YAML) is deliberate: stdlib-only parsing means the
wrappers import cleanly under any python, including an unattended/headless pass,
with no venv or third-party dependency to bootstrap.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_BEGIN = "<!-- BEGIN triage-config -->"
_END = "<!-- END triage-config -->"
_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*$", re.MULTILINE)


class ProfileError(Exception):
    """Raised when the profile is missing, malformed, or incomplete."""


def _locate(explicit: str | None) -> Path:
    """Resolve the profile path: explicit arg > env > search up from cwd."""
    if explicit:
        p = Path(explicit).expanduser()
        if not p.is_file():
            raise ProfileError(f"profile not found: {p}")
        return p
    env = os.environ.get("TRIAGE_PROFILE")
    if env:
        p = Path(env).expanduser()
        if not p.is_file():
            raise ProfileError(f"TRIAGE_PROFILE points at a missing file: {p}")
        return p
    # The cwd search is bounded to the enclosing git work tree (stop at the
    # first directory containing a .git entry, inclusive) -- same rule as the
    # ghw shared library. A stray TRIAGE.md in /tmp or $HOME must never
    # decide a repo's profile.
    here = Path.cwd()
    dirs = (here, *here.parents)
    for boundary, d in enumerate(dirs):
        if (d / ".git").exists():
            break
    else:
        raise ProfileError(
            "no TRIAGE.md found (cwd is not inside a git work tree); "
            "pass --profile or set TRIAGE_PROFILE"
        )
    for d in dirs[: boundary + 1]:
        cand = d / "TRIAGE.md"
        if cand.is_file():
            return cand
    raise ProfileError(
        "no TRIAGE.md found (searched up to the git work-tree root); "
        "pass --profile or set TRIAGE_PROFILE"
    )


def _extract_block(text: str, path: Path) -> dict:
    try:
        start = text.index(_BEGIN) + len(_BEGIN)
        end = text.index(_END, start)
    except ValueError:
        raise ProfileError(
            f"{path}: missing the {_BEGIN!r} / {_END!r} config block"
        )
    inner = text[start:end]
    # strip the markdown code fence if present
    inner = _FENCE_RE.sub("", inner).strip()
    try:
        return json.loads(inner)
    except json.JSONDecodeError as e:
        raise ProfileError(f"{path}: config block is not valid JSON: {e}")


def _require(d: dict, key: str, path: Path, ctx: str = ""):
    if key not in d or d[key] in (None, ""):
        where = f"{ctx}." if ctx else ""
        raise ProfileError(f"{path}: required config field missing: {where}{key}")
    return d[key]


class Profile:
    """Validated, typed view over the profile config block."""

    def __init__(self, raw: dict, path: Path):
        self.path = path
        self.raw = raw

        repo = _require(raw, "repo", path)
        if "/" not in repo:
            raise ProfileError(f"{path}: repo must be 'owner/name', got {repo!r}")
        self.repo = repo
        self.owner, self.name = repo.split("/", 1)

        self.project_number = int(_require(raw, "project_number", path))
        self.project_node_id = _require(raw, "project_node_id", path)

        fields = _require(raw, "fields", path)
        self.status_field_id = _require(fields.get("status", {}), "id", path, "fields.status")
        self.status_options = dict(_require(fields.get("status", {}), "options", path, "fields.status"))
        self.priority_field_id = _require(fields.get("priority", {}), "id", path, "fields.priority")
        self.priority_options = dict(_require(fields.get("priority", {}), "options", path, "fields.priority"))
        # Size is optional ("not used" projects).
        size = fields.get("size") or {}
        self.size_field_id = size.get("id")
        self.size_options = dict(size.get("options", {}))
        self.last_triaged_field_id = _require(
            fields.get("last_triaged", {}), "id", path, "fields.last_triaged"
        )

        labels = raw.get("labels", {})
        self.type_labels = list(labels.get("type", []))
        self.area_labels = list(labels.get("area", []))

        stale = raw.get("staleness", {})
        self.staleness_multiplier = float(stale.get("multiplier", 1))
        self.threshold_overrides = dict(stale.get("threshold_overrides", {}))
        self.bot_whitelist = set(stale.get("bot_whitelist", []))

        pmd = raw.get("pm_distribution", {})
        self.p0_cap = int(pmd.get("p0_cap", 3))
        self.collapse_pct = float(pmd.get("collapse_pct", 80))
        self.min_prioritized = int(pmd.get("min_n", 10))

        self.cadence = dict(raw.get("cadence", {}))

        # Ledger issue: structurally optional pre-bootstrap (null), but any
        # ledger-touching wrapper must assert it (see require_ledger()).
        self.ledger_issue = raw.get("ledger_issue")

    # -- accessors with friendly errors -------------------------------------

    def status_option_id(self, canonical_state: str) -> str:
        try:
            return self.status_options[canonical_state]
        except KeyError:
            raise ProfileError(
                f"{self.path}: no Status option mapping for {canonical_state!r} "
                f"(have: {', '.join(self.status_options)})"
            )

    def priority_option_id(self, level: str) -> str:
        try:
            return self.priority_options[level]
        except KeyError:
            raise ProfileError(f"{self.path}: no Priority option mapping for {level!r}")

    def size_option_id(self, size: str) -> str:
        if not self.size_field_id:
            raise ProfileError(f"{self.path}: Size field not configured for this project")
        try:
            return self.size_options[size]
        except KeyError:
            raise ProfileError(f"{self.path}: no Size option mapping for {size!r}")

    def is_known_label(self, label: str) -> bool:
        return label in self.type_labels or label in self.area_labels

    def require_ledger(self) -> int:
        if self.ledger_issue in (None, "", 0):
            raise ProfileError(
                f"{self.path}: ledger_issue is not set. Run the one-time bootstrap "
                "(create the ledger issue, write its number into the profile) before "
                "any ledger operation."
            )
        return int(self.ledger_issue)


def load(explicit: str | None = None) -> Profile:
    path = _locate(explicit)
    text = path.read_text(encoding="utf-8")
    return Profile(_extract_block(text, path), path)


def add_common_args(parser):
    """Register the --profile flag shared by every wrapper."""
    parser.add_argument(
        "--profile",
        default=None,
        help="Path to the project's TRIAGE.md (default: TRIAGE.md found upward from cwd)",
    )


def load_or_die(args) -> Profile:
    try:
        return load(getattr(args, "profile", None))
    except ProfileError as e:
        print(f"triage profile error: {e}", file=sys.stderr)
        sys.exit(2)
