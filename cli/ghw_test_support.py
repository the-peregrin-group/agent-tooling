"""Shared support for the ghw-* wrapper test files.

The wrapper executables have no .py extension, so behavior tests load them
as modules by path. This module holds only maximally-generic scaffolding
shared across the wrapper test files; helpers that aid reading a specific
suite stay local to it (tests are documentation).
"""

from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path


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
