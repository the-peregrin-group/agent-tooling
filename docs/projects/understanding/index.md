# understanding: home-in, use-adrs, and use-lexicon

Three Skills that turn a conversation into understanding a project can keep.
`home-in` interrogates the user, one question per turn across a tree of Lines
of Inquiry, toward an opinion on a problem they can defend, and records it in
an artifact the user chooses. `use-lexicon` keeps a project's `LEXICON.md`,
the canonical names of its concepts, and holds all work to those names.
`use-adrs` decides which decisions deserve an ADR and how one is written,
read, and superseded. They share one contract: home-in captures terms only through use-lexicon and decisions only
through use-adrs, at each Line of Inquiry Exit. They are split so that each
can be invoked alone.

home-in's design, including its rejected alternatives, is the dated
[home-in design](home-in-design.md) (as of 2026-09-30). The decisions behind
it: capture happens only at Line of Inquiry Exits
([ADR 0003](../../adr/0003-capture-at-line-of-inquiry-exits.md)); home-in has
no unattended form ([ADR 0004](../../adr/0004-home-in-is-attended-only.md));
the independent review at wrap-up reaches the user unfiltered
([ADR 0005](../../adr/0005-independent-review-delivered-unfiltered.md)); and
an ADR duplicates the context of the document that motivated it
([ADR 0006](../../adr/0006-adrs-duplicate-their-motivating-document.md)).

## Status

| Capability | State | Where |
|---|---|---|
| Interrogation toward a defensible opinion: one question per turn, gathering and verifying against what exists, pressure-testing every proposition including the agent's own | shipped | `skills/home-in/SKILL.md` |
| A tree of Lines of Inquiry from ten shipped roots, expanded lazily into the domain, with coverage reported at every Line of Inquiry Exit | shipped | `skills/home-in/lines-of-inquiry.md` |
| Capture at Line of Inquiry Exits through use-lexicon and use-adrs, with working names and the Resolution Queue between exits | shipped | `skills/home-in/SKILL.md`, `skills/home-in/wrap-up.md` |
| An artifact the user chooses, rewritten in place at every exit | shipped | `skills/home-in/SKILL.md` |
| Attended only: refuses and stops when the session is unattended | shipped | `skills/home-in/SKILL.md` |
| Wrap-up with three offered checks (the user's three-sentence summary, a cold read, an independent review), and park and resume from the artifact | shipped | `skills/home-in/wrap-up.md` |
| Finding a project's lexicon, or creating one from the bundled template | shipped | `skills/use-lexicon/SKILL.md`, `skills/use-lexicon/lexicon-template.md` |
| Conversion of an existing glossary into `LEXICON.md` | shipped | `skills/use-lexicon/SKILL.md` |
| Naming a concept with the user, and proposals for review when unattended | shipped | `skills/use-lexicon/writing-lexicon.md` |
| Renaming and retiring terms, and resolving conflicts between code and the lexicon | shipped | `skills/use-lexicon/writing-lexicon.md` |
| Correcting drift from the lexicon's terms in conversation | shipped | `skills/use-lexicon/SKILL.md` |
| Lexicon injected at session start by a hook, with no per-project pointer | planned | `agent-tooling-0s1.4` |
| Conversion sweeps a dropped or renamed glossary term from State docs and open Issues instead of adding a Retired terms line | planned | `agent-tooling-i3n` |
| A third-party product's own vocabulary excluded from the lexicon | planned | `agent-tooling-i3n` |
| Every invariant listed in an entry's Invariants field, even when the definition already implies it | planned | `agent-tooling-i3n` |
| ADR placement, numbering, and file naming | shipped | `skills/use-adrs/SKILL.md` |
| The three-part gate on what deserves an ADR, and a draft ADR for the reviewer when unattended | shipped | `skills/use-adrs/SKILL.md` |
| Reading ADRs before design work, and superseding rather than silently contradicting one | shipped | `skills/use-adrs/SKILL.md` |
| The ADR template, hard length limits, self-contained snapshot, supersession, and citation by inline summary and link | shipped | `skills/use-adrs/writing-adrs.md` |
| Loading the use-privacy Skill, when listed, before writing anything bound outward | planned | `agent-tooling-n0p` (home-in, use-adrs), `agent-tooling-i3n` (use-lexicon) |

### Known gaps

- use-adrs forbids editing a landed ADR beyond typo fixes and supersession,
  but is silent on partial supersession of a pre-template ADR that has no `status:` field, link
  repoints after a file move, retired vocabulary, post-decision
  observations, and adopted ADRs (`agent-tooling-eeu`).
