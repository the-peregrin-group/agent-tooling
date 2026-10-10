---
name: use-bd
description: >
  The operating manual for Beads (`bd`) as a repo's Issue Tracker, run
  through the `bdw` wrapper: the session loop (prime, ready, claim, file,
  close, land the plane), who may claim and close, Branch and Leaf Issues
  and working a Branch Issue in passes, filing discipline (breakdown, the
  four relationships, labels), free text through files, work waiting on a
  human, and friction reporting. Load at the start of any session in a repo
  with a `.beads/` directory, before the first `bdw` or `bd` call, and
  whenever `bd prime` or a `bdw` message says to. Triggers: "bdw ready",
  "what's ready", "claim this issue", "file a bead", "close the bead",
  "land the plane", "break this epic down", "Beads". EXCLUDE: GitHub Issues
  (use-github) and setting Beads up in a new repo (this skill's
  onboarding.md).
---

# Use Beads

Beads (`bd`) is the Issue Tracker; `bdw` is the wrapper every agent runs it
through. `bdw` records which session acted (the Actor) and otherwise passes
the arguments to `bd` untouched, so bd's own help is the reference for
flags: `bdw help <verb>` or `bdw <verb> --help`.

Three rules hold for every call:

- **Always `bdw`, never `bd` or `beads`.** Raw writes prompt or are denied
  by design.
- **Verb first, global flags after:** `bdw ready --json`, never
  `bdw --json ready`. Permission rules are prefix rules, and a flag-first
  spelling either prompts or trips a deny meant for something else.
- **A denied call is the policy working.** Do not look for another
  spelling of it. If the normal path for a real need is denied or prompts,
  that is a gap: say so (see Friction, below).

The repo's own conventions are in `.beads/PRIME.md`, which `bdw prime`
prints. Read this skill's `quirks.md` when bd surprises you, and
`onboarding.md` only when setting Beads up in a new repo.

## The loop

1. `bdw prime` at session start.
2. `bdw ready` to find work, `bdw show <id>` to read it. `bdw ready` also
   lists Branch Issues (below) that still have open children; skip those
   by hand (`bdw show <id> --children` shows them). A Branch Issue whose
   children are all closed is ready for its verifying pass.
3. `bdw update <id> --claim` before touching anything.
4. File what you find along the way as new Issues linked back:
   `--deps=discovered-from:<id>` (see Filing).
5. Append progress to the Issue as you go (see Free text).
6. `bdw close <id> --reason-file=<path>` when its acceptance criteria hold.
7. **Land the plane.** Before the session ends, close or release
   (`bdw unclaim <id>`) every Issue you claimed. A claim never outlives
   its session: continuity lives in the Issue's pick-up section and
   metadata, never in a claim.

## Who may claim, close, and rewrite

The Actor `bdw` records comes from the session's environment, and a
sub-agent's environment cannot be told from its parent's. So **an agent
that shares its session's Actor (a sub-agent, a workflow agent) reads,
files new Issues, and appends notes and comments, but never claims,
closes, or rewrites an Issue.** The session that holds the conversation
does those. An orchestrator puts this rule in every brief it hands down.

Attended sessions of one user share one Actor today, so two attended
sessions must not work the same Issue. Never pass `--actor`; `bdw`
refuses it. Never take over someone else's claim; ask.

## Branch Issues and Leaf Issues

A **Leaf Issue** is a unit of work sized for one session. A **Branch
Issue** holds other Issues as children (an epic): its own work is
management, scoping it, breaking it down, and verifying it is done. It is
worked in **passes**, each a session that claims it and ends in one of
two ways:

- **Breakdown.** Draft the whole breakdown first (each child's title,
  description file, type, labels, and dependencies), then file the
  children in one sitting with `--parent=<id>`, add the dependencies
  between them, and release the Branch Issue (`bdw unclaim <id>`). Each
  child is ready work the moment it exists, so file only what is drafted.
- **Verification.** When every child is closed, check the Branch Issue's
  own acceptance criteria against the result, then close it or file the
  children still missing.

Only an epic takes children. When a task proves bigger than a session,
retype it first (`bdw update <id> --type=epic`) and break it down;
otherwise file a sibling Leaf Issue linked by a dependency. Never claim a
Branch Issue that has open children.

## Filing

- **Search first:** `bdw search <words>` (titles and IDs) and
  `bdw list --desc-contains=<words> --all`. Afterwards,
  `bdw find-duplicates` sweeps for near-duplicates (its default method
  stays on the machine).
- **One Issue, one session's work.** Anything bigger is an epic, broken
  down in its own pass.
- **Kind goes in the type field** (`--type=task|bug|feature|chore|epic|...`,
  `bdw types` lists them), never in a label.
- **Labels:** every Issue has at least one area label and may carry
  others; use the ones already in use (`bdw label list-all`) unless the
  repo's `PRIME.md` says otherwise. Children inherit their parent's labels
  unless filed with `--no-inherit-labels`.
- **Description:** what and why, then a `## Acceptance Criteria` section.
  bd's `--acceptance` flag takes inline text only, so the criteria live in
  the description file.
- **The four relationships.** At filing, look for each:

  | Relationship | In Beads | When on your own |
  |---|---|---|
  | dependency | `bdw dep add <blocked> <blocker> --type=blocks` | always |
  | duplication | `bdw duplicate <id> --of=<canonical>` (closes it) | only when very confident |
  | composition | `--parent=<id>` at filing | only when very confident |
  | contradiction | `bdw dep add <a> <b> --type=relates-to`, plus a label naming it | only when very confident |

  Otherwise raise it with the user (unattended: report it). Always pass
  `--type` to `dep add`: bare, it creates a blocking edge, and a wrong
  blocking edge silently removes work from `bdw ready`. `discovered-from`
  records provenance and does not block.
- **Context outside the tracker.** Material that belongs in a standard
  document (requirements, design, UX, an ADR, a lexicon entry) goes there,
  and the Issue links it through a metadata key per document type:
  `bdw update <id> --set-metadata=design=<path>` (common keys:
  `requirements`, `design`, `ux`, `adr`). If you do not know where it
  belongs, keep it in the description.

## Free text

Put free text in a file and pass the file. Inline text is allowed, but in
a worktree-isolated session the harness refuses any command whose inline
arguments mention git, because it cannot show the command is not a git
operation; and a deny rule can match a denied word inside your text. Both
refusals happen before `bdw` runs. **When inline text is refused, switch
to the file form; never reword the text to get past the refusal.**

| Field | File form |
|---|---|
| description | `create` / `update --body-file=<path>` |
| design | `create` / `update --design-file=<path>` |
| a note, appended | `bdw note <id> --file=<path>` |
| a comment | `bdw comments add <id> -f <path>` |
| close reason | `bdw close <id> --reason-file=<path>` |
| metadata | `--metadata=@<file>.json` (replaces all keys) |

bd 1.3.0 has no file form for the title, acceptance criteria, or
replacing notes (`--notes` overwrites them; append with `note --file`). A
title is the one place where keeping the word out is sanctioned until
`bdw` adds a file form; log a friction entry when it happens.

Write files under the session's scratch directory with unique names.

**State versus log.** An Issue's description is its state: rewrite it in
place (`--body-file`) so it always reads as the current picture,
including a `## Pick-up` section that tells the next session where the
work stands. Notes and comments are its log: append, never rewrite.

## Work waiting on a human

When an Issue cannot move until a person acts (a PR in review, a
decision), release it and block it with a gate, so it leaves ready work
without a custom status:

- A PR: `bdw gate create --blocks=<id> --type=gh:pr --await-id=<number>`.
  `bdw gate check` resolves gates whose PR has merged.
- Anything else: `bdw gate create --blocks=<id> --type=human
  --reason=<why>`. The person resolves it.
- Add the `human` label (`bdw label add <id> human`), so the maintainer
  has one queue: `bdw human list`.

After merge, close the Issue the normal way. Never close it through
`bdw human respond`, which closes at once.

Record the Issue's branch and PR as metadata, the one current answer:
`bdw update <id> --set-metadata=branch=<name> --set-metadata=pr=<number>`.

## Friction and upstream

When a `bdw` refusal, a prompt, or bd itself surprises you, say so: log a
friction entry where the repo's `PRIME.md` says, and mention anything
about the Issue Tracker that felt awkward in your final report. Offer to
report a Beads bug or contribute a fix upstream; never do it on your own.
Unattended, mention the bug in your final report.
