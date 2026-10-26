"""Where bdw's push keeps its state, and the two questions every bdw call
asks of it: is a push owed, and did the last one fail.

Kept apart from lib.bdw_push, which does the pushing, so that a bdw call
with nothing owed and nothing failed pays only for a hash and two file
checks, not for the push machinery's imports.

The state is Machine State (docs/adr/0015-three-roots-for-machine-
specific-files.md), in `push/<key>/` under bdw's subdirectory of the
Machine State Directory, as lib.paths resolves it; `<key>` is a hash of
the Beads directory. The write markers: a write leaves PENDING; a pass
about to push renames it to PUSHING, and deletes PUSHING only once the
push's outcome is recorded, so a PUSHING left behind means a push that was
taken and never finished.

Standard library only; Python 3.9.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

from lib import paths

PENDING = "pending"
PUSHING = "pushing"
LAST_FAILURE = "last-failure.json"

# The values, compared case-insensitively after trimming, that turn the
# push off: in BD_NO_PUSH, and in bd's `no-push` config as `bd config get`
# prints it (the raw value, such as `1` or `yes`). bdw is the one that
# pushes, so this set, not bd's own parsing, decides; it takes the forms
# Go's strconv.ParseBool reads as true (1, t, true) plus yes and on. bdw's
# pre-spawn opt-out and the worker's check share it.
TRUTHY = frozenset({"1", "t", "true", "yes", "on"})


def is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in TRUTHY


def state_dir(beads_dir: Path, environ: Mapping[str, str]) -> Path | None:
    """The per-database push state directory, `push/<key>/` in bdw's
    subdirectory of the Machine State Directory (lib.paths), `<key>` a hash
    of the Beads directory; None when lib.paths finds no state root."""
    tool = paths.state_dir("bdw", environ)
    if tool is None:
        return None
    key = hashlib.sha256(
        str(beads_dir.resolve()).encode("utf-8")).hexdigest()[:16]
    return tool / "push" / key


def push_owed(state: Path) -> bool:
    """Whether a write is waiting to be pushed, or a push was taken and
    never finished."""
    return (state / PENDING).exists() or (state / PUSHING).exists()


def last_failure(state: Path) -> dict | None:
    """The last push failure, or None when the last push succeeded."""
    try:
        payload = json.loads((state / LAST_FAILURE).read_text())
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None
