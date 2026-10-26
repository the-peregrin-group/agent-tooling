# Extract E: Forgejo issue conventions (fjw / use-forgejo)

> This document captures state as of 2026-10-26. For current state, see [docs/index.md](../../index.md).

Sources read: docs/projects/fjw/issue-verbs.md (dated proposal, "captures state as of 2026-09-14"), docs/projects/fjw/design.md, docs/projects/fjw/index.md (Status), skills/use-forgejo/SKILL.md, Beads agent-tooling-1vr (epic: implement fjw issue and label Verbs), agent-tooling-1vr.1 (live-Forgejo probes, closed), agent-tooling-1vr.5 (use-forgejo tiers/conventions/editorial pass, open, not started).

## Shipped vs planned (read this first)

- **Shipped:** PR Verbs only. fjw index.md Status: "Issue and label Verbs, with PR/issue index guard | planned | issue-verbs.md; `agent-tooling-1vr`". use-forgejo SKILL.md today covers PRs only (frontmatter: "Day-to-day conventions for pull-request operations").
- **Planned, ratified (proposal 2026-09-14), not implemented:** every issue/label principle in issue-verbs.md (E1-E14, E16-E20 below), all five "use-forgejo changes" conventions, the capability tiers, and the grant grammar. They reach the Skill only via agent-tooling-1vr.5 ("Pick-up: Not started").
- **Ratified amendments (maintainer rulings 2026-10-24, on agent-tooling-1vr):** exit codes for the index guard (2/3), unknown labels (3), label-create on existing name (2); "wrappers impose the constraints and UX we want regardless of how the Forgejo API behaves"; grants are per-repo policy, not an fjw recommendation.
- **History note:** issue-verbs.md entered the repo whole in edd9853 (2026-10-01, "docs: migrate the fjw and installer project docs; add ADR 0007"), commit body: "the issue-verbs proposal ratified 2026-09-14". Its earlier drafting history is outside this repo (not traced; the maintainer's knowledge base was off-limits). Diff edd9853..HEAD touches only the opening note, the 404 section's status wording, and removes "Implementation notes"; every principle quoted below is **unchanged** since edd9853. Its "Earliest form" is therefore edd9853 throughout unless stated.

## Principles

### E1: Issues are living documents; PRs are append-only
- Category: lifecycle
- Generic or specific: generic (the edit-in-place stance); specific is only the consequence "`fjw-issue-edit` exists and `fjw-pr-edit` does not".
- Current text: "**Issues are living documents; PRs are append-only submissions.** An issue moves from placeholder to corrected and expanded over its life, so editing in place is expected; reconstructing its current truth from a trail of comments is worse for whoever implements it. A PR is close to done when opened, and changes append." (docs/projects/fjw/issue-verbs.md:24-28). Echoed in design.md:261-265: "a PR is close to done when opened, and changes append as comments. The convention is that a later comment supersedes the description. Issues differ: they are living documents, so the planned issue Verbs include an edit Verb".
- Earliest form: edd9853, 2026-10-01; unchanged.
- Provenance: ratified (proposal header "ratified 2026-09-14"; edd9853 commit body). Planned, not shipped.

### E2: No closed-issue edit guard
- Category: lifecycle
- Generic or specific: generic
- Current text: "**No closed-issue edit guard.** Blocking edits on closed issues is theater, since the issue can be reopened." (issue-verbs.md:30-31)
- Earliest form: edd9853; unchanged.
- Provenance: ratified (proposal). Planned.

### E3: A number of the wrong kind is a call to fix, not an absence (index guard)
- Category: other (relationships between PR and issue namespaces; guard)
- Generic or specific: mixed. Generic: "a caller told there is no item 12 may file a new one, when the fix is to call the sibling Verb" (do not treat a wrong-kind miss as absence and file a duplicate). Specific: Forgejo's shared index space, the HTTP probe order.
- Current text: "**A number of the wrong kind is a call to fix, not an absence.** Forgejo numbers issues and PRs from one index space, so a number can name a real object of the other kind. A Verb given one exits 2, naming the sibling Verb; a number that names nothing exits 3. The two codes ask the caller for different next steps (fix the call, or accept the answer), and the check is what keeps an issue Verb from reaching around a PR Verb's pins." (design.md:37-43). Rationale at design.md:266-273: "Rejected because 3 means \"treat as an answer\", and the answer it invites is wrong: a caller told there is no item 12 may file a new one, when the fix is to call the sibling Verb."
- Earliest form: proposal edd9853 (issue-verbs.md:32-39): "**The PR/issue index guard is load-bearing.** ... Every `fjw-issue-*` Verb checks that its index names a real issue ... but exits 4 where the shipped check exits 3. Without the guard, `fjw-issue-comment` would bypass `fjw-pr-comment`'s head-prefix pin, and `fjw-issue-edit set-body` would silently rewrite a PR description." design.md invariant first in c3f03ac, 2026-10-24, "fjw design: a number of the wrong kind exits 4, not 3". Drift: exit code 4 (proposal) -> 4 (ruling 2026-10-24) -> 2 (ADR 0013 Exit-code contract), per agent-tooling-1vr Rulings; the principle itself is unchanged.
- Provenance: ratified (proposal; maintainer ruling 2026-10-24 on agent-tooling-1vr: "Index guard, aligned across the wrapper families"; ADR 0013 for the code). Known gap: shipped PR Verbs still exit 3 (agent-tooling-1vr.6).

### E4: Schema-free labels; schema prescription belongs to a setup Skill
- Category: setup / labels-priority
- Generic or specific: generic (separation of "apply what exists" from "decide what should exist")
- Current text: "What stays out is schema prescription: deciding which labels should exist, and validating against a canonical schema, belongs to a separate setup Skill." (issue-verbs.md:18-20); "**Schema-free labels.** Label Verbs manage and apply the repo's live registry as it is: no canonical type labels, no area contract, no sync machinery." (issue-verbs.md:40-42)
- Earliest form: edd9853; unchanged.
- Provenance: ratified (proposal). Planned.

### E5: Labels encode the triage schema; changing them is a human decision
- Category: labels-priority / agent-vs-human / setup
- Generic or specific: generic
- Current text: "**Labels encode the project's triage schema; they are not fungible data.** Issues and PRs come and go, but a label changing name or meaning can break process repo-wide. An edit implies a schema version change or a conflicting schema to reconcile, and both want a human. The automated use case is first-time creation while initializing a repo; any other change to an initialized repo's labels is the signal to stop and ask." (issue-verbs.md:43-48)
- Earliest form: edd9853; unchanged.
- Provenance: ratified (proposal). Planned.

### E6: Labeling is table stakes for any tracker surface
- Category: labels-priority
- Generic or specific: generic
- Current text: "Labels are in scope from the start: managing a repo's label registry, and adding or removing labels on both issues and PRs, is table stakes for any issue-tracker-shaped surface." (issue-verbs.md:16-19)
- Earliest form: edd9853; unchanged.
- Provenance: ratified (proposal). Planned.

### E7: Duplicate search before filing covers closed issues too; create is not idempotent
- Category: filing
- Generic or specific: generic
- Current text: "Filters exist because duplicate search before filing and \"was this settled before?\" checks need closed issues, and label filtering is the basic triage read." (issue-verbs.md:64-67); "Deliberately not idempotent, like `ghw-issue-create`; searching for duplicates stays Skill guidance." (issue-verbs.md:81-82); "Create is not idempotent: search open and closed issues before filing." (issue-verbs.md:239); restated as "search open and closed before filing" in agent-tooling-1vr.5 Scope, "Shared conventions".
- Earliest form: edd9853; unchanged.
- Provenance: ratified (proposal). Planned (not in use-forgejo yet).

### E8: Unknown label is a typo to fix, never a label to create
- Category: labels-priority / filing
- Generic or specific: generic (the "never create a label to satisfy a typo" rule); specific (exit code).
- Current text: "Each trailing label must exist in the live registry; unknown labels exit 4, named. That is typo refusal against what exists, not schema prescription." (issue-verbs.md:78-80); "An unknown-label exit 4 means fix the call. Never create a label to satisfy a typo; label edits are human-gated because labels encode the triage schema." (issue-verbs.md:240-242). Ruling: "An unknown label on any label-taking Verb exits 3 (the named label does not exist), named, and is never created. The ruling said 4; under the contract, non-existence is 3." (agent-tooling-1vr Rulings)
- Earliest form: edd9853; drift is exit code only (4 -> 3 via ADR 0013).
- Provenance: ratified (proposal; maintainer ruling 2026-10-24). Planned.

### E9: Classifying your own new issue is part of filing (the accepted leak)
- Category: labels-priority / filing / agent-vs-human
- Generic or specific: generic
- Current text: "**Accepted leak.** A contributor can pass trailing labels to `fjw-issue-create`. ... This is accepted on principle: classifying your own new issue is part of filing it, triage governs changing the surface in place, and mislabeled filings are what triage is for." (issue-verbs.md:171-176)
- Earliest form: edd9853; unchanged.
- Provenance: ratified (proposal). Planned (rendering guidance owned by agent-tooling-1vr.5).

### E10: Comments on issues need no ownership pin; noting progress on human-filed issues is the main use case
- Category: agent-vs-human / lifecycle
- Generic or specific: mixed. Generic: agents comment progress on human-filed issues; comments are append-only, attributed, auditable. Specific: no positional scope token.
- Current text: "Branches give PRs a natural ownership namespace fixed at creation; issues have none. A label pin is mutable by anyone who can add labels, and a creator pin breaks the main use case (noting progress on human-filed issues). Comments are append-only, attributed, and auditable." (issue-verbs.md:85-89)
- Earliest form: edd9853; unchanged.
- Provenance: ratified (proposal). Planned.

### E11: Retitle and body rewrite are separate, separately grantable acts; labels are not edits
- Category: lifecycle / agent-vs-human
- Generic or specific: mixed (generic: one spelling per operation; specific: subverb grammar)
- Current text: "The subverb at position 2 lets a grant pin `retitle` without `set-body`. ... Label changes are not edit subverbs, so each operation has one spelling." (issue-verbs.md:93-95)
- Earliest form: edd9853; unchanged.
- Provenance: ratified (proposal). Planned.

### E12: Edits should be audited mutation, not history destruction
- Category: lifecycle
- Generic or specific: mixed (generic aim; Forgejo-specific finding)
- Current text: "Whether Forgejo records edit history for issue title and body PATCHes, so that `fjw-issue-edit` is audited mutation rather than history destruction." (issue-verbs.md:227-229). Result (agent-tooling-1vr.1 notes, maintainer 2026-10-25): "Forgejo keeps body content history in the web UI, though the API timeline carries no event for a body edit (title edits leave change_title)."
- Earliest form: edd9853; unchanged. Result recorded 2026-10-24/25.
- Provenance: ratified (proposal); probe result maintainer-observed.

### E13: Mandatory close comment, as the audit record, across all trackers; auto-close on merge the one exception
- Category: closing
- Generic or specific: generic
- Current text: "closes with a mandatory comment, matching `fjw-pr-close`: a silent close must be inexpressible, and the comment is the audit record (\"done because X, see commit Y\"). The comment posts first, then the close; an already-closed issue is a no-op success that posts nothing. The mandatory close comment is meant to hold across Wrapper families: `ghw-issue-close` should require one too, with forge automation's auto-close on PR merge as the one sanctioned exception." (issue-verbs.md:96-103); "Close and reopen comments are mandatory; they are the audit record." (issue-verbs.md:238). Shipped PR form: "The comment is mandatory — say *why* it's being closed (typically: link the successor PR)." (skills/use-forgejo/SKILL.md:141-142)
- Earliest form: PR side in cb6f1eb (2026-09-22, "Initial import"); issue/cross-family form edd9853; unchanged. ghw side has since shipped (skills/use-github/SKILL.md:216-219: "The forge's auto-close on PR merge is the one sanctioned comment-less close.").
- Provenance: ratified (proposal). fjw issue side planned; fjw PR side and ghw shipped.

### E14: Reopen is its own act, with a reason, at a higher tier than close
- Category: lifecycle / agent-vs-human
- Generic or specific: generic
- Current text: "reopening is a state change with a reason (\"closed in error\", \"regressed\"), and a separate Verb keeps it separately grantable. Comment mandatory, as for close. It sits in a higher tier than close: an agent that may close its own finished work does not thereby get to resurrect anything." (issue-verbs.md:105-109)
- Earliest form: edd9853; unchanged.
- Provenance: ratified (proposal). Planned.

### E15: Capability tiers: reader / contributor / triage / admin
- Category: agent-vs-human
- Generic or specific: mixed (the tier model and what each tier means are generic; the Verb lists are fjw)
- Current text: table at issue-verbs.md:158-164 (reader allow: reads; contributor allow: create, comment, close; triage allow: edit, reopen, issue-label, pr-label, label-create, later issue-dep; triage ask: label-edit "(labels encode the triage schema)"; admin ask: label-delete "denied below admin, never allowed anywhere"), and "Contributor covers participation: filing, commenting, closing with a comment. Triage changes the surface in place: retitling, rewriting bodies, reopening, labeling, and relinking. `fjw-label-create` sits in triage because first-time creation during repo setup is the automated use case." (issue-verbs.md:166-169). "every Verb must have a disposition" (issue-verbs.md:156).
- Earliest form: edd9853; unchanged. agent-tooling-1vr.5 carries it forward: "every Verb has a disposition; fjw-label-edit and fjw-label-delete are ask; nothing renders fjw-label-delete as allow".
- Provenance: ratified (proposal). Planned (agent-tooling-1vr.5).

### E16: Label deletion: refuse while on open items; proceed (with audit) when only on closed
- Category: labels-priority / closing
- Generic or specific: mixed (generic: don't strip labels off closed issues to enable a delete; specific: scan, counts)
- Current text: "It refuses (exit 4) while the label is on any open issue or PR, reporting the count and example indices; the path forward is the visible two-step of removing it from the open items, then deleting. With attachments only on closed items it proceeds and reports the closed-attachment count in its plan, so the history cost (deletion detaches closed items too) is in the audit record. Blocking there would push agents to the worse workaround of stripping labels off closed issues." (issue-verbs.md:128-135)
- Earliest form: edd9853; unchanged (exit 4 not yet re-mapped by any ruling; see Contradictions).
- Provenance: ratified (proposal). Planned.

### E17: Dependencies deferred; first use case is a flat task list
- Category: relationships
- Generic or specific: mixed
- Current text: "**Issue dependencies** (Forgejo's blocked-by/blocks relation, the counterpart of `ghw-issue-link`'s blocked-by half; Forgejo has no sub-issue hierarchy as of this proposal). Deferred, not rejected, because the first use case is a flat task list." (issue-verbs.md:140-145). 1vr.5 AC: "fjw-issue-dep marked as not yet shipped, or omits it; no living doc presents it as current."
- Earliest form: edd9853; unchanged.
- Provenance: ratified (proposal). Deferred (not even planned in 1vr).

### E18: Missing grant / too-weak grant: report, never retry or work around
- Category: agent-vs-human
- Generic or specific: mixed (generic: refusal is the system working; report to the user. Specific: 404/403 codes)
- Current text (shipped): "**A repo-level exit 3 with a correct slug is a missing grant.** ... Check the slug once; if it is right, report it to the user. Never retry, never hunt for credentials, never push again." (SKILL.md:72-75); "**On exit 2 or 4, fix the call.** Never work around a refusal with raw API calls, `curl`, or `tea` — the refusal is the contract doing its job." (SKILL.md:76-77). Planned: "use-forgejo teaches that exit 4 on a write the grant does not cover (HTTP 403) means report it, never retry or work around it." (agent-tooling-1vr.5). Ruling: "a refusal caused by a too-weak grant is the system working as intended (exit 5, report it)" (agent-tooling-1vr.1 description).
- Earliest form: issue-verbs.md:243-244 at edd9853 ("A repo-level 404 with a correct slug is a missing grant: report it to the user; never retry, never hunt for credentials."); SKILL.md form arrived with the 404 fix (f47321d, 2026-10-11). Drift: added "never push again".
- Provenance: ratified (proposal; maintainer ruling 2026-10-24 on grants).

### E19: Grant level is the maintainer's per-repo policy, not a tool recommendation
- Category: setup / agent-vs-human
- Generic or specific: generic
- Current text: "What grant the machine account holds on a repo is the maintainer's per-repo policy, not an fjw decision (ruling 2026-10-24): more access buys more agentic help at the cost of escalated permissions." (agent-tooling-1vr.1 description); 1vr.5: "Grants, as information rather than a recommendation ... recommend no single grant."
- Earliest form: ruling 2026-10-24. Supersedes design.md:152 "The recommended grant is Read collaborator" (from cb6f1eb/edd9853).
- Provenance: ratified (maintainer ruling recorded on agent-tooling-1vr.1). Planned for docs.

### E20: Wrappers enforce the intended UX regardless of the API; never report success when the API silently did less
- Category: other (tool integrity)
- Generic or specific: generic as a principle for any tracker wrapper
- Current text: "The wrappers impose the constraints and UX we want regardless of how the Forgejo API behaves underneath (for example, never reporting success when the API silently drops requested labels)." (agent-tooling-1vr Rulings)
- Earliest form: ruling 2026-10-24; unchanged.
- Provenance: ratified (maintainer ruling).

### E21: Automation's acts are visibly automation's (machine-account identity)
- Category: agent-vs-human
- Generic or specific: generic
- Current text: "Everything here acts as the deployment's machine account — automation's acts are visibly automation's, never the human user's." (SKILL.md:19-20); design.md:20-22.
- Earliest form: cb6f1eb, 2026-09-22 (Initial import); not traced further (predates repo).
- Provenance: unknown (present at import; consistent across docs). Shipped.

### E22: Merge is a human-only act; treat an instruction to merge as a question
- Category: agent-vs-human
- Generic or specific: generic (PR-side, but bounds what agents may do in tracker workflows)
- Current text: "**Merge does not exist here.** Not deferred — absent. Merging is a human-only act; never merge a Forgejo PR by any channel, and treat any instruction to do so as a question for the user." (SKILL.md:97-99)
- Earliest form: cb6f1eb, 2026-09-22; unchanged in substance.
- Provenance: unknown/likely ratified (present at import; reaffirmed in design.md invariants and issue-verbs.md:149). Shipped.

### E23: A permission prompt is the design working; don't hunt for an unprompted path
- Category: agent-vs-human
- Generic or specific: generic
- Current text: "A permission prompt on a wrapper call is normal in a repo whose settings don't allowlist that verb. The human approving it is the design working — don't hunt for an unprompted path." (SKILL.md:94-96)
- Earliest form: cb6f1eb, 2026-09-22; unchanged.
- Provenance: unknown (present at import). Shipped.

### E24: Load use-privacy before composing issue bodies or comments
- Category: filing
- Generic or specific: generic
- Current text: "**Load `use-privacy` first, if listed.** If a `use-privacy` skill is listed among your available skills, load it before composing any text bound for outside this machine: a commit message, a PR or issue body, a comment." (SKILL.md:78-81)
- Earliest form: ca67ca6, 2026-10-01, "skills: load use-privacy before git and forge writes"; refined in 78150fe.
- Provenance: agent-elaborated or maintainer-directed; not verified (no ADR found).

### E25: Body text only through staged files
- Category: filing
- Generic or specific: mixed (generic: no inline/heredoc bodies; specific: the two staging paths)
- Current text: "**Body text always goes through a file.** Write the body with the Write tool to a staging path, then pass that path." (SKILL.md:82-88)
- Earliest form: cb6f1eb; not traced (largely mechanics).
- Provenance: unknown. Shipped.

### E26: Wrapper and Skill stay consumer-generic; Permission rules carry policy; grant only what is exercised
- Category: setup
- Generic or specific: generic
- Current text: "**Consumer-generic code and Skill.** No consumer's branch names, repos, or hostnames belong in the Wrapper or use-forgejo; Permission rules carry the policy." (design.md:57-59); "Grant only the verbs the consumer exercises." (SKILL.md:172)
- Earliest form: cb6f1eb/edd9853; unchanged.
- Provenance: unknown/ratified with design. Shipped.

### E27: Skill text carries only what an operating agent needs
- Category: docs-linkage
- Generic or specific: generic
- Current text: "After the changes, an editorial pass checks that the whole Skill is coherent, carries only what an operating agent needs (no history, dates, or prior-version residue), and is as concise as clarity allows." (issue-verbs.md:246-248)
- Earliest form: edd9853; unchanged.
- Provenance: ratified (proposal). Planned (1vr.5; AC requires maintainer review of the pass).

## Platform-specific mechanics

- Forgejo keeps PRs and issues in one index space; `GET /issues/{pr#}` returns the PR with non-null `pull_request`; `GET /pulls/{issue#}` 404s (1vr.1 notes).
- `fjw-issue-list` must pass `type=issues`; position 2 is always a state keyword, labels from position 3, ANDed (ruling; issue-verbs.md:58-68).
- `CreateIssueOption.labels` takes IDs only (names 422); `POST/DELETE /issues/{n}/labels` take IDs or names (1vr.1 probe 2).
- Under Read, create-with-labels returns 201 with labels silently dropped (1vr.1); Verbs must not report success (to agent-tooling-1vr.3).
- Duplicate label names are allowed by Forgejo; `fjw-label-create` on an existing name exits 2 pointing to `fjw-label-edit` (ruling).
- Exclusive-scope label collision silently removes the displaced label; exclusive flag support is follow-on agent-tooling-f4d (P4).
- Read collaborator: create issues, comment anywhere, edit/close/reopen only own issues; no labels, no registry, 403 on human-filed issues. Write: everything (1vr.1).
- Under Read the server makes merging impossible; under Write, merge safety rests on branch protection excluding the account (1vr.5).
- Grant grammar: repo pinned at position 1; subverb pinnable at position 2 for issue-edit, issue-label, pr-label, label-edit; label-edit and label-delete render as `ask` (issue-verbs.md:180-192).
- 404 disambiguation is lazy (one `GET /repos/...` only after a resource 404); shipped in agent-tooling-5np.
- Close is comment-then-PATCH (no atomic close); `PARTIAL` on stderr if close fails after the comment.
- `--draft` is the `WIP: ` title prefix; `fjw-pr-comment` head-prefix scope token.

## Contradictions

1. **Exit codes, proposal vs rulings vs shipped Skill.** issue-verbs.md:236: "Index-guard exit 4 means the number names the other kind" and :240 "An unknown-label exit 4" vs agent-tooling-1vr Rulings: wrong kind "exits 2", unknown label "exits 3". The proposal is a dated doc and the epic says the rulings win, so this is expected, but issue-verbs.md:128-129 ("It refuses (exit 4) while the label is on any open issue or PR") has **no** ruling re-mapping it; under ADR 0013 a conflict with existing state would seem to be 2. Unresolved.
2. **Too-weak grant: 4 or 5.** design.md:218: "A 403 that means the grant is too weak for the action is 4." and 1vr.5: "exit 4 on a write the grant does not cover (HTTP 403)"; vs agent-tooling-1vr.1: "(HTTP 403, exit 5)" and "(exit 5, report it)"; vs SKILL.md:70: "`5` roster/auth/config (deployment)" and SKILL.md:68-69 "`4` refused: the call violated a wrapper-enforced policy". Epic explains: "until it lands [agent-tooling-cjvo.3], a too-weak grant exits 5 rather than 4." So the shipped Skill teaches the old seven-code taxonomy (SKILL.md:60-71, including "`6` network failure") while design.md describes the six-code contract (Known gap, agent-tooling-cjvo.3).
3. **Recommended grant.** design.md:152: "The recommended grant is Read collaborator" vs ruling (agent-tooling-1vr.1): "What grant the machine account holds on a repo is the maintainer's per-repo policy, not an fjw decision"; 1vr.5 AC "recommend no single grant". Living doc not yet updated (scheduled for 1vr.5).
4. **Label creation on an initialized repo.** issue-verbs.md:47-48: "any other change to an initialized repo's labels is the signal to stop and ask" vs tier table issue-verbs.md:162 putting `fjw-label-create` at triage **allow**, unconditionally. Rationale (:168-169) covers only setup; the table does not distinguish setup from an initialized repo. Tension, possibly intended to be carried by Skill guidance rather than permission.
5. **Close tier vs "own finished work".** issue-verbs.md:108-109 justifies reopen's higher tier by "an agent that may close its own finished work", but the contributor tier (:161) allows `fjw-issue-close` on any issue; "own" is enforced only by the server grant under Read (1vr.1), which the ruling says is per-repo policy. Under Write, a contributor-tier agent may close human-filed issues.
6. **index.md Status vs issue-verbs.md edit Verb in design.md.** None material; design.md:4-5 and index.md correctly label issue Verbs planned.

## Judgement calls

- Treated every issue-verbs.md principle as "ratified" on the strength of its own header and the edd9853 commit body ("ratified 2026-09-14"); I could not see the ratification record itself (likely in the maintainer's knowledge base, which was off-limits).
- "Earliest form" for issue-verbs.md is edd9853 (the in-repo arrival); pre-migration history is outside this repo and not traced.
- Included PR-side Skill rules (merge human-only, permission prompts, privacy, staged bodies, identity) because they govern what agents may do on the same tracker surface; excluded PR-only mechanics (draft, query, head-prefix) to the mechanics list.
- Marked E21-E23, E25-E26 provenance "unknown": present in the Initial import (cb6f1eb) with no ADR or recorded ruling found.
- Did not read ADR 0013 or ADR 0011 bodies (outside source group); referenced them only as cited by my sources.
