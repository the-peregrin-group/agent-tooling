# Extract G: ADRs, LEXICON.md, CLAUDE.md, docs/index.md

> This document captures state as of 2026-10-26. For current state, see [docs/index.md](../../index.md).

Repo: agent-tooling, at `2bf1ca6` (main, 2026-10-26).
Sources read: all 16 ADR titles; full text of ADRs 0001, 0002, 0009, 0010, 0011, 0012 (Issue-relevant); LEXICON.md (Wrappers, Agentic systems, Tracking Work, Documents, Relationships); CLAUDE.md "Issue tracking & workflow", "Agent integration branches", "Documentation"; docs/index.md (only incidental Issue content).

ADRs judged out of scope (no Issue guidance): 0003-0006 (home-in / ADR mechanics), 0007 (installed copies), 0008 (bare-slash prefix), 0013 (exit codes; touched only under Contradictions), 0014 (bdw push mechanism), 0015 (path roots), 0016 (push host allowlist).

Provenance note: every commit in this repo is authored by the maintainer with an `Executed-By: claude-job-…` trailer, so authorship never distinguishes maintainer from agent text. Provenance below rests on (a) ADR status (ratified by definition), (b) commit messages that say "Ratified in the use-bd home-in session" or "The maintainer ratified", or (c) judgement.

---

## Principles

### G1: One Issue Tracker, one system of record, per repo
- Category: setup
- Generic or specific: generic
- Current text: LEXICON.md:193-196 "**Issue Tracker**: The one system of record (e.g., Beads, GitHub Issues) for this repo's actionable work: each unit of work is an Issue, tracked from filed to done. - _Avoid_: backlog, board"; ADR 0001 docs/adr/0001-adopt-beads-for-the-tracker-trial.md:10 "One tracker per repo with nothing leaving the machine keeps the trial readable and its perimeter trivially safe"
- Earliest form: e6b9834, 2026-09-24, "Docs: ADR 0001 for the Beads adoption; CONTEXT.md in the glossary format". CONTEXT.md: "**Tracker**: The one system of record for this repo's work; during the trial it is Beads, and GitHub Issues is frozen. - _Avoid_: backlog, board, issues (as a system name)". Ratified into its current wording at 8201891 (2026-09-28). Drift: generalized from a trial-specific "Tracker" to a tool-neutral "Issue Tracker"; the "one per repo" claim was later softened by ADR 0011 (see G3 and Contradictions).
- Provenance: ratified; evidence: 8201891 message "The maintainer ratified the lexicon's first state ... Tracking Work reduced to Issue Tracker, Issue, and Issue ID"; ADR 0001.

### G2: An Issue is one unit of actionable work, with status and dependencies
- Category: filing
- Generic or specific: generic
- Current text: LEXICON.md:198-200 "**Issue**: One tracked unit of actionable work in the Issue Tracker (e.g., a bug, a feature, a task), with a status and dependencies on other Issues. - _Avoid_: ticket"
- Earliest form: e6b9834, 2026-09-24. CONTEXT.md: "**Bead**: One tracked item of work in Beads, with a status, a type, an actor history, and dependencies on other beads. - _Avoid_: issue, ticket, task (as a system-level noun; `task` is a bead type)". Drift: "Bead" became tool-neutral "Issue" at 8201891; "a type" and "an actor history" dropped; "actionable" added; "issue" moved from avoid-list to the canonical term.
- Provenance: ratified; evidence: 8201891 (maintainer ratification).

### G3: Every reference to an Issue includes its Issue ID
- Category: docs-linkage
- Generic or specific: generic
- Current text: LEXICON.md:202-204 "**Issue ID**: An Issue's stable identifier in the Issue Tracker: unambiguous, but opaque to humans. - _Invariants_: every reference to an Issue includes its Issue ID"
- Earliest form: e6b9834, 2026-09-24. CONTEXT.md: "**Bead ID**: A bead's stable identifier, prefixed with this repo's issue prefix; the only way code, commits, and PR bodies refer to a bead. - _Avoid_: `#N` (that is a GitHub issue number)". Drift: "the only way ... refer to" (exclusive) became "includes" (an ID is required but other words may accompany it); "opaque to humans" added, which leaves room for the user's "name issues by title" practice.
- Provenance: ratified; evidence: 8201891.

### G4: Branch Issue vs Leaf Issue, defined by children or by designated kind
- Category: breakdown
- Generic or specific: generic (the "(e.g., an epic)" kind clause is the only tracker-flavoured part)
- Current text: LEXICON.md:206-211 "**Branch Issue**: An Issue that holds other Issues as its children: a project, rather than a unit of work one session finishes. An Issue is a Branch Issue if it has any children, open or closed, or if it is of a kind designated to hold children (e.g., an epic), even before it has any."; LEXICON.md:214 "- _Avoid_: branch (alone), parent, container"; LEXICON.md:216-219 "**Leaf Issue**: An Issue that is not a Branch Issue: a unit of work meant to be claimed and finished in one session (e.g., a task, a bug). A Leaf Issue that is given a child becomes a Branch Issue. - _Avoid_: subtask"; LEXICON.md:283-284 "An Issue is either a Branch Issue or a Leaf Issue, never both." / "A Branch Issue has zero or more child Issues; a Leaf Issue has none."
- Earliest form: 92ccc6d, 2026-10-08, "LEXICON: add Branch Issue and Leaf Issue". Unchanged since.
- Provenance: ratified; evidence: 92ccc6d message "Ratified in the use-bd home-in session ... The pair lets the hierarchy rules and the ready-work rules be stated without the industry baggage of "epic" and "task"." (Refs agent-tooling-aio).

### G5: A Leaf Issue is sized to one session
- Category: breakdown
- Generic or specific: generic (but "claimed" presumes a claim mechanism; see Contradictions)
- Current text: LEXICON.md:216-217 "a unit of work meant to be claimed and finished in one session (e.g., a task, a bug)"; LEXICON.md:206-207 "a project, rather than a unit of work one session finishes"
- Earliest form: 92ccc6d, 2026-10-08; unchanged.
- Provenance: ratified; evidence: 92ccc6d (home-in).

### G6: A Branch Issue's work is management
- Category: breakdown
- Generic or specific: generic
- Current text: LEXICON.md:209-211 "The work of a Branch Issue is management: scoping, setting success criteria, breaking down into child Issues, and verifying completion."; ADR 0009 docs/adr/0009-branch-issues-are-worked-in-passes.md:8 "A Branch Issue's work is management (scoping, setting success criteria, breaking down, verifying completion), but nothing in Beads schedules it"
- Earliest form: 92ccc6d (lexicon) and bf8609a (ADR 0009), both 2026-10-08; unchanged.
- Provenance: ratified; evidence: ADR 0009; 92ccc6d "Ratified in the use-bd home-in session".

### G7: A Branch Issue is ready work exactly when it has no open children; worked in session-sized passes
- Category: lifecycle
- Generic or specific: mixed (the rule is generic; "ready work" as a computed queue is Beads-native, and ADR 0011:30 says forge issues have no ready queue)
- Current text: docs/adr/0009-branch-issues-are-worked-in-passes.md:10 "**Decision:** A Branch Issue is ready work exactly when it has no open children, and each claim on it is one session-sized pass that ends either by adding children or by verifying completion and closing it."; :12 "The state of the tree then says when management work is due, so it needs neither a long-lived owner nor special tasks to stand in for one."; :16 "A new Branch Issue is ready work at once, and its first pass breaks it down."; LEXICON.md:212 "- _Invariants_: ready work exactly when it has no open children"
- Earliest form: bf8609a, 2026-10-08, "ADR 0009: Branch Issues are worked in passes". Unchanged except the link target (design.md to v1-proposal.md, b08ba40).
- Provenance: ratified; evidence: ADR 0009; bf8609a "Ratified in the use-bd home-in session".

### G8: No long-lived owner for a Branch Issue
- Category: agent-vs-human
- Generic or specific: generic
- Current text: docs/adr/0009-branch-issues-are-worked-in-passes.md:8 "No agent stays available across the days or weeks a Branch Issue can live, so that work cannot belong to a standing owner."; :35 "No agent stays available and up to speed across many sessions and days, and a claim cannot outlive its session."
- Earliest form: bf8609a, 2026-10-08; unchanged.
- Provenance: ratified; evidence: ADR 0009 (rejected alternative "A long-lived lead who owns the Branch Issue").

### G9: A Branch Issue is never closed merely because its children closed
- Category: closing
- Generic or specific: generic
- Current text: docs/adr/0009-branch-issues-are-worked-in-passes.md:17 "A Branch Issue is never closed merely because its children closed; a pass verifies it first."; :25 "An unbroken-down Branch Issue is invisible, and nobody verifies that the whole met its goal."; LEXICON.md:212-213 "never closed without a pass verifying completion"
- Earliest form: bf8609a and c9d62cf, 2026-10-08; unchanged.
- Provenance: ratified; evidence: ADR 0009; c9d62cf "give Branch Issue its invariants from ADR 0009".

### G10: Draft the whole breakdown before submitting it (atomic batch)
- Category: breakdown
- Generic or specific: mixed (drafting first is generic; "one atomic batch" assumes a tracker that can create several Issues at once)
- Current text: docs/adr/0009-branch-issues-are-worked-in-passes.md:18 "Children added in a pass become ready work as soon as they exist, so a pass drafts its whole breakdown before submitting it."; :40 "A session that dies mid-pass hides the whole subtree until its lease expires, whereas building the breakdown in one atomic batch gives the same privacy without a lock."
- Earliest form: bf8609a, 2026-10-08; unchanged.
- Provenance: ratified; evidence: ADR 0009.

### G11: No breakdown/acceptance placeholder tasks
- Category: breakdown
- Generic or specific: generic
- Current text: docs/adr/0009-branch-issues-are-worked-in-passes.md:29-30 "File a breakdown task first and an acceptance task, blocked by every sibling, last." / "The acceptance task's dependencies must be kept current as children are added, which works against the grain and is easily misunderstood or skipped."
- Earliest form: bf8609a, 2026-10-08; unchanged.
- Provenance: ratified; evidence: ADR 0009 Alternatives Considered.

### G12: Which tracker holds work follows who drives the work
- Category: setup
- Generic or specific: generic (names Beads vs forge issues as the instances)
- Current text: docs/adr/0011-beads-for-swarmed-work-forge-issues-for-long-lived-work.md:10 "**Decision:** The trial ends with Beads kept for work that agents swarm, while long-lived, low-churn, or human-driven work belongs in forge issues (GitHub or Forgejo Issues), and this repo stays on Beads alone until its long tail can move back to forge issues."; :12 "Beads' one real advantage over forge issues is agent-native operation (a computed ready queue, single-owner claims, a per-session Actor, no forge round-trip), whereas ownership and self-hosting argue for Forgejo just as well, so the choice follows who drives the work."; :35 "For work agents do not swarm, Beads adds nothing over forge issues and offers a human reader less."
- Earliest form: 9612742, 2026-10-16, "ADRs 0011 and 0012: end the Beads trial; private Forgejo remote"; unchanged.
- Provenance: ratified; evidence: ADR 0011 (status current).

### G13: Each Issue has one writable home at a time; no sync between trackers
- Category: setup
- Generic or specific: generic
- Current text: docs/adr/0011-beads-for-swarmed-work-forge-issues-for-long-lived-work.md:17 "A project with both kinds of work needs Beads and forge issues together, each Issue with one writable home at a time, checked out to Beads for a swarm and back afterwards; that pattern is not built (`agent-tooling-ze3`)."; CLAUDE.md:54 "There is no sync in either direction."; docs/adr/0001-adopt-beads-for-the-tracker-trial.md:26 "Two writable sources of truth for one repo make the trial's outcome unreadable and the perimeter non-trivial; the freeze costs one hand refile on no-go, which is cheaper than any conflict rule."
- Earliest form: e6b9834, 2026-09-24, ADR 0001 Decision "no sync in either direction"; and CONTEXT.md "**External reference**: The pointer a bead carries to the record it was imported from, here a GitHub issue URL; it identifies provenance and never implies sync." Drift: began as "one tracker per repo, no sync"; ADR 0011 (2026-10-16) reframed to "one writable home per Issue", permitting two trackers in one project. "External reference" was dropped from the lexicon at 8201891 without a Retired line.
- Provenance: ratified; evidence: ADR 0001, ADR 0011; 6b20686 message "the principles become one writable home per Issue and private Issue data".

### G14: No writes to the stale GitHub copies
- Category: agent-vs-human
- Generic or specific: specific to this repo (generic kernel: a non-home copy of an Issue is never written)
- Current text: CLAUDE.md:50-54 "GitHub Issues stays enabled but takes no work: the open issues were imported into Beads once, one way, on 2026-09-24, and stay open on GitHub as stale copies. No GitHub issue is filed, edited, relabeled, reprioritized, or closed until the long tail moves back to forge issues (`agent-tooling-ze3`)."; docs/adr/0011-...:16 "agents file and change nothing there until the long tail moves back."; CLAUDE.md:131-132 "GitHub issues are stale copies and stay untouched (see Issue tracking)."
- Earliest form: 50e29e6, 2026-09-24, "CLAUDE.md: tracking moves to Beads for the trial; GitHub Issues frozen": "GitHub Issues are frozen: the open issues were imported into Beads once, one way, and no GitHub issue is filed, edited, relabeled, reprioritized, or closed while the freeze holds." Drift: "while the freeze holds" became "until the long tail moves back" at 6b20686.
- Provenance: ratified (via ADR 0001 and ADR 0011 Consequences).

### G15: Tracker policy belongs in code agents cannot talk past, not in text
- Category: agent-vs-human
- Generic or specific: generic principle; Beads-specific instance
- Current text: docs/adr/0010-bdw-carries-beads-policy-in-tiers.md:10 "**Decision:** `bdw` carries the Beads policy that Permission rules cannot express, handling each operation in the lightest of three tiers that suffices: pass-through, a thin intercept that fails closed on any command line it cannot read unambiguously, or a Verb of its own whose superseded raw `bd` commands are denied."; :12 "Policy then lives in code that agents cannot talk past"; :24 "Prefix rules cannot express kind checks, readiness, or claim release, and text alone loses to agents' habits."; LEXICON.md:10-14 "**Wrapper**: A facade over one raw tool or service (e.g., git, a forge, the Issue Tracker) that ... encodes the project's conventions in code instead of leaving them to agent judgment."; LEXICON.md:97-99 "**Permission rule**: A declared rule that decides whether an agent may take an action on its own, only with a human's approval, or never. - _Invariants_: enforced programmatically, never left to agent judgment"
- Earliest form: 50e29e6, 2026-09-24 (CLAUDE.md): "Which `bd` subcommands an agent may run is policy in `.claude/settings.json` (allow, ask, deny), not judgment. A denied call is the policy working; do not look for another spelling of it." and e6b9834 CONTEXT.md "**Command policy**: The allow, ask, and deny rules that decide which tracker subcommands an agent may run without a human, with a human, or never; policy, not judgment." Drift: grew from "settings.json rules, not judgment" to a three-tier wrapper-carried policy (ADR 0010, 4207112, 2026-10-09). The instruction "A denied call is the policy working; do not look for another spelling of it" is no longer in CLAUDE.md (not checked whether it survives in use-bd).
- Provenance: ratified; evidence: ADR 0010; 4207112 "Ratified in the use-bd home-in session".

### G16: Kind checks on what may take children
- Category: breakdown
- Generic or specific: mixed (rule is generic; enforcement is bdw)
- Current text: docs/adr/0010-bdw-carries-beads-policy-in-tiers.md:8 "The use-bd design needs policy that Permission rules cannot express (which kinds may take children, what counts as ready work, releasing a Branch Issue's claim)"
- Earliest form: 4207112, 2026-10-09; unchanged. The ADR names the policy but does not state which kinds; the rule itself lives elsewhere (use-bd).
- Provenance: ratified (existence of the policy); content of the rule not in my sources.

### G17: Every tracker write records its Actor
- Category: agent-vs-human
- Generic or specific: mixed (recording the actor is generic; BD_ACTOR/trailer is specific)
- Current text: LEXICON.md:40-42 "**Actor**: The party, an agent or a person, that carried out an action or a piece of work and is recorded as having done so. - _Avoid_: user, author, assignee"; LEXICON.md:44-46 "**Actor ID**: ... - _Invariants_: never shared by two Actors"; LEXICON.md:268-269 "bdw and gitw record the Actor on the writes they attribute: bdw on the Issue Tracker, gitw on its commits."; docs/adr/0002-beads-identity.md:10 "Identity must come from the harness environment on every invocation"
- Earliest form: e6b9834, 2026-09-24, CONTEXT.md: "**Actor**: The session identity a wrapper derives from its own environment and records on every write it makes: a job-derived actor for background-job sessions, a visibly distinct attended fallback otherwise. _Avoid_: user, author, assignee (an actor is a session, not a person)". Drift: at b90e669 (2026-10-08) Actor became "the party, agent or person"; "an actor is a session, not a person" was reversed; session mechanics moved to the use-bd design.
- Provenance: ratified; evidence: ADR 0002; 8201891 and b90e669 (use-bd home-in, Refs agent-tooling-aio).

### G18: Issue content is private; never published outside the content lint
- Category: setup
- Generic or specific: generic principle (Issue data can carry unlinted content); Dolt/Forgejo specific instance
- Current text: docs/adr/0012-beads-data-syncs-to-private-forgejo-remote.md:12 "a private, self-hosted remote keeps unlinted Issue content, with its full Dolt history, from ever being published."; :30 "Every Issue, note, and comment would be published along with its full history, outside the content lint; no lint path for Issue data exists, and a published history cannot be withdrawn."
- Earliest form: e6b9834, 2026-09-24, ADR 0001 Rationale "nothing leaving the machine keeps ... its perimeter trivially safe". Drift: local-only became private-remote-only at 9612742 (2026-10-16).
- Provenance: ratified; evidence: ADR 0012.

### G19: Nothing is deleted from the tracker; closed Issues are hidden, not forgotten
- Category: closing
- Generic or specific: mixed (no forgetting is generic; the command list is Beads)
- Current text: docs/adr/0001-adopt-beads-for-the-tracker-trial.md:10 "closed beads are hidden from agents by default so forgetting buys nothing."; :14 "The forgetting commands (`admin cleanup`, `prune`, `gc`, `admin compact`) never run; the command policy denies them and nothing else deletes."
- Earliest form: e6b9834, 2026-09-24, in the Decision: "and the forgetting commands (`admin cleanup`, `prune`, `gc`, `admin compact`) never run." Moved from Decision to Gotchas later (6d14234 or 4b7e708); substance unchanged. ADR 0001 is now "amended" but neither amendment touches this.
- Provenance: ratified; evidence: ADR 0001.

### G20: PR body names the Issue it lands ("Lands <id>"), not "Closes #N"
- Category: docs-linkage
- Generic or specific: mixed (naming the Issue is generic; "Closes #N" vs "Lands" is because Beads cannot auto-close from a forge)
- Current text: CLAUDE.md:69-72 "Pull requests are unaffected. **Load the `use-github` skill before opening a PR**; its issue-filing and board conventions do not apply while Beads is the Issue Tracker, and a PR body names the Issue it lands (`Lands agent-tooling-xyz`) instead of `Closes #N`."
- Earliest form: 50e29e6, 2026-09-24: "a PR body names the bead it lands (`Lands agent-tooling-xyz`) instead of `Closes #N`." Drift: "bead" became "Issue"; "suspended for the trial" became "do not apply while Beads is the Issue Tracker".
- Provenance: unknown (CLAUDE.md; agent-executed commit with no ratification record), though it implements G3.

### G21: TODO comments cite the Issue ID
- Category: todo-comments
- Generic or specific: mixed
- Current text: CLAUDE.md:59-60 "This repo's Beads conventions (labels, the friction log, `TODO` citations) are in `.beads/PRIME.md`, which `bdw prime` prints." (pointer only; the rule itself is not in my sources now)
- Earliest form: 50e29e6, 2026-09-24: "a `TODO` comment cites the bead ID (`TODO(agent-tooling-xyz)`), not `#N`." Before that, CLAUDE.md pointed to use-github's "`TODO(#N)` rule". Drift: the rule moved out of CLAUDE.md into .beads/PRIME.md; CLAUDE.md now holds only a pointer.
- Provenance: unknown; same as G20.

### G22: A Known gap is a defect or omission in a shipped capability, one line with its Issue ID, added when filed and removed by the fixing PR
- Category: docs-linkage
- Generic or specific: generic
- Current text: CLAUDE.md:102-104 "`### Known gaps` under `## Status`: defects or omissions in shipped capabilities, one line each with its Issue ID, added when the Issue is filed and removed by the PR that fixes it."; CLAUDE.md:113-115 "Living docs describe shipped capabilities as intended. Where `main` falls short of that (a defect, or an omission not yet built), the project's Known gaps says so, citing the Issue."
- Earliest form: d99d605, 2026-10-01, "docs: scaffold the per-project documentation convention": "`### Known gaps` follows: defects in shipped capabilities only, one line each with its Issue ID." and "Living docs describe the code as it is on `main`. No living doc presents unbuilt behavior as current". Drift: at fb5f8bd (2026-10-24) "defects ... only" widened to "defects or omissions"; the filed/fixed lifecycle was added; and the living-docs rule flipped from "describe the code as it is on main" to "describe shipped capabilities as intended", with Known gaps carrying the difference.
- Provenance: unknown; fb5f8bd is agent-executed with no ratification statement. (Judged likely maintainer-directed because it rewrites a CLAUDE.md rule and the flip is deliberate, but no record says so.)

### G23: A planned capability links its proposal and Issue IDs
- Category: docs-linkage
- Generic or specific: generic
- Current text: CLAUDE.md:98-101 "with the closed state set `shipped`, `planned` (ratified; links its proposal doc and Issue IDs), `proposed` (proposal in workshop), `retired` (kept only if it prevents reintroduction; links an ADR)."; CLAUDE.md:115-117 "A capability not yet built at all lives in a dated proposal, linked from a `planned` or `proposed` Status row and its Issues."
- Earliest form: d99d605, 2026-10-01; unchanged in substance.
- Provenance: unknown (same as G22).

### G24: A PR that lands an Issue updates its Status row; what one PR cannot make true becomes a Known gap or open Issue
- Category: closing
- Generic or specific: generic
- Current text: CLAUDE.md:119-126 "**Per PR:** a PR leaves the repo as consistent as one PR can make it. Search for what changed (the Verb, flag, exit code, path, Issue ID, old behavior) across `docs/`, `skills/`, `cli/` (docstrings and tests), `README.md`, `LEXICON.md`, `.beads/PRIME.md`, and open Beads Issues (`bdw search`, `bdw list --desc-contains=<words> --all`), and update every hit. Whatever one PR cannot make true yet (a later PR, another repo, a deployment) is a Known gap or an open Issue that names it. A PR that lands an Issue updates its capability's Status row."
- Earliest form: d99d605, 2026-10-01: "Merge-readiness: a PR that lands an Issue updates that capability's Status row in the same PR, and a PR that changes behavior a living doc describes updates that doc in the same PR." Drift: fb5f8bd replaced "Merge-readiness" with the two-level "Done is consistency" rule; searching open Issues and filing an Issue for leftovers are new.
- Provenance: unknown (fb5f8bd, no ratification record).

### G25: An Issue is done only when every surface agrees
- Category: closing
- Generic or specific: generic
- Current text: CLAUDE.md:127-132 "**Per task:** an Issue is done only when every reference across every surface we control agrees with the change, however many PRs, repos, deployments, or authors that takes: this repo, consumer repos, the installed copies (`tooling-install apply`), Beads, and Permission rules."
- Earliest form: fb5f8bd, 2026-10-24; unchanged.
- Provenance: unknown (as G24).

### G26: Every Docs Inbox item is owned by an open Issue
- Category: docs-linkage
- Generic or specific: generic
- Current text: LEXICON.md:248-256 "**Docs Inbox**: The one place in a project where an agent drops material that belongs in the project's documentation when it does not know where that material belongs, so that later tracked work can incorporate it. ... - _Invariants_: every item in it is owned by an open Issue to incorporate it; nothing is meant to stay in it"
- Earliest form: b66891c, 2026-10-09, "LEXICON: add Docs Inbox; use-bd design: how it is used"; unchanged. The commit adds "recorded on that Issue" for the incorporation judgement, which the entry does not carry.
- Provenance: unknown, leaning ratified (lexicon entry from the use-bd home-in job, Refs agent-tooling-aio; the message does not say "ratified").

### G27: Agents land into agent integration branches; `main` is human-only
- Category: agent-vs-human
- Generic or specific: generic (git, but it bounds what an agent may do once an Issue's work is ready to land)
- Current text: CLAUDE.md:76-83 "Agents may rebase onto one ... and merge PRs into it unattended ... The exact branch for a run is pinned by the maintainer's local Permission rules, and deleting those rules retires it. `main` stays human-only: the only PRs to `main` are the ones a human asked for."
- Earliest form: 4a00475, 2026-10-10, "CLAUDE.md: designate integrate/ branches as integration branches"; "`main` stays human-only" unchanged. The final clause "the only PRs to `main` are the ones a human asked for" was added later (not traced).
- Provenance: unknown, leaning ratified (lexicon "Agent integration branch" came in as "ratified proposal", 132bf4a, 2026-10-11).

### G28: Agents may not choose their recorded identity
- Category: agent-vs-human
- Generic or specific: specific mechanics with a generic kernel
- Current text: docs/adr/0002-beads-identity.md:9 "A `bdw` wrapper derives the actor on every call, sets `BD_ACTOR` and `BEADS_ACTOR` to it (overriding the caller), refuses bd's `--actor` flag"; docs/adr/0001-...:18 "bd's own `--actor` flag would let a caller name the actor `bdw` is supposed to derive; the policy denies the flag in any position on every name of the binary."
- Earliest form: 7ecc672 / 6fd4a89, 2026-09-25; unchanged in substance.
- Provenance: ratified; evidence: ADR 0002.

### Principles present in earlier forms of these sources, now gone from them
Recorded because the brief asks for the union and for original intent. Not checked whether use-bd or PRIME.md carry them now.
- G29 (lifecycle): 50e29e6, CLAUDE.md, 2026-09-24: "Loop: `bd prime` at session start, `bd ready` to find work, `bd update <id> --claim` before touching code, `bd create --deps=discovered-from:<id>` for anything you find along the way, `bd close <id>` when done, and close or unclaim everything you hold before the session ends." Generic kernels: claim before work; file what you discover, linked to where you found it; release everything you hold at session end.
- G30 (relationships): e6b9834, CONTEXT.md: "**Discovered-from**: The dependency recorded from a bead to the bead whose work surfaced it." Dropped at 8201891 with no Retired line ("the converted glossary was never ratified").
- G31 (agent-vs-human): 50e29e6: "A denied call is the policy working; do not look for another spelling of it."
- G32 (other): 50e29e6: "Ignore `bd prime` where it contradicts the harness or `use-git`: memory stays in the harness's memory files". The kernel: the tracker's own agent instructions yield to the project's.
- Provenance of G29-G32: unknown; agent-executed commits. G30 was explicitly not ratified (8201891).

---

## Platform-specific mechanics (not traced)
- ADR 0001:15 `bd init` side effects (Dolt remote from origin, auto-backup, metrics, commits `.beads/`, `.beads.gate.lock`); `bd dolt remote remove origin` is a maintainer hand step.
- ADR 0001:16 command policy is `.claude/settings.json` deny/ask/allow with `cli/repo_policy_test.py` as spec; ask rows on `exec`, `env`, `sh -c`, `xargs`; not safe in auto mode until the parsed-command hook lands.
- CLAUDE.md:62-67 Beads Permission rules are generated from `skills/use-bd/rules.json` plus the local layer in `cli/repo_policy_test.py`.
- ADR 0002:9,16 `bdw` sets both `BD_ACTOR` and `BEADS_ACTOR`; `gitw-commit` writes `Executed-By:` trailer, refuses several.
- ADR 0002:18 `bdw` exits 3 when no `bd` on PATH or the first one is `bdw`.
- ADR 0010:16 raw `bd` commands superseded by a `bdw` Verb are denied; agents learn `bdw`'s Verb names.
- ADR 0012:17 the remote address stays out of tracked `.beads/config.yaml`.
- ADR 0014:10 `bdw` starts a detached, coalesced background push after every successful non-read call.
- CLAUDE.md:123 consistency search via `bdw search` and `bdw list --desc-contains=<words> --all`.
- docs/index.md:82-84 on a forge where issues and PRs share one number space, a number naming the other kind exits 2 and the message names the sibling Verb.
- docs/index.md:155-156 `bdw` passes arguments to `bd`, whose parser owns the refusal.

---

## Contradictions

1. **Database "local to the maintainer's machine" vs the shipped private remote.**
   - CLAUDE.md:48-49 "The committed `.beads/` files are config only; the database is local to the maintainer's machine."
   - .beads/PRIME.md:8 "The database is local to the maintainer's machine, and"
   - vs docs/projects/beads-trial/index.md:63 "| A private Dolt remote on the maintainer's self-hosted Forgejo, pushed after every write | shipped |" and ADR 0012:10 / ADR 0014:10. HEAD commit 2bf1ca6 is "Beads docs: the private Dolt remote is shipped". CLAUDE.md and PRIME.md are stale.

2. **One Issue Tracker per repo vs two trackers in one project.**
   - LEXICON.md:193 "**Issue Tracker**: The one system of record (e.g., Beads, GitHub Issues) for this repo's actionable work"; LEXICON.md:282 "The Issue Tracker holds many Issues"; ADR 0001:10 "One tracker per repo"
   - vs ADR 0011:17 "A project with both kinds of work needs Beads and forge issues together, each Issue with one writable home at a time". The lexicon was not updated for ADR 0011. A generic `use-issues` skill needs one answer: one tracker per repo, or one home per Issue.

3. **Leaf Issue "claimed" and Branch "ready work" vs trackers that have neither.**
   - LEXICON.md:216-217 "a unit of work meant to be claimed and finished in one session"; LEXICON.md:212 "ready work exactly when it has no open children"
   - vs ADR 0011:30 "Forge issues have no ready queue, no single-owner claims, and one identity for every agent". The lexicon is meant to be tracker-neutral but leans on Beads-native concepts. Not a hard contradiction (assignment or a label could stand in for a claim), but a generic skill has to say what "claim" and "ready" mean on a forge.

4. **Is bdw inside the Exit-code contract?** (tangential, but it bears on how agents read tracker failures)
   - LEXICON.md:266-267 "Every Wrapper and the Installer report through the Exit-code contract; an underlying tool's own exit status never reaches the caller." and ADR 0013:10 "All agent-tooling software exits with one six-code contract"
   - vs docs/index.md:155-156 "`bdw` is outside it by design: it passes its arguments to `bd`, whose own parser owns the refusal." and ADR 0013:8 "`bdw` passes bd's codes through" (stated as the problem being fixed). Possibly a Known gap that is worded as "by design".

5. **Issue ID "the only way" vs "includes".** Not a live contradiction, but the drift matters for intent: CONTEXT.md e6b9834 "the only way code, commits, and PR bodies refer to a bead" vs LEXICON.md:204 "every reference to an Issue includes its Issue ID".

6. **Living docs: "as it is on main" vs "as intended".** Not a contradiction within today's sources; d99d605 "Living docs describe the code as it is on `main`" was deliberately replaced at fb5f8bd with CLAUDE.md:113 "Living docs describe shipped capabilities as intended". Flagged because it reverses the earlier rule; any skill text that still says "describe the code as it is" is stale.

---

## Judgement calls
- Included ADRs 0001, 0002, 0009, 0010, 0011, 0012 as Issue-relevant. Excluded 0014 and 0016 (push mechanics) except as mechanics lines, and 0013 except for Contradiction 4.
- Treated CLAUDE.md text as "unknown" provenance unless an ADR or a "ratified" commit message backs it. Every commit has the maintainer as git author and an agent `Executed-By`, so authorship proves nothing. CLAUDE.md is the maintainer's standing instruction, so it is plausibly endorsed, but I found no ratification record.
- Included G27 (main human-only) and G28 (actor not chosen by the caller) under agent-vs-human, though they are adjacent to Issues rather than about them.
- Added G29-G32, which are gone from the current sources, because the brief's purpose is recovering original intent; they are marked as not ratified or unknown.
- Did not consult use-bd, use-github, PRIME.md, or Beads Issues except to verify Contradiction 1 (.beads/PRIME.md:8 and beads-trial index.md:63). Other readers cover those.
- docs/index.md has no Issue-workflow principles; I used it only for mechanics and Contradiction 4.
