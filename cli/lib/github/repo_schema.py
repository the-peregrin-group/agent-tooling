"""A GitHub repo's Tracker Schema, read from `TRACKER.md` on its default branch.

The one way a ghw Verb gets a repo's Tracker Schema. `load(repository)`
fetches the file through `gh` in one GraphQL request, parses it with the
reader (lib.tracker_schema), prints every problem as a warning on stderr,
and returns a RepoSchema. There is no local-file input and no fallback to
the shipped default: a change to a repo's labels or states goes through the
repo's own review, by merging `TRACKER.md`, before a Verb acts on it
(docs/projects/use-issues/design.md, "How a Wrapper uses the schema").

Loading never fails. A repo with no `TRACKER.md`, a file the reader cannot
read at all, and a fetch that fails all give a RepoSchema with no schema
and a warning saying why, because most of what a Verb does needs nothing
from the schema, and the rest degrades:

  - a read, or a write that needs nothing from the schema, goes ahead;
  - an additive write checks what `section(...)` can still give it and goes
    ahead on the rest;
  - a destructive write calls `require_complete(...)` on every section it
    derives from, and is refused (SchemaIncomplete, which the Verb turns
    into exit 4) when any is missing, unusable, or incomplete.

Which class each of a Verb's actions falls in is the Verb's decision,
recorded in docs/projects/ghw/design.md.

Standard library only, Python 3.9.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Optional, TextIO, Tuple

from lib import plan, tracker_schema
from lib.github import gh

PATH = "TRACKER.md"

# Each section of the reader, by the TrackerSchema property that gives it.
_PROPERTIES = {
    tracker_schema.PROVENANCE: "provenance",
    tracker_schema.ISSUE_KINDS: "issue_kinds",
    tracker_schema.ISSUE_PRIORITIES: "issue_priorities",
    tracker_schema.LABEL_AXES: "label_axes",
    tracker_schema.UNAXED_LABELS: "unaxed_labels",
    tracker_schema.ISSUE_STATES: "issue_states",
    tracker_schema.CLOSE_REASONS: "close_reasons",
}

# The file at PATH on the repo's default branch, with the branch's name, so
# the read is pinned to the default branch whatever the repo's HEAD says.
_QUERY = """
query($owner: String!, $name: String!, $path: String!) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      name
      target {
        ... on Commit {
          file(path: $path) {
            object { ... on Blob { text isBinary isTruncated } }
          }
        }
      }
    }
  }
}
"""


class SchemaIncomplete(Exception):
    """A destructive write needs a part of the Tracker Schema that is
    missing, unusable, or incomplete. The message names the part and why."""


@dataclass(frozen=True)
class RepoSchema:
    """What a repo's `TRACKER.md` gave, and why not when it gave nothing.

    `schema` is the reader's result, or None when there is none to read;
    `failure` then says why (a missing file, an unreadable block, a failed
    fetch). `branch` is the default branch's name, or None when it could not
    be learned. `fetch_exit_code` is a failed fetch's exit code class
    (lib.plan's EXIT_NETWORK, EXIT_AUTH, and so on), or None when nothing
    failed in the fetch itself, so that a Verb refusing a destructive write
    for want of the schema can exit with a transient fault's own code
    rather than as a refusal."""

    repository: str
    branch: Optional[str]
    schema: Optional[tracker_schema.TrackerSchema]
    failure: Optional[tracker_schema.TrackerSchemaError] = None
    fetch_exit_code: Optional[int] = None

    @property
    def source(self) -> str:
        """The file, named as warnings and refusals name it."""
        return f"{self.repository}@{self.branch or 'default-branch'}:{PATH}"

    def warning_lines(self) -> Tuple[str, ...]:
        """One stderr line per problem, in the reader's words."""
        result = self.schema if self.schema is not None else self.failure
        return tracker_schema.warning_lines(result, self.source)

    def summary(self) -> dict:
        """The `tracker_schema` value a Verb's JSON output carries: which
        file it read, whether it could be read at all, and how many
        warnings it gave."""
        return {
            "source": self.source,
            "readable": self.schema is not None,
            "warnings": len(self.warning_lines()),
        }

    def usable(self, section: str) -> bool:
        return self.schema is not None and self.schema.usable(section)

    def section(self, section: str):
        """The section's value (what the reader's property of the same name
        gives), or None when there is no schema or the section is unusable.
        The problems behind a None were already warned about."""
        if not self.usable(section):
            return None
        return getattr(self.schema, _PROPERTIES[section])

    def refusal_exit_code(self) -> int:
        """The exit code for a destructive write this schema cannot back: a
        transient fetch fault (network, auth) keeps its own class, so a
        caller can retry or flag it; anything else is a refusal."""
        if self.fetch_exit_code in (plan.EXIT_NETWORK, plan.EXIT_AUTH):
            return self.fetch_exit_code
        return plan.EXIT_REFUSED

    def require_complete(self, *sections: str) -> None:
        """Raise SchemaIncomplete for the first of `sections` that is not
        complete, naming it."""
        if self.schema is None:
            raise SchemaIncomplete(
                f"{self.source}: {self.failure.detail}, so "
                f"{', '.join(sections)} cannot be checked"
            )
        try:
            self.schema.require_complete(*sections)
        except tracker_schema.SectionError as error:
            raise SchemaIncomplete(f"{self.source}: {error}") from None


def fetch(repository: str) -> RepoSchema:
    """Fetch and parse `repository`'s `TRACKER.md`, printing nothing.

    Never raises: a missing file, a block the reader cannot read, and a
    failed fetch each give a RepoSchema with no schema and a `failure`."""
    owner, name = repository.split("/", 1)
    try:
        data = gh.graphql(_QUERY, {"owner": owner, "name": name, "path": PATH})
    except gh.GhError as error:
        return RepoSchema(
            repository, None, None,
            tracker_schema.TrackerSchemaError(
                f"could not be fetched ({_first_line(error)})"),
            error.exit_code)
    ref = ((data.get("repository") or {}).get("defaultBranchRef")) or None
    if ref is None:
        return _without(repository, None, "not found: the repo has no default branch")
    branch = ref.get("name")
    entry = ((ref.get("target") or {}).get("file")) or None
    if entry is None:
        return _without(repository, branch, "not found on the default branch")
    blob = entry.get("object") or {}
    if "text" not in blob:
        return _without(repository, branch, "not a file, so it cannot be read")
    if blob.get("isBinary") or blob.get("text") is None:
        return _without(repository, branch, "not text, so it cannot be read")
    if blob.get("isTruncated"):
        return _without(repository, branch,
                        "too large for GitHub to return whole, so it cannot be read")
    try:
        schema = tracker_schema.parse(blob["text"])
    except tracker_schema.TrackerSchemaError as error:
        return RepoSchema(repository, branch, None, error)
    return RepoSchema(repository, branch, schema)


def load(repository: str, stream: Optional[TextIO] = None) -> RepoSchema:
    """`fetch`, then print every warning line on `stream` (stderr by
    default), whether or not the caller needs the part at fault. It prints
    on every call, so a Verb loads once."""
    result = fetch(repository)
    stream = stream if stream is not None else sys.stderr
    for line in result.warning_lines():
        print(line, file=stream)
    return result


def _without(repository: str, branch: Optional[str], detail: str) -> RepoSchema:
    return RepoSchema(repository, branch, None,
                      tracker_schema.TrackerSchemaError(detail))


def _first_line(error: Exception) -> str:
    lines = str(error).strip().splitlines()
    return lines[0] if lines else type(error).__name__
