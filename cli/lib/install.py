"""tooling-install's engine: cohort resolution, drift computation, swaps.

Consumer-generic by construction: everything repo-specific arrives from the
source checkout's `install.json`, so one installed copy of `tooling-install`
serves every source repo that ships agent tooling (this repo, or any other
checkout with its own manifest). This module knows about *kinds* of target,
never about a particular repo's contents.

install.json
------------
At the source checkout's root, version 1:

    {
      "version": 1,
      "source_repo": "<label>",
      "exclude": [<pattern>, ...],          # applies to every cohort
      "cohorts": {
        "<name>": {
          "kind": "bin" | "skills" | "agents",
          "sources": ["<dir>", ...],        # repo-relative
          "exclude": [<pattern>, ...]       # cohort-specific, optional
        }
      }
    }

Each cohort's `kind` must be unique within the file: a kind owns one target
directory, and two cohorts competing for the same target would make ownership
(below) ambiguous. A pattern excludes a file when it fnmatch-matches the
file's source-relative posix path, or any single component of it, or names a
directory prefix of it -- so `*_test.py` drops tests by basename,
`__pycache__` drops a whole directory anywhere, and `some-skill/NOTES.md`
drops one named file.

The two exclude lists differ in reach. The top-level `exclude` is the *noise*
list -- bytecode, OS droppings, VCS metadata -- things that are never content
on either side, so it is applied to the *target* scan too: a `__pycache__`
regenerated inside an installed skill is not a hand-drop and must never be
counted as unowned. A cohort's own `exclude` says "this repo deliberately does
not ship that file"; the same name appearing in a target genuinely is unowned
content, so cohort excludes narrow the source scan only.

Cohort selection
----------------
`diff` and `apply` take an optional subset of cohort names (`--cohort`,
repeatable); an unknown name is a usage error. A selected run touches only the
named cohorts' targets, and judges source dirtiness only over their source
directories -- the unselected trees do not ship in this run, so their state
cannot invalidate its receipt. The source/target overlap refusal (below) is
always evaluated over every declared cohort, selected or not: it is a
statement about the checkout, not about one shipment.

Target kinds
------------
    bin     -> ~/.local/libexec/agent-tooling/
    skills  -> ~/.claude/skills/
    agents  -> ~/.claude/agents/

`bin` and `agents` are *merge* targets: every cohort source directory's
contents land in one target root, each source directory's internal layout
preserved (cli/lib/plan.py -> <target>/lib/plan.py). "Flat" means the source
directories collapse into a single root, not that subdirectories are
flattened -- the wrapper CLIs do `sys.path.insert(0, <own dir>)` and import
`lib.*`, so the package layout is load-bearing. Two source files claiming the
same target-relative path are refused, never silently shadowed.

`skills` is a *unit* target: each immediate subdirectory of the cohort's
source directory is one skill, installed and swapped independently, so
installing this repo's skills never disturbs another repo's. A unit is owned
wholesale: the swap replaces the whole directory, so anything inside an
installed skill that the incoming unit does not ship is gone after an install.
`diff` reports that loss in two buckets, by who claimed what was lost:
`unowned_replaced` for what no record claims (bytecode caches, hand-drops) and
`foreign_replaced` for what another source's record claims.

Ownership and the receipt
-------------------------
Each target directory carries `install-receipt.json`, keyed by source repo:

    {"version": 1, "sources": {"<source_repo>": {
        "kind": ..., "source_path": ..., "source_commit": ...,
        "installed_at": ..., "files": {"<relpath>": "sha256:..."},
        "units": [...]                      # skills kind only
    }}}

Keying by source repo is what lets two repos ship into one target: an install
from `repo-a` rewrites only the `repo-a` key, and every path listed under the
other keys is *foreign* -- outside this run's diff, carried through its swap
untouched. Files present in a target that no record claims are *unowned*
(pre-existing content, or a hand-drop): reported, preserved, never claimed.
Removing a file from the source removes it from the target only because the
previous receipt proves this source repo put it there.

Ownership transfer
------------------
A source that ships a path -- or, on a unit target, a unit -- another
source's record already claims is a *collision*. When the incoming copy is
byte-identical to what is installed the collision is *adoptable*: the entry
moves into this source's record and is dropped from the other's, the bytes on
disk never changing. That is how a cohort migrates between source repos. The
new owner ships the same content and adopts it; the old owner stops shipping
it on its next run, by which point its record no longer claims it, so that
run neither retires it nor re-claims it.

Byte-identity is measured against the *installed* copy, not against the other
record's stored digest: the question adoption answers is "would taking this
over destroy anything?", and only the target can answer it. A unit adopts
only when its installed file set and the incoming file set are equal and every
pair of digests matches -- a unit swap is wholesale, so an installed file the
incoming source does not ship (including one its own cohort `exclude` drops)
would be destroyed by the adoption. Migrating a unit therefore requires the
two manifests' exclude lists to agree on it.

A collision that is not adoptable is *conflicting*, and refuses the run. A
name the other record claims but that is absent from the target is
conflicting too: with nothing installed there is no evidence the two sources
agree, and a stale claim is a human's to resolve.

An other-source record that adoption empties -- no files left, and no units
on a unit target -- is dropped from the receipt outright. A record claiming
nothing is a stale stamp, not ownership, and keeping it would have the next
run report a foreign source with no foreign content.

Superseding a source repo: `adopt`
----------------------------------
Byte-identity cannot carry a migration on its own. A repo that rewrites
content as it takes a cohort over -- editing prose, renaming
references -- ships nothing identical to adopt, and the refusal it
meets is correct but useless. `adopt` is the declared act that gets past it:

    tooling-install adopt <source-checkout> <superseded-source-repo>

It installs exactly as `apply` does, with one difference: a collision with
the *named* record transfers regardless of content. The incoming copy wins,
as it would in any ordinary install of a file this source already owned, and
nothing is destroyed that the superseded checkout cannot reproduce. A
collision with any other record still refuses, so the widening is scoped to
one named repo. The name must match a record in a selected target's receipt;
an unknown one is a usage error, never a silently narrower run.

The reason this is a subcommand and not a flag on `apply`: permission rules
match literal command prefixes, so a trailing option cannot be excluded from
`Bash(tooling-install apply *)`. Separate verbs let `apply` -- which never
overwrites another repo's content -- be granted broadly while `adopt` sits
behind its own rule, and put the superseded repo in the command line the
human reads before approving it.

On a unit target `adopt` swaps the unit wholesale like any install, so
content inside a superseded unit that the incoming unit does not ship does not
survive -- whether no record claims it (`unowned_replaced`) or the superseded
record itself does (`foreign_replaced`). That second case is the one to watch
when the two manifests' exclude lists diverge: the outgoing owner shipped a
file the incoming owner drops, and adopting the unit deletes it.

`adopt` has no preview of its own, so **`diff` is its dry run**. Three lists
say what a transfer would do: `conflicting` is what it would take over
(minus any entry belonging to a repo other than the one it names, which it
would refuse over instead), and `unowned_replaced` and `foreign_replaced` are
what it would destroy.

A symlink in a target is unowned by construction -- no source ever ships one,
since `collect_sources` skips them -- so it is scanned, reported, and on a
merge target carried through the swap as a symlink (the link is copied, never
the referent). On a unit target it falls inside the wholesale replacement like
any other unowned file, and says so via `unowned_replaced`.

Content a swap would destroy is drift, not a footnote: `diff` exits 1 for
`unowned_replaced` and for `foreign_replaced`, because the only honest answer
to "would installing lose something?" is yes.

Refusals
--------
- A source that equals, contains, or is contained by any target. Installing
  into your own checkout would make the swap rename the source out from under
  the run, so a target must never sit inside the source checkout, nor the
  source inside a target.
- A dirty source, unless forced -- a forced install stamps the commit
  `<hash>-dirty`, never launders it.
- Two source files colliding on one target path, or a conflicting collision
  with a foreign file or unit already in the target. A byte-identical
  collision is adopted instead, as is any collision with the record `adopt`
  names (see Ownership transfer and `adopt`, above).

The swap
--------
Per target directory (or per skill unit): stage into a temporary sibling
`<name>.new-<pid>`, rename the live copy to `<name>.retired-<pid>`, rename
staging into place, delete the retired copy. Two renames are not atomic, so a
crash between them leaves the target missing and a retired copy beside it;
`recover()` restores it before any other work. `apply` performs recovery;
`diff` only reports it, because `diff` must stay read-only enough to
allowlist.

Two `apply` runs from different source repos into one merge target, overlapping
in time, are last-writer-wins: each stages from the receipt it read at its
start, so the later swap carries a snapshot taken before the earlier one
landed. Nothing here guards against that, deliberately -- `apply` is a human
act behind a permission prompt, not a daemon, and a lock would buy safety
against a situation that requires two humans installing at once.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

CONFIG_NAME = "install.json"
CONFIG_VERSION = 1
RECEIPT_NAME = "install-receipt.json"
RECEIPT_VERSION = 1

KINDS = ("bin", "skills", "agents")
UNIT_KINDS = ("skills",)

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_USAGE = 2
EXIT_REFUSED = 4


class InstallError(Exception):
    """A refusal or an unusable environment, carrying its own exit code."""

    def __init__(self, message: str, exit_code: int = EXIT_USAGE):
        super().__init__(message)
        self.exit_code = exit_code


# --------------------------------------------------------------------------
# Configuration


class Cohort:
    """One declared shipment: source directories -> one target kind.

    `excludes` narrows the source scan (the manifest's shared noise list plus
    this cohort's own list); `noise` is the shared list alone, and is what the
    target scan applies -- see the module docstring on the two lists' reach.
    """

    def __init__(self, name: str, kind: str, sources, excludes, noise=()):
        self.name = name
        self.kind = kind
        self.sources = tuple(sources)
        self.excludes = tuple(excludes)
        self.noise = tuple(noise)

    @property
    def is_unit_kind(self) -> bool:
        return self.kind in UNIT_KINDS


class Config:
    def __init__(self, source_repo: str, cohorts):
        self.source_repo = source_repo
        self.cohorts = tuple(cohorts)


def load_config(source: Path) -> Config:
    """Parse and validate `<source>/install.json`."""
    path = source / CONFIG_NAME
    if not path.is_file():
        raise InstallError(f"{source} has no {CONFIG_NAME}: not an installable source")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise InstallError(f"{path} is unreadable or not valid JSON: {error}")
    if not isinstance(raw, dict):
        raise InstallError(f"{path} must contain a JSON object")
    if raw.get("version") != CONFIG_VERSION:
        raise InstallError(
            f"{path} has version {raw.get('version')!r}; "
            f"this tooling-install understands version {CONFIG_VERSION}"
        )
    source_repo = raw.get("source_repo")
    if not isinstance(source_repo, str) or not source_repo:
        raise InstallError(f"{path} must set a non-empty string 'source_repo'")
    shared = _string_list(raw.get("exclude", []), f"{path}: 'exclude'")
    declared = raw.get("cohorts")
    if not isinstance(declared, dict) or not declared:
        raise InstallError(f"{path} must set a non-empty 'cohorts' object")

    cohorts = []
    seen_kinds = {}
    for name in sorted(declared):
        body = declared[name]
        where = f"{path}: cohort {name!r}"
        if not isinstance(body, dict):
            raise InstallError(f"{where} must be an object")
        kind = body.get("kind")
        if kind not in KINDS:
            raise InstallError(
                f"{where} has kind {kind!r}; expected one of {', '.join(KINDS)}"
            )
        if kind in seen_kinds:
            raise InstallError(
                f"{where} and cohort {seen_kinds[kind]!r} both declare kind "
                f"{kind!r}; one kind is one target directory, so it takes "
                "exactly one cohort"
            )
        seen_kinds[kind] = name
        sources = _string_list(body.get("sources"), f"{where}: 'sources'")
        if not sources:
            raise InstallError(f"{where} must list at least one source directory")
        for entry in sources:
            if Path(entry).is_absolute() or ".." in Path(entry).parts:
                raise InstallError(
                    f"{where}: source {entry!r} must be a relative path inside "
                    "the checkout"
                )
        excludes = _string_list(body.get("exclude", []), f"{where}: 'exclude'")
        cohorts.append(
            Cohort(
                name,
                kind,
                sources,
                tuple(shared) + tuple(excludes),
                noise=tuple(shared),
            )
        )
    return Config(source_repo, cohorts)


def _string_list(value, where: str):
    if value is None:
        raise InstallError(f"{where} is required")
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise InstallError(f"{where} must be a list of strings")
    return list(value)


def select_cohorts(config: Config, names=None):
    """The cohorts a run acts on: every declared one, or the named subset.

    An unknown name is a usage error rather than a silently empty run -- a
    typo in `--cohort` must never look like a successful install of nothing.
    """
    if not names:
        return config.cohorts
    declared = {cohort.name: cohort for cohort in config.cohorts}
    unknown = sorted({name for name in names if name not in declared})
    if unknown:
        raise InstallError(
            f"unknown cohort(s) {', '.join(unknown)}; {config.source_repo} "
            f"declares {', '.join(sorted(declared))}"
        )
    return tuple(declared[name] for name in sorted(set(names)))


# --------------------------------------------------------------------------
# Targets and source-file collection


def target_for(kind: str, home=None) -> Path:
    """The install directory for a target kind, under `home` (default ~)."""
    root = Path(home) if home is not None else Path.home()
    if kind == "bin":
        return root / ".local" / "libexec" / "agent-tooling"
    if kind == "skills":
        return root / ".claude" / "skills"
    if kind == "agents":
        return root / ".claude" / "agents"
    raise InstallError(f"unknown target kind {kind!r}")


def excluded(relpath: str, patterns) -> bool:
    """Whether a source-relative posix path is excluded by any pattern.

    A pattern matches the whole relative path, any single path component, or
    (when it is a literal, glob-free path) a directory prefix of it.
    """
    parts = relpath.split("/")
    for pattern in patterns:
        if fnmatch.fnmatch(relpath, pattern):
            return True
        for part in parts:
            if fnmatch.fnmatch(part, pattern):
                return True
        literal = pattern.rstrip("/")
        is_glob = any(character in literal for character in "*?[")
        if not is_glob and relpath.startswith(literal + "/"):
            return True
    return False


def collect_sources(source: Path, cohort: Cohort):
    """Map target-relative posix path -> source file, for one cohort.

    Refuses a missing source directory, a collision between two source
    directories, and (for unit kinds) a loose file where a unit directory
    belongs.
    """
    files = {}
    origin = {}
    for entry in cohort.sources:
        base = source / entry
        if not base.is_dir():
            raise InstallError(
                f"cohort {cohort.name!r} declares source {entry!r}, "
                f"which is not a directory in {source}"
            )
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(base).as_posix()
            if relative == RECEIPT_NAME or excluded(relative, cohort.excludes):
                continue
            if cohort.is_unit_kind and "/" not in relative:
                raise InstallError(
                    f"cohort {cohort.name!r} is a {cohort.kind} cohort, so "
                    f"{entry}/ must hold only unit directories; found the loose "
                    f"file {relative!r}"
                )
            if relative in files:
                raise InstallError(
                    f"cohort {cohort.name!r}: {origin[relative]} and {entry} both "
                    f"ship {relative!r} to the same target path",
                    EXIT_REFUSED,
                )
            files[relative] = path
            origin[relative] = entry
    return files


def unit_of(relpath: str) -> str:
    return relpath.split("/", 1)[0]


def digest(path: Path) -> str:
    """A content identity for a target entry; symlinks digest as their link.

    A symlink and a regular file therefore never compare equal, which is the
    answer we want: a link standing where a shipped file belongs is drift.
    """
    if path.is_symlink():
        return "symlink:" + os.readlink(str(path))
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def present_files(target: Path, noise=()):
    """Map target-relative posix path -> entry, for everything in a target.

    Symlinks count as entries (never descended into, so a symlinked directory
    is one entry, not a subtree). `noise` is the manifest's shared exclude
    list: regenerated bytecode and OS droppings are not target content, and
    counting them as unowned would make every installed tree look dirty.
    """
    found = {}
    if not target.is_dir():
        return found
    for path in sorted(target.rglob("*")):
        if not path.is_symlink() and not path.is_file():
            continue
        relative = path.relative_to(target).as_posix()
        if relative == RECEIPT_NAME or excluded(relative, noise):
            continue
        found[relative] = path
    return found


# --------------------------------------------------------------------------
# Receipts


def read_receipt(target: Path) -> dict:
    path = target / RECEIPT_NAME
    if not path.is_file():
        return {"version": RECEIPT_VERSION, "sources": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise InstallError(f"{path} is unreadable or not valid JSON: {error}")
    if not isinstance(data, dict) or not isinstance(data.get("sources"), dict):
        raise InstallError(f"{path} is not a version {RECEIPT_VERSION} receipt")
    return data


def owned_by(receipt: dict, source_repo: str):
    """The set of target-relative paths this source repo installed last time."""
    record = receipt.get("sources", {}).get(source_repo)
    if not isinstance(record, dict):
        return set()
    files = record.get("files")
    return set(files) if isinstance(files, dict) else set()


def owned_by_others(receipt: dict, source_repo: str):
    """Target-relative path -> the other source repo that claims it."""
    claims = {}
    for name, record in receipt.get("sources", {}).items():
        if name == source_repo or not isinstance(record, dict):
            continue
        for relative in record.get("files", {}):
            claims[relative] = name
    return claims


def units_of_others(receipt: dict, source_repo: str):
    units = {}
    for name, record in receipt.get("sources", {}).items():
        if name == source_repo or not isinstance(record, dict):
            continue
        for unit in record.get("units", []):
            units[unit] = name
    return units


def classify_collisions(sources, foreign, installed, supersedes=None):
    """Split the foreign-claimed paths this source ships into (adoptable, conflicting).

    Adoptable means the installed copy is byte-identical to the incoming one,
    so taking ownership destroys nothing. A claimed path that is not installed
    at all is conflicting: nothing on disk can show the two sources agree.

    `supersedes` names the one record whose claims transfer regardless of
    content -- `adopt`'s widening. None (an `apply`) matches no record, since
    a source repo label is never empty.
    """
    adoptable, conflicting = [], []
    for name in sorted(sources):
        if name not in foreign:
            continue
        entry = installed.get(name)
        if foreign[name] == supersedes or (
            entry is not None and digest(entry) == digest(sources[name])
        ):
            adoptable.append(name)
        else:
            conflicting.append(name)
    return adoptable, conflicting


def classify_unit_collisions(sources, foreign_units, installed, supersedes=None):
    """Split the foreign-claimed units this source ships into (adoptable, conflicting).

    A unit swap is wholesale, so a unit adopts only when its installed file set
    and its incoming file set are equal and every pair of digests matches --
    any other installed file inside it would be destroyed by the adoption.
    `supersedes` lifts that for the one named record, as it does for files.
    """
    adoptable, conflicting = [], []
    for unit in sorted({unit_of(name) for name in sources}):
        if unit not in foreign_units:
            continue
        shipped = {
            name: path for name, path in sources.items() if unit_of(name) == unit
        }
        present = {
            name: path for name, path in installed.items() if unit_of(name) == unit
        }
        identical = set(shipped) == set(present) and all(
            digest(present[name]) == digest(path) for name, path in shipped.items()
        )
        transfers = foreign_units[unit] == supersedes or identical
        (adoptable if transfers else conflicting).append(unit)
    return adoptable, conflicting


def _other_repos(supersedes):
    """How a refusal names the ownership this run is not entitled to take."""
    if supersedes is None:
        return "another source repo"
    return f"a source repo other than {supersedes!r}"


# --------------------------------------------------------------------------
# Source state


def source_state(source: Path, cohorts) -> dict:
    """The source checkout's commit and dirtiness, scoped to what ships.

    Dirtiness is judged over the selected cohorts' source directories plus
    install.json: the receipt pins those trees, and nothing else in the
    checkout ships in this run. A source that is not a git checkout counts as
    dirty with commit "unknown" -- it can still be forced, and will be stamped
    as such.
    """
    pathspecs = sorted({entry for cohort in cohorts for entry in cohort.sources})
    pathspecs.append(CONFIG_NAME)
    inside = _git(source, "rev-parse", "--is-inside-work-tree")
    if inside is None:
        return {"commit": "unknown", "dirty": "(not a git checkout)"}
    commit = _git(source, "rev-parse", "HEAD")
    if commit is None:
        return {"commit": "unknown", "dirty": "(no commits yet)"}
    dirty = _git(source, "status", "--porcelain", "--", *pathspecs)
    return {"commit": commit, "dirty": dirty or ""}


def _git(cwd: Path, *arguments):
    """Run a read-only git command; None when git refuses or is absent."""
    try:
        process = subprocess.run(
            ["git", "-C", str(cwd), *arguments],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
        )
    except OSError:
        return None
    if process.returncode != 0:
        return None
    return process.stdout.strip()


def stamp_commit(state: dict) -> str:
    return state["commit"] + ("-dirty" if state["dirty"] else "")


# --------------------------------------------------------------------------
# Overlap refusal


def check_overlap(source: Path, config: Config, home=None) -> None:
    """Refuse a source that equals, contains, or sits inside any target."""
    source = source.resolve()
    for cohort in config.cohorts:
        target = target_for(cohort.kind, home)
        resolved = _resolve_existing(target)
        if source == resolved:
            raise InstallError(
                f"refusing to install from {source}: it is the {cohort.kind} "
                "target itself",
                EXIT_REFUSED,
            )
        if resolved.is_relative_to(source):
            raise InstallError(
                f"refusing to install from {source}: the {cohort.kind} target "
                f"{resolved} sits inside it, so the swap would rename part of "
                "the source out from under this run. Install from a separate "
                "checkout (a worktree).",
                EXIT_REFUSED,
            )
        if source.is_relative_to(resolved):
            raise InstallError(
                f"refusing to install from {source}: it sits inside the "
                f"{cohort.kind} target {resolved}, which the swap replaces "
                "wholesale.",
                EXIT_REFUSED,
            )


def _resolve_existing(path: Path) -> Path:
    """Resolve as much of a path as exists; absolutize the rest."""
    resolved = Path(os.path.abspath(str(path)))
    existing = resolved
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    return existing.resolve() / resolved.relative_to(
        Path(os.path.abspath(str(existing)))
    )


# --------------------------------------------------------------------------
# Crash recovery


def pending_recoveries(parent: Path, names):
    """Retired copies of `names` in `parent` that a crashed swap left behind.

    Returns (restorable, orphaned): names whose live copy is missing and can
    be restored, and retired copies whose live copy is present (the swap
    completed; the retired copy is just garbage).
    """
    restorable, orphaned = [], []
    if not parent.is_dir():
        return restorable, orphaned
    for path in sorted(parent.iterdir()):
        marker = path.name.find(".retired-")
        if marker < 0:
            continue
        base = path.name[:marker]
        if base not in names:
            continue
        if (parent / base).exists():
            orphaned.append(path)
        else:
            restorable.append(path)
    return restorable, orphaned


def recover(parent: Path, names):
    """Undo a crashed swap before doing anything else. Returns a report list."""
    restorable, orphaned = pending_recoveries(parent, names)
    actions = []
    by_base = {}
    for path in restorable:
        by_base.setdefault(path.name[: path.name.find(".retired-")], []).append(path)
    for base, copies in sorted(by_base.items()):
        if len(copies) > 1:
            raise InstallError(
                f"{parent / base} is missing and {len(copies)} retired copies "
                f"exist ({', '.join(copy.name for copy in copies)}); a human "
                "must pick the right one before installing",
                EXIT_REFUSED,
            )
        copies[0].rename(parent / base)
        actions.append({"restored": str(parent / base), "from": copies[0].name})
    for path in orphaned:
        shutil.rmtree(path, ignore_errors=True)
        actions.append({"discarded": path.name})
    if parent.is_dir():
        for base in sorted(names):
            for path in sorted(parent.glob(base + ".new-*")):
                shutil.rmtree(path, ignore_errors=True)
                actions.append({"discarded": path.name})
    return actions


# --------------------------------------------------------------------------
# Diff


def diff(source: Path, home=None, cohorts=None) -> dict:
    """Compute, without touching anything, what `apply` would do.

    `cohorts` restricts the run to the named cohorts; None means all of them.

    Collisions with another source's record are classified per cohort into
    `adoptable` and `conflicting` -- target-relative paths on a merge target,
    unit names on a unit target. `foreign_files` and `foreign_units` then carry
    their narrowed meaning: claimed by another source and *not* shipped by this
    one. Either new category being non-empty makes the cohort drift, so the
    exit-code contract is unchanged and now honest: 0 means `apply` would do
    nothing, 1 means it would act (including rewriting ownership) or refuse.

    Unit cohorts also report `foreign_replaced`: files another record claims
    that sit inside a unit this source ships *without* them, so the wholesale
    unit swap would delete them. `unowned_replaced` is the same statement for
    files no record claims. The four foreign categories partition -- a foreign
    name appears in exactly one of `adoptable`, `conflicting`,
    `foreign_replaced`, or `foreign_files` -- so `foreign_files` means foreign
    and untouched by this run.

    This is also `adopt`'s dry run, since `adopt` has no preview of its own:
    `conflicting` is what it would take over, and the two `*_replaced` lists
    are what it would destroy.
    """
    source = source.resolve()
    config = load_config(source)
    selected = select_cohorts(config, cohorts)
    check_overlap(source, config, home)
    state = source_state(source, selected)

    report = {
        "source": str(source),
        "source_repo": config.source_repo,
        "source_commit": stamp_commit(state),
        "selected_cohorts": [cohort.name for cohort in selected],
        "cohorts": {},
        "recovery_pending": [],
    }
    drift = False
    for cohort in selected:
        target = target_for(cohort.kind, home)
        sources = collect_sources(source, cohort)
        receipt = read_receipt(target)
        record = receipt.get("sources", {}).get(config.source_repo) or {}
        owned = owned_by(receipt, config.source_repo)
        foreign = owned_by_others(receipt, config.source_repo)
        installed = present_files(target, cohort.noise)

        only_in_source = sorted(name for name in sources if name not in installed)
        changed = sorted(
            name
            for name, path in sources.items()
            if name in installed and digest(path) != digest(installed[name])
        )
        only_installed = sorted(
            name for name in owned if name not in sources and name in installed
        )
        unowned = sorted(
            name
            for name in installed
            if name not in sources and name not in owned and name not in foreign
        )

        extra = {}
        foreign_replaced = []
        if cohort.is_unit_kind:
            # A unit swap replaces a whole skill directory, so anything inside
            # a unit this source ships that it does not itself ship goes with
            # it; content elsewhere in the target is never touched. Which
            # bucket a casualty lands in is a question of who claimed it.
            incoming_units = {unit_of(name) for name in sources}
            replaced = [name for name in unowned if unit_of(name) in incoming_units]
            unowned = [name for name in unowned if unit_of(name) not in incoming_units]
            foreign_replaced = sorted(
                name
                for name in installed
                if name not in sources
                and name in foreign
                and unit_of(name) in incoming_units
            )
            names = sorted(incoming_units | {unit_of(name) for name in owned})
            restorable, orphaned = pending_recoveries(target, names)
            foreign_units = units_of_others(receipt, config.source_repo)
            adoptable, conflicting = classify_unit_collisions(
                sources, foreign_units, installed
            )
            extra["foreign_units"] = sorted(
                unit for unit in foreign_units if unit not in incoming_units
            )
            extra["foreign_replaced"] = foreign_replaced
        else:
            replaced = []
            restorable, orphaned = pending_recoveries(target.parent, {target.name})
            adoptable, conflicting = classify_collisions(sources, foreign, installed)
        report["recovery_pending"].extend(
            sorted(path.name for path in restorable + orphaned)
        )
        at_risk = set(foreign_replaced)

        if not target.is_dir():
            status = "not-installed"
        elif (
            only_in_source
            or changed
            or only_installed
            or replaced
            or foreign_replaced
            or adoptable
            or conflicting
        ):
            status = "drift"
        else:
            status = "in-sync"
        if status != "in-sync":
            drift = True
        report["cohorts"][cohort.name] = {
            "kind": cohort.kind,
            "target": str(target),
            "status": status,
            "installed_commit": record.get("source_commit"),
            "ships": len(sources),
            "only_in_source": only_in_source,
            "changed": changed,
            "only_installed": only_installed,
            "unowned_preserved": unowned,
            "unowned_replaced": replaced,
            "foreign_files": sorted(
                name
                for name in foreign
                if name not in sources and name not in at_risk
            ),
            "adoptable": adoptable,
            "conflicting": conflicting,
            **extra,
        }
    report["status"] = "drift" if drift else "in-sync"
    return report


# --------------------------------------------------------------------------
# Apply


def apply(
    source: Path, home=None, force: bool = False, cohorts=None, supersedes=None
) -> dict:
    """Install each selected cohort, one swap per target directory or unit.

    `cohorts` restricts the run to the named cohorts; None means all of them.

    Each cohort's outcome reports `adopted`: the entries taken over from
    another source's record (paths on a merge target, unit names on a unit
    target). It is disjoint from `retired`, which names what this source
    stopped shipping, and it overlaps `installed` by construction -- an
    adopted entry ships in this run like any other.

    `supersedes` is the `adopt` subcommand: the named record's claims transfer
    regardless of content, while collisions with any other record refuse as
    usual. It must name a record in a selected target's receipt. None is a
    plain `apply`, which adopts only byte-identical collisions.
    """
    source = source.resolve()
    config = load_config(source)
    selected = select_cohorts(config, cohorts)
    check_overlap(source, config, home)
    if supersedes is not None:
        _check_supersedes(config, selected, supersedes, home)
    state = source_state(source, selected)
    if state["dirty"] and not force:
        raise InstallError(
            f"{source} has uncommitted changes in what ships; commit them or "
            "pass --force (a forced install is stamped -dirty in the "
            "receipt):\n" + state["dirty"],
            EXIT_REFUSED,
        )
    commit = stamp_commit(state)
    installed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    result = {
        "source": str(source),
        "source_repo": config.source_repo,
        "source_commit": commit,
        "selected_cohorts": [cohort.name for cohort in selected],
        "cohorts": {},
        "recovered": [],
    }
    if supersedes is not None:
        result["supersedes"] = supersedes
    for cohort in selected:
        target = target_for(cohort.kind, home)
        sources = collect_sources(source, cohort)
        target.parent.mkdir(parents=True, exist_ok=True)
        if cohort.is_unit_kind:
            target.mkdir(parents=True, exist_ok=True)
        swap = _apply_units if cohort.is_unit_kind else _apply_merged
        outcome = swap(
            config,
            cohort,
            source,
            target,
            sources,
            commit,
            installed_at,
            supersedes=supersedes,
        )
        result["recovered"].extend(outcome.pop("recovered"))
        result["cohorts"][cohort.name] = outcome
    return result


def _check_supersedes(config: Config, selected, supersedes: str, home) -> None:
    """Refuse an `adopt` whose superseded repo names no record we could find.

    A typo would otherwise read as "nothing to take over" and install as a
    plain `apply` -- a quiet refusal at best, and at worst a run the human
    approved for a migration that did not happen.
    """
    if supersedes == config.source_repo:
        raise InstallError(
            f"{supersedes!r} is this source's own repo label; adopt names the "
            "other repo whose ownership it supersedes"
        )
    known = set()
    for cohort in selected:
        receipt = read_receipt(target_for(cohort.kind, home))
        known.update(receipt.get("sources", {}))
    known.discard(config.source_repo)
    if supersedes not in known:
        recorded = (
            f"they record {', '.join(sorted(known))}"
            if known
            else "they record no other source repo"
        )
        raise InstallError(
            f"no receipt in the selected target(s) records a source repo "
            f"{supersedes!r}; {recorded}"
        )


def _apply_merged(
    config, cohort, source, target, sources, commit, installed_at, supersedes=None
):
    """Whole-target swap for the merge kinds (bin, agents).

    A path another source's record claims is adopted when the installed copy
    is byte-identical to the incoming one, or when `supersedes` names that
    record; anything else refuses the run.
    """
    recovered = recover(target.parent, {target.name})
    receipt = read_receipt(target)
    foreign = owned_by_others(receipt, config.source_repo)
    owned = owned_by(receipt, config.source_repo)
    installed = present_files(target, cohort.noise)

    carried = {}
    for name, path in installed.items():
        if name in owned and name not in sources:
            continue  # this source shipped it and no longer does: retire it
        if name in sources:
            continue  # replaced by the incoming copy
        carried[name] = path
    adopted, conflicting = classify_collisions(
        sources, foreign, installed, supersedes
    )
    if conflicting:
        raise InstallError(
            f"cohort {cohort.name!r}: {len(conflicting)} file(s) already "
            f"installed by {_other_repos(supersedes)} would be overwritten "
            f"with different content ({', '.join(conflicting[:5])}); resolve "
            "the overlap in the source repos",
            EXIT_REFUSED,
        )

    staging = target.parent / f"{target.name}.new-{os.getpid()}"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    for name, path in sources.items():
        _place(staging / name, path)
    for name, path in carried.items():
        _place(staging / name, path)

    record = {
        "kind": cohort.kind,
        "source_path": str(source),
        "source_commit": commit,
        "installed_at": installed_at,
        "files": {name: digest(path) for name, path in sorted(sources.items())},
    }
    _write_receipt(staging, receipt, config, record, adopted=adopted)
    _two_rename_swap(target, staging)
    return {
        "kind": cohort.kind,
        "target": str(target),
        "installed": len(sources),
        "adopted": adopted,
        "retired": sorted(name for name in owned if name not in sources),
        "preserved": sorted(carried),
        "recovered": recovered,
    }


def _apply_units(
    config, cohort, source, target, sources, commit, installed_at, supersedes=None
):
    """Per-unit swap for the unit kinds (skills).

    A unit another source's record claims is adopted when its installed and
    incoming file sets are equal and every file matches byte for byte, or when
    `supersedes` names that record; any other clash refuses the run.
    """
    receipt = read_receipt(target)
    owned = owned_by(receipt, config.source_repo)
    foreign_units = units_of_others(receipt, config.source_repo)
    incoming = sorted({unit_of(name) for name in sources})
    previous = sorted({unit_of(name) for name in owned})
    recovered = recover(target, set(incoming) | set(previous))
    installed = present_files(target, cohort.noise)

    adopted, clash = classify_unit_collisions(
        sources, foreign_units, installed, supersedes
    )
    if clash:
        raise InstallError(
            f"cohort {cohort.name!r}: unit(s) {', '.join(clash)} are already "
            f"installed by {_other_repos(supersedes)} and differ from what "
            "this source ships; resolve the overlap in the source repos",
            EXIT_REFUSED,
        )

    for unit in incoming:
        staging = target / f"{unit}.new-{os.getpid()}"
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir(parents=True)
        for name, path in sources.items():
            if unit_of(name) == unit:
                _place(staging / name.split("/", 1)[1], path)
        _two_rename_swap(target / unit, staging)

    retired = [unit for unit in previous if unit not in incoming]
    for unit in retired:
        _retire(target / unit)

    record = {
        "kind": cohort.kind,
        "source_path": str(source),
        "source_commit": commit,
        "installed_at": installed_at,
        "units": incoming,
        "files": {name: digest(path) for name, path in sorted(sources.items())},
    }
    _write_receipt(target, receipt, config, record, adopted_units=adopted)
    return {
        "kind": cohort.kind,
        "target": str(target),
        "installed": len(sources),
        "units": incoming,
        "adopted": adopted,
        "retired": retired,
        "foreign_units": sorted(
            unit for unit in foreign_units if unit not in adopted
        ),
        "recovered": recovered,
    }


def _place(destination: Path, origin: Path) -> None:
    """Copy one entry into staging, links as links rather than as referents."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if origin.is_symlink():
        destination.symlink_to(os.readlink(str(origin)))
        return
    shutil.copy2(str(origin), str(destination))


def _write_receipt(
    directory: Path,
    receipt: dict,
    config: Config,
    record: dict,
    adopted=(),
    adopted_units=(),
):
    """Rewrite the receipt: this source's record, plus the others' minus adoptions.

    `adopted` names target-relative paths and `adopted_units` names units; a
    run passes one or the other, never both. Every other source's record gives
    the adopted content up, and a record left claiming nothing is dropped.
    """
    adopted = frozenset(adopted)
    adopted_units = frozenset(adopted_units)
    merged = {}
    for name, entry in receipt.get("sources", {}).items():
        if name == config.source_repo:
            continue
        if adopted or adopted_units:
            entry = _release(entry, adopted, adopted_units)
            if entry is None:
                continue
        merged[name] = entry
    merged[config.source_repo] = record
    ordered = {
        "version": RECEIPT_VERSION,
        "sources": {name: merged[name] for name in sorted(merged)},
    }
    (directory / RECEIPT_NAME).write_text(
        json.dumps(ordered, indent=2) + "\n", encoding="utf-8"
    )


def _release(entry, names, units):
    """One other source's record with the adopted content removed.

    Returns the entry unchanged when it claimed none of it, and None when the
    removal leaves it claiming nothing at all -- the caller then drops it.
    """
    if not isinstance(entry, dict):
        return entry
    result = dict(entry)
    dropped = False
    files = entry.get("files")
    if isinstance(files, dict):
        kept = {
            name: value
            for name, value in files.items()
            if name not in names and unit_of(name) not in units
        }
        dropped = dropped or len(kept) != len(files)
        result["files"] = kept
    declared = entry.get("units")
    if isinstance(declared, list):
        kept_units = [unit for unit in declared if unit not in units]
        dropped = dropped or len(kept_units) != len(declared)
        result["units"] = kept_units
    if not dropped:
        return entry
    if not result.get("files") and not result.get("units"):
        return None
    return result


def _two_rename_swap(target: Path, staging: Path) -> None:
    """Rename the live copy aside, rename staging in, delete the retired copy."""
    retired = target.parent / f"{target.name}.retired-{os.getpid()}"
    shutil.rmtree(retired, ignore_errors=True)
    if target.exists():
        target.rename(retired)
    try:
        staging.rename(target)
    except OSError:
        if retired.exists() and not target.exists():
            retired.rename(target)
        raise
    shutil.rmtree(retired, ignore_errors=True)


def _retire(target: Path) -> None:
    """Remove an installed unit through the same rename-then-delete path."""
    if not target.exists():
        return
    retired = target.parent / f"{target.name}.retired-{os.getpid()}"
    shutil.rmtree(retired, ignore_errors=True)
    target.rename(retired)
    shutil.rmtree(retired, ignore_errors=True)
