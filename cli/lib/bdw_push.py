"""Push a Beads database to its Dolt remote, coalesced, for bdw.

bdw calls request_push() after every write that bd ran successfully. That
records a dirty mark and starts this file as a detached background worker
(`python3 bdw_push.py <beads-dir> <bd>`), so the write returns at once and
the push never affects bdw's exit code. The worker:

1. takes a lock (fcntl.flock, non-blocking); if another worker holds it,
   exits at once, since the holder sees the dirty mark;
2. while the dirty mark exists: clears it and pushes once, so writes that
   land during a push get exactly one more push. There is no cap on
   passes: the loop runs only while writes keep arriving;
3. releases the lock, then checks the dirty mark once more and goes back to
   1, so a mark set just before the release is not lost.

The worker exits under the Exit-code contract (see exit_code): 2 for a
malformed invocation, 1 when its last push failed, 4 when the destination
guard refused it, else 0. Nothing reads that exit today; bdw reports from
the state files below.

One push:

- reads the Dolt remotes from the embedded database's repo_state.json
  (`<beads-dir>/embeddeddolt/<dolt_database>/.dolt/repo_state.json`,
  named by metadata.json); with no remote, or a database not in embedded
  mode, it does nothing;
- refuses when any Dolt remote URL names the same repository as any of the
  workspace's git remotes (see same_repository), so Issue data never goes
  where the code goes;
- skips when bd's effective `no-push` config is true (config.yaml, or the
  BD_NO_PUSH environment variable, which bd maps to it);
- runs `bd dolt push --no-adopt` with BD_NO_REMOTE_ADOPT=1, because bd
  1.3.0 otherwise offers to adopt a remote derived from the git origin.

State lives outside the repo, under
`$XDG_STATE_HOME/agent-tooling/bdw-push/<key>/` (XDG_STATE_HOME defaulting
to ~/.local/state; <key> a hash of the Beads directory): `lock`, `dirty`,
`last-failure.json` (present only while the last push failed), and
`push.log`. bdw reads last-failure.json to warn on its next call. Without a
resolvable state directory nothing is pushed.

Standard library only; Python 3.9.
"""

from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

PUSH_TIMEOUT = 300
LOG_LIMIT = 256 * 1024
STDERR_TAIL = 2000

Runner = Callable[[Sequence[str], Mapping[str, str], Path], "tuple[int, str, str]"]


# -- state ------------------------------------------------------------------

def state_dir(beads_dir: Path, environ: Mapping[str, str]) -> Path | None:
    """The per-database state directory, or None when neither
    XDG_STATE_HOME nor HOME is set."""
    base = environ.get("XDG_STATE_HOME")
    if base:
        root = Path(base)
    elif environ.get("HOME"):
        root = Path(environ["HOME"]) / ".local" / "state"
    else:
        return None
    key = hashlib.sha256(
        str(beads_dir.resolve()).encode("utf-8")).hexdigest()[:16]
    return root / "agent-tooling" / "bdw-push" / key


def last_failure(state: Path) -> dict | None:
    """The last push failure, or None when the last push succeeded."""
    try:
        payload = json.loads((state / "last-failure.json").read_text())
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _log(state: Path, message: str) -> None:
    log = state / "push.log"
    try:
        if log.exists() and log.stat().st_size > LOG_LIMIT:
            log.write_text("")
        with log.open("a") as handle:
            handle.write(f"{_now()} {message}\n")
    except OSError:
        pass


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _record_failure(state: Path, reason: str, detail: str = "") -> None:
    _log(state, f"FAILED: {reason}" + (f"\n{detail}" if detail else ""))
    payload = {"time": _now(), "reason": reason}
    try:
        (state / "last-failure.json").write_text(json.dumps(payload) + "\n")
    except OSError:
        pass


def _clear_failure(state: Path) -> None:
    try:
        os.unlink(state / "last-failure.json")
    except OSError:
        pass


# -- remotes ----------------------------------------------------------------

def dolt_remote_urls(beads_dir: Path) -> list[str] | None:
    """The Dolt remote URLs of the workspace's embedded database; [] when
    there are none; None when the database is not embedded or its state
    cannot be read (nothing to push to that bdw knows of)."""
    try:
        metadata = json.loads((beads_dir / "metadata.json").read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(metadata, dict):
        return None
    if metadata.get("dolt_mode", "embedded") != "embedded":
        return None
    database = metadata.get("dolt_database")
    if not isinstance(database, str) or not database or "/" in database:
        return None
    state_file = (beads_dir / "embeddeddolt" / database / ".dolt"
                  / "repo_state.json")
    try:
        repo_state = json.loads(state_file.read_text())
    except (OSError, ValueError):
        return None
    remotes = repo_state.get("remotes") if isinstance(repo_state, dict) else None
    if not isinstance(remotes, dict):
        return []
    urls = []
    for remote in remotes.values():
        if isinstance(remote, dict) and isinstance(remote.get("url"), str):
            urls.append(remote["url"])
    return urls


_SCP = re.compile(r"^(?:[^@/]+@)?([^:/]+):(?!//)(.+)$")
_URL = re.compile(r"^[a-z][a-z0-9+.-]*://(?:[^@/]+@)?([^/:]+)(?::\d+)?(/.*)?$",
                  re.IGNORECASE)


def repository_key(url: str) -> tuple[str, str] | None:
    """A (host, path) key naming the repository a URL points at: scheme,
    user, port, a trailing `.git` or `/`, and case dropped, so the
    git+ssh, ssh, https, and scp-style forms of one repository agree. A
    file URL or bare path keys as ('', path). None when unreadable."""
    text = url.strip()
    if not text:
        return None
    lowered = text.lower()
    if lowered.startswith("file://"):
        host, path = "", text[len("file://"):]
    else:
        match = _URL.match(text)
        if match:
            host, path = match.group(1), match.group(2) or ""
        else:
            match = _SCP.match(text)
            if match:
                host, path = match.group(1), match.group(2)
            elif text.startswith("/"):
                host, path = "", text
            else:
                return None
    path = path.strip("/")
    if path.endswith(".git"):
        path = path[:-len(".git")]
    path = path.strip("/")
    return host.lower(), path.lower()


def same_repository(left: str, right: str) -> bool:
    a, b = repository_key(left), repository_key(right)
    return a is not None and a == b


def git_remote_urls(workspace: Path, environ: Mapping[str, str],
                    runner: Runner) -> list[str] | None:
    """Every URL of every git remote of the workspace, or None when git
    cannot say."""
    code, out, _ = runner(
        ["git", "-C", str(workspace), "config", "--get-regexp",
         r"^remote\..*\.(url|pushurl)$"], environ, workspace)
    if code == 1 and not out.strip():
        return []  # no remotes at all
    if code != 0:
        return None
    return [line.split(None, 1)[1].strip()
            for line in out.splitlines() if len(line.split(None, 1)) == 2]


# -- one push ---------------------------------------------------------------

def run_command(argv: Sequence[str], environ: Mapping[str, str],
                cwd: Path) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            list(argv), env=dict(environ), cwd=str(cwd),
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=PUSH_TIMEOUT)
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {PUSH_TIMEOUT}s"
    except OSError as error:
        return 127, "", str(error)
    return (result.returncode,
            result.stdout.decode("utf-8", "replace"),
            result.stderr.decode("utf-8", "replace"))


def push_once(beads_dir: Path, state: Path, bd: str,
              environ: Mapping[str, str], runner: Runner = run_command,
              remotes: Callable[[Path], "list[str] | None"] = dolt_remote_urls,
              ) -> str:
    """Push once; return what happened: 'pushed', 'no-remote', 'opted-out',
    'refused', or 'failed'."""
    workspace = beads_dir.parent
    dolt_urls = remotes(beads_dir)
    if not dolt_urls:
        _clear_failure(state)
        return "no-remote"
    environment = dict(environ)
    environment["BD_NO_REMOTE_ADOPT"] = "1"
    git_urls = git_remote_urls(workspace, environment, runner)
    if git_urls is None:
        _record_failure(state, "refused: cannot read the workspace's git "
                        "remotes to check the push destination")
        return "refused"
    for dolt_url in dolt_urls:
        if any(same_repository(dolt_url, git_url) for git_url in git_urls):
            _record_failure(state, "refused: a Dolt remote names the same "
                            "repository as a git remote of this workspace")
            return "refused"
    code, out, _ = runner([bd, "config", "get", "no-push"], environment,
                          workspace)
    if code == 0 and out.strip().lower() == "true":
        _log(state, "skipped: no-push is set")
        return "opted-out"
    code, _, err = runner([bd, "dolt", "push", "--no-adopt"], environment,
                          workspace)
    if code != 0:
        _record_failure(state, f"bd dolt push exited {code}",
                        err[-STDERR_TAIL:])
        return "failed"
    _clear_failure(state)
    _log(state, "pushed")
    return "pushed"


# -- coalescing -------------------------------------------------------------

def _try_lock(state: Path):
    handle = open(state / "lock", "a")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        handle.close()
        if error.errno in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK):
            return None
        raise
    return handle


def _take_dirty(state: Path) -> bool:
    try:
        os.unlink(state / "dirty")
    except FileNotFoundError:
        return False
    return True


def run_worker(beads_dir: Path, state: Path, bd: str,
               environ: Mapping[str, str],
               push: Callable[[], str] | None = None) -> list[str]:
    """Push until the dirty mark stays clear; return each push's outcome.
    Returns [] at once when another worker holds the lock.

    There is no cap on passes: the worker loops only while writes keep
    setting the mark, and a cap would have to clear a mark without pushing,
    stranding the last writes of a busy session until the next write."""
    if push is None:
        def push():
            return push_once(beads_dir, state, bd, environ)
    outcomes: list[str] = []
    while True:
        handle = _try_lock(state)
        if handle is None:
            return outcomes
        try:
            while _take_dirty(state):
                outcomes.append(push())
        finally:
            handle.close()
        # A write may have set the mark after the last take but before the
        # release, when its own worker found the lock still held.
        if not (state / "dirty").exists():
            return outcomes


def exit_code(outcomes: Sequence[str]) -> int:
    """The worker's exit under the Exit-code contract, from its last push:
    1 when the push failed, 4 when the destination guard refused it,
    otherwise 0 (pushed, nothing to push, opted out, or left to the lock's
    holder). Nothing reads it today; the push log and last-failure.json
    are what bdw reports from."""
    last = outcomes[-1] if outcomes else None
    if last == "failed":
        return 1
    if last == "refused":
        return 4
    return 0


def request_push(beads_dir: Path, bd: str, environ: Mapping[str, str],
                 spawn: Callable[[Sequence[str], Mapping[str, str]], None]
                 | None = None) -> Path | None:
    """Mark the database dirty and start a detached worker. Returns the
    state directory, or None when there is none (nothing is pushed)."""
    state = state_dir(beads_dir, environ)
    if state is None:
        return None
    try:
        state.mkdir(parents=True, exist_ok=True)
        (state / "dirty").touch()
    except OSError:
        return None
    argv = [sys.executable, str(Path(__file__).resolve()),
            str(beads_dir), bd]
    try:
        (spawn or _spawn_detached)(argv, environ)
    except OSError as error:
        _record_failure(state, f"cannot start the push worker: {error}")
    return state


def _spawn_detached(argv: Sequence[str], environ: Mapping[str, str]) -> None:
    subprocess.Popen(
        list(argv), env=dict(environ), stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        close_fds=True, start_new_session=True)


def main(argv: Iterable[str]) -> int:
    arguments = list(argv)
    if len(arguments) != 2:
        return 2
    beads_dir, bd = Path(arguments[0]), arguments[1]
    state = state_dir(beads_dir, os.environ)
    if state is None:
        return 0
    return exit_code(run_worker(beads_dir, state, bd, os.environ))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
