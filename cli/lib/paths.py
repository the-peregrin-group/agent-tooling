"""Where agent-tooling keeps its machine-specific files: the config and
state directories of the three-root layout (docs/adr/0015-three-roots-for-
machine-specific-files.md).

    config_dir(tool, environ)  ${XDG_CONFIG_HOME:-$HOME/.config}/agent-tooling/<tool>
    state_dir(tool, environ)   ${XDG_STATE_HOME:-$HOME/.local/state}/agent-tooling/<tool>

Config is small and hand-maintained, sometimes secret (a roster, a token);
state is machine-generated, churns, and is safe to delete (a lock, a log).
The third root, the Install Targets, is the Installer's (`lib.install`).
`config_root(environ)` and `state_root(environ)` return the roots
themselves, the part before `agent-tooling/`.

The resolvers are pure: they read only the mapping the caller passes
(normally `os.environ`), never the process environment or the filesystem,
and never create anything. That makes every caller's source of location
explicit and gives tests one seam: pass a mapping whose roots point into a
temporary directory.

Resolution follows the XDG Base Directory spec where it speaks:

- An XDG variable that is unset or empty means its default under HOME.
- An XDG variable holding a relative path is ignored, as the spec directs,
  and the default under HOME is used instead.
- An absolute XDG value is honored as given, even one that is not a
  directory: `gitw_test_support` sets XDG_CONFIG_HOME to /dev/null for git
  subprocesses, and there the config directory resolves under /dev/null,
  reads find nothing, and `ensure_private_dir` raises OSError. Resolving
  stays pure rather than probing the filesystem to second-guess it.

HOME is the one way home is found: not `Path.home()` or `expanduser()`,
which fall back to the password database and so escape the injected
mapping. A HOME that is unset, empty, or relative is unusable (a relative
one would resolve against whatever directory the caller runs in), and when
it is needed the resolvers return None. Callers treat None as "no place to
keep this file" and decide for themselves whether that means skip or fail.

`ensure_private_dir(path, root)` creates `path`, a directory at or below
one of the roots, with mode 0700, as the spec asks of directories it
creates. It creates the root itself when missing (`~/.local/state` often
is), but never the root's parent: a missing home directory, or an XDG
variable naming a place that does not exist, is a misconfigured
environment to report, not a tree to build. A directory that already
exists keeps its mode: tightening a user's own directory is the user's
call.

`tool` names one tool's subdirectory (`gitw`, `bdw`, `triage-issues`): a
lowercase name of letters, digits, and hyphens, so that it is one path
segment and can never climb out of the product directory. Anything else is
a programming error and raises ValueError.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Mapping

PRODUCT = "agent-tooling"

# Used with fullmatch: `$` would also match before a final newline.
_TOOL = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def config_root(environ: Mapping[str, str]) -> Path | None:
    """The config root, or None when neither XDG_CONFIG_HOME nor HOME is
    usable."""
    return _root(environ, "XDG_CONFIG_HOME", (".config",))


def state_root(environ: Mapping[str, str]) -> Path | None:
    """The state root, or None when neither XDG_STATE_HOME nor HOME is
    usable."""
    return _root(environ, "XDG_STATE_HOME", (".local", "state"))


def config_dir(tool: str, environ: Mapping[str, str]) -> Path | None:
    """`<config root>/agent-tooling/<tool>`, or None when no root resolves."""
    return _tool_dir(tool, config_root(environ))


def state_dir(tool: str, environ: Mapping[str, str]) -> Path | None:
    """`<state root>/agent-tooling/<tool>`, or None when no root resolves."""
    return _tool_dir(tool, state_root(environ))


def ensure_private_dir(path: Path, root: Path) -> None:
    """Create `path`, and whatever is missing between `root` and it, with
    mode 0700.

    Raises ValueError when `path` is not `root` or below it, and OSError
    when a directory cannot be created: FileNotFoundError when the root's
    parent is missing, another OSError when a file is in the way.
    Existing directories are left as they are."""
    if (path != root and root not in path.parents) or \
            ".." in path.relative_to(root).parts:
        raise ValueError(f"{path} is not under {root}")
    missing = []
    current = path
    while not current.is_dir():
        missing.append(current)
        if current == root:
            break
        current = current.parent
    if root in missing and not root.parent.is_dir():
        raise FileNotFoundError(f"no such directory: {root.parent}")
    for directory in reversed(missing):
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            if not directory.is_dir():
                raise
            continue  # a concurrent caller created it first
        # mkdir's mode is filtered by the umask; set it outright.
        os.chmod(directory, 0o700)


def _root(environ: Mapping[str, str], variable: str,
          default: tuple[str, ...]) -> Path | None:
    root = _absolute(environ.get(variable))
    if root is not None:
        return root
    home = _absolute(environ.get("HOME"))
    return None if home is None else home.joinpath(*default)


def _tool_dir(tool: str, root: Path | None) -> Path | None:
    if not isinstance(tool, str) or not _TOOL.fullmatch(tool):
        raise ValueError(f"not a tool name: {tool!r}")
    return None if root is None else root / PRODUCT / tool


def _absolute(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else None
