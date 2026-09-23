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

This project uses this repository's **GitHub Issues** as the single source of
truth for work tracking. Priority lives on the repository's linked project
board, not on labels; `ghw-orient` reports the board and its fields.

**Load the `use-github` skill before filing, labeling, or prioritizing an
issue, before writing a `TODO` comment, and before opening a PR.** It carries
the label schema, the board fields, the `TODO(#N)` rule, and the branch/PR
workflow. Don't improvise these conventions.

## Documentation

- `README.md` is the front door and the fresh-machine bootstrap.
- `CONTEXT.md` is the vocabulary. Use its terms.
- Design decisions are ADRs in `docs/adr/`, numbered from 0001, indexed in
  `docs/adr/index.md`, which describes the format.
