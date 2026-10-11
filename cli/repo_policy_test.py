"""The spec for .claude/settings.json, this repo's permission rules for Beads.

The file under test is repo-level, one directory up; the test lives here so
the existing discover command finds it without a second test root. The
policy's source of truth is two layers: use-bd's canonical Beads rule set
(`skills/use-bd/rules.json`, shipped with the Skill as data, which every repo
on Beads carries) and this repo's local layer below. Each list in the file
must be exactly the canonical rows plus the local rows, sorted. A
hand-edited row with a typo fails a deny open silently, and nothing else
notices a verb missing one of its spellings, so equality against a generated
set is the control. To change the policy, change the canonical data (if
every repo on Beads should get the change) or the local layer, regenerate
the JSON from `generated_permissions()`, and let the test confirm the two
agree.

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

from use_bd_rules_test_support import canonical_rows

POLICY = Path(__file__).resolve().parents[1] / ".claude" / "settings.json"

# The names the binary answers to: Homebrew links both `bd` and `beads`
# beside each other, and `bdw` is the Beads wrapper. The canonical set
# denies the raw names outright and rules only on `bdw`.
GRANTED_BINARIES = ("bdw",)
RAW_BINARIES = ("bd", "beads")

# This repo's own layer on top of the canonical set. Shell indirections
# would hide a verb from prefix matching. A prompt on these is cheaper than
# one deny row per verb per indirection, and it holds in auto mode, where
# only ask and deny rows do. The list is enumerative and cannot be complete;
# the parsed-command deny hook is the real fix. They are a local layer, not
# canonical, because they rule on general shell commands, not on Beads.
LOCAL_DENY: tuple = ()
LOCAL_ASK = (
    "Bash(exec *)",
    "Bash(env *)",
    "Bash(sh -c *)",
    "Bash(bash -c *)",
    "Bash(zsh -c *)",
    "Bash(xargs *)",
    "Bash(eval *)",
    # Shell deletes and moves prompt, by the maintainer's ruling: auto mode
    # approved them for agents with no rule granting them.
    "Bash(rm *)",
    "Bash(mv *)",
)
LOCAL_ALLOW: tuple = ()


def expected_deny() -> set:
    return set(canonical_rows()["deny"]) | set(LOCAL_DENY)


def expected_ask() -> set:
    return set(canonical_rows()["ask"]) | set(LOCAL_ASK)


def expected_allow() -> set:
    return set(canonical_rows()["allow"]) | set(LOCAL_ALLOW)


def generated_permissions() -> dict:
    """The permissions object the file must hold, each list sorted."""
    return {
        "deny": sorted(expected_deny()),
        "ask": sorted(expected_ask()),
        "allow": sorted(expected_allow()),
    }

def policy_lists() -> dict:
    with POLICY.open(encoding="utf-8") as handle:
        return json.load(handle)["permissions"]


class RepoPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.lists = policy_lists()

    def test_the_file_has_exactly_the_three_lists(self) -> None:
        self.assertEqual(set(self.lists), {"deny", "ask", "allow"})

    def test_every_list_contains_the_canonical_set(self) -> None:
        for name, rows in canonical_rows().items():
            missing = set(rows) - set(self.lists[name])
            self.assertEqual(missing, set(), name)

    def test_deny_is_exactly_the_generated_set(self) -> None:
        self.assertEqual(set(self.lists["deny"]), expected_deny())

    def test_ask_is_exactly_the_listed_set(self) -> None:
        self.assertEqual(set(self.lists["ask"]), expected_ask())

    def test_allow_is_exactly_the_listed_set(self) -> None:
        self.assertEqual(set(self.lists["allow"]), expected_allow())

    def test_the_file_is_what_regeneration_would_write(self) -> None:
        self.assertEqual(self.lists, generated_permissions())

    def test_the_local_layer_does_not_repeat_a_canonical_row(self) -> None:
        canonical = canonical_rows()
        for name, local in (("deny", LOCAL_DENY), ("ask", LOCAL_ASK), ("allow", LOCAL_ALLOW)):
            self.assertEqual(set(local) & set(canonical[name]), set(), name)

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
        for verb in (
            "create", "update", "close", "note", "comments add", "dep add",
            "label add", "unclaim", "heartbeat", "gate create", "gate check",
            "duplicate", "supersede", "defer", "undefer",
        ):
            self.assertIn(f"Bash(bdw {verb} *)", allow)

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
