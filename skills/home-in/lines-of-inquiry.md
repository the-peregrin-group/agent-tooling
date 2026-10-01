# Lines of Inquiry

A Line of Inquiry (LOI) is one line of questioning that must be examined
before an opinion is defensible. The ten roots below apply to any problem
that needs an opinion: a product's next move, a software design, a career
decision, an essay's thesis, someone else's proposal. The domain enters
only through expansion.

## The ten roots

Each root is a subtree, not a question. The text under each says what the
root exists to force into the open, not what to ask.

1. **Trigger.** Why this problem, why now, and what happens if nothing
   changes. Separates a real forcing function from an itch, and often
   reveals that the stated problem is a symptom.
2. **Success.** What good looks like, and how the user would know. Measured
   or felt, but stated before any option is weighed; an option cannot be
   judged against criteria that do not exist yet.
3. **Anti-goals.** What must not happen, and what the user refuses to trade
   away. Usually shorter than Success and more decisive.
4. **Stakeholders.** Who is affected, who actually decides, and whose input
   is missing from the room. The missing voice is the finding.
5. **Constraints.** Time, money, skill, dependencies, obligations. For each:
   genuinely fixed, or assumed fixed? The assumed ones are often the real
   decision space.
6. **Load-bearing assumptions.** What must be true for the leading option
   to work, and how each could be checked or falsified. Most adversarial
   questions attach here, and each one names the assumption it tests.
7. **Alternatives.** Including doing nothing, and the option the user has
   been avoiding naming. An opinion with no live alternative is a
   preference, not a decision.
8. **Reversibility and horizon.** How long until the user would know it
   worked, and what undoing it would cost. Cheap-to-reverse decisions
   deserve less interrogation; say so and move faster.
9. **Pre-mortem.** It is a year on and this failed. Why. Asked as a story,
   not a list; the first failure named is usually the one the user already
   fears.
10. **Disconfirmation.** What evidence would change the user's mind, and
    whether any of it already exists. If nothing would, the opinion is a
    commitment, and the interrogation should say so.

## Expansion

Expand a root into the domain from your own knowledge of that domain. The
skill encodes roots and this rule, never domain trees: they are unbounded,
and the tree for a software design shares nothing below the roots with the
tree for a kitchen remodel or a video essay.

- **Lazy.** At the opening move, sketch the whole tree one level deep for
  the user to prune or extend. Expand a subtree further only when you enter
  it.
- **Depth-first.** Walk a LOI to the bottom before entering the next. When
  an answer opens a sub-LOI ("the Foo and Bar projects were painful"),
  follow it down before returning.
- **Considered, not necessarily asked.** Every LOI ends in one of two
  states: explored to the depth the problem warrants, or set aside with a
  one-line reason the user can see. There is no third state and no silent
  skip.
- **Depth tracks stakes.** Reversibility and horizon sets the budget: a
  decision that can be undone next week gets a shallow tree and a fast
  walk, and you say so.

## Coverage

The frontier is the tree's state: which subtrees are exhausted, in
progress, untouched, set aside. Report it at every LOI Exit, in a few lines,
so the user always knows where they are and what remains.

The ten roots are a taxonomy under test. When you want to ask something
that fits no root, ask it anyway and note it; surface every such question
at the next LOI Exit, so the roots can be refined against use.

## Example expansion: a software design

One domain's tree, one level deep, shown to calibrate what expansion looks
like. It is not a template; a second software design would expand
differently, and a non-software problem shares nothing with it below the
roots.

- **Success**: the use cases in scope and out; expected usage and load,
  the outliers, and whether to support them; the business metrics that
  move, and the study design if it is an experiment.
- **Constraints**: the interfaces and APIs that must not change; data that
  already exists and its migration; the rollout path and who it disrupts;
  the team's skills and time.
- **Load-bearing assumptions**: performance and scaling at the expected
  load; concurrency and what happens under contention; fault handling,
  recovery, and degradation; what the tests can actually prove at each
  layer, from lint to end-to-end.
- **Stakeholders**: the operators who will carry the pager, and the
  observability (metrics, logs, traces, dashboards, SLOs) they need to do
  it.
- **Reversibility and horizon**: which choices are one-way doors (schema,
  public API, data format) and which can be revisited after launch.

Each of these lines is itself a subtree. Concurrency alone can be twenty
questions. Expand only what you enter.
