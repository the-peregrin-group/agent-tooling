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
  top of an order's GO can land one change twice. For the same reason an
  order that is replaced is first withdrawn in its own file, so that two
  orders for one change are never both GO.
- **The steward lands, after the review and the gate.** The one exception
  is a gate-free landing that a charter lets the dispatcher make. Nobody
  lands on another agent's word: a reply's claim that the dispatcher has
  gone is hearsay, and landing on it skips the review.
- **An approval is a stop, and is written as one.** A point where the
  user or the lead must approve before work goes on is recorded in the
  ruling as a stop, and reaches the steward as a HOLD step that only a
  later ruling lifts. "Show me before you land" written any other way
  reads as a notification, and the landing it guarded happens first.
  Only the approver lifts a stop: the lead does not lift the user's on
  having shown them.
- **No rule depends on a hand-back arriving.** An anonymous sub-agent's
  hand-back goes only to the agent that spawned it, or to the lead when
  that agent's run has ended, and it fails outright while the spawner is
  blocked on the Agent call that spawned it; the spawner's Agent result
  then carries none of the child's final text. A teammate has no
  hand-back: the text it ends its turn with reaches the lead as an idle
  notification. So the result file is the delivery and carries a State
  line the spawner watches, a hand-back is a few lines and a path with
  no copy sent by message, a failed hand-back is not retried, and the
  lead forwards a hand-back that reaches it in place of a rotated
  dispatcher. Only the lead reports a lieutenant as stopped: its list of
  agents shows its teammates, and a completion notice tells it the
  dispatcher has ended. No list shows anonymous agents, so the
  dispatcher judges its workers by their result files and how long
  their jobs should take. The harness keeps
  demanding a retry after a failed hand-back even when the agent
  declines; the Skill tells the agent to stop anyway, which bounds the
  cost to the demand turns.
- **Messages to a busy agent are not read until it looks.** Measured
  across a day's team runs (agent-tooling-smir): a named teammate that
  was mid-turn read none of its 506 messages until its turn ended
  (median delay 8 minutes, maximum 131), while an idle one was woken in
  under a second; an anonymous sub-agent read its messages at its next
  tool round (8 of 8, and one probe). So anything a busy agent must act on is written into a
  file its wait watches, and a message only points to it or wakes an
  idle agent.
- **Each role waits by what can wake it** (provisional). A background
  job's notice, or a watcher's, has failed to wake a sub-agent that had
  ended its turn: in a live team run a steward was not woken when its
  smoke test ended, and the shared resource sat idle for about an hour
  and a half until the lead noticed. Stewards that waited in their turn
  had no misses. So a lieutenant waits for its own jobs inside its turn,
  in foreground slices, and a watcher that runs in the background is no
  substitute. A slice returns as soon as what it waits for or a file
  carrying the agent's instructions changes, and otherwise runs about 4
  minutes, under the prompt cache's 5-minute default lifetime (see
  "Short fixed slices" below for why). The roles then differ:
  - The steward is a named teammate. It waits in its turn on its own
    jobs, is steered only through its order file, which its slices
    watch, and tells the dispatcher things by a line in the steward log.
    At a STOP, a HOLD, or between orders it ends its turn, and the
    dispatcher's message wakes it within seconds.
  - The dispatcher is an anonymous sub-agent, spawned by the lead in the
    background. Its own spawns then run in the background too, and it
    receives their hand-backs, their task notifications, and the lead's
    messages at each slice boundary while it stays in its turn; its
    slices watch result files, the steward log, the ledger, and the
    charter. Ending its turn ends its run: it hands back to the lead, a
    child that finishes later hands back to the lead, and a message to
    its agent id resumes it. So it ends its turn only to rotate, or when
    nothing is in flight and what remains waits on the lead (an order
    held for approval is not in flight), and the lead keeps its current
    agent id in the charter. Because a message resumes a rotated
    dispatcher too, which would give the steward two voices, the lead
    never messages a rotated one, and a resumed dispatcher that finds a
    later one named in the charter stops without writing anything. A
    task notification that a child "completed" can be interim (the child
    stopped while waiting on a job of its own), so the result file's
    State line stays the test of done.
  - A worker is an anonymous sub-agent of the dispatcher. It waits in
    its turn on its own long jobs, and a correction goes to a fresh
    worker.
  - The lead is the exception: the user must be able to reach it, so it
    ends its turn with work in flight and sets timers, which also back
    stop a worker or dispatcher that dies without a word. The lead has
    not been seen to miss a wake-up.

  This reverses, for dispatchers, the in-turn wait of PR #125 as it
  stood: a named dispatcher that waited in its turn, often blocked on a
  foreground Agent call for a worker's whole life, could be reached by
  neither message nor file. In one run a dispatcher stayed in its turn
  81 minutes and received 58 messages in one batch after it had handed
  over. The case for the change is responsiveness. Cost savings are not
  established: the measured shares count token-turns, not dollars, and
  the retry demands come seconds apart, so they are mostly cache reads.
  The cause of the missed wake-ups is still not diagnosed, which is why
  the rule is provisional.
- **The outcome is the user's intent, not a passing check.** Before
  anyone proposes changing what the user designed, they find its purpose
  in the user's plan. A check that flags the design is first suspected of
  being too broad.
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
sub-agent's context at start: the dispatcher, spawned without a name,
has been seen to start with it (one probe); whether workers do is
unchecked. A spawn given a name,
which is how the Skill has the steward and the auditor spawned, runs as
a teammate where the harness has agent teams enabled, and Claude Code
does not apply a definition's `skills:` to a teammate
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

- falling back to the lead spawning workers when the dispatcher's
  spawns do not run in the background;
- an amendment to an order in motion needing an explicit acknowledgement;
- the dispatcher making gate-free landings itself, where a charter
  grants them;
- the context thresholds for rotating lieutenants;
- the strong tier being enough for the lead;
- a worker's commits on its own branch counting as staging, with the
  steward integrating them, which is reasoning and not experience;
- the lead making the audit check itself on a run of one or two
  landings, so that a small job does not pay for an auditor;
- an ignored folder in the main checkout as the default team folder,
  chosen because one absolute path then serves every agent and nothing
  wipes it during the run;
- a steward staying on for consecutive orders in a busy batch, which
  takes the lead off the path of every order at the cost of a steward's
  context growing between gates;
- a lieutenant waiting for its own jobs inside its turn instead of
  trusting a watcher, which rests on one run's missed wake-ups whose
  cause is not diagnosed;
- the anonymous dispatcher spawned in the background: each fact it
  rests on (background spawns, mid-turn messages and hand-backs, the run
  ending with the turn, resume by agent id) comes from one probe run of
  a small agent, and a real-sized batch (several parallel workers,
  4-minute slices, a dispatcher rotation mid-flight) is untested;
- a worker's own sub-agent (spawn depth 3), whose hand-back routing and
  background behaviour are untested.

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
- **Letting a lieutenant end its turn once a watcher is armed.** A
  watcher wakes an idle agent once, where waiting in slices re-reads the
  agent's context on every slice and adds a little to it, so the Skill
  first offered the watcher and kept slices as the fallback. A live run
  showed the watcher missing a wake-up while the shared resource sat
  idle, and an idle resource costs more than the slices do (see the
  per-role wait above).
- **Short fixed slices, or slices as long as the foreground limit.**
  Every order and amendment is in a file and a message only points to
  it, so a slice that ends when an instruction file changes reads them
  promptly at any length; what sets the length is the prompt cache. A
  slice under a minute wakes the agent, re-reads its context, and grows
  it many times for no news. A gap of more than the cache's 5-minute
  default lifetime, between turns or inside one tool call, re-writes the
  agent's whole context to the cache, which cost a steward 75,000 to
  400,000 tokens per life in a measured run (agent-tooling-smir). A
  slice just under the lifetime, about 4 minutes, re-reads a cached
  context instead, which is the cheapest per wake.
- **The lead spawning every worker** (option A in agent-tooling-smir),
  so that a named dispatcher could end its turn and be woken by name. It
  puts the lead on every worker's path, costs a lead wake per worker,
  and stalls the queue whenever the lead is talking to the user. It
  stays only as the fallback for when the dispatcher's spawns do not run
  in the background.
- **A named dispatcher with foreground workers** (option B), steered
  through files. A named teammate's Agent call blocks its turn until the
  child ends, so for each worker's whole life the dispatcher reads no
  message and watches no file, and the worker's hand-back fails, which
  makes the harness's retry loop the normal case.
- **Stating how long a lieutenant lasts before it is rotated.** One run's
  figure would be read as a rule. The Skill gives context thresholds and
  leaves the clock to the lead.
