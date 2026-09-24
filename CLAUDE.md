# agent-tooling: agent instructions

## Install model

- This checkout is source only. Nothing runs from it.
- Edit here, then install with `tooling-install apply <this-checkout>`. The
  installed copies under `~/.local/libexec/agent-tooling/`, `~/.claude/skills/`,
  and `~/.claude/agents/` are outputs. Never edit them directly: the next install
  overwrites a hot patch, and the receipt hashes stop matching.
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
Tests must never read or write the real install targets, the real roster, or
the network.

## Issue tracking & workflow

**Trial freeze, from 2026-09-24:** work tracking lives in **Beads** (`bd`,
embedded Dolt under `.beads/`, local to this machine) for the duration of the
Beads trial. GitHub Issues are frozen: the open issues were imported into
Beads once, one way, and no GitHub issue is filed, edited, relabeled,
reprioritized, or closed while the freeze holds. There is no sync in either
direction. Pinned issue #18 says the same for humans.

- Loop: `bd prime` at session start, `bd ready` to find work, `bd update <id>
  --claim` before touching code, `bd create --deps=discovered-from:<id>` for
  anything you find along the way, `bd close <id>` when done, and close or
  unclaim everything you hold before the session ends.
- Imported beads carry the GitHub issue URL as their external reference; a
  `TODO` comment cites the bead ID (`TODO(agent-tooling-xyz)`), not `#N`.
- Which `bd` subcommands an agent may run is policy in `.claude/settings.json`
  (allow, ask, deny), not judgment. A denied call is the policy working; do
  not look for another spelling of it.
- Ignore `bd prime` where it contradicts the harness or `use-git`: memory
  stays in the harness's memory files, and feature branches are pushed and
  reviewed as usual.

Pull requests are unaffected. **Load the `use-github` skill before opening a
PR**; its issue-filing and board conventions are suspended for the trial, and a
PR body names the bead it lands (`Lands agent-tooling-xyz`) instead of
`Closes #N`.

## Documentation

- `README.md` is the front door and the fresh-machine bootstrap.
- `CONTEXT.md` is the vocabulary. Use its terms.
- Design decisions are ADRs in `docs/adr/`, numbered from 0001, indexed in
  `docs/adr/index.md`, which describes the format.
