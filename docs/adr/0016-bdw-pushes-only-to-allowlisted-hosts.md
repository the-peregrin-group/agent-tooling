---
date: 2026-10-25
status: current
---

# bdw pushes the Beads database only to hosts on a fail-closed allowlist

**Context:** [ADR 0014](0014-bdw-pushes-the-beads-database-after-writes.md) (bdw pushes the Beads database after every write) makes the push run unattended after every write, and [ADR 0012](0012-beads-data-syncs-to-private-forgejo-remote.md) (Beads data syncs to a private Forgejo remote) forbids the public origin, but a Dolt remote is whatever `bd dolt remote add` or `bd init` last set, and a push publishes every Issue with its full history beyond recall. A first draft of ADR 0014, never on `main`, only refused a Dolt remote naming the same repository as a git remote of the workspace, which stops one mistake and lets every other wrong remote through. The file and its format are in the [bdw project doc](../projects/bdw/index.md#the-push-host-allowlist).

**Decision:** `bdw` pushes only when every Dolt remote's host is listed in a hand-written allowlist in its subdirectory of the Machine Config Directory, refusing when the list is missing, unreadable, or malformed, and still refusing a remote that names the same repository as a git remote of the workspace.

**Rationale:** A push that runs unattended and cannot be taken back must fail closed, so only a destination a person named is trusted, while the repository check stays because an allowed forge can host the public code beside the private Dolt repository.

## Consequences

- A machine pushes nothing until its maintainer writes the allowlist, and every refused push is warned about until then.
- The allowlist names hosts, not ports or repositories, so a second repository on an allowed host is trusted too; the repository check covers only the code's own.

## Alternatives Considered

### The repository blocklist alone

**Description:** Refuse only a Dolt remote naming the same repository as a git remote of the workspace.
**Rejection rationale:** It names one mistake and trusts every other remote, so a mistyped or adopted remote on any third-party host would be pushed to.

### Allow host and port

**Description:** List `host:port` pairs rather than hosts.
**Rejection rationale:** One server answers on several ports (ssh on 22 or another, https on 443), so the list would break on a change of transport, and anyone who controls a port on an allowed host controls the host.

### Allow whole remote URLs

**Description:** List the exact Dolt remote URLs that may be pushed to.
**Rejection rationale:** The URL is the secret detail the public repository must never carry, it changes with transport and spelling, and the question the list answers is which machine may hold the data.

### Trust a host derived from the repository's own config

**Description:** Read the allowed host from a tracked file in the repository, such as `.beads/config.yaml`.
**Rejection rationale:** A tracked file in a public repository cannot hold a private host, and an allowlist the workspace can rewrite does not constrain the workspace.
