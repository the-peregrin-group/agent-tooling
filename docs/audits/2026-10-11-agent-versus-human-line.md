# Audit: the agent-versus-human line across Skills and Wrappers

> **Audit as of 2026-10-11, against `main` at 39ffb0e.** A dated document:
> it is never updated to describe later state. Line numbers are as of that
> commit. It lands Issue `agent-tooling-xla` (audit the agent-versus-human
> line for one consistent policy); the decisions it asks for are filed as
> their own Issues, linked `discovered-from` that one.

Each Skill and Wrapper drew its own line between what an agent may do on
its own and what needs a human, in whichever document was being written at
the time. This audit inventories every such decision point, names the
principles they rest on, lists where they disagree, and asks the
maintainer one question per disagreement. It proposes no edits: the
answers are the maintainer's, those that pass the ADR gate become ADRs,
and the resulting edits become their own Issues.

**Scope read:** every `SKILL.md` under `skills/` (11) and the files
bundled with them; every executable under `cli/` (28: `bdw`, 7 `fjw-*`,
12 `ghw-*`, 7 `gitw-*`, `tooling-install`) and `cli/lib/actor.py`; the six
`triage-*` reference wrappers and `skills/triage-issues/reference/DEPLOYMENT.md`
(the only DEPLOYMENT doc in the tree); the Permission rule spec
`cli/repo_policy_test.py` against `.claude/settings.json`; the README's
minimum rules; `CLAUDE.md`; `.beads/PRIME.md`; the living `design.md` files
that state the rules' reasons; and every ADR (0001 to 0010). ADRs 0004
(home-in is attended-only), 0008 (a bare `/` prefix means no branch
constraint), 0009 (Branch Issues are worked in passes) and 0010 (bdw
carries Beads policy in tiers) bear on the line; the rest do not draw it.

## The principles

Named here so the inventory can mark each row. A principle is listed only
if at least two independent passages state or plainly rest on it.

| Principle | Statement | Stated at |
|---|---|---|
| **Trunk** | Trunk, or a branch the project protects, advances only with a human in the loop. An agent integration branch the project designates may advance unattended. | `skills/use-git/SKILL.md:358-366`; `docs/projects/gitw/design.md:86-94`; `CLAUDE.md:71-80` |
| **Exact ref** | A grant to move a ref names that ref exactly; a grant for an act that only reads a ref may be starred. (The principle that settled the `gitw-rebase ... onto <base>` review.) | `skills/use-git/SKILL.md:404-421`; `docs/projects/gitw/design.md:521-532` |
| **Merge** | Merging a pull request is a human act. | `skills/use-forgejo/SKILL.md:12,89-91`; `docs/projects/fjw/design.md:23`; `docs/projects/ghw/design.md:73-76` |
| **Indistinct actor** | The recorded identity cannot tell a sub-agent from its session (nor one attended session of a user from another), so acts that assert ownership stay with the session holding the conversation, and identity comes only from the environment. | `skills/use-bd/SKILL.md:59-75`; `cli/bdw:1-12`; ADR 0002 (Beads identity) |
| **Setup** | Configuring the machine or a deployment (the roster, installs, credentials, tracker init and config, bootstrap artifacts) is a human act; an agent may draft it. | `cli/gitw-repo-register:4-5,26-28`; `cli/tooling-install:7-10`; `skills/use-bd/onboarding.md:5-9`; `skills/triage-issues/SKILL.md:628` |
| **Irreversible** | An act that loses information irrecoverably needs a human, or is left out of the surface. | `skills/use-git/SKILL.md:266-267`; `cli/ghw-board-sync:10-13`; `cli/repo_policy_test.py:157-159`; `docs/projects/beads-trial/design.md:60-70` |
| **Ratify** | Meaning (vocabulary, decisions, scope, design, priority) is ratified by the user; an agent proposes. | `skills/use-lexicon/SKILL.md:26-32`; `skills/use-adrs/SKILL.md:44`; `skills/triage-issues/SKILL.md:75,166,343`; ADR 0004 |
| **Degrade** | With no one to ask, take the conservative branch, leave a reviewable artifact, and report it. | `skills/handoff/SKILL.md:42-43,128-130`; `skills/refine-state-doc/SKILL.md:158-162`; `skills/use-adrs/SKILL.md:45-47`; `skills/use-git/SKILL.md:126-127,353-357` |
| **Rule is the gate** | The human gate is a Permission rule: the prompt is the ceremony, a refusal is never routed around, and the permission boundary is the autonomy boundary. | `skills/use-git/SKILL.md:85-87`; `skills/use-forgejo/SKILL.md:86-88`; `skills/triage-issues/SKILL.md:595,617-620`; `docs/projects/installer/design.md:165-168`; LEXICON.md "Permission rule" |
| **Not yours** | Do not take over work another agent or a human may hold. | `skills/use-git/SKILL.md:132-166,205-209`; `cli/gitw-push:256-262`; `skills/use-bd/SKILL.md:72-75`; `cli/repo_policy_test.py:83-87` |
| **Stays local** | Secrets, local-only files and tracker data do not leave the machine; outward text passes through a visible, staged file. | `skills/use-forgejo/SKILL.md:46-52`; `cli/gitw-commit:20-24`; `docs/projects/ghw/design.md:61-71`; ADR 0001 (Beads trial) |
| **Bounded autonomy** | An unattended write path emits only bounded, enumerable values, or free text confined to one owned target. | `skills/triage-issues/SKILL.md:505,622`; `skills/triage-issues/reference/DEPLOYMENT.md:28-38` |
| **Raw override** | A Wrapper has no override path; overriding its check is a human at the prompt using the raw tool. | `cli/ghw-pr-merge:9-11`; `skills/use-github/SKILL.md:270-272`; `cli/ghw-issue-link:128-134` |

## Inventory

One row per decision point. "Restricts" says who may do what: an agent on
its own, only with a human's approval (ask), or never. "Principle" is
"none" when the passage gives no reason that ties to a principle above.

### use-git and the gitw Wrappers

| # | Where | Restricts | Reason given | Principle |
|---|---|---|---|---|
| G1 | `skills/use-git/SKILL.md:358-366`; `docs/projects/gitw/design.md:86-94` | Integrating into trunk or a protected branch: attended, always. Into a designated agent integration branch: may be unattended. Project silent: push-and-PR is the unattended ceiling. | Trunk advances only with a human in the loop. | Trunk |
| G2 | `cli/gitw-integrate:4-6`; `skills/use-git/SKILL.md:314-316,429-431` | `gitw-integrate` is granted per repo and per base, only where direct integration is sanctioned. | The allowlist carries the policy; the Wrapper the machine-checkable part. | Trunk; Rule is the gate |
| G3 | `docs/projects/gitw/design.md:96-99` | Nothing in code distinguishes attended from unattended; `gitw-integrate` is gated only by the grant. | Enforcement beyond the grant belongs to a future capability system. | Rule is the gate |
| G4 | `skills/use-git/SKILL.md:348-357`; `docs/projects/gitw/design.md:101-109`; `cli/gitw-rebase:47-49` | An agent rebases its own branch unattended, conflicts included; discloses every resolved file; aborts when not confident. | A rebase cannot reach trunk; the risk is unreviewed resolutions, which disclosure addresses. | Degrade |
| G5 | `skills/use-git/SKILL.md:266-267`; `cli/gitw-rebase:43-45` | No `skip`: dropping a commit is never an agent act. | Silently dropping a commit is a human decision. | Irreversible |
| G6 | `skills/use-git/SKILL.md:404-421`; `docs/projects/gitw/design.md:521-532` | Rebase rows may be starred (any base); `gitw-push` rows never are; the landing Verb's base is pinned exactly. | A rebase rewrites only the agent's own branch; the pin belongs on the ref being written. | Exact ref |
| G7 | `skills/use-git/SKILL.md:126-127` (`gitw-orient` exit 3) | Unregistered repo: attended, propose the registration plan; unattended, stop and flag. | Registration is the human's ceremony. | Setup; Degrade |
| G8 | `skills/use-git/SKILL.md:339-345,431-432`; `cli/gitw-repo-register:4-5,26-28`; `docs/projects/gitw/design.md:540-541`; `README.md:97,103-104` | `gitw-repo-register`: every invocation ask-ruled, never allowed; removals and `operable_from` edits are the user's hand edits. | Registration can never go silent; `ask` outranks `allow`. | Setup; Rule is the gate |
| G9 | `skills/use-git/SKILL.md:132-153` | A working copy is never presumed the agent's; mode (c), work on the default branch, needs the user's explicit assurance of no parallel agents. | No process list can see the agent a human is about to start. | Not yours |
| G10 | `skills/use-git/SKILL.md:163-166`; `docs/projects/gitw/design.md:114-117` | Changes to untracked `settings.local.json`: attended-only, with a competing-work check and an explicit go-ahead. | Clobbering it is invisible to git. | Not yours |
| G11 | `skills/use-git/SKILL.md:205-209`; `cli/gitw-branch-start:12-16` | `resume` refuses a branch checked out in another worktree; the agent stops and tells the user. | Another agent may be live on it. | Not yours |
| G12 | `cli/gitw-push:256-262`; `skills/use-git/SKILL.md:284-289` | A lease failure refuses; fetch and reconcile, never blind-retry. | Another agent or the human may have moved the ref. | Not yours |
| G13 | `cli/gitw-commit:20-24`; `skills/use-git/SKILL.md:247-251` | The sweep guard refuses `settings.local.json` and `.env*`; beyond the gitignore or pathspec fix, "it's the user's call". | Local-only files. | Stays local |
| G14 | `skills/use-git/SKILL.md:42-46,387-389` | `git mv` / `git rm` grantable per repo, path-narrowed; shell `rm`/`mv` never allowlisted; remote branch deletion and tags absent. | Git fences both to tracked paths; the rest await a consumer. | Irreversible |
| G15 | `skills/use-git/SKILL.md:234-236`; ADR 0008 | Whether the bare `/` prefix is granted is the repo's policy, not the agent's choice. | A prompt on it is the policy asking. | Rule is the gate |
| G16 | `skills/use-git/SKILL.md:368-377` | A cross-repo write needs two independently maintained artifacts to agree: the anchoring repo's grant and the roster's `operable_from`. | No ambient reach into checkouts on disk. | Rule is the gate |
| G17 | `skills/use-git/SKILL.md:61-73,85-87` | Exit 4 is never retried unchanged nor worked around with raw git; a prompt is the design working. | The refusal is the contract doing its job. | Rule is the gate |

### use-github and the ghw Wrappers

| # | Where | Restricts | Reason given | Principle |
|---|---|---|---|---|
| H1 | `skills/use-github/SKILL.md:262-272`; `cli/ghw-pr-merge:4-11` | Merge only when the user has said to; no override; merging over red checks is a human with raw `gh`. | Many repos have no branch protection, so the Wrapper's checks are the only ones. | Merge; Raw override |
| H2 | `docs/projects/ghw/design.md:73-76` | `ghw-pr-merge` is never granted to unattended agents absent project rules that say otherwise. | Merging is a human act. | Merge |
| H3 | `CLAUDE.md:71-80` | Agents may merge PRs into the run's `integrate/` branch unattended with `ghw-pr-merge`; the exact branch is pinned by the maintainer's local rules; `main` is human-only. | Agent integration branches are per run and disposable. | Trunk; Exact ref |
| H4 | `docs/projects/ghw/design.md:46-52` (`ghw-orient` included) | No ghw rule at user level, reads included; grants live per repo. | A user-level grant is repo-unpinned exposure. | Rule is the gate |
| H5 | `cli/ghw-issue-close:4-6`; `skills/use-github/SKILL.md:210-214` | Closing an issue is its own Verb, independently grantable; when granted, an agent closes with a reason. | Closing should be grantable or withheld on its own. | Rule is the gate |
| H6 | `cli/ghw-issue-edit:4-5` | `set-body` can be withheld while label edits are granted. | Subverb position makes the split grantable. | Rule is the gate; Bounded autonomy |
| H7 | `cli/ghw-board-set:4-5`; `skills/use-github/SKILL.md:186-189` | Priority grantable without Status; Status transitions belong to triage. | Field position makes the split grantable. | Ratify |
| H8 | `cli/ghw-board-sync:10-13,124-127`; `skills/setup-github-issues/SKILL.md:78-82` | Drift on live board fields is reported, never edited; a second board is never created. | Replacing a live option orphans values: "a human decision"; a second board is "a deliberate act for a human". | Irreversible; Setup |
| H9 | `cli/ghw-label-sync:11-21`; `skills/setup-github-issues/SKILL.md:326-334` | Label deletion is granted by allowlisting the `apply-delete` mode; the Skill shows the plan and waits for approval. | `plan` is where a human decides whether to grant deletion. | Irreversible; Rule is the gate |
| H10 | `cli/ghw-issue-link:128-134` | When existing edges cannot be verified, the Wrapper refuses; a human runs raw `gh` at the prompt. | Refusing to guess. | Raw override |
| H11 | `skills/use-github/SKILL.md:280-285` | An unattended triage run writes only through the `triage-*` wrappers. | Deliberately the only unattended write path. | Bounded autonomy |
| H12 | `cli/ghw-pr-create:9-10`; `cli/fjw-pr-create:7-8`; `skills/use-github/SKILL.md:249-251` | `--draft` is the one trailing flag; PRs stay non-draft unless the user asks. | A de-escalation is safe in trailing position. | Rule is the gate |

### use-forgejo and the fjw Wrappers

| # | Where | Restricts | Reason given | Principle |
|---|---|---|---|---|
| F1 | `skills/use-forgejo/SKILL.md:12,89-91,157-158`; `cli/fjw-pr-close:11-12`; `docs/projects/fjw/design.md:23` | Merge is absent; never merge a Forgejo PR by any channel; an instruction to merge is a question for the user. | Merging is a human-only act. | Merge |
| F2 | `cli/fjw-pr-close:4-5`; `docs/projects/fjw/design.md:76-77` | An agent may close a PR, only with a comment. | A silent unattended close must not be expressible. | Degrade |
| F3 | `skills/use-forgejo/SKILL.md:46-52`; `README.md:96,103` | Never read, write, or work around the fjw config; on auth failure, report. | Token rotation is the deployment's job; deny rules keep the token out of reach. | Stays local; Setup |
| F4 | `cli/fjw-pr-create:4-5`; `skills/use-forgejo/SKILL.md:18-20`; `docs/projects/fjw/design.md:15-21` | Every fjw write acts as the deployment's machine account, never the human user. | Automation's acts are visibly automation's. | none |
| F5 | `cli/fjw-pr-comment:4-8`; `skills/use-forgejo/SKILL.md:136-143` | Commenting is scoped by a head-prefix token that rules pin. | Scope is a rule's to grant; the Wrapper verifies it. | Rule is the gate |

### use-bd, bdw, and the Beads Permission rules

| # | Where | Restricts | Reason given | Principle |
|---|---|---|---|---|
| B1 | `skills/use-bd/SKILL.md:59-66` | A sub-agent or workflow agent reads, files, and appends; it never claims, closes, or rewrites. | Its environment cannot be told from its parent's. | Indistinct actor |
| B2 | `skills/use-bd/SKILL.md:68-75` | A successful claim does not prove ownership; stop and ask; never pass `--actor`; never take over a claim. | Attended sessions of one user share an Actor. | Indistinct actor; Not yours |
| B3 | `skills/use-bd/SKILL.md:54-57` | Every claim is closed or released before the session ends. | A claim never outlives its session. | Not yours |
| B4 | `skills/use-bd/SKILL.md:117-124` | Duplication, composition and contradiction links only when very confident; otherwise ask (unattended: report). | None given. | none |
| B5 | `skills/use-bd/SKILL.md:167-185`; `skills/use-bd/quirks.md:27-28`; `cli/repo_policy_test.py:180-183,285-287`; `docs/projects/beads-trial/design.md:83-84` | Work waiting on a human is gated; `gate resolve` has no rule so it prompts; `human respond` is ask-ruled; never close through it. | Resolving a human gate is the human's act; a review never closes that way. | Rule is the gate |
| B6 | `skills/use-bd/SKILL.md:193-194` | Offer an upstream report or fix; never do it unasked. | None given beyond the offer. | Stays local |
| B7 | `cli/repo_policy_test.py:29-37,132-141` | Raw `bd` and `beads` denied, reads included, and `bdw` by install path. | The habit of typing `bd` fails at once. | Indistinct actor; Rule is the gate |
| B8 | `cli/repo_policy_test.py:39-100`; `docs/projects/beads-trial/design.md:60-71` | Denied outright: forgetting and destructive Verbs (`delete`, `purge`, `compact`, `gc`, `prune`), sync and tracker integrations, `init`, `migrate`, `upgrade`, and alias spellings. | Forgetting buys nothing; nothing leaves the machine; one spelling per operation. | Irreversible; Stays local; Setup |
| B9 | `cli/repo_policy_test.py:83-87`; `docs/projects/beads-trial/design.md:72-74` | `reclaim` denied, not asked for. | It would take live work from sessions waiting on a human (the user's ruling of 2026-09-25). | Not yours |
| B10 | `cli/repo_policy_test.py:103-109` | `ready --claim`, `close --claim-next`, `close --continue` denied. | They claim around the choice of work. | none |
| B11 | `cli/repo_policy_test.py:56-58`; ADR 0009 | `epic close-eligible` denied. | It skips the Branch Issue's verifying pass. | none |
| B12 | `cli/repo_policy_test.py:127-130`; `cli/bdw:9-12`; ADR 0002 | `--actor` denied in any position and refused by `bdw`. | Identity comes from the environment, never the caller. | Indistinct actor |
| B13 | `cli/repo_policy_test.py:157-201` | Ask-ruled: flags that delete, override another Actor's claim, close on the agent's behalf, write files, or send data off; config and backup changes. | "Human gate on top of an allow". | Irreversible; Not yours; Setup; Stays local |
| B14 | `cli/repo_policy_test.py:143-155` | Shell indirections (`exec`, `env`, `sh -c`, `xargs`, `eval`, ...) ask-ruled. | They hide a Verb from prefix matching; an ask holds in auto mode, where only ask and deny rows do. | Rule is the gate |
| B15 | `CLAUDE.md:61-64`; `docs/projects/beads-trial/index.md:55` | The Beads rules are not safe in auto mode until the parsed-command deny hook lands. | Prefix rules cannot see a Verb inside a nested shell string. | Rule is the gate |
| B16 | `skills/use-bd/onboarding.md:5-9` | Onboarding a repo to Beads is a maintainer procedure; a human runs or approves each step; an agent may draft. | `init` and every `dolt` subcommand are denied to agents. | Setup |
| B17 | `.claude/settings.json:123-124` | Shell `rm` and `mv` ask-ruled (commit 264ecfd). | The commit subject: to keep auto mode from running wild. Absent from the spec. | Irreversible |

### tooling-install

| # | Where | Restricts | Reason given | Principle |
|---|---|---|---|---|
| T1 | `cli/tooling-install:7-10,42-46`; `docs/projects/installer/design.md:165-172`; `README.md:98-99,103-104` | `apply` and `adopt` are explicit ask rules, not merely unlisted; `diff` is allowlistable; `adopt` is its own Verb so it can be granted differently. | `ask` outranks `allow`, so a later broad allow cannot swallow them; the prompt is the ceremony. | Setup; Rule is the gate |
| T2 | `docs/projects/installer/design.md:131-133` | Concurrent installs are unguarded. | An install is a human act behind a prompt. | Setup |
| T3 | `docs/projects/installer/design.md:173-176`; `CLAUDE.md:8-11` | Edit denied on every Install Target; installed copies are never edited. | A change reaches installed tooling only through a committed source and an approved install. | Setup |

### triage-issues and its reference wrappers

The six reference wrappers (`triage-inventory`, `triage-timeline`,
`triage-apply-sync`, `triage-fix-label`, `triage-bump-triaged`,
`triage-update-ledger`) carry their decision points through rows R10 and R13.

| # | Where | Restricts | Reason given | Principle |
|---|---|---|---|---|
| R1 | `skills/triage-issues/SKILL.md:52-56` | `Needs Triage` fully agent-autonomous; `Needs Scope` and `Needs Eng Design` agent with a human in the loop. | The split is explicit per state. | Bounded autonomy; Ratify |
| R2 | `skills/triage-issues/SKILL.md:75` | Backward status moves: triage proposes, a human approves. | None given. | Ratify |
| R3 | `skills/triage-issues/SKILL.md:132` | Grouping never auto-acts; reparenting, tracker creation and closing await a human. | None given. | Ratify |
| R4 | `skills/triage-issues/SKILL.md:166` | ADR creation never autonomous. | The human decides whether to create one. | Ratify |
| R5 | `skills/triage-issues/SKILL.md:193` | Typo and link fixes in bodies are proposed, never applied. | It needs a free-text write to an arbitrary issue. | Bounded autonomy |
| R6 | `skills/triage-issues/SKILL.md:197-198` | Moves to `Done` or `Rejected` need a human's OK. | None given. | Ratify |
| R7 | `skills/triage-issues/SKILL.md:343` | PM-axis findings (priority, staleness, duplicates) never auto-act; surfaced in batches. | None given. | Ratify |
| R8 | `skills/triage-issues/SKILL.md:505` | Autonomous only: status syncs, schema label fixes, `Last Triaged`; everything else, closes included, is proposed. | All bounded, enumerable field writes. | Bounded autonomy |
| R9 | `skills/triage-issues/SKILL.md:593-595` | Unattended runs accumulate proposals, never resolve them; a denial is terminal for the pass, with no alternate path. | The dangerous direction stalls, the safe one flows. | Degrade; Rule is the gate |
| R10 | `skills/triage-issues/SKILL.md:617-622`; `skills/triage-issues/reference/DEPLOYMENT.md:14-44` | The allowlist is wrapper names only; proposed mutations have no wrapper; each write wrapper re-derives its own precondition. | The permission boundary and the autonomy boundary are the same line. | Bounded autonomy; Rule is the gate |
| R11 | `skills/triage-issues/SKILL.md:628`; `skills/triage-issues/reference/DEPLOYMENT.md:211-222` | Bootstrap (ledger issue, profile commit) is interactive, never autonomous. | A durable artifact and a committed file are outside the autonomous set. | Setup |
| R12 | `skills/triage-issues/SKILL.md:632`; `skills/triage-issues/reference/DEPLOYMENT.md:101-105` | Do not host unattended triage in a repo whose settings grant ghw write Verbs. | It opens a write path outside the triage wrappers. | Rule is the gate |
| R13 | `skills/triage-issues/reference/DEPLOYMENT.md:55-78`; `README.md:117-121` | The triage wrappers are allowed at user level, by install path through `python3`; no `gh` rule ever. | The allowlist is project-agnostic because the profile holds every id. | Rule is the gate |
| R14 | `skills/triage-issues/reference/DEPLOYMENT.md:82-99` | Unattended runs must be deny-by-default; never `bypassPermissions`. | Under bypass a stray proposed mutation would execute. | Rule is the gate |
| R15 | `skills/triage-issues/SKILL.md:402` | Triage's writes run under the operator's own GitHub account. | v1 has no bot identity. | none |

### setup-github-issues

| # | Where | Restricts | Reason given | Principle |
|---|---|---|---|---|
| S1 | `skills/setup-github-issues/SKILL.md:41-44` | Confirm the target repo with the user. | None given. | Setup |
| S2 | `skills/setup-github-issues/SKILL.md:284-287` | Wait for explicit approval of the whole plan before executing. | The user may adjust it. | Setup; Ratify |
| S3 | `skills/setup-github-issues/SKILL.md:396` | An agent deletes `TODO.md` with `git rm` once every item is an issue. | None given. | Irreversible |

### home-in, use-lexicon, use-adrs

| # | Where | Restricts | Reason given | Principle |
|---|---|---|---|---|
| U1 | `skills/home-in/SKILL.md:11,30-35`; ADR 0004 | Attended only; unattended, say so and stop. Not enforced. | An interrogation with no one to answer is the agent's opinion dressed as the user's. | Ratify |
| U2 | `skills/use-lexicon/SKILL.md:26-32` | The user ratifies every lexicon change except mechanical ones. | None beyond the list of mechanical changes. | Ratify |
| U3 | `skills/use-lexicon/SKILL.md:33-35`; `skills/use-lexicon/writing-lexicon.md:244-247` | A session is unattended only if its prompt says "unattended"; unattended, never edit `LEXICON.md`, write a proposal file; never file a tracker issue for a proposal. | None given. | Ratify; Degrade |
| U4 | `skills/use-lexicon/writing-lexicon.md:367-385` | Lexicon versus code conflict: attended, the user rules; unattended, propose, or fix code within scope. | None given. | Ratify; Degrade |
| U5 | `skills/use-adrs/SKILL.md:43-47` | Never create an ADR unasked; unattended, a gate-passing decision gets a draft ADR in the same change, and the review is the ratification. | None given. | Ratify; Degrade |
| U6 | `skills/use-adrs/SKILL.md:69-72`; `skills/use-adrs/writing-adrs.md:101-107,129-132` | Capture fixes need the user, so attended only; a true-up unattended edits nothing and is reported. | The user ratifies every capture fix except objective ones. | Ratify; Degrade |

### handoff and refine-state-doc

| # | Where | Restricts | Reason given | Principle |
|---|---|---|---|---|
| D1 | `skills/handoff/SKILL.md:42-43` | Recipient unclear: ask; unattended, pick the likeliest and say so. | None given. | Degrade |
| D2 | `skills/handoff/SKILL.md:128-130` | Offer a handoff, never write one unasked; unattended, write it and give its path. | No one would see the offer. | Degrade |
| D3 | `skills/refine-state-doc/SKILL.md:158-162` | A badly fudged TODO list: attended, raise it; unattended, leave it untouched and report. | None given. | Degrade |

### No agent-versus-human decision point

These Wrappers draw no line of their own beyond the shared rule that a
prompt is the design working (`skills/use-github/SKILL.md:58-60`,
`skills/use-forgejo/SKILL.md:86-88`): `ghw-issue-create`,
`ghw-issue-comment`, `ghw-pr-comment`, `fjw-pr-list`, `fjw-pr-view`,
`fjw-pr-comments`, `fjw-pr-query`. Every Skill appears above.

## Inconsistencies, and a question for each

Each item names the passages on both sides and asks which side should
give. "ADR gate" says whether the decision would likely pass the three-part
gate in `skills/use-adrs/SKILL.md` (several real options, costly to
reverse, surprising without context).

### 1. Is merging the human act, or is advancing a protected base?

- **Merging is human, full stop:** use-forgejo never merges "by any
  channel" (`skills/use-forgejo/SKILL.md:89-91`); fjw has no merge Verb and
  "never will" (`cli/fjw-pr-close:11-12`, `docs/projects/fjw/design.md:23`).
- **Merging is grantable:** `ghw-pr-merge` exists, merges "only when the
  user has said to" (`skills/use-github/SKILL.md:262`), and the ghw design
  lets project rules grant it to unattended agents
  (`docs/projects/ghw/design.md:73-76`). This repo does exactly that for its
  `integrate/` branches (`CLAUDE.md:71-80`), and use-git names "the forge
  merge the project names" as a way to land on an agent integration branch
  (`skills/use-git/SKILL.md:362-365`).
- The Trunk principle would explain the GitHub side: what needs a human is
  the base, not the act. Under it, the Forgejo ban is stricter than the
  policy, and a Forgejo-hosted project could not run an integration-branch
  workflow through the forge.

**Question:** Is the line "merging is a human act" (then the `integrate/`
merge grant is an exception to record), or "a protected base advances only
with a human" (then fjw's permanent absence of merge, and its stated
reason, should be restated as a choice about Forgejo's bases)?
**ADR gate:** likely passes: both options are real, it decides whether a
Verb exists, and the current text surprises a reader who meets both Skills.

### 2. Is closing an Issue or a PR an agent act?

- **Agent act:** `ghw-issue-close` closes on a grant
  (`cli/ghw-issue-close:4-6`, `skills/use-github/SKILL.md:210-214`);
  `fjw-pr-close` lets an agent close a PR with a comment
  (`cli/fjw-pr-close:4-5`); `bdw close` is allowed to sessions
  (`.claude/settings.json:175`, `skills/use-bd/SKILL.md:52`).
- **Human-confirmed:** triage proposes every close and waits for a human
  (`skills/triage-issues/SKILL.md:132,197-198,505`), interactive passes
  included, and gives no reason beyond the bounded-autonomy rule that
  governs its unattended passes.
- Sub-agents may not close Beads Issues (`skills/use-bd/SKILL.md:59-66`)
  but nothing stops them closing a GitHub issue or a Forgejo PR.

**Question:** Is a close an ordinary reversible act that needs only a
reason, with triage's restriction scoped to its unattended passes, or a
judgement the human confirms everywhere, in which case use-github and
fjw should say when an agent may close?
**ADR gate:** probably not: cheap to change in text.

### 3. Three definitions of "unattended"

- **The prompt says so:** "A session is unattended only if its prompt says
  'unattended'; otherwise it is attended" (`skills/use-lexicon/SKILL.md:33-34`).
- **A background job:** the Actor is `claude-job-<id>` in a background job
  and `attended-<user>` otherwise (`cli/lib/actor.py:3-15`, `cli/bdw:5-6`,
  `cli/gitw-commit:30-32`), so the audit trail labels every
  non-job session attended.
- **No dialogue possible:** triage's unattended mode is "headless, e.g. a
  scheduled background job" (`skills/triage-issues/SKILL.md:589,593`).
- use-git, use-adrs, use-bd, handoff and refine-state-doc branch on the
  word without defining it; LEXICON.md has no entry; and the gitw design
  notes that neither code nor Permission rules can tell the two apart
  (`docs/projects/gitw/design.md:96-99,639-640`).
- A background job whose prompt does not say "unattended" is attended to
  use-lexicon and a job to the Actor; a session the user has walked away
  from is attended to both.

**Question:** Which definition governs, and should "Attended" and
"Unattended" become lexicon terms that every Skill uses, with the Actor's
`attended-` prefix renamed if it no longer matches?
**ADR gate:** likely a lexicon decision rather than an ADR; it passes the
gate only if the answer changes the Actor format.

### 4. Does a reviewed change ratify?

- **Yes, for ADRs:** unattended, a gate-passing decision gets a draft ADR in
  the same change and "the review is the ratification"
  (`skills/use-adrs/SKILL.md:45-47`).
- **No, for the lexicon:** unattended, never edit `LEXICON.md`; write a
  proposal file instead (`skills/use-lexicon/SKILL.md:34-35`,
  `skills/use-lexicon/writing-lexicon.md:246`).
- **No, for ADR capture fixes:** they need the user, so attended only, and
  a true-up unattended edits nothing (`skills/use-adrs/writing-adrs.md:105-107,129-132`).
- All three reach `main` only through a PR a human reviews, so the same
  review is trusted to ratify a new decision but not a new term or a
  wording fix to an old decision.

**Question:** Is PR review a ratification? If yes, an unattended agent may
edit `LEXICON.md` and make capture fixes in a reviewed change; if no, an
unattended draft ADR should be a proposal outside `docs/adr/` like a
lexicon proposal.
**ADR gate:** likely passes: two Skills' procedures turn on it, and it is
surprising that the riskier artifact gets the looser rule.

### 5. Human gates that rely on an absent rule

- **The stated mechanism is an explicit rule:** installs are explicit
  `ask` rules, "not merely unlisted", because `ask` outranks `allow`
  (`docs/projects/installer/design.md:165-168`); the spec notes that in
  auto mode only ask and deny rows hold (`cli/repo_policy_test.py:143-146`);
  the triage boundary holds only under deny-by-default
  (`skills/triage-issues/reference/DEPLOYMENT.md:89-99`).
- **Gates that are only an absent rule or Skill text:**
  - `gate resolve` is "the human's act" because it has no rule, so it
    prompts (`cli/repo_policy_test.py:285-287`,
    `docs/projects/beads-trial/design.md:83-84`), which is not true in
    auto mode, while its sibling `human respond` is an explicit ask
    (`cli/repo_policy_test.py:180-182`).
  - `ghw-pr-merge` is "never granted to unattended agents"
    (`docs/projects/ghw/design.md:73-74`), but a grant cannot tell attended
    from unattended (`docs/projects/gitw/design.md:639-640`); outside a
    grant, "only when the user has said to" is Skill text
    (`skills/use-github/SKILL.md:262`).
  - Integrating into trunk is "attended, always"
    (`skills/use-git/SKILL.md:358-360`), but `gitw-integrate` is gated only
    by whether a rule grants it (`docs/projects/gitw/design.md:96-99`); no
    shipped or minimum rule asks on it.
- Related: the parsed-command deny hook (Issue
  `agent-tooling-1790288522490-13-6d52b051`) addresses what prefix rules
  cannot match, not this.

**Question:** Should every act a Skill calls human-only carry an explicit
`ask` or `deny` row in the rules this repo ships or recommends (the
README minimum, the Beads spec), so the gate survives auto mode and a
later broad allow; and if so, which acts: `gate resolve`, trunk
`gitw-integrate`, `ghw-pr-merge` outside designated bases?
**ADR gate:** passes: it fixes how the whole policy layer expresses a
human gate.

### 6. The policy spec and the settings file disagree

- `CLAUDE.md:61-63` says `.claude/settings.json` is generated from
  `cli/repo_policy_test.py` and the test confirms they agree; the spec
  calls itself "this repo's permission rules for Beads"
  (`cli/repo_policy_test.py:1-10`).
- Commit 264ecfd added `Bash(rm *)` and `Bash(mv *)` to the `ask` list
  (`.claude/settings.json:123-124`) without touching the spec, out of sort
  order. On `main`, `test_ask_is_exactly_the_listed_set` and
  `test_every_list_is_sorted_so_membership_is_checkable_by_eye` fail.
- These rows are not Beads rules; they gate shell deletion and move,
  which use-git says are never allowlisted
  (`skills/use-git/SKILL.md:42-46`).

**Question:** Does the spec own every project Permission rule (then `rm`
and `mv` join it with a stated reason, and its docstring stops saying
"for Beads"), or only the Beads rules (then `CLAUDE.md` and the
exact-equality tests must admit rows from elsewhere)?
**ADR gate:** no.

### 7. Irreversible deletion at three strengths

- **Denied outright:** Beads `delete`, `purge`, `compact`, `gc`, `prune`
  (`cli/repo_policy_test.py:42-100`).
- **Absent from the surface:** editing a live board option
  (`cli/ghw-board-sync:10-13`), remote branch deletion
  (`skills/use-git/SKILL.md:387-389`), branch deletion on merge
  (`cli/ghw-pr-merge:11`).
- **Grantable, with Skill-text approval:** label deletion through the
  `apply-delete` mode, which also strips the labels from open issues
  (`cli/ghw-label-sync:11-21`, `skills/setup-github-issues/SKILL.md:330-334`).
- **An agent act:** `git rm` of tracked files where granted
  (`skills/use-git/SKILL.md:42-46`), and the bootstrap's `git rm TODO.md`
  (`skills/setup-github-issues/SKILL.md:396`).
- One reading would make these consistent: recoverability. A tracked file
  survives in history; a stripped label assignment and a compacted Issue
  do not. No passage says so.

**Question:** Is recoverability the criterion (state it, and then decide
whether label deletion, which is not recoverable, should be an ask rule
rather than a grantable mode), or should every deletion get one treatment?
**ADR gate:** borderline: real options, but the cost of change is a few
rules.

### 8. The sub-agent ban rests on a reason that reaches further than Beads

- use-bd forbids sub-agents to claim, close or rewrite because "a
  sub-agent's environment cannot be told from its parent's"
  (`skills/use-bd/SKILL.md:59-66`).
- The same identity is written into every `Executed-By:` trailer
  (`cli/gitw-commit:30-32`, `cli/lib/actor.py:10-15`), yet sub-agents
  commit, push, open PRs, and here merge into `integrate/` branches with no
  equivalent rule (`CLAUDE.md:71-80`). Issue `agent-tooling-jk2` records
  the identity gap itself.
- If the reason is attribution, it applies to every write; if it is that a
  claim asserts ownership, which a shared Actor cannot prove, the ban is
  narrower and the stated reason should say so.

**Question:** Is the ban about attribution (then it should extend to the
other writes, or `agent-tooling-jk2` should be fixed first), or about
ownership (then use-bd should state that as the reason)?
**ADR gate:** no, unless the answer extends the ban to git and forge
writes.

### 9. A second declaration: interlock or drift hazard?

- **Interlock:** a cross-repo write needs "two independently-maintained
  artifacts to agree", the anchoring repo's grant and the roster's
  `operable_from` (`skills/use-git/SKILL.md:368-377`).
- **Drift hazard:** agent integration branches are declared only by the
  Permission rule, because "a second declaration would have to agree with
  the rules ... and two sources of truth for one policy drift"
  (`docs/projects/gitw/design.md:384-389`).
- Both describe a grant that extends where an agent may write; the two
  passages reach opposite conclusions about a second declaration without
  naming what distinguishes the cases (perhaps that the roster is
  machine-local and hand-edited by the user only).

**Question:** What makes a second declaration an interlock in one case and
a drift hazard in the other? Name the criterion in the gitw design, or
align the two.
**ADR gate:** no: recording the criterion is enough.

### 10. Whose name is on an agent's forge act?

- On Forgejo, every write acts as a machine account, "so automation's acts
  are visibly automation's" (`docs/projects/fjw/design.md:15-21`,
  `cli/fjw-pr-create:4-5`).
- On GitHub, ghw writes, merges included, run as the user's own account,
  and triage's mutations are "indistinguishable from genuine manual
  activity" (`skills/triage-issues/SKILL.md:402`); no passage records this
  as a decision.
- Git commits split the difference: the human's author identity plus an
  `Executed-By:` trailer naming the Actor (ADR 0002).

**Question:** Should agent acts on a forge be distinguishable from the
user's, as fjw decided, and if so is a machine account, a body marker, or
nothing the GitHub answer?
**ADR gate:** likely passes for GitHub: options are real and a machine
account is costly to introduce and to back out.

### 11. User-level write grants: ghw forbids them, triage requires them

- No ghw rule at user level, reads included, because a user-level grant is
  repo-unpinned (`docs/projects/ghw/design.md:46-52`).
- The triage wrappers, which write to GitHub, are allowed at user level by
  design (`skills/triage-issues/reference/DEPLOYMENT.md:40-44,55-72`,
  `skills/triage-issues/SKILL.md:618`), and are invoked by install path
  through `python3`, the one recorded exception to bare-name invocation
  (`README.md:117-121`).
- The justification differs (each triage wrapper writes only bounded values
  to the repo its profile names), but neither design says why bounded
  output outweighs being repo-unpinned.

**Question:** Is "bounded output, target named by an in-repo profile"
enough to justify a user-level write grant? If so, record it in the ghw
design as the exception; if not, triage needs per-repo grants.
**ADR gate:** no.

## Consistent across the tree

For the record, the sweep found these lines drawn the same way everywhere
they appear: unattended conflict resolutions are disclosed
(`skills/use-git/SKILL.md:353-357`, `skills/use-github/SKILL.md:256-258`,
`skills/use-forgejo/SKILL.md:81-83`); a refusal is never worked around with
the raw tool (`skills/use-git/SKILL.md:69-71`,
`skills/use-github/SKILL.md:44-46`, `skills/use-forgejo/SKILL.md:68-69`,
`skills/triage-issues/SKILL.md:595`); setup acts are a human's (rows G7,
G8, T1, B16, R11 and S1 above); and taking over another's work is refused
or asked for (rows G9 to G12, B2 and B9 above).
