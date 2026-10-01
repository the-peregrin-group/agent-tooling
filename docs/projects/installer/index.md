# installer: the Installer

The Installer, `tooling-install`, copies agent tooling from Source repos into
fixed Install Targets, and agents only ever run the installed copies. A
checkout is source; nothing runs from it. Each Source repo declares its
Cohorts in an Install Manifest (`install.json`), each Install Target carries
a Receipt recording which Source repo installed which file from which
commit, and several Source repos can share one Install Target without
overwriting each other. `diff` reports drift and is safe to grant; `apply`
and `adopt` change what agents run and are gated behind a human's approval.
How it works and why is in [design.md](design.md); the founding decision,
that agent tooling runs only from installed copies, is
[ADR 0007](../../adr/0007-tooling-runs-from-installed-copies.md).

## Status

| Capability | State | Where |
|---|---|---|
| Report drift between a source checkout and what is installed | shipped | `tooling-install diff` |
| Install a Source repo's tooling, refusing a dirty source | shipped | `tooling-install apply` |
| Install from a dirty source, marked in the Receipt | shipped | `--force` |
| Install selected Cohorts only | shipped | `--cohort` |
| Per-Install-Target Receipts recording owner, commit, and file hashes | shipped | `install-receipt.json` |
| Several Source repos sharing one Install Target | shipped | Receipts keyed by Source repo |
| Adoption of byte-identical content, and explicit takeover from a named Source repo | shipped | `tooling-install apply`, `tooling-install adopt` |

### Known gaps

- `tooling-install` resolves `python3` through `/usr/bin/env` instead of
  pinning the system interpreter like the fjw and gitw Verbs
  (`agent-tooling-1790288520721-1-86415521`).
- The README's minimum Permission rules omit the Edit deny on the Install
  Targets and the allow for `tooling-install diff` (Issue to be filed).
