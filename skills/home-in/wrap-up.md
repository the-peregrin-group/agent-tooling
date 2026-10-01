# Line of Inquiry Exits and wrap-up

Read this file at each Line of Inquiry Exit and again when the user moves
to wrap up. Procedures read at the point of use are followed; procedures
read hours earlier are remembered loosely.

## At every Line of Inquiry Exit

In this order:

1. **Report the frontier**: exhausted, in progress, untouched, set aside,
   reopened, in a few lines, ending with roots done, roots remaining, and
   the depth prompt: "deeper, shallower, or as we are?" Honor the answer
   immediately and visibly.
2. **Surface questions that fit no root** Line of Inquiry, if any came up.
3. **Drain the Resolution Queue** of the items from the LOI just exited.
   - Candidate terms: run `use-lexicon`'s naming procedure, one concept per
     turn, identity first and names next. Every working name ends here:
     ratified, renamed, or dropped. Write each ratified entry at once.
   - Candidate decisions: apply `use-adrs`'s three-part gate to each.
     Draft the ones that pass, in the compact form, with Context linking
     the artifact. The user ratifies before anything is written.
   - Assumptions under test: each is confirmed, refuted, or carried
     forward with a reason.
   - Pending gathering: do it now, or say why it no longer matters.
4. **Rewrite the artifact in place.** First exit: draft it. Every exit
   after: rewrite the body so it reads cleanly as of now, with the frontier
   and the remaining Resolution Queue in its open-items section. Ratified
   terms replace working names throughout.
5. **Commit**, if the owning project is a repo, following `use-git`.

Any working name still unresolved after step 3 is a failure. Say so in the
report rather than carrying it quietly.

## Wrap-up

Done is the user's to declare. Never begin the wrap-up on your own
initiative; the most you do is observe that the frontier looks empty.

### The check

Report the frontier and the Resolution Queue. Both are expected empty. If
either is not, say what remains and why; the user may overrule with a word,
and that is their call.

### The offers

Then offer, in one short paragraph, the three checks below, singly or in
any combination. Name the risk they address in one line: a long session of
small ratifications can add up to a conclusion the user would not have
endorsed cold, and nobody inside the conversation, you included, can see
that from inside it. Base your recommendation on the stakes and
reversibility the user described under Reversibility and horizon, never on
how many exits the session had: a decision that is cheap to undo needs no
review, and one with years of consequences deserves all three. If the user
said at the opening move what they intended to do about these checks and
now chooses differently, remind them of their earlier answer in one
sentence, then accept whatever they decide. Run only what the user asks
for. None of these checks verifies that the user holds the opinion; the
skill accepts that gap, because a validation step that costs the user more
than the session saved defeats the skill.

**The user's own summary.** Ask the user, before showing the final
rewrite, for three sentences without the document: what they are going to
do, why, and what they rejected. Someone who holds the opinion produces
that in a minute. Compare it to the artifact and say plainly where they
diverge; divergence is the finding. Never ask for more than three
sentences.

**Cold read.** Give a subagent the artifact alone, no conversation, no
queue, and ask it to state in its own words: the problem, the success
criteria, the recommendation, and why each rejected path was rejected. The
test is whether the artifact stands on its own, not whether the user agrees
with it. Gaps the reader finds go back into the artifact.

**Independent review.** Spawn a separate agent with the artifact, the
session's new ADRs, the owning project's lexicon, and the sources the
artifact cites, and nothing else. It never sees the conversation, the
Resolution Queue, or you; it is blind to the path, not to the world, so it
can test whether the premises are true and not only whether the argument
is coherent. Tell the user in one line that the reviewer is the same model
with different inputs: it corrects for anchoring on the path, not for
biases the model brings to any well-structured document. Its brief,
verbatim:

> You are writing a judicial opinion on the attached recommendation, for
> the person who must act on it. You are not helping the author polish it,
> and reaching agreement is not your goal. Read the artifact and the ADRs
> cold. Then write your opinion: whether the premises hold, whether the
> conclusion follows from them or only from the path taken to reach it,
> which single step, if wrong, brings the whole recommendation down, and
> what the author has not considered. You may reject the premise, the
> argument, or the conclusion outright. You may offer to write a
> counterproposal; do not write one unasked. Write for a reader who has
> the artifact in front of them: cite its sections, do not summarize it.
> Write your opinion to the file path given below and return only that
> path.

Give it a path under `/tmp/claude/` or beside the artifact, as the user
prefers. When it returns, print the path and relay the opinion verbatim:
nothing summarized, softened, reordered, or omitted, and nothing of yours
in the same turn. Offer your response as author in one sentence and give
it only in a later turn, if the user asks; an attack and the anchored
party's defense read together, with the defense last, is a filter by
framing. The user decides what to do with the opinion; if they commission
the counterproposal, the reviewer writes it, not you.

### Closing

When the user declares done:

1. Rewrite the artifact a final time. Remove the open-items section if the
   frontier and queue are empty; otherwise leave it, stating that the user
   chose to close with those items open.
2. State in one line what the session produced in lexicon entries and ADRs,
   including "no terms met the bar" or "no decision passed the gate" when
   that is the case. Silence reads as forgotten; a stated empty result
   reads as judged.
3. Commit and follow the project's own rules from there (`use-git`, the
   forge skill).

## Park and resume

Stopping early is a normal outcome, not a failure. When the user says
"park it," or the session must end before done:

1. Run the Line of Inquiry Exit procedure above for the LOI in progress,
   with its state marked in progress rather than exhausted.
2. Leave the frontier and the full Resolution Queue in the artifact's
   open-items section. That section is the resume point; nothing needed to
   continue may live only in the conversation.
3. Commit, and offer `/handoff` in one sentence.

Resuming is `/home-in continue from <artifact>`. Read the artifact in
full, rebuild the frontier and Resolution Queue from its open-items
section, state them back to the user in a few lines, and re-enter the LOI
that was in progress.
