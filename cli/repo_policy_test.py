"""The spec for .claude/settings.json, this repo's permission rules for Beads.

The file under test is repo-level, one directory up; the test lives here so
the existing discover command finds it without a second test root. The
tuples below are the policy's source of truth: the deny list must be exactly
the rows the shapes generate, and the ask and allow lists must be exactly the
rows listed. A hand-edited row with a typo fails a deny open silently, and
nothing else notices a verb missing one of its spellings, so equality against
a generated set is the control. To change the policy, change these tuples,
regenerate the JSON from them, and let the test confirm the two agree.

Rule grammar (Claude Code permissions): deny beats ask beats allow; `*`
matches at the start, middle, or end of a pattern; a single trailing
space-star also matches the bare command (docs, and observed 2026-09-25 on
Claude Code 2.1.282 in manual mode; friction log entry 35 on
agent-tooling-w7p.4); deny and ask rules match past a leading environment
assignment and inside compound commands; `command` is stripped before
matching; a bare-name rule never matches the same program invoked by path.

The 2026-09-25 observation covers an allow row only: with no bd rows in the
user or local settings, a bare `bdw ready` ran unprompted under the starred
allow row alone. Deny-side matching was not itself observed, so the exact
bare deny rows for the verbs that act with no arguments stay as belt and
braces against a future harness change. A deny row that fails to match fails
open, while an allow row that fails to match fails closed, so keeping them
costs only rows.

The project file only applies to sessions launched from a checkout
whose checked-out branch contains it.
"""

import json
import unittest
from pathlib import Path

POLICY = Path(__file__).resolve().parents[1] / ".claude" / "settings.json"

# The names the binary answers to: Homebrew links both `bd` and `beads`
# beside each other, and `bdw` is the Beads wrapper. Agents touch Beads only
# through `bdw` (the use-bd Skill), so the raw names are denied outright,
# reads included: the habit of typing `bd` fails at once instead of
# working for reads and prompting for writes. Everything below applies to
# `bdw` alone.
GRANTED_BINARIES = ("bdw",)
RAW_BINARIES = ("bd", "beads")
RAW_DENY_SHAPES = ("Bash({b})", "Bash({b} *)")

# Never run by an agent. Each verb gets two spellings: the subcommand-first
# form (which also matches the bare call) and the flag-first form that
# catches global flags placed before the verb.
DENY_VERBS = (
    "admin",
    "ado",
    "branch",
    "compact",
    "conflicts",
    "delete",
    "dolt",
    # Aliases (`done` for close, `hb` for heartbeat, `new` for create) and
    # `link` (shorthand for dep add) are denied so the use-bd Skill's one
    # spelling of each operation is the only one, while bdw does not map
    # them.
    "done",
    "edit",
    # Closes epics because their children closed, skipping the Branch
    # Issue's verifying pass (ADR 0009).
    "epic close-eligible",
    "events prune",
    "federation",
    "flatten",
    "forget",
    "gc",
    "github",
    "gitlab",
    "hb",
    "hooks",
    "init",
    "jira",
    "linear",
    "link",
    "mail",
    # Memories stay in the harness's own memory files, never in Beads.
    "memories",
    "metrics on",
    "migrate",
    "migrate-personal",
    "new",
    "notion",
    "prune",
    "purge",
    "recall",
    # The lease reaper: it reverts every claim whose lease has expired to
    # open. A lapsed lease is inert until reclaim runs, and our sessions sit
    # for hours waiting on a human, so a reclaim would rob live work. Denied
    # rather than asked for, by the user's ruling of 2026-09-25.
    "reclaim",
    "remember",
    "rename",
    "rename-prefix",
    "repo",
    "serve",
    "setup",
    "ship",
    "sql",
    "sync",
    "upgrade",
    "vc",
    "worktree",
)
DENY_SHAPES = ("Bash({b} {v} *)", "Bash({b} -* {v}*)")

# Flags that claim the next Issue for the agent, around the choice of what
# to work on. Denied wherever they appear on their verb.
DENY_FLAG_ROWS = (
    "Bash(bdw ready *--claim*)",
    "Bash(bdw close *--claim-next*)",
    "Bash(bdw close *--continue*)",
)

# Verbs that act with no arguments at all, given an exact bare row as well,
# so that a deny does not depend on the space-star-matches-bare rule. The
# rule is observed for allow rows, not for deny rows, and a deny that fails
# to match fails open, so these rows stay.
BARE_DENY_VERBS = (
    "compact",
    "flatten",
    "gc",
    "init",
    "migrate",
    "prune",
    "purge",
    "reclaim",
    "sync",
    "upgrade",
)
BARE_DENY_SHAPE = "Bash({b} {v})"

# bd's own --actor flag would let a caller name the actor, defeating the
# bdw's rule that identity comes from the environment. Denied in first
# position and after anything.
ACTOR_FLAG_DENY_SHAPES = ("Bash({b} --actor*)", "Bash({b} * --actor*)")

# Invocation by install path, which a bare-name rule cannot see. Kept to the
# install locations so reading the wrapper's source (cli/bdw) is not denied.
PATH_DENY_ROWS = (
    "Bash(*/bin/bd)",
    "Bash(*/bin/bd *)",
    "Bash(*/bin/beads)",
    "Bash(*/bin/beads *)",
    "Bash(*libexec/agent-tooling/bdw)",
    "Bash(*libexec/agent-tooling/bdw *)",
)

# Shell indirections that would hide a verb from prefix matching. A prompt on
# these is cheaper than one deny row per verb per indirection, and it holds in
# auto mode, where only ask and deny rows do. The list is enumerative and
# cannot be complete; the parsed-command deny hook is the real fix.
INDIRECTION_ASK_ROWS = (
    "Bash(exec *)",
    "Bash(env *)",
    "Bash(sh -c *)",
    "Bash(bash -c *)",
    "Bash(zsh -c *)",
    "Bash(xargs *)",
    "Bash(eval *)",
)

# Shell deletion and move. Git fences `git rm` and `git mv` to tracked,
# in-repo paths; the shell forms have no fence, and auto mode's classifier
# was seen approving a shell rm of a tracked file unprompted. An ask row
# puts the human back in front of them (the maintainer's ruling of
# 2026-10-11, PR #49).
SHELL_FILE_ASK_ROWS = (
    "Bash(rm *)",
    "Bash(mv *)",
)

# Human gate on top of an allow: flags that delete, override another actor's
# claim, close Issues on the agent's behalf, write files, or send data off
# the machine, and configuration or backup changes.
ASK_FLAGS = (
    "Bash(bdw update *--force*)",
    "Bash(bdw update *--no-history*)",
    "Bash(bdw update *--assignee*)",
    "Bash(bdw update * -a*)",
    "Bash(bdw unclaim *--force*)",
    "Bash(bdw close *--force*)",
    "Bash(bdw close * -f*)",
    "Bash(bdw create *--no-history*)",
    "Bash(bdw doctor *--fix*)",
    "Bash(bdw doctor *--clean*)",
    "Bash(bdw doctor *--yes*)",
    "Bash(bdw doctor * -y*)",
    "Bash(bdw doctor *--perf*)",
    "Bash(bdw doctor *--output*)",
    "Bash(bdw doctor * -o*)",
    "Bash(bdw orphans *--fix*)",
    "Bash(bdw orphans * -f*)",
    "Bash(bdw preflight *--fix*)",
    "Bash(bdw find-duplicates *--method*)",
    # Comments, then closes the Issue at once; a review never closes this
    # way, so only a human-attended call may.
    "Bash(bdw human respond *)",
    "Bash(bdw human dismiss *)",
    "Bash(bdw config set *)",
    "Bash(bdw config set-many *)",
    "Bash(bdw config unset *)",
    "Bash(bdw config apply *)",
    "Bash(bdw backup init *)",
    "Bash(bdw backup add *)",
    "Bash(bdw backup restore *)",
    "Bash(bdw backup remove *)",
    # Pushes the whole database to the backup destination.
    "Bash(bdw backup sync *)",
    "Bash(bdw assign *)",
    "Bash(bdw duplicates *)",
    "Bash(bdw import *)",
    "Bash(bdw export *)",
    "Bash(bdw batch *)",
    "Bash(bdw bootstrap *)",
    "Bash(bdw restore *)",
)

# Reads, granted on bdw. `metrics off` is the one write here: it only turns
# telemetry off.
ALLOW_READS = (
    "Bash({b})",
    "Bash({b} --help)",
    "Bash({b} help *)",
    "Bash({b} version)",
    "Bash({b} prime)",
    "Bash({b} quickstart)",
    "Bash({b} ready *)",
    "Bash({b} list *)",
    "Bash({b} show *)",
    "Bash({b} status *)",
    "Bash({b} search *)",
    "Bash({b} query *)",
    "Bash({b} count *)",
    "Bash({b} graph *)",
    "Bash({b} history *)",
    "Bash({b} diff *)",
    "Bash({b} blocked *)",
    "Bash({b} children *)",
    "Bash({b} comments *)",
    "Bash({b} orphans *)",
    "Bash({b} dep)",
    "Bash({b} dep list *)",
    "Bash({b} dep tree *)",
    "Bash({b} dep cycles *)",
    "Bash({b} label)",
    "Bash({b} label list *)",
    "Bash({b} label list-all *)",
    "Bash({b} epic)",
    "Bash({b} epic status *)",
    "Bash({b} gate list *)",
    "Bash({b} gate show *)",
    "Bash({b} human)",
    "Bash({b} human list *)",
    "Bash({b} human stats *)",
    "Bash({b} context *)",
    "Bash({b} where *)",
    "Bash({b} info *)",
    "Bash({b} ping *)",
    "Bash({b} schema *)",
    "Bash({b} stale *)",
    "Bash({b} lint *)",
    "Bash({b} doctor *)",
    "Bash({b} preflight *)",
    "Bash({b} statuses *)",
    "Bash({b} types *)",
    "Bash({b} state *)",
    "Bash({b} find-duplicates *)",
    "Bash({b} backup status *)",
    "Bash({b} config get *)",
    "Bash({b} config list *)",
    "Bash({b} config show *)",
    "Bash({b} config drift *)",
    "Bash({b} config validate *)",
    "Bash({b} metrics)",
    "Bash({b} metrics off *)",
    "Bash({b} metrics example *)",
)

# Reversible writes, allowed through bdw, which carries the actor.
WRITE_VERBS = (
    "create *",
    "q *",
    "update *",
    "close *",
    "reopen *",
    "comment *",
    "comments add *",
    "note *",
    "dep add *",
    "dep remove *",
    "dep relate *",
    "dep unrelate *",
    "label add *",
    "label remove *",
    "label propagate *",
    "tag *",
    "priority *",
    "unclaim *",
    "heartbeat *",
    # Work waiting on a human is blocked by a gate. `gate check` closes the
    # gates whose condition holds (a merged PR). `gate resolve` stays
    # unruled, so it prompts: resolving a human gate is the human's act.
    "gate create *",
    "gate check *",
    "set-state *",
    "recompute-blocked *",
    "todo *",
    # Reversible, visible record-keeping: when to use them is a filing
    # discipline (use-bd), not a permission.
    "duplicate *",
    "supersede *",
    "defer *",
    "undefer *",
)


def expected_deny() -> set:
    rows = set(PATH_DENY_ROWS) | set(DENY_FLAG_ROWS)
    for binary in RAW_BINARIES:
        rows.update(shape.format(b=binary) for shape in RAW_DENY_SHAPES)
    for verb in DENY_VERBS:
        for shape in DENY_SHAPES:
            rows.add(shape.format(b="bdw", v=verb))
    for verb in BARE_DENY_VERBS:
        rows.add(BARE_DENY_SHAPE.format(b="bdw", v=verb))
    for shape in ACTOR_FLAG_DENY_SHAPES:
        rows.add(shape.format(b="bdw"))
    return rows


def expected_ask() -> set:
    return set(INDIRECTION_ASK_ROWS) | set(SHELL_FILE_ASK_ROWS) | set(ASK_FLAGS)


def expected_allow() -> set:
    rows = set()
    for binary in GRANTED_BINARIES:
        rows.update(row.format(b=binary) for row in ALLOW_READS)
    rows.update("Bash(bdw {v})".format(v=verb) for verb in WRITE_VERBS)
    return rows


def policy_lists() -> dict:
    with POLICY.open(encoding="utf-8") as handle:
        return json.load(handle)["permissions"]


class RepoPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.lists = policy_lists()

    def test_the_file_has_exactly_the_three_lists(self) -> None:
        self.assertEqual(set(self.lists), {"deny", "ask", "allow"})

    def test_deny_is_exactly_the_generated_set(self) -> None:
        self.assertEqual(set(self.lists["deny"]), expected_deny())

    def test_ask_is_exactly_the_listed_set(self) -> None:
        self.assertEqual(set(self.lists["ask"]), expected_ask())

    def test_allow_is_exactly_the_listed_set(self) -> None:
        self.assertEqual(set(self.lists["allow"]), expected_allow())

    def test_no_list_repeats_a_row(self) -> None:
        for name, rows in self.lists.items():
            self.assertEqual(len(rows), len(set(rows)), name)

    def test_no_row_appears_in_two_lists(self) -> None:
        names = list(self.lists)
        for i, first in enumerate(names):
            for second in names[i + 1:]:
                overlap = set(self.lists[first]) & set(self.lists[second])
                self.assertEqual(overlap, set(), f"{first} and {second}")

    def test_every_list_is_sorted_so_membership_is_checkable_by_eye(self) -> None:
        for name, rows in self.lists.items():
            self.assertEqual(rows, sorted(rows), name)

    def test_allow_rows_start_with_a_granted_binary_and_a_literal_verb(self) -> None:
        for row in self.lists["allow"]:
            self.assertTrue(row.startswith("Bash("), row)
            body = row[len("Bash("):-1]
            tokens = body.split(" ")
            self.assertIn(tokens[0], GRANTED_BINARIES, row)
            if len(tokens) > 1:
                self.assertNotIn("*", tokens[1], row)

    def test_the_raw_names_are_denied_outright_and_never_granted(self) -> None:
        deny = set(self.lists["deny"])
        granted = self.lists["allow"] + self.lists["ask"]
        for binary in RAW_BINARIES:
            self.assertIn(f"Bash({binary})", deny)
            self.assertIn(f"Bash({binary} *)", deny)
            for row in granted:
                self.assertFalse(row.startswith(f"Bash({binary} "), row)
                self.assertNotEqual(row, f"Bash({binary})")

    def test_every_forgetting_verb_is_denied(self) -> None:
        deny = set(self.lists["deny"])
        for verb in ("admin", "prune", "gc", "compact"):
            self.assertIn(f"Bash(bdw {verb} *)", deny)
            self.assertIn(f"Bash(bdw -* {verb}*)", deny)

    def test_nothing_that_leaves_the_machine_is_anything_but_denied(self) -> None:
        deny = set(self.lists["deny"])
        granted = set(self.lists["allow"]) | set(self.lists["ask"])
        for verb in ("github", "sync", "dolt", "federation", "mail", "ship", "metrics on"):
            self.assertIn(f"Bash(bdw {verb} *)", deny)
            self.assertIn(f"Bash(bdw -* {verb}*)", deny)
            self.assertNotIn(f"Bash(bdw {verb} *)", granted)

    def test_the_actor_flag_is_denied_in_any_position(self) -> None:
        deny = set(self.lists["deny"])
        self.assertIn("Bash(bdw --actor*)", deny)
        self.assertIn("Bash(bdw * --actor*)", deny)

    def test_reclaim_is_denied_and_never_asked_for(self) -> None:
        deny = set(self.lists["deny"])
        granted = set(self.lists["allow"]) | set(self.lists["ask"])
        self.assertIn("Bash(bdw reclaim)", deny)
        self.assertIn("Bash(bdw reclaim *)", deny)
        self.assertIn("Bash(bdw -* reclaim*)", deny)
        self.assertNotIn("Bash(bdw reclaim *)", granted)

    def test_every_write_verb_is_allowed_through_the_wrapper(self) -> None:
        allow = set(self.lists["allow"])
        for verb in WRITE_VERBS:
            self.assertIn(f"Bash(bdw {verb})", allow)

    def test_what_use_bd_says_never_to_do_is_denied_or_asked_for(self) -> None:
        # The Skill's "never" calls must not run unattended: claiming
        # around the choice of work, closing an epic or a review on the
        # agent's behalf, and taking over another Actor's claim.
        deny = set(self.lists["deny"])
        ask = set(self.lists["ask"])
        for row in (
            "Bash(bdw epic close-eligible *)",
            "Bash(bdw ready *--claim*)",
            "Bash(bdw close *--claim-next*)",
            "Bash(bdw close *--continue*)",
            "Bash(bdw memories *)",
            "Bash(bdw recall *)",
        ):
            self.assertIn(row, deny)
        for row in (
            "Bash(bdw human respond *)",
            "Bash(bdw unclaim *--force*)",
            "Bash(bdw update *--assignee*)",
            "Bash(bdw update * -a*)",
            "Bash(bdw orphans *--fix*)",
            "Bash(bdw backup sync *)",
        ):
            self.assertIn(row, ask)


if __name__ == "__main__":
    unittest.main()
