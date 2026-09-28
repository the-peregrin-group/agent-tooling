"""Output and exit-code conventions shared by every wrapper.

Exit codes (shared taxonomy; codes 3-6 were carved out of 1's space when the
fjw verbs arrived, so pre-existing callers stay correct):
    0 -- success, including a converged no-op
    1 -- unclassified runtime failure (or, historically, any `gh` failure)
    2 -- usage error or policy refusal at argument-parse time
    3 -- not found (unattended callers treat this as an answer, not an error)
    4 -- validation/policy refusal past parse time -- a caller bug, never retry
    5 -- auth failure (unattended callers abort and flag deployment)
    6 -- network failure (the one retryable class)

Every fjw verb classifies from day one; ghw verbs still collapse 3-6 into 1
and migrate opportunistically.

Write wrappers emit a JSON plan to stdout with "action": "plan" |
"applied" | "conflict" -- the last for a write that stopped partway
leaving deliberate resumable state (a gitw-rebase conflict stop), so
every Wrapper shares one discriminator vocabulary.
"""

from __future__ import annotations

import json
import sys
from typing import NoReturn

EXIT_OK = 0
EXIT_RUNTIME = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_REFUSED = 4
EXIT_AUTH = 5
EXIT_NETWORK = 6


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
    sys.exit(EXIT_USAGE)
