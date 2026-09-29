---
name: use-adrs
description: >
  TODO
---

# Use ADRs

**ADR stands for "Architecture Decision Record"**

This skill explains how and when to read and write ADRs into your current project.

ADRs are stored in the `docs/adr/` directory in your project, or, if the project has both `docs` and `meta_docs` directories, in the `meta_docs/adr/` directory.

ADRs are indexed chronologically in order starting with `0001`. Each new ADR should be given the index corresponding to the next-lowest unused positive number, padding with zeroes as needed to achieve a four-character representation.

ADR filenames are formated `IIII-descriptive_slug_snake_case.md`, where "IIII" is the four-character index representation described above.

## Why ADRs?

The primary purpose of ADRs is _to preserve context on **why** past decisions were made_ so that:

- Future decisions can be informed by and consistent with past decisions
- We don't relitigate past decisions unnecessarily
- We can accurately discern when a past decision is obsolete and _should_ be changed

Litmus test: if what you are adding does not materially serve this goal, drop it. That includes skipping the ADR altogether.

## ADRs are not _the_ documentation

Do not confuse ADRs with the project's core documentation. ADRs are a stream format, with each ADR being an append-only near-immutable record of a decision made at a point in time. _They are the wrong tool for the job when it comes to general documentation_. Do not coerce ADRs into serving this purpose!

Instead, keep them short, and keep them focused on the decision and the reasoning for the decision. Let proper documentation capture the rest.

## ADRs in non-code repos

You should still use ADRs in non-code repos (e.g., a pure-markdown knowledge vault). Think of ADRs as figurative and applying to major non-code design, project, execution, and life decisions as well.

## When to write an ADR

You should offer to the user to capture an ADR only when ***all*** of the following are true. If you're unsure, err on the side of offering.

1. There are multiple compelling choices. If there was only one decent option, there's no meaningful decision to document.
2. A wrong decision has significant cost to unwind later. If it's easy to change, it's not worth documenting.
3. The decision seems non-obvious or even counter-intuitive without sufficient background.

If these are not all true, resist the temptation and _do not create an ADR_.

## Examples of ADR-worthy decisions

- Rejecting the seemingly-obvious choice
  - "we're only going to sell our products to our US customer base in exchange for Swiss Francs."
- Deciding based on non-obvious constraints
  - "We shouldn't choose S-corp tax election despite everybody's advice because we hold many appreciating assets (taxed unfavorably in an S-Corp)."
- Fundamental, identity decisions
  - "We writing this in golang"
  - "We're rejecting SQL in favor of a graph DB."
  - "We're going to be a non-profit."
- Vendor lock-in:
  - "We're building everything natively into AWS's Elastic Container Service, not Kubernetes."
- Removing capabilities
  - "Cameras will not be allowed to send any traffic to the internet at all."

## How to write an ADR

See `./writing-adrs.md`.
