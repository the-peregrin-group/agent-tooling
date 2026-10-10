# use-bd: the Beads operating manual

use-bd is the Skill that teaches agents how this ecosystem uses Beads
(`bd`) as its Issue Tracker, through [`bdw`](../bdw/index.md), the Beads
Wrapper. It installs machine-wide and serves every repo that uses Beads, so
it holds only what is the same everywhere; each repo states its own
conventions in a committed `.beads/PRIME.md`, which `bd prime` prints in
place of its default text, and its policy in its reviewed Permission rules.

The Skill is `skills/use-bd/`: `SKILL.md`, read on every load, and two
supporting files read on need, `quirks.md` (the known behavior of the
verified bd version) and `onboarding.md` (setting Beads up in a new repo).
It teaches only what works on `main`; it grows as the `bdw` changes of the
[version-one proposal](v1-proposal.md) ship, slice by slice, under
`agent-tooling-aio` (the use-bd epic). Branch Issues worked in passes are
[ADR 0009](../../adr/0009-branch-issues-are-worked-in-passes.md); `bdw`
carrying policy in tiers is
[ADR 0010](../../adr/0010-bdw-carries-beads-policy-in-tiers.md).

## Status

| Capability | State | Where |
|---|---|---|
| The session loop through `bdw`: prime, ready, claim, file discovered work, append, close, land the plane | shipped | `skills/use-bd/SKILL.md` |
| The sub-agent rule (an agent sharing its session's Actor reads, files, and appends, never claims, closes, or rewrites) and claims ending with their session | shipped | `skills/use-bd/SKILL.md` |
| Branch and Leaf Issues, and working a Branch Issue in passes, practiced by hand | shipped | `skills/use-bd/SKILL.md` |
| Filing discipline: search first, one-session Leaf Issues, kind in the type field, at least one area label, the four relationships, context linked by metadata key | shipped | `skills/use-bd/SKILL.md` |
| Free text through bd's existing file forms, switching to a file form when inline text is refused; description as state, notes and comments as log | shipped | `skills/use-bd/SKILL.md` |
| Work waiting on a human: gates, the `human` label, `branch` and `pr` metadata | shipped | `skills/use-bd/SKILL.md`; gate rules in `.claude/settings.json` |
| Friction reporting, and offering (never filing) upstream bug reports | shipped | `skills/use-bd/SKILL.md` |
| Known bd 1.3.0 behavior | shipped | `skills/use-bd/quirks.md` |
| Onboarding a repo: init cleanup, `PRIME.md`, Permission rules, pinning bd | shipped | `skills/use-bd/onboarding.md` |
| This repo's conventions in `.beads/PRIME.md`, printed by `bd prime` | shipped | `.beads/PRIME.md` |
| `bdw` runs bd as a child process and points every help output and usage error at use-bd | planned | [v1-proposal.md](v1-proposal.md); `agent-tooling-aio.2` |
| `bdw` refuses flag-first calls, database-switching flags, a missing workspace config, and writes on unverified bd versions | planned | [v1-proposal.md](v1-proposal.md); `agent-tooling-aio.2` |
| One Actor ID per session, from the harness's session ID | planned | [v1-proposal.md](v1-proposal.md); `agent-tooling-aio.2` |
| The canonical Beads rule set as data, raw `bd` denied, and a test that every command the Skill teaches is allowed | planned | [v1-proposal.md](v1-proposal.md); `agent-tooling-aio.3` |
| `bdw ready` without Branch Issues that have open children, and the pass rules enforced (claim refusal, claim release on breakdown, branch-kind check) | planned | [v1-proposal.md](v1-proposal.md); `agent-tooling-aio.4` |
| Filing through a validated graph plan (`bdw file graph`), with near-duplicate search, lint warnings, and a ready-work echo; other paths to structure denied | planned | [v1-proposal.md](v1-proposal.md); `agent-tooling-aio.5` |
| The repo's structured conventions file, label checks against its scheme, file forms for every free-text field, and the Docs Inbox Verb | planned | [v1-proposal.md](v1-proposal.md); `agent-tooling-aio.6` |
| A SessionStart hook that loads use-bd, and a hook refusing raw Beads calls | planned | [v1-proposal.md](v1-proposal.md); `agent-tooling-0s1.5`, `agent-tooling-0s1.6` |
| Formulas as templates for a Branch Issue's standard phases | planned | [v1-proposal.md](v1-proposal.md); `agent-tooling-sn6` |

### Known gaps

- The sub-agent rule cannot be enforced: nothing in a sub-agent's
  environment distinguishes it from its parent (`agent-tooling-jk2`).
- A title has no file form in bd 1.3.0, so a title that names the VCS is
  refused inline (`agent-tooling-aio.6`).
- Calls the Skill says never to make are still allowed in this repo
  (`human respond`, `epic close-eligible`, `unclaim --force`,
  `ready --claim`, `close --claim-next`), and marking a duplicate prompts
  (`agent-tooling-aio.3`).
