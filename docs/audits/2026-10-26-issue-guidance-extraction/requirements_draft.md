# Requirements draft: the generic use-issues model

> This document captures state as of 2026-10-26. For current state, see [docs/index.md](../../index.md).

Drafted 2026-10-26 for agent-tooling-u9n.1 (scope the Issue Tracker skill family),
step 2 (requirements review). Inferred from catalog.md in this directory; catalog
IDs are in brackets. Tags: [ratified] = an ADR, the use-bd home-in, the fjw
issue-verbs proposal, or a recorded maintainer ruling says it; [consistent] =
several sources agree but who wrote them is unknown; [single-source] = one
source says it, provenance unknown (almost always triage-issues).

## Requirements

### Where Issues live

- **R1.** Each Issue has exactly one writable home: work agents swarm lives in Beads; long-lived, low-churn, or human-driven work lives in forge issues. Trackers never sync, and a copy that is not an Issue's home is never written. [K1, K3, K4] [ratified]
- **R2.** Issue content stays private unless it is deliberately published. [K5] [ratified]
- **R3.** Load the privacy rules before composing any Issue text that leaves the machine. [K6] [consistent]

### What agents may do

- **R4.** What an agent may do on a tracker is decided only by reviewed Permission rules, granted per operation and per repo at the maintainer's choice. Per-repo conventions never grant anything, and an agent acts only on its own project's Issues unless expressly permitted. [K11, K12, K86] [ratified]
- **R5.** A denial, refusal, or permission prompt is the policy working: fix the call or report the gap, and never look for another spelling or reword the text to get past it. Report friction with the tracker; offer upstream bug reports, but never file them on your own. [K14, K15, K87] [ratified]
- **R6.** Setting up a tracker, or standing up triage in a repo, is a human procedure: the agent confirms the target, drafts the whole plan, and waits for approval. [K7, K85] [consistent]
- **R7.** Labels and other tracker schema encode the project's process: an agent may create them while initializing a repo, and treats an unknown label as a typo to fix, but any later change to the schema is a human's call. [K30, K31] [ratified]
- **R8.** Decisions (scope, design, direction, whether to write an ADR) belong to the human; the agent surfaces them and drafts. [K82, K89] [consistent]
- **R9.** Every state change has exactly one recorded owner, and an agent cannot choose the identity it is recorded under. [K60] [ratified]
- **R10.** An agent that shares its session's identity (a sub-agent) reads, files, and appends, but never claims, closes, or rewrites an Issue; an orchestrator puts this rule in every brief. [K61] [ratified]

### Filing

- **R11.** Search open and closed Issues before filing; if a near-twin exists, add to it instead of filing another. [K16] [ratified]
- **R12.** Capture is never blocked: file with what you know and say honestly what is unknown, never with placeholder text. No Issue is empty. [K17, K18] [ratified]
- **R13.** The title states the outcome; the body says what, why, and what done looks like, so someone outside the conversation can pick it up. [K19] [consistent]
- **R14.** File what you find along the way as a new Issue, linked to the Issue whose work surfaced it. [K22] [ratified]
- **R15.** Classifying your own new Issue is part of filing it; changing an Issue's surface in place is triage, and mislabeled filings are what triage is for. [K23] [ratified]
- **R16.** Every Issue has exactly one kind, recorded once in the tracker's own mechanism for kind, and at least one area from the project's declared scheme; it may carry other labels. [K27, K29] [consistent]
- **R17.** The kinds are feature, improvement, bug, debt, and meta, kept the same across repos. [K28] [consistent]
- **R18.** Priority has four levels (P0 drop everything, P1 most important non-emergency, P2 standard backlog, P3 opportunistic), lives in one place per repo, and exists to answer "what do I work on next?" [K32] [consistent]
- **R19.** Converting an existing backlog gives every item one verdict and keeps its source, then produces one deduplicated plan, written as a full document the maintainer reviews, which one filer then files serially. [K25] [ratified]

### Breakdown

- **R20.** One Issue is one session's work (a Leaf Issue); anything bigger is a Branch Issue. A task that outgrows a session is retyped as a Branch Issue rather than given subtasks. [K21, K36, K40] [ratified]
- **R21.** A Branch Issue's work is management: scoping, setting success criteria, breaking down, and verifying completion. It is worked in session-sized passes, is ready exactly when it has no open children, and is never closed merely because its children closed. [K36, K37, K39] [ratified]
- **R22.** A pass drafts its whole breakdown before filing any of it, with no placeholder breakdown or acceptance tasks. [K38, K41] [ratified]
- **R23.** Group Issues under a parent only when no member delivers value alone, never because of a dependency or a schedule; prefer vertical slices and do not over-decompose. A parent's status is its own, not derived from its children's. [K42, K43] [single-source]

### Relationships

- **R24.** At filing, look for four relationships (dependency, duplication, composition, contradiction) and add dependencies on your own. [K45] [ratified]
- **R25.** State every relationship's type explicitly: a wrong blocking edge silently hides work, and provenance links do not block. [K46] [ratified]
- **R26.** Each relationship has one spelling and one direction, and the tracker's native link, not prose, is its source of truth. [K47, K48] [consistent]
- **R27.** A blocker matters only once the Issue reaches the stage it blocks; mark it then, and link it when the blocker is itself an Issue. [K49] [single-source]
- **R28.** Work waiting on a human leaves ready work through a blocker, not a special status, and joins one queue for the human. [K50] [ratified]

### Lifecycle

- **R29.** Status answers "what kind of expert attention does this Issue need next?" [K51] [consistent]
- **R30.** An Issue may regress to an earlier state at any time; no later-stage work goes on top of an earlier stage's gap; and open-or-closed always agrees with status. [K52, K54, K57] [single-source]
- **R31.** Scoping defines the problem, not the solution (motivation, beneficiary, acceptance criteria, out of scope, constraints, adjacencies); engineering design is done when an implementer could proceed without further design input. [K55, K56] [single-source]
- **R32.** The working loop: choose work explicitly, claim before touching it, append progress as you go (on human-filed Issues too), close when the acceptance criteria hold, and release everything you hold before the session ends. Never take over someone else's claim; ask. [K44, K58, K59, K68, K69] [ratified]
- **R33.** An Issue is a living document: its description is its current state, rewritten in place, and its comments are an append-only log. [K62, K63] [ratified]
- **R34.** A fresh session can resume any Issue from the tracker alone: the Issue points to context kept in the project's standard documents rather than holding it. [K64, K65] [ratified]

### Closing and linkage

- **R35.** Every close and every reopen carries its reason; forge auto-close on PR merge is the one exception, and reopening needs more authority than closing. [K70, K71] [ratified]
- **R36.** Nothing is deleted from the tracker; closed Issues are hidden, not forgotten. [K72] [ratified]
- **R37.** An Issue is done only when everything that describes it agrees, including the TODO comments that cite it. Every TODO comment cites a real Issue, filed first. [K74, K75] [consistent]
- **R38.** Every reference to an Issue includes its Issue ID. [K77] [ratified]
- **R39.** A PR or commit says whether it finishes an Issue or only advances it. [K78] [consistent]

### Triage

- **R40.** Filing-time checks are best effort; a separate batch pass across the whole tracker reconciles what they miss. [K79] [ratified]
- **R41.** Unattended work accumulates proposals and reports, and never resolves what needs a human. [K81] [consistent]
- **R42.** Judge recency and staleness from exact timestamps compared with the current time, never from rendered dates. [K84] [ratified]

## Disconnects

Ordered by how much each shapes the design.

### 1. One tracker per repo, or one writable home per Issue?
- "**Issue Tracker**: The one system of record (e.g., Beads, GitHub Issues) for this repo's actionable work" (LEXICON.md:193-196) [ratified, 8201891]; "One tracker per repo with nothing leaving the machine keeps the trial readable" (docs/adr/0001-adopt-beads-for-the-tracker-trial.md:10) [ratified, trial-era]
- "Set up GitHub Issues as the single source of truth for a repository's task tracking." (skills/setup-github-issues/SKILL.md:4-5) [unknown]
- "A project with both kinds of work needs Beads and forge issues together, each Issue with one writable home at a time" (docs/adr/0011-beads-for-swarmed-work-forge-issues-for-long-lived-work.md:17) [ratified, later]
- Affects: R1, the lexicon's Issue Tracker entry, whether setup claims sole authority in a repo, and whether use-issues must route each new Issue to one of two trackers.

### 2. May an agent close, mark a duplicate, or reparent on its own?
- "reparenting, tracker creation, and especially issue-closing await human confirmation." (skills/triage-issues/SKILL.md:132); "Flag candidates; do not auto-merge." (:191) [unknown]
- "| duplication | `bdw duplicate <id> --of=<canonical>` (closes it) | only when very confident |" and "| composition | `--parent=<id>` at filing | only when very confident |" (skills/use-bd/SKILL.md:154-155) [ratified, home-in]; "reversible, visible operations such as marking a duplicate or superseding an Issue are allowed, and when to use them is a filing discipline, not a permission." (PROP:198-213) [ratified]
- Contributor tier allows close; "an agent that may close its own finished work does not thereby get to resurrect anything." (docs/projects/fjw/issue-verbs.md:108-109, :161) [ratified]
- "Is a close an ordinary reversible act that needs only a reason, with triage's restriction scoped to its unattended passes, or a judgement the human confirms everywhere" (`bdw show agent-tooling-k6z`) [open]
- Affects: R24 (I kept only "add dependencies on your own"; the "other three only when very confident" half is held here), R32, R35, triage's autonomy boundary (K80), and per-platform grants.

### 3. Are requirements checked at filing or when an Issue leaves a state?
- "each state has exit requirements, checked when an Issue moves on, rather than requirements checked at creation." and "To leave needs_triage: a reasonable title and description, a priority, labels conforming to the project's scheme" (`bdw show agent-tooling-c86`) [sketch]
- "**No barrier to capture.** ... would refuse a bug filed before anyone knows how to reproduce it, inviting placeholder text." (PROP:258-264) [ratified; supports the sketch's motive]
- "every Issue has at least one area label" and "**Description:** what and why, then a `## Acceptance Criteria` section." (skills/use-bd/SKILL.md:142, :146) [ratified in part; the template is agent-elaborated]
- "Set both [Priority and Status] as part of filing, not later." (skills/use-github/SKILL.md:165) [unknown]
- Affects: R12, R13, R16, R18, R29-R31, and whether filing and triage are one skill's concern or two.

### 4. Does the generic layer adopt the eight-state status model, and what do status, claim, and ready mean on a tracker that lacks them?
- "v1 requires all 8 states." (skills/triage-issues/SKILL.md:63) [unknown]; c86 moves Issues "in the manner of the triage-issues skill's state model" [sketch]
- "`\"p-labels\"` (priority is an issue label, and there is no status beyond open/closed)" (skills/use-github/SKILL.md:94-96) [unknown]
- "Forge issues have no ready queue, no single-owner claims, and one identity for every agent" (ADR 0011:30) [ratified]; Leaf Issue "meant to be claimed and finished in one session" (LEXICON.md:216-217) [ratified]
- Affects: R20, R21, R28-R32. The lexicon's Branch and Leaf terms lean on Beads-native claim and ready.

### 5. Where does an Issue's kind live, and what are the kinds?
- "**Kind goes in the type field** ... never in a label." (skills/use-bd/SKILL.md:140-141) [ratified]
- "**Every issue gets exactly one type label plus one or more `area:` labels.**" (skills/use-github/SKILL.md:120) [unknown]
- "debt -> type chore • meta -> a new custom type meta" (`bdw show agent-tooling-aio.7`) [ratified]; Beads also has `task` and `epic` kinds that the five-kind set lacks
- "`debt` ... Code quality, refactoring, documentation" against "`meta` ... Design documents, planning artifacts, and non-code project work" (skills/setup-github-issues/SKILL.md:180-181) [unknown; overlap on documentation]
- Affects: R16, R17, and whether "epic" is a kind or a Branch Issue property.

### 6. Acceptance criteria or success criteria?
- "To leave needs_scope: success criteria (Branch Issues) or acceptance criteria (Leaf Issues)." (`bdw show agent-tooling-c86`) [sketch]; Branch Issue work includes "setting success criteria" (LEXICON.md:209-211) [ratified]
- "check the Branch Issue's own acceptance criteria against the result" (skills/use-bd/SKILL.md:124) and every description gets "a `## Acceptance Criteria` section" (:146) [agent-elaborated]; triage's scoped body requires "**Acceptance criteria** (required)" (skills/triage-issues/SKILL.md:244) [unknown]
- Affects: R13, R21, R31, R32, and the body template.

### 7. Which Issues may take children?
- "**Parent-child decomposition:** original becomes parent" (skills/triage-issues/SKILL.md:109) [unknown]: any Issue.
- "Only an epic takes children." (skills/use-bd/SKILL.md:127) [agent-narrowed]
- "**Only branch kinds take new children.** ... This is a convenience guard, not a correctness rule" (b90e669, home-in) [ratified]; "Which Issue types count as branch kinds beyond the epic" left open (PROP:401-403, agent-tooling-aio.4) [ratified as open]
- Affects: R20 and triage's split flavors.

### 8. Where does the pick-up note live?
- "the skill should standardize how an issue's notes field is used as a pick-up point ... Decide which field carries which" (`bdw show agent-tooling-aio`, NOTES, 2026-09-25) [ratified ruling, field left open]; agent-tooling-w7p practice rewrites NOTES in place [practice]
- "An Issue's description is its state ... including a `## Pick-up` section ... Notes and comments are its log: append, never rewrite." (skills/use-bd/SKILL.md:196-199) [agent-settled]
- Affects: R33 and R34. Forges have only a body and comments, so on GitHub and Forgejo the description is the only in-place field.

### 9. Ratified rulings missing from the shipped Skill: restore them?
- X4: "Agents reasoning about recency or staleness use the exact UTC instants in the JSON output of bd show and compare against the date command, never the rendered date." (aio note, 2026-09-25) [ratified] versus quirks.md:59 "**Dates in `bd show` are UTC.**" only. "never add a blocks dependency from a parent to its own children, which deadlocks silently (upstream #6506)" (aio note, 2026-09-25) [ratified] versus absent. Heartbeat "prescribe it wherever a claim is held across long work" (aio note, 2026-09-26) [ratified] versus "the intended lease procedure is itself open" (`bdw show agent-tooling-3lo`, 2026-10-24) [later ruling].
- X10: "**No reach outside the project.**" (PROP:265-266), "**Every state change has one owner.**" (PROP:58-59), "**A cold pick-up works.**" (PROP:55-57) [all ratified] versus not taught in skills/use-bd/SKILL.md.
- Affects: R4, R9, R34, R42 (included here on their ratified standing) and the Beads residue (the parent-child blocks rule).

### 10. Do the 2026-09-25 epic rulings still stand?
- "(b) Never claim an epic; it is a container and its work is its children. (c) Close an epic individually once its children are closed" (`bdw show agent-tooling-aio`, NOTES) [ratified 2026-09-25, never marked superseded]
- "each claim on it is one session-sized pass" and "never closed merely because its children closed" (ADR 0009:10, :17) [ratified 2026-10-08; rejects "Branch Issues as passive containers"]
- Affects: R21. I treated ADR 0009 as governing.

### 11. Who may rewrite an Issue's body or definition?
- "Triage changes the surface in place: retitling, rewriting bodies, reopening, labeling, and relinking." (docs/projects/fjw/issue-verbs.md:166-168) [ratified]; "editing in place is expected" (:24-28) [ratified]
- "Trivial body corrections ... may be *proposed* but are **not autonomous.**" and "Forbidden at any autonomy level in this state: changing the issue's actual *definition*" (skills/triage-issues/SKILL.md:193) [unknown]
- Typical ghw grant has "`set-body` withheld" (docs/projects/ghw/design.md:377-380) [unknown]
- The working session rewrites its own Issue's description each session (skills/use-bd/SKILL.md:196-199) [ratified]
- Affects: R15 and R33.

### 12. What must a bug carry before it moves on?
- "for a bug, steps to reproduce" (`bdw show agent-tooling-c86`) [sketch]
- "problem/goal + at least one pointer (code location, repro, observable behavior)" (skills/triage-issues/SKILL.md:186) [unknown]
- Affects: R12 and the intake exit.

### 13. Which sizing model?
- "the item, as its own issue, would be sized M+. XS items rarely worth splitting" (skills/triage-issues/SKILL.md:102) [unknown], with Size set "no later than exit from `Needs Eng Design`" (:189)
- "**One Issue, one session's work.**" (skills/use-bd/SKILL.md:138) [ratified]
- Affects: R20, R23, and whether a Size field exists at all.

### 14. What does "be liberal with Priority" mean, and when is priority set?
- "Be liberal with Priority; be conservative with Status." (skills/use-github/SKILL.md:190) [unknown]
- "open P0 count > cap → flag ... \"P0\" means *drop everything*, which is bounded by human attention" (skills/triage-issues/SKILL.md:426) [unknown]; "Priority assigned at this stage is by definition an *educated guess*" (:188) [unknown]
- c86 makes priority an exit requirement of needs_triage [sketch]
- Affects: R18.

### 15. After initialization, may an agent create or delete labels?
- "any other change to an initialized repo's labels is the signal to stop and ask." (docs/projects/fjw/issue-verbs.md:47-48) [ratified] versus the same doc's tier table allowing `fjw-label-create` at triage tier with no setup condition (:162) [ratified]
- "Show it to the user; on approval:" then `apply-delete` (skills/setup-github-issues/SKILL.md:330-331) [unknown] versus the audit's lean toward "label deletion moved to an ask rule" (docs/audits/2026-10-11-agent-versus-human-line.md:399-406), open as agent-tooling-76b
- Affects: R7.

### 16. Where does context go when the agent does not know its home?
- "One that does not drops it in the repo's Docs Inbox" and "A repo with no docs home keeps such context in the Issue's description." (PROP:302-309) [ratified]
- "If you do not know where it belongs, keep it in the description." (skills/use-bd/SKILL.md:166-167) [agent-elaborated stopgap]
- Affects: R34.

### 17. What does "unattended" mean?
- "use-lexicon treats a session as unattended only if its prompt says \"unattended\"", "the Actor is claude-job-<id> in a background job", "triage's unattended mode is headless" (`bdw show agent-tooling-7kn`) [open]
- Affects: R41 and every "otherwise raise it (unattended: report it)" rule.

### 18. Must an agent's tracker acts be distinguishable from the human's?
- "automation's acts are visibly automation's, never the human user's." (skills/use-forgejo/SKILL.md:19-20) [unknown]
- "v1 runs under the operator's own GitHub account (no dedicated bot identity), so triage's autonomous status-syncs/label-fixes are indistinguishable from genuine manual activity." (skills/triage-issues/SKILL.md:402) [unknown]
- "Should agent acts on a forge be distinguishable from the user's, as fjw decided" (`bdw show agent-tooling-0vm`) [open]
- Affects: R9.

### 19. Do skill-owned Issues (the triage ledger) follow the classification rules?
- "**Every issue gets exactly one type label plus one or more `area:` labels.**" (skills/use-github/SKILL.md:120) [unknown]
- The ledger "is **excluded from triage as a subject** — never itself triaged, sized, or prioritized." (skills/triage-issues/SKILL.md:601) [unknown]; agent-tooling-5kf asks which labels it takes [open]
- Affects: R16 and R18.

### 20. How does a commit name its Issue, and is "lands" different from "touches"?
- Closing keywords versus "contributing language ... `furthers #42`, `part of #42`, `towards #42`" (skills/use-github/SKILL.md:260-263) [unknown]
- "a PR body names the Issue it lands (`Lands agent-tooling-xyz`)" (CLAUDE.md:69-72) [unknown]
- "Does the trailer replace Lands ... / Refs ... / Toward ...?" (`bdw show agent-tooling-nbj`) [open]
- Affects: R39.

### 21. When a backlog moves into the tracker, may setup delete or rewrite the old TODO sources?
- "**TODO.md**: Delete it if all its items are now issues" and "**Notes-vault entry**: Same treatment — replace TODO sections with a GitHub Issues pointer" (skills/setup-github-issues/SKILL.md:400-408) [unknown; audit row S3 "None given"]
- eta's verdicts include "stays upstream" and "done in code (clean up upstream)" [ratified in outline]
- Affects: R19.

## Judgement calls

1. **Provenance tags.** Text from the 2026-09-22 import (setup-github-issues, use-github, triage-issues) is "unknown", never "agent-elaborated", following the readers. Where two of those skills agree I tagged [consistent], though they likely share one predecessor author, so "consistent" there is weaker evidence than agreement between, say, use-bd and fjw.
2. **"Ratified in outline" counts as ratified.** R19 rests on agent-tooling-eta, "ratified in outline ... not final". I tagged it [ratified]; the maintainer may want [consistent].
3. **The c86 lifecycle sketch is kept out of the requirements.** It is explicitly not ratified and conflicts with filing-time rules, so it appears only in Disconnects 3, 4, 6, 12, and 14. R29 keeps only the "what attention next" question, which c86 adopts by reference.
4. **R24 is half of a ratified rule.** The home-in rule also lets agents mark duplication, composition, and contradiction "only when very confident". That half conflicts with triage, so it sits in Disconnect 2 rather than the requirements.
5. **R1 names Beads and forge issues.** That is a tool choice, but it is the ratified ADR 0011 rule, so I kept the names instead of abstracting them away.
6. **Left out of the requirements:** PR-only rules (merge is human-only, non-draft PRs, conflict disclosure), tooling-design principles (enforce in code, wrappers never report false success, version-pinned quirks), skill-family architecture (K90, K91), triage report mechanics (K83), staleness thresholds and inventory rules (K84 apart from timestamps), templated phases (K43a), memories outside the tracker (K88), the sanctioned filing path (K26), and K66 (preserve triage-owned body structure). That last rule is real, but it names GitHub-triage structures. These stay in the catalog.
7. **The moved-not-lost correction.** The claim, discovered-from, and release loop and "A denied call is the policy working" appear in R14, R32, and R5 as ratified current text (skills/use-bd/SKILL.md:36-38, :74-88), not as recovered losses.
8. **The superseded epic rulings (Disconnect 10)** are listed, though ADR 0009 plainly governs, because nothing marks them superseded and agents still read them on agent-tooling-aio and agent-tooling-w7p.
9. [omitted: private source]
10. **I did not re-open repo sources** beyond confirming that skills/use-bd/SKILL.md carries the loop and the denied-call rule (lines 36, 82-88). Quotes come from the extracts.
