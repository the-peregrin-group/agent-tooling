"""Output and exit-code conventions shared by every wrapper.

Exit codes follow the Exit-code contract in docs/index.md#exit-code-contract
(ADR 0013); that section is the source of truth for what each code means and
how the boundaries between them fall. The constants below name its six codes.

Families migrate to the contract one at a time (the agent-tooling-cjvo epic).
Until a family has migrated it keeps exiting with the earlier seven-code
taxonomy through the transitional constants, whose values are unchanged.

Write wrappers emit a JSON plan to stdout with "action": "plan" |
"applied" | "conflict" -- the last for a write that stopped partway
leaving deliberate resumable state (a gitw-rebase conflict stop), so
every Wrapper shares one discriminator vocabulary.
"""

from __future__ import annotations

import json
import sys
from typing import NoReturn

# The six-code Exit-code contract (docs/index.md#exit-code-contract).
EXIT_OK = 0  # done
EXIT_BROKEN = 1  # broken on our side, not the caller's fault
EXIT_CALLER_ERROR = 2  # the caller must change the call, or the state it acts on
EXIT_NOT_FOUND = 3  # the named resource does not exist
EXIT_FORBIDDEN = 4  # policy forbids this caller this action
EXIT_PARTIAL_COMPLETION = 5  # partial completion, with caller work to do

# Transitional: the earlier seven-code taxonomy, still exited by families
# that have not migrated. Values are unchanged so those families exit as
# before. Each comment names the contract code the old meaning maps to; a
# family's migration reclassifies each exit path rather than renaming
# blindly. The epic's final pass removes these names.
EXIT_RUNTIME = 1  # unclassified failure -> EXIT_BROKEN (1)
EXIT_USAGE = 2  # usage error -> EXIT_CALLER_ERROR (2)
EXIT_REFUSED = 4  # refusal -> EXIT_FORBIDDEN (4) if authorization, else EXIT_CALLER_ERROR (2)
EXIT_AUTH = 5  # roster/auth/config -> EXIT_BROKEN (1); 5 now means EXIT_PARTIAL_COMPLETION
EXIT_NETWORK = 6  # network failure -> EXIT_BROKEN (1); the contract has no 6


def emit(payload: dict) -> None:
    """Pretty-print `payload` as JSON on stdout, trailing newline included."""
    json.dump(payload, sys.stdout, indent=2)
    print()


def emit_plan(action: str, **payload) -> None:
    """Emit a write-wrapper plan: `action` must be "plan", "applied", or
    "conflict" (stopped partway, resumable state left in place). Raises
    ValueError otherwise."""
    if action not in ("plan", "applied", "conflict"):
        raise ValueError(
            f"plan action must be 'plan', 'applied', or 'conflict', got {action!r}"
        )
    emit({"action": action, **payload})


def usage_die(message: str, usage: str) -> NoReturn:
    """Refuse with exit 2, printing the mistake and the correct usage.

    Rigid positional signatures mean mistakes fail at the wrapper, so this
    message must let an agent self-correct in one round-trip.
    """
    print(f"error: {message}\nusage: {usage}", file=sys.stderr)
    sys.exit(EXIT_CALLER_ERROR)
