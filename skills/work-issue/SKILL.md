---
name: work-issue
description: >
  Work an Issue, or change one, on any Issue Tracker (Beads, GitHub Issues,
  Forgejo issues): find ready work in the states you work; claim it before
  touching it, at any stage; append what you learn to the Issue it belongs
  to; edit, comment on, move, close or reopen an Issue, whether or not you
  hold it, judging every move against the repo's Issue State Diagram and
  giving every close and reopen its reason; close or release everything you
  hold before the session ends; name the Issue in commits and PRs with the
  `Lands:` and `Advances:` trailers. Load before picking up or claiming
  work, before you edit, comment on, move, close or reopen an Issue, and
  before writing a commit message or PR body for work an Issue tracks.
  Triggers: "what's ready", "pick this up", "claim this issue", "move this
  issue to", "close the issue", "reopen the issue", "land the plane".
  EXCLUDE: filing an Issue (create-issue); breaking down a Branch Issue
  (use-bd); a triage pass over the whole tracker (triage-issues); setting a
  tracker up.
---

# Work Issue

Two moments, on any Issue Tracker: doing the work an Issue tracks, and
changing an Issue itself. The discipline is the same everywhere and only the
commands differ, so this skill is written against no platform: where a step
needs a command, run your wrapper's help for the Verb. Until each wrapper's
help carries its own usage, the last section lists today's spellings.

The procedure says what must be done, not who may do it. What you may do
yourself is decided by the repo's Permission rules: if the grant exists, do
the act; if not, the call is denied or asked, and that is the answer. Fix
the call or report the gap, and never look for another spelling or reword
the text to get past it.

## Doing the work

### 1. Find ready work

Choose work explicitly. The ready queue is defined by the agent: unclaimed,
unblocked Issues in the Issue States it works. A blocking dependency blocks
in every state. A Branch Issue is ready exactly when it has no open
children.

A fresh session can resume any Issue from the tracker alone: the Issue
points to context kept in the project's standard documents rather than
holding it. So read the Issue before you claim it, its pick-up note
included, and follow its pointers.

### 2. Claim it

Before touching it, at any stage and not only implementation, make it
visible that you are working on it, since one person or agent advances an
Issue at a time.

- Never take over someone else's work in progress; ask.
- On a forge, a claim leaves a comment carrying the Actor ID, and that
  comment is the lease: an Issue is held when its latest claim or release is
  a claim. The assignee is routing, meaning whose work the Issue is expected
  to be, and holds nothing by itself; a claim assigns the Forge identity it
  runs under only when nobody is assigned.
- Whether a claim also moves the Issue State is the Issue State Diagram's
  call.
- An agent sharing its session's Actor ID (a sub-agent, a workflow agent)
  does not claim, close, or rewrite: a limitation to close, not a
  principle. Such an agent still reads, files new Issues, and appends.

### 3. Append what you learn

As you go, append what you learn to the Issue it belongs to, regardless of
who filed it or who has claimed it.

An Issue is a living document: its description is its current state,
rewritten in place, and its comments are an append-only log. The pick-up
note is a section of the description on every tracker. Whoever works an
Issue rewrites its description as state, so keep the pick-up note saying
where the work stands.

Context that belongs in one of the project's standard documents goes there,
and the Issue points to it. Context whose proper document is unknown goes to
the project's Docs Inbox, where an open Issue owns incorporating it. A
project without a Docs Inbox keeps it in the Issue's description.

Work you find along the way that this Issue does not cover is a new Issue:
load `create-issue`.

### 4. When the work waits on a person

When an Issue cannot move until a person acts (a PR in review, a decision),
release it. Work waiting on a person shows as waiting on that person, and
everything waiting on the human sits in one queue they can see. The
mechanism is per platform.

### 5. Close it, or release it

Close it when its criteria hold: a Leaf Issue is closed when its acceptance
criteria hold, and a Branch Issue is never closed merely because its
children closed. An Issue is done only when everything that describes it
agrees with the change. Closing is a change to the Issue, so the rules under
Changing an Issue apply.

Otherwise release it. A release is left after the pick-up is written; on a
forge it is a comment too.

**Land the plane.** Before you stop, close or release everything you hold.

## Changing an Issue

These apply whether or not you hold the Issue. Changing or destroying
existing data requires more delegation than purely additive change. Closing
one's own finished work is the routine case.

- **Comment.** What you learn about any Issue is appended to it, regardless
  of who filed it or who has claimed it. Comments are an append-only log:
  never rewrite one.
- **Edit.** The description is the Issue's current state, rewritten in
  place so it reads as one picture, never as a list of amendments. The
  filer refines what they filed, and whoever works an Issue rewrites its
  description as state. Rewriting an Issue's scope on your own inference is
  the high-judgement case: attended, ask first; unattended, propose it in
  the report.
- **Link.** Record every relationship with its type explicit; blocking is
  never the default, because a wrong blocking link silently hides work.
  `create-issue` has the other relationship rules and the spellings.
- **Move.** Judge every move against the repo's Issue State Diagram: an
  Issue Transition is taken only when its condition holds, judged by whoever
  moves the Issue. A wrong state puts later work on an earlier gap.
- **Regress.** An Issue may regress to an earlier state at any time; no
  later-stage work goes on top of an earlier stage's gap. A regression is a
  transition like any other, whose condition is that an earlier bar turned
  out not to be met. Say which bar, on the Issue.
- **Close.** Every close and every reopen carries its reason; forge
  auto-close on PR merge is the one exception. An Issue is closed, not
  deleted; the closed Issue stays as the record. Open-or-closed always
  agrees with status. Every TODO comment that cites the Issue is cleaned up
  when that Issue closes.
- **Reopen.** Reopening needs more authority (a higher permission tier) than
  closing. A closed Issue that matches new work (done, regressed, or closed
  unfinished) is reopened rather than filed again.

A repo that has no Tracker Schema file yet declares its states wherever its
tracker was set up; the last section says where to look on each platform.

## Naming the Issue in commits and PRs

A commit or PR names the Issue it serves in a git trailer, `Lands: <Issue
ID> (a few words)` when it finishes the Issue and `Advances: <Issue ID> (a
few words)` when it only moves it, and never names the tracker.

- **`Lands:`** when it finishes the Issue: with this change in, the Issue's
  criteria hold.
- **`Advances:`** when it only moves it: more work remains under the same
  Issue.
- The few words say what the Issue is, for a person reading the log.
- Each trailer is one line, never wrapped, and the trailers are the last
  paragraph of the commit message or PR body, with nothing else in that
  paragraph: git reads no trailer from a paragraph that holds any other
  line.
- Where a project uses more than one forge, a forge Issue ID is written
  qualified (`owner/repo#42`), since a bare number would be ambiguous.
- A platform's own closing mechanics (GitHub's `Closes #N`) are added only
  where the Issue lives on that platform and auto-close is wanted. They go
  in the text above the trailers, never among them.
- Neither trailer closes anything: the close is still its own act, with its
  reason.

`use-git` has the trailer's place in a commit message.

## Today's spellings

These stand in for each wrapper's help until the wrapper is rebuilt to
document its own Verbs; each list goes when its wrapper's help replaces it.
Free text (a body, a note, a comment) always goes through a file.

**Beads** (`bdw`). Help: `bdw help <verb>`. `use-bd` holds what Beads adds
(the session start, claims and the Actor ID, gates). The states today are
bd's own statuses, which `bdw statuses` lists.

- Ready work: `bdw ready`, then `bdw show <id>` to read an Issue.
- Claim: `bdw update <id> --claim`. bd's claim sets the status to
  `in_progress` in every case.
- Append: `bdw note <id> --file=<path>` or
  `bdw comments add <id> -f <path>`. On Beads the notes field is a log, like
  comments.
- Edit: `bdw update <id> --body-file=<path>` rewrites the description; the
  pick-up note is its `## Pick-up` section.
- Move or regress: `bdw update <id> --status=<status>`, with the why in a
  note. Never close this way: it carries no reason.
- Waiting on a person: a gate and the `human` label; `use-bd` has the steps.
- Release: `bdw unclaim <id>`.
- Close: `bdw close <id> --reason-file=<path>`.
- Reopen: the reason in a note (`bdw note <id> --file=<path>`), then
  `bdw reopen <id>`. bd has no file form for a reopen reason.

**GitHub Issues** (`ghw-*`). Help: each Verb's `--help`. `use-github` holds
the arguments until that help does. The states today are the options of the
board's Status field, which `ghw-orient <owner/repo>` reports, with their
meanings and conditions in `triage-issues`; a repo with no board has no
state beyond open and closed.

- Ready work: there is no queue mechanism on a forge, only the query:
  `gh issue list --repo <owner/repo> --state open`. To read an issue and
  its comments: `gh issue view <issue#> --repo <owner/repo> --comments`.
- Claim and release: `ghw` has no Verb for either yet. Until it does, leave
  the comment yourself with `ghw-issue-comment`, naming your session, since
  nothing adds the Actor ID for you.
- Append: `ghw-issue-comment`.
- Edit: `ghw-issue-edit` (`set-body` rewrites the description).
- Move or regress: `ghw-board-set` on the Status field, with the why in a
  comment.
- Waiting on a person: the forges have no standard mechanism yet; say who
  the Issue waits on in a comment.
- Close: `ghw-issue-close`, whose comment file is the reason. Where the
  repo has a board, then set its Status field to the closed option that
  matches the reason (`ghw-board-set`).
- Reopen: `ghw` has no Verb for it yet.

**Forgejo issues.** `fjw` has no issue Verbs yet.
