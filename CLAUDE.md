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

Run from `cli/` with the system interpreter that every shebang pins:

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

Work tracking lives in **Beads** (`bd`), this repo's only Issue Tracker. The
committed `.beads/` files are config only; the database is local to the
maintainer's machine. GitHub Issues stays enabled but takes no work: the
open issues were imported into Beads once, one way, on 2026-09-24, and stay
open on GitHub as stale copies. No GitHub issue is filed, edited, relabeled,
reprioritized, or closed until the long tail moves back to forge issues
(`agent-tooling-ze3`). There is no sync in either direction. ADR 0011 (Beads
tracks agent-swarmed work; long-lived work belongs in forge issues) has the
reasons, and `docs/projects/beads-trial/` the setup.

**Load the `use-bd` skill at session start**: it is the operating manual for
Beads through `bdw`. This repo's Beads conventions (labels, the friction
log, `TODO` citations) are in `.beads/PRIME.md`, which `bdw prime` prints.

The Beads Permission rules in `.claude/settings.json` are generated from
use-bd's canonical rule set (`skills/use-bd/rules.json`) plus this repo's
local layer in their spec, `cli/repo_policy_test.py`: change the data or
the spec, regenerate the file, and let the test confirm they agree. The
rules are prefix rules, so they are not safe in auto mode until the
parsed-command deny hook lands.

Pull requests are unaffected. **Load the `use-github` skill before opening a
PR**; its issue-filing and board conventions do not apply while Beads is the
Issue Tracker, and a PR body names the Issue it lands
(`Lands agent-tooling-xyz`) instead of `Closes #N`.

## Agent integration branches

Branches under the `integrate/` prefix are agent integration branches, one
per run and disposable (`integrate/workjam-2026-10-10`, say). Agents may
rebase onto one (`gitw-rebase agent-tooling <prefix> onto integrate/<run>`)
and merge PRs into it unattended
(`ghw-pr-merge the-peregrin-group/agent-tooling integrate/<run> merge <pr#>`).
The exact branch for a run is pinned by the maintainer's local Permission
rules, and deleting those rules retires it. `main` stays human-only: the
only PRs to `main` are the ones a human asked for.

## Documentation

- `README.md` is the front door and the fresh-machine bootstrap;
  `docs/index.md` is the documentation front door. `LEXICON.md` is the
  vocabulary (`use-lexicon`); `docs/adr/` holds the decisions (`use-adrs`).
- Every project (a Wrapper, a Skill or Skill family, the Installer) documents
  itself under `docs/projects/<project>/`, a State doc set with no overlap:
  - `index.md`, the project's living dictionary entry: what it is and where
    it stands, in brief. Depth belongs in `design.md`, the encyclopedia
    entry.
    - `## Overview`: what the project is _today_, in at most 250 words.
    - `## Status`: the table, and the sole source of truth for status. No
      dates, PR numbers, or narrative/history. `Capability | State | Where`,
      one row per user-sized capability, with the closed state set
      `shipped`, `planned` (ratified; links its proposal doc and Issue IDs),
      `proposed` (proposal in workshop), `retired` (kept only if it
      prevents reintroduction; links an ADR).
    - `### Known gaps` under `## Status`: defects or omissions in shipped
      capabilities, one line each with its Issue ID, added when the Issue is
      filed and removed by the PR that fixes it.
  - `design.md`, optional, the one living design and the encyclopedia
    entry: current architecture, invariants, rationale, and the rejected
    alternatives that prevent relitigation. How and why live only here.
  - Everything else is dated: a proposal, an audit, a design anchored at a
    date. Each opens with one note, "This document captures state as of
    <date>. For current state, see <living doc(s)>.", and beyond that note
    is never updated to describe later state.
- Living docs describe shipped capabilities as intended. Where `main` falls
  short of that (a defect, or an omission not yet built), the project's
  Known gaps says so, citing the Issue. A capability not yet built at all
  lives in a dated proposal, linked from a `planned` or `proposed` Status
  row and its Issues.
- Done is consistency everywhere, at two levels:
  - **Per PR:** a PR leaves the repo as consistent as one PR can make it.
    Search for what changed (the Verb, flag, exit code, path, Issue ID, old
    behavior) across `docs/`, `skills/`, `cli/` (docstrings and tests),
    `README.md`, `LEXICON.md`, `.beads/PRIME.md`, and open Beads Issues
    (`bdw search`, `bdw list --desc-contains=<words> --all`), and update
    every hit. Whatever one PR cannot make true yet (a later PR, another
    repo, a deployment) is a Known gap or an open Issue that names it. A PR
    that lands an Issue updates its capability's Status row.
  - **Per task:** an Issue is done only when every reference across every
    surface we control agrees with the change, however many PRs, repos,
    deployments, or authors that takes: this repo, consumer repos, the
    installed copies (`tooling-install apply`), Beads, and Permission
    rules. GitHub issues are stale copies and stay untouched (see Issue
    tracking).
- `skills/use-bd/onboarding.md` is the maintainer's checklist for
  initializing Beads in another repo.
