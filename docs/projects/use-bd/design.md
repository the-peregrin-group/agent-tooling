# use-bd: design

use-bd is the Skill that teaches agents how this ecosystem uses Beads (`bd`)
as its Issue Tracker, through [`bdw`](../bdw/index.md), the Beads Wrapper.
This document holds why use-bd and `bdw` work the way they do; the Skill
(`skills/use-bd/`) holds the procedure.

> **In progress.** This design is being worked out in a home-in session
> (2026-10-07 to 2026-10-08). The sections above the open items are
> settled; the open items at the end are the live state of that session and
> are removed before the change merges.

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
- **Enforce the simple rule in code.** Where a rule fits in one sentence and
  agents' habits (industry practice in their training data) pull against
  it, `bdw` enforces it with a refusal that teaches the right form, rather
  than the Skill spending paragraphs on judgment.
- **Our layer absorbs what is fixable.** Friction that can be fixed easily
  without changing Beads' fundamental nature, identity, or values (its
  design ideology, APIs, data model, features and limitations) is our
  tooling's to fix, and counts against our tooling, not Beads, at the
  trial's verdict. Friction that clashes with that nature counts against
  Beads; working around it would mean building a spinoff, which is not the
  goal. This is a judgment call, deliberately not an enumerated test. The
  go/no-go criteria built on it are tracked in `agent-tooling-bs8` (write
  down the go/no-go criteria).

## Success criteria

1. **The normal path never prompts.** Every step of the loop is a `bdw` call
   the Permission rules allow; a prompt or denial on routine work is a
   defect. Genuinely dangerous operations are the one exception.
2. **No workarounds.** Every real use case has a normal path; no agent
   rewords Issue text to dodge a refusal or skips a field because it only
   takes inline text. A real use case with no normal path is a gap to fix.
3. **A cold pick-up works.** A fresh session can resume any Issue from the
   Issue Tracker alone. The Issue points to the context it needs rather
   than holding all of it, so nothing is duplicated where it can drift.
4. **Every state change has one owner.** Every claim, close, and rewrite is
   attributable to exactly one Actor.
5. **Agents load use-bd before touching the Issue Tracker,** not after a
   refusal, and nothing `bd prime` prints contradicts it.
6. **Policy has one home.** Each rule is written once, in the Skill or this
   design; `CLAUDE.md`, the README, and the trial docs point here.
7. **Organizational hygiene.** Work is broken down into Leaf Issues sized
   for one session, under Branch Issues for anything bigger, and the four
   relationships (dependency, contradiction, duplication, composition) are
   looked for when an Issue is filed.
8. **Labels follow the project's conventions.**

**Version one covers** the loop (prime, ready, claim, file discovered work,
append, close, land the plane); the write rules; filing discipline
(breakdown, relationships, labels); pick-up notes; and the known Beads
1.3.0 quirks. Onboarding a new repo is a supporting file inside the Skill,
read only by whoever does it. **Out of scope:** batch triage and
reconciliation, phase-two sync, and the go/no-go criteria.

## The Issue hierarchy

Every Issue is either a Branch Issue (it has any children, or is of a kind
designated to hold children, e.g., an epic) or a Leaf Issue (every other
Issue, meant to be claimed and finished in one session); see `LEXICON.md`.

- **Branch Issues are worked in passes.** A Branch Issue is ready work
  exactly when it has no open children; each claim on it is one pass that
  ends by adding children or by verifying completion and closing it. It is
  never closed merely because its children closed. (See
  [ADR 0009](../../adr/0009-branch-issues-are-worked-in-passes.md),
  Branch Issues are worked in passes.)
- **Only branch kinds take new children.** `bdw` refuses to add a child to
  an Issue that is not of a branch kind, with a refusal that teaches the
  alternative: file a sibling Leaf Issue linked by a dependency, or retype
  the Issue to a branch kind first. This is a convenience guard, not a
  correctness rule: an Issue that somehow gains a child is a Branch Issue
  by definition and is treated as one. Its job is to stop an agent's habit
  (subtasks under a task) from silently turning a task in progress into a
  project; a task that proves bigger than a session is retyped instead. A
  Branch Issue that is not of a branch kind is an anomaly to repair.
- **Ending a pass.** When the session holding a Branch Issue's claim adds
  children to it, `bdw` releases the claim in the same call; closing it
  releases it too. A pass drafts its whole breakdown before submitting it,
  as one atomic batch (`bd create --graph`, previewed with `--dry-run`),
  because the children are ready work as soon as they exist; restructuring
  afterwards is an ordinary edit made knowing children may be claimed.
- **What `bdw ready` shows:** Leaf Issues with no open blockers, and Branch
  Issues with no open children; never a Branch Issue with open children
  (`bdw` also refuses to claim one).

**Rejected:** Branch Issues as passive containers (invisible before
breakdown, never verified); breakdown and acceptance child tasks (their
dependencies must be maintained by hand, against the grain); a long-lived
lead owning a Branch Issue (no agent stays available that long; deferred,
not ruled out, until longer-lived agents exist); hiding children while the
Branch Issue is claimed (a dead session hides the subtree; atomic batches
give the same privacy without a lock). Beads formulas and molecules
(templated trees) are not used for breakdown; whether they serve as
phase-subtree templates is open.

## What must never happen

- **Command policy.** The Permission rules sort every Beads operation into
  three classes:
  - **Deny** what is irreversible, sends Issue data off the machine, or
    falsifies the record; and deny any raw `bd` command, read or write, that
    a `bdw` Verb supersedes, so agents cannot take the old path out of
    habit. Reads `bdw` does not supersede stay open.
  - **Ask** for what fits the deny criteria but normal work still
    occasionally needs (it then runs only with a human attending, e.g.,
    `init` when onboarding a repo, restoring a backup), and for anything
    that steps around a `bdw` or `bd` safeguard or changes the safeguards
    or configuration themselves (e.g., `--force`, `--no-history`, `config
    set`, `batch`, `import`, `assign`).
  - **Allow** everything else. Beads is meant as a tracker for agents, by
    agents: reversible, visible operations such as marking a duplicate or
    superseding an Issue are allowed, and when to use them is a filing
    discipline, not a permission.
- **Unilateral relationships.** Agents add dependencies they find at filing
  time on their own; contradiction, duplication, and composition only when
  very confident, and otherwise raise them (or, unattended, report them).
  Because a wrong blocking dependency silently removes work from ready,
  `bdw` echoes what each new blocking dependency took out of ready work, so
  the mistake shows in the same turn. Batch reconciliation is separate work
  (`agent-tooling-r6b`, automated batch triage).
- **No silent switch of database.** `bdw` refuses to run when it cannot find
  the workspace's Beads config, because bd 1.3.0 otherwise falls back to an
  empty database without complaint.
- **The Skill never drifts from the rules.** A test checks every command the
  Skill teaches against the Permission rules spec.
- **No field agents cannot write.** `bdw` accepts every free-text field from
  a file (title, notes appended or replaced, acceptance criteria, close
  reason, comments), since inline text that names the VCS is refused by the
  harness.
- **One voice.** A committed `.beads/PRIME.md` replaces `bd prime`'s
  default text with a short pointer to use-bd.
- **No reach outside the project.** An agent acts only on its own project's
  Issues unless expressly given permission to act on another's.

## One Skill, many repos

use-bd installs machine-wide and serves every repo that uses Beads, so it
holds only what is the same everywhere. What differs per repo splits along
one line: policy (what agents may do) versus conventions (how this project
does things).

- **Policy** stays in each repo's reviewed Permission rules, never in a file
  an agent could edit to loosen its own limits. A canonical Beads rule set
  ships with the Skill as data; a test checks that every command the Skill
  teaches is allowed by it, and each repo's rules spec checks that the
  repo's settings contain it. When the repo capability system is extracted
  from the brain (`agent-tooling-137.1`), Beads policy moves into it and
  the canonical rule set becomes its input.
- **Conventions** live in two committed files, each fact in exactly one:
  `.beads/PRIME.md`, prose that `bd prime` prints at session start (it
  replaces bd's default text with a pointer to use-bd and states the
  project's conventions in words), and `.beads/bdw.json` (or
  `bdw-config.json` at the repo root, if bd does not tolerate the extra
  file), the structured facts `bdw` reads: the label scheme, extra document
  link keys, the docs inbox path. Neither may grant or limit anything an
  agent may do.
- **Labels** follow the scheme the repo declares; `bdw create` refuses
  unknown labels or a missing required category. Beads' own type field
  carries the Issue's kind, so labels carry only areas and the like.
- **Context outside the Issue Tracker.** If information makes sense in a
  requirements doc, a design doc, a UX design, an ADR, a lexicon entry, or
  any other standard document type the project uses, it goes there, and the
  Issue links to it through a metadata key per document type (e.g.,
  `requirements`, `design`, `ux`; the Skill defines the common keys, a repo
  may add its own). A filing agent need not know the repo's layout: it drops
  the material in the repo's docs inbox, and the same `bdw` Verb files a
  Leaf Issue to incorporate it, whose worker moves it to its proper home and
  updates every Issue that links to it. A repo with no docs home keeps such
  context in the Issue's description.
- **The Beads version.** `bdw` carries the bd versions it has been verified
  against, and the Skill's list of known quirks names the same version. On
  any other version `bdw` refuses writes and warns on reads; onboarding
  pins bd so it changes only deliberately. An upgrade re-verifies the
  quirks.
- **Upstream.** Agents offer to report Beads bugs, or contribute small
  fixes, upstream; they never do it on their own, and especially not during
  the trial. Unattended, they mention the bug in their final report.

## Identity and claims (version-one choices)

These are deliberate choices for version one, made around current
limitations rather than as lasting architecture; each is expected to change
when its limitation is lifted.

- **One Actor ID per session.** `bdw` derives the Actor ID from the
  session ID the harness sets (`CLAUDE_CODE_SESSION_ID`), for attended
  sessions and background jobs alike, and also sets the variable bd reads
  to record the closing session. Today's job-based ID is a prefix of the
  same value, so background jobs keep their IDs.
- **Sub-agents share their session's Actor ID,** because nothing in a
  sub-agent's environment distinguishes it from its parent
  (`agent-tooling-jk2`). So an agent without an Actor ID of its own reads,
  files new Issues, and appends, but never claims, closes, or rewrites; the
  session that holds the conversation does those. The Skill teaches this,
  and orchestrators' briefs carry it; `bdw` cannot enforce it.
- **A claim never outlives its session.** Before a session ends it closes
  or releases every Issue it claimed; continuity between sessions lives in
  the Issue (its pick-up note and metadata), never in a claim. Longer-lived
  agents would revisit this.
- **Work waiting on a human** (e.g., a PR in review) is released into a
  custom status that keeps it out of ready work, and the Issue records its
  branch and PR as metadata keys, which are structured and queryable,
  rather than as prose in its notes.

---

## Open items

**Frontier** of the home-in walk (Lines of Inquiry):

- Exhausted: Trigger, Success, Anti-goals, Stakeholders, Constraints.
- Untouched: Load-bearing assumptions (deep), Alternatives (deep),
  Reversibility and horizon (shallow), Pre-mortem (shallow),
  Disconfirmation (shallow).

**Resolution Queue:**

- Decision: `bdw` grows its own Verbs where policy needs them and passes the
  rest through, amending the decision that it execs `bd` with arguments
  untouched ([ADR 0002](../../adr/0002-beads-identity.md), Beads identity).
  Walk under Alternatives.
- Lexicon: whether bdw follows the Exit-code contract (settle with the
  `bdw` Verbs).
- Repair: `agent-tooling-aio` (the use-bd Issue) is a Branch Issue with an
  open child, so this session's claim on it is a pass that should end by
  breaking it down.
- Working name: *docs inbox* (the one place a filing agent drops material
  for the project's documentation); to be named at the Constraints exit.
- Carried forward, with where each is walked:
  - fixes in our layer stay easy, so `bdw` never grows into a spinoff
    (Load-bearing assumptions; evidence so far: the hierarchy rules match
    upstream's own conventions, and `bdw` must stay standard-library Python
    3.9);
  - Beads' native `human` label (`bd human list`, `bd human respond`) as an
    alternative to a custom status for work waiting on a human
    (Alternatives);
  - whether our own Verbs reuse bd's names (`bdw ready`) or get their own
    (decided as each is needed);
  - loading the Skill at the moment of need (Alternatives);
  - whether use-bd version one is already big enough to split
    (Alternatives);
  - formulas as phase-subtree templates (Alternatives);
  - to verify when building: whether `bd ready` excludes custom statuses,
    whether `--graph` accepts an existing parent, that `bdw` can read a
    parent's type cheaply, and whether bd tolerates `.beads/bdw.json`.
- To do in this change: rewrite the trial's stated question in
  `docs/projects/beads-trial/index.md` to the "Beads run well" framing, and
  note the attribution rule on `agent-tooling-0pe` (record the go/no-go
  verdict as an ADR).
