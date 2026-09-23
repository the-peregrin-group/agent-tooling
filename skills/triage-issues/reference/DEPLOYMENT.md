# Deploying `triage-issues` for recurring / unattended operation

Scheduling is a per-deployment concern, not skill policy (the skill behaves
identically however it is invoked). This document covers how to run triage
*repeatedly and unattended* safely. Read `../SKILL.md` (`## Cadence & autonomous
operation`) first for the policy this operationalizes.

The load-bearing safety property is **fail-closed autonomy**: the permission
boundary and the autonomy boundary are the *same line*. Everything below exists to
preserve that line.

---

## 1. The wrapper model (why this is safe)

All GitHub I/O routes through the six skill-owned wrappers in this directory. The
agent is allowed to invoke *these wrapper names only* — never raw `gh`.

| Wrapper | Kind | Bound by |
|---|---|---|
| `triage-inventory` | read | — (read-only) |
| `triage-timeline` | read | — (read-only) |
| `triage-apply-sync` | autonomous write | **policy**: derives the R-SYNC-1/2 correction itself; cannot be told a target status |
| `triage-fix-label` | autonomous write | **schema**: refuses any label not in the profile's label set |
| `triage-bump-triaged` | autonomous write | **value**: writes only the Last Triaged date field |
| `triage-update-ledger` | autonomous write | **target**: writes only to the profile's ledger issue; takes no issue number |

Two consequences make the boundary hold by construction:

1. **Every autonomous wrapper emits only bounded output** — an enumerable option
   id, a schema label, a date, or free text confined to the one ledger issue.
   None can write free text to an arbitrary issue.
2. **Proposed mutations have no wrapper.** Status/priority/size *transitions*,
   scope-body rewrites, closes, and reparenting are not implemented as wrappers.
   The only path to them is raw `gh`, which is not allowlisted — so under a
   deny-by-default permission mode they *fail closed* (deny, not hang, not
   execute). A denied call is terminal for the pass: the agent records the intended
   action as a pending ledger finding and moves on (R-CAD-3).

Because the wrappers are the sole readers of every opaque per-project id (field /
option / project-node ids + ledger issue number, all in `TRIAGE.md`), no id ever
appears in a shell command or a settings file, and **the allowlist is
project-agnostic** — it can live in global `~/.claude/settings.json` and serve
every project that adopts the skill.

### No third-party runtime dependency

The wrappers are stdlib-only Python 3 (the profile config block is JSON, parsed by
`json`). There is **no venv or pip install to bootstrap** on the machine that runs
the unattended pass — a deliberate choice so a headless run cannot fail on a
missing dependency. (`gh` must be installed and authenticated; see §4.)

---

## 2. The allowlist (global `~/.claude/settings.json`)

Add these to `permissions.allow`. They name the wrappers by their installed
path, and permission rules match the command string as typed, so the agent must
invoke them spelled exactly as the rule spells them (the skill instructs this).
The rows below use the `~/` form of the installed skill path; if your deployment
writes the path out in full instead, write the rules the same way. Headless
invocations always pass at least `--profile`, so a trailing argument always
follows the wrapper name.

```jsonc
"Bash(python3 ~/.claude/skills/triage-issues/reference/triage-inventory *)",
"Bash(python3 ~/.claude/skills/triage-issues/reference/triage-timeline *)",
"Bash(python3 ~/.claude/skills/triage-issues/reference/triage-apply-sync *)",
"Bash(python3 ~/.claude/skills/triage-issues/reference/triage-fix-label *)",
"Bash(python3 ~/.claude/skills/triage-issues/reference/triage-bump-triaged *)",
"Bash(python3 ~/.claude/skills/triage-issues/reference/triage-update-ledger *)"
```

**Do not** add `Bash(gh *)` or any broader `gh` rule to the unattended allowlist —
that would give proposed mutations an allowlisted path and defeat the fail-safe.

Read wrappers are allowlisted too: reads are autonomous, and letting them run
un-prompted is what makes an unattended pass possible at all.

---

## 3. Run modes and the permission-mode requirement

The skill runs in two modes over one ledger (R-CAD-1). The permission mode is what
distinguishes them operationally:

- **Interactive** (a human is present): normal session. Proposed mutations prompt;
  the human approves in-session. Any permission mode is fine.
- **Unattended** (headless): must run **deny-by-default** — `--permission-mode
  dontAsk` (CLI) or the Desktop equivalent — with the allowlist above. This is the
  enforcement, not a suggestion: it is the mechanism that turns "no wrapper for
  proposed mutations" into "proposed mutations cannot happen."

> **NEVER run the unattended pass under `bypassPermissions`.** Under bypass, raw
> `gh` is auto-approved, so a stray proposed mutation would *execute* rather than
> fail closed — collapsing the autonomy boundary to an instruction the model is
> merely asked to honor. If a scheduler offers only `bypassPermissions` (no
> deny-by-default), it is **not** an acceptable host for the unattended pass; use
> the background-job fallback (§4), which runs `--permission-mode dontAsk`, instead.

> ⚠️ **Caveat: project-level write rules.** An unattended pass launched in a
> repo whose project settings allowlist `ghw-*` write verbs gains a write path
> outside the triage wrappers, so its permission boundary no longer equals its
> autonomy boundary. Until that is resolved, do not host unattended triage in
> such a repo.

### Verification checklist before trusting an unattended host

1. Confirm the host honors `~/.claude/settings.json` `permissions.allow`.
2. Confirm it runs deny-by-default (a non-allowlisted command is *denied*, not
   auto-approved and not indefinitely prompting).
3. Smoke test: run one unattended pass and confirm the ledger body updated and no
   proposed mutation was applied (diff the board before/after; only R-SYNC /
   R-LABEL / Last Triaged should have moved).

---

## 4. Deployment options

### Recommended — Claude Desktop *Local* routine

Runs against the real local repo, honors `~/.claude/settings.json` (so the
allowlist + deny-by-default boundary apply unchanged), and lets the Desktop app own
scheduling and subscription auth — no trigger script to maintain.

- Configure it **deny-by-default** (`dontAsk` or equivalent). See the §3 warning:
  if the routine only exposes `bypassPermissions`, do not use it for autonomous
  mutation — use the background-job fallback.
- Point it at the project directory so `TRIAGE.md` is found from cwd.

> **Open verification:** confirm a Local routine actually exposes a
> deny-by-default posture (not just allow / `bypassPermissions`). If it does not,
> the unattended pass must run via the background-job fallback, where
> `--permission-mode dontAsk` is explicit.

### Fallback — a background job dispatched by a guard script

A trigger runs a small guard script, and the script dispatches the pass as a
Claude Code background job:

- **Trigger:** a `launchd` agent (or cron) on a schedule, or a `SessionStart`
  hook so the first session of the day starts the pass.
- **Guard:** exit early when a marker file says today's pass already ran, and
  take a lock file atomically (for example with `set -o noclobber`) so two
  triggers cannot dispatch twice; give the lock an age limit so a crashed run
  cannot hold it forever. The guard returns right after dispatch and never
  writes the marker. The run itself writes it, as its final act after its
  ledger update, so a failed pass retries at the next trigger.
- **Dispatch,** from the project directory so `TRIAGE.md` is found:

    ```sh
    claude --bg "Run an unattended triage pass on this repo per the triage-issues skill." \
      --name triage-<date> --worktree triage-<date> \
      --permission-mode dontAsk \
      --allowedTools "Edit(<worktree-root>/**),Edit(<job-tmp-root>/**)" \
      < /dev/null
    ```

    The Edit grants are required: `dontAsk` denies every file write, even
    inside the run's own worktree, and the run must write the ledger body to a
    file for `triage-update-ledger --body-file` (a piped stdin would not match
    the allow rule). The run also writes the success marker, so grant the
    marker's path too, or give the run an allowlisted command that writes it.
    Scope the grants to the run's own worktree and job tmp dir, nothing
    wider. Put the prompt
    before `--allowedTools`: that flag is variadic and swallows trailing
    positionals. Take stdin from `/dev/null`: a hook script inherits the
    triggering session's payload on stdin, and `claude --bg` appends piped
    stdin to the prompt. Never put a raw `gh` rule in `--allowedTools`.
- **Cleanup:** each run leaves a worktree and branch behind; have the guard
  reap finished runs' worktrees and branches before dispatching, so they do
  not accumulate.
- **Failure surfacing:** log each dispatch, and add the **stale-ledger
  tripwire** — alert if the ledger issue's last-updated date has not advanced
  since the last scheduled pass (a silent failure otherwise looks like "nothing
  to do").

**Alternative — `claude -p`.** The same trigger can run
`claude -p "<prompt>" --permission-mode dontAsk` with the same Edit grants
instead, which needs no job naming or worktree. `claude -p` may be billed
differently from interactive use on subscription plans; check your plan's terms
before adopting it.

### Ruled out

- **Claude Desktop *Cloud* routine** — executes against a repo *clone* with
  connector-based writes, bypassing this skill's local wrapper/allowlist model.
  Do not use for autonomous mutation.
- **In-session schedulers** (`CronCreate` / `/loop` / `ScheduleWakeup`) — require
  an open REPL and expire after 7 days. Not suitable for a durable daily cadence.

---

## 5. Billing guardrails

An unattended pass should never be able to produce a surprise bill. `claude -p`
may be billed differently from interactive use on subscription plans; check your
plan's terms before adopting it (§4). Beyond that:

- **Authenticate via the subscription**, never `ANTHROPIC_API_KEY` (that switch is
  all-or-nothing pay-as-you-go).
- **Leave Console *usage credits* disabled** — an exhausted run then *stops* rather
  than overflowing to paid API.
- **Run the unattended pass on a cost-efficient model** — it is mechanical
  (R-SYNC / R-LABEL / Last Triaged / ledger reconcile). Reserve Opus for
  interactive scope / eng-design. The profile's `cadence.unattended_model` may bind
  this.

---

## 6. One-time bootstrap per project (interactive)

Standing up triage in a repo is interactive, never autonomous (R-CAD-6):

1. Ensure `TRIAGE.md` exists at the repo root with a valid `<!-- BEGIN triage-config
   -->` block (all field / option / project-node ids filled in). Verify it parses:
   `python3 .../triage-inventory --profile ./TRIAGE.md` should return the board.
2. Create the ledger issue: `gh issue create --repo <repo> --title "Triage ledger"
   --body "Managed by the triage-issues skill."` (optionally `gh issue pin`).
3. Write its number into the profile config block as `ledger_issue` and commit.
4. From here, steady state only ever *reads* that pointer and *edits* the existing
   ledger — both within the autonomous set.
