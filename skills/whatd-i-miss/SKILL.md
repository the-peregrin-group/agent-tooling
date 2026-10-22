---
name: whatd-i-miss
description: >
  Fill the user in on where the session stands since the last user turn/message. Give high-level
  explanations that explain the proverbial forest, not the texture of the knot on a branch of an
  individual tree.
argument-hint: "[anything in particular on which to focus filling you in?]"
disable-model-invocation: true
---

# What'd I Miss?

Provide an editorialized summary of what has transpired in this session since the last time the user sent a message. Your editorializing should focus on maximizing the user's understanding of overall progress towards session goals while being as clear and concise as possible.
## Editorial guidance

- **Plain english; minimal jargon**
- **300-400 words max:** if you think there is more that must be said, offer breadcrumbs to the user to expand in the most important areas. Example: "We discovered unexpected complexity in X that changes the path forward. Shall I fill you in?"
- **Focus on high-level outcomes, not narrative:** frame progress in terms of the user's requested outcomes/requirements, not nitty gritty implementation steps. History/narrative is only needed if it informs the outcomes (e.g., forced a different outcome than anticipated).
- **Spell out opaque references**: any opaque ids or references (e.g., git commit sha, github issue or pr number, document section, list item, legal code, etc.) should be accompanied by plain english summaries for human consumption and a pointer (or link, if possible) to the source. Example:
  - Bad: "...and after resolving #71 we can address #133."
  - Better: "...and after factoring authentication and authorization into two separate modules ([#71](https://link.to/github/issue)), we can address the new authentication race condition you found today ([#133](https://link.to/other/issue))."

## Asking for decisions

If there are pending decisions that the user must make, leave it to the end of your summary in a single sentence of the form:

> There are `N` pending decisions needed from you to be able to proceed. Shall we take them one-by-one now?

If the user affirms, explain one decision at a time (one per turn) in the following format:

```md
**[decision headline]**

Context: [2-3 sentences max, high-level motivation for the problem, locating the problem from the top down as needed]

Decision: [1 clear, concise sentence: exactly what must be decided?]

[optional] Options: [only if the decision is "multiple-choice," a list of the options to choose from, one sentence each with clear, high-level explanation]
```

Do not move on to the next decision on your own until the user has confirmed the current decision.
