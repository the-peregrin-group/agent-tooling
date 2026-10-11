"""Reading use-bd's canonical Beads rule set, and matching commands against it.

The canonical set is `skills/use-bd/rules.json`, data shipped with the Skill.
Two tests read it: `repo_policy_test.py` (this repo's settings contain it) and
`use_bd_rules_test.py` (every command the Skill teaches is allowed by it).

The matcher models the Claude Code Bash rule grammar these rules rely on:
`*` matches any run of characters anywhere in the pattern, a single trailing
space-star also matches the bare command, and deny beats ask beats allow.
It deliberately ignores what the rules here never use (`:*` suffixes,
compound-command splitting, environment-assignment stripping), so it answers
only for single, plain commands.
"""

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "use-bd"
CANONICAL = SKILL_DIR / "rules.json"
LISTS = ("deny", "ask", "allow")


def load_canonical(path: Path = CANONICAL) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def expand_group(group: dict) -> List[str]:
    rows = list(group.get("rows", ()))
    for verb in group.get("verbs", ()):
        rows.extend(shape.format(v=verb) for shape in group["shapes"])
    return rows


def expand_list(groups: Iterable[dict]) -> List[str]:
    rows: List[str] = []
    for group in groups:
        rows.extend(expand_group(group))
    return rows


def canonical_rows(data: dict = None) -> Dict[str, List[str]]:
    """Each list's rows, in file order, duplicates kept so a test can see them."""
    if data is None:
        data = load_canonical()
    return {name: expand_list(data[name]) for name in LISTS}


def rule_matches(rule: str, command: str) -> bool:
    if not (rule.startswith("Bash(") and rule.endswith(")")):
        raise ValueError(f"not a Bash rule: {rule}")
    pattern = rule[len("Bash("):-1]
    regex = ".*".join(re.escape(part) for part in pattern.split("*"))
    if re.fullmatch(regex, command, flags=re.DOTALL):
        return True
    if pattern.endswith(" *") and pattern.count("*") == 1:
        return command == pattern[:-2]
    return False


def classify(command: str, rows: Dict[str, Iterable[str]]) -> str:
    """'deny', 'ask', or 'allow' by the first list with a match; else 'prompt'."""
    for name in LISTS:
        if any(rule_matches(rule, command) for rule in rows[name]):
            return name
    return "prompt"
