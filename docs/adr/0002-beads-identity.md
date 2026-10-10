---
date: 2026-09-24
status: amended
---

# Beads identity: the bdw wrapper and the Executed-By trailer

**Context:** Beads takes the identity it records from an environment variable, and each harness Bash call is a fresh shell, so an actor exported once does not survive to the next call. `gitw-commit` owns the commit message, so Beads' own trailer hook cannot be used (ADR 0001 rejects the Beads hooks).
**Decision:** A `bdw` wrapper derives the actor on every call, sets `BD_ACTOR` and `BEADS_ACTOR` to it (overriding the caller), refuses bd's `--actor` flag, and otherwise execs `bd` untouched; `gitw-commit` writes the same actor as an `Executed-By:` trailer, replacing a caller-written one and refusing a message that carries more than one.
**Rationale:** Identity must come from the harness environment on every invocation, and `bdw` as a distinct name keeps permission rules literal and keeps the identity path independent of PATH order.

**Gotchas:**

- The trailer is an audit aid, not proof. It is only as reliable as the environment it was derived from, and a commit made outside `gitw-commit` can carry any trailer.
- A background job that loses `CLAUDE_JOB_DIR` shows up as `attended-…`, not as a job. That is by design: the fallback shape is deliberately distinct from the job shape.
- `BEADS_ACTOR` is set alongside `BD_ACTOR` because Beads 1.3.0 honours `BD_ACTOR` (issues show it in `created_by`) while its help names only `BEADS_ACTOR`.
- The token charset `[A-Za-z0-9._-]` (checked as a full match, not `.` or `..`) is what makes the actor safe to put in an env var and in a trailer without escaping.
- `bdw` exits 3 when no `bd` is on PATH, or when the first one on PATH resolves to `bdw` itself; the search does not continue past it. That check compares realpaths, so a byte copy of `bdw` installed as `bd` is not caught.
- git's `--if-exists replace` removes only one existing trailer, so `gitw-commit` refuses a message carrying several `Executed-By:` trailers rather than leave a caller value beside the derived one. It copies the message, with a final newline added, to a private file before adding the trailer, because `interpret-trailers` glues a trailer onto an unterminated last line.
- The `--actor` guard is an equality test on each argument (`--actor`, or anything beginning `--actor=`), not argument parsing, and it applies after `--` as well. The command policy of ADR 0001 also denies the flag. Both exist on purpose: `bdw` installs machine-wide and runs in repos with no command policy, and the policy covers bare `bd`.

## Alternatives Considered

### A `bd` earlier on PATH

**Description:** Name the wrapper `bd` and put it ahead of the real binary on PATH.
**Rejection rationale:** Permission rules match literal command strings, so one name for two binaries makes them ambiguous. A session whose PATH puts the real `bd` first would also skip the identity path silently.

### Export the actor once per session

**Description:** Set `BD_ACTOR` once at session start and call `bd` directly.
**Rejection rationale:** Each harness Bash call is a fresh shell, so the export does not survive to the next call.

## Amended by

- [ADR 0010](0010-bdw-carries-beads-policy-in-tiers.md): `bdw` no longer always execs `bd` with arguments untouched; it intercepts, or replaces with its own Verbs, the operations that carry policy.
