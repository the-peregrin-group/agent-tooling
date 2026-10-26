# Documentation

The front door to this repo's documentation. `README.md` is the bootstrap
and the install model; `LEXICON.md` is the vocabulary; `docs/adr/` holds the
decisions. Everything else lives under `docs/projects/`, one directory per
project, in the shape `CLAUDE.md` ("Documentation") prescribes: a living
`index.md` with an Overview and a Status table, an optional living
`design.md`, and dated targeted docs. The one exception is a dated audit that spans several
projects, which lives under `docs/audits/`.

## Projects

### Wrappers and the Installer

- [bdw](projects/bdw/index.md): the Wrapper over Beads.
- [fjw](projects/fjw/index.md): the Wrapper over a Forgejo forge; its
  [design](projects/fjw/design.md) and the issue-verbs proposal.
- [ghw](projects/ghw/index.md): the Wrapper over GitHub, with the triage
  reference wrappers; its [design](projects/ghw/design.md) and the
  triage-library-rebase proposal.
- [gitw](projects/gitw/index.md): the Wrapper over git; its
  [design](projects/gitw/design.md), the trunk-sync proposal, and the
  read-rule audit.
- [installer](projects/installer/index.md): `tooling-install`, the
  Installer that ships Source repos' tooling into Install Targets; its
  [design](projects/installer/design.md).

### Tracking work

- [beads-trial](projects/beads-trial/index.md): Beads as this repo's
  Issue Tracker, kept after an in-repo trial; its
  [design](projects/beads-trial/design.md) and the dated phase-two
  proposal.
- [use-bd](projects/use-bd/index.md): the Skill that is the operating
  manual for Beads through `bdw`, including onboarding a new repo; its
  version-one proposal.

### Skills

- [understanding](projects/understanding/index.md): the `home-in`,
  `use-adrs`, and `use-lexicon` Skills, one project because home-in
  captures lexicon entries and ADRs through the other two; its
  [home-in design](projects/understanding/design.md).
- [handoff](projects/handoff/index.md): the Skill that writes a Handoff.
- [refine-state-doc](projects/refine-state-doc/index.md): the guide for
  writing and refining State docs.

## Cross-cutting audits

Dated audits that span several projects live under `audits/`; like every
dated doc, each opens with a note giving its date and pointing to current
state, and is otherwise never updated after its date.

- [The agent-versus-human line](audits/2026-10-11-agent-versus-human-line.md),
  as of 2026-10-11: every point where a Skill or Wrapper decides what an
  agent may do on its own and what needs a human, the principles behind
  them, and the inconsistencies awaiting the maintainer's decisions.

## Exit-code contract

All agent-tooling software, every Wrapper family and the Installer, exits
with one contract, so a caller (an unattended agent especially) knows what
to do next without knowing which tool ran or what it runs underneath. Each
code borrows the meaning of an HTTP status class. Why this contract, and
the alternatives rejected, is
[ADR 0013 (one exit-code contract for all agent-tooling software)](adr/0013-one-exit-code-contract-for-all-agent-tooling.md).

| Code | Means | HTTP analogue | Caller's next step |
|---|---|---|---|
| `0` | It worked: done, including a converged no-op, and a read that answered | 2xx | proceed |
| `1` | Broken on our side, not the caller's fault: a crash, configuration, the Roster, credentials, a missing binary, the network | 5xx | stop and report |
| `2` | The caller must change something on their side: the call, or the state it acts on; the JSON says which | 400, 409 | fix it; never retry unchanged |
| `3` | The named resource does not exist | 404 | treat it as an answer |
| `4` | Policy forbids this caller this action | 403 | don't, or ask a human |
| `5` | Partial completion: the caller has work to do, as the output directs, before resuming | none | act on the output, then resume |

How the boundaries fall:

- **2 is about whose fault, not when it is caught.** A malformed call is
  `2` whether the Wrapper catches it while parsing, after a local read,
  or after a network call, and whether the Wrapper or the tool beneath
  it detects it. So is a call naming the wrong kind of object: on a forge
  that numbers issues and PRs from one index space, a number naming a
  real object of the other kind is `2`, and the message names the sibling
  Verb. So is state the caller must change first: a dirty worktree, a
  remote that moved under a lease, a branch that already exists.
- **3 is non-existence only.** A number naming nothing, an unknown Roster
  label, a missing branch. A forge answers 404 for a repo the caller
  cannot see as for one that does not exist, so both are `3`.
- **4 is authorization only.** A branch-prefix mismatch, a push to the
  default branch, a merge gate, a forbidden flag such as bd's `--actor`, a
  forge grant too weak for the action (HTTP 403). Asking a human is the
  way forward; rephrasing the call is not.
- **1 covers everything inside the abstraction.** Configuration, Roster,
  and credential faults, a missing `git`, `gh`, or `bd`, network failures,
  a write that may or may not have landed, and any crash: an uncaught
  Python exception exits 1, which reads correctly. No code says "retry":
  a Wrapper retries internally where a retry is worthwhile and safe, and
  otherwise a retry is the caller's judgement.
- **5 means stopped on purpose, part way.** A `gitw-rebase` conflict stop
  is the case: the JSON (`"action": "conflict"`) lists what to resolve
  before `continue`.
- **An underlying tool's code never reaches the caller.** A Wrapper
  translates git's, gh's, or bd's failures into the contract.
- **Outside the contract:** 126 and 127 (the shell could not run the
  command) and 128 + N (signal N ended it).

The code constants live in `cli/lib/plan.py`, which still defines the
earlier seven codes until `agent-tooling-cjvo.1` (the shared six-code
constants) lands. Where a family's Verbs do not exit this way yet, its
Known gaps says so; until a family's gap clears, its Skill states the
codes it actually exits with.

## Argument contract

A Wrapper accepts exactly the arguments its usage line defines. A
surplus positional is a usage error, exit `2`, and so is a flag-shaped
token (one beginning with `-`) anywhere the usage line has no required
slot for it:

- **Fixed arity.** A Verb checks its argument count exactly, before it
  reads a roster, a forge, or an Install Target, so one extra token,
  flag-shaped or not, is refused.
- **Optional slots.** A flag-shaped token in an optional positional
  slot is refused at parse time, never taken as the value: a remote
  name, a target name, or a mode word.
- **Variadic tails** consume every element, and refuse a flag-shaped
  one at parse time. `gitw-commit`'s pathspecs and `ghw-issue-create`'s
  labels take no flags (a path that really begins with `-` is spelled
  `./-name`); `tooling-install`'s option tail refuses any token it does
  not parse. Any other element is validated like the rest of the tail:
  an extra `ghw-issue-create` label must exist in the repo's live label
  registry.
- **Required slots** take their token as the value and validate it on
  their own terms, flag-shaped or not. A title of `--bogus` is a title,
  and a message or body file named `--bogus` is read when, resolved
  against the working directory, it names a file in a staging directory.
  A Permission rule that leaves a required slot to a wildcard grants
  every value that slot accepts. One required slot is stricter:
  `ghw-issue-close`'s comment file refuses a flag-shaped path at parse
  time (spell such a path `./-name`).

The reason is the Permission system. A rule may put its wildcard in the
middle (`Bash(foo bar * baz)`), and that rule matches
`foo bar x baz --something-dangerous` too. Such a rule is only as tight
as the Wrapper's own grammar: a Wrapper that ignored or absorbed the
trailing token would run a command the rule's author never meant to
grant. Rejecting what the usage line does not define is therefore a
security property, not a nicety.

The contract covers the `gitw-*`, `ghw-*`, and `fjw-*` Verbs and
`tooling-install`, and each Verb's test file pins it with a surplus
positional and an unrecognized flag (the shared case for the `gitw-*`,
`ghw-*`, and `fjw-*` Verbs lives in `cli/ghw_test_support.py`;
`tooling-install`'s cases are in `cli/lib/install_test.py`). `bdw` is outside it by design: it passes its
arguments to `bd`, whose own parser owns the refusal. The `triage-*`
reference wrappers have not been audited against it.

## Path layout

agent-tooling's machine-specific files live in three places, one per kind
of file. Why three, and the layouts rejected, is
[ADR 0015 (three places for machine-specific files)](adr/0015-three-roots-for-machine-specific-files.md).

| Holds | Where | Subdivided |
|---|---|---|
| Machine Config: small files a person writes, some secret (the Roster, a token, an allowlist) | the Machine Config Directory, `${XDG_CONFIG_HOME:-~/.config}/agent-tooling/` | one subdirectory per tool |
| Machine State: what the tools record for their own later runs, safe to delete (a lock, a failure record, a log) | the Machine State Directory, `${XDG_STATE_HOME:-~/.local/state}/agent-tooling/` | one subdirectory per tool |
| installed tooling, written only by the Installer ([installer](projects/installer/index.md)) | the Install Targets: `~/.local/libexec/agent-tooling/`, `~/.claude/skills/`, `~/.claude/agents/` | one Install Target per kind of tooling |

Code that touches Machine Config or Machine State finds it through
`cli/lib/paths.py` and no other way. `config_dir(tool, environ)` and
`state_dir(tool, environ)` resolve a tool's subdirectory of the Machine
Config Directory or the Machine State Directory from the environment
mapping the caller passes; `config_root` and `state_root` return the XDG
base directory above each; and `ensure_private_dir(path, root)` creates
a directory at or below a base directory with mode 0700, creating the
base directory if it is missing but never its parent. An unset, empty, or relative XDG variable falls back to its
default under `HOME`, as the XDG Base Directory spec directs; with no
usable `HOME` either, the resolvers return None and the caller decides
whether that means skip or fail. The module docstring has the details.

Staging directories (`/tmp/claude/`, a background job's `tmp/`) are
scratch space for message and body files, not machine-specific files, and
sit outside the layout (`cli/lib/staging.py`).

Code that predates the layout does not follow it yet, and each move has
its own Issue: gitw's Roster (`agent-tooling-fpkl.5`) and fjw's config
(`agent-tooling-fpkl.6`) are still read from `~/.config/gitw/` and
`~/.config/fjw/` without the helper, and triage-issues' guard marker and
lock have yet to move into the Machine State Directory
(`agent-tooling-fpkl.9`).
