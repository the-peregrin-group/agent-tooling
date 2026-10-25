# Proposal: rebase the triage wrappers onto the shared library

This document captures state as of 2026-08-16. For current state, see
[index.md](index.md) and [design.md](design.md).

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
