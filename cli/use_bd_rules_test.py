"""use-bd's canonical Beads rule set, and the Skill held to it.

`skills/use-bd/rules.json` is the canonical rule set, shipped with the Skill
as data. This test checks the data's shape, then that every `bdw` command
the Skill teaches (in code spans and fenced blocks of `SKILL.md`,
`quirks.md`, and `onboarding.md`) is allowed by it: it matches an allow row
and no deny or ask row, so it neither prompts nor is refused.

A command the Skill names only to forbid it, or as a template rather than a
call, is listed in NOT_TAUGHT with the reason, and the test holds each of
those to the opposite: the rules must not allow it outright. Raw `bd`
commands are out of scope: the canonical set denies them to agents, and the
ones in `onboarding.md` are steps a human runs.
"""

import re
import textwrap
import unittest

import use_bd_rules_snapshot_test_support as snapshot
from use_bd_rules_test_support import (
    CANONICAL,
    LISTS,
    SKILL_DIR,
    canonical_rows,
    classify,
    load_canonical,
    rule_matches,
)

SKILL_FILES = ("SKILL.md", "quirks.md", "onboarding.md")

# Commands the Skill writes in code but does not teach as calls, each with
# why. The test requires that the rules do not allow them outright.
NOT_TAUGHT = {
    # The flag-first spelling, shown as what never to type.
    "bdw --json ready": "flag-first spelling the Skill forbids",
    # A template for asking a verb for its own help; it matches the verb's
    # own rules, which is why the Skill teaches `bdw help <verb>` instead.
    "bdw X --help": "template the Skill warns can prompt or be denied",
    # Comments, then closes at once; the Skill says never to close this way.
    "bdw human respond": "the Skill says never to close through it",
}

# A fence may be indented, as it is inside a list item; its lines carry the
# same indent, which commands_in strips.
FENCE = re.compile(r"^[ \t]*```[^\n]*\n(.*?)^[ \t]*```", re.MULTILINE | re.DOTALL)
SPAN = re.compile(r"`([^`]+)`")
PLACEHOLDER = re.compile(r"<[^<>]+>")


def normalize(text: str) -> str:
    """One command as it would be typed: placeholders filled, options taken."""
    text = PLACEHOLDER.sub("X", text)
    text = text.replace("[", "").replace("]", "")
    return " ".join(text.split())


def commands_in(markdown: str) -> list:
    found = []
    for block in FENCE.findall(markdown):
        found.extend(line for line in textwrap.dedent(block).splitlines() if line.strip())
    prose = FENCE.sub("", markdown)
    found.extend(SPAN.findall(prose))
    commands = []
    for raw in found:
        command = normalize(raw)
        if command == "bdw" or command.startswith("bdw "):
            commands.append(command)
    return commands


def skill_commands() -> dict:
    """Each `bdw` command the Skill writes, mapped to the files it is in."""
    seen: dict = {}
    for name in SKILL_FILES:
        text = (SKILL_DIR / name).read_text(encoding="utf-8")
        for command in commands_in(text):
            seen.setdefault(command, set()).add(name)
    return seen


class CanonicalDataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.data = load_canonical()
        self.rows = canonical_rows(self.data)

    def test_the_data_ships_beside_the_skill(self) -> None:
        self.assertEqual(CANONICAL.parent, SKILL_DIR)
        self.assertTrue((SKILL_DIR / "SKILL.md").is_file())

    def test_it_names_the_bd_version_it_was_verified_against(self) -> None:
        self.assertEqual(self.data["bd_version"], "1.3.0")

    def test_every_group_says_why_and_has_one_form(self) -> None:
        for name in LISTS:
            for group in self.data[name]:
                self.assertTrue(group.get("why"), group)
                self.assertIn(
                    set(group),
                    ({"why", "rows"}, {"why", "verbs", "shapes"}),
                    group,
                )
                for shape in group.get("shapes", ()):
                    self.assertIn("{v}", shape, group)

    def test_every_row_is_a_bash_rule(self) -> None:
        for name, rows in self.rows.items():
            for row in rows:
                self.assertTrue(row.startswith("Bash(") and row.endswith(")"), row)

    def test_no_row_repeats_within_or_across_lists(self) -> None:
        everything = []
        for rows in self.rows.values():
            everything.extend(rows)
        repeated = {row for row in everything if everything.count(row) > 1}
        self.assertEqual(repeated, set())

    def test_rules_touch_only_bdw_beyond_the_raw_name_denies(self) -> None:
        # The one exemption is positive: the raw names, and the binaries
        # invoked by install path. Any other row off `bdw` would be a
        # general shell rule that every onboarded repo inherits unreviewed.
        raw_name_denies = {"bd", "bd *", "beads", "beads *"}
        install_paths = ("*/bin/bd", "*/bin/beads", "*libexec/agent-tooling/bdw")
        for name, rows in self.rows.items():
            for row in rows:
                body = row[len("Bash("):-1]
                if name == "deny" and (
                    body in raw_name_denies
                    or any(body in (p, p + " *") for p in install_paths)
                ):
                    continue
                self.assertTrue(body == "bdw" or body.startswith("bdw "), row)

    def test_the_data_expands_to_the_snapshot(self) -> None:
        # The data and the generated settings move together, so only an
        # independent copy notices a row dropped or added by mistake.
        for name, frozen in (
            ("deny", snapshot.DENY),
            ("ask", snapshot.ASK),
            ("allow", snapshot.ALLOW),
        ):
            rows = set(self.rows[name])
            self.assertEqual(sorted(frozen - rows), [], f"{name}: dropped")
            self.assertEqual(sorted(rows - frozen), [], f"{name}: added")

    def test_bare_deny_verbs_are_also_denied_in_both_spellings(self) -> None:
        deny = set(self.rows["deny"])
        for row in deny:
            body = row[len("Bash("):-1]
            if body.startswith("bdw ") and "*" not in body:
                verb = body[len("bdw "):]
                self.assertIn(f"Bash(bdw {verb} *)", deny, row)
                self.assertIn(f"Bash(bdw -* {verb}*)", deny, row)

    def test_raw_names_are_denied_outright(self) -> None:
        for binary in ("bd", "beads"):
            self.assertEqual(classify(binary, self.rows), "deny")
            self.assertEqual(classify(f"{binary} ready", self.rows), "deny")
            self.assertEqual(classify(f"/opt/homebrew/bin/{binary} list", self.rows), "deny")


class ExtractorTest(unittest.TestCase):
    def test_it_reads_inline_spans_and_flush_left_fences(self) -> None:
        text = "Run `bdw ready`.\n\n```sh\nbdw show <id>\n```\n"
        self.assertEqual(commands_in(text), ["bdw show X", "bdw ready"])

    def test_it_reads_fences_indented_inside_a_list_item(self) -> None:
        text = "- [ ] Step:\n\n  ```sh\n  bdw delete <id>\n  ```\n"
        self.assertEqual(commands_in(text), ["bdw delete X"])

    def test_it_skips_what_is_not_bdw(self) -> None:
        text = "`bd init`, `bdwx`, and\n\n  ```sh\n  git status\n  ```\n"
        self.assertEqual(commands_in(text), [])


class MatcherTest(unittest.TestCase):
    def test_a_trailing_space_star_also_matches_the_bare_command(self) -> None:
        self.assertTrue(rule_matches("Bash(bdw ready *)", "bdw ready"))
        self.assertTrue(rule_matches("Bash(bdw ready *)", "bdw ready --json"))
        self.assertFalse(rule_matches("Bash(bdw ready *)", "bdw readyx"))

    def test_star_matches_anywhere(self) -> None:
        self.assertTrue(rule_matches("Bash(bdw * --actor*)", "bdw show X --actor=me"))
        self.assertTrue(rule_matches("Bash(bdw -* done*)", "bdw --json done X"))
        self.assertFalse(rule_matches("Bash(bdw -* done*)", "bdw close X"))

    def test_an_exact_rule_matches_only_itself(self) -> None:
        self.assertTrue(rule_matches("Bash(bdw prime)", "bdw prime"))
        self.assertFalse(rule_matches("Bash(bdw prime)", "bdw prime --full"))

    def test_deny_beats_ask_beats_allow(self) -> None:
        rows = {
            "deny": ["Bash(x d *)"],
            "ask": ["Bash(x d *)", "Bash(x a *)"],
            "allow": ["Bash(x *)"],
        }
        self.assertEqual(classify("x d", rows), "deny")
        self.assertEqual(classify("x a 1", rows), "ask")
        self.assertEqual(classify("x b", rows), "allow")
        self.assertEqual(classify("y", rows), "prompt")


class SkillTeachesOnlyAllowedCommandsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = canonical_rows()
        self.commands = skill_commands()

    def test_the_extractor_finds_the_loop(self) -> None:
        # Guards against an extractor that silently finds nothing.
        for command in (
            "bdw prime",
            "bdw ready",
            "bdw update X --claim",
            "bdw close X --reason-file=X",
            "bdw gate create --blocks=X --type=gh:pr --await-id=X",
        ):
            self.assertIn(command, self.commands)

    def test_every_taught_command_is_allowed(self) -> None:
        wrong = {}
        for command, files in self.commands.items():
            if command in NOT_TAUGHT:
                continue
            verdict = classify(command, self.rows)
            if verdict != "allow":
                wrong[command] = (verdict, sorted(files))
        self.assertEqual(wrong, {})

    def test_every_not_taught_command_is_still_in_the_skill(self) -> None:
        # A stale exclusion would hide a command the Skill starts to teach.
        for command in NOT_TAUGHT:
            self.assertIn(command, self.commands)

    def test_what_the_skill_forbids_is_not_allowed_outright(self) -> None:
        for command, why in NOT_TAUGHT.items():
            self.assertNotEqual(classify(command, self.rows), "allow", why)


if __name__ == "__main__":
    unittest.main()
