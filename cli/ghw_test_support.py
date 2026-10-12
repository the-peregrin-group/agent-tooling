"""Shared support for the ghw-* wrapper test files.

The wrapper executables have no .py extension, so behavior tests load them
as modules by path. This module holds only maximally-generic scaffolding
shared across the wrapper test files (the gitw and fjw tests use it too);
helpers that aid reading a specific suite stay local to it (tests are
documentation).
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

# A HOME and a PATH that hold nothing: an argument-contract call that
# wrongly got past parsing finds no roster, no Install Target, no forge
# config, and no git or gh to run, so it cannot touch real state or the
# network. Never created.
_EMPTY_HOME = "/tmp/claude/wrapper-argument-contract-test-home-absent"
_EMPTY_PATH = "/tmp/claude/wrapper-argument-contract-test-path-absent"


def load_wrapper_module(script_path: Path):
    """Load a wrapper executable (e.g. .../ghw-pr-merge) as a Python module.

    The module name is the filename with hyphens as underscores, suffixed
    `_script` so it can never shadow a *_test module name.
    """
    loader = SourceFileLoader(
        script_path.name.replace("-", "_") + "_script", str(script_path)
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class ArgumentContractTests:
    """Mixin pinning the Wrapper argument contract (docs/index.md, "Argument
    contract"): a Wrapper accepts exactly the arguments its usage line
    defines, and a surplus positional or an unrecognized flag is a usage
    error, exit 2. A middle-wildcard Permission rule (`Bash(foo bar * baz)`)
    is only as tight as that.

    Mix into a unittest.TestCase and set:
      SCRIPT -- the Wrapper executable.
      LONGEST -- the longest well-formed argument list the usage line
        admits, so anything appended to it is surplus.
      FLAG_SLOT_FORMS -- argument lists that put an unrecognized flag where
        an optional positional, a named flag, or a variadic element goes.
      VARIADIC -- True when the usage line ends in a variadic tail: a
        surplus positional is then one more element by definition, and
        the tail's own validation is pinned in the Wrapper's own tests.
    Every call here must fail at argument-parse time.
    """

    SCRIPT: Path
    LONGEST: tuple = ()
    FLAG_SLOT_FORMS: tuple = ()
    VARIADIC = False

    def _run_contract(self, arguments: tuple) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.SCRIPT), *arguments],
            env={**os.environ, "HOME": _EMPTY_HOME, "PATH": _EMPTY_PATH},
            capture_output=True, text=True, stdin=subprocess.DEVNULL,
            timeout=30,
        )

    def _assert_usage_error(self, arguments: tuple, offender: str) -> None:
        """Exit 2, and stderr either prints the usage line or names the
        offending token (a staged-file slot refuses a flag-shaped path
        with its own message, still exit 2)."""
        with self.subTest(arguments=arguments):
            result = self._run_contract(arguments)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertTrue(
                f"usage: {self.SCRIPT.name}" in result.stderr
                or offender in result.stderr,
                result.stderr,
            )

    def test_surplus_positional_is_usage_error(self):
        if self.VARIADIC:
            self.skipTest("variadic tail: a surplus positional is an element")
        self._assert_usage_error((*self.LONGEST, "surplus"), "surplus")

    def test_unrecognized_flag_is_usage_error(self):
        for arguments in ((*self.LONGEST, "--bogus"), *self.FLAG_SLOT_FORMS):
            self._assert_usage_error(arguments, "--bogus")
