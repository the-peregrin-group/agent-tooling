---
name: know-issues
description: >
  How this ecosystem tracks work. Each Issue has exactly one writable home.
  The filing bar is a minimum: a title that states the outcome; a body that
  says what is known and what is not, with no placeholder text; and an
  Issue Kind, an Issue Priority, and the entry Issue State, each set as
  best the filer can. A Leaf Issue is one focused task sized for one
  session; anything bigger is a project, tracked by a Branch Issue, whose
  work is management: scoping, setting success criteria, breaking down, and
  verifying completion. One person or agent advances an Issue at a time.
  Judge every move against the repo's Issue State Diagram. What an agent
  may do on a tracker is decided only by reviewed Permission rules; the
  skills carry discipline: when an act is correct, what it must carry, what
  to check first. Load for the full principles before deciding how an Issue
  should be filed, broken down, linked, worked, or closed.
---

# Know: issues

Capitalized terms (Issue, Branch Issue, Leaf Issue, Tracker Schema, Issue
State Diagram, Permission rule, Actor ID, and the rest) are the lexicon's
([LEXICON.md](https://github.com/the-peregrin-group/agent-tooling/blob/main/LEXICON.md)),
and the lexicon is authoritative for them.

The principles below are the approved requirements of the Issue Tracker
skill family, in the maintainer's wording and under their original numbers
([the proposal's appendix](https://github.com/the-peregrin-group/agent-tooling/blob/main/docs/projects/use-issues/2026-11-13-proposal.md#appendix-the-approved-requirements)).
The numbers have gaps: the requirements that are procedures live in the
moment skills.

## The moment skills

The generic skills are split by moment of need (filing, working an Issue,
breaking down a Branch Issue, triage, setup), one skill per moment, written
against no platform.

| Moment | Skill |
|---|---|
| filing | `create-issue` |
| working an Issue | `work-issue` |
| breaking down a Branch Issue | `breakdown-issue` |
| triage | `triage-issues` |
| setup | `setup-issue-tracker` |

## Where Issues live

- **R1.** Each Issue has exactly one writable home, chosen by who drives
  the work: in this ecosystem (ADR 0011), Beads for work agents swarm and
  forge issues for long-lived, low-churn, or human-driven work, and a
  project may use both.
- **R3.** Any Issue text bound off the machine is held to the privacy
  rules (use-privacy) before it is written.

## What agents may do

- **R4.** What an agent may do on a tracker is decided only by reviewed
  Permission rules, granted per operation and per repo at the
  maintainer's choice. Per-repo conventions never grant anything, and an
  agent acts only on its own project's Issues unless expressly permitted.
- **R5.** A denial, refusal, or permission prompt is the policy working:
  fix the call or report the gap, and never look for another spelling or
  reword the text to get past it. Report friction with the tracker; offer
  upstream bug reports, but never file them on your own.
- **R7.** The tracker schema (labels and other tracker structure) is the
  purview of the repo's owner: its design is their call, even when an
  agent helps set it up or change it. The owner is usually the human user,
  but Permission rules are the final arbiter of what an agent may do, so
  making a repo agent-owned means changing a grant, not rewriting skills
  or tools.
- **R9.** Every state change has exactly one recorded owner. The identity
  an agent acts under is one the Permission rules grant for that repo,
  named by the agent and resolved by the Wrapper, never supplied as a raw
  account. The Actor ID is recorded on every write, whatever identity it
  ran under; when an agent acts under a person's account, that record is
  what keeps its acts distinguishable from the person's.
- **R10.** An agent sharing its session's Actor ID (a sub-agent, a workflow
  agent) does not claim, close, or rewrite: a limitation to close, not a
  principle.
- **R46.** Changing or destroying existing data requires more delegation
  than purely additive change. Within that, less judgement is needed when
  the action merely executes an existing, already-authorized plan (forming
  Issues from a design document's scope, say), and more when the agent is
  making the decision itself rather than carrying one out (inferring a new
  overarching project and reparenting existing Issues under it). Dangerous
  operations whose policy must be foolproof are gated on the operation
  itself.
- **R48.** Policy (who may do what) lives in Permission rules, and leaves
  the skills wherever the system can express it as a grant: if the grant
  exists, the agent does the act; if not, the call is denied or asked, and
  that is the answer. Only where Permission rules cannot separate the
  situations does a skill say which situation calls for which invocation.
  Discipline (when an act is correct, what it must carry, what to check
  first) stays in the skills; it is not a grant and never says who may
  act.

## Filing

- **R12.** Capture is never blocked: file with what you know and say
  honestly what is unknown, never with placeholder text. No Issue is
  empty.
- **R13.** The title states the outcome; the body says what and why, and
  what done looks like as far as it is known, so someone outside the
  conversation can pick it up.
- **R14.** Proactively file Issues for needed work discovered in the course
  of other work; do not leave it undocumented or deferred to "future
  sessions".
- **R15.** Where permissions are graded, the right to file an Issue
  includes the right to edit Issues you filed, even without the right to
  edit Issues in general. Classifying and refining an Issue is part of
  filing it: a filer who cannot correct their own mistakes or record what
  they learn cannot meet the responsibility filing gives them. Like any
  grant, this can be limited or withdrawn.
- **R16.** Every Issue has exactly one kind, recorded once in the tracker's
  own mechanism for kind, and is classified by the project's declared
  scheme.
- **R18.** Priority lives in exactly one place per repo and exists to
  answer "what do I work on next?"
- **R49.** The filing bar is the same on every tracker, and it is a
  minimum: a title that states the outcome; a body that says what is known
  and what is not, with no placeholder text; and an Issue Kind, an Issue
  Priority, and the entry Issue State, each set as best the filer can. A
  more complete Issue is welcome, so long as it states what is known rather
  than presuming what is not: technical design and implementation choices
  are not the filer's to settle at filing, least of all when filing into a
  project whose context the filer lacks. Everything beyond the minimum (a
  pointer, reproduction steps, criteria) is a condition on a later Issue
  Transition, not on filing.

## Breakdown

- **R20.** A Leaf Issue is one focused task sized for one session, whether
  an agent or a human does it. Anything bigger is a project, not a task,
  and is tracked by a Branch Issue whose children are Leaf or Branch
  Issues; it is never shoehorned into a Leaf Issue. A Leaf Issue that
  proves bigger than a session is reorganized as a Branch Issue and broken
  down into session-sized children. "Session-sized" is a subjective,
  best-effort guideline: a task that runs past one session simply carries
  into the next, with no extra Issues. Split off a sibling Issue only when
  the remainder cannot be done now, or is substantial.
- **R21.** A Branch Issue's work is management: scoping, setting success
  criteria, breaking down, and verifying completion. It is worked in
  session-sized passes, is ready exactly when it has no open children, and
  is never closed merely because its children closed.
- **R23.** An Issue goes under a parent only when its scope is part of the
  parent's scope: work bigger than a session is a Branch Issue, broken
  down into children. A dependency or a shared schedule is never by itself
  a reason to group; link it instead. Prefer vertical slices and do not
  over-decompose. A parent's status is judged against its own definition
  and criteria, not on the state of its children.

## Relationships

- **R25.** Record every relationship with its type explicit; blocking is
  never the default, because a wrong blocking link silently hides work.
- **R26.** A relationship lives in the tracker's native link, which is its
  source of truth; prose about it in a body is narrative only.
- **R28.** Work waiting on a person shows as waiting on that person, and
  everything waiting on the human sits in one queue they can see.

## Lifecycle

- **R29.** Status answers "what kind of expert attention does this Issue
  need next?"
- **R30.** An Issue may regress to an earlier state at any time; no
  later-stage work goes on top of an earlier stage's gap; open-or-closed
  always agrees with status.
- **R32.** Choose work explicitly; before touching it, at any stage and not
  only implementation, make it visible that you are working on it, since
  one person or agent advances an Issue at a time; as you go, append what
  you learn to the Issue it belongs to, regardless of who filed it or who
  has claimed it; close it when its criteria hold; before you stop, close
  or release everything you hold. Never take over someone else's work in
  progress; ask.
- **R33.** An Issue is a living document: its description is its current
  state, rewritten in place, and its comments are an append-only log.
- **R34.** A fresh session can resume any Issue from the tracker alone: the
  Issue points to context kept in the project's standard documents rather
  than holding it.
- **R43.** Context whose proper document is unknown goes to the project's
  Docs Inbox, where an open Issue owns incorporating it. A project without
  a Docs Inbox keeps it in the Issue's description.
- **R50.** Every repo has a Tracker Schema, bootstrapped from the shipped
  default and recording the revision it was copied from; every edit to it
  is that repo's customization. Its Issue State Diagram holds all state
  meanings and transition conditions, in natural language, with one
  structural attribute per Issue State: open or closed. The skills say
  nothing about states beyond "judge every move against the repo's Issue
  State Diagram". The ready queue is defined by the agent: unclaimed,
  unblocked Issues in the Issue States it works.

## Closing and linkage

- **R35.** Every close and every reopen carries its reason; forge
  auto-close on PR merge is the one exception; reopening needs more
  authority (a higher permission tier) than closing.
- **R36.** An Issue is closed, not deleted; the closed Issue stays as the
  record. Deleting one is irreversible and is gated by permission like any
  other irreversible act: not-correctable is the floor, and the test is a
  judgement over harm, detection latency, and compounding, made when tiers
  are designed.
- **R37a.** An Issue is done only when everything that describes it agrees
  with the change.
- **R37b.** Every TODO comment cites a real Issue, filed first, and is
  cleaned up when that Issue closes.
- **R38.** Every reference to an Issue includes its Issue ID, and in text
  meant for people, a few words of what the Issue is.
- **R39.** A PR or commit says whether it finishes an Issue or only
  advances it.

## Triage

- **R40.** Filing-time checks are best effort; a separate batch pass across
  the whole tracker reconciles what they miss.
- **R42.** Judge recency and staleness from exact timestamps compared with
  the current time, never from rendered dates.
