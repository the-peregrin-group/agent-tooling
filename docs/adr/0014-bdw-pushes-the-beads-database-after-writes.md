---
date: 2026-10-16
status: current
---

# bdw pushes the Beads database to its Dolt remote after every write

**Context:** [ADR 0012](0012-beads-data-syncs-to-private-forgejo-remote.md) (Beads data syncs to a private Forgejo remote) gave the database a remote but left open what triggers a push, and bd 1.3.0 in embedded mode was observed not to push on writes, even with `sync.remote` set. Agents are denied every `dolt` verb, a Beads push bypasses gitw and git's pre-push hooks, and the 2026-10-12 workjam ran about 300 sub-agents writing to one database at once. The mechanism is described in the [bdw project doc](../projects/bdw/index.md).

**Decision:** After each call that `bd` ran successfully and that is not a read, `bdw` starts a detached, coalesced background push of the database to its Dolt remote, refusing any remote that names the same repository as a git remote of the workspace.

**Rationale:** `bdw` already sits on every agent write and carries the Beads policy Permission rules cannot express ([ADR 0010](0010-bdw-carries-beads-policy-in-tiers.md), bdw carries Beads policy in tiers), so the remote stays current with no hook, timer, or agent instruction, and the one remote write stays in code agents cannot talk past.

## Consequences

- Agents never type a push, and they stay denied every `dolt` verb; the Permission rules see `bdw <verb>`, not the push `bdw` runs.
- A push failure never fails the write: a recorded failure makes `bdw` warn on later calls until a push succeeds, and the next push sends every unpushed commit.
- A maintainer's raw `bd` writes are pushed by the next `bdw` write.

## Alternatives Considered

### Chain a push into git's pre-push hook

**Description:** Run `bd dolt push`, best-effort and in the background, from the repo's pre-push hook, so every code push also pushes the Issue data.
**Rejection rationale:** The installed pre-push hook is owned and versioned outside this repo, and sessions that write to the tracker without pushing code would leave the remote stale until the next code push.

### A scheduled job

**Description:** A launchd timer runs `bd dolt push` every few hours.
**Rejection rationale:** The remote lags by up to the interval, the job needs its own install, privacy grants, and failure alerting, and it fails silently if never installed.

### bd's own auto-push

**Description:** Configure `sync.remote` and let bd push after writes.
**Rejection rationale:** It was not observed to push in embedded mode, even with `sync.remote` set through the untracked `BD_SYNC_REMOTE`, and setting it in the tracked config is how `bd dolt remote add` came to commit the remote's address to a public repo.

### Push synchronously after each write

**Description:** `bdw` runs the push before returning.
**Rejection rationale:** Every write would wait on the network, and concurrent writers would race to update the same remote ref.
