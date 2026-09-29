# agent-tooling: agent instructions

Load `use-lexicon` and `use-adrs` for this project.

## Install model

- This checkout is source only. Nothing runs from it.
- Edit here, then install with `tooling-install apply <this-checkout>`. The
  installed copies under `~/.local/libexec/agent-tooling/`, `~/.claude/skills/`,
  and `~/.claude/agents/` are outputs. Never edit them directly: the next install
  overwrites a hot patch, and the Receipt hashes stop matching.
- `tooling-install diff <this-checkout>` is read-only and shows what an install
  would change. Run it before asking the user to approve an `apply` or `adopt`.
- `install.json` declares what ships. A new file under `cli/`, `skills/`, or
  `agents/` ships automatically unless an exclude pattern covers it.

## Invoking the wrappers

The wrappers are invoked by bare name on PATH (`gitw-orient`, `ghw-issue-create`,
`fjw-pr-create`), never by path and never through `python3`. Permission rules
match literal command strings, so the bare name is the one allowlistable form.
The `use-git`, `use-github`, and `use-forgejo` skills are the operating manuals.

## Tests

Run from `cli/` with the system interpreter that some shebangs pin (others
use `/usr/bin/env python3`):

```sh
cd cli && /usr/bin/python3 -m unittest discover -s . -p '*_test.py'
```

Code must stay compatible with Python 3.9 and the standard library only. The
wrappers are invoked from any repo and any session, before any project
environment exists, so they must run under the operating system's own
`/usr/bin/python3` (macOS ships 3.9) with no virtualenv, no pip, and no setup.
On macOS that Apple-signed interpreter is also the one OS-level privacy
permissions (Local Network access, for example) are granted to; a Homebrew or
pyenv interpreter is silently denied them in background sessions. So: stdlib
only, 3.9 syntax, and prefer the system interpreter.

Many tests write their fixtures under `/tmp/claude/`, the staging root the
wrappers accept, creating it if missing; the rest use a temporary directory.
Tests must never read or write the real Install Targets, the real roster, or
the network.

## Issue tracking & workflow

**Trial freeze, from 2026-09-24 until the go/no-go recorded on pinned issue
#18:** work tracking lives in **Beads** (`bd`). The committed `.beads/` files
are config only; the database is local to the maintainer's machine. GitHub
Issues are frozen: the open issues were imported into Beads once, one way,
and no GitHub issue is filed, edited, relabeled, reprioritized, or closed
while the freeze holds. There is no sync in either direction. ADR 0001 has
the reasons.

Agents run Beads through `bdw`, the Beads wrapper in `cli/`, which derives
the session's actor from its environment, refuses bd's own `--actor` flag,
and otherwise execs `bd` with the arguments untouched. Reads may use either
name. Writes go through `bdw`; a raw `bd` write prompts by design. Put the
verb first and global flags such as `--json` after it: the permission rules
deny flag-first spellings whose arguments happen to contain a denied word.

The loop, every session:

1. `bdw prime` at session start.
2. `bdw ready` to find work, `bdw show <id>` to read it.
3. `bdw update <id> --claim` before touching code.
4. `bdw create --deps=discovered-from:<id> ...` for anything found along the
   way.
5. `bdw close <id>` when done.
6. Land the plane: close or unclaim everything you hold before the session
   ends.

- Imported issues carry the GitHub issue URL as their external reference. A
  `TODO` comment cites the Issue ID (`TODO(agent-tooling-xyz)`), not `#N`.
- Which subcommands may run is set by the permission rules in
  `.claude/settings.json` (allow, ask, deny), not judgment;
  `cli/repo_policy_test.py` is that file's spec. A denied call is the policy
  working; do not look for another spelling of it. The policy is prefix
  rules, so it is not safe in auto mode until the parsed-command deny hook
  lands.
- Ignore `bd prime` where it contradicts Claude Code or `use-git`: memory
  stays in Claude Code's memory files, and feature branches are pushed and
  reviewed as usual.

Pull requests are unaffected. **Load the `use-github` skill before opening a
PR**; its issue-filing and board conventions are suspended for the trial, and a
PR body names the issue it lands (`Lands agent-tooling-xyz`) instead of
`Closes #N`.

## Documentation

- `README.md` is the front door and the fresh-machine bootstrap.
- `docs/beads-init.md` is the maintainer's checklist for initializing Beads
  in another repo.
