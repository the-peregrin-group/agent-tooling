# use-bd: design

use-bd is the Skill that teaches agents how this ecosystem uses Beads (`bd`)
as its Issue Tracker, through [`bdw`](../bdw/index.md), the Beads Wrapper.
This document holds why use-bd and `bdw` work the way they do; the Skill
(`skills/use-bd/`) holds the procedure.

> **In progress.** This design is being worked out in a home-in session
> (2026-10-07). Only the sections below the line are settled; the open
> items at the end are the live state of that session and are removed
> before the change merges.

## Why use-bd exists

Beads' operating policy for agents is spread across `CLAUDE.md`, the README,
the Beads ADRs, the Permission rules' spec comments, the trial docs, and
[`docs/beads-init.md`](../../beads-init.md), and works only if each is read
at the right moment. Meanwhile `bd prime`, the one text every agent is told
to run first, teaches the opposite of local policy in several places (raw
`bd` writes, `bd edit`, `bd remember`, inline text, raw git commits).

use-bd is part of the [Beads trial](../beads-trial/index.md)'s phase one,
not something built after it. The trial tests Beads run well: with the
systems and guardrails that let agents cooperate on it uniformly and
reliably. A verdict on Beads used bare would grade the wrong thing.

## Design stance

- **Usage first, then encoding.** The design settles how agents should use
  Beads, then encodes that in the Skill and, where the Skill's guidance
  needs it, in `bdw`. `bdw` is ours: where the right practice needs it to
  behave differently, it changes, rather than the Skill teaching around it.
- **Our layer absorbs what is fixable.** Friction that can be fixed easily
  without changing Beads' fundamental nature, identity, or values (its
  design ideology, APIs, data model, features and limitations) is our
  tooling's to fix, and counts against our tooling, not Beads, at the
  trial's verdict. Friction that clashes with that nature counts against
  Beads; working around it would mean building a spinoff, which is not the
  goal. This is a judgment call, deliberately not an enumerated test. The
  go/no-go criteria built on it are tracked in `agent-tooling-bs8` (write
  down the go/no-go criteria).

---

## Open items

**Frontier** of the home-in walk (Lines of Inquiry):

- Exhausted: Trigger.
- Untouched: Success, Anti-goals, Stakeholders, Constraints, Load-bearing
  assumptions, Alternatives, Reversibility and horizon, Pre-mortem,
  Disconfirmation.
- Depth: deep on Success, Constraints, Alternatives, Load-bearing
  assumptions; shallow on the rest.

**Resolution Queue:**

- Assumption under test: use-bd can be one Skill serving every repo, though
  it installs machine-wide while much current policy is this repo's trial
  policy (walk under Constraints).
- Assumption under test: fixes in our layer stay easy, so `bdw` never grows
  into a spinoff; needs a ceiling (walk under Alternatives).
- Candidate decision: amend or supersede the decision that `bdw` execs `bd`
  with arguments untouched ([ADR 0002](../../adr/0002-beads-identity.md),
  Beads identity).
- Candidate lexicon change: whether bdw follows the Exit-code contract (the
  lexicon says only gitw, ghw, and fjw do; `docs/index.md` and the bdw docs
  say bdw does too).
- To do in this change: rewrite the trial's stated question in
  `docs/projects/beads-trial/index.md` to the "Beads run well" framing, and
  note the attribution rule on `agent-tooling-0pe` (record the go/no-go
  verdict as an ADR).
