"""Working-copy verification and the read primitives gitw verbs share.

Trust-but-verify, the gitw novel invariant: a verb's leading label claims
"this working copy is the rostered repo", and this module checks the claim
before anything acts. Verification is two-layer: the checkout at cwd must
*be* the registered primary checkout (or one of its linked worktrees --
matched via the shared git common directory, so a rogue second clone is
refused even with the right URL), and the configured remote must match the
registered URL. cwd outside the repo is admitted only under the roster's
`operable_from` interlock, and then only for verbs that never touch a
working tree.

Everything here is read-only; RefusalError maps to exit 4 upstream.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lib import plan
from lib.git import arguments, run
from lib.git.roster import Entry


class RefusalError(Exception):
    """A trust-but-verify failure: the working copy does not match the
    roster's claim. Exit 4 upstream -- a caller bug, never retry."""


@dataclass(frozen=True)
class Workspace:
    """The verified working copy a verb operates on. `root` is the current
    worktree's top level when cwd is inside the labeled repo; otherwise
    (operable_from) it is the registered primary checkout, and `in_repo`
    is False -- working-tree-switching verbs must refuse that case."""

    entry: Entry
    root: Path
    in_repo: bool


def locate_checkout(cwd: Path) -> tuple[Path, Path] | None:
    """Resolve cwd's repo: returns (worktree top level, primary checkout
    root) or None when cwd is not inside a git working tree. The primary
    root comes from the git *common* directory, which linked worktrees
    share with the main checkout -- the anchor that makes checkout
    identity worktree-proof."""
    result = run.run(["rev-parse", "--show-toplevel", "--git-common-dir"], cwd)
    if result.returncode != 0:
        return None
    lines = result.stdout.splitlines()
    if len(lines) < 2:
        return None
    toplevel = Path(lines[0]).resolve()
    # --git-common-dir may be relative to cwd; Path('/a') / '/b' is '/b',
    # so joining first handles both shapes.
    common = (cwd / lines[1]).resolve()
    if common.name != ".git":
        # A bare repo or a detached git dir; no rostered checkout looks
        # like this, so identity cannot match.
        return None
    return toplevel, common.parent


def resolve_workspace(entry: Entry, cwd: Path) -> Workspace:
    """Verify cwd against the roster entry and return the Workspace.

    Raises RefusalError when cwd is neither inside the registered checkout
    (or a linked worktree of it) nor under one of the entry's
    operable_from roots.
    """
    cwd = cwd.resolve()
    checkout = entry.checkout.resolve()
    located = locate_checkout(cwd)
    if located is not None:
        toplevel, primary = located
        if primary == checkout:
            return Workspace(entry=entry, root=toplevel, in_repo=True)
    for allowed in entry.operable_from:
        resolved = allowed.resolve()
        if cwd == resolved or cwd.is_relative_to(resolved):
            return Workspace(entry=entry, root=checkout, in_repo=False)
    raise RefusalError(
        f"cwd {cwd} is not inside the registered checkout for "
        f"{entry.label!r} ({entry.checkout}) or its worktrees"
        + (
            ", nor under its operable_from roots"
            if entry.operable_from
            else ""
        )
        + "; run from a working copy of the rostered repo"
    )


def _normalize_url(url: str) -> str:
    normalized = url.strip().rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[: -len(".git")]
    return normalized


def verify_remote(workspace: Workspace) -> None:
    """Verify the workspace against the entry's registered remote.

    For a machine-local entry there is no remote to check, but an
    operable_from workspace still verifies that the registered checkout
    actually is a git repo (a stale roster path is a deployment problem:
    GitError with the auth/config code, the fjw precedent).
    Raises RefusalError on a missing remote or a URL mismatch.
    """
    entry = workspace.entry
    if not workspace.in_repo and locate_checkout(workspace.root) is None:
        raise run.GitError(
            f"registered checkout for {entry.label!r} ({entry.checkout}) is "
            "not a git working tree; fix the roster",
            plan.EXIT_AUTH,
        )
    if entry.machine_local:
        return
    result = run.run(["remote", "get-url", entry.remote], workspace.root)
    if result.returncode != 0:
        raise RefusalError(
            f"repo {entry.label!r}: remote {entry.remote!r} is not "
            f"configured in {workspace.root}"
        )
    actual = result.stdout.strip()
    if _normalize_url(actual) != _normalize_url(entry.remote_url):
        raise RefusalError(
            f"repo {entry.label!r}: remote {entry.remote!r} points at "
            f"{actual!r}, but the roster registers {entry.remote_url!r} -- "
            "this working copy is not the blessed one"
        )


def authoritative_ref(entry: Entry) -> tuple[str, str]:
    """The authoritative default branch as (display name, full refname):
    the fetched remote-tracking ref, or the local branch itself for a
    machine-local repo (the degradation rule)."""
    if entry.machine_local:
        return entry.default_branch, f"refs/heads/{entry.default_branch}"
    display = f"{entry.remote}/{entry.default_branch}"
    return display, f"refs/remotes/{entry.remote}/{entry.default_branch}"


def ref_exists(root: Path, refname: str) -> bool:
    result = run.run(["rev-parse", "--verify", "--quiet", refname], root)
    return result.returncode == 0


def current_branch(root: Path) -> str | None:
    """The checked-out branch name, or None when HEAD is detached."""
    return run.output(["symbolic-ref", "--quiet", "--short", "HEAD"], root)


def head_commit(root: Path) -> str | None:
    """The HEAD commit hash, or None on an unborn branch."""
    return run.output(["rev-parse", "--verify", "--quiet", "HEAD"], root)


def upstream_of(root: Path, branch: str) -> str | None:
    """The branch's configured upstream as a short name (e.g.
    'origin/fix-x'), or None when no upstream is set."""
    return run.output(
        [
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            branch + "@{upstream}",
        ],
        root,
    )


def ahead_behind(root: Path, ref: str, base: str) -> tuple[int, int] | None:
    """(commits only in `ref`, commits only in `base`), or None when
    either side is unresolvable (unborn branch, missing base)."""
    counts = run.output(
        ["rev-list", "--left-right", "--count", f"{ref}...{base}"], root
    )
    if counts is None:
        return None
    left, right = counts.split()
    return int(left), int(right)


def status_entries(root: Path, pathspecs: tuple = ()) -> list:
    """Porcelain status records as (index_state, tree_state, path)
    tuples, optionally limited to `pathspecs`. Rename/copy origin paths
    are consumed (the reported path is the destination); ignored files
    stay ignored. Untracked files list individually (-uall), never as a
    collapsed directory -- gitw-commit's sweep guard must see the actual
    file paths a directory hides."""
    arguments = ["status", "--porcelain", "-z", "--untracked-files=all"]
    if pathspecs:
        arguments += ["--", *list(pathspecs)]
    result = run.run(arguments, root)
    if result.returncode != 0:
        detail = result.stderr.strip() or "no output"
        raise run.GitError(f"git status failed: {detail}")
    entries = []
    # Never strip: the first entry's index-state column may be a space.
    fields = iter(result.stdout.split("\0"))
    for field in fields:
        if len(field) < 3:
            continue
        index_state, tree_state = field[0], field[1]
        if index_state in "RC" or tree_state in "RC":
            # Rename/copy records carry an origin path in a second NUL
            # field -- in *either* column (` R` is a worktree-side rename).
            next(fields, None)
        entries.append((index_state, tree_state, field[3:]))
    return entries


def status_counts(root: Path) -> dict:
    """Dirty/untracked tallies for the worktree: {'staged', 'unstaged',
    'untracked'}. Unmerged entries count on both tracked sides (any
    nonzero tally means not clean)."""
    staged = unstaged = untracked = 0
    for index_state, tree_state, _ in status_entries(root):
        if index_state == "?":
            untracked += 1
            continue
        if index_state != " ":
            staged += 1
        if tree_state not in " ?":
            unstaged += 1
    return {"staged": staged, "unstaged": unstaged, "untracked": untracked}


# Shared with fjw; see lib.arguments for the bare-slash semantics.
branch_matches_prefix = arguments.branch_matches_prefix


def describe_dirty(counts: dict) -> str:
    """One phrase for a status_counts() result, for refusal messages."""
    return (
        f"staged {counts['staged']}, unstaged {counts['unstaged']}, "
        f"untracked {counts['untracked']}"
    )


def require_prefixed_branch(
    root: Path, prefix: str, label: str, default_branch: str
) -> str:
    """The branch-prefix scope check shared by every mutating verb: the
    worktree's current branch must be <prefix> plus a non-empty tail.
    Returns the branch name; RefusalError on detached HEAD or mismatch."""
    branch = current_branch(root)
    if branch is None:
        raise RefusalError(
            f"worktree {root} has a detached HEAD; the branch-prefix scope "
            "requires a checked-out branch (gitw-branch-start creates one)"
        )
    require_branch_in_scope(branch, prefix, label, default_branch)
    return branch


def require_branch_in_scope(
    branch: str, prefix: str, label: str, default_branch: str
) -> None:
    """RefusalError unless `branch` matches `prefix`. Under the bare-slash
    prefix the default branch is refused too: a real prefix can never
    match a slashless default like 'main', and that implicit guard must
    not vanish when the prefix constraint does."""
    if not branch_matches_prefix(branch, prefix):
        raise RefusalError(
            f"current branch {branch!r} does not match the pinned prefix "
            f"{prefix!r} for {label!r} -- the prefix is the allowlist "
            "scope; switch branches or fix the invocation"
        )
    if prefix == arguments.NO_BRANCH_PREFIX and branch == default_branch:
        raise RefusalError(
            f"branch {branch!r} is the authoritative default branch of "
            f"{label!r}; the bare-slash prefix {prefix!r} admits any branch "
            "except the default"
        )


def rebase_head_branch(root: Path) -> str | None:
    """The branch an in-progress rebase is rewriting (HEAD is detached
    mid-rebase, so the state directory's head-name is the identity), or
    None when no rebase is in progress."""
    for state_dir in ("rebase-merge", "rebase-apply"):
        location = run.output(
            ["rev-parse", "--git-path", f"{state_dir}/head-name"], root
        )
        if location is None:
            continue
        head_name = Path(root) / location
        if not head_name.is_file():
            continue
        try:
            name = head_name.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if name.startswith("refs/heads/"):
            return name[len("refs/heads/") :]
        return name or None
    return None


def pending_operation(root: Path) -> str | None:
    """The multi-step operation whose pending-commit state a plain commit
    would silently conclude ('merge', 'cherry-pick', 'revert'), or None.
    A commit made with MERGE_HEAD present, for example, quietly becomes a
    two-parent merge commit."""
    for ref, operation in (
        ("MERGE_HEAD", "merge"),
        ("CHERRY_PICK_HEAD", "cherry-pick"),
        ("REVERT_HEAD", "revert"),
    ):
        if ref_exists(root, ref):
            return operation
    return None


def conflicted_paths(root: Path) -> list:
    """Paths with unmerged index entries, NUL-parsed and ordered as git
    reports them."""
    result = run.run(["diff", "--name-only", "--diff-filter=U", "-z"], root)
    if result.returncode != 0:
        detail = result.stderr.strip() or "no output"
        raise run.GitError(f"git diff --diff-filter=U failed: {detail}")
    return [path for path in result.stdout.split("\0") if path]


def worktree_holding_branch(root: Path, branch: str) -> Path | None:
    """The worktree that has `branch` checked out, or None. Runs from any
    worktree of the repo (the list is repo-wide) -- git's
    one-checkout-per-branch rule makes this the 'another agent is live on
    this branch' detector."""
    raw = run.must(["worktree", "list", "--porcelain"], root)
    current: Path | None = None
    for line in raw.splitlines():
        if line.startswith("worktree "):
            current = Path(line[len("worktree ") :])
        elif line == f"branch refs/heads/{branch}" and current is not None:
            return current.resolve()
    return None
