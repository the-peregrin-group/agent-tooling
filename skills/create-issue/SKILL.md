---
name: create-issue
description: >
  File an Issue on any Issue Tracker (Beads, GitHub Issues, Forgejo issues):
  search open and closed Issues first and let what is found decide the next
  step; meet the filing bar (a title that states the outcome, a body that
  says what is known and what is not, and a kind, a priority, and the entry
  state, each set as best you can); take kind, priority, and labels from the
  repo's Tracker Schema; record every relationship with its type explicit;
  say where the Issue came from; refine what you filed. Load before filing
  an Issue, and when work in progress turns up other work that needs doing.
  Triggers: "file an issue", "file a bead", "open an issue for this", "is
  there an issue for this", "track this", "what kind or priority is this".
  EXCLUDE: claiming, working, or closing an Issue, and breaking down a
  Branch Issue (the platform's skill: use-bd, use-github); a triage pass
  over the whole tracker (triage-issues); setting a tracker up.
---

# Create Issue

The moment of filing an Issue, on any Issue Tracker. The discipline is the
same everywhere and only the commands differ, so this skill is written
against no platform: where a step needs a command, run your wrapper's help
for this Verb. Until each wrapper's help carries its own usage, the last
section lists today's spellings.

The procedure says what must be done, not who may do it. What you may do
yourself is decided by the repo's Permission rules: if the grant exists, do
the act; if not, the call is denied or asked, and that is the answer. Fix
the call or report the gap, and never look for another spelling or reword
the text to get past it.

## When to file

- Proactively file Issues for needed work discovered in the course of other
  work; do not leave it undocumented or deferred to "future sessions".
- Capture is never blocked: file with what you know and say honestly what is
  unknown, never with placeholder text. No Issue is empty.

## 1. Search first

Before filing, search open and closed Issues for overlap or contradiction.
What is found decides the next step:

- **A dependency:** file the Issue and link the dependency.
- **A duplicate:** add any missing context to the existing Issue rather than
  filing a new one.
- **A logical parent** (a clear, much larger superset): file the new Issue
  as its child.
- **A logical child** (a clear, much smaller subset): file the new Issue as
  its parent. This reparents existing work on your own inference, so expect
  it to be granted under a stricter rule, usually `ask`.
- **A contradiction** (conflicting plans, work already done in another
  direction, conflicting claims about core invariants): do not file; report
  it immediately when attended, in the final report when unattended, with
  the drafted Issue text.
- **Partial overlap:** attended, talk the overlap through and consider
  merging or altering; two Issues often come from one root need seen through
  narrow lenses, and the real step is to zoom out. Unattended, propose it in
  the report.
- **A closed match** (done, regressed, or closed unfinished): a reopen,
  which carries its reason and sits in a higher permission tier than
  filing.

Filing-time checks are best effort; a separate batch pass across the whole
tracker reconciles what they miss.

## 2. Meet the filing bar

The filing bar is the same on every tracker, and it is a minimum:

- a title that states the outcome;
- a body that says what is known and what is not, with no placeholder text:
  what and why, and what done looks like as far as it is known, so someone
  outside the conversation can pick it up;
- an Issue Kind, an Issue Priority, and the entry Issue State, each set as
  best the filer can.

An Issue with a title and one honest sentence is correctly in the entry
state. A more complete Issue is welcome, so long as it states what is known
rather than presuming what is not: technical design and implementation
choices are not the filer's to settle at filing, least of all when filing
into a project whose context the filer lacks. Everything beyond the minimum
(a pointer, reproduction steps, criteria) is a condition on a later Issue
Transition, not on filing.

## 3. Kind, priority, and labels

All three come from the repo's Tracker Schema, which is the repo owner's to
change: read it, and never extend it by using something it does not
declare.

- **Kind.** Every Issue has exactly one kind, recorded once in the tracker's
  own mechanism for kind, and is classified by the project's declared
  scheme. A Kind Label carries it only where the tracker has no field for
  kind, and is never used beside one.
- **Priority.** Priority lives in exactly one place per repo and exists to
  answer "what do I work on next?" Set it as best you can: where the tracker
  fills in a default, that default is the tool's guess, not the filer's. A
  wrong priority costs nothing, since the batch pass reconciles it.
- **Entry state.** A new Issue goes in the entry Issue State the repo's
  Issue State Diagram declares. Any later move is judged against that
  diagram and is not part of filing.
- **Labels.** Labels are drawn from the Issue Label Schema; an unknown label
  is a mistake to fix, not a new label. Every Issue carries at least one
  Area Label.

A repo that has no Tracker Schema file yet declares these wherever its
tracker was set up; the last section says where to look on each platform.

## 4. Relationships

- Record every relationship with its type explicit; blocking is never the
  default, because a wrong blocking link silently hides work.
- A relationship lives in the tracker's native link, which is its source of
  truth; prose about it in a body is narrative only.
- Record a dependency when you find it.
- An Issue goes under a parent only when its scope is part of the parent's
  scope. A dependency or a shared schedule is never by itself a reason to
  group; link it instead.

## 5. Where the Issue came from

An Issue filed for work found along the way says, in its body's why, what
the filer was doing when they found it, naming the Issue that surfaced it if
there was one. That is provenance, not a relationship: it changes nothing
about when or how the work happens, and it is narrative. Where a platform
has a native provenance link, record it as well.

## 6. Refine what you filed

Classifying and refining an Issue is part of filing it: correct your own
mistakes and record what you learn on the Issues you filed. Where
permissions are graded, the right to file an Issue includes the right to
edit Issues you filed, even without the right to edit Issues in general.
Like any grant, this can be limited or withdrawn.

## Today's spellings

These stand in for each wrapper's help until the wrapper is rebuilt to
document its own Verbs; each list goes when its wrapper's help replaces it.
Free text (a body, a note, a comment) always goes through a file.

**Beads** (`bdw`). Help: `bdw help <verb>`. The repo's scheme today is in
`.beads/PRIME.md`, which `bdw prime` prints.

- Search: `bdw search <words>` (titles and IDs, closed Issues included) and
  `bdw list --desc-contains=<words> --all`. After filing,
  `bdw find-duplicates` sweeps for near-duplicates (its default method stays
  on the machine).
- File: `bdw create "<title>" --type=<kind> --priority=<level>
  --labels=<labels> --body-file=<path>`.
- Kind is the type field (`--type`; `bdw types` lists the kinds), never a
  label. bd defaults the priority and the status on every Issue, so the
  entry state needs no call and the priority still needs yours.
- Labels: `bdw label list-all` lists the ones in use.
- A dependency: `bdw dep add <blocked> <blocker> --type=blocks`. Always pass
  `--type` to `dep add`: bare, it creates a blocking edge. Any other link is
  the same call with its own type, such as
  `bdw dep add <a> <b> --type=relates-to`.
- A parent: `--parent=<id>` at filing.
- Context for an existing Issue: `bdw note <id> --file=<path>` or
  `bdw comments add <id> -f <path>`.
- Provenance: `--deps=discovered-from:<id>` at filing, which records where
  the Issue came from and does not block.
- Refining what you filed: `bdw update <id> --body-file=<path>`, with
  `--type` or `--priority` to reclassify, and `bdw label add <id> <label>`.

**GitHub Issues** (`ghw-*`). Help: each Verb's `--help`. `use-github` holds
the arguments, the label contract, and the board mechanics until that help
does; the repo's scheme today is what `ghw-orient <owner/repo>` reports.

- Search: `gh issue list --repo <owner/repo> --search "<keywords>" --state
  all --limit 20`.
- File: `ghw-issue-create`. Kind is its type label, a Kind Label.
- Priority and the entry state: `ghw-board-set`, where priority is a board
  field; otherwise the priority is a label attached at filing.
- A dependency or a parent: `ghw-issue-link` (`add-blocked-by`, `add-sub`).
- Context for an existing Issue: `ghw-issue-comment`.
- Provenance: GitHub has no native provenance link; the body's why carries
  it.
- Refining what you filed: `ghw-issue-edit`.

**Forgejo issues.** `fjw` has no issue Verbs yet.
