---
name: setup-issue-tracker
description: >
  Set up a repo's Issue Tracker (Beads, GitHub Issues, Forgejo issues): its
  Tracker Schema, labels, board, and backlog. Always load when setting up
  issue tracking for a repo.
---

# Setup Issue Tracker

Capitalized terms (Issue, Tracker Schema, Issue State Diagram, Forge
identity, Permission rule, and the rest) are the lexicon's
([LEXICON.md](https://github.com/the-peregrin-group/agent-tooling/blob/main/LEXICON.md)),
and the lexicon is authoritative for them. This skill is written against no
platform. Each platform's mechanics are a file beside it, read on demand
when the plan needs them:

- Beads: `beads.md` in this skill's directory.
- GitHub Issues: `github.md` in this skill's directory.
- Forgejo issues: `forgejo.md` in this skill's directory.

The procedure says what must be done, not who may do it. What you may do
yourself is decided by the repo's Permission rules: if the grant exists, do
the act; if not, the call is denied or asked, and that is the answer. Fix
the call or report the gap, and never look for another spelling or reword
the text to get past it.

## Setup is the owner's procedure

Setting up a tracker is a human procedure: confirm the target, draft the
whole plan, and wait for the owner's approval before changing anything. The
Tracker Schema and the rest of the tracker's structure are the repo owner's
design, even when an agent drafts them. The owner is usually the person in
the session; whether an agent may act as one is a matter of Permission
rules, never of reading this skill loosely.

If a `use-privacy` skill is listed, load it before composing any text bound
for outside this machine: an Issue, a label description, a commit message.

## 1. Confirm the target

Say which repo and which tracker, and confirm both with the owner. Find out
what is already there: a tracker in use, a `TRACKER.md` at the repo root, a
backlog kept elsewhere. A repo that already has a Tracker Schema is not set
up again from the default; where the source repo is at hand, offer to show
the owner what the default has changed since the copy's provenance, and
take only what they accept.

## 2. Draft the whole plan

One document, covering every part below that applies, so the owner
approves the whole of it at once.

### The Tracker Schema

- Copy the shipped default, `TRACKER.default.md` in this skill's directory,
  whole, to `TRACKER.md` at the repo root. Never write a partial file or a
  reference to the default: the copy is the repo's only context for its
  lifecycle.
- Record the provenance the default's own text asks for. The commit is the
  one the Installer recorded for this skill's source repo in the Receipt
  (`install-receipt.json` beside the installed skills). If that commit is
  marked dirty or cannot be found, stop and say so rather than record a
  revision nobody can diff against.
- Tailor the copy to the platform, as its platform file says: where the
  default leaves something for the repo to designate, have the owner
  designate it; where the tracker has built-in kinds or priority levels,
  the copy's become the tracker's own; fill in the Area Labels with the
  parts of this project, enough to label meaningfully and few enough to
  apply consistently. Lines meant for other platforms may be trimmed or
  left.
- The default's kinds and priority levels are proposals, not mandates. The
  owner keeps, changes, or replaces them, unless the platform materially
  prevents it. Every change is the repo's customization of its copy.

### Forge identities

On a forge, every operation is to name a Forge identity, and which
identities a repo grants is decided by its Permission rules. Setup
registers the repo's identities and gives the machine account the access
it needs on the forge. Registration is a Wrapper's Verb or the owner's own
edit to their Machine Config, never an agent's improvised one. Where the
Wrapper cannot register an identity yet, the platform file says what exists
today; the plan says what the owner has to do and what has to wait.

### The tracker's own structure

Whatever the tracker needs so that it can record what the Tracker Schema
declares: its labels, its board or status fields, its settings. The
platform file has the mechanics.

### The backlog

Ask whether there is existing work to bring in: TODO files, sections of the
repo's documents or agent instructions, code comments, notes kept
elsewhere, another tracker. If there is:

- Give every item one verdict (file it, fold it into another item, already
  done, or drop it) and keep where it came from.
- Write the result as one deduplicated plan, a full document of the Issues
  to file, each with its title, kind, priority, labels, relationships, and
  source. The owner reviews it as part of the whole plan.
- One filer then files it, one Issue at a time, in an order that lets every
  relationship be recorded as it is filed. Each Issue meets the filing bar
  and says where it came from (`create-issue`).

### Retiring each source

Each source is retired by whoever owns it. A source the repo owns may be
removed, or replaced with a pointer to the tracker, once every item in it
has a verdict. A source owned elsewhere changes only through its owner's
channel: the plan says what to tell that owner, and the agent does not
edit it.

### Pointing the repo's agents at the tracker

The repo's agent instructions (its `CLAUDE.md`, or whatever its agents
read first) gain a short pointer: where Issues are tracked, that the
Tracker Schema is `TRACKER.md`, and which skill to load. A pointer, not a
copy of the conventions. On a re-run, rewrite the existing section in
place rather than add a second.

## 3. Wait for approval

Present the whole plan and wait for the owner's explicit approval. They may
change any part of it; revise and present it again until they approve.

## 4. Carry it out

Carry out what was approved, in the order the plan gives, and nothing
else. `TRACKER.md` and every other file change go through the repo's
normal review. Anything denied, or found different from what the plan
assumed, is put to the owner, not worked around.

## 5. Verify and report

Read back what was set up: the tracker's structure against the Tracker
Schema, the filed Issues against the backlog plan, each source retired or
its owner told. Report what was done and what remains, including anything
that had to wait for a Wrapper.

A recurring triage pass is a separate setup, in `triage-issues`.
