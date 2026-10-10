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

**Load the `use-bd` skill at session start**: it is the operating manual for
Beads through `bdw`. This repo's Beads conventions (labels, the friction
log, `TODO` citations) are in `.beads/PRIME.md`, which `bdw prime` prints.

The Beads Permission rules in `.claude/settings.json` are generated from
their spec, `cli/repo_policy_test.py`: change the spec, regenerate the
file, and let the test confirm they agree. The rules are prefix rules, so
they are not safe in auto mode until the parsed-command deny hook lands.

Pull requests are unaffected. **Load the `use-github` skill before opening a
PR**; its issue-filing and board conventions are suspended for the trial, and a
PR body names the issue it lands (`Lands agent-tooling-xyz`) instead of
`Closes #N`.

## Documentation

- `README.md` is the front door and the fresh-machine bootstrap;
  `docs/index.md` is the documentation front door. `LEXICON.md` is the
  vocabulary (`use-lexicon`); `docs/adr/` holds the decisions (`use-adrs`).
- Every project (a Wrapper, a Skill or Skill family, the Installer) documents
  itself under `docs/projects/<project>/`, a State doc set with no overlap:
  - `index.md`, the one living overview: what the project is, then a
    `## Status` table, `Capability | State | Where`, one row per user-sized
    capability, with the closed state set `shipped`, `planned` (ratified;
    links its proposal doc and Issue IDs), `proposed` (proposal in
    workshop), `retired` (kept only if it prevents reintroduction; links an
    ADR). `### Known gaps` follows: defects in shipped capabilities only, one
    line each with its Issue ID. No dates, PR numbers, or narrative in
    Status. Status lives only here.
  - `design.md`, optional, the one living design: current architecture,
    invariants, rationale, and the rejected alternatives that prevent
    relitigation. How and why live only here.
  - Everything else is dated: a proposal, an audit, a design anchored at a
    date. Each states its date in its header and is never updated to
    describe later state.
- Living docs describe the code as it is on `main`. No living doc presents
  unbuilt behavior as current: what the system should do lives in a dated
  proposal, linked from a `planned` or `proposed` Status row and its Issues.
- Merge-readiness: a PR that lands an Issue updates that capability's Status
  row in the same PR, and a PR that changes behavior a living doc describes
  updates that doc in the same PR.
- `skills/use-bd/onboarding.md` is the maintainer's checklist for
  initializing Beads in another repo.
