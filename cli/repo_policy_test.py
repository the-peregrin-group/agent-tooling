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
space-star also matches the bare command (docs; not yet observed from a
session that provably enforces this file, hence the bare rows for the verbs
that act with no arguments); deny and ask rules match past a leading
environment assignment and inside compound commands; `command` is stripped
before matching; a bare-name rule never matches the same program invoked by
path. The project file only applies to sessions launched from a checkout
whose checked-out branch contains it.
"""

import json
import unittest
from pathlib import Path

POLICY = Path(__file__).resolve().parents[1] / ".claude" / "settings.json"

# The names the binary answers to: Homebrew links both `bd` and `beads`
# beside each other, and `bdw` is the Beads wrapper. Reads and reversible
# writes are granted on `bd` and `bdw` only; `beads` is denied and asked for
# so that it cannot be the unguarded spelling in auto mode.
GRANTED_BINARIES = ("bd", "bdw")
GUARDED_BINARIES = ("bd", "bdw", "beads")

# Never run by an agent. Each verb gets two spellings per binary: the
# subcommand-first form (which also matches the bare call) and the
# flag-first form that catches global flags placed before the verb.
DENY_VERBS = (
    "admin",
    "ado",
    "branch",
    "compact",
    "conflicts",
    "delete",
    "dolt",
    "edit",
    "events prune",
    "federation",
    "flatten",
    "forget",
    "gc",
    "github",
    "gitlab",
    "hooks",
    "init",
    "jira",
    "linear",
    "mail",
    "metrics on",
    "migrate",
    "migrate-personal",
    "notion",
    "prune",
    "purge",
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

# Verbs that act with no arguments at all, given an exact bare row as well,
# so that a deny does not depend on the space-star-matches-bare rule.
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

# Human gate on top of an allow: flags that delete, override another actor's
# claim, write files, or send data off the machine, and configuration or
# backup-destination changes.
ASK_FLAGS = (
    "Bash({b} update *--force*)",
    "Bash({b} update *--no-history*)",
    "Bash({b} close *--force*)",
    "Bash({b} close * -f*)",
    "Bash({b} create *--no-history*)",
    "Bash({b} doctor *--fix*)",
    "Bash({b} doctor *--clean*)",
    "Bash({b} doctor *--yes*)",
    "Bash({b} doctor * -y*)",
    "Bash({b} doctor *--perf*)",
    "Bash({b} doctor *--output*)",
    "Bash({b} doctor * -o*)",
    "Bash({b} preflight *--fix*)",
    "Bash({b} find-duplicates *--method*)",
    "Bash({b} human dismiss *)",
    "Bash({b} config set *)",
    "Bash({b} config set-many *)",
    "Bash({b} config unset *)",
    "Bash({b} config apply *)",
    "Bash({b} backup init *)",
    "Bash({b} backup add *)",
    "Bash({b} backup restore *)",
    "Bash({b} backup remove *)",
    "Bash({b} assign *)",
    "Bash({b} supersede *)",
    "Bash({b} duplicate *)",
    "Bash({b} duplicates *)",
    "Bash({b} import *)",
    "Bash({b} export *)",
    "Bash({b} batch *)",
    "Bash({b} bootstrap *)",
    "Bash({b} restore *)",
)

# Reads, granted on bd and bdw. A read needs no actor, so either name may
# run it. `metrics off` is the one write here: it only turns telemetry off.
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

# Reversible writes. Allowed through bdw, which carries the actor, and
# asked for on the bare names, so a raw write prompts even in auto mode.
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
    "human respond *",
    "set-state *",
    "epic close-eligible *",
    "recompute-blocked *",
    "backup sync *",
    "todo *",
)
# `ready --claim` is a write hiding under the `ready *` read.
RAW_WRITE_EXTRA = ("Bash({b} ready *--claim*)",)
RAW_BINARIES = tuple(b for b in GUARDED_BINARIES if b != "bdw")


def expected_deny() -> set:
    rows = set(PATH_DENY_ROWS)
    for binary in GUARDED_BINARIES:
        for verb in DENY_VERBS:
            for shape in DENY_SHAPES:
                rows.add(shape.format(b=binary, v=verb))
        for verb in BARE_DENY_VERBS:
            rows.add(BARE_DENY_SHAPE.format(b=binary, v=verb))
        for shape in ACTOR_FLAG_DENY_SHAPES:
            rows.add(shape.format(b=binary))
    return rows


def expected_ask() -> set:
    rows = set(INDIRECTION_ASK_ROWS)
    for binary in GUARDED_BINARIES:
        rows.update(row.format(b=binary) for row in ASK_FLAGS)
    for binary in RAW_BINARIES:
        rows.update("Bash({b} {v})".format(b=binary, v=verb) for verb in WRITE_VERBS)
        rows.update(row.format(b=binary) for row in RAW_WRITE_EXTRA)
    return rows


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

    def test_the_beads_name_is_never_granted(self) -> None:
        for row in self.lists["allow"]:
            self.assertFalse(row.startswith("Bash(beads"), row)

    def test_every_forgetting_verb_is_denied_for_every_guarded_binary(self) -> None:
        deny = set(self.lists["deny"])
        for binary in GUARDED_BINARIES:
            for verb in ("admin", "prune", "gc", "compact"):
                self.assertIn(f"Bash({binary} {verb} *)", deny)
                self.assertIn(f"Bash({binary} -* {verb}*)", deny)

    def test_nothing_that_leaves_the_machine_is_anything_but_denied(self) -> None:
        deny = set(self.lists["deny"])
        granted = set(self.lists["allow"]) | set(self.lists["ask"])
        for binary in GUARDED_BINARIES:
            for verb in ("github", "sync", "dolt", "federation", "mail", "ship", "metrics on"):
                self.assertIn(f"Bash({binary} {verb} *)", deny)
                self.assertIn(f"Bash({binary} -* {verb}*)", deny)
                self.assertNotIn(f"Bash({binary} {verb} *)", granted)

    def test_the_actor_flag_is_denied_in_any_position_for_every_guarded_binary(self) -> None:
        deny = set(self.lists["deny"])
        for binary in GUARDED_BINARIES:
            self.assertIn(f"Bash({binary} --actor*)", deny)
            self.assertIn(f"Bash({binary} * --actor*)", deny)

    def test_reclaim_is_denied_and_never_asked_for_on_every_guarded_binary(self) -> None:
        deny = set(self.lists["deny"])
        granted = set(self.lists["allow"]) | set(self.lists["ask"])
        for binary in GUARDED_BINARIES:
            self.assertIn(f"Bash({binary} reclaim)", deny)
            self.assertIn(f"Bash({binary} reclaim *)", deny)
            self.assertIn(f"Bash({binary} -* reclaim*)", deny)
            self.assertNotIn(f"Bash({binary} reclaim *)", granted)

    def test_every_raw_write_verb_is_asked_for_and_only_the_wrapper_is_allowed(self) -> None:
        ask = set(self.lists["ask"])
        allow = set(self.lists["allow"])
        for verb in WRITE_VERBS:
            for binary in RAW_BINARIES:
                self.assertIn(f"Bash({binary} {verb})", ask)
                self.assertNotIn(f"Bash({binary} {verb})", allow)
            self.assertIn(f"Bash(bdw {verb})", allow)


if __name__ == "__main__":
    unittest.main()
