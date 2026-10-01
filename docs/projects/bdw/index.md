# bdw: the Beads Wrapper

`bdw` is the Wrapper over Beads (`bd`): it runs the real `bd` with the
session's Actor set, so every write Beads records says which session made it.
Beads takes the identity it records from an environment variable, and every
harness Bash call is a fresh shell, so an Actor exported once does not
survive to the next call; `bdw` derives it again on every call. It has its
own name, rather than shadowing `bd` on PATH, so that Permission rules can
grant `bdw` writes literally while raw `bd` writes stay behind a human
prompt. These choices are recorded in the decision to give Beads a
distinctly named identity wrapper that refuses `--actor` (see
[ADR 0002](../../adr/0002-beads-identity.md)).

`bdw` ships in the `bin` Cohort and so is installed machine-wide: it serves
any repo that uses Beads, whether or not that repo has Permission rules for
it. Its lifecycle is independent of this repo's
[Beads trial](../beads-trial/index.md), which is its first consumer.

What one call does:

1. Refuse any argument equal to `--actor` or starting with `--actor=`,
   wherever it appears, including after `--`, because bd's own flag would
   override the environment; exit 4. This is an equality test on each
   argument, not argument parsing.
2. Find the first `bd` on PATH. If there is none, or it resolves (by
   realpath) to `bdw` itself, exit 3; the search does not continue past
   it.
3. Derive the Actor (`cli/lib/actor.py`): `claude-job-<job-id>` from the
   basename of `CLAUDE_JOB_DIR` in a background job, otherwise
   `attended-<user>` from `USER`, or `attended-unknown`. A value counts
   only if it is a token of `[A-Za-z0-9._-]` other than `.` or `..`, so
   the Actor needs no escaping anywhere it is written.
4. Set both `BD_ACTOR` and `BEADS_ACTOR` to the Actor, overriding any
   value the caller supplied, and replace itself (execve) with `bd`,
   arguments untouched. No flag rewriting, no output capture. If the
   exec fails, exit 1; once it succeeds, the exit code is bd's own.

These are bdw's codes under the
[Exit-code contract](../../index.md#exit-code-contract): its own codes
apply only before the exec.

`gitw-commit` derives the same Actor from the same module and writes it as
the `Executed-By:` commit trailer, so a session's Issue Tracker writes and
its commits carry one identity.

## Status

| Capability | State | Where |
|---|---|---|
| Actor derivation on every call, set as `BD_ACTOR` and `BEADS_ACTOR` | shipped | `bdw`; `cli/lib/actor.py` |
| Refusal of bd's `--actor` flag in any position | shipped | `bdw` |
| Pass-through exec of the real `bd`, arguments untouched | shipped | `bdw` |
| Exit codes per the [Exit-code contract](../../index.md#exit-code-contract) (own codes only before the exec) | shipped | `bdw` |

### Known gaps

- Sub-agents of one background job share its job directory, so they record
  one Actor and the trail cannot tell an orchestrator from its implementers
  (Issue to be filed).
