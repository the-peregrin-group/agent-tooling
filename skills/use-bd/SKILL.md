---
name: use-bd
description: >
  The operating manual for Beads (`bd`) as a repo's Issue Tracker, run
  through the `bdw` wrapper: the session loop (prime, ready, claim, file,
  close, land the plane), who may claim and close, the Beads commands for
  a Branch Issue pass (breakdown-issue), what Beads adds to filing (the
  filing discipline is create-issue), free text through files, work waiting
  on a human, and friction reporting. Load at the start of any session in a
  repo with a `.beads/` directory, before the first `bdw` or `bd` call, and
  whenever `bd prime` or a `bdw` message says to. Triggers: "bdw ready",
  "what's ready", "claim this issue", "file a bead", "close the bead",
  "land the plane", "Beads". EXCLUDE: GitHub Issues (use-github), the rules
  for working a Branch Issue in passes (breakdown-issue), and setting Beads
  up in a new repo (this skill's onboarding.md).
---

# Use Beads

Beads (`bd`) is the Issue Tracker; `bdw` is the wrapper every agent runs it
through. `bdw` records which session acted (the Actor), runs `bd` with
the arguments unchanged, and refuses the few calls listed below, so bd's
own help is the reference for flags: `bdw help <verb> [<subcommand>]`.
(`bdw <verb> --help` can prompt or match a deny rule; `bdw help` never
does.) Every help output, bd usage error, and `bdw` refusal ends with
"Agents, load /use-bd immediately.": that line is pointing here.

Three rules hold for every call:

- **Always `bdw`, never `bd` or `beads`,** reads included. Raw calls do
  not record the Actor, and a repo set up for use-bd denies them.
- **Verb first, global flags after:** `bdw ready --json`, never
  `bdw --json ready`. Permission rules are prefix rules, and a flag-first
  spelling either prompts or trips a deny meant for something else; `bdw`
  refuses it anyway (exit 2), except `bdw --help` and `bdw --version`.
- **A denied call is the policy working.** Do not look for another
  spelling of it. If the normal path for a real need is denied or prompts,
  that is a gap: say so (see Friction, below).

`bdw` refuses, with exit 4 and before bd runs: `--actor` anywhere (the
Actor comes from the session), and the flags that point bd at another
database (`-C`, `--directory`, `--db`, `--database`, `--global`) anywhere.
Policy forbids these: drop the flag, and if the need behind it is real,
report the gap. It exits 1, a deployment problem no change to the call
can fix, when no `bd` is on PATH; for any call when the workspace's
`.beads/metadata.json` cannot be found, since bd would otherwise fall
back to an empty database; and, on a bd version it has not been verified
against, for any call that is not a plain read: a read verb with no
flags beyond the ones this skill uses for reads (reads run with a
warning). When a `bdw:` line on stderr explains an exit 1, stop and
report it; do not rephrase around it.

bd's own exit code never reaches you: `bdw` translates it under the
Exit-code contract (`docs/index.md#exit-code-contract` in agent-tooling).
A bd that succeeds exits 0. A bd that fails with a usage error (an unknown
verb or flag, a missing argument) exits 2, followed by the help line: fix
the call. Any other bd failure exits 1, with bd's own reason on stderr.

Where the database has a Dolt remote, `bdw` pushes to it in the
background after every write; you never push. If a call prints any
`bdw: warning:` line about the push, your call itself worked: carry on,
and tell the user once, in your report, with the reason the line gives.
Do not try to push by hand. `bdw` pushes only to hosts on the user's
push-host allowlist (`~/.config/agent-tooling/bdw/config.toml`); when the
warning says the allowlist is missing or a host is not on it, writing that
file is the user's decision, not yours: report it. The push's record and
log live in `bdw`'s subdirectory of the Machine State Directory
(`~/.local/state/agent-tooling/bdw/push/` by default), and the warning
names the log.

The repo's own conventions are in `.beads/PRIME.md`, which `bdw prime`
prints. Read this skill's `quirks.md` when bd surprises you, and
`onboarding.md` only when setting Beads up in a new repo. `rules.json`
beside it is the canonical Permission rule set for Beads: every command
this skill teaches as a call (not the ones it tells you never to make) is
allowed by it, so a taught command that prompts or is denied means the
repo's rules have drifted from it.

## The loop

1. `bdw prime` at session start, then `bdw gate check` to resolve gates
   whose condition now holds (see Work waiting on a human).
2. `bdw ready` to find work, `bdw show <id>` to read it. `bdw ready` also
   lists Branch Issues (below) that still have open children; skip those
   by hand. `bdw epic status --eligible-only` lists the epics whose
   children are all closed, which are ready for their verifying pass.
3. `bdw update <id> --claim` before touching anything.
4. File what you find along the way as new Issues linked back:
   `--deps=discovered-from:<id>` (load `create-issue`; see Filing).
5. Append progress to the Issue as you go (see Free text).
6. `bdw close <id> --reason-file=<path>` when its acceptance criteria hold.
7. **Land the plane.** Before the session ends, close or release
   (`bdw unclaim <id>`) every Issue you claimed. A claim never outlives
   its session: continuity lives in the Issue's pick-up section and
   metadata, never in a claim.

## Who may claim, close, and rewrite

The Actor `bdw` records comes from the session's environment: one Actor
ID per session, derived from the session ID the harness sets, and bd
also records that session ID as the one that closed an Issue. A
sub-agent's environment cannot be told from its parent's. So **an agent
that shares its session's Actor (a sub-agent, a workflow agent) reads,
files new Issues, and appends notes and comments, but never claims,
closes, or rewrites an Issue.** The session that holds the conversation
does those. An orchestrator puts this rule in every brief it hands down.

`--claim` succeeds silently when the Issue is already claimed by the
same Actor, and a session whose session ID is missing falls back to a
shared `attended-<user>` Actor. So a successful claim does not prove the
Issue is yours: if `bdw show` already showed it `in_progress` under your
Actor before you claimed it, another agent or session may hold it; stop
and ask. Never pass `--actor`; `bdw`
refuses it. Never take over someone else's claim (`unclaim --force`,
`update --assignee`); ask.

## Branch Issues and Leaf Issues

What a Branch Issue's work is, how it is worked in passes, when an Issue
belongs under a parent, and how big a Leaf Issue is are the
`breakdown-issue` skill's: load it before claiming a Branch Issue. This
section holds only the Beads commands for a pass.

- **Only an epic takes children.** To reorganize a Leaf Issue as a Branch
  Issue, retype it first (`bdw update <id> --type=epic`).
- **Adding children:** file each with `--parent=<id>`, then add the
  dependencies between them.
- **Removing a child** that is not wanted: `bdw close <id>
  --reason-file=<path>`. **Redrawing one:** rewrite its description
  (`bdw update <id> --body-file=<path>`).
- **Ending the pass:** release the Branch Issue (`bdw unclaim <id>`), or,
  after verifying it, close it (`bdw close <id> --reason-file=<path>`).
- **A Branch Issue that has open children is not ready work,** though
  `bdw ready` lists it all the same (see The loop). Starting a pass on one
  for cause is `breakdown-issue`'s rule.

## Filing

Load `create-issue` before filing an Issue. It holds the filing discipline
(search first and what each finding means, the filing bar, kind, priority,
and labels, relationships, where the Issue came from, refining what you
filed) and today's `bdw` spellings for each step. How big a Leaf Issue is
is the `breakdown-issue` skill's. What Beads adds, and one rule (context
outside the tracker) that stays here until its own skill takes it:

- **Labels:** children inherit their parent's labels unless filed with
  `--no-inherit-labels`.
- **Acceptance criteria** go in the description file, under a
  `## Acceptance Criteria` section: bd's `--acceptance` flag takes inline
  text only.
- **Two existing Issues that duplicate each other:**
  `bdw duplicate <id> --of=<canonical>` closes the duplicate. On your own,
  only when very confident; otherwise raise it with the user (unattended:
  report it).
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

bd 1.3.0 has no file form for the title, acceptance criteria, replacing
notes (`--notes` overwrites them; append with `note --file`), or the
reasons on `unclaim` and `gate`. Leave those reasons off and put the why
in a note. A title is the one place where keeping the word out is
sanctioned until `bdw` adds a file form; log a friction entry when it
happens.

Write the files in the temporary directory your harness designates
(never in the repo), with unique names.

**State versus log.** An Issue's description is its state: rewrite it in
place (`--body-file`) so it always reads as the current picture,
including a `## Pick-up` section that tells the next session where the
work stands. Notes and comments are its log: append, never rewrite.

## Work waiting on a human

When an Issue cannot move until a person acts (a PR in review, a
decision), release it and block it with a gate, so it leaves ready work
without a custom status:

- A PR on GitHub: `bdw gate create --blocks=<id> --type=gh:pr
  --await-id=<number>`. `bdw gate check` resolves it once the PR has
  merged (it asks the `gh` CLI, so it works only for GitHub-hosted repos;
  elsewhere use a `human` gate).
- Anything else: `bdw gate create --blocks=<id> --type=human`, with the
  why in a note on the Issue. The person resolves it.
- Add the `human` label (`bdw label add <id> human`), so the maintainer
  has one queue: `bdw human list`.

An open gate blocks closing as well as ready work. After merge, run
`bdw gate check`, then close the Issue the normal way; never force the
close. Never close it through `bdw human respond`, which closes at once.

Record the Issue's branch and PR as metadata, the one current answer:
`bdw update <id> --set-metadata=branch=<name> --set-metadata=pr=<number>`.

## Friction and upstream

When a `bdw` refusal, a prompt, or bd itself surprises you, say so: log a
friction entry where the repo's `PRIME.md` says, and mention anything
about the Issue Tracker that felt awkward in your final report. Offer to
report a Beads bug or contribute a fix upstream; never do it on your own.
Unattended, mention the bug in your final report.
