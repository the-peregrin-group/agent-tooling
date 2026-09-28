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
scopes a mutating gitw Verb, and that Permission rules pin when granting it.

### Agentic systems

**Skill**: A package, compliant with the agentskills.io standard, that teaches
agents an additional capability.

**Agent definition**: A package that defines a specialized agent (e.g., its
role, instructions, and permitted capabilities) that another agent can spawn
to carry out a delegated task. An agent is the running session; an Agent
definition is what it is spawned from.
- _Avoid_: agent

**Permission rule**: A declared rule that decides whether an agent may take an
action on its own, only with a human's approval, or never.
- _Invariants_: enforced programmatically, never left to agent judgment
- _Avoid_: allowlist, permission row

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

## Relationships

- gitw, ghw, fjw, and bdw are Wrappers; each Wrapper offers one or more Verbs.
- Every mutating gitw Verb is scoped by exactly one Roster label and one
  Branch prefix.
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

## Retired terms
