---
name: know-unattended
description: >
  A session is unattended only when its initial prompt includes the sentence
  "You are running an `unattended` session (see `/know-unattended`)";
  otherwise it is attended, and the user can be asked and is expected to
  answer eventually, though without guarantee on latency. Load when deciding
  whether to ask the user or act on your own judgment, when a prompt or brief
  mentions "unattended", and before starting a session, subagent, or
  workflow that the user will not answer.
---

# Know: unattended sessions

The concepts are the lexicon's **Attended session** and **Unattended
session**
([LEXICON.md](https://github.com/the-peregrin-group/agent-tooling/blob/main/LEXICON.md)),
and the lexicon is authoritative for them.

## Starting unattended sessions

When you start a session, subagent, or workflow that the user will not
answer, include this sentence, verbatim, in its initial prompt:

> You are running an `unattended` session (see `/know-unattended`).

## How to tell

If your session's initial prompt includes the sentence in
[Starting unattended sessions](#starting-unattended-sessions) above, you're
in an unattended session. If not, you're in an attended session. There is
no other signal.

## When unattended

- Carry on with everything you may do without the user's approval.
- An act that would need the user's approval (a permission prompt, a
  decision the project reserves for the user, a question you would
  otherwise ask) becomes a proposal in the session's final report: what you
  would do and why, with the drafted text or command ready to approve as
  written. Do not attempt it, and do not look for a route around the
  approval.
- Record each judgment call you make on your own in the final report, so
  the user can review it.
