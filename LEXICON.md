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
- _Invariants_: when a Verb applies in situations a project may grant
  separately, each situation is a different invocation, so that a Permission
  rule can match it; the token that names the situation comes before every
  argument that varies
- _Avoid_: command, subcommand

**Exit-code contract**: The fixed meaning of an exit status, shared by all
agent-tooling software, that tells the caller what to do next (e.g., proceed,
fix the call, treat it as an answer, ask a human) without knowing which tool
ran or what it runs underneath. The code table lives in
`docs/index.md#exit-code-contract`.

**Actor**: The party, an agent or a person, that carried out an action or a
piece of work and is recorded as having done so.
- _Avoid_: user, author, assignee

**Actor ID**: The identifier recorded for an Actor, unambiguous across every
Actor, agent or person.
- _Invariants_: never shared by two Actors

**Forge identity**: An account on a forge, registered by name in a person's
Machine Config, under which a Wrapper performs an operation (e.g., a machine
account, or the person's own). A Forge identity belongs to one forge; which
ones an agent may act under is granted per repo by Permission rules.
- _Invariants_: named on every forge operation, reads included; resolved by
  the Wrapper from Machine Config, never supplied as a raw account; every
  write made under one is also marked with the Actor ID
- _Avoid_: account, user, actor, persona

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

**Agent integration branch**: A non-default branch a project creates for
agents to land work into unattended, typically for one run and under a
Branch prefix the project's CLAUDE.md designates (e.g., `integrate/` in this
repo). Which branch agents may land into is pinned per run by Permission
rules. The qualifier "agent" marks the separation: an integration branch in
general is any branch work flows into, the default branch included, and a
project that lets agents land into its default branch has no Agent
integration branch, only a default branch agents may land into. Whether
agents may land into a default branch is each project's policy, not this
term's.
- _Invariants_: never the default branch; agents land into one only while
  Permission rules pin that exact branch
- _Avoid_: integration branch (unqualified, for this sense), agent trunk,
  designated base

### Agentic systems

**Skill**: A package, compliant with the agentskills.io standard, that teaches
agents an additional capability.

**Knowledge Skill**: A Skill that teaches knowledge (e.g., a principle, a
fact, a condensed approach to a craft) rather than directing a procedure. Its
description gives a concise distillation of that knowledge, so that it
reaches every session before the Skill is loaded; its body optionally adds
depth that did not fit in the description, and guidance on how to apply the
knowledge.
- _Invariants_: named with the `know-` prefix (e.g., `know-unattended`)

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

**Attended session**: A session in which a person may be asked and is
expected to answer, however the session was launched (e.g., as a background
job).
- _Invariants_: every session is attended unless its prompt declares
  otherwise
- _Avoid_: interactive, foreground

**Unattended session**: A session whose prompt declares that no person will
answer during it.
- _Invariants_: declared by the prompt, never inferred from how the session
  was launched or whether it is headless; an act that would need a person's
  approval is written up as a proposal in the session's report instead of
  attempted
- _Avoid_: background, headless, autonomous

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

### Machine Config and State

**Machine Config**: The settings a person keeps on one machine for
agent-tooling's tools (e.g., which repos a Wrapper may act on, a forge
credential), some of them secret, one part per tool.
- _Invariants_: written by a person or a Verb a person approves, never by a
  tool's routine run; kept only in the Machine Config Directory

**Machine State**: What agent-tooling's tools record on one machine for their
own later runs (e.g., a lock, a record of the last failure, a log), one part
per tool.
- _Invariants_: written only by the tools; deleting it loses no one's work;
  kept only in the Machine State Directory

**Machine Config Directory**: The one directory on a machine that holds all
Machine Config, with one subdirectory per tool.
- _Invariants_: one per machine; never written by the Installer

**Machine State Directory**: The one directory on a machine that holds all
Machine State, with one subdirectory per tool.
- _Invariants_: one per machine; safe to delete as a whole; never written by
  the Installer

### Tracking Work

**Issue Tracker**: A system of record (e.g., Beads, GitHub Issues) for a
repo's actionable work: each unit of work is an Issue, tracked from filed to
done. A repo may use more than one, each Issue having exactly one writable
home.
- _Avoid_: backlog, board

**Issue**: One tracked unit of actionable work in the Issue Tracker (e.g., a
bug, a feature, a task), with an Issue State and dependencies on other
Issues.
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
- _Invariants_: states success criteria, which its verifying pass checks
  against the outcome; ready work exactly when it has no open children; never
  closed without a pass verifying completion
- _Avoid_: branch (alone), parent, container

**Leaf Issue**: An Issue that is not a Branch Issue: a unit of work meant to
be claimed and finished in one session (e.g., a task, a bug). A Leaf Issue
that is given a child becomes a Branch Issue.
- _Invariants_: states acceptance criteria; closed when they hold
- _Avoid_: subtask

### The Tracker Schema

**Tracker Schema**: A repo's declared structure for its Issue Tracker: its
Issue Kinds, Issue Priorities, Issue Label Schema, and Issue State Diagram. It
is bootstrapped from a shipped default and records which revision of that
default it was copied from, so later changes to the default can be shown
against it.
- _Invariants_: exactly one per repo, always present; the repo owner's to
  change; data that grants nothing, since what an agent may do is decided by
  Permission rules alone; read by agents and tooling alike
- _Avoid_: config, workflow configuration, conventions

**Issue Kind**: What sort of thing an Issue is (e.g., a bug, a feature, a
chore), drawn from the set the Tracker Schema declares.
- _Invariants_: every Issue has exactly one; recorded once, in the tracker's
  own mechanism for kind
- _Avoid_: category

**Issue Priority**: An Issue's rank for "what do I work on next?", drawn from
the levels the Tracker Schema declares.
- _Invariants_: every Issue has one from filing on, set as best the filer can
  and adjusted later; lives in exactly one place per repo
- _Avoid_: severity, urgency

**Issue Label**: A tag attached to an Issue to classify it along an axis the
Issue Label Schema declares (e.g., its area), whatever the tracker calls such
tags.
- _Invariants_: drawn from the Issue Label Schema; an unknown label is a
  mistake to fix, not a new label
- _Avoid_: tag

**Issue Label Schema**: The part of the Tracker Schema that declares the
allowed Issue Labels, their meanings, and the axes they classify along.
- _Avoid_: label scheme, taxonomy

**Area Label**: An Issue Label naming the part of the project an Issue
concerns (e.g., `area:skills`).
- _Invariants_: every Issue carries at least one

**Kind Label**: The Issue Label that carries an Issue's Issue Kind on a
tracker that has no native field for kind.
- _Invariants_: exists only where the tracker has no kind field; never used
  beside one

**Issue State Diagram**: The part of the Tracker Schema that declares the
Issue States and the Issue Transitions between them, in natural language, so
that whoever moves an Issue judges the move against it.
- _Invariants_: every Issue State is marked open or closed; the one place
  state meanings and transition conditions are written
- _Avoid_: workflow, lifecycle

**Issue State**: One state an Issue can be in, declared in the Issue State
Diagram with what it means: what kind of attention the Issue needs next.
- _Invariants_: every Issue is in exactly one; recorded once, in the
  tracker's own mechanism for status where it has one, otherwise in the one
  place the Tracker Schema designates; whether an Issue is open or closed
  follows from its Issue State

**Issue Transition**: A move from one Issue State to another, declared in the
Issue State Diagram together with the condition under which it is taken.
- _Invariants_: taken only when its condition holds, judged by whoever moves
  the Issue; a move back to an earlier Issue State is a transition like any
  other

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

**Docs Inbox**: The one place in a project where an agent drops material that
belongs in the project's documentation when it does not know where that
material belongs, so that later tracked work can incorporate it.
Incorporating an item is a judgment, not a move: the item may be moved and
renamed into its proper home, folded into one or more existing documents, or
discarded as already captured or outdated.
- _Invariants_: every item in it is owned by an open Issue to incorporate it;
  nothing is meant to stay in it
- _Avoid_: mailbox, staging, scratch

## Relationships

- gitw, ghw, fjw, and bdw are Wrappers; each Wrapper offers one or more Verbs.
- Every mutating gitw Verb is scoped by exactly one Roster label and one
  Branch prefix; fjw-pr-comment is scoped by one Branch prefix.
- A project has zero or more Agent integration branches; each is distinct
  from the default branch (trunk), and work landed in one reaches the
  default branch only on the project's own terms.
- Every Wrapper and the Installer report through the Exit-code contract; an
  underlying tool's own exit status never reaches the caller.
- bdw and gitw record the Actor on the writes they attribute: bdw on the Issue
  Tracker, gitw on its commits.
- An Actor has exactly one Actor ID.
- A Forge identity belongs to exactly one forge; ghw and fjw perform each
  operation under exactly one Forge identity.
- A write on a forge is recorded under one Forge identity and marked with one
  Actor ID.
- A Source repo contains exactly one Install Manifest, which declares one or
  more Cohorts.
- A Cohort holds one or more tools, and a tool may belong to more than one
  Cohort; each Cohort installs into exactly one Install Target.
- An Install Target holds exactly one Receipt, which records what each Source
  repo's tooling owns there.
- The Installer is the only writer of Install Targets and Receipts; an
  Adoption moves ownership between two Source repos within one Receipt.
- The Machine Config Directory, the Machine State Directory, and the Install
  Targets are distinct directories, none inside another.
- The Roster is part of gitw's Machine Config.
- The Issue Tracker holds many Issues; an Issue has exactly one Issue ID.
- An Issue is either a Branch Issue or a Leaf Issue, never both.
- A Tracker Schema declares the Issue Kinds, Issue Priorities, Issue Label
  Schema, and Issue State Diagram of one repo.
- An Issue has exactly one Issue Kind, one Issue Priority, one Issue State,
  and one or more Issue Labels, at least one of them an Area Label.
- An Issue State Diagram has one or more Issue States and, between any two,
  zero or more Issue Transitions.
- A Branch Issue has zero or more child Issues; a Leaf Issue has none.
- A Line of Inquiry contains zero or more finer Lines of Inquiry.
- A document as a whole is either a State doc or a Stream doc, never both.
- A State doc may embed one bounded Stream doc section (e.g., a decision
  log, an append-only TODO list) at its end; that section owns events and
  the rest owns facts; a Stream that is unbounded or large lives in its own
  document, referenced from the State doc.
- A Knowledge Skill is a Skill; its name begins with `know-`.

## Retired terms
