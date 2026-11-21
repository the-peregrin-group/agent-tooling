# own-the-outcome: design

The living design of the `own-the-outcome` Skill and its four Agent
definitions. What ships and where is in the [index](index.md).

## The problem it solves

A lead session that coordinates sub-agents drifts into doing their work:
landing changes, polling, reading every result in full, re-running checks.
The lead holds the largest context on the team for the most turns, and
every turn re-reads that context, so a hands-on lead becomes the team's
largest single cost and its bottleneck. The fix is a stance, not a tool:
the lead is the job's directly responsible individual (DRI), who answers
for the outcome and delegates everything that does not need its judgement.

The process was trialled on real work before it was written down here,
and most of its rules answer a failure seen in that trial.

## Shape

- **One Skill holds the protocol** every role shares: `SKILL.md`. Each
  role's own rules sit in a support file beside it (`lead.md`,
  `dispatcher.md`, `steward.md`, `worker.md`, `auditor.md`), and
  `templates.md` holds the shape of every team file.
- **Four thin Agent definitions** (`dispatcher`, `steward`, `worker`,
  `auditor`) carry what only a definition can: the
  role's model, and the Skill listed under `skills:`. Their bodies
  name the role, tell the agent to load the Skill if it arrived without
  it, point to its support file, and repeat only the few rules
  the role must never miss.
- **Project specifics live in the charter.** The Skill names no
  version-control tool, build system, or shared resource.

## Invariants

- **The rulings ledger is the only authority to act.** A ruling
  authorizes work, and an order file marked GO carries a ruling to the
  steward by citing it. Messages are lost, delayed, and duplicated; a file
  the recipient re-reads is not, so a dispatcher cut off from the lead's
  messages still acts correctly from the ledger.
- **One voice to the steward.** Only the dispatcher's order file moves the
  steward. Two voices contradict each other, and a GO in a spawn brief on
  top of an order's GO can land one change twice.
- **The steward lands, after the review and the gate.** The one exception
  is a gate-free landing that a charter lets the dispatcher make. Nobody
  lands on another agent's word: a reply's claim that the dispatcher has
  gone is hearsay, and landing on it skips the review.
- **Verification is a role, not something delegation removes.** Hands-on
  checks catch real errors, so when the lead stops making them the auditor
  makes them, and the lead samples the auditor.
- **`SKILL.md` stays small.** After a session's context is compacted, only
  the first few thousand tokens of an invoked Skill are re-attached. A
  lead runs long enough to be compacted, so everything every role must
  remember fits in `SKILL.md`, and depth goes in the support files.
- **Tiers are named by judgement, not by model.** Model names change, so
  one line in `SKILL.md` binds the three tiers to today's models, and the
  Agent definitions pin the strong tier's.

## What is enforced and what is discipline

Everything in the Skill is discipline. The role limits ("only the steward
lands", "the dispatcher never spawns a steward") are not Permission rules:
version-control writes go through the shell, which an Agent definition's
tool list cannot split, and a sub-agent's definition cannot limit which
agent types it spawns. The one mechanical guarantee is the model: a spawn
from an Agent definition resolves to the definition's model before the
parent's. A project that wants a limit enforced adds its own Permission
rules.

The Skill's presence in a lieutenant's context is discipline too. A
definition's `skills:` list puts the Skill's text into an ordinary
sub-agent's context at start. A spawn given a name, which is how the
Skill has every lieutenant spawned, runs as a teammate where the harness
has agent teams enabled, and Claude Code does not apply a definition's
`skills:` to a teammate
([agent teams](https://code.claude.com/docs/en/agent-teams)): it starts
with only the Skill's description. So each definition's body tells its
agent to load the Skill when the text is missing, and the `skills:` list
stays for the spawns that honour it.

The definitions restrict no tools, on purpose. Removing the spawning tool
from workers, stewards, and auditors would enforce "only the dispatcher
spawns workers", but it would also stop a steward or a worker from handing
a noisy search to a sub-agent to protect its own context.

## Provisional rules

The Skill marks these (provisional), because each rests on one trial or
on reasoning alone:

- falling back from nested spawning to the lead spawning everyone;
- an amendment to an order in motion needing an explicit acknowledgement;
- the dispatcher making gate-free landings itself, where a charter
  grants them;
- the context thresholds for rotating lieutenants;
- the strong tier being enough for the lead;
- a worker's commits on its own branch counting as staging, with the
  steward integrating them, which is reasoning and not experience.

## Rejected alternatives

- **An Agent definition for the lead, instead of a Skill.** A session
  launched as a custom agent takes the definition's body in place of the
  default system prompt, can only be chosen at launch, and covers one role
  of five, leaving the shared protocol without a home. Its strengths (the
  rules survive compaction whole, the spawn list can be restricted) may
  justify adding a `lead` definition later, as a thin wrapper over the
  Skill, once use shows the Skill alone does not hold the lead to its
  role.
- **A Skill alone, with no Agent definitions.** Passing a model on every
  spawn would stay a matter of memory, and the cost of forgetting is a
  team of agents on the lead's tier.
- **Rules restated in each Agent definition's body.** Five copies of one
  protocol drift apart. The definitions bring the Skill in and point to
  it.
- **Naming the Skill for the jargon** (`dri-team` and kin). "DRI" is
  opaque to a reader who has not met it, and "DRI team" reads as a
  contradiction. The name says what the lead does, and the Skill defines
  DRI once.
- **A `dri-` prefix on the Agent definitions.** The DRI is the lead, so a
  subordinate role that carries the lead's title in its name misleads.
  The definitions are named for their roles alone. The cost is that bare
  names share one namespace with every other Agent definition: a project
  that defines its own `worker` or `auditor` shadows these, and such a
  project has to rename its own or accept that the team uses it.
- **Shipping the context hook inside this change.** The hook depends on an
  undocumented transcript layout and needs its own source, tests, and
  install path; it is tracked separately (see the index's Known gaps).
