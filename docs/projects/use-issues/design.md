# use-issues design

How the shipped parts of the Issue Tracker skill family work and why. What
is shipped is in [index.md](index.md). The Tracker Schema file,
`work-issue`, `triage-issues`, and `setup-issue-tracker` are described here
so far; the design of everything not yet built is in the dated
[proposal](2026-11-13-proposal.md), and each slice carries its part into
this document when it lands.

## The Tracker Schema file

Every repo carries its own full copy of the Tracker Schema, bootstrapped
from the shipped default
([ADR 0020](../../adr/0020-every-repo-carries-its-own-copy-of-the-tracker-schema.md),
every repo carries its own copy of the Tracker Schema), and its Issue State
Diagram holds every state meaning and transition condition in natural
language
([ADR 0019](../../adr/0019-issue-lifecycle-semantics-live-in-the-issue-state-diagram.md),
lifecycle semantics live in the Issue State Diagram). The maintainer ruled
on the file's format, its path in a repo, where the shipped default lives,
and its provenance on 2026-11-13. The format is recorded in
[ADR 0025](../../adr/0025-the-tracker-schema-is-one-markdown-file-with-one-json-block.md)
(the Tracker Schema is a Markdown file with one JSON block for what tooling
reads, each fact in exactly one place); the other three did not clear the
ADR gate and are recorded here, each with the options rejected.

### Format

The file is Markdown with one fenced JSON block. Each fact lives in exactly
one place: the JSON block holds the Issue Kinds, the Issue Priorities with
their staleness thresholds, the Issue Label Schema, each Issue State's name
with its open or closed flag, and the provenance; the prose holds the state
meanings and the transition conditions, keyed by state name. JSON, because
the Wrappers run on the system Python 3.9 with the standard library only,
which parses JSON and neither TOML nor YAML. Rejected: pure Markdown prose
(Wrappers would parse prose), and a pure JSON file (multi-paragraph
mini-prompts in JSON strings are poor to write and review).

The block uses the same marker convention as `TRIAGE.md`'s config block:
two HTML comment marker lines naming `tracker-schema`, with one fenced
`json` block between them. The matching rule is stricter than that
precedent's: a reader matches each marker as a whole line, so prose that
mentions a marker cannot be mistaken for one. The file itself states the
rule and what each key holds, since it is the only context a repo's agents
have.

### Path

In a repo, the Tracker Schema is `TRACKER.md` at the repo root, the same
convention as `LEXICON.md` and `TRIAGE.md`, found with no configuration on
any platform. Rejected: a dot-directory (hidden from people browsing the
repo, and this file is meant to be read and edited); a path under `docs/`
(repos lay out their docs differently, so finding it would need
configuration); and the tracker's own directory such as `.beads/` (it ties
the schema to one tracker, and GitHub and Forgejo have no such directory).
This answers `agent-tooling-wx5`
(one canonical per-repo config home) for the schema. `TRIAGE.md`'s config
block is not folded into this file's JSON block: it holds one board's
opaque GitHub IDs, which only the GitHub triage scripts read, and that
Issue stays open for what becomes of it.

### The shipped default

The default is [`TRACKER.default.md`](../../../skills/setup-issue-tracker/TRACKER.default.md)
in the setup skill's directory, so it ships in the skills Cohort with no
change to the Install Manifest. It started in `skills/setup-github-issues/`
and moved when `setup-issue-tracker` replaced that skill. Rejected:
`skills/know-issues/` (setup is the only thing that copies the default, so
it belongs with setup); `cli/lib/` (the default is a document agents read,
not code, and that directory ships in a different Cohort); and a new
top-level directory with its own Cohort (a change to the Install Manifest
for one file).

The default is written to read true both as the original and as a repo's
copy, because setup copies it whole: it calls itself "this repo's Tracker
Schema" and names no path of its own. Its content (the default Issue Kinds,
Issue Priorities, Issue Label Schema, and Issue State Diagram) is in the
file and is not repeated here.

Where an Issue State is recorded on a forge with no status mechanism is
left open in the default, per platform, until `agent-tooling-vb2v` (where
an Issue State is recorded on forges with no status mechanism) decides it.

### Provenance

A repo's copy records, in the JSON block, the source repo, the full commit
from the Installer's Receipt (`source_commit`), and the default's path at
that commit, so "what has the default changed since" is a diff of that path
at the recorded commit against the default as it is now. The path is
recorded, not assumed, because the default can move: a copy made before it
moved to `skills/setup-issue-tracker/` records its old path in
`skills/setup-github-issues/`, which still resolves at the recorded commit.
Rejected: a hand-bumped revision number (someone has to remember to bump
it, and a number cannot be diffed against), and a content hash (it shows
that the default changed but not what changed). In the shipped default the
three fields are `null`, since it is not a copy.

When the Receipt's commit is `-dirty` or unknown, setup stops and says so
rather than recording a revision that cannot be diffed against.

### This repo's own copy

This repo's Tracker Schema is [`TRACKER.md`](../../../TRACKER.md), the
first copy of the default. It was copied by hand, before any setup skill
did the copy, and this repo is itself the source repo: its `source_commit`
is the commit on `main` that last changed the default, not a Receipt's
commit, and its `default_path` is the default's old path under
`skills/setup-github-issues/`. What it changes from the default is a diff
of the two files. Its Issue
State Diagram is the default's, and its last section says how much of an
Issue State the Beads status records today, which is open or closed and
whether a claim is held; holding the states themselves on Beads is
`agent-tooling-c86` (status-gated Issue lifecycle on Beads).

## work-issue

`work-issue` covers two moments in one Skill: doing the work an Issue
tracks, and changing an Issue. It carries no state semantics. Every move
is judged against the repo's Issue State Diagram, so the Skill and the
diagram cannot disagree. Finished work has three outcomes (close, hand to
review, release), and what review a piece of work needs, if any, is left to
the judgement of whoever did it.

### The Lands and Advances trailers

A commit or PR names the Issue it serves in a git trailer: `Lands:` when,
with that change in, the Issue's criteria hold, and `Advances:` when more
remains. Each commit and each PR is judged on its own. Rejected: only the
PR lands and every commit advances (it binds the trailer to PRs, which some
repos do not have, and GitHub's default merge message drops the PR body, so
git history would carry no `Lands:` at all). The cost accepted is that a
fix-up after a `Lands:` commit says `Lands:` again, which is harmless
because neither trailer closes anything.

On GitHub, `Closes #N` goes in the text above the trailers, because git
reads no trailer from a paragraph that holds any other line. The colon form
`Closes: #N` among the trailers also parses and was not chosen; the bare
keyword is GitHub's documented form.

### What the Skill leaves out until the tooling exists

- **Status moves on GitHub.** Until a repo has a Tracker Schema, a session
  makes only the moves its own work causes (claimed, released, finished)
  and leaves every other move to a triage pass. Rejected: judging moves
  against the conditions `triage-issues` documented at the time, which
  would have made its older eight-state model the working diagram for
  every GitHub repo.
- **A free status change on Beads.** Beads holds only its own statuses
  until `agent-tooling-c86` (status-gated lifecycle on Beads) lands, so
  there is no diagram to judge `bdw update --status` against, and the flag
  can set in progress without a claim and blocked in place of a gate. The
  Skill teaches only the moves a claim, a release, a close, and a reopen
  make.
- **The claim protocol on a forge.** A claim on GitHub is a plain comment
  until `ghw` has the Verb (`agent-tooling-fyxo`, ghw issue Verbs on the
  shared grammar). The lease, the Actor ID, and the assignee's role are
  designed with that Verb, not ahead of it.

## triage-issues

`triage-issues` is the batch pass over the whole tracker. Its generic text
names no platform and no state; a pass is read against the repo's Tracker
Schema, and each platform's mechanics are one section at the end of the
Skill. GitHub's are the six `triage-*` scripts, documented under
[ghw](../ghw/design.md#triage-on-github).

- **No state model of its own.** The Skill's eight-state table, transition
  list, and per-state playbooks are gone
  ([ADR 0019](../../adr/0019-issue-lifecycle-semantics-live-in-the-issue-state-diagram.md),
  lifecycle semantics live in the Issue State Diagram). The pass checks
  each recorded state against the diagram in both directions and says
  nothing more about states, so a repo that changes its diagram changes
  what triage does without touching the Skill.
- **No autonomy boundary of its own.** What a pass may do on its own is the
  Permission rules it runs under. The Skill carries discipline only: be
  liberal with priority and conservative with state, comment rather than
  rewrite, say why on the Issue, and never try another path to a denied
  act.
- **A pass checks; it does not work.** Scoping and engineering design used
  to be interactive steps of a triage pass. They are work on one Issue,
  done by whoever claims it, so they left triage.
- **The human queue is on the Issues.** What needs a person is a comment on
  the affected Issue with the `human` label. The digest is a kind-`meta`
  Issue whose body is the current report and whose comments are the log of
  passes. Because findings live on the Issues, the tracker is the pass's
  memory: the body is read back from the `human` queue each pass, and a
  finding is not repeated while it stands. That replaced the ledger's
  finding identities, carry-forward, aging, and dismissal section. The
  one exception today is an unattended GitHub pass, which can neither
  write to the affected issue nor read bodies, comments, or its own
  digest: it lists findings in the digest and derives them afresh each
  pass (`agent-tooling-u9n.13`, `agent-tooling-u9n.14`).
  Rejected: the ledger as the queue (a person resolves a finding on the
  affected Issue, and a copy in the ledger goes stale with every change to
  that Issue).
- **Staleness has no exempt state.** Every open Issue is judged against its
  priority's `stale_after_days`. The earlier Skill exempted its entry
  state, because every pass screened every Issue there. An Issue that
  lingers in the default entry state past its threshold is one screening
  could not move and nobody has fixed, which is what staleness is for, and
  the rule needs no state name.
- **Judgement over enumeration.** The earlier Skill enumerated cases (split
  and group gates, consequence rubrics, linkage keyword lists, report entry
  formats, distribution thresholds). The Skill is used in repos that are
  not code, and the enumerations kept disagreeing with the diagram, so it
  now states each rule once, plainly, and leans on the agent's judgement.

A repo with no Tracker Schema file yet is read against the shipped
default's diagram, and the digest says so. What the GitHub scripts still
assume, and what a pass on Beads lacks, are Known gaps in
[index.md](index.md) and [ghw's index](../ghw/index.md#known-gaps).

## setup-issue-tracker

`setup-issue-tracker` sets a repo's Issue Tracker up on any platform. Its
text names no platform; each platform's mechanics are a file read on
demand: `github.md` and `forgejo.md` beside the Skill, and `use-bd`'s
`onboarding.md` for Beads. It replaced `setup-github-issues`, whose
still-true GitHub steps became `github.md`.

- **The owner approves the whole plan first.** Setup is a human
  procedure: confirm the target, draft one plan covering the Tracker
  Schema, Forge identities, the tracker's structure, the backlog, the
  retirement of each source, and the pointer in the repo's agent
  instructions, and change nothing until the owner approves it. The
  schema is the owner's design even when an agent drafts it. Whether an
  agent may act as an owner is a Permission rule, not the Skill's reading.
- **A whole copy of the default, tailored.** Setup copies the shipped
  default whole and records its provenance
  ([ADR 0020](../../adr/0020-every-repo-carries-its-own-copy-of-the-tracker-schema.md)),
  then tailors the copy to the platform: only the repo's own platform where
  the copy says where a state is recorded, the tracker's own kinds or
  priority levels proposed where it has them, and the Area Labels filled
  in. The default's kinds and priorities are proposals, not mandates.
  Rejected: per-platform variants of the default (each would drift from
  the others, and the default is written to read true on any platform).
- **Forge identities: what exists today, and what waits.** Setup registers
  a repo's Forge identities and gives the machine account access
  ([ADR 0018](../../adr/0018-every-forge-operation-names-its-forge-identity.md)).
  No Wrapper registers identities yet, so the platform files say what
  exists (ghw acts as `gh`'s account; fjw has one machine account in its
  Machine Config, given access by the owner in the forge's settings), and
  the plan says what has to wait. Registration is a Verb or the owner's
  own edit to Machine Config, never an agent's improvised one.
- **One verdict per item, one plan, one filer.** A backlog is converted by
  giving every item one verdict and keeping its source, then writing one
  deduplicated plan the owner reviews, which one filer files serially.
  Rejected: filing while auditing (nothing is reviewed and duplicates
  across sources survive), and several filers at once (relationships
  cannot be recorded in order, and duplicates race).
- **Each source is retired by its owner.** A source the repo owns may be
  removed or replaced with a pointer once every item has a verdict; a
  source owned elsewhere changes only through its owner's channel.
  Rejected: setup editing a notes vault the repo does not own, which
  `setup-github-issues` did. The plan says what to tell that owner
  instead.
- **Judgement over recipes.** `setup-github-issues` carried fixed recipes:
  a grep for TODO comments, an optional code review to find more work,
  plan tables with set columns, a priority count, and a list of
  conventions to recite. They are gone. The backlog's sources and the
  plan's shape depend on the repo, which may not be code, and the
  conventions belong to the platform Skill that enforces them.

Where the platform steps live. Rejected: `use-github/setup.md`, the
interim home the [proposal](2026-11-13-proposal.md) named for slice 5,
since `use-github` is shrinking to a failsafe pointer and its directory
should not carry a procedure only setup reads; and one setup Skill per
platform, which repeats the procedure and lets the copies disagree.
`use-bd`'s `onboarding.md` stays where it is because the canonical Beads
Permission rules it installs live beside it, and the rules test reads it
there for the commands it teaches.
