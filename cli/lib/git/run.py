"""Subprocess substrate for the gitw verbs (the git CLI, stdlib-only).

Non-interactive by construction: every invocation closes stdin, disables
the terminal credential prompt, and neuters editor/pager hooks -- anything
that could block waiting for input is a defect (unattended consumers hang).
For commands that may reach the network, ssh gets -oBatchMode=yes unless
the user has already taken control of the ssh command (GIT_SSH_COMMAND /
GIT_SSH in the environment, or core.sshCommand in git config), in which
case their setup is trusted to be non-interactive.

Remote failures classify into the shared exit-code taxonomy (lib.plan):
auth markers are 5, a missing remote repository is 3, everything else
remote is network (6, the one retryable class). Local failures stay
unclassified runtime (1) unless a verb reclassifies them.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

from lib import plan

_TIMEOUT_SECONDS = 300

_AUTH_MARKERS = (
    "permission denied",
    "authentication failed",
    "could not read username",
    "could not read password",
    "invalid username or password",
    "publickey",
)
_NOT_FOUND_MARKERS = (
    "repository not found",
    "does not appear to be a git repository",
)


class GitError(Exception):
    """A classified git failure: `exit_code` is from the shared taxonomy."""

    def __init__(self, message: str, exit_code: int = plan.EXIT_RUNTIME):
        super().__init__(message)
        self.exit_code = exit_code


def die(message: str, code: int) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def base_environment() -> dict:
    """The environment every git subprocess gets: no terminal prompts, no
    editor, no pager, no askpass (a configured GUI askpass would stall to
    the timeout; with prompts dead, missing credentials drive git to its
    "could not read Username" path, which classifies as auth). LC_ALL=C
    because failure classification sniffs English message substrings, and
    GIT_OPTIONAL_LOCKS=0 because even `git status` opportunistically
    rewrites the index -- orient's operable_from mode reads a primary
    checkout that may be another live agent's working copy."""
    environment = dict(os.environ)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment["GIT_EDITOR"] = "true"
    environment["GIT_SEQUENCE_EDITOR"] = "true"
    environment["GIT_PAGER"] = "cat"
    environment["GIT_ASKPASS"] = "/usr/bin/false"
    environment["SSH_ASKPASS"] = "/usr/bin/false"
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["LC_ALL"] = "C"
    return environment


def remote_environment(cwd: Path) -> dict:
    """base_environment() plus batch-mode ssh, unless the user's own ssh
    arrangement (environment variable or core.sshCommand config) is
    already in charge."""
    environment = base_environment()
    if "GIT_SSH_COMMAND" in os.environ or "GIT_SSH" in os.environ:
        return environment
    probe = run(["config", "--get", "core.sshCommand"], cwd)
    if probe.returncode == 0 and probe.stdout.strip():
        return environment
    environment["GIT_SSH_COMMAND"] = "ssh -oBatchMode=yes"
    return environment


def run(
    arguments: list[str],
    cwd: Path,
    env: dict | None = None,
    remote: bool = False,
) -> subprocess.CompletedProcess:
    """Run one git command; never raises on a nonzero exit (callers decide
    what a failure means). Raises GitError on a timeout: network (the one
    retryable class) when `remote` says the call touches the network,
    unclassified runtime otherwise -- a local command that stalls (a hung
    hook, fsmonitor) must not invite a retry loop that re-runs it."""
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=str(cwd),
            env=env or base_environment(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        raise GitError(
            f"git {' '.join(arguments)} timed out after {_TIMEOUT_SECONDS}s",
            plan.EXIT_NETWORK if remote else plan.EXIT_RUNTIME,
        )


def output(arguments: list[str], cwd: Path) -> str | None:
    """Run one git command and return its stripped stdout, or None on a
    nonzero exit."""
    result = run(arguments, cwd)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def must(arguments: list[str], cwd: Path) -> str:
    """Run one git command that is expected to succeed; returns stripped
    stdout, raises GitError (unclassified runtime) otherwise."""
    result = run(arguments, cwd)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise GitError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout.strip()


def classify_remote_failure(detail: str) -> int:
    """Map a failed remote operation's stderr to an exit code: auth (5),
    missing remote repository (3), else network (6)."""
    lowered = detail.lower()
    if any(marker in lowered for marker in _AUTH_MARKERS):
        return plan.EXIT_AUTH
    if any(marker in lowered for marker in _NOT_FOUND_MARKERS):
        return plan.EXIT_NOT_FOUND
    return plan.EXIT_NETWORK


def fetch(remote: str, cwd: Path) -> None:
    """`git fetch --prune <remote>` -- the exact sanctioned form
    (configured refspec only; remote-tracking refs and FETCH_HEAD are the
    only writes). Pruning keeps the remote-tracking refs truthful: a ref
    deleted on the remote must not linger locally, because gitw-push's
    named-target lease reads its expectation from exactly those refs and
    a stale one would refuse every later pointer move as "moved". Raises
    GitError classified via classify_remote_failure."""
    result = run(
        ["fetch", "--prune", remote], cwd, env=remote_environment(cwd),
        remote=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise GitError(
            f"git fetch {remote} failed: {detail}",
            classify_remote_failure(detail),
        )
