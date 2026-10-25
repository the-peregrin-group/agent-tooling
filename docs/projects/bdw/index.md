# bdw: the Beads Wrapper

## Overview

`bdw` is the Wrapper over Beads (`bd`): it runs the real `bd` with the
session's Actor set, so every write Beads records says which session made it.
Beads takes the identity it records from an environment variable, and every
harness Bash call is a fresh shell, so an Actor exported once does not
survive to the next call; `bdw` derives it again on every call. It has its
own name, rather than shadowing `bd` on PATH, so that Permission rules can
grant `bdw` literally while denying raw `bd` (in this repo, outright).
These choices are recorded in the decision to give Beads a
distinctly named identity wrapper that refuses `--actor` (see
[ADR 0002](../../adr/0002-beads-identity.md)).

`bdw` ships in the `bin` Cohort and so is installed machine-wide: it serves
any repo that uses Beads, whether or not that repo has Permission rules for
it. Its lifecycle is independent of this repo's
[Beads trial](../beads-trial/index.md), which is its first consumer.

`bdw` also carries the Beads policy that Permission rules cannot express,
in the lightest tier that suffices (see
[ADR 0010](../../adr/0010-bdw-carries-beads-policy-in-tiers.md), bdw
carries Beads policy in tiers). Today that is tiers one and two only:
pass-through with a few thin intercepts, and no Verbs of its own. Every
argument check is an equality test on whole arguments, not parsing of
bd's grammar.

What one call does:

1. Refuse, with exit 4:
   - any argument equal to `--actor` or starting with `--actor=`, wherever
     it appears, including after `--`, because bd's own flag would
     override the environment;
   - any argument naming a global flag that points bd at another
     database: `--directory`, `--db`, `--database`, `--global`, bare or
     with `=`, and `-C` inside any single-dash cluster (`-C`, `-Cdir`,
     `-qC`), wherever it appears. A single-dash argument such as a value
     `-Coffee` is refused too: fail closed; the long `--flag=value` form
     gets past it;
   - a first argument that is a flag, other than `help`, `--help`, `-h`,
     `version`, `--version`, `-V`: the verb comes first.
2. Find the first `bd` on PATH. If there is none, or it resolves (by
   realpath) to `bdw` itself, exit 3; the search does not continue past
   it.
3. Unless the call is a help call (no arguments, or a first argument of
   `help`, `--help`, or `-h`) or a version call, probe bd twice, each a
   child run with its output captured:
   - `bd where --json` must name a Beads directory holding
     `metadata.json`; otherwise exit 5. bd 1.3.0 falls back silently to an
     empty database when that file is missing, so this refusal keeps
     writes from going to the wrong database. bd's own discovery
     (worktrees, redirects, and a caller-set `BEADS_DIR`) decides which
     directory counts; see Known gaps.
   - `bd version --json` must name a version in `VERIFIED_BD_VERSIONS`
     (`1.3.0` today). On any other version, or one it cannot read, a
     write exits 5 and a read runs after a warning on stderr. A read is
     one of the verbs `blocked`, `children`, `context`, `count`, `diff`,
     `find-duplicates`, `graph`, `history`, `info`, `lint`, `list`,
     `prime`, `query`, `ready`, `schema`, `search`, `show`, `stale`,
     `status`, `statuses`, `types`, `where`, or one of the subcommands
     `config get|list|show`, `dep list|tree`, `epic status`,
     `gate list|show`, `human list`, `label list|list-all`, whose every
     argument starting with `-` is one of the flags the use-bd Skill
     teaches for reads: `--all`, `--children`, `--desc-contains`,
     `--eligible-only`, `--json`, `--limit` (bare or with `=`). Everything
     else counts as a write, `ready --claim` included, so a flag a newer
     bd adds to a read verb cannot write unchecked.
4. Derive the Actor (`cli/lib/actor.py`), taking the first shape that
   applies: `claude-job-<session-id>` in a background job and
   `claude-session-<session-id>` in an attended session, from the
   harness's `CLAUDE_CODE_SESSION_ID`; without a usable session ID,
   `claude-job-<job-id>` from the basename of `CLAUDE_JOB_DIR`, then
   `attended-<user>` from `USER`, then `attended-unknown`. A job's ID is
   a prefix of its session ID, so the job shape keeps Actors derived from
   the job ID alone as literal prefixes. A value counts only if it is a
   token of `[A-Za-z0-9._-]` other than `.` or `..`, so the Actor needs no
   escaping anywhere it is written.
5. Run `bd` as a child process with both `BD_ACTOR` and `BEADS_ACTOR` set
   to the Actor and `CLAUDE_SESSION_ID`, the variable bd 1.3.0 reads to
   record the session that closed an Issue (named in `bd help close`),
   set to the session ID, or removed when there is none. All three
   override whatever the caller supplied. Arguments pass unchanged; stdin
   and stdout are bd's own, and bd's stderr is relayed line by line as it
   arrives, so `bdw` can read it. If `bdw`'s own stderr closes (a caller
   that stops reading it), `bdw` keeps draining bd's and still returns
   bd's exit code. `SIGTERM`, `SIGHUP`, and `SIGQUIT`
   sent to `bdw` are forwarded to bd, and `bdw` keeps waiting for bd to
   exit; `SIGINT` is not forwarded, since a terminal delivers it to bd as
   well. If bd cannot be started, exit 1; otherwise the exit code is bd's
   own (128 + N when signal N ends it).
6. Print `Agents, load /use-bd immediately.` on stderr after a help call,
   after any call whose arguments before a `--` include `--help` or `-h`,
   after bd reports a usage error (a stderr line starting with cobra's
   usage-error messages, such as `Error: unknown command`,
   `Error: unknown flag:`, or `Run 'bd --help' for usage.`), and after
   every failure of its own (exits 1, 3, 4, and 5).

These are bdw's codes under the
[Exit-code contract](../../index.md#exit-code-contract): its own codes
are 1, 3, 4, and 5; any other code is bd's. The argument refusals in
step 1 exit 4, a caller bug to fix in the call. The step 3 refusals
exit 5, a configuration problem: a missing workspace config or an
unverified bd version cannot be fixed by changing the call, so the
caller stops and flags the deployment.

`gitw-commit` derives the same Actor from the same module and writes it as
the `Executed-By:` commit trailer, so a session's Issue Tracker writes and
its commits carry one identity.

## Status

| Capability | State | Where |
|---|---|---|
| Actor derivation on every call from the harness's session ID, set as `BD_ACTOR` and `BEADS_ACTOR`, and the session ID set as `CLAUDE_SESSION_ID` | shipped | `bdw`; `cli/lib/actor.py` |
| Refusal of bd's `--actor` flag in any position | shipped | `bdw` |
| Refusal of the database-switching flags in any position, and of a flag before the verb | shipped | `bdw` |
| Refusal to run without the workspace's Beads config | shipped | `bdw` |
| Verified bd versions: writes refused and reads warned on any other version | shipped | `bdw` |
| `bd` run as a child process, arguments unchanged, output, exit status, and termination signals relayed | shipped | `bdw` |
| The use-bd help line on every help output, usage error, and refusal | shipped | `bdw` |
| Exit codes per the [Exit-code contract](../../index.md#exit-code-contract) | shipped | `bdw` |

### Known gaps

- A caller-set `BEADS_DIR` still moves bd to another database, which the
  refused database-switching flags cannot (`agent-tooling-24u`).

- Sub-agents share their session's environment, session ID included, so
  they record one Actor and the trail cannot tell an orchestrator from its
  implementers (`agent-tooling-jk2`).
