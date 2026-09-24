"""The spec for .claude/settings.json, this repo's Beads command policy.

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
space-star also matches the bare command; deny and ask rules match past a
leading environment assignment and inside compound commands; a bare-name
rule never matches the same program invoked by path.
"""

import json
import unittest
from pathlib import Path

POLICY = Path(__file__).resolve().parents[1] / ".claude" / "settings.json"

BINARIES = ("bd", "bdw")

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
    "metrics on",
    "migrate",
    "migrate-personal",
    "notion",
    "prune",
    "purge",
    "remember",
    "rename",
    "rename-prefix",
    "serve",
    "setup",
    "sql",
    "sync",
    "upgrade",
    "vc",
    "worktree",
)
DENY_SHAPES = ("Bash({b} {v} *)", "Bash({b} -* {v}*)")

# Invocation by install path, which a bare-name rule cannot see. Kept to the
# install locations so reading the shim's source (cli/bdw) is not denied.
PATH_DENY_ROWS = (
    "Bash(*/bin/bd)",
    "Bash(*/bin/bd *)",
    "Bash(*libexec/agent-tooling/bdw)",
    "Bash(*libexec/agent-tooling/bdw *)",
)

# Shell wrappers that would hide a verb from prefix matching. A prompt on
# these is cheaper than one deny row per verb per wrapper, and it holds in
# auto mode, where only ask and deny rows do.
WRAPPER_ASK_ROWS = (
    "Bash(command *)",
    "Bash(exec *)",
    "Bash(env *)",
    "Bash(sh -c *)",
    "Bash(bash -c *)",
    "Bash(zsh -c *)",
    "Bash(xargs *)",
    "Bash(eval *)",
)

# Human gate on top of an allow, for both binaries: flags that delete,
# override another actor's claim, write files, or send data off the machine,
# and configuration or backup-destination changes.
ASK_BOTH = (
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
    "Bash({b} reclaim *)",
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

# Reads, for both binaries. A read needs no actor, so either name may run it.
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

# Reversible writes. Allowed through the shim, which carries the actor, and
# asked for on the bare binary, so a raw write prompts even in auto mode.
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
ASK_BD_ONLY_EXTRA = ("Bash(bd ready *--claim*)",)


def expected_deny() -> set:
    rows = set(PATH_DENY_ROWS)
    for binary in BINARIES:
        for verb in DENY_VERBS:
            for shape in DENY_SHAPES:
                rows.add(shape.format(b=binary, v=verb))
    return rows


def expected_ask() -> set:
    rows = set(WRAPPER_ASK_ROWS) | set(ASK_BD_ONLY_EXTRA)
    for binary in BINARIES:
        rows.update(row.format(b=binary) for row in ASK_BOTH)
    rows.update("Bash(bd {v})".format(v=verb) for verb in WRITE_VERBS)
    return rows


def expected_allow() -> set:
    rows = set()
    for binary in BINARIES:
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

    def test_allow_rows_start_with_a_bare_binary_and_a_literal_verb(self) -> None:
        for row in self.lists["allow"]:
            self.assertTrue(row.startswith("Bash("), row)
            body = row[len("Bash("):-1]
            tokens = body.split(" ")
            self.assertIn(tokens[0], BINARIES, row)
            if len(tokens) > 1:
                self.assertNotIn("*", tokens[1], row)

    def test_every_forgetting_verb_is_denied_for_both_binaries(self) -> None:
        deny = set(self.lists["deny"])
        for binary in BINARIES:
            for verb in ("admin", "prune", "gc", "compact"):
                self.assertIn(f"Bash({binary} {verb} *)", deny)
                self.assertIn(f"Bash({binary} -* {verb}*)", deny)

    def test_nothing_that_leaves_the_machine_is_allowed(self) -> None:
        allow = set(self.lists["allow"])
        for binary in BINARIES:
            for verb in ("github", "sync", "dolt", "federation", "metrics on"):
                self.assertNotIn(f"Bash({binary} {verb} *)", allow)


if __name__ == "__main__":
    unittest.main()
