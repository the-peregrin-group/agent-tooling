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
`execve`s the first `bd` on PATH with the arguments untouched. It does no
parsing and captures no output, and `bd`'s exit code is the shim's. When no
`bd` is on PATH, or the only one found is the shim itself, it exits 3 (the
wrappers' not-found code).

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

**Beads hooks stay off, and the trailer moves into `gitw-commit`.** The only
Beads hook worth having is the commit trailer, and a hook that rewrites the
message would compete with `gitw-commit` for ownership of it. So
`gitw-commit` appends `Executed-By: <actor>` itself, from the same
derivation, using `git interpret-trailers --if-exists doNothing`. That leaves
trailer-block placement to git and never adds a second trailer. It writes the
result to a private temporary file, leaves the caller's staged message file
untouched, and reports the actor as `executed_by` in its JSON.

## Consequences

- Agents call `bdw`, never `bd`. Permission rules should allow `bdw` and keep
  bare `bd` behind ask or deny.
- Every `gitw-commit` commit names its session. The trailer is not
  authenticated: a message that already carries `Executed-By:` keeps it
  unchanged (the `doNothing` policy). The trailer is an audit aid, not proof
  of who made the commit.
- If a background job loses `CLAUDE_JOB_DIR`, its actions show up as
  `attended-…`, which is easy to spot in the audit trail.
- Rejected: exporting the actor once per session, since each Bash call is a
  fresh shell. Rejected: a `bd` that shadows the real one, for the PATH-order
  and permission-rule reasons above. Rejected: enabling the Beads hooks, since
  they would fight `gitw-commit` for the commit message.
