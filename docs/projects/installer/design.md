# Installer design

How the Installer works and why. What is shipped is in
[index.md](index.md). The founding decision, that agent tooling runs only
from installed copies shipped from one or more Source repos, is recorded
in [ADR 0007](../../adr/0007-tooling-runs-from-installed-copies.md).

## Why installed copies

Agents run tooling that can act with credentials and policy: Wrappers that
front a forge token, Skills that tell agents what they may do, hooks that
gate sessions. If that tooling ran from a checkout, every half-finished edit
would go live machine-wide, and a tampered file would look like routine
work. The Claude Code config directory, where Skills are read from, cannot
simply be write-protected either: every session writes there (memory,
transcripts, settings).

So a checkout is source only. The Installer copies it into Install Targets
that no agent writes in the course of normal work, which lets Permission
rules deny Edit on them wholesale with no false positives. Anything that
writes there is anomalous by construction. Updating what agents run becomes
a deliberate, approved act: a silent edit that looks routine turns into a
loud, deniable write outside the source tree. This raises the bar; it is not
a hard boundary within one OS user. The cost is a dev-loop step: every
change is committed, then installed.

## Model

- **Source repo.** A repo with an **Install Manifest**, `install.json` at
  its root (version 1): its `source_repo` label, a top-level `exclude`
  list, and its **Cohorts**. The source checkout is always an explicit
  argument, never inferred, because one installed `tooling-install` serves
  every Source repo.
- **Cohort.** A named set of source directories that installs into one
  Install Target, with an optional cohort-level `exclude`. Each Cohort's
  `kind` is unique within a manifest, so a Source repo has one Cohort per
  Install Target it uses.
- **Install Target.** One directory per kind:

  | Kind | Install Target | Shape |
  |---|---|---|
  | `bin` | `~/.local/libexec/agent-tooling/` | merge |
  | `skills` | `~/.claude/skills/` | unit (one Skill per unit) |
  | `agents` | `~/.claude/agents/` | merge |

  A *merge* target collapses a Cohort's source directories into one root
  while preserving each one's internal layout (`cli/lib/plan.py` lands at
  `lib/plan.py`); the Wrappers import `lib.*` from their own directory,
  so the layout is load-bearing. Two source files claiming one target
  path are refused. A *unit* target installs and swaps each Skill
  directory wholesale and independently.
- **Exclusions.** The top-level `exclude` is the noise list (bytecode, OS
  droppings, VCS metadata, tests): never content on either side, so it also
  filters the target scan. A Cohort's own `exclude` means "this repo does
  not ship that file"; the same name found in a target is genuinely unowned,
  so cohort excludes narrow only the source scan. A pattern matches a
  source-relative path, any single component of it, or a directory prefix.
- **Receipt.** Each Install Target holds one `install-receipt.json`, keyed
  by Source repo. A record holds the kind, source path, source commit
  (`<hash>-dirty` for a forced install), install time, a sha256 per file,
  and, on a unit target, the units. An install rewrites only its own
  record, apart from entries Adoption moves out of another. Files another
  record claims are *foreign* and carried through untouched. Files no
  record claims are *unowned*: reported, preserved on merge targets, never
  claimed.
- **Adoption.** A source that ships a path, or a unit, another record
  claims has a collision. If the incoming copy is byte-identical to the
  installed one, ownership moves to the incoming record and the bytes do
  not change; this is how a Cohort migrates between Source repos. A unit
  adopts only if its installed and incoming file sets are equal and every
  digest matches. A collision that is not byte-identical, or a claimed name
  missing from the target, is *conflicting* and refuses the run. A record
  that Adoption empties is dropped.

## Commands

```
tooling-install {diff | apply} <source-checkout> [--cohort <name>]... [--force]
tooling-install adopt <source-checkout> <superseded-source-repo> [--cohort <name>]... [--force]
```

- **`diff`** is read-only. It reports drift per Cohort, classifies
  collisions as `adoptable` or `conflicting`, and lists what an install
  would destroy: `unowned_replaced` (unclaimed files inside a unit being
  swapped) and `foreign_replaced` (files another record claims that the
  incoming unit does not ship). All of these count as drift. It reports an
  interrupted swap but never repairs one, so it stays safe to grant.
  `--force` is illegal with `diff`.
- **`apply`** installs. It refuses a dirty source unless `--force`, judging
  dirtiness only over the selected Cohorts' source directories. It never
  overwrites another Source repo's content, except by byte-identical
  Adoption, and reports adopted names.
- **`adopt`** installs exactly as `apply` does, except that a collision
  with the *named* superseded record transfers whatever the content: the
  incoming copy wins, and the superseded checkout still holds what it gave
  up. Collisions with any other record still refuse. A superseded name no
  selected receipt records is a usage error, so a typo cannot silently turn
  the takeover into a plain install. `adopt` has no preview; `diff` is its
  dry run, and its `conflicting`, `unowned_replaced`, and
  `foreign_replaced` lists are what to read before approving one.
- **`--cohort <name>`**, repeatable, restricts any command to the named
  Cohorts. An undeclared name is a usage error, never an empty run.

## Invariants

- The Installer is the only writer of Install Targets and their Receipts.
- It never overwrites content another Source repo owns, except by
  Adoption.
- It removes a file from a target only when this Source repo's previous
  Receipt proves it installed that file.
- It never replaces unowned content without reporting it, and `diff`
  treats any such loss as drift.
- What is installed is git-addressable: the Receipt names the commit, and a
  forced install from a dirty tree is stamped `<hash>-dirty`, never
  laundered.
- A source that equals, contains, or sits inside any declared Install
  Target is refused, over every Cohort, selected or not; otherwise the swap
  would rename part of the source out from under the run.

## The swap

Per target directory, or per Skill unit: stage into a sibling
`<name>.new-<pid>`, rename the live copy to `<name>.retired-<pid>`, rename
the staging copy into place, then delete the retired copy. Two renames are
not atomic, so a crash between them leaves the target missing beside a
retired copy. `apply` and `adopt` recover that before any other work;
recovery that is ambiguous refuses.

Two concurrent installs from different Source repos into one merge target
are last-writer-wins: each stages from the Receipt it read at its start.
This is deliberately unguarded. An install is a human act behind a
permission prompt, not a daemon, and a lock would only guard against two
humans installing at once.

## Exit codes

The Installer keeps its own codes rather than the Wrappers' Exit-code
contract; [the Exit-code contract](../../index.md#exit-code-contract)
lists each family's codes.

| Code | `diff` | `apply`, `adopt` |
|---|---|---|
| 0 | in sync | applied |
| 1 | drift, or not installed | failed |
| 2 | usage or environment error | usage or environment error, including an unknown superseded repo |
| 4 | refused | refused: dirty source without `--force`, source/target overlap, conflicting collision, ambiguous crash recovery |

## The executable-tooling directory

`~/.local/libexec/agent-tooling/` is the installed executable-tooling
directory for every Source repo, hooks included. It is on PATH in place of
any checkout, so Skills invoke tools by bare name and those names are what
Permission rules match. It is a dedicated directory, not `~/.local/bin`:
package managers write to `~/.local/bin` routinely, so a deny rule there
would trip on legitimate traffic, while a directory only the Installer
writes can be denied wholesale. Hooks belong there too, because they gate
sessions and want the same tamper protection as Wrappers. Cohorts keep each
source tree single-purpose, so mixing purposes in the installed directory
costs nothing; the Edit deny and the Receipts protect the installed set.

## Permission model

- Allow `tooling-install diff`, so an agent can report drift without being
  able to act on it.
- Ask on `tooling-install apply` and `tooling-install adopt` as explicit
  `ask` rules, not merely unlisted ones: `ask` outranks `allow`, so a later
  broad allow cannot swallow them. The prompt is the ceremony.
- `adopt` is a separate verb, not a flag on `apply`, because Permission
  rules match literal prefixes and cannot exclude a trailing option.
  `apply`, which never overwrites another repo's content, can then be
  granted differently from `adopt`, and the superseded repo is visible in
  the command the human approves.
- Deny Edit on every Install Target. No file-tool rule grants a write
  there, so a change reaches installed tooling only through a committed
  source and an approved install. A residual shell channel remains: some
  broad Bash grants can write files, and `~/.local/libexec/` is not a path
  the harness itself protects.

## Development and bootstrap

- Tests run from the source tree, offline, and never touch the real
  Install Targets. No credential meets uninstalled code.
- Live-testing an uninstalled change means invoking the checkout script by
  path. That matches no bare-name rule and so prompts on every call, which
  is deliberate friction; for iterative live work, install the work in
  progress.
- A fresh machine bootstraps by running the Installer once from its own
  checkout, `python3 <checkout>/cli/tooling-install apply <checkout>`. It
  ships in the `bin` Cohort, so it installs itself.
