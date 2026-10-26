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
     push sends every unpushed commit;
   - after any other call, a read included, start a worker when a push is
     still owed (a write marker is left, as a killed worker leaves one)
     and no worker is running. Nothing is created when nothing is owed.

   If a push cannot be requested or restarted (its state directory or
   marker cannot be written, its lock cannot be taken, or the worker
   cannot start), `bdw` prints one warning line saying so.

   Nothing in this step, an exception included, changes `bdw`'s exit
   code. The push (`cli/lib/bdw_push.py`) runs as a detached background
   process under `/usr/bin/python3`, the interpreter macOS grants Local
   Network access to, whatever interpreter `bdw` itself ran under. It is
   coalesced: a write leaves the marker `pending` and starts a worker
   unless one already holds the lock; one worker at a time holds the lock
   and pushes until no marker is left, so writes landing during a push
   get exactly one more. A pass takes the write by renaming `pending` to
   `pushing`, and deletes `pushing` only once the push's outcome is
   recorded (pushed, nothing to push, opted out, or a failure written); a
   worker treats a leftover `pushing` as work. A worker asks bd for
   `no-push` once per run. Each push:
   - reads the Dolt remotes from the embedded database's
     `repo_state.json` (named through `metadata.json`), and does nothing
     when there are none or the database is not in embedded mode; when
     that state cannot be read, it records a failure. That file is
     Dolt's own, not a bd interface, so a bd upgrade re-checks it with the
     rest of the verified behavior;
   - skips when bd's effective `no-push` is set, clearing any recorded
     failure so the warning above stops;
   - refuses, and records a failure, unless every Dolt remote's host is
     on the push-host allowlist (below). This fails closed: no allowlist,
     an unreadable or malformed one, a remote whose URL has no readable
     host, or a host not listed all refuse;
   - also refuses, and records a failure, when any Dolt remote names the
     same repository as any git remote of the workspace, comparing host
     and path with scheme, user, port, `.git`, and case dropped. The
     allowlist cannot catch this when the code's host is itself allowed
     (a private Dolt repository beside the public code on one forge), and
     a Dolt remote on the code's own repository is what `bd init` sets up
     by default;
   - runs `bd dolt push --no-adopt` with `BD_NO_REMOTE_ADOPT=1`, because
     bd 1.3.0 otherwise offers to adopt a remote derived from the git
     origin. bd runs in its own process group, killed whole on a timeout;
     its output goes to files, so a detached descendant holding it cannot
     stretch that timeout.

   Two locks keep pushes apart. The coordination lock means a worker is
   running; only the worker holds it, so a killed worker frees it at once
   and the next `bdw` call starts a new one. The push-in-flight lock means a
   `bd dolt push` may still be running: the worker takes it, waiting up
   to the push timeout, before each pass, holds it for the whole pass,
   and hands it to `bd dolt push` alone, whose descendants inherit it. A
   push left running by a killed worker, or a descendant that outlives bd
   (git's detached gc, a credential daemon), therefore makes the next
   pass wait instead of running beside it.

   What this guarantees: once a write's marker exists, its push either
   completes or leaves a recorded failure, which the warning above then
   names, as long as `bdw` is called again in this workspace with a state
   root and the push turned on. In particular:
   - A worker killed while it waits for the push-in-flight lock, or one
     that fails before taking the write, leaves `pending`.
   - A worker killed mid-push leaves `pushing`. The next `bdw` call starts
     a worker, which waits for the orphaned `bd dolt push` and then
     pushes again, recording the outcome.
   - If the push-in-flight lock is still held when the wait runs out,
     the pass records a failure naming the lock's path, keeps the marker,
     and the worker stops; the next call tries again.
   - Any other error inside a pass is recorded as a failure.

   What it does not: with no later `bdw` call, nothing retries; an
   orphaned push that fails is not itself recorded, only the push that
   follows it; and a `bd dolt push` that survives `SIGKILL` for 10
   seconds is left running, held off only by the push-in-flight lock.

   Its state is Machine State, in `push/<key>/` under `bdw`'s
   subdirectory of the Machine State Directory
   (`${XDG_STATE_HOME:-~/.local/state}/agent-tooling/bdw/push/<key>/`,
   resolved through `cli/lib/paths.py`; see the
   [Path layout](../../index.md#path-layout)). `<key>` is a hash of the
   Beads directory, so each database has its own. Missing directories are
   created with mode `0700`; one that already exists keeps its mode. It
   holds the two locks, the markers `pending` and `pushing`,
   `last-failure.json` while the
   last push failed (replaced atomically), and `push.log`. When no state
   root resolves (no usable `XDG_STATE_HOME` or `HOME`), nothing is
   pushed.

### The push-host allowlist

`bdw` pushes only to hosts its maintainer has listed (why, and the
alternatives rejected:
[ADR 0016](../../adr/0016-bdw-pushes-only-to-allowlisted-hosts.md), bdw
pushes only to hosts on a fail-closed allowlist). The list is
Machine Config, `config.toml` in `bdw`'s subdirectory of the Machine
Config Directory: `~/.config/agent-tooling/bdw/config.toml` by default,
or under `$XDG_CONFIG_HOME` (resolved through `cli/lib/paths.py`; see the
[Path layout](../../index.md#path-layout)). It holds one key:

```toml
# Hosts that may hold this machine's Beads data.
push_hosts = ["git.example.org"]
```

- **The format** is a subset of TOML that `cli/lib/bdw_push.py` parses
  itself, since the system Python 3.9 has no `tomllib`: the one key
  `push_hosts`, an array of quoted host names on one line or several (a
  trailing comma is fine), and `#` comments. Anything else in the file
  makes it malformed. It is valid TOML, so a later `tomllib` reads it
  unchanged.
- **An entry is a host**, compared without case: no scheme, user, port,
  or path. The list answers which machine may hold the Issue data, and one
  server answers on several ports (ssh on 22 or another, https on 443),
  so listing ports would break the list on a change of transport without
  keeping anything out.
- **It fails closed.** No file, an unreadable or malformed one, an empty
  list, a Dolt remote whose URL has no host (a file path), or any Dolt
  remote whose host is not listed refuses the push. The refusal is
  recorded and warned about like a failed push (the worker exits 4), and
  the message names the file and the key to write, never a remote's URL
  or host; `bd dolt remote list` shows the remotes.
- **Writing it is a person's act**, once per machine, after the Dolt
  remote is added (use-bd's onboarding checklist has the order).

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
| Coalesced background push to the Dolt remote after writes, restarted by any later call when owed, with the failure warning | shipped | `bdw`; `cli/lib/bdw_push.py` |
| Fail-closed push-host allowlist in the Machine Config Directory, plus refusal of a Dolt remote on the code's own repository | shipped | `cli/lib/bdw_push.py`; [the push-host allowlist](#the-push-host-allowlist) |

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
