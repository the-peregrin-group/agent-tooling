# Reader brief: extract issue-guidance principles (unattended)

> This document captures state as of 2026-10-26. For current state, see [docs/index.md](../../index.md).

This is an unattended, read-only research task. Do not ask questions; where
you must make a judgement call, make it and record it in your output's
"Judgement calls" section.

## Context

The maintainer of the agent-tooling repo
is designing a generic, tool-agnostic `use-issues` skill: the core of how
agents use Issues and think about filing, breakdown, linking, triage, and
process on every Issue Tracker (Beads, GitHub Issues, Forgejo). The existing
guidance is scattered across tool-specific skills, and it has drifted through
many sessions and layers of agents, each reinterpreting the last one's text a
little further from the maintainer's original intent. The goal is to recover
the original intent ("collapse the wave"), not to improve on it.

You are one of several readers, each covering one source group. Take the
UNION of the principles in your sources, not the common subset: a principle
stated in only one place still counts.

## Rules

- Read-only. Do not edit any file in the repo. Write only your output file.
- No Beads writes. `bdw show <id>`, `bdw list ...`, and `bdw search ...` are
  fine (always `bdw`, never `bd`; verb first, flags after). No claims, notes,
  or comments.
- Git: read-only commands only (`git log`, `git log -S`, `git log --follow`,
  `git show`, `git blame`), run from the repo root without `-C`.
- Never use shell `rm` or `mv`.
- Do not read anything under the maintainer's knowledge base.

## What to extract

For every principle about HOW AGENTS SHOULD USE ISSUES (filing, scoping,
breakdown, deduplication, linking/relationships, labels and priority,
triage, lifecycle/states, closing, what agents may do versus humans,
setup of a tracker, TODO-comment rules, and so on), write:

```
### <SourceLetter><n>: <short handle>
- Category: <filing | breakdown | relationships | labels-priority | triage | lifecycle | closing | agent-vs-human | setup | todo-comments | docs-linkage | other>
- Generic or specific: <generic (holds on any tracker) | specific (tool mechanics) | mixed (say which part is which)>
- Current text (verbatim, with path:line): "<quote>"
- Earliest form: <commit short sha, date, subject>; verbatim earliest wording if it differs; one line on how it drifted, or "unchanged"
- Provenance: <ratified | agent-elaborated | unknown>; evidence: <an ADR, a recorded maintainer ruling, a home-in outcome, a commit or Issue saying the maintainer raised/decided it, or why you judge it agent-elaborated>
```

Trace history for the generic principles (use `git log -S '<distinctive phrase>'`
or `git log --follow -p <file>`). Be pragmatic: if a principle has a long
history, give its first form and the final form. Do not trace pure tool
mechanics (flags, commands, API quirks); list them compactly in a
"Platform-specific mechanics" section, one line each.

Then add:

- **Contradictions**: within your sources, or against anything you saw
  elsewhere in the repo, each with both quotes and paths.
- **Judgement calls**: what you decided and why.

Quote; do not paraphrase. The maintainer will read the result word for word,
so precision beats coverage of trivia.

## Return

Write the full output to the path given below. Your final message (the
return value) is only: the output path, the number of principles found, and
at most five lines naming the most important or surprising findings.
