---
date: 2026-10-25
status: current
---

# agent-tooling keeps its machine-specific files in three roots by kind: config, state, and the Install Targets

**Context:** agent-tooling's machine-specific files grew one tool at a time, gitw's roster under `~/.config/gitw/` and fjw's token under `~/.config/fjw/`, while the code finds the home directory three different ways and its config lookups ignore `XDG_CONFIG_HOME`. `bdw`'s push work was about to add the first state files (a lock, a failure record, a log) and a hand-written push-host allowlist, so the layout needed settling before more files landed in ad hoc places. The layout as it stands, and the helper every new caller uses, are in [Path layout](../index.md#path-layout).

**Decision:** agent-tooling's machine-specific files live in three roots by kind, configuration under `${XDG_CONFIG_HOME:-~/.config}/agent-tooling/<tool>/`, state under `${XDG_STATE_HOME:-~/.local/state}/agent-tooling/<tool>/`, and installed tooling in the Install Targets, which stay where [ADR 0007 (tooling runs only from installed copies)](0007-tooling-runs-from-installed-copies.md) put them.

**Rationale:** Config is small, hand-maintained, sometimes secret, and worth backing up, while state is machine-generated, churns, and is safe to delete, so they belong in the separate roots the XDG Base Directory spec gives each kind, under one product name so a user finds every tool's files in one predictable place per kind.

## Consequences

- The gitw roster and the fjw config move from their per-tool directories to `agent-tooling/gitw/` and `agent-tooling/fjw/` under the config root, each with a migration for files already on disk.
- Permission rules that protect these files name literal paths, so a machine whose `XDG_CONFIG_HOME` or `XDG_STATE_HOME` points elsewhere is not covered by rules written for the defaults.
- Staging directories (`/tmp/claude/`, a background job's `tmp/`) are scratch space for message and body files, not machine-specific files, and stay outside the three roots.

## Alternatives Considered

### A single `~/.agent-tooling` directory

**Description:** Keep every tool's config and state under one dotfile directory in the home directory.
**Rejection rationale:** It is no easier to find than the config root, it adds another entry to the home directory, and it mixes config with state.

### A single `~/.config/agent-tooling` with a `state/` subdirectory

**Description:** Use the config root alone, with state in a subdirectory beside the tools' config.
**Rejection rationale:** It mixes config with state, so a backup of config sweeps up churning state, and "safe to delete" no longer holds for the directory as a whole.

### Keep the per-tool directories

**Description:** Leave each tool its own top-level name under the root, `~/.config/gitw/` and the like.
**Rejection rationale:** Short tool names collide with unrelated software in a shared root, and nothing ties a tool's directory to agent-tooling, so a user cannot find or protect all of it at once.

### Move the Install Targets under the new roots

**Description:** Install tooling under the config root or a data root beside the other files.
**Rejection rationale:** The Install Targets are where ADR 0007 put them for reasons that still hold (agents' harness reads Skills and Agent definitions from `~/.claude/`, and the executable directory is chosen to be Edit-deniable wholesale), and moving them would migrate every installed copy and Permission rule for no gain.
