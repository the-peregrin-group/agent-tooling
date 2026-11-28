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
reads, each fact in exactly one place), and what the block holds beyond its
first keys in
[ADR 0027](../../adr/0027-the-tracker-schema-block-holds-state-order-entry-state-close-reasons-and-colours.md)
(the block also holds the state order, the Entry State, the Close Reasons,
and every colour); the other three did not clear the ADR gate and are
recorded here, each with the options rejected.

### Format

The file is Markdown with one fenced JSON block. Each fact lives in exactly
one place. The JSON block holds:

- the Issue Kinds, each with its meaning and colour;
- the Issue Priorities, highest first, each with its meaning, staleness
  threshold, and colour;
- the Issue Label Schema: its axes, and each label, on an axis or on none,
  with its meaning and colour. A repo's own labels that take no prefix are
  labels on no axis, so they need no key of their own;
- the Issue States, in Issue State Diagram order, each with its open or
  closed flag and colour, and exactly one open state flagged as the Entry
  State;
- the Close Reasons, each with its meaning;
- the provenance.

The prose holds the state meanings and the transition conditions, keyed by
state name, and the condition for giving each Close Reason, keyed by the
reason's name. A fact moved into the block leaves the prose: the prose
names no Entry State and does not hold the order, and only describes its
states in the block's order. JSON, because the Wrappers run on the system
Python 3.9 with the standard library only, which parses JSON and neither
TOML nor YAML. Rejected: pure Markdown prose (Wrappers would parse prose),
and a pure JSON file (multi-paragraph mini-prompts in JSON strings are poor
to write and review).

A colour is six hex digits with no leading `#`, the form labels take on
GitHub and Forgejo, and it is declared like a
description: a sync makes the tracker's colour match the file's, and a
repo that wants other colours changes its `TRACKER.md`. Where the file's
colour for an entry is missing or bad, a Wrapper warns, leaves a live
colour as it is, and gives a neutral default only to a label or option it
must create. Where a tracker offers only a few named colours (a GitHub
project board's options take one of eight), the Wrapper that writes there
shows the nearest, so the file holds one form for every platform. The
shipped default's colours are the ones the labels of repos already set
up with ghw carry, where such a label exists, and
for the states hex values chosen to read as the board colours ghw gives
those states before the board followed the schema, so that the first sync
from the schema need change little; what "nearest" means is the board
Verb's to define, and the ghw design states its rule
([Colours](../ghw/design.md#schema-sync-bootstrap-grade-declarative)).
Rejected, with ADR 0027: a colour
rule in the Wrappers, and colours set on creation only; both make colour a
special case unlike every other part of the schema.

The block uses the same marker convention as `TRIAGE.md`'s config block:
two HTML comment marker lines naming `tracker-schema`, with one fenced
`json` block between them. The matching rule is stricter than that
precedent's: a reader matches each marker as a whole line, so prose that
mentions a marker cannot be mistaken for one, and the fence lines are
exactly `` ```json `` and `` ``` ``, one of the several spellings of a
`json` fence that Markdown allows, so there is one form to write and check.
Trailing whitespace and a CRLF line ending do not stop a line from
matching, since neither can turn prose into a marker and both are easy to
introduce unseen; indentation does, since an indented line can be a code
block or part of a list item in Markdown, so an indented marker line is an
example, not a marker. Rejected: matching only an exact line (it refuses a
file over an invisible trailing space that changes nothing), and stripping
both ends (it would take a marker inside an indented example for the real
one). The written rule is the one form a file should have, and the
validity test holds this repo's files to it; the reader is more tolerant
(see the next section), so a repo whose file strays from it in a way that
leaves the block plain to see still has its schema read. The file itself
states the rule and what each key holds, since it is the only context a
repo's agents have.

### The reader

`cli/lib/tracker_schema.py` is the one reader of the block, for every
Wrapper that follows a repo's Tracker Schema. It degrades gracefully: a
defect in a repo's file never stops what the file's valid data can still
support, and it is always reported. The maintainer ruled this on
2026-11-25, and it shapes everything below.

- **Whole-file failure only for an unclear block.** The file fails as a
  whole only when it is unclear which block is meant (a marker missing or
  repeated, END before BEGIN, no fence or two between the markers, a fence
  never closed) or the block's JSON does not parse. A file that strays
  from the delimiting rule but whose block is plain to see (an indented
  copy of a marker, a fence spelled another way, a stray line beside the
  fence) is read, with a problem for each stray.
- **Section by section.** Otherwise the reader always returns a result.
  It reads each section on its own: provenance, kinds, priorities, label
  axes, unaxed labels, states, and Close Reasons. A caller that asks for an
  unusable section gets an error for that section alone. A caller that
  never asks is unaffected.
- **Keep what is sound.** Within a section, a bad entry is left out and the
  rest kept. A bad descriptive field (a meaning, a colour, a staleness
  threshold) reads as absent, and so does a missing one; a colour is
  treated exactly like a meaning. A flag a caller acts on (a state's open
  flag, an axis's required flag) is never absent: an entry whose flag is
  bad is left out, so no caller can take an unknown flag for false. A key
  the reader does not know is ignored, and a key it needs but cannot find
  leaves that field or section absent. So a repo's copy written for a
  newer reader, and one written for an older reader, both keep everything
  else working. The reader is updated whenever the block's shape changes.
- **Order survives a lost entry.** The priorities and the states are read
  in file order, and leaving an entry out keeps the others' order relative
  to each other, which is all the order means.
- **The Entry State is unknown, not guessed.** The entry flag picks one
  state out of the list rather than describing each, so its defects are
  handled apart from the open flag's: no state flagged, more than one, a
  flag that is not true or false, the flagged state left out, or a closed
  state flagged all keep every state and leave the Entry State unknown
  (`entry_state` is None), with a problem on the states that is not lossy,
  since no state is lost. So the states can still be complete, and only a
  caller that needs the Entry State, such as filing that sets it, stops,
  and only for that need; a board sync that needs the states complete but
  never the Entry State goes ahead. A state with no entry key is simply
  not the Entry State, since only one state carries it.
- **Conflicts lose only the entries in conflict.** Where entries contradict
  each other, every entry involved is left out and the rest kept:
  - a priority listed twice, since it would have no one rank;
  - a state listed twice with opposite open flags;
  - axes that share a name, or whose prefixes overlap, since which axis a
    label sits on would depend on list order. Their prefixes still keep
    labels out of the unaxed labels.

  A name listed twice where nothing hangs on which entry is kept (a kind,
  a label, a Close Reason, a state flagged the same way twice) keeps one
  entry, the first whose fields all read.
- **Unusable as a whole only where nothing can be kept safely:**
  - provenance with any bad field, since its fields are used together as
    one diff target;
  - a section that is missing, written twice, or not a list;
  - every section inside a block, or an `issue_label_schema`, that is not
    a JSON object;
  - kinds, priorities, states, or Close Reasons with no usable entry left,
    since an empty list would make every Issue, or every close,
    nonconforming.
- **Usable is not complete.** Each problem says whether it is lossy: the
  reader dropped or doubted data the file meant to declare. An unknown key,
  partly-null provenance, a stray from the delimiting rule, or an unknown
  Entry State loses nothing. A missing or bad colour, like a missing or bad
  meaning, is lossy. A section is complete when it is
  usable and has no lossy problem. The unaxed labels are in doubt, and so
  not complete, when an axis's prefix could not be read, since a label
  among them may belong on that axis.
- **Older copies.** A copy written before the entry flag, the Close
  Reasons, and the colours existed still reads: its kinds, priorities,
  labels, and states are usable, with a warning for each missing colour
  and for the unknown Entry State, and its Close Reasons are unusable.
  Since a missing colour is lossy, none of those sections is complete
  until the copy declares its colours, so a destructive sync waits for
  that edit, as it would for a missing meaning.
- **Ambiguous names are flaws.** Beyond the documented shape, the reader
  treats as a flaw anything that would make a tracker's reading ambiguous:
  - two names that differ only in case, since GitHub matches label names
    case-insensitively, and kinds, priorities, and states can become
    labels or board options;
  - axis prefixes where one begins another;
  - names holding control or invisible characters.
- **Every flaw is reported.** Each flaw is a problem on the result.
  `warning_lines` turns the problems, or a whole-file failure, into one
  stderr warning each, naming the file, the key path at fault, and what is
  wrong and what was done about it, so every Wrapper warns in the same
  words. Nothing from the file reaches a warning unescaped, so a file
  cannot forge a warning line or send terminal escapes.
- **No exit codes.** The library makes no exit-code decisions; the rule
  below is the callers'.

It does not reuse the triage scripts' `lib_profile.py`, which matches its
markers by substring, so prose that mentions a marker can be taken for
one. Rejected:
- refusing the whole file on any unknown, missing, or malformed key. Any
  drift between a repo's copy and the installed Wrappers would then stop
  every Verb in that repo, including Verbs that need nothing from the
  schema, and an agent would be sent to fix a file that was correct;
- refusing the whole file whenever it strays from the delimiting rule,
  when the block is still plain to see; that would stop every Verb over a
  stray the reader can name and step past;
- making a whole section unusable when some of its entries conflict.
  Completeness already keeps a destructive write off such a section, so
  refusing the rest would only stop additive writes it still supports;
- keeping a state or axis whose flag is bad with the flag absent, since a
  caller testing the flag as true or false would take absent for false;
- leaving out a state whose entry flag is bad, or every state flagged as
  the Entry State, as the open flag's rule would; that loses states over a
  fact about one of them, when an unknown Entry State is easy for a caller
  to test for;
- reading the first state flagged, or the first state listed, as the Entry
  State when the flags do not name one plainly, since filing an Issue in
  the wrong state is the guess the flag exists to prevent.

The reader reads none of the prose. Whether a file's prose and block agree
is checked by a test over the shipped default and this repo's copy, not by
the reader, because the prose's headings are written for people and agents
and a repo may arrange its own copy's prose differently. The test checks
that the meaning sections and the "Out of" sections name the block's
states in the block's order, and that the conditions under "Into Closed"
are keyed by exactly the block's Close Reasons. The same test is where
strictness lives: both files must read with no problem at all, so each
names exactly one Entry State and gives everything that takes a colour its
colour.

### How a Wrapper uses the schema

The maintainer ruled on 2026-11-25 how a Wrapper finds a repo's Tracker
Schema and what it does when the schema is missing or broken
(`agent-tooling-u9n.19`).

- **Where it is read.** The ghw and fjw Verbs read `TRACKER.md` from the
  repo's default branch on the forge. No local file is an input to any
  Verb, so a change to a repo's labels or states goes through the repo's
  own review: change `TRACKER.md` and merge it, then sync. bdw reads the
  `TRACKER.md` of the workspace it stands in, which is the repo whose
  `.beads/` it already uses. Reading it costs a ghw or fjw Verb one more
  forge request per call; how to keep that cost down is left to the
  Verbs that read it.
- **When data a Verb needs is missing or unusable** (the repo has no
  `TRACKER.md`, the forge cannot be reached to fetch it, or the section the
  Verb's check needs cannot be used):
  - Reads, and writes that need nothing from the schema (orient, a
    comment, a link), always work.
  - Additive writes whose schema check cannot run (filing an Issue,
    attaching a label) go ahead on what can still be verified, such as the
    label existing on the forge.
  - Destructive writes (a label sync deleting labels, a board sync
    removing options) are refused unless every section they derive from is
    complete, not merely usable (`require_complete`), naming the problem.
    A usable section may have lost entries, and a lost entry would
    otherwise read as one to delete.
- **Warnings.** In all three cases, every problem found in `TRACKER.md`
  is printed as a warning, even when nothing is blocked, so the defect is
  visible to people and agents alike.

Rejected:
- reading from the checkout the session stands in, since the answer would
  depend on which branch is checked out, and a ghw Verb is not bound to a
  checkout;
- a path argument, and a file that label sync accepts for setup, since
  either lets a local file change a repo's labels without its review;
- falling back to the shipped default when a repo has none, since the
  default's area axis lists no labels, so every check against it would
  fail, and a Wrapper would have to read a file from the Skills;
- refusing every Verb when a repo has none, since most Verbs need nothing
  from the schema.

The triage pass's rule under triage-issues, below, is for an agent's
judgement, not for a Wrapper. That rule is to read a repo with no schema
against the default's diagram, and say so.

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
change to the Install Manifest. Rejected:
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

The default is one platform-neutral file. Every sentence in it must read
true in an untouched copy on any Issue Tracker, so what depends on the
platform or on the repo is written as a condition ("once the repo's Beads
holds these states", "while the axis lists none") instead of as a fact
about the shipped default, and it names no Issue ID or requirement number,
which a copy's readers could not look up. It has no key marking which kind
holds children, because an Issue is a Branch Issue by what it holds or is
meant to hold, not by its kind. Rejected: one variant of the default per
Issue Tracker (the diagram would exist in several copies that drift); a
sentence calling the kinds and priorities a starting set (false in a copy
that has adopted them, and the file already says every edit is the repo's
customization).

The listed Issue Kinds and Issue Priorities fit GitHub's labels. Replacing
them with the kinds and levels the repo's own tracker has is the setup
skill's step when it copies the file (`agent-tooling-u9n.9`, write
setup-issue-tracker).

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
three fields are `null`, since it is not a copy, and the reader's test
holds it to that.

When the Receipt's commit is `-dirty` or unknown, setup stops and says so
rather than recording a revision that cannot be diffed against.

### This repo's own copy

This repo's Tracker Schema is [`TRACKER.md`](../../../TRACKER.md), the
first copy of the default. It was copied by hand, before any setup skill
did the copy, and this repo is itself the source repo: its `source_commit`
is the commit on `main` whose default it follows, not a Receipt's commit,
and it moves forward by hand when the copy takes what the default changed
since. What it changes from the default is a diff of the two files. Its
Issue State Diagram is the default's as of that commit except its last
section, which says how much of an Issue State the
Beads status records today, which is open or closed and whether a claim is
held; holding the states themselves on Beads is
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
  priority's `stale_after_days`. The earlier Skill exempted its Entry
  State, because every pass screened every Issue there. An Issue that
  lingers in the Entry State past its threshold is one screening
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
text names no platform; each platform's mechanics are a file beside it,
read on demand: `beads.md`, `github.md`, and `forgejo.md`.

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
  then tailors the copy to the platform, as the platform file says: the
  owner designates what the default leaves open, the kinds and priority
  levels become the tracker's own where it has built-in ones, and the Area
  Labels are filled in. Trimming the lines for other platforms is
  optional. The default's kinds and
  priorities are proposals, not mandates. Rejected: per-platform variants
  of the default (each would drift from the others, and the default is
  written to read true on any platform).
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
  Rejected: setup editing a notes vault the repo does not own. The plan
  says what to tell that owner instead.
- **Judgement over recipes.** The backlog's sources and the plan's shape
  depend on the repo, which may not be code, and the day-to-day
  conventions belong to the platform Skill that enforces them. Rejected:
  fixed recipes in the setup text (a grep for TODO comments, an optional
  code review to find more work, plan tables with set columns, a recited
  list of conventions).

Where the platform steps live: every platform's, Beads included, in a
file beside this Skill, so one Skill holds all of setup. A platform file
says which steps an agent runs through the platform's Wrapper and which
are the owner's, since what a Wrapper can do differs by platform: on
Beads most of setup is raw `bd` calls, which the canonical rules deny to
agents, and machine configuration, which is the owner's. A file may point at what its
platform Skill owns (the Beads steps at `rules.json` and `quirks.md` in
`use-bd`'s directory) rather than copy it. Rejected: `use-github/setup.md`,
which the [proposal](2026-11-13-proposal.md) named for slice 5 as a
waypoint until this Skill existed; with the Skill shipped, the steps go
straight to their home beside it. Also rejected: one setup Skill per
platform, which repeats the procedure and lets the copies disagree; and
keeping the Beads steps in `use-bd` beside the canonical rules they
install, which would make Beads the one platform whose setup lives
outside the setup Skill. The rules test reads the steps wherever they live.
