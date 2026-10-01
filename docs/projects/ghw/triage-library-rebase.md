# Proposal: rebase the triage wrappers onto the shared library

Proposal, ratified 2026-08-10, amended 2026-08-16. Status and Issues:
[index.md](index.md). Current architecture: [design.md](design.md).

## Problem

The six `triage-*` reference wrappers predate the shared library the ghw
Verbs use. They carry their own `gh` layer (`lib_gh.py`) and profile parser
(`lib_profile.py`), so:

- the schema constants are declared twice; `triage-apply-sync` hardcodes its
  own terminal-state set instead of importing it;
- the `TRIAGE.md` config block has two parsers, triage's and the one the ghw
  board code grew;
- triage's `gh` calls lack the shared layer's hardening: no subprocess
  timeout, so a prompting subcommand or stalled connection hangs an
  unattended pass instead of failing.

## Plan

- **A library, not a CLI.** The wrappers import the shared code; they never
  shell out to `ghw-*`. Their names, contracts, and Permission rules stay
  exactly as deployed: the sync wrapper still cannot be told a target status,
  and the ledger wrapper still cannot be told a target issue. Shelling out to
  the Verbs would make those narrow bindings buy nothing, since the Verbs
  accept far wider arguments.
- **One home for constants.** Inline literals (the terminal-state set and the
  like) become imports of the shared schema constants, behavior unchanged.
- **One config parser.** The `TRIAGE.md` config block is parsed in one place.
- **Inherit the hardened `gh` layer, timeouts included.** This is the one
  deliberate behavior change: a call that used to hang now fails loudly.
- **No silent truncation.** The shared open-issue listing must fail or
  paginate, never truncate silently, before triage depends on it.

Later, not part of this change: once IDs resolve at runtime, `TRIAGE.md`
profiles shrink to genuine policy tuning (staleness, ledger issue, cadence).

## Implementation notes (as of 2026-10-01)

- The shared library is `cli/lib/` (constants in `cli/lib/schema.py`) plus
  `cli/lib/github/`; the second `TRIAGE.md` parser is
  `cli/lib/github/boards.py`, although the triage README calls
  `lib_profile.py` the only one.
- `triage-inventory` already truncates silently at 500 open issues through
  triage's own copy of `issue_list_open`; the rebase must not carry that
  over. The shared `gh.issue_list_open` has the same 500 limit and no ghw
  caller.
- **Open question.** The plan was written when wrappers and their library
  shipped inside the skill directory. Today the Installer puts `cli/lib/` in
  `~/.local/libexec/agent-tooling/` and the triage wrappers in
  `~/.claude/skills/triage-issues/reference/`, different Install Targets. How
  the wrappers locate the library across Install Targets, or whether they
  move into `cli/`, is not yet designed.
