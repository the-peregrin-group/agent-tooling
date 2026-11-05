---
date: 2026-11-03
status: current
---

# Platform usage lives in the wrapper's help; platform skills are failsafe pointers

**Context:** Each platform skill (use-bd, use-github, use-forgejo) was an operating manual for its wrapper, restating Verb grammars, exit codes, and quirks that the wrapper itself already knew, so the text drifted from the tool and every session paid for it whole. With the generic skills split by moment ([ADR 0021](0021-issue-skills-are-split-by-moment-of-need.md), issue skills split by moment of need), the question was what a platform skill is for at all. The 2026-11-03 home-in on the Issue Tracker skill family ([proposal](../projects/use-issues/2026-11-05-proposal.md)) settled it.

**Decision:** How to use a platform's tool lives in the tool. Every issue Verb documents itself through a help form that Permission rules can grant once, bounded per Verb, and every refusal and usage error names the skill to load. A platform skill is a failsafe entry point for an agent that searches tool-first: it says the wrapper exists, how to get its help, and which issue skills apply, and nothing more. A moment skill reaches the platform by saying "run your wrapper's help for this Verb".

**Rationale:** Usage that the tool prints cannot drift from the tool, is loaded at the exact moment of need and only then, and can be tested against the tool, none of which a skill's prose can offer.

## Consequences

- A wrapper is not done until its help meets the rule; each wrapper is brought up to it when it is built or rebuilt, so platform skills shrink to failsafes one at a time, not at once.
- The help form must be allowlistable without a wildcard inside the command, or the discovery edge prompts and agents stop following it.
- The rules test that parsed skill text for taught commands parses help output instead.
- Help text is reviewed prose like any skill; it may render from files shipped beside the wrapper so that it is read in review.

## Alternatives Considered

### Platform skills as operating manuals

**Description:** Keep use-bd, use-github, and use-forgejo as the complete teaching for each wrapper, as today.
**Rejection rationale:** Two sources for one fact, the tool and its manual, with the manual the one that drifts, and every session loads it whole.

### Platform sections inside the generic skills

**Description:** Each moment skill carries a short section per platform with that platform's Verb and quirks.
**Rejection rationale:** Every moment skill grows by the number of platforms, every session pays for platforms it is not on, and the drift moves into the generic layer.
