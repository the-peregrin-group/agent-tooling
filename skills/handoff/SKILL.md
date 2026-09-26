---
name: handoff
description: >
  Impart a portion (or all) of your context to a future agent (or human). Can
  be used proactively whenever there are still loose ends to tie up but the
  session is ending (or a task is being put down and left to a future agent).
  The user may also use this skill explicitly when they need a handoff
  artifact to share themselves.
argument-hint: add specific guidance on how to produce the handoff here
---

## Prerequisite

- To write a proper handoff, you must understand to whom you are handing off. If you do not know this already,
  get clarification from the user first.
- One must also understand the repo/project into which one will be handing off, how state is stored in that project,
  and how issues are tracked. Your handoff should get filed in the appropriate manner for the repo/project.

## Properties of a good handoff

- Complete coverage of all necessary context for a future agent to be able to understand and properly execute on their task.
- Clear writing, logical organization, progressive disclosure, and concision.
- Reference existing, _accessible_ artifacts rather than duplicating their contents. If there are relevant documents, designs, assets, URLs, github/forgejo/beads/etc. issues, git commits, snippets, chat logs, etc. _*and*_ they are accessible to the recipient, include resolvable references.

Test: do I imagine the result of following my handoff would be akin to the result of doing the task myself with my current context?
If not, what's missing?

## Writing the handoff

If the user passes arguments, treat them as additional guidance on how to produce the handoff and what to focus on. Direct user
guidance overrides instructions below.

By default, the handoff should be written as a `.md` file with a unique filename to `/tmp/claude/` and shared with the user.

However, if your current context makes you aware of circumstance- or project-specific conventions, follow those (e.g., to write
TODOs to an existing project file, to write a comment on a github issue, etc.). If you're unsure, ask the user for guidance. If
you're unsure but the session is unattended, write the handoff to the highest-confidence location that is also machine-private and
reversible, ultimately falling back to `/tmp/claude/` if necessary.