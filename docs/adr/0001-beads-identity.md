# 0001. Beads identity: the bdw shim and the Executed-By trailer

Status: accepted, 2026-09-24.

## Context

This repo is trialling Beads (`bd`) as its tracker. Beads takes the identity it
records for an action from an environment variable. Agents here run as harness sessions: attended, or
background jobs that the harness identifies by setting `CLAUDE_JOB_DIR` to
`~/.claude/jobs/<job-id>`. Every harness Bash call starts a fresh shell, so an
identity exported once doesn't reach the next call, and an agent asked to
prefix every `bd` call with the variable will sooner or later forget.

We also want commits to say which session made them. Beads ships git hooks
that would add a trailer. But `gitw-commit` owns the commit message outright:
the message comes from a staged file and the wrapper performs the commit.

## Decision

**A shim, `bdw`, derives the actor on every call.** `cli/bdw` computes the
actor from its own environment, sets it in the child environment, and
`execve`s the first `bd` on PATH. Apart from the `--actor` refusal below, it
passes the arguments through untouched. It captures no output, and `bd`'s
exit code is the shim's. When no `bd` is on PATH, or the only one found is the
shim itself, it exits 3 (the wrappers' not-found code).

**The shim is `bdw`, not a `bd` placed earlier on PATH.** Permission rules
match literal command strings, so `bdw ...` and `bd ...` are two distinct,
unambiguous things to allow, ask about, or deny. A shadowing `bd` would make
the identity path depend on PATH order: a shell or a session whose PATH puts
the real `bd` first would silently skip the shim, and the audit trail would
show nothing wrong.

**Two actor shapes, from `lib/actor.py`.** `claude-job-<job-id>` when
`CLAUDE_JOB_DIR` has a usable basename, since the harness sets it for
background jobs and the job ID is the session's identity. Otherwise
`attended-<USER>`, or `attended-unknown`. The fallback is a different shape
on purpose: a job whose job directory went missing shows up as `attended-…`
in the audit trail instead of looking like a job. Both parts are limited to
`[A-Za-z0-9._-]`, so the actor fits in an env var or a git trailer without
escaping.

**The shim sets `BD_ACTOR` and `BEADS_ACTOR`, overriding the caller.** Identity
comes from the harness environment, not from whoever invokes the shim, so a
caller-supplied value of either variable is replaced. Beads 1.3.0 honours
`BD_ACTOR`: issues created under it show it in `created_by`. Its help text
names only `BEADS_ACTOR`. Setting both covers either reading.

`bd`'s own `--actor` flag takes precedence over both variables, so two
separate guards close that route:

- **The shim refuses `--actor`.** Any argument equal to `--actor`, or starting
  with `--actor=`, in any position (including after `--`, since `bd` still
  sees it there), gets exit 4 before the exec. This is an equality test on
  each argument, not argument parsing, and every other argument still passes
  through untouched. The shim needs its own guard because it installs
  machine-wide and will run in repos that have no command policy yet.
- **The repo command policy in `.claude/settings.json`, added by PR #19, also
  denies the flag in any position.**

Both guards exist on purpose, and neither is enough alone.

**Beads hooks stay off, and the trailer moves into `gitw-commit`.** The only
Beads hook worth having is the commit trailer, and a hook that rewrites the
message would compete with `gitw-commit` for ownership of it. So
`gitw-commit` appends `Executed-By: <actor>` itself, from the same
derivation, using `git interpret-trailers --if-exists replace`. That leaves
trailer-block placement to git. It also applies the shim's override rule
(identity comes from the environment, not the caller): a caller-written
`Executed-By:` trailer is replaced by the derived actor. git's `replace`
deletes only one existing trailer, so a message carrying several is refused
(exit 4) rather than committed with a caller value beside the derived one.
Every commit ends up with exactly one `Executed-By:` trailer. The wrapper
copies the message to a private temporary file, adding a final newline if
it lacks one, because `interpret-trailers` would otherwise glue the trailer
onto the last line. It adds the trailer to that copy and commits from it,
so the caller's staged message file is never modified. The JSON output
reports the actor as `executed_by`.

## Consequences

- Agents call `bdw` for anything that writes. The permission policy treats
  the two names differently by verb class:
  - reads are allowed on either name;
  - reversible writes are allowed on `bdw` and asked for on bare `bd`;
  - destructive and outward verbs are denied on every name.

  `.claude/settings.json` and `cli/repo_policy_test.py` hold the rules; this
  ADR does not repeat them.
- Every `gitw-commit` commit names its session, and a caller can't set that
  name through the message: a caller's `Executed-By:` is replaced, and several
  are refused. The trailer is still not authenticated. It is only as reliable
  as the environment it was derived from, and a commit made outside
  `gitw-commit` can carry any trailer. So it is an audit aid, not proof of
  who made the commit.
- If a background job loses `CLAUDE_JOB_DIR`, its actions show up as
  `attended-…`, which is easy to spot in the audit trail.
- Rejected: exporting the actor once per session, since each Bash call is a
  fresh shell. Rejected: a `bd` that shadows the real one, for the PATH-order
  and permission-rule reasons above. Rejected: enabling the Beads hooks, since
  they would fight `gitw-commit` for the commit message.
