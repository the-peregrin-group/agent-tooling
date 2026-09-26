"""Shared support for the gitw-* wrapper test files.

Builds throwaway git repositories entirely offline: a bare file-path
"remote" plus clones, with identity and global/system config isolated per
invocation so no test depends on (or touches) the developer's git setup or
the real roster. Repo/label names here are invented fixtures -- never real
projects.
"""

from __future__ import annotations

import os
import subprocess
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

_ISOLATED_CONFIG = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    # Deterministic commit identity for the wrapper's own commit-creating
    # calls (commit, commit-tree): with config isolated above, git would
    # otherwise fall back to auto-detected user@host identity -- or fail
    # outright on machines where auto-detection cannot.
    "GIT_AUTHOR_NAME": "gitw-test",
    "GIT_AUTHOR_EMAIL": "gitw-test@example.invalid",
    "GIT_COMMITTER_NAME": "gitw-test",
    "GIT_COMMITTER_EMAIL": "gitw-test@example.invalid",
    # The *default* global ignore file ($XDG_CONFIG_HOME/git/ignore, or
    # ~/.config/git/ignore) applies even with the config files nulled;
    # pointing XDG at a non-directory makes ambient ignore rules (e.g. a
    # developer-machine rule for settings.local.json) invisible to tests.
    "XDG_CONFIG_HOME": os.devnull,
}


def git(cwd: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run one git command in a fixture repo; asserts success unless
    `check` is off (fixture building is not what any test is testing, but
    some fixtures need a deliberately failing command, e.g. a conflicted
    rebase)."""
    result = subprocess.run(
        [
            "git",
            "-c", "user.name=gitw-test",
            "-c", "user.email=gitw-test@example.invalid",
            "-c", "commit.gpgsign=false",
            "-c", "init.defaultBranch=main",
            *arguments,
        ],
        cwd=str(cwd),
        env={**os.environ, **_ISOLATED_CONFIG},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"fixture git {arguments} failed in {cwd}: {result.stderr}"
        )
    return result


def make_remote_and_clone(base: Path) -> tuple[Path, Path, Path]:
    """One bare 'remote' with a seeded main branch, plus two clones:
    returns (remote, seed, clone). Tests advance the remote by committing
    and pushing from `seed`; the wrapper under test operates in `clone`."""
    remote = base / "remote.git"
    remote.mkdir()
    git(remote, "init", "--bare", "--initial-branch=main", ".")
    git(base, "clone", str(remote), "seed")
    seed = base / "seed"
    (seed / "README.md").write_text("seed\n")
    git(seed, "add", "-A")
    git(seed, "commit", "-m", "seed")
    git(seed, "push", "origin", "main")
    git(base, "clone", str(remote), "clone")
    return remote, seed, base / "clone"


def commit_on(repository: Path, filename: str, content: str, message: str) -> None:
    """One commit touching `filename` in `repository`."""
    (repository / filename).write_text(content)
    git(repository, "add", filename)
    git(repository, "commit", "-m", message)


def advance_remote(seed: Path, filename: str = "advance.txt") -> None:
    """Move the remote's main forward by one commit, via the seed clone."""
    commit_on(seed, filename, "advance\n", "advance main")
    git(seed, "push", "origin", "main")


def add_pre_push_hook(repository: Path, body: str) -> None:
    """Install an executable sh pre-push hook in a non-bare fixture repo;
    `body` follows the shebang line."""
    hook = repository / ".git" / "hooks" / "pre-push"
    hook.write_text("#!/bin/sh\n" + body)
    hook.chmod(0o755)


def proxies_off():
    """Patch os.environ so a push to a loopback URL cannot be sent
    off-host by a proxy configured on the machine: no_proxy for the
    environment variables, and an empty http.proxy through command-line
    config (GIT_CONFIG_COUNT, git 2.31+). Returns the patcher, for use as
    a context manager."""
    return mock.patch.dict(
        "os.environ",
        {
            "no_proxy": "*",
            "NO_PROXY": "*",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "http.proxy",
            "GIT_CONFIG_VALUE_0": "",
        },
    )


@contextmanager
def chdir(path: Path):
    """contextlib.chdir is 3.11+; the entry points pin Apple's 3.9."""
    previous = os.getcwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(previous)


@contextmanager
def isolated_git_config():
    """Route the wrapper's own git subprocesses (which inherit os.environ)
    away from the developer's global/system git config."""
    saved = {key: os.environ.get(key) for key in _ISOLATED_CONFIG}
    os.environ.update(_ISOLATED_CONFIG)
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
