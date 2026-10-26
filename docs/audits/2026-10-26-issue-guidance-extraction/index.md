# Audit: issue guidance extraction

This document captures state as of 2026-10-26 (`main` at 2bf1ca6). For
current state, see [docs/index.md](../../index.md).

This audit is step one of scoping the Issue Tracker skill family (Beads
Issue `agent-tooling-u9n.1`, under the epic `agent-tooling-u9n`, split the
Issue Tracker skills into a tool-agnostic layer and tool-specific skills).
Its aim is to recover the maintainer's own design philosophy for Issues,
which had drifted as successive sessions and layers of agents each
reinterpreted the last one's text, before any of it is redesigned.

## Method

Seven read-only readers each covered one source group and followed one
brief ([reader_brief.md](reader_brief.md)). Each took the union of the
principles in its sources, not the common subset, and recorded every one
with a verbatim quote and its location, its earliest form in git history,
and its provenance: ratified by the maintainer (an ADR, a home-in outcome,
a recorded ruling), elaborated by an agent, or unknown. A synthesizer then
merged the seven extracts.

The Skills `setup-github-issues`, `use-github`, and `triage-issues` were
imported whole on 2026-09-22 (cb6f1eb) from a predecessor repo whose
history did not come with them, so most of their provenance is unknown
rather than agent-elaborated.

## Files

| File | Source group |
|---|---|
| [extract_A_setup-github-issues.md](extract_A_setup-github-issues.md) | the `setup-github-issues` Skill |
| [extract_B_use-github.md](extract_B_use-github.md) | the `use-github` Skill and the ghw docs' issue policy |
| [extract_C_triage-issues.md](extract_C_triage-issues.md) | the `triage-issues` Skill |
| [extract_D_use-bd.md](extract_D_use-bd.md) | the `use-bd` Skill, `.beads/PRIME.md`, and the Beads project docs |
| [extract_E_forgejo.md](extract_E_forgejo.md) | the planned Forgejo issue conventions and `use-forgejo` |
| [extract_F_beads-epics.md](extract_F_beads-epics.md) | the maintainer's sketches and rulings recorded in Beads Issues |
| [extract_G_adrs-lexicon.md](extract_G_adrs-lexicon.md) | the ADRs, the lexicon, and `CLAUDE.md` |
| [catalog.md](catalog.md) | the merged catalog of generic principles, platform-specific residue, and side findings |
| [requirements_draft.md](requirements_draft.md) | the requirements draft and the disconnects between sources |

`requirements_draft.md` is the draft as it stood before the maintainer
reviewed it. The reviewed requirements, with each ruling and its reason,
are recorded on `agent-tooling-u9n.1`, and will carry into the skill
family's dated proposal.

These files passed a privacy review before publication: private sources
were removed, not paraphrased, and a few positions in the draft's
disconnects are marked `[omitted: private source]`.
