# handoff: the Handoff Skill

The `handoff` Skill writes a Handoff: a self-contained brief with which an
agent passes work to another agent or a human, so the recipient can carry it
on without the sender's conversation. The default case is a fresh agent on a
strong model, in the same repo on the same machine, started by the user
within minutes; the Skill writes the Handoff to a temporary file under
`/tmp/claude/` and prints a paste-ready kickoff prompt for that session.
Guidance in the invocation overrides every default (recipient, destination,
focus, length) except the privacy rules.

## Status

| Capability | State | Where |
|---|---|---|
| A Handoff written to a temporary file, with the path, a paste-ready kickoff prompt, and a warning that the file will be wiped | shipped | `skills/handoff/SKILL.md` |
| Recipient defaults, adjusted for a human, another repo or machine, or a weaker model | shipped | `skills/handoff/SKILL.md` |
| Work the recipient builds on committed (and pushed when it may leave the machine) and named by ref, and the current time read rather than guessed | shipped | `skills/handoff/SKILL.md` |
| Privacy: no secrets, the use-privacy Skill loaded when listed, and no content sent to a wider audience than its source had | shipped | `skills/handoff/SKILL.md` |
| A fixed section order (Summary, Goal, Verification always; checked and believed claims under State) and writing rules that link rather than copy | shipped | `skills/handoff/SKILL.md` |
| A self-check against five questions, with an optional cold read by a subagent | shipped | `skills/handoff/SKILL.md` |
| A one-sentence offer when work is set aside unfinished; written unasked only when unattended | shipped | `skills/handoff/SKILL.md` |
