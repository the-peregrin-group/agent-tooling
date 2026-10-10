# use-bd: version-one proposal

Proposal, ratified 2026-10-09 in a home-in session (2026-10-07 to
2026-10-09). A point-in-time capture of the plan for version one of use-bd,
the Skill that teaches agents how this ecosystem uses Beads (`bd`) as its
Issue Tracker, through [`bdw`](../bdw/index.md), the Beads Wrapper. It is
being built in slices under `agent-tooling-aio` (the use-bd epic) and is not
updated as they ship: status and Issues are in [index.md](index.md), and the
Skill (`skills/use-bd/`) holds the procedure.

## Why use-bd exists

Beads' operating policy for agents is spread across `CLAUDE.md`, the README,
the Beads ADRs, the Permission rules' spec comments, the trial docs, and
the post-init checklist (`docs/beads-init.md`, since folded into the
Skill's `onboarding.md`), and works only if each is read
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
6. **Policy has one home.** Each rule is written once: its procedure in the
   Skill, its rationale in the project's design doc or an ADR; `CLAUDE.md`,
   the README, and the trial docs point to the Skill. Enforcement is
   separate from the prose: the Permission rules decide what an agent may
   run, and `bdw`'s own behavior carries what they cannot express.
7. **Organizational hygiene.** Work is broken down into Leaf Issues sized
   for one session, under Branch Issues for anything bigger, and the four
   relationships (dependency, contradiction, duplication, composition) are
   looked for when an Issue is filed.
8. **Labels follow the project's conventions.**

During the Beads trial, each entry in the friction log (`agent-tooling-w7p.4`)
names the criterion above it bears on, or "none" (a gap in the criteria),
so the verdict can read the log criterion by criterion. That is this repo's
trial convention, stated in its `PRIME.md`, not part of the Skill.

**Version one covers** the loop (prime, ready, claim, file discovered work,
append progress to the Issue, close, and land the plane: close or
release every claim before the session ends); the write rules; filing
discipline (breakdown, relationships, labels); pick-up notes (a summary
of where the work stands, for the next session to resume from, rewritten
in place rather than appended); and the known Beads 1.3.0 quirks. Onboarding a new repo is a supporting file inside the Skill,
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
  as one atomic batch (one graph plan through the filing Verb, previewed
  with a dry run; see "Filing is a plan file" below),
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
(templated trees) are not used for breakdown, which is the Branch Issue's
own pass; as templates for a Branch Issue's standard phases they are in
scope but deferred from the first shipment (`agent-tooling-sn6`, evaluate formulas as phase templates).

## How bdw carries policy

`bdw` carries the Beads policy that Permission rules cannot express, each
operation in the lightest tier that suffices (see
[ADR 0010](../../adr/0010-bdw-carries-beads-policy-in-tiers.md), bdw carries
Beads policy in tiers):

1. **Pass-through** when an operation carries no risk or special usage
   expectation: `bdw` sets the Actor and runs `bd` as a child process
   with the arguments unchanged (e.g., reads,
   setting `branch` and `pr` metadata).
2. **Thin intercept** when a feature needs wrapping without handling a
   combinatorial explosion of arguments: `bdw` reads the one or two flags
   it cares about, in the forms bd documents, and fails closed, refusing
   and naming the gap, on any command line it cannot read unambiguously
   (e.g., the echo after a blocking `dep add`, refusing a call whose first
   argument is a flag, refusing the flags that point bd at another
   database). File forms for every free-text field are `bdw`'s own added flags,
   turned into bd's inline flags by `bdw` itself.
3. **A Verb of its own** when the operation encodes a practice or process,
   or narrows a bd command so far that an intercept would duplicate much of
   its grammar; the raw `bd` commands it supersedes are denied (e.g.,
   `ready`, whose meaning changes, and dropping material in the Docs
   Inbox). Whether a Verb reuses bd's name or takes its own is decided per
   Verb.

`bdw` stays standard-library Python 3.9, like the other Wrappers, and its
list of verified bd versions covers every intercept and Verb, along with
the JSON shapes it reads.

**Filing is a plan file.** Creating structure (new Issues, their parents,
labels, and dependencies) is tier 3, because a parent, a label, or a
dependency can be set through too many of bd's commands for intercepts to
cover. Every filing goes through one `bdw` Verb that takes a graph plan,
the JSON `bd create --graph` understands (one Issue is a one-node plan).
`bdw` validates the plan before submitting it (parent kinds, labels against
the scheme, dependency types), searches for near-duplicates, releases the
claim on any Branch Issue the plan adds children to (ending the pass), and
echoes what left ready work; it validates JSON whose shape it controls instead of
parsing bd's command line. The plan is a file, so no free text reaches the
command line, and the submission is atomic and previewable, which makes
"draft, preview, submit" the only way to file. Every other path to
creating structure is denied (`create` in its other forms, `q`, `todo`,
`create -f`, `link`, `parent-child` dependencies through `dep add`).
Changing structure after filing (reparenting, labels, dependencies) gets a
thin intercept or the same plan mechanism, decided when built.

The filing Verb (`bdw file graph`) is one grant that covers every kind of
structural change, so prefix rules cannot grant some changes and not
others. That is a known gap, closed when a first need arises, preferably
by having `bdw` check a plan's contents against machine-level capability
policy once the capability system exists (`agent-tooling-137.1`): finer
than prefix rules, independent of Claude Code, and reusable beyond Beads.
Narrower Verbs, each grantable by its own prefix rule, are the fallback.

**Free text.** The Skill teaches the file forms as the default for every
text field. Inline text stays allowed; when it trips the harness's refusal
of text naming the VCS (in a worktree-isolated session, Claude Code refuses
a command whose inline arguments mention git, because it cannot show the
command is not a git operation outside the worktree;
`agent-tooling-doq`), or a deny rule matching a denied word, the
refusal happens before `bdw` runs, and the Skill tells the agent to switch
to the file form rather than reword.

## What must never happen

- **Command policy.** The Permission rules sort every Beads operation into
  three classes:
  - **Deny** what is irreversible, sends Issue data off the machine, or
    falsifies the record; and deny any raw `bd` command that a `bdw` Verb
    supersedes, so agents cannot take the old path out of habit. Since
    `bdw` forwards everything else to `bd`, that means denying raw `bd`
    and `beads` outright, reads included: agents touch Beads only through
    `bdw`, and the classes below apply to `bdw` calls.
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

  In this document, `bd <verb>` names a bd feature; agents reach it as
  `bdw <verb>`.

  Applied to bd 1.3.0's surface, in addition to the denies already in
  place (e.g., `edit`, `remember`, `delete`), bd's full command set gives:
  deny `epic close-eligible` (it closes epics because their children
  closed), `close --claim-next` and `--continue` and `ready --claim` (they
  claim around `bdw ready`), `memories` and `recall` (`bd prime` injects
  memories even with a custom `PRIME.md`), and the `link` command and the
  `new`, `done`, and `hb` aliases unless `bdw` maps them; ask for
  `unclaim --force` and `update --assignee` (taking over a claim, like
  `assign`), `orphans --fix` (it closes Issues), and `backup sync` (it
  pushes the whole database to the backup destination); allow `duplicate`,
  `supersede`, `defer`, and `undefer`. `bdw` refuses the global flags that
  point bd at another database (`-C`, `--db`, `--database`, `--global`)
  wherever they appear.
- **Unilateral relationships.** Agents add dependencies they find at filing
  time on their own; contradiction, duplication, and composition only when
  very confident, and otherwise raise them (or, unattended, report them).
  Because a wrong blocking dependency silently removes work from ready,
  `bdw` echoes what each new blocking dependency took out of ready work
  (built on `bd ready --explain`), so the mistake shows in the same turn;
  closing echoes what it unblocked (`close --suggest-next`). Before filing,
  agents search for near-duplicates themselves (`search`); the filing
  Verb's own near-duplicate check is a backstop, and `find-duplicates`
  sweeps after filing. The four relationships map to Beads' native ones:
  dependency to `blocks`, duplication to `duplicate --of`, composition to
  `parent-child`, and contradiction, which Beads has no type for, to
  `relates-to` plus a label naming the contradiction. Batch reconciliation
  is separate work (`agent-tooling-r6b`, automated batch triage).
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
- **No empty Issues.** `create.require-description` is on, so every Issue
  says what it is.
- **No barrier to capture.** Beads' section lint (`bd lint`) is
  type-dependent and, if enforced at creation, would refuse a bug filed
  before anyone knows how to reproduce it, inviting placeholder text. So
  `validation.on-create` stays off, and the filing Verb's dry run reports
  lint findings as warnings only. Rigor that arrives as an Issue moves
  through its lifecycle is separate work (`agent-tooling-c86`, a
  status-gated Issue lifecycle).
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
  into this repo (`agent-tooling-137.1`), Beads policy moves into it and
  the canonical rule set becomes its input.
- **Conventions** live in two committed files, each fact in exactly one:
  `.beads/PRIME.md`, prose that `bd prime` prints at session start (it
  replaces bd's default text with a pointer to use-bd and states the
  project's conventions in words), and `.beads/bdw.json` (or
  `bdw-config.json` at the repo root, if bd does not tolerate the extra
  file), the structured facts `bdw` reads: the label scheme, extra document
  link keys, the Docs Inbox path. Neither touches the Permission rules:
  `bdw.json` may steer what the `bdw` executable itself does (e.g., which
  labels the filing Verb accepts), but whether an agent may run an
  operation at all is decided only by the reviewed Permission rules.
- **Labels** follow the scheme the repo declares: every Issue has at least
  one area label and may carry others (e.g., Beads' own `human` label).
  The filing Verb refuses unknown labels or an Issue with no area label.
  An Issue's kind lives in Beads' type field, not in a label.
- **Context outside the Issue Tracker.** If information makes sense in a
  requirements doc, a design doc, a UX design, an ADR, a lexicon entry, or
  any other standard document type the project uses, it goes there, and the
  Issue links to it through a metadata key per document type (e.g.,
  `requirements`, `design`, `ux`; the Skill defines the common keys, a repo
  may add its own). An agent that knows where the material belongs under
  the project's conventions puts it there directly. One that does not drops
  it in the repo's Docs Inbox (see `LEXICON.md`), and the same `bdw` Verb
  files a Leaf Issue to incorporate it. Incorporating is a reading and a
  judgment, not a move: the item is moved and renamed into its proper home,
  folded into one or more existing documents, or discarded as already
  captured or outdated; the Issue records which, and why, before it closes,
  and every Issue that linked to the item is updated. A repo with no docs
  home keeps such context in the Issue's description.
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
  to record the closing session. A background job's ID is a prefix of
  its session ID, so Actor IDs that `bdw` derived from job IDs still
  identify the same sessions.
- **Sub-agents share their session's Actor ID,** because nothing in a
  sub-agent's environment distinguishes it from its parent
  (`agent-tooling-jk2`, sub-agents share their job's Actor). So an agent without an Actor ID of its own reads,
  files new Issues, and appends, but never claims, closes, or rewrites; the
  session that holds the conversation does those. The Skill teaches this,
  and orchestrators' briefs carry it; `bdw` cannot enforce it.
- **A claim never outlives its session.** Before a session ends it closes
  or releases every Issue it claimed; continuity between sessions lives in
  the Issue (its pick-up note and metadata), never in a claim. Longer-lived
  agents would revisit this.
- **Work waiting on a human** (e.g., a PR in review, a decision) is
  released and blocked by a native Beads gate (`bd gate`): a `gh:pr` gate
  that resolves when the PR merges, or a `human` gate that a person
  resolves. A gated Issue is out of ready work without any custom status.
  Anything that needs a human also carries Beads' native `human` label, so
  the maintainer has one queue (`bd human list`). A review closes through
  the normal close after merge, never through `bd human respond`, which
  closes the Issue at once.
- **Branch and PR.** The Issue records its branch and PR as metadata keys
  (`branch`, `pr`): the one current answer, structured and queryable.
  Beads' provenance log (`bd provenance`) supplements them with the
  history of branch, PR, and commit events; it does not replace them, as a
  stream never replaces the state it records.

## Getting agents to load use-bd

Agents often load an operating-manual Skill only when they feel the need,
despite instructions, so use-bd's loading is pushed from several sides:

- the Skill's description and trigger phrases;
- `.beads/PRIME.md`, which `bd prime` prints, pointing to use-bd;
- every help output and usage error from `bdw` saying "Agents, load
  `/use-bd` immediately." (which is why `bdw` runs `bd` as a child process
  and reads its failures, rather than replacing itself with `bd`);
- the Permission rules denying raw `bd`, so the habit fails at once;
- once agent-tooling can ship hooks (`agent-tooling-0s1`, not yet built): a SessionStart hook
  that has the agent load use-bd in any repo with a `.beads/` directory
  (`agent-tooling-0s1.5`), and a hook that refuses raw Beads calls with a
  message pointing to use-bd and `bdw` (`agent-tooling-0s1.6`).

A per-session reminder printed by `bdw` was rejected. The help line is a
fixed string of about ten tokens, with no logic or state, so it costs
nothing even though its effect is small. A once-per-session reminder needs
a mechanism (state that tracks what a session has seen, keyed to how
Claude Code identifies sessions), which adds complexity and can break when
Claude Code changes, for an effect no larger.

## The Skill's shape

One Skill, with supporting files read only when needed, so the part every
load pays for stays small:

- `SKILL.md`, read on every load: the loop; the write, hierarchy, and claim
  rules; free text through files, and what to do when refused; filing
  discipline (breakdown, the four relationships, labels, the Docs Inbox);
  working a Branch Issue in passes; landing the plane.
- `onboarding.md`: setting Beads up in a new repo (the canonical rules,
  `PRIME.md` and `bdw.json`, pinning bd), read by whoever onboards.
- `quirks.md`: the known behaviors of the verified bd version, read when bd
  surprises an agent or is upgraded.
- The canonical Beads rule set, as data the tests read.

Splitting into sibling Skills (e.g., a separate setup Skill) belongs to the
skill-family work (`agent-tooling-u9n`).

## Decided in its slice

This proposal deliberately leaves these interface choices to the slice that
builds them, where they can be settled against working code:

- Which Issue types count as branch kinds beyond the epic, and whether a
  Branch Issue with no open children but an open blocker is ready work
  (`agent-tooling-aio.4`, `bdw ready` and the pass rules).
- How structure is changed after filing (reparenting, labels,
  dependencies): a thin intercept or the plan mechanism; and how a Branch
  Issue that is not of a branch kind is detected for repair
  (`agent-tooling-aio.5`, the filing Verb).
- The config file's name and place (`.beads/bdw.json` or a repo-root
  file), its schema, and the label scheme's format; the names of the file-form flags; and the Docs Inbox Verb's
  name (`agent-tooling-aio.6`, config, label checks, file forms, Docs
  Inbox).
- Whether `link` and the `new`, `done`, and `hb` aliases are mapped or
  denied (`agent-tooling-aio.3`, the canonical rule set).
- The variable `bdw` sets so bd records the closing session
  (`agent-tooling-aio.2`, bdw hardening).

## What would change this design

The design's core bet is enforcing simple rules in `bdw`, with refusals
that teach, rather than relying on the Skill's text. The evidence that
would most argue against it is an inability to teach agents to use `bdw`
successfully over time: agents routing around `bdw` despite the denials,
the help line, and the Skill; the same refusal hit again and again across
sessions; agents reporting the Issue Tracker as awkward even when they
comply; or friction under the first two success criteria (no prompts, no
workarounds) caused mostly by our own refusals rather than by Beads. So the
Skill asks agents to log a friction entry when a `bdw` refusal surprised
them, and to say in their final report anything about the Issue Tracker
that felt awkward. The cost of bd upgrades is not such evidence: upgrades
are optional, taken only when a release is worth re-verifying.

The likeliest failures, as foreseen: Beads proving too volatile, or its
values diverging from ours (both verdict evidence, softened by the version
pin and by keeping our concepts tracker-agnostic); the system proving too
opinionated for agents (the bet above); the build never finishing (so it
ships in thin slices, each useful alone); and, during the local-only trial,
losing the single copy of the database (`agent-tooling-mfs`, snapshots to
the maintainer's NAS).

