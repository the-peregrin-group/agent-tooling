"""A Tracker Schema fixture for the ghw tests: a small, complete JSON block,
and helpers that turn it, or a damaged copy of it, into what a Verb gets
from lib.github.repo_schema.

Its kinds, priorities, and labels are deliberately not the shipped
default's, so a test that passes against it cannot be leaning on a value
ghw used to hold as a constant.
"""

from __future__ import annotations

import copy
import json

from lib import tracker_schema
from lib.github import repo_schema

DOCUMENT = {
    "provenance": {"source_repo": None, "source_commit": None,
                   "default_path": None},
    "issue_kinds": [
        {"name": "task", "meaning": "Work that fits no other kind",
         "color": "c5def5"},
        {"name": "bug", "meaning": "Something is broken", "color": "d73a4a"},
        {"name": "chore", "meaning": "Maintenance", "color": "fbca04"},
    ],
    "issue_priorities": [
        {"name": "P0", "meaning": "Drop everything", "stale_after_days": 1,
         "color": "b60205"},
        {"name": "P1", "meaning": "Important", "stale_after_days": 7,
         "color": "d93f0b"},
        {"name": "P4", "meaning": "Not planned", "stale_after_days": 56,
         "color": "cfd3d7"},
    ],
    "issue_label_schema": {
        "axes": [
            {"name": "area", "prefix": "area:",
             "meaning": "The part of the project an Issue concerns",
             "every_issue_carries_at_least_one": True,
             "labels": [
                 {"name": "area:core", "meaning": "Core engine",
                  "color": "bfdadc"},
                 {"name": "area:docs", "meaning": "Documentation",
                  "color": "bfdadc"},
             ]},
            {"name": "site", "prefix": "site:",
             "meaning": "The deployment an Issue concerns",
             "every_issue_carries_at_least_one": False,
             "labels": [
                 {"name": "site:a", "meaning": "The Site A deployment",
                  "color": "c5def5"},
             ]},
        ],
        "labels": [
            {"name": "human", "meaning": "Waiting on a person",
             "color": "d876e3"},
            {"name": "perf", "meaning": "Performance", "color": "0e8a16"},
        ],
    },
    "issue_states": [
        {"name": "Needs Triage", "open": True, "entry": True,
         "color": "d73a4a"},
        {"name": "In progress", "open": True, "color": "7057ff"},
        {"name": "Closed", "open": False, "color": "6a737d"},
    ],
    "close_reasons": [
        {"name": "done", "meaning": "Finished"},
    ],
}


def document() -> dict:
    """A fresh deep copy of DOCUMENT, to damage freely."""
    return copy.deepcopy(DOCUMENT)


def text(doc: dict | None = None) -> str:
    """A TRACKER.md holding `doc` (DOCUMENT by default) as its JSON block."""
    block = json.dumps(DOCUMENT if doc is None else doc, indent=2)
    return (
        "# Tracker Schema\n\n"
        f"{tracker_schema.BEGIN_MARKER}\n```json\n{block}\n```\n"
        f"{tracker_schema.END_MARKER}\n"
    )


def loaded(doc: dict | None = None, repository: str = "o/r",
           branch: str = "main") -> repo_schema.RepoSchema:
    """What repo_schema.fetch gives for a repo whose TRACKER.md holds `doc`."""
    return repo_schema.RepoSchema(
        repository, branch, tracker_schema.parse(text(doc))
    )


def missing(repository: str = "o/r",
            branch: str = "main") -> repo_schema.RepoSchema:
    """What repo_schema.fetch gives for a repo with no TRACKER.md."""
    return repo_schema.RepoSchema(
        repository, branch, None,
        tracker_schema.TrackerSchemaError("not found on the default branch"),
    )


def graphql_response(file_text: str | None, branch: str = "main") -> dict:
    """The `data` gh.graphql returns for repo_schema's query: the file's
    text, or no file when `file_text` is None."""
    entry = None if file_text is None else {
        "object": {"text": file_text, "isBinary": False, "isTruncated": False}
    }
    return {"repository": {"defaultBranchRef": {
        "name": branch, "target": {"file": entry},
    }}}
