# use-issues design

How the shipped parts of the Issue Tracker skill family work and why. What
is shipped is in [index.md](index.md). Only the Tracker Schema file is
described here so far; the design of everything not yet built is in the
dated [proposal](2026-11-13-proposal.md), and each slice carries its part
into this document when it lands.

## The Tracker Schema file

Every repo carries its own full copy of the Tracker Schema, bootstrapped
from the shipped default
([ADR 0020](../../adr/0020-every-repo-carries-its-own-copy-of-the-tracker-schema.md),
every repo carries its own copy of the Tracker Schema), and its Issue State
Diagram holds every state meaning and transition condition in natural
language
([ADR 0019](../../adr/0019-issue-lifecycle-semantics-live-in-the-issue-state-diagram.md),
lifecycle semantics live in the Issue State Diagram). The file's form, path,
and provenance are decided in
[ADR 0025](../../adr/0025-the-tracker-schema-is-one-markdown-file-with-one-json-block.md)
(the Tracker Schema is one Markdown file at the repo root, with one JSON
block for what tooling reads), which also holds the rejected alternatives.

### Form

The file is Markdown with one fenced JSON block. Each fact lives in exactly
one place: the JSON block holds the Issue Kinds, the Issue Priorities with
their staleness thresholds, the Issue Label Schema, each Issue State's name
with its open or closed flag, and the provenance; the prose holds the state
meanings and the transition conditions, keyed by state name. JSON, because
the Wrappers run on the system Python 3.9 with the standard library only,
which parses JSON and neither TOML nor YAML.

The block is delimited the way `TRIAGE.md`'s config block is: two HTML
comment marker lines naming `tracker-schema`, with one fenced `json` block
between them. A reader matches each marker as a whole line, so prose that
mentions a marker cannot be mistaken for one. The file itself states the
rule and what each key holds, since it is the only context a repo's agents
have. Nothing reads the block yet: the reader, and a test that the shipped
default is well formed, are `agent-tooling-rtag` (a reader and a validity
test for the Tracker Schema's JSON block).

### Path

In a repo, the Tracker Schema is `TRACKER.md` at the repo root, the same
convention as `LEXICON.md` and `TRIAGE.md`, found with no configuration on
any platform. This answers `agent-tooling-wx5` (one canonical per-repo
config home) for the schema. Folding `TRIAGE.md`'s config block into this
file's JSON block is left to `agent-tooling-u9n.8` (make triage-issues
tool-agnostic).

### The shipped default

The default is [`TRACKER.default.md`](../../../skills/setup-github-issues/TRACKER.default.md)
in the setup skill's directory, so it ships in the skills Cohort with no
change to the Install Manifest. That directory is
`skills/setup-github-issues/` today; `agent-tooling-u9n.10` (move the
shipped default Tracker Schema from setup-github-issues to
setup-issue-tracker) tracks the move, which lands with `agent-tooling-u9n.9`
(write setup-issue-tracker, the generic setup skill). Considered and
rejected as its home: `skills/know-issues/`, `cli/lib/`, and a new top-level
directory with its own Cohort. This choice is cheap to reverse, so it is
recorded here and not in an ADR.

The default is written to read true both as the original and as a repo's
copy, because setup copies it whole: it calls itself "this repo's Tracker
Schema" and names no path of its own. Its content (the default Issue Kinds,
Issue Priorities, Issue Label Schema, and Issue State Diagram) is in the
file and is not repeated here.

Where an Issue State is recorded on a forge with no status mechanism is
left open in the default, per platform, until `agent-tooling-vb2v` (where
an Issue State is recorded on forges with no status mechanism) decides it.

### Provenance

A repo's copy records, in the JSON block, the source repo, the full commit
from the Installer's Receipt (`source_commit`), and the default's path at
that commit, so "what has the default changed since" is a diff of that path
between the recorded commit and the current one. In the shipped default the
three fields are `null`, since it is not a copy.

When the Receipt's commit is `-dirty` or unknown, setup stops and says so
rather than recording a revision that cannot be diffed against. Setup is
not built yet (`agent-tooling-u9n.9`); this is the rule it is built to.
