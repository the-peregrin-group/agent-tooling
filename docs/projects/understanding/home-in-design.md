# home-in: design

State as of 2026-09-30.

`/home-in` is a Skill the user asks for by name, for arriving at an
opinion. The user
names a problem and a desired outcome ("I have X and want to home in on
Y"); the agent interrogates them across the whole decision space, gathers
and verifies against what already exists, pressure-tests every proposition
including its own, and captures the result as a coherent artifact plus
whatever lexicon entries and ADRs the discussion earns. It is a wise
steward, not a note-taker and not a critic: the interrogation is the
product, the documents are its record, and it pressure-tests the
proposition, never the person.

## Problem

Design conversations between a human and an agent produce good thinking
and lose most of it. Decisions are made in passing and never recorded.
Concepts get names by accident. The "design doc" that results is a
transcript in disguise, or is written at the end from a tired memory. The
user's account of what happened drifts from what they wrote down at the
time, and nobody checks. And the agent, by default, asks whatever question
occurs to it next, so neither party can see which parts of the problem
have been examined and which were merely mentioned.

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

The skill verifies only the second half of that criterion. Its checks test
whether the artifact stands on its own and whether the conclusion follows
from its premises; none of them can verify that the user holds the
opinion, and the one instrument that could, the user restating the whole
case cold, costs more time and energy than the session saved and so
defeats the skill. This gap is accepted deliberately: a chain of small
ratifications may drift to a conclusion the user would not have endorsed
cold, and the skill mitigates that risk in proportion to stakes (see
Wrap-up) rather than eliminating it. The alternative is the user writing
everything themselves and asking agents to review it for coherence, which
is the authoring burden the skill exists to deflate.

## The process

### Attended only

home-in is live collaboration and has no unattended form: an interrogation
with no one to answer it produces the agent's opinion dressed as the
user's, and every other skill's unattended branch would have to be
mirrored here for a case that does not exist (see
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

Before the first question of the interrogation, over as many turns as it
needs with each turn still ending in one question, the agent:

1. Loads `use-lexicon`, `use-adrs`, and `refine-state-doc`, reads the
   roots file, and reads the owning project's lexicon.
2. States the owning project: the repo or directory whose conventions the
   deliverables follow and whose lexicon and ADRs are used. It is the
   session's root (the directory the session started in) by default and
   can be overridden in the invocation; whether an override succeeds is
   decided by the machine's own permission rules, not by the skill.
3. Reads what already exists: documents the invocation named, and whatever
   the project holds about the topic. It reports what that material
   establishes and what it leaves open. When the invocation arrives with a
   proposal (a PRD, a plan), this report is the first pressure test of it.
4. Asks what the deliverables are. There is no default location or format.
   The agent proposes one from the project's own layout and conventions,
   so the user can accept in a word, but writes nothing until the user
   answers. Project conventions inform this proposal only; they do not
   alter the skill's rules.
5. Sketches the tree of Lines of Inquiry for this domain one level deep,
   one line per root naming the domain's first-level children under it,
   for the user to prune or extend before it is walked, and says how deep
   it intends to go and why. Depth costs the user time and energy, not
   tokens. There is no formal budget, which would be a mode by another
   name; the user steers depth throughout, and the skill makes the steer
   easy to give (see Line of Inquiry Exits and capture).
6. Asks whether this session's wrap-up should include the independent
   checks, given the stakes and reversibility just described. The answer
   is not binding; it is recorded, and at wrap-up the agent recalls it in
   one sentence if the user decides differently, then accepts their
   choice. Stakes are assessed before any chain of ratifications has
   formed, so this answer is the user's uncontaminated judgment, offered
   back to them later as a nudge rather than a rule.

### Three sub-processes, interleaved

The interrogation is three activities running concurrently, not in
sequence:

- **Gather.** Read what exists before asking. An answer that names a
  checkable asset (a project, a document, a past event the project has
  notes on) triggers gathering before the next question, and that
  gathering verifies the user's account against the record, not only fills
  gaps. A discrepancy comes back to the user plainly, with its source,
  before the interrogation continues. Gathering that no immediate question
  depends on goes on the Resolution Queue and is done when the
  conversation next pauses anyway, or at the Line of Inquiry Exit at the
  latest, because a subagent between every turn destroys conversational
  momentum. Every pause is narrated in one line.
- **Interrogate.** One question per turn, always. Each question belongs to
  a node of the tree of Lines of Inquiry, and a Line of Inquiry is walked
  to the bottom before the next is entered.
- **Pressure-test.** Always on. The adversary targets the strongest
  current proposition: the premises when nothing is on the table yet, the
  user's proposal when one arrived with the invocation, and the agent's
  own emerging recommendation once one forms, with equal vigor. Every
  adversarial question names the assumption it tests, and that assumption
  goes on the Resolution Queue. Devil's advocacy with no named assumption
  is not allowed. An adversarial question belongs to the Line of Inquiry
  being walked and opens no other; the Load-bearing assumptions root is
  where the assumptions queued along the way are collected and tested
  systematically. Depth-first and always-on therefore coexist, and exits
  stay discrete events.

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
   to work, and how each could be falsified. Where the assumptions queued
   by adversarial questions are tested systematically.
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
in progress, untouched, set aside, reopened. An exhausted LOI reopens when
a later finding reframes it, as a late-discovered alternative often does to
Success or Anti-goals; the reopening is reported and the LOI is walked and
exited again.

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

1. Reports the frontier and the Resolution Queue, ending with roots done,
   roots remaining, and the depth prompt: "deeper, shallower, or as we
   are?" An absorbed user does not notice time and energy passing, so the
   steer is handed to them at the moment they are least likely to reach
   for it, and honored immediately.
2. Surfaces questions that fit no root LOI.
3. Drains the Resolution Queue's items from that LOI: the lexicon naming
   procedure for each candidate term, one concept per turn; the ADR gate
   for each candidate decision, drafting those that pass; each assumption
   under test confirmed, refuted, or carried forward with a reason; each
   pending gathering done or dropped with a reason.
4. Rewrites the artifact in place.

Between exits, capture is deferred but definition is not. When a
discussion cannot proceed without a concept, the agent runs the identity
step of the lexicon naming procedure inline ("what is this, independent of
how it is built?") and gives the concept a working name, marked as such in
prose the first time it appears and on the Resolution Queue. A working
name is spent, not chosen: the plainest available description, with no
candidate generation, so the naming discussion is not pre-empted by a name
the agent has invested in. (Plain working names may well be ratified as
the final terms, as three were in this design; that is the user choosing
literal clarity, not the name sticking.) Every working name
must be resolved (ratified, renamed, or dropped) at the next LOI Exit;
none survives into the artifact unratified, and one that crosses an exit
unresolved is a failure the exit report calls out. Provisional decisions
("assume X for now") work the same way and need no extra rule.

### The Resolution Queue

The Resolution Queue is the set of everything raised during the
interrogation that awaits formal resolution: candidate terms with their
working names, candidate decisions, assumptions under test, and gathering
not yet done. It appears at the foot of the agent's reply whenever it has
changed and always at an exit, since a queue repeated unchanged on every
turn is noise competing with the one question, and it lives in the
artifact's open-items section between exits, so it survives a dropped
session. It must be empty before the session is done.

### The artifact

The agent produces whatever deliverable the user asked for. The default,
when the user has no format in mind, is a state doc in the sense of
`refine-state-doc`: a coherent picture as of the wrap-up, with context,
problem, success criteria, recommendation, rationale, and rejected paths.
It never preserves the conversation's turn order or who said what; it is
not a transcript. It is drafted at the first LOI Exit and
rewritten in place at every exit after, so the wrap-up is a final rewrite
rather than a big-bang authoring step, the current picture is there for
the user to read at any exit they choose to, and the Resolution Queue has
a durable home.

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
overrule with a word. It then offers three checks, singly or combined, and
runs only what is asked for:

- **The user's own summary.** Three sentences, spoken before the final
  rewrite is shown, without the document: what they will do, why, and what
  they rejected. Someone who holds the opinion produces it in a minute;
  divergence from the artifact is the finding. Never more than three
  sentences, because a full restatement would cost more than the session
  saved.
- **A cold read.** A subagent is given the artifact alone and asked to
  state the problem, the success criteria, the recommendation, and why the
  rejected paths lost. The test is whether the artifact stands on its own,
  not whether the user agrees with it.
- **An independent review.** A separate agent, given the artifact, the
  session's new ADRs, the owning project's lexicon, and the sources the
  artifact cites, and nothing else, writes a judicial opinion for the
  user: it may attack the premise, dismantle the argument, reject the
  conclusion, or offer a counterproposal. Its brief is a verdict, not
  polish. It writes the opinion to a file, and the authoring agent relays
  it verbatim with the path and nothing of its own in that turn; the
  author's response comes only later and only if asked, since an attack
  read together with the anchored party's defense is a filter by framing.
  The reviewer never sees the conversation or the Resolution Queue: it is
  blind to the path, not to the world, so it can test whether the premises
  are true and not only whether the argument coheres (see
  [ADR 0005](../../adr/0005-independent-review-delivered-unfiltered.md),
  which records why the reviewer is separate and unfiltered and the
  rejected self-review and polish-loop alternatives). The user is told in
  one line that the reviewer is the same model with different inputs: it
  corrects for anchoring on the path, not for biases the model brings to
  any well-structured document.

The offer names the risk it addresses in one line. The agent's
recommendation follows the stakes and reversibility surfaced under
Reversibility and horizon, never the number of exits: exit count is a
proxy for chain length, which the user cannot assess from inside, while
stakes are what they can. A decision cheap to undo needs no review; one
with years of consequences deserves all three. If the user answered the
opening-move question about these checks and now chooses differently, the
agent recalls that answer in one sentence and then accepts their choice.

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
the first is that several questions at once get partial answers, and the
unanswered ones must be asked again, so the conversation fragments and
repeats. The reason for the second is that human memory retrieves by
meaning, not by identifier, and every bare id is a separate lookup that
fragments attention.

## Deliverables of a session

1. The artifact, as the user specified it at the opening move.
2. Lexicon entries, through `use-lexicon`, for concepts that met its bar.
3. ADRs, through `use-adrs`, for decisions that passed its gate.

Lexicon and ADR placement is those skills' business; home-in has no
opinion on it. Either of the last two may legitimately be empty, and the
wrap-up says so in one line rather than omitting it silently.

## Deliverables of this design

- `skills/home-in/`, three files on the pattern of `use-adrs`, a short
  SKILL.md with reference files beside it. `SKILL.md` carries the process
  and reads the other two at the moments they are needed.
  `lines-of-inquiry.md` is authoritative for the ten roots, the expansion
  rule, coverage, and one example expansion for a software design, labeled
  as one domain's tree; it is read at the opening move. `wrap-up.md` holds
  the procedures read at the point of use, because instructions loaded at
  turn one are remembered loosely hours later: the Line of Inquiry Exit
  steps, the wrap-up check and offers with the reviewer's brief verbatim,
  closing, and park-and-resume. The roots file has no agent-side benefit
  over inlining, since it is loaded on turn one every time, and exists for
  human navigation; the wrap-up file earns its split on recency.
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
  The gate, from `use-adrs`, is three criteria that must all hold: several
  compelling options, expensive to reverse, surprising without the
  background. Every skill decision is cheap to reverse in the file itself,
  so the second criterion turns on what has been built on the decision; the
  four above each carry structure (the Resolution Queue and working names,
  the absence of unattended branches, the review protocol, every future
  ADR's shape). The no-modes decision carries nothing and surprises nobody
  once the three sub-processes are described, so it failed the gate and is
  recorded under Rejected paths instead.
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
  yes/no is a proofread of one's own conviction, which the acclimatized
  user cannot perform. Rejected; the three-sentence summary at wrap-up is
  what survived of the idea.
- **A mandatory restatement of the whole case by the user at wrap-up.**
  The one instrument that would measure the success criterion directly,
  and it costs the user more time and energy than the session saved, which
  is the authoring burden the skill exists to deflate. Rejected; the gap
  is accepted and stated under Success.
- **Running the independent review by default.** The argument for it was
  that insiders cannot detect their own drift and so should not decide
  whether to run the detector. But assessing stakes is a different act
  from detecting drift and does not require seeing the path, and reading
  and digesting a review costs real time; for a low-stakes decision it is
  not worth it. Rejected for offered checks, recommended by stakes, with
  the user's own opening-move answer recalled as a nudge.
- **A binding pre-commitment at the opening move to run the checks.** The
  right idea in a perfect world; softened to a recorded, non-binding
  answer that is recalled at wrap-up if the user deviates.
- **A formal depth budget in turns.** A mode by another name. Rejected for
  the depth prompt at every exit.
- **Skill-level awareness of the user's knowledge-base repo.** The owning
  project is overridable at invocation and local policy decides whether
  the override succeeds; the skill needs no notion of any particular
  repo. Rejected as out of scope.
- **An unattended home-in over a written brief.** The questions would have
  no one to answer them, so nothing would distinguish the result from the
  agent's own analysis. Rejected for attended-only.
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
empty. The Stakeholders root was set aside early on a weak reason (that
the skill's other users are agents, when other installers are human and
the people affected by any session's outcome are stakeholders too); the
independent review surfaced what that root would have, proportionality
and register, and both are now addressed in the body rather than by
reopening the walk.

Deliberately left to be learned from use rather than decided now:

- Whether the ten root Lines of Inquiry hold up. The
  surfaced-unfitted-questions rule exists to test this; if unfitted
  questions keep accumulating, or users prune most roots every session,
  the taxonomy is wrong.
- Whether agents over-index on the example expansion.
- Whether capture at exits is the right cadence. If sessions routinely
  park before the first exit, the process is too heavy for its users.
- Whether the independent review earns its cost. If, over many sessions,
  it never changes an outcome, it should go.

The skill's own Disconfirmation: the design is abandoned or reworked if
users of it report that the interrogation felt like a tribunal rather than
a steward, or that the outputs were not worth the time and energy the
sessions cost. The success criterion itself is not measured, by decision
(see Success).
