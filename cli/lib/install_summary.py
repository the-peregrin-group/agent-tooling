"""The concise, plain-text form of a tooling-install report.

`summarize` turns the report `diff` returns, or the "applied" plan that
`apply` and `adopt` emit, into a few lines for a human or an agent to read.
`tooling-install --json` prints the full report instead; this module only
presents it and never changes what it holds.

The one rule: the summary never hides what an install would destroy or
overwrite. Every report key is classified here explicitly:

- Inventory keys (`INVENTORY`) list what a run leaves alone or merely ships,
  and are shown as counts only.
- Every other non-empty list is printed with its item names. Keys in `LISTED`
  get a readable label, and the destructive ones are labelled in capitals so
  they stand out; a key this module does not know is printed under its own
  name, so a key added to the report later is visible by default.
- Known scalars are folded into the header and cohort lines or, for
  `kind` and `target` (fixed per cohort), left to `--json`. An unknown scalar
  is printed as `key: value`.
"""

from __future__ import annotations

import json
import re

# Lists of what a run leaves alone or ships as a matter of course: counts only.
INVENTORY = {
    "unowned_preserved": "unowned files",
    "foreign_files": "foreign files",
    "foreign_units": "foreign units",
    "preserved": "other files",
    "units": None,  # apply's shipped units: folded into the "installed" line
}

# Lists printed by name. The label for a dry run (`diff`), then for a run
# that happened (`apply`, `adopt`); capitals mark loss or overwriting.
LISTED = {
    "only_in_source": ("only in source", "only in source"),
    "changed": ("changed", "changed"),
    "adoptable": ("adoptable", "adoptable"),
    "adopted": ("adopted", "adopted"),
    "receipt_mismatch": (
        "RECEIPT MISMATCH (installed copy edited or missing; apply overwrites)",
        "RECEIPT MISMATCH",
    ),
    "only_installed": ("WOULD REMOVE (no longer shipped)", "REMOVED"),
    "retired": ("WOULD REMOVE (no longer shipped)", "REMOVED (no longer shipped)"),
    "unowned_replaced": ("WOULD DELETE unowned", "DELETED unowned"),
    "foreign_replaced": ("WOULD DELETE foreign", "DELETED foreign"),
    "conflicting": (
        "CONFLICTING (apply refuses; adopt takes over)",
        "CONFLICTING",
    ),
}

# Scalars the cohort line already carries, or that --json alone shows.
COHORT_SCALARS = {"kind", "target", "status", "ships", "installed_commit", "installed"}

# Top-level keys the header and the recovery lines already carry.
TOP_KEYS = {
    "action",
    "source",
    "source_repo",
    "source_commit",
    "selected_cohorts",
    "cohorts",
    "status",
    "supersedes",
    "recovery_pending",
    "recovered",
}

_SHA = re.compile(r"^[0-9a-f]{40}")


def short_commit(commit) -> str:
    """A full hash shortened to seven characters, keeping any `-dirty` suffix."""
    if not isinstance(commit, str):
        return str(commit)
    if _SHA.match(commit):
        return commit[:7] + commit[40:]
    return commit


def _value(value) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _names(items) -> str:
    if not isinstance(items, list):
        return _value(items)
    return ", ".join(_value(item) for item in items)


def summarize(report: dict) -> str:
    """The plain-text summary of a diff report or an applied plan."""
    applied = report.get("action") is not None
    lines = []

    header = f"{report.get('source_repo')} @ {short_commit(report.get('source_commit'))}"
    if applied:
        header = f"{report['action']} {header}"
        if report.get("supersedes") is not None:
            header += f", superseding {report['supersedes']}"
    elif "status" in report:
        header += f": {report['status']}"
    lines.append(header)

    if report.get("recovery_pending"):
        lines.append(
            "  RECOVERY PENDING (interrupted swap; apply restores or refuses): "
            + _names(report["recovery_pending"])
        )
    if report.get("recovered"):
        lines.append("  RECOVERED interrupted swap: " + _names(report["recovered"]))
    for key in sorted(set(report) - TOP_KEYS):
        lines.append(f"  {key}: {_value(report[key])}")

    elided = False
    cohorts = report.get("cohorts") or {}
    width = max((len(name) for name in cohorts), default=0)
    for name, cohort in cohorts.items():
        cohort_lines, counted = _cohort(
            cohort, applied, report.get("source_commit")
        )
        elided = elided or counted
        lines.append(f"{name.ljust(width)}  {cohort_lines[0]}")
        lines.extend(f"  {line}" for line in cohort_lines[1:])

    if elided:
        lines.append("(counts only for what is left alone; --json lists it)")
    return "\n".join(lines)


def _cohort(cohort: dict, applied: bool, source_commit):
    """(lines, counted): the cohort's own line, then one line per detail."""
    if applied:
        first = f"installed {cohort.get('installed')} files"
        units = cohort.get("units")
        if isinstance(units, list):
            first += f" in {len(units)} units"
    else:
        first = f"{cohort.get('status')} ({cohort.get('ships')} shipped"
        installed_commit = cohort.get("installed_commit")
        if installed_commit is not None and installed_commit != source_commit:
            first += f"; installed @ {short_commit(installed_commit)}"
        first += ")"

    counts = [
        f"{len(cohort[key])} {label}"
        for key, label in INVENTORY.items()
        if label is not None and isinstance(cohort.get(key), list) and cohort[key]
    ]
    if counts:
        first += "; " + ", ".join(counts) + " left alone"

    details = []
    for key, labels in LISTED.items():
        if cohort.get(key):
            details.append(f"{labels[1] if applied else labels[0]}: {_names(cohort[key])}")
    for key in sorted(set(cohort) - set(LISTED) - set(INVENTORY) - COHORT_SCALARS):
        value = cohort[key]
        if isinstance(value, list):
            if value:
                details.append(f"{key}: {_names(value)}")
        else:
            details.append(f"{key}: {_value(value)}")
    return [first] + details, bool(counts)
