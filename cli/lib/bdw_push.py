"""Push a Beads database to its Dolt remote, coalesced, for bdw.

bdw calls request_push() after every write that bd ran successfully. That
records a dirty mark and, unless a worker already holds the lock, starts
this file as a detached background worker under the system interpreter
(`/usr/bin/python3 bdw_push.py <beads-dir> <bd>`), so the write returns at
once and the push never affects bdw's exit code. A state directory or mark
that cannot be written comes back as a reason bdw warns with. The worker:

1. takes the coordination lock (fcntl.flock, non-blocking), which no
   child ever inherits; if another worker holds it, exits at once, since
   the holder sees the dirty mark;
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
  mode, it does nothing; when that state cannot be read, it records a
  failure;
- skips, clearing any recorded failure, when bd's effective `no-push` is
  set (config.yaml, or BD_NO_PUSH, which bd maps to it; asked once per
  worker run, and read through bdw's own TRUTHY);
- refuses when any Dolt remote URL names the same repository as any of the
  workspace's git remotes (see same_repository), so Issue data never goes
  where the code goes;
- runs `bd dolt push --no-adopt` with BD_NO_REMOTE_ADOPT=1, because bd
  1.3.0 otherwise offers to adopt a remote derived from the git origin. It
  runs in its own process group, killed whole on timeout.

Before each pass the worker takes the push-in-flight lock, waiting up to
PUSH_TIMEOUT, and only then claims the dirty mark; it hands the lock to
`bd dolt push` alone, whose descendants keep it if they outlive the push,
so the next pass waits for them, and records a failure (keeping the mark)
if they outlast the wait. run_worker's docstring says exactly what is and
is not guaranteed.

State is Machine State (docs/adr/0015-three-roots-for-machine-specific-
files.md), in `push/<key>/` under bdw's subdirectory of the Machine State
Directory, `${XDG_STATE_HOME:-~/.local/state}/agent-tooling/bdw/`, as
lib.paths resolves it (<key> a hash of the Beads directory; missing
directories are created 0700 by lib.paths.ensure_private_dir, and an
existing one keeps its mode, as ADR 0015 decides): the two locks `lock`
and `inflight`, `dirty`, `last-failure.json` (present only while the last
push failed, written atomically), and `push.log`. bdw reads
last-failure.json to warn on its next call. Without a resolvable state
root nothing is pushed.

Standard library only; Python 3.9.
"""

from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

if __package__ in (None, ""):
    # Run as a script (the push worker): make `lib` importable, as bdw does.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib import paths  # noqa: E402

PUSH_TIMEOUT = 300
KILL_WAIT = 10
LOG_LIMIT = 256 * 1024
STDERR_TAIL = 2000
STDOUT_LIMIT = 64 * 1024

# The interpreter the worker runs under: the system one every shebang here
# pins, since on macOS it is the one Local Network access is granted to (a
# Homebrew or pyenv interpreter is silently denied it in background
# sessions), whatever interpreter bdw itself was started with.
WORKER_PYTHON = "/usr/bin/python3"

# The values, compared case-insensitively after trimming, that turn the
# push off: in BD_NO_PUSH, and in bd's `no-push` config as `bd config get`
# prints it (the raw value, such as `1` or `yes`). bdw is the one that
# pushes, so this set, not bd's own parsing, decides; it takes the forms
# Go's strconv.ParseBool reads as true (1, t, true) plus yes and on. bdw's
# pre-spawn opt-out and the worker's check share it.
TRUTHY = frozenset({"1", "t", "true", "yes", "on"})

Runner = Callable[[Sequence[str], Mapping[str, str], Path], "tuple[int, str, str]"]


def is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in TRUTHY


# -- state ------------------------------------------------------------------

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
    """Log a failure and write last-failure.json atomically (a temporary
    file, then os.replace), so bdw never reads a half-written record."""
    _log(state, f"FAILED: {reason}" + (f"\n{detail}" if detail else ""))
    payload = {"time": _now(), "reason": reason}
    temporary = state / f"last-failure.json.{os.getpid()}.tmp"
    try:
        with temporary.open("w") as handle:
            handle.write(json.dumps(payload) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, state / "last-failure.json")
    except OSError:
        try:
            os.unlink(temporary)
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
    it has none, or when the database is not in embedded mode (bdw pushes
    only embedded databases); None when its metadata or Dolt state cannot
    be read, which is a failure, not an absence of remotes."""
    try:
        metadata = json.loads((beads_dir / "metadata.json").read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(metadata, dict):
        return None
    if metadata.get("dolt_mode", "embedded") != "embedded":
        return []
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
                cwd: Path, timeout: float = PUSH_TIMEOUT,
                pass_fds: Sequence[int] = ()) -> tuple[int, str, str]:
    """Run a command in its own process group; on timeout, kill the whole
    group, so no grandchild (Dolt's git or ssh) outlives it. `pass_fds`
    hands the child the push-in-flight lock (see run_worker).

    Output goes to temporary files, not pipes, and the wait is on the
    process itself: a descendant that left the group (a daemon that called
    setsid) and still holds the child's stdout or stderr then neither keeps
    the worker past `timeout` nor turns a finished command into a
    timeout. Only the tail of each file is read (STDOUT_LIMIT and
    STDERR_TAIL bytes), and a timeout keeps the stderr tail, since what a
    push printed before it hung (a host-key prompt, say) is the clue."""
    # The temporary files are unlinked at once; a detached descendant that
    # inherited them may go on writing to them after this returns. That
    # costs disk until it exits and is accepted: nothing reads them later.
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            child = subprocess.Popen(
                list(argv), env=dict(environ), cwd=str(cwd),
                stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                start_new_session=True, pass_fds=tuple(pass_fds))
        except OSError as error:
            return 127, "", str(error)
        try:
            code = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except OSError:
                pass
            try:
                child.wait(timeout=KILL_WAIT)
            except subprocess.TimeoutExpired:
                pass  # unkillable for now; the failure is recorded anyway
            return (124, "", f"timed out after {timeout}s\n"
                    + _tail(err, STDERR_TAIL))
        return code, _tail(out, STDOUT_LIMIT), _tail(err, STDERR_TAIL)


def _tail(handle, limit: int) -> str:
    """The last `limit` bytes written to `handle`, decoded."""
    size = handle.seek(0, os.SEEK_END)
    handle.seek(max(0, size - limit))
    return handle.read(limit).decode("utf-8", "replace")


def no_push_configured(bd: str, workspace: Path, environ: Mapping[str, str],
                       runner: Runner) -> bool:
    """Whether bd's effective `no-push` is set: config.yaml, or BD_NO_PUSH,
    which bd maps to it."""
    code, out, _ = runner([bd, "config", "get", "no-push"], environ,
                          workspace)
    return code == 0 and is_truthy(out)


def push_once(beads_dir: Path, state: Path, bd: str,
              environ: Mapping[str, str], runner: Runner = run_command,
              remotes: Callable[[Path], "list[str] | None"] = dolt_remote_urls,
              no_push: Callable[[], bool] | None = None,
              push_runner: Runner | None = None,
              ) -> str:
    """Push once; return what happened: 'pushed', 'no-remote', 'opted-out',
    'refused', or 'failed'. `no_push` answers whether bd's no-push is set;
    run_worker passes one that asks bd once per run. `push_runner` (default
    `runner`) runs `bd dolt push` alone; run_worker's hands that one
    command the push-in-flight lock."""
    workspace = beads_dir.parent
    environment = dict(environ)
    environment["BD_NO_REMOTE_ADOPT"] = "1"
    dolt_urls = remotes(beads_dir)
    if dolt_urls is None:
        _record_failure(state, "cannot read this database's Dolt remotes "
                        "(metadata.json or Dolt's repo_state.json)")
        return "failed"
    if not dolt_urls:
        _clear_failure(state)
        return "no-remote"
    if no_push is None:
        def no_push():
            return no_push_configured(bd, workspace, environment, runner)
    if no_push():
        # An opted-out push clears any old failure, so bdw stops warning.
        _clear_failure(state)
        _log(state, "skipped: no-push is set")
        return "opted-out"
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
    code, _, err = (push_runner or runner)(
        [bd, "dolt", "push", "--no-adopt"], environment, workspace)
    if code != 0:
        _record_failure(state, f"bd dolt push exited {code}",
                        err[-STDERR_TAIL:])
        return "failed"
    _clear_failure(state)
    _log(state, "pushed")
    return "pushed"


# -- coalescing -------------------------------------------------------------

COORDINATION_LOCK = "lock"
INFLIGHT_LOCK = "inflight"
INFLIGHT_POLL = 0.1


class InflightBusy(Exception):
    """A previous push's process still holds the push-in-flight lock."""


def _try_lock(state: Path, name: str = COORDINATION_LOCK):
    """Take `state/name` with a non-blocking exclusive flock; None when
    another holder has it. The file is opened non-inheritable (Python's
    default), so no child gets it unless handed it through pass_fds."""
    handle = open(state / name, "a")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        handle.close()
        if error.errno in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK):
            return None
        raise
    return handle


def _wait_for_inflight(state: Path, timeout: float):
    """Take the push-in-flight lock, polling for up to `timeout` seconds;
    raise InflightBusy when it stays held."""
    deadline = time.monotonic() + timeout
    while True:
        handle = _try_lock(state, INFLIGHT_LOCK)
        if handle is not None:
            return handle
        if time.monotonic() >= deadline:
            raise InflightBusy()
        time.sleep(INFLIGHT_POLL)


def _has_mark(state: Path) -> bool:
    """Whether a write is waiting to be pushed."""
    return (state / "dirty").exists()


def _claim_mark(state: Path) -> bool:
    """Claim the waiting write for the push about to start; False when
    there is none. Called only once the push can start (the push-in-flight
    lock is held), so a worker killed while it waits leaves the mark for
    the next worker."""
    try:
        os.unlink(state / "dirty")
    except FileNotFoundError:
        return False
    return True


def _finish_claim(state: Path, outcome: str) -> None:
    """Called once a claimed push has an outcome (recorded, when it
    failed). Nothing to do while _claim_mark deletes the mark outright."""


def run_worker(beads_dir: Path, state: Path, bd: str,
               environ: Mapping[str, str],
               push: Callable[[], str] | None = None,
               runner: Callable[..., "tuple[int, str, str]"] | None = None,
               remotes: Callable[[Path], "list[str] | None"] = dolt_remote_urls,
               inflight_timeout: float = PUSH_TIMEOUT,
               ) -> list[str]:
    """Push until the dirty mark stays clear; return each push's outcome.
    Returns [] at once when another worker holds the lock.

    There is no cap on passes: the worker loops only while writes keep
    setting the mark, and a cap would have to clear a mark without pushing,
    stranding the last writes of a busy session until the next write.

    bd's `no-push` is asked once per run, at the first push that has a
    remote to go to.

    Two locks, with two jobs. The coordination lock (`lock`) says a worker
    is running; only the worker holds it, never a child, so a killed
    worker frees it at once and the next write starts a new worker. The
    push-in-flight lock (`inflight`) says a `bd dolt push` may still be
    running: the worker takes it, waiting up to `inflight_timeout`, before
    each pass, holds it for the whole pass, and hands it to `bd dolt push`
    alone (pass_fds), whose descendants inherit it too. So a push left
    running by a killed worker, or a descendant that outlives bd (git's
    detached gc, a credential daemon), makes the next pass wait instead of
    running beside it.

    What is guaranteed, and what is not:
    - A pass claims the waiting write (the dirty mark) only after it holds
      the push-in-flight lock. A worker killed while it waits, or that
      fails before the claim, leaves the mark, and the next write's worker
      pushes it with that write. If no write follows, it waits until one
      does.
    - When the push-in-flight lock stays held past the wait, the pass
      records a failure naming the lock, keeps the mark, and the worker
      stops (bdw then warns on every call).
    - Any other error inside a pass is recorded as a failure.
    - Not covered: a worker killed after the claim, mid-push. Its
      orphaned `bd dolt push` runs on; if that push then fails, nothing
      records it, and the claimed write is pushed only with the next
      write."""
    held: list = []
    opted_out: list[bool] = []

    def plain_runner(argv, environment, cwd):
        if runner is not None:
            return runner(argv, environment, cwd, pass_fds=())
        return run_command(argv, environment, cwd)

    def push_runner(argv, environment, cwd):
        fds = (held[0].fileno(),) if held else ()
        if runner is not None:
            return runner(argv, environment, cwd, pass_fds=fds)
        return run_command(argv, environment, cwd, pass_fds=fds)

    def no_push() -> bool:
        if not opted_out:
            environment = dict(environ)
            environment["BD_NO_REMOTE_ADOPT"] = "1"
            opted_out.append(no_push_configured(
                bd, beads_dir.parent, environment, plain_runner))
        return opted_out[0]

    if push is None:
        def push():
            return push_once(beads_dir, state, bd, environ,
                             runner=plain_runner, push_runner=push_runner,
                             remotes=remotes, no_push=no_push)

    def one_pass() -> "tuple[str | None, bool]":
        """One pass: its outcome (None when nothing was waiting), and
        whether the worker must stop."""
        try:
            inflight = _wait_for_inflight(state, inflight_timeout)
        except InflightBusy:
            _record_failure(
                state, "a previous push still holds the push-in-flight lock "
                f"{state / INFLIGHT_LOCK} (see lsof)")
            return "failed", True
        except Exception as error:  # noqa: BLE001 -- recorded, never lost
            _record_failure(state, f"the push worker failed: {error}")
            return "failed", True
        held[:] = [inflight]
        try:
            if not _claim_mark(state):
                return None, True
            try:
                outcome = push()
            except Exception as error:  # noqa: BLE001 -- recorded
                _record_failure(state, f"the push worker failed: {error}")
                outcome = "failed"
            _finish_claim(state, outcome)
            return outcome, False
        finally:
            held[:] = []
            inflight.close()

    outcomes: list[str] = []
    while True:
        handle = _try_lock(state)
        if handle is None:
            return outcomes
        try:
            while _has_mark(state):
                outcome, stop = one_pass()
                if outcome is not None:
                    outcomes.append(outcome)
                if stop:
                    return outcomes
        finally:
            handle.close()
        # A write may have set the mark after the last check but before the
        # release, when its own request found the lock still held.
        if not _has_mark(state):
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
                 | None = None) -> str | None:
    """Mark the database dirty and start a detached worker, unless a worker
    already holds the lock (it sees the mark, before or after its release).
    Returns None when the push was requested, or when there is no state
    directory to request it in (lib.paths finds no state root);
    otherwise a one-line reason the push could not be requested, for bdw to
    warn with."""
    state = state_dir(beads_dir, environ)
    if state is None:
        return None
    try:
        paths.ensure_private_dir(state, paths.state_root(environ))
        (state / "dirty").touch()
    except OSError as error:
        return (f"cannot request a push: state directory {state} is not "
                f"writable ({error.strerror or error})")
    try:
        handle = _try_lock(state)
    except OSError as error:
        return (f"cannot request a push: cannot lock "
                f"{state / COORDINATION_LOCK} ({error.strerror or error})")
    if handle is None:
        return None
    handle.close()
    argv = [WORKER_PYTHON, str(Path(__file__).resolve()), str(beads_dir), bd]
    try:
        (spawn or _spawn_detached)(argv, environ)
    except OSError as error:
        _record_failure(state, f"cannot start the push worker: {error}")
        return f"cannot start the push worker: {error}"
    return None


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
    try:
        return exit_code(run_worker(beads_dir, state, bd, os.environ))
    except Exception as error:  # noqa: BLE001 -- detached: record, not raise
        _record_failure(state, f"the push worker failed: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
