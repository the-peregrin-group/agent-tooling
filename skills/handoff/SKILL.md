---
name: handoff
description: >
  Write a handoff: a self-contained brief that lets another agent (or a
  human) take over or continue work without this conversation. By default,
  writes a temporary file under /tmp/claude/ and prints a paste-ready kickoff
  prompt, for starting a parallel or fresh session now. Trigger on "hand this
  off", "handoff", "write a handoff", "brief another agent", "spin up another
  agent on this", "continue this in a new session", "park this". Can be
  offered when work is being set aside unfinished. EXCLUDE: saving the
  transcript (save-log), logging accomplishments (update-snippet), filing
  issues or beads (the tracker's own workflow, unless the invocation asks for
  it).
argument-hint: "[to <recipient>] [focus or other guidance]"
---

# Handoff

A handoff is usually read within minutes, by a session the user starts right
away. Write for that case unless told otherwise.

## Explicit guidance wins

Guidance from the invoker, in the invocation arguments or the conversation,
overrides every default in this skill except the privacy rules. It can name
the recipient, the destination, the focus, a length limit, and anything else.

## The recipient

Unless told otherwise, write for a fresh agent running a strong model, in the
same repo on the same machine, that has none of this conversation and none of
this session's temporary or job files.

When the signs point to a different recipient, adjust:

- A human: explain more of the why; give fewer commands.
- Another repo, another machine, or a cloud session: no local paths, and put
  the handoff's content in the kickoff prompt itself.
- A weaker model, if the guidance names one: add a Next steps section with
  concrete steps.

If the recipient is unclear, ask. In an unattended session, pick the likeliest
recipient and say in the handoff which one you assumed.

## Before writing

- Commit whatever the recipient must build on; push it too if the recipient
  may be on another machine. The handoff names the ref to start from. Never
  describe unshared changes in prose instead.
- Get the current time with `date`; do not guess it.

## Privacy

- Never include secrets: tokens, passwords, keys, credentialed URLs. Say where
  the recipient gets them instead.
- If a skill named `use-privacy` is in your available skills, load it before
  writing and apply its rules to everything in the handoff, taking the
  destination into account.
- Otherwise, never put content where it reaches a wider audience than its
  source had.
- If the guidance would break these rules, say so and leave that content out.
  Include it only if a clarification shows the concern does not apply (e.g.,
  the destination is private after all). Insisting alone is not enough.

## Destination

Write to `/tmp/claude/handoff-<slug>-<YYYYMMDD-HHMMSS>.md`. Never write to a
job's own temporary directory: it is deleted with the job. Write anywhere else
(a bead, an issue, a PR, a project file) only when the guidance says to.

## Sections

In this order. Leave out empty ones, except those marked always.

1. **Summary** (always): three to five lines: goal, status, what remains.
2. **Goal** (always): what done means, and why the work matters.
3. **Verification** (always): how to prove the goal is met.
4. **As of**: the ref to start from, e.g. `origin/main`.
5. **Who does what**: what the sender still holds or keeps doing (branches,
   beads, files, running jobs), and what the recipient owns.
6. **State** (always): what is true now. Mark each claim as checked (you
   verified it this session) or believed (you did not).
7. **Decisions**: each with its reason and who made it: the user, or you
   without the user's sign-off.
8. **Dead ends**: only those tempting enough that the recipient might retry
   them.
9. **Open questions**: blockers and undecided points.

Tell a strong recipient what and why, not how. Add Next steps only for a
weaker recipient or when asked.

## Writing rules

- Link rather than copy, and only to what the recipient can reach.
- Resolve every reference to this conversation inline: never "option B" or
  "the fix we agreed on"; state the option or the fix itself.
- Leave out what the recipient can cheaply learn from the repo or the ref.
- No length limit unless the guidance sets one. If the handoff runs past about
  a screen, check whether you are copying what you could link.

## Check before handing off

Reading only the handoff and what it links to, can the recipient answer:

- What is the goal, and why?
- What does done look like, and how is it proved?
- Where do I start from?
- What is already decided or ruled out?
- What must I leave alone, because the sender still holds it?

If not, fix the handoff. If the invocation asks for a cold read, give a
subagent only the handoff, have it answer these questions, and fix any gaps it
finds.

## Tell the user

Print:

1. The path.
2. A kickoff prompt in a code block, ready to paste, e.g.:
   ``Read `/tmp/claude/handoff-<slug>-<timestamp>.md` and take over the work
   it describes.``
3. This line: "This is in /tmp and will be wiped; ask if it should be filed
   somewhere durable."

## Offering a handoff

When work is set aside unfinished, offer `/handoff` in one sentence; do not
write one unasked. In an unattended session, where no one would see the offer,
write it and give its path in your final report.
