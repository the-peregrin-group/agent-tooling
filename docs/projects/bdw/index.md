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

1. Refuse:
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
   realpath) to `bdw` itself, exit 1; the search does not continue past
   it.
3. Unless the call is a help call (no arguments, or a first argument of
   `help`, `--help`, or `-h`) or a version call, probe bd twice, each a
   child run with its output captured:
   - `bd where --json` must name a Beads directory holding
     `metadata.json`; otherwise exit 1. bd 1.3.0 falls back silently to an
     empty database when that file is missing, so this refusal keeps
     writes from going to the wrong database. bd's own discovery
     (worktrees, redirects, and a caller-set `BEADS_DIR`) decides which
     directory counts; see Known gaps.
   - `bd version --json` must name a version in `VERIFIED_BD_VERSIONS`
     (`1.3.0` today). On any other version, or one it cannot read, a
     write is refused and a read runs after a warning on stderr. A read is
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
   that stops reading it), `bdw` keeps draining bd's and still waits for
   bd's exit. `SIGTERM`, `SIGHUP`, and `SIGQUIT`
   sent to `bdw` are forwarded to bd, and `bdw` keeps waiting for bd to
   exit; `SIGINT` is not forwarded, since a terminal delivers it to bd as
   well. If bd cannot be started, exit 1; otherwise bd's exit is
   translated into the contract (below).
6. Print `Agents, load /use-bd immediately.` on stderr after a help call,
   after any call whose arguments before a `--` include `--help` or `-h`,
   after bd reports a usage error (a stderr line starting with cobra's
   usage-error messages, such as `Error: unknown command`,
   `Error: unknown flag:`, or `Run 'bd --help' for usage.`), and after
   every failure of its own.
7. Push the database to its Dolt remote (see
   [ADR 0014](../../adr/0014-bdw-pushes-the-beads-database-after-writes.md),
   bdw pushes the Beads database after every write). After any call that
   probed the workspace in step 3, unless the push is turned off.
   `BD_NO_PUSH`, or bd's `no-push` config (which bd also maps from
   `BD_NO_PUSH`), turns it off when its value is one of `1`, `t`,
   `true`, `yes`, or `on`, in any case. `bdw` is what pushes, so this
   set, not bd's own parsing, decides:
   - while the last push failed, print one warning line on stderr naming
     the failure's time and reason and the push log, never the remote's
     address;
   - when bd exited 0 and the call is not a read, request a push and
     return at once. For this step a read is any call to a verb or
     subcommand in the read tables of step 3, whatever its flags; `dolt`
     and `backup` calls never push either. A write this misses (a read
     verb with a writing flag) is pushed by the next write, since a Dolt
     push sends every unpushed commit. If the push cannot be requested
     (its state directory or mark cannot be written, its lock cannot be
     taken, or the worker cannot start), print one warning line saying
     so.

   Nothing in this step, an exception included, changes `bdw`'s exit
   code. The push (`cli/lib/bdw_push.py`) runs as a detached background
   process under `/usr/bin/python3`, the interpreter macOS grants Local
   Network access to, whatever interpreter `bdw` itself ran under. It is
   coalesced: `bdw` leaves a dirty mark and starts a worker unless one
   already holds the lock; one worker at a time holds the lock and pushes
   until the mark stays clear, so writes landing during a push get exactly
   one more. A worker asks bd for `no-push` once per run. Each push:
   - reads the Dolt remotes from the embedded database's
     `repo_state.json` (named through `metadata.json`), and does nothing
     when there are none or the database is not in embedded mode; when
     that state cannot be read, it records a failure. That file is
     Dolt's own, not a bd interface, so a bd upgrade re-checks it with the
     rest of the verified behavior;
   - skips when bd's effective `no-push` is set, clearing any recorded
     failure so the warning above stops;
   - refuses, and records a failure, when any Dolt remote names the same
     repository as any git remote of the workspace, comparing host and
     path with scheme, user, port, `.git`, and case dropped, so the Issue
     data never goes where the public code goes;
   - runs `bd dolt push --no-adopt` with `BD_NO_REMOTE_ADOPT=1`, because
     bd 1.3.0 otherwise offers to adopt a remote derived from the git
     origin. bd runs in its own process group, killed whole on a timeout;
     its output goes to files, so a detached descendant holding it cannot
     stretch that timeout.

   Two locks keep pushes apart. The coordination lock means a worker is
   running; only the worker holds it, so a killed worker frees it at once
   and the next write starts a new one. The push-in-flight lock means a
   push's commands may still be running: the worker takes it before a
   push's first command and hands it to each of them, and bd's
   descendants inherit it. A push left running by a killed worker, or a
   descendant that outlives bd (git's detached gc, a credential daemon),
   therefore makes the next push wait, up to the push timeout, instead of
   running beside it; past that wait the push records a failure, so the
   warning above names it rather than the write going silently unpushed.

   Its state lives outside the repo, in
   `$XDG_STATE_HOME/agent-tooling/bdw-push/<key>/` (`XDG_STATE_HOME`
   defaulting to `~/.local/state`, `<key>` a hash of the Beads
   directory, kept at mode `0700`): the two locks, the dirty mark,
   `last-failure.json` while the last push failed (replaced atomically),
   and `push.log`. With neither `XDG_STATE_HOME` nor `HOME` set, nothing
   is pushed.

`bdw` follows the [Exit-code contract](../../index.md#exit-code-contract)
(why: [ADR 0013 (one exit-code contract for all agent-tooling software)](../../adr/0013-one-exit-code-contract-for-all-agent-tooling.md)).
bd's own exit code never reaches the caller: `bdw` translates it, and a
bd that succeeds exits 0. A signal that ends bd passes through as
128 + N, which is outside the contract. In step 1, the forbidden flags
(`--actor` and the database-switching flags) are 4, and a flag before
the verb is a malformed call, 2. A missing `bd` and a missing workspace
config are 1. How bd's failures and a write on an unverified bd version
classify is settled by `agent-tooling-cjvo.4`, and `bdw` does not exit
this way yet; see Known gaps.

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
| `bd` run as a child process, arguments unchanged, output and termination signals relayed | shipped | `bdw` |
| The use-bd help line on every help output, usage error, and refusal | shipped | `bdw` |
| Exit codes per the [Exit-code contract](../../index.md#exit-code-contract) | shipped | `bdw` |
| Coalesced background push to the Dolt remote after writes, with the destination guard and the failure warning | shipped | `bdw`; `cli/lib/bdw_push.py` |

### Known gaps

- A caller-set `BEADS_DIR` still moves bd to another database, which the
  refused database-switching flags cannot (`agent-tooling-24u`).

- Sub-agents share their session's environment, session ID included, so
  they record one Actor and the trail cannot tell an orchestrator from its
  implementers (`agent-tooling-jk2`).

- `bdw` still passes bd's exit code through and exits its own codes in
  the earlier seven-code taxonomy, not the six-code Exit-code contract
  (`agent-tooling-cjvo.4`).

- A push started from a background session on macOS has not yet been
  verified against a remote on the local network (`agent-tooling-cy3`).
