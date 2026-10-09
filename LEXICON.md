# agent-tooling

A repo that ships policy-enforcing Wrappers, Skills, and Agent definitions for
agents.

## Entries

### Wrappers

**Wrapper**: A facade over one raw tool or service (e.g., git, a forge, the
Issue Tracker) that restricts the surface available to agents, makes that
surface grantable by Permission rules without granting the raw tool, and
encodes the project's conventions in code instead of leaving them to agent
judgment.
- _Avoid_: script, helper, alias, shim

**gitw**: The Wrapper over git; every allowed mutating git operation goes
through it.

**ghw**: The Wrapper over GitHub; every allowed GitHub write goes through it.

**fjw**: The Wrapper over a Forgejo forge; every allowed Forgejo write goes
through it.

**bdw**: The Wrapper over Beads; every allowed Beads write goes through it.

**Verb**: One operation a Wrapper offers agents. Verbs are an editorial choice
and need not mirror the raw tool's operations one to one: each is shaped by
the journey the Wrapper supports and the restrictions it imposes (e.g., gitw's
integrate runs several git operations while allowing few git capabilities
during integration).
- _Avoid_: command, subcommand

**Exit-code contract**: The fixed meaning of a Verb's exit status (e.g.,
success, refused by policy, network failure, etc.) that callers branch on.

**Actor**: The session identity a Wrapper derives from its own environment and
records on the writes it attributes: one per background job, and a visibly
distinct fallback for attended sessions. An Actor is a session, never a
person.
- _Avoid_: user, author, assignee

### Repos and branches

**Roster**: The machine-local registry that pins, per repo, the one blessed
checkout, its authoritative remote, and its default branch.

**Roster label**: A repo's short name in the Roster, by which tools (e.g.,
gitw) identify the repo.
- _Invariants_: repo identity comes from the Roster label, never from a path
  or the working directory
- _Avoid_: repo name, slug

**Branch prefix**: The token naming a class of branches (e.g., fix/) that
scopes a Verb acting on a branch, and that Permission rules pin when
granting it. A bare / names the class of every branch.
- _Invariants_: a Wrapper only verifies a Branch prefix; whether a
  particular one is granted is decided by Permission rules alone

### Agentic systems

**Skill**: A package, compliant with the agentskills.io standard, that teaches
agents an additional capability.

**Agent definition**: A package that defines a specialized agent (e.g., its
role, instructions, and permitted capabilities) that another agent can spawn
to carry out a delegated task. An agent is the running session; an Agent
definition is what it is spawned from.
- _Avoid_: agent

**Handoff**: A self-contained brief with which an agent passes work to
another agent or a human, so the recipient can carry it on without the
sender's conversation.
- _Invariants_: readable without the sender's conversation; states what done
  means and how to verify it; never contains a secret

**Permission rule**: A declared rule that decides whether an agent may take an
action on its own, only with a human's approval, or never.
- _Invariants_: enforced programmatically, never left to agent judgment
- _Avoid_: allowlist, permission row

### Homing in

**Line of Inquiry**: One line of questioning into a problem, which must be
examined before an opinion on the problem is defensible. Lines of Inquiry
form a tree: one may contain finer, domain-specific Lines of Inquiry, and a
fixed set of roots is shipped with the home-in Skill. A Line of Inquiry is
explored to the depth the problem warrants, or set aside with a reason.
Abbreviated LOI after first use.
- _Invariants_: considered before an opinion is declared, whether or not it
  is asked about
- _Avoid_: angle, lens, dimension

**Line of Inquiry Exit**: The event of an interrogation leaving a Line of
Inquiry, because it has been explored to the depth the problem warrants or
set aside with a reason. Abbreviated LOI Exit after first use.
- _Avoid_: checkpoint

**Resolution Queue**: The set of everything raised during an interrogation
that awaits formal resolution: candidate terms with their working names,
provisional decisions awaiting the ADR gate, assumptions under test, and
gathering not yet done. Visible to the user throughout; travels with the
artifact between sessions.
- _Invariants_: every item is resolved at the next Line of Inquiry Exit;
  empty before an interrogation is declared done
- _Avoid_: ledger, parking lot, backlog

### Installing

**Install Target**: A directory into which agent tooling is installed. Not all
tooling need be installed into the same Install Target.
- _Invariants_: never edited directly; only the Installer writes it

**Installer**: The component that installs Source repos' tooling into Install
Targets, and the only writer of Install Targets and their Receipts.
- _Invariants_: never overwrites content another Source repo owns, except by
  Adoption; never replaces content no Receipt claims without reporting it

**Install Manifest**: A Source repo's declaration of the tooling that can be
installed from it: the repo's name, and which tooling installs into which
Install Target, with any exclusions.
- _Invariants_: one per Source repo; the Installer installs only what an
  Install Manifest declares

**Source repo**: A repo that contains an Install Manifest, which declares the
tooling that can be installed from it; the tooling of several Source repos can
be installed into the same Install Target.

**Cohort**: A set of a Source repo's tooling, declared in its Install
Manifest, that installs into one Install Target (e.g., "the skills Cohort");
the Installer can install Cohorts selectively.
- _Invariants_: a Source repo has exactly one Cohort for each Install Target
  it uses

**Receipt**: The ownership record in an Install Target that lets the Installer
keep one Source repo's tooling from overwriting another's: which Source repo's
tooling each installed file came from (a Skill counts as one whole), and from
which source revision.
- _Invariants_: each installed file or Skill has at most one owning Source
  repo; the Installer removes from an Install Target only what its Receipt
  shows a Source repo installed

**Adoption**: The transfer, within a Receipt, of ownership of installed
tooling from one Source repo to another.
- _Invariants_: happens without an explicit request only when the incoming
  content is identical to what is installed

### Tracking Work

**Issue Tracker**: The one system of record (e.g., Beads, GitHub Issues) for
this repo's actionable work: each unit of work is an Issue, tracked from filed
to done.
- _Avoid_: backlog, board

**Issue**: One tracked unit of actionable work in the Issue Tracker (e.g., a
bug, a feature, a task), with a status and dependencies on other Issues.
- _Avoid_: ticket

**Issue ID**: An Issue's stable identifier in the Issue Tracker: unambiguous,
but opaque to humans.
- _Invariants_: every reference to an Issue includes its Issue ID

**Branch Issue**: An Issue that holds other Issues as its children: a project,
rather than a unit of work one session finishes. An Issue is a Branch Issue if
it has any children, open or closed, or if it is of a kind designated to hold
children (e.g., an epic), even before it has any. The work of a Branch Issue
is management: scoping, setting success criteria, breaking down into child
Issues, and verifying completion.
- _Avoid_: branch (alone), parent, container

**Leaf Issue**: An Issue that is not a Branch Issue: a unit of work meant to
be claimed and finished in one session (e.g., a task, a bug). A Leaf Issue
that is given a child becomes a Branch Issue.
- _Avoid_: subtask

### Documents

**State doc**: A document that describes one entity (e.g., a design, a plan,
a project's status) as it is at one point in time, by default now, and that is
updated by rewriting its body in place so it always reads as one coherent
picture rather than as a sequence of edits. Examples of State docs include a
project's lexicon, technical design documents (TDDs), product requirements
documents (PRDs), API documentation, user manuals, equipment specifications,
an encyclopedia article, an essay, etc.
- _Invariants_: one owning place per fact, with every other mention a
  reference to it; readable end to end without replaying its history; a
  State doc anchored at a past date states that date in its header and is
  never updated to describe later state

**Stream doc**: A document that records events in the order they happened,
whose value is the record itself; it grows by appending, and an existing
entry changes only to make the record clearer or truer, never to hide or
alter what happened. Examples include a student's transcript, an
accountant's ledger, a recurring meeting-notes doc, a commit log, a user's
daily journal, a project's ADRs, etc. An append-only TODO list, recording
every item ever filed and its completion, is a Stream doc; a list that shows
only the open items, deleted on completion, is a State doc.
- _Invariants_: entries are diffs (what was learned, decided, or done on a
  date), never a restatement of current state; an entry contains nothing
  learned after its date; the current state of anything is never derivable
  only by replaying a Stream doc

## Relationships

- gitw, ghw, fjw, and bdw are Wrappers; each Wrapper offers one or more Verbs.
- Every mutating gitw Verb is scoped by exactly one Roster label and one
  Branch prefix; fjw-pr-comment is scoped by one Branch prefix.
- gitw, ghw, and fjw Verbs report through the Exit-code contract.
- bdw and gitw record the Actor on the writes they attribute: bdw on the Issue
  Tracker, gitw on its commits.
- A Source repo contains exactly one Install Manifest, which declares one or
  more Cohorts.
- A Cohort holds one or more tools, and a tool may belong to more than one
  Cohort; each Cohort installs into exactly one Install Target.
- An Install Target holds exactly one Receipt, which records what each Source
  repo's tooling owns there.
- The Installer is the only writer of Install Targets and Receipts; an
  Adoption moves ownership between two Source repos within one Receipt.
- The Issue Tracker holds many Issues; an Issue has exactly one Issue ID.
- An Issue is either a Branch Issue or a Leaf Issue, never both.
- A Branch Issue has zero or more child Issues; a Leaf Issue has none.
- A Line of Inquiry contains zero or more finer Lines of Inquiry.
- A document as a whole is either a State doc or a Stream doc, never both.
- A State doc may embed one bounded Stream doc section (e.g., a decision
  log, an append-only TODO list) at its end; that section owns events and
  the rest owns facts; a Stream that is unbounded or large lives in its own
  document, referenced from the State doc.

## Retired terms
