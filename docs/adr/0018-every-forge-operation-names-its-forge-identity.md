---
date: 2026-10-27
status: current
---

# Every forge operation names its Forge identity, and every write carries the Actor ID

**Context:** On Forgejo agents act as a machine account, but on GitHub ghw runs under the maintainer's own account, so an agent's act is recorded as the maintainer's, which breaks the rule that every state change has one true recorded owner and the accountability that [ADR 0017](0017-delegation-is-expressed-as-permission-rules-on-situation-split-verbs.md) (delegation as Permission rules on situation-split Verbs) rests on. One machine account everywhere does not fit either: the maintainer sometimes wants agents assisting with their own work under their own account, and third-party repos admit no machine account at all. The 2026-10-27 home-in on the Issue Tracker skill family ([proposal](../projects/use-issues/2026-11-05-proposal.md)) settled it.

**Decision:** Every forge Verb takes a Forge identity as its argument directly after the repo, on reads and writes alike. The name resolves to an account registered in the forge Wrapper's Machine Config; an agent never supplies a raw account. Which Forge identities an agent may act under is granted per repo by Permission rules. Every write, under any identity, is marked with the Actor ID.

**Rationale:** The account answers "with whose authority" and the Actor ID answers "whose hands", and putting the identity right after the repo lets each repo grant its own identities with the fewest rules.

## Consequences

- Rule sets at most double, since a repo has one or two identities.
- Each forge keeps its own identity list: a GitHub identity and a Forgejo identity are different things, and this scales per platform.
- Setting up a repo includes registering its identities and giving the machine account access.
- Acting under a person's account is a risk that person accepts by granting it; the Actor ID marker is what keeps those acts distinguishable from the person's own.

## Alternatives Considered

### A machine account, always

**Description:** Agents act on every forge as a machine account, as on Forgejo today.
**Rejection rationale:** Third-party repos admit no machine account, and the maintainer wants agents assisting under their own account at times.

### An Actor ID marker only, under the person's account

**Description:** Keep acting as the person and mark every write with the Actor ID.
**Rejection rationale:** The recorded owner stays wrong, and telling agent acts from the person's means reading every body instead of looking at the account.

### Identity before repo in the argument order

**Description:** `<verb> <identity> <repo> …`, so one rule could cover an identity across repos.
**Rejection rationale:** Permission rules are granted per project, so repo-first gives the smallest rule set, and it matches gitw's `<repo> <branch-prefix>` shape, where the situation token follows the repo.

### Identity from the environment or a config default

**Description:** The Wrapper picks the identity from an environment variable or a per-repo default, with no argument.
**Rejection rationale:** A Permission rule cannot match what is not in the command, so one grant would cover every identity.
