---
name: know-unattended
description: >
  A session is unattended only when its prompt declares that no person will
  answer during it; otherwise it is attended, and a person can be asked and
  is expected to answer. Load when deciding whether to ask a person or act
  on your own judgment, when a prompt or brief mentions "unattended", and
  before starting a subagent or workflow that no person will answer.
---

# Know: unattended sessions

The concepts are the lexicon's **Attended session** and **Unattended
session**
([LEXICON.md](https://github.com/the-peregrin-group/agent-tooling/blob/main/LEXICON.md)),
and the lexicon is authoritative for them. This Skill holds the operating
rule: how to tell which kind of session you are in, and what changes when
no person will answer.

## How to tell

Read the prompt: the request that started the session, or the brief that
started you as a subagent. It is the only evidence. How the session was
launched says nothing about whether anyone will answer: a background job, a
headless run, or a job-style Actor ID is common in sessions whose person is
at the keyboard. So a session is attended unless its prompt declares
otherwise.

Mentioning the word is not declaring it. A prompt that quotes an Issue about
unattended sessions, or names this Skill, has not said that no person will
answer. When the prompt leaves it unclear, treat the session as attended:
an unneeded question costs a turn, while acting alone on a decision that
was the person's can cost them the work of undoing it.

## When unattended

- Carry on with everything you may do without a person's approval.
- An act that would need a person's approval (a permission prompt, a
  decision the project reserves for a person, a question you would
  otherwise ask) becomes a proposal in the session's final report: what you
  would do and why, with the drafted text or command ready to approve as
  written. Do not attempt it, and do not look for a route around the
  approval.
- Record each judgment call you make on your own in the final report, so
  the person can review it.

## Starting other agents

A subagent or workflow cannot tell from its launch whether a person will
answer, any more than you can. When you start one that no person will
answer, say so in its prompt.
