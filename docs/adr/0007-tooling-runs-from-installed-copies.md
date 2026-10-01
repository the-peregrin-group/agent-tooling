---
date: 2026-09-23
status: current
---

# Agent tooling runs only from installed copies, which the Installer ships from one or more Source repos

**Context:** Agents run tooling that fronts credentials and enforces policy,
and running it straight from a checkout put every half-finished edit live
machine-wide, where a tampered file looked like routine work. A consumer may
also keep agent tooling in more than one repo, for instance to keep tooling
it cannot share out of a repo it shares, while every repo's tooling must
land in the same places agents look. The analysis and the current mechanics
are in the [Installer design](../projects/installer/design.md).

**Decision:** Agent tooling runs only from copies that `tooling-install`
installs into fixed Install Targets (`~/.local/libexec/agent-tooling/` for
every Source repo's executables, hooks included, plus `~/.claude/skills/`
and `~/.claude/agents/`), each Source repo declaring its Cohorts in an
`install.json` and each Install Target recording per-Source-repo ownership,
commit, and file hashes in one Receipt.

**Rationale:** An installed copy with a Receipt makes "what is running" a
fact separate from "what is being edited", and Install Targets that no
agent writes in normal work can be Edit-denied wholesale, so the
ask-gated `apply` becomes the only sanctioned way to change what agents run.

## Consequences

- Every source change is committed and then installed through an approved
  `tooling-install apply`; a forced install from a dirty tree is stamped
  `<hash>-dirty` in the Receipt.
- Skills invoke tools by bare name on PATH, so Permission rules match one
  literal form and never name a checkout path.
- Live-testing uninstalled code means invoking it by path, which prompts on
  every call.

## Alternatives Considered

### Run tooling from the checkout

**Description:** Put the checkout on PATH and read Skills from it directly.
**Rejection rationale:** Every unsaved or uncommitted edit goes live
machine-wide, and the config directory Skills are read from cannot be
write-denied because every session writes there.

### Symlinks from Install Targets into checkouts

**Description:** Install by linking each target entry to its source file.
**Rejection rationale:** It is indirection without protection: a link into
the checkout silently restores running from the checkout.

### An environment-variable switch to run from the checkout

**Description:** A variable such as `GHW_DEV=1` redirects bare names to the
checkout for development.
**Rejection rationale:** Any agent can export it, and the switch is
invisible to Permission rules, so it reopens running from the checkout
behind a flag.

### Install executables into `~/.local/bin`

**Description:** Use the conventional user executable directory.
**Rejection rationale:** Package managers write there routinely, so an Edit
deny on it would trip on legitimate traffic.

### Reserve the executable directory for credential-fronting Wrappers

**Description:** Keep hooks and other executables out of
`~/.local/libexec/agent-tooling/`, or give them a target of their own.
**Rejection rationale:** Hooks gate sessions and need the same tamper
protection; the worry was mixed-purpose source trees, which Cohorts already
prevent.

### Claude Code plugins

**Description:** Ship the tooling as a plugin.
**Rejection rationale:** Plugin Skills are namespaced `plugin:skill`, which
breaks every existing invocation and Permission rule.

### A single Source repo for all tooling

**Description:** One repo holds every tool, so one Receipt record suffices.
**Rejection rationale:** A consumer with tooling it cannot share would have
to keep it all private; a Receipt keyed by Source repo lets several repos
share the targets without overwriting each other.
