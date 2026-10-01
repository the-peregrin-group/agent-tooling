# home-in: design

State as of 2026-09-30.

`/home-in` is a user-invoked Skill for arriving at an opinion. The user
names a problem and a desired outcome ("I have X and want to home in on
Y"); the agent interrogates them across the whole decision space, gathers
and verifies against what already exists, pressure-tests every proposition
including its own, and captures the result as a coherent artifact plus
whatever lexicon entries and ADRs the discussion earns. It is a wise
steward, not a note-taker: the interrogation is the product, and the
documents are its record.

## Problem

Design conversations between a human and an agent produce good thinking
and lose most of it. Decisions are made in passing and never recorded.
Concepts get names by accident. The "design doc" that results is a
transcript in disguise, or is written at the end from a tired memory. And
the agent, by default, asks whatever question occurs to it next, so
neither party can see which parts of the problem have been examined and
which were merely mentioned.

The skill applies to any domain where an opinion must be reached and
defended: a product's next move, a software design, a career decision, an
essay's thesis, a review of someone else's proposal. Everything below is
domain-agnostic; the domain enters only through the tree of Lines of
Inquiry.

## Success

A home-in session has succeeded when the user holds an opinion on Y that
they can defend cold, and the artifact records that opinion, its premises,
its success criteria, and why the rejected paths were rejected, well enough
that a reader with no access to the conversation can follow it.

The skill has succeeded when an agent following it produces that outcome
without the user having to steer the process itself.

## The process

### Attended only

home-in is live collaboration and has no unattended form (see
[ADR 0004](../../adr/0004-home-in-is-attended-only.md), which records the
decision and the rejected unattended-over-a-brief alternative). The skill
is model-invocable: Claude Code parses a slash command only as the first
token of a message, and the natural way to ask for it is mid-sentence
("help me /home-in on whether to quit"), which only the model path can
honor. So the frontmatter does not set `disable-model-invocation`, and the
description is kept narrow (the literal phrases "home in on," "/home-in,"
"hone in on," and "zero in on") so the skill does not fire on ordinary
decision-making help. The body states attended-only. None of the
downstream skills' unattended branches (lexicon proposals, draft ADRs for
a reviewer) apply within it.

### Opening move

Before the first question, the agent:

1. Loads `use-lexicon`, `use-adrs`, and `refine-state-doc`, and reads the
   owning project's lexicon.
2. States the owning project. It is the session's root by default and can
   be overridden in the invocation; whether an override succeeds is decided
   by the machine's own policy, not by the skill.
3. Reads what already exists: documents the invocation named, and whatever
   the project holds about the topic. It reports what that material
   establishes and what it leaves open. When the invocation arrives with a
   proposal (a PRD, a plan), this report is the first pressure test of it.
4. Asks what the deliverables are. There is no default location or format.
   The agent proposes one from the project's own layout and conventions,
   so the user can accept in a word, but writes nothing until the user
   answers. Project conventions inform this proposal only; they do not
   alter the skill's rules.
5. Sketches the tree of Lines of Inquiry for this domain one level deep, a
   dozen lines or so, for the user to prune or extend before it is walked.

### Three sub-processes, interleaved

The interrogation is three activities running concurrently, not in
sequence:

- **Gather.** Read what exists before asking. An answer that names a
  checkable asset (a project, a document, a past event the project has
  notes on) triggers gathering before the next question, and that
  gathering verifies the user's account against the record, not only fills
  gaps. A discrepancy comes back to the user plainly, with its source,
  before the interrogation continues. Gathering that no immediate question
  depends on goes on the Resolution Queue and is cleared at the next
  natural pause, because a subagent between every turn destroys
  conversational momentum. Every pause is narrated in one line.
- **Interrogate.** One question per turn, always. Each question belongs to
  a node of the tree of Lines of Inquiry, and a Line of Inquiry is walked
  to the bottom before the next is entered.
- **Pressure-test.** Always on. The adversary targets the strongest
  current proposition: the premises when nothing is on the table yet, the
  user's proposal when one arrived with the invocation, and the agent's
  own emerging recommendation once one forms, with equal vigor. Every
  adversarial question names the assumption it tests, and that assumption
  goes on the Resolution Queue. Devil's advocacy with no named assumption
  is not allowed.

There are no modes. The invocations differ only in what is already on the
table when the session opens.

### The tree of Lines of Inquiry

A Line of Inquiry (LOI) is one line of questioning that must be examined
before an opinion is defensible. The skill ships ten root LOIs, each the
root of a subtree that the agent expands into the domain from its own
knowledge. The skill encodes the roots and the expansion rule, never the
domain trees, which are unbounded and differ completely between a software
design, a kitchen remodel, and an essay. One example expansion is included
to calibrate depth, labeled as one domain's tree and not a template.

The root Lines of Inquiry:

1. **Trigger.** Why this, why now, and what happens if nothing changes.
2. **Success.** What good looks like and how the user would know.
3. **Anti-goals.** What must not happen; what will not be traded away.
4. **Stakeholders.** Who is affected, who decides, whose input is missing.
5. **Constraints.** Time, money, skill, dependencies; what is fixed versus
   assumed fixed.
6. **Load-bearing assumptions.** What must be true for the leading option
   to work, and how each could be falsified. Most adversarial questions
   attach here.
7. **Alternatives.** Including doing nothing, and the option the user has
   been avoiding naming.
8. **Reversibility and horizon.** How long until it is known to have
   worked; what undoing it costs.
9. **Pre-mortem.** A year on, it failed. Why.
10. **Disconfirmation.** What evidence would change the user's mind, and
    whether any of it already exists.

A root LOI is a subtree, not a question. Twenty questions on Success is
expected. Every LOI is considered and not every LOI is asked: each is
either explored to the depth the problem warrants or set aside with a
one-line reason. Expansion is lazy (a subtree expands when entered) and
depth-first. The agent's coverage report is the tree's frontier: exhausted,
in progress, untouched, set aside.

The ten roots are a taxonomy under test. At each Line of Inquiry Exit the
agent surfaces any question it wanted to ask that fit no root, so the
roots can be refined against use rather than trusted.

### Line of Inquiry Exits and capture

A Line of Inquiry Exit (LOI Exit) is the event of leaving a LOI, exhausted
or set aside. It is the only moment at which the formal capture machinery
runs, so the interrogation is never derailed by ceremony (see
[ADR 0003](../../adr/0003-capture-at-line-of-inquiry-exits.md), which
records the decision to capture at exits rather than inline or at
wrap-up). At a LOI Exit the agent:

1. Reports the frontier and the Resolution Queue.
2. Surfaces questions that fit no root LOI.
3. Drains the Resolution Queue's items from that LOI: the lexicon naming
   procedure for each candidate term, one concept per turn; the ADR gate
   for each candidate decision, drafting those that pass.
4. Rewrites the artifact in place.

Between exits, capture is deferred but definition is not. When a
discussion cannot proceed without a concept, the agent runs the identity
step of the lexicon naming procedure inline ("what is this, independent of
how it is built?") and gives the concept a working name, marked as such in
prose the first time it appears and on the Resolution Queue. A working
name is spent, not chosen: the plainest available description, with no
candidate generation, so nobody grows attached to it. Every working name
must be resolved (ratified, renamed, or dropped) at the next LOI Exit;
none survives into the artifact unratified, and one that crosses an exit
unresolved is a failure the exit report calls out. Provisional decisions
("assume X for now") work the same way and need no extra rule.

### The Resolution Queue

The Resolution Queue is the set of everything raised during the
interrogation that awaits formal resolution: candidate terms with their
working names, candidate decisions, assumptions under test, and gathering
not yet done. It appears at the foot of the agent's replies and lives in
the artifact's open-items section between exits, so it survives a dropped
session. It must be empty before the session is done.

### The artifact

The agent produces whatever deliverable the user asked for. The default,
when the user has no format in mind, is a state doc in the sense of
`refine-state-doc`: a coherent picture as of the wrap-up, with context,
problem, success criteria, recommendation, rationale, and rejected paths.
It never preserves the conversation's turn order or who said what; the
transcript is `save-log`'s job. It is drafted at the first LOI Exit and
rewritten in place at every exit after, so the wrap-up is a final rewrite
rather than a big-bang authoring step, the user can catch a misreading
early, and the Resolution Queue has a durable home.

### ADRs and the artifact

ADRs and the artifact overlap on purpose (see
[ADR 0006](../../adr/0006-adrs-duplicate-their-motivating-document.md),
which records the decision against deduplication and the rejected
two-tier alternative). An ADR is a stream doc, a minute of the meeting: it
snapshots a decision's context, rationale, and alternatives at the moment
of decision, and it must carry them itself, because the artifact that
motivated it is a state doc that may be rewritten later. The artifact is
where the full analysis lives, and it is the source of truth for the
design going forward. Neither points at the other instead of stating its
own content; the artifact refers to every ADR it touches with an inline
summary plus a link, never a bare code. There is no deduplication policy.

An ADR's core (Context, Decision, Rationale) has fixed limits in every case.
Alternatives Considered is never omitted, since the gate guarantees
alternatives existed, and it is the one section that flexes: one sentence
per description and rejection rationale when a state doc holds the
analysis and Context links it; unbounded rejection rationale, cut to what
prevents relitigation, when the ADR stands alone. The same rule is being
written into `use-adrs`; see Deliverables of this design.

### Wrap-up

Done is the user's to declare. Before agreeing, the agent reports the
frontier and the Resolution Queue, both expected empty; the user can
overrule with a word. It then offers, and runs only on request:

- **A cold read.** A subagent is given the artifact alone and asked to
  state the problem, the success criteria, the recommendation, and why the
  rejected paths lost. The test is whether the artifact stands on its own,
  not whether the user agrees with it.
- **An independent review.** A separate agent, given the artifact and the
  session's new ADRs and nothing else, writes a judicial opinion for the
  user: it may attack the premise, dismantle the argument, reject the
  conclusion, or offer a counterproposal. Its brief is a verdict, not
  polish. It writes the opinion to a file, and the authoring agent relays
  it verbatim with the path, adding its own response only under a separate
  heading. The reviewer never sees the conversation or the Resolution
  Queue; its blindness to the path is what makes the verdict cold (see
  [ADR 0005](../../adr/0005-independent-review-delivered-unfiltered.md),
  which records why the reviewer is separate and unfiltered and the
  rejected self-review and polish-loop alternatives).
- **Both.**

The offer names the risk it addresses in one line, and the agent recommends
both when the session ran past a handful of LOI Exits.

Early exit is a normal outcome. "Park it" triggers a LOI Exit rewrite,
leaves the frontier and Resolution Queue in the artifact's open-items
section, and offers `/handoff`. Resuming is "/home-in, continue from
`<artifact>`."

### Two rules that must be written in

One question per turn, and inline summaries on opaque ids (an issue
number, an ADR number, a commit, a bead id, a section letter: the first
mention in a turn pairs the id with a few words of meaning, and hash-like
ids get the summary every time), are rules the skill's author holds in
user-level instructions that no other installer of the skill will have.
Both are load-bearing for home-in and are written into it. The reason for
the second is that human memory retrieves by meaning, not by identifier,
and every bare id is a separate lookup that fragments attention.

## Deliverables of a session

1. The artifact, as the user specified it at the opening move.
2. Lexicon entries, through `use-lexicon`, for concepts that met its bar.
3. ADRs, through `use-adrs`, for decisions that passed its gate.

Lexicon and ADR placement is those skills' business; home-in has no
opinion on it. Either of the last two may legitimately be empty, and the
wrap-up says so in one line rather than omitting it silently.

## Deliverables of this design

- `skills/home-in/`, three files on the pattern of `use-adrs`. `SKILL.md`
  carries the process and the ten roots, since they are needed from the
  first turn and held throughout. `lines-of-inquiry.md` holds the roots in
  full, the expansion rule, coverage, and one example expansion for a
  software design, labeled as one domain's tree. `wrap-up.md` holds the
  procedures read at the point of use, because instructions loaded at turn
  one are remembered loosely hours later: the Line of Inquiry Exit steps,
  the wrap-up check and offers with the reviewer's brief verbatim, closing,
  and park-and-resume. The second file has no agent-side benefit over
  inlining and exists for human navigation; the third earns its split on
  recency.
- This document.
- Lexicon entries in this repo's `LEXICON.md`, written: Line of Inquiry,
  Line of Inquiry Exit, Resolution Queue. The independent reviewer's
  opinion was judged not to need a term: it is mentioned rarely and
  "judicial opinion" already names it.
- ADRs in `docs/adr/`, written: capture at Line of Inquiry Exits
  ([ADR 0003](../../adr/0003-capture-at-line-of-inquiry-exits.md));
  attended-only ([ADR 0004](../../adr/0004-home-in-is-attended-only.md));
  independent review delivered unfiltered
  ([ADR 0005](../../adr/0005-independent-review-delivered-unfiltered.md));
  ADRs duplicate their motivating document
  ([ADR 0006](../../adr/0006-adrs-duplicate-their-motivating-document.md)).
  The no-modes decision was judged not to pass the gate and is recorded
  under Rejected paths instead.
- Four edits to `skills/use-adrs/writing-adrs.md`, in their own commit,
  each closing a gap this design exposed.
  1. A paragraph stating that an ADR is a self-contained snapshot and
     duplicates its motivating document's context on purpose, because that
     document is state and may change.
  2. The core sentence limits made explicitly hard, with Alternatives
     Considered as the section that flexes, in the compact and standalone
     forms described above, and never omitted.
  3. Context links the motivating state doc when one exists.
  4. The citation rule replaced: inline summary plus link, never a bare
     `ADR-XXXX`. The current rule is also out of step with this repo's own
     practice, which already writes "ADR 0001" in prose and links as
     `[ADR 0002](docs/adr/0002-beads-identity.md)`.

## Rejected paths

Each of these looked right at some point in the design and is recorded so
it is not relitigated. Where an ADR exists, its Alternatives Considered
holds the same rejection in snapshot form.

- **Capture inline, as concepts and decisions arise.** The lexicon naming
  procedure takes two turns per term and an ADR can only be written once a
  decision has landed, so inline capture derails every insight into
  ceremony. Rejected for capture at LOI Exits with inline identity and
  working names.
- **Three modes (exploration, synthesis from sources, adversarial
  review).** They differ only in the starting state, not the process:
  gathering applies even with no documents given, and pressure-testing
  applies even with no proposal given. Rejected for three always-on
  sub-processes.
- **A default artifact location (`meta_docs/` or `docs/`).** The
  deliverable is sometimes a revised existing document, not a new note, so
  a location default silently produces the wrong kind of artifact.
  Rejected for asking at the opening move with a project-informed
  proposal.
- **Deduplicating rationale between ADRs and the artifact.** Stream-doc
  versus state-doc confusion: an ADR must carry its own snapshot because
  the artifact may be rewritten. Rejected for deliberate overlap.
- **Two ADR length tiers, terse with a design doc and longer standalone.**
  The terse tier cannot be shorter than the snapshot minimum, and a longer
  tier is a mode agents will select for themselves. Rejected for fixed
  core limits with Alternatives Considered as the flex section.
- **The authoring agent pressure-tests the composed conclusion at
  wrap-up.** The authoring agent climbed the same ladder as the user and
  is anchored on every step; it is the wrong entity to attack the whole.
  Rejected for an independent reviewer blind to the path.
- **Asking the user "do you hold this opinion without the document?"** A
  weak instrument for a real hazard (a chain of locally reasonable
  ratifications adding up to a conclusion the user would not endorse
  cold), and a new mechanism where an existing one fits. Rejected for the
  independent review.
- **Skill-level awareness of the user's knowledge-base repo.** The owning
  project is overridable at invocation and local policy decides whether
  the override succeeds; the skill needs no notion of any particular
  repo. Rejected as out of scope.
- **Enforcing attended-only with `disable-model-invocation: true`.** The
  flag would make the skill unreachable from the mid-sentence phrasing
  that is its natural invocation, since the parser recognizes a slash
  command only as a message's first token. Rejected for a narrow
  description and a stated rule.
- **Naming the formal capture step.** It is simply what happens at a Line
  of Inquiry Exit; the lexicon defines the event, and the skill prescribes
  the behavior. Rejected as a term.

## Open items

As of 2026-09-30 the frontier is exhausted and the Resolution Queue is
empty. One Line of Inquiry was set aside with a reason: stakeholders beyond
the author, since the skill's other users are agents and the design
addresses them directly. Two things are deliberately left to be learned
from use rather than decided now: whether the ten root Lines of Inquiry
hold up, which the surfaced-unfitted-questions rule exists to test, and
whether agents over-index on the example expansion.
