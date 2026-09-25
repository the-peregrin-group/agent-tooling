# agent-tooling

The vocabulary for a repo that ships policy-enforcing wrappers, skills, and
agent definitions for Claude Code sessions, and that tracks its own work in a
per-repo tracker. Every term below is implicitly an agent-tooling term.

## Language

### Wrappers

**Wrapper**:
A small executable that stands between an agent and one raw tool (git, a
forge CLI, or the tracker) and enforces policy on the call, so that
permission rules can grant it by literal command prefix instead of granting
the raw tool. `bdw` is the Beads wrapper: it passes its arguments through to
`bd` unchanged except bd's own `--actor` flag, which it refuses.
_Avoid_: script, helper, alias, shim

**Verb**:
One wrapper, named `<family>-<verb>`, invoked by bare name on PATH.
_Avoid_: command, subcommand (those belong to the raw tools)

**Wrapper family**:
The set of verbs for one target: `gitw-*` for git, `ghw-*` for GitHub,
`fjw-*` for Forgejo.

**Roster**:
The machine-local registry that pins, per repo, the one blessed checkout, its
authoritative remote, and its default branch.

**Roster label**:
A repo's short name in the roster and the first argument of every `gitw-*`
verb; repo identity comes from the label, never from a path or the cwd.
_Avoid_: repo name, slug

**Branch prefix**:
The `fix/`-style token (lowercase, one level, trailing slash) that scopes a
mutating verb and that allowlist rules pin.

**Exit-code contract**:
The fixed meaning of a verb's exit status (success, unclassified failure,
usage, not found, refused by policy, roster or auth failure, network) that
callers branch on.

**Actor**:
The session identity a wrapper derives from its own environment and records
on every write it makes: a job-derived actor for background-job sessions, a
visibly distinct attended fallback otherwise.
_Avoid_: user, author, assignee (an actor is a session, not a person)

### Installing

**Source repo**:
A checkout with an `install.json` at its root, named by that file's
`source_repo` field; several source repos can ship into the same targets.

**Cohort**:
One named section of `install.json`: a set of source directories that
installs into one target, with its own excludes.

**Target**:
The directory a cohort installs into, fixed by the cohort's kind.

**Unit**:
One skill directory; skills install and swap a whole unit at a time, while
`bin` and `agents` install file by file.

**Receipt**:
The record in each target of what each source repo installed there: the
commit and a hash for every file or unit it owns.

**Foreign / unowned**:
A file in a target that another source repo's receipt claims is foreign; a
file no receipt claims is unowned. Installs preserve both and report them.

**diff / apply / adopt**:
The installer's three commands: `diff` compares installed against source and
changes nothing; `apply` installs, refusing to overwrite foreign content;
`adopt` installs and takes over the files one named source repo owned.

### Tracking

**Tracker**:
The one system of record for this repo's work; during the trial it is Beads,
and GitHub Issues is frozen.
_Avoid_: backlog, board, issues (as a system name)

**Bead**:
One tracked item of work in Beads, with a status, a type, an actor history,
and dependencies on other beads.
_Avoid_: issue, ticket, task (as a system-level noun; `task` is a bead type)

**Bead ID**:
A bead's stable identifier, prefixed with this repo's issue prefix; the only
way code, commits, and PR bodies refer to a bead.
_Avoid_: `#N` (that is a GitHub issue number)

**External reference**:
The pointer a bead carries to the record it was imported from, here a GitHub
issue URL; it identifies provenance and never implies sync.

**Discovered-from**:
The dependency recorded from a bead to the bead whose work surfaced it.

**Trial freeze**:
The state in which GitHub Issues stays readable but is neither written nor
synced, so that the tracker is the only source of truth for the trial.

**Command policy**:
The allow, ask, and deny rules that decide which tracker subcommands an agent
may run without a human, with a human, or never; policy, not judgment.
_Avoid_: allowlist (ambiguous between this and the wrappers' permission rows)

### Claude Code

**Harness**:
Claude Code as the environment agents run in: the permission rules, hooks,
worktree isolation, and memory files that surround a session.

**Skill**:
A directory with a `SKILL.md` that the harness loads on demand; the
instructions an agent follows for one kind of task.

**Agent definition**:
A subagent definition in `agents/`, a Markdown file with frontmatter that the
harness can spawn for a delegated task.
_Avoid_: agent (alone; an agent is a running session, this is its definition)

## Relationships

- A **Wrapper family** contains one or more **Verbs**; `bdw` is a **Wrapper**
  in no family.
- Every mutating `gitw-*` **Verb** takes exactly one **Roster label** and one
  **Branch prefix**, and reports through the **Exit-code contract**.
- `bdw` derives one **Actor** per invocation and records it on the
  **Tracker**; `gitw-commit` records the same **Actor** on every commit.
- A **Source repo** declares one or more **Cohorts**; each **Cohort**
  installs into exactly one **Target** and leaves a **Receipt** there.
- A **Tracker** holds many **Beads**; a **Bead** has exactly one **Bead ID**,
  at most one **External reference**, and any number of **Discovered-from**
  links.
- The **Command policy** governs every **Tracker** write; the **Trial
  freeze** governs the frozen system, not the **Tracker**.

## Example dialogue

> **Dev:** "The agent found a bug while working bead `agent-tooling-w7p.2`.
> Does it file a GitHub issue?"
> **Maintainer:** "No. The **Trial freeze** is on, so it creates a new
> **Bead** with a **Discovered-from** link to `w7p.2`. Its **Bead ID** is what
> the commit and the PR body cite."
> **Dev:** "And who does the tracker say did it?"
> **Maintainer:** "The **Actor** `bdw` derived for that session, the
> job-derived one if it was a background job. The same **Actor** is on the
> commit's `Executed-By` trailer."
> **Dev:** "Can the agent prune closed beads to keep things tidy?"
> **Maintainer:** "The **Command policy** denies it. Nothing in the
> **Tracker** is deleted during the trial; closed beads are hidden, not gone."

## Flagged ambiguities

- "shim" was used for `bdw` beside "wrapper" for the `gitw-*`/`ghw-*`/`fjw-*`
  verbs; resolved: one term, **Wrapper**, since `bdw` inspects its arguments
  too and pass-through distinguished nothing.
- "allowlist" was used for both the wrappers' literal permission rows and the
  tracker's policy; resolved: **Command policy** for the tracker, and
  "permission rows" for what a consumer repo grants a verb.
- "issue" was used for both GitHub issues and beads; resolved: **Bead** in
  the tracker, "GitHub issue" only for the frozen system, and `#N` never
  names a bead.
- "actor" could be read as a person; resolved: an **Actor** is a session
  identity, and a person appears only as a bead's assignee.
