"""Unit tests for install.py and the tooling-install entry point.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'

Every test builds a throwaway source repo and a fabricated HOME under a
temporary directory: nothing here reads or writes the real ~/.claude tree,
the real ~/.local/libexec, or the network. Repo and cohort names are invented
fixtures, never this repo's real cohorts -- the point is the engine, not
one repo's manifest.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if __package__ in (None, ""):  # direct invocation: python3 lib/install_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gitw_test_support as fixture  # noqa: E402
from lib.install import (  # noqa: E402
    EXIT_REFUSED,
    EXIT_USAGE,
    RECEIPT_NAME,
    InstallError,
    apply,
    check_overlap,
    collect_sources,
    diff,
    excluded,
    load_config,
    read_receipt,
    recover,
    select_cohorts,
    target_for,
)

CLI = Path(__file__).resolve().parent.parent / "tooling-install"

MANIFEST = {
    "version": 1,
    "source_repo": "widget-kit",
    "exclude": ["__pycache__", "*.pyc", ".DS_Store", "*_test.py"],
    "cohorts": {
        "bin": {"kind": "bin", "sources": ["bin1", "bin2"], "exclude": ["skip-me.sh"]},
        "skills": {"kind": "skills", "sources": ["kits"], "exclude": ["beta/drop.md"]},
        "agents": {"kind": "agents", "sources": ["bots"]},
    },
}


def write(path: Path, text: str, executable: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


class InstallTestCase(unittest.TestCase):
    """Fixture base: a committed source repo plus an empty fabricated HOME."""

    manifest = MANIFEST

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tooling-install-test."))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.source = self.tmp / "widget-kit"
        self.source.mkdir()
        self.populate(self.source)
        self.commit_all()

    def populate(self, root: Path):
        write(root / "install.json", json.dumps(self.manifest, indent=2) + "\n")
        write(root / "bin1" / "tool-a", "#!/bin/sh\necho a\n", executable=True)
        write(root / "bin1" / "lib" / "helper.py", "VALUE = 1\n")
        write(root / "bin1" / "helper_test.py", "raise SystemExit('never ships')\n")
        write(root / "bin1" / "lib" / "__pycache__" / "helper.pyc", "bytecode")
        write(root / "bin2" / "tool-b.sh", "#!/bin/sh\necho b\n", executable=True)
        write(root / "bin2" / "skip-me.sh", "#!/bin/sh\nexit 1\n", executable=True)
        write(root / "kits" / "alpha" / "SKILL.md", "alpha\n")
        write(root / "kits" / "alpha" / "notes.md", "alpha notes\n")
        write(root / "kits" / "beta" / "SKILL.md", "beta\n")
        write(root / "kits" / "beta" / "drop.md", "never ships\n")
        write(root / "bots" / "one.md", "bot one\n")

    def commit_all(self, root: Path = None):
        root = root or self.source
        if not (root / ".git").exists():
            fixture.git(root, "init", "--initial-branch=main", ".")
        fixture.git(root, "add", "-A")
        fixture.git(root, "commit", "-m", "fixture", check=False)

    def targets(self):
        return {kind: target_for(kind, self.home) for kind in ("bin", "skills", "agents")}

    def install(self, **kwargs):
        return apply(self.source, home=self.home, **kwargs)

    def report(self):
        return diff(self.source, home=self.home)

    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(CLI), *arguments],
            env={**os.environ, "HOME": str(self.home)},
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=60,
        )


class ConfigTest(InstallTestCase):
    def test_parses_cohorts_with_shared_and_local_excludes(self):
        config = load_config(self.source)
        self.assertEqual(config.source_repo, "widget-kit")
        names = [cohort.name for cohort in config.cohorts]
        self.assertEqual(names, ["agents", "bin", "skills"])
        cohort = next(item for item in config.cohorts if item.name == "bin")
        self.assertEqual(cohort.sources, ("bin1", "bin2"))
        self.assertIn("skip-me.sh", cohort.excludes)
        self.assertIn("*_test.py", cohort.excludes)

    def test_missing_manifest_is_a_usage_error(self):
        (self.source / "install.json").unlink()
        with self.assertRaisesRegex(InstallError, "no install.json"):
            load_config(self.source)

    def test_wrong_version_refused(self):
        write(self.source / "install.json", json.dumps({"version": 99}))
        with self.assertRaisesRegex(InstallError, "version 99"):
            load_config(self.source)

    def test_two_cohorts_of_one_kind_refused(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["cohorts"]["extra"] = {"kind": "bin", "sources": ["bin1"]}
        write(self.source / "install.json", json.dumps(manifest))
        with self.assertRaisesRegex(InstallError, "both declare kind"):
            load_config(self.source)

    def test_unknown_kind_refused(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["cohorts"]["bin"]["kind"] = "sbin"
        write(self.source / "install.json", json.dumps(manifest))
        with self.assertRaisesRegex(InstallError, "expected one of"):
            load_config(self.source)

    def test_escaping_source_path_refused(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["cohorts"]["bin"]["sources"] = ["../elsewhere"]
        write(self.source / "install.json", json.dumps(manifest))
        with self.assertRaisesRegex(InstallError, "relative path inside"):
            load_config(self.source)


class ExcludeTest(unittest.TestCase):
    def test_basename_glob_matches_any_depth(self):
        self.assertTrue(excluded("lib/git/run_test.py", ["*_test.py"]))
        self.assertFalse(excluded("lib/git/run.py", ["*_test.py"]))

    def test_bare_name_matches_a_directory_component(self):
        self.assertTrue(excluded("a/__pycache__/b.pyc", ["__pycache__"]))

    def test_literal_path_matches_exactly(self):
        self.assertTrue(excluded("triage/handoff.md", ["triage/handoff.md"]))
        self.assertFalse(excluded("triage/handoff.md.bak", ["triage/handoff.md"]))

    def test_literal_directory_prefix_matches_contents(self):
        self.assertTrue(excluded("reference/scratch/x.py", ["reference/scratch"]))


class CollectTest(InstallTestCase):
    def cohort(self, name):
        return next(
            item for item in load_config(self.source).cohorts if item.name == name
        )

    def test_merges_two_source_dirs_preserving_inner_layout(self):
        files = collect_sources(self.source, self.cohort("bin"))
        self.assertEqual(
            sorted(files), ["lib/helper.py", "tool-a", "tool-b.sh"]
        )

    def test_excludes_tests_bytecode_and_named_files(self):
        files = collect_sources(self.source, self.cohort("bin"))
        self.assertNotIn("helper_test.py", files)
        self.assertNotIn("lib/__pycache__/helper.pyc", files)
        self.assertNotIn("skip-me.sh", files)

    def test_unit_cohort_keeps_unit_prefixes(self):
        files = collect_sources(self.source, self.cohort("skills"))
        self.assertEqual(
            sorted(files),
            ["alpha/SKILL.md", "alpha/notes.md", "beta/SKILL.md"],
        )

    def test_collision_between_source_dirs_refused(self):
        write(self.source / "bin2" / "tool-a", "#!/bin/sh\necho clash\n")
        with self.assertRaises(InstallError) as caught:
            collect_sources(self.source, self.cohort("bin"))
        self.assertEqual(caught.exception.exit_code, EXIT_REFUSED)
        self.assertIn("same target path", str(caught.exception))

    def test_loose_file_in_a_unit_cohort_refused(self):
        write(self.source / "kits" / "README.md", "loose\n")
        with self.assertRaisesRegex(InstallError, "only unit directories"):
            collect_sources(self.source, self.cohort("skills"))

    def test_missing_source_directory_refused(self):
        shutil.rmtree(self.source / "bin2")
        with self.assertRaisesRegex(InstallError, "not a directory"):
            collect_sources(self.source, self.cohort("bin"))


class TargetTest(InstallTestCase):
    def test_kinds_map_to_their_directories(self):
        self.assertEqual(
            target_for("bin", self.home),
            self.home / ".local" / "libexec" / "agent-tooling",
        )
        self.assertEqual(target_for("skills", self.home), self.home / ".claude" / "skills")
        self.assertEqual(target_for("agents", self.home), self.home / ".claude" / "agents")

    def test_unknown_kind_rejected(self):
        with self.assertRaisesRegex(InstallError, "unknown target kind"):
            target_for("sbin", self.home)


class OverlapTest(InstallTestCase):
    def refuses(self, source: Path, fragment: str):
        with self.assertRaises(InstallError) as caught:
            check_overlap(source, load_config(self.source), self.home)
        self.assertEqual(caught.exception.exit_code, EXIT_REFUSED)
        self.assertIn(fragment, str(caught.exception))

    def test_disjoint_source_and_targets_pass(self):
        check_overlap(self.source, load_config(self.source), self.home)

    def test_source_containing_a_target_refused(self):
        # The ~/.claude case: the checkout holds the skills and agents targets.
        self.refuses(self.home, "sits inside it")

    def test_source_equal_to_a_target_refused(self):
        target = target_for("agents", self.home)
        target.mkdir(parents=True)
        write(target / "install.json", json.dumps(self.manifest))
        self.refuses(target, "the agents target itself")

    def test_source_inside_a_target_refused(self):
        inner = target_for("skills", self.home) / "inner-checkout"
        inner.mkdir(parents=True)
        self.refuses(inner, "sits inside the skills target")


class DiffTest(InstallTestCase):
    def test_nothing_installed_reports_not_installed_for_every_cohort(self):
        report = self.report()
        self.assertEqual(report["status"], "drift")
        for cohort in report["cohorts"].values():
            self.assertEqual(cohort["status"], "not-installed")
            self.assertIsNone(cohort["installed_commit"])
        self.assertEqual(report["cohorts"]["bin"]["ships"], 3)
        self.assertEqual(report["cohorts"]["skills"]["ships"], 3)

    def test_after_apply_everything_is_in_sync(self):
        self.install()
        report = self.report()
        self.assertEqual(report["status"], "in-sync")
        self.assertEqual(
            sorted(item["status"] for item in report["cohorts"].values()),
            ["in-sync", "in-sync", "in-sync"],
        )
        self.assertEqual(
            report["cohorts"]["bin"]["installed_commit"], report["source_commit"]
        )

    def test_changed_source_file_shows_as_changed(self):
        self.install()
        write(self.source / "bin1" / "tool-a", "#!/bin/sh\necho edited\n")
        self.commit_all()
        report = self.report()
        self.assertEqual(report["cohorts"]["bin"]["changed"], ["tool-a"])
        self.assertEqual(report["status"], "drift")

    def test_dropped_source_file_shows_as_only_installed(self):
        self.install()
        (self.source / "bin1" / "lib" / "helper.py").unlink()
        self.commit_all()
        report = self.report()
        self.assertEqual(report["cohorts"]["bin"]["only_installed"], ["lib/helper.py"])

    def test_unowned_file_in_a_shipped_unit_is_reported_as_replaced(self):
        self.install()
        write(target_for("skills", self.home) / "alpha" / "stray.txt", "junk\n")
        write(target_for("skills", self.home) / "gamma" / "SKILL.md", "other\n")
        report = self.report()["cohorts"]["skills"]
        self.assertEqual(report["unowned_replaced"], ["alpha/stray.txt"])
        self.assertEqual(report["unowned_preserved"], ["gamma/SKILL.md"])
        # The replaced file is drift: installing would destroy it. The
        # preserved one, outside any shipped unit, is not touched and is not.
        self.assertEqual(report["status"], "drift")
        self.assertEqual(self.report()["status"], "drift")

    def test_unowned_content_outside_shipped_units_is_not_drift(self):
        self.install()
        write(target_for("skills", self.home) / "gamma" / "SKILL.md", "other\n")
        report = self.report()["cohorts"]["skills"]
        self.assertEqual(report["unowned_preserved"], ["gamma/SKILL.md"])
        self.assertEqual(report["unowned_replaced"], [])
        self.assertEqual(report["status"], "in-sync")

    def test_regenerated_bytecode_in_a_unit_is_not_unowned(self):
        # The bug this guards: a .pyc regenerated inside an installed skill
        # used to land in unowned_replaced, so every run reported something
        # it would destroy while still calling the cohort in-sync.
        self.install()
        alpha = target_for("skills", self.home) / "alpha"
        write(alpha / "__pycache__" / "mod.cpython-39.pyc", "bytecode")
        write(alpha / ".DS_Store", "finder junk")
        report = self.report()["cohorts"]["skills"]
        self.assertEqual(report["unowned_replaced"], [])
        self.assertEqual(report["unowned_preserved"], [])
        self.assertEqual(report["status"], "in-sync")

    def test_cohort_excludes_do_not_hide_target_content(self):
        # `beta/drop.md` is excluded from the *source* scan, so a copy sitting
        # in the target is a real hand-drop and must still be reported.
        self.install()
        write(target_for("skills", self.home) / "beta" / "drop.md", "dropped\n")
        report = self.report()["cohorts"]["skills"]
        self.assertEqual(report["unowned_replaced"], ["beta/drop.md"])
        self.assertEqual(report["status"], "drift")

    def test_unowned_file_in_a_merge_target_is_reported_as_preserved(self):
        self.install()
        write(target_for("bin", self.home) / "hand-drop", "local\n")
        report = self.report()["cohorts"]["bin"]
        self.assertEqual(report["unowned_preserved"], ["hand-drop"])
        self.assertEqual(report["unowned_replaced"], [])
        self.assertEqual(report["status"], "in-sync")

    def test_diff_does_not_create_or_modify_targets(self):
        self.report()
        self.assertFalse(target_for("bin", self.home).exists())
        self.assertFalse(target_for("skills", self.home).exists())


class ApplyTest(InstallTestCase):
    def test_installs_every_cohort_to_its_target(self):
        result = self.install()
        binary = target_for("bin", self.home)
        self.assertEqual((binary / "tool-a").read_text(), "#!/bin/sh\necho a\n")
        self.assertEqual((binary / "lib" / "helper.py").read_text(), "VALUE = 1\n")
        self.assertEqual((binary / "tool-b.sh").read_text(), "#!/bin/sh\necho b\n")
        self.assertFalse((binary / "helper_test.py").exists())
        self.assertFalse((binary / "skip-me.sh").exists())
        self.assertFalse((binary / "lib" / "__pycache__").exists())
        skills = target_for("skills", self.home)
        self.assertEqual((skills / "alpha" / "SKILL.md").read_text(), "alpha\n")
        self.assertFalse((skills / "beta" / "drop.md").exists())
        self.assertEqual((target_for("agents", self.home) / "one.md").read_text(), "bot one\n")
        self.assertEqual(result["cohorts"]["bin"]["installed"], 3)
        self.assertEqual(result["cohorts"]["skills"]["units"], ["alpha", "beta"])

    def test_executable_bit_survives(self):
        self.install()
        self.assertTrue(os.access(target_for("bin", self.home) / "tool-a", os.X_OK))
        self.assertFalse(
            os.access(target_for("bin", self.home) / "lib" / "helper.py", os.X_OK)
        )

    def test_receipt_records_commit_and_per_file_hashes(self):
        self.install()
        receipt = read_receipt(target_for("bin", self.home))
        record = receipt["sources"]["widget-kit"]
        self.assertEqual(record["kind"], "bin")
        self.assertEqual(record["source_path"], str(self.source.resolve()))
        self.assertRegex(record["source_commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(record["installed_at"], r"^\d{4}-\d\d-\d\dT")
        self.assertEqual(sorted(record["files"]), ["lib/helper.py", "tool-a", "tool-b.sh"])
        for value in record["files"].values():
            self.assertRegex(value, r"^sha256:[0-9a-f]{64}$")

    def test_skills_receipt_lists_units(self):
        self.install()
        record = read_receipt(target_for("skills", self.home))["sources"]["widget-kit"]
        self.assertEqual(record["units"], ["alpha", "beta"])

    def test_receipt_is_not_itself_installed_content(self):
        self.install()
        self.assertFalse((self.source / RECEIPT_NAME).exists())
        report = self.report()
        self.assertEqual(report["status"], "in-sync")

    def test_reapply_is_idempotent(self):
        self.install()
        first = read_receipt(target_for("bin", self.home))["sources"]["widget-kit"]
        self.install()
        second = read_receipt(target_for("bin", self.home))["sources"]["widget-kit"]
        self.assertEqual(first["files"], second["files"])
        self.assertEqual(self.report()["status"], "in-sync")

    def test_dropped_source_file_is_retired_from_the_target(self):
        self.install()
        (self.source / "bin1" / "lib" / "helper.py").unlink()
        self.commit_all()
        result = self.install()
        self.assertEqual(result["cohorts"]["bin"]["retired"], ["lib/helper.py"])
        self.assertFalse((target_for("bin", self.home) / "lib" / "helper.py").exists())

    def test_dropped_skill_unit_is_retired(self):
        self.install()
        shutil.rmtree(self.source / "kits" / "beta")
        self.commit_all()
        result = self.install()
        self.assertEqual(result["cohorts"]["skills"]["retired"], ["beta"])
        self.assertFalse((target_for("skills", self.home) / "beta").exists())
        self.assertTrue((target_for("skills", self.home) / "alpha").exists())

    def test_unowned_file_in_a_merge_target_survives_the_swap(self):
        self.install()
        write(target_for("bin", self.home) / "hand-drop", "local\n")
        self.install()
        self.assertEqual((target_for("bin", self.home) / "hand-drop").read_text(), "local\n")

    def test_unowned_file_inside_a_shipped_unit_does_not_survive(self):
        self.install()
        write(target_for("skills", self.home) / "alpha" / "stray.txt", "junk\n")
        self.install()
        self.assertFalse((target_for("skills", self.home) / "alpha" / "stray.txt").exists())

    def test_no_staging_or_retired_directories_are_left_behind(self):
        self.install()
        for target in self.targets().values():
            leftovers = [
                path.name
                for path in list(target.parent.iterdir()) + list(target.iterdir())
                if ".new-" in path.name or ".retired-" in path.name
            ]
            self.assertEqual(leftovers, [])


class SymlinkTest(InstallTestCase):
    """No source ever ships a symlink, so every symlink found in a target is
    unowned content -- reported like any other, and on a merge target carried
    through the swap as a link rather than silently eaten."""

    def link(self, path: Path, points_at: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(points_at)
        return path

    def test_symlink_in_a_merge_target_is_reported_as_preserved(self):
        self.install()
        self.link(target_for("bin", self.home) / "tool-local", "/usr/bin/true")
        report = self.report()["cohorts"]["bin"]
        self.assertEqual(report["unowned_preserved"], ["tool-local"])
        self.assertEqual(report["status"], "in-sync")

    def test_symlink_in_a_merge_target_survives_the_swap_as_a_symlink(self):
        self.install()
        target = target_for("bin", self.home)
        self.link(target / "tool-local", "/usr/bin/true")
        self.link(target / "nested" / "up", "../tool-a")
        result = self.install()
        self.assertIn("tool-local", result["cohorts"]["bin"]["preserved"])
        self.assertTrue((target / "tool-local").is_symlink())
        self.assertEqual(os.readlink(str(target / "tool-local")), "/usr/bin/true")
        self.assertTrue((target / "nested" / "up").is_symlink())
        self.assertEqual(os.readlink(str(target / "nested" / "up")), "../tool-a")

    def test_a_dangling_symlink_is_reported_and_carried(self):
        self.install()
        target = target_for("bin", self.home)
        self.link(target / "broken", "nowhere-at-all")
        self.assertEqual(self.report()["cohorts"]["bin"]["unowned_preserved"], ["broken"])
        self.install()
        self.assertTrue((target / "broken").is_symlink())

    def test_symlink_to_a_directory_is_one_entry_not_a_subtree(self):
        self.install()
        target = target_for("bin", self.home)
        outside = self.tmp / "outside"
        write(outside / "thing", "x\n")
        self.link(target / "linked-dir", str(outside))
        self.assertEqual(
            self.report()["cohorts"]["bin"]["unowned_preserved"], ["linked-dir"]
        )
        self.install()
        self.assertTrue((target / "linked-dir").is_symlink())
        self.assertEqual((outside / "thing").read_text(), "x\n")

    def test_symlink_inside_a_shipped_unit_is_replaced_and_is_drift(self):
        self.install()
        self.link(target_for("skills", self.home) / "alpha" / "link.md", "SKILL.md")
        report = self.report()["cohorts"]["skills"]
        self.assertEqual(report["unowned_replaced"], ["alpha/link.md"])
        self.assertEqual(report["status"], "drift")

    def test_symlink_where_a_shipped_file_belongs_is_drift_and_is_overwritten(self):
        self.install()
        target = target_for("bin", self.home)
        (target / "tool-a").unlink()
        self.link(target / "tool-a", "/usr/bin/true")
        report = self.report()["cohorts"]["bin"]
        self.assertEqual(report["changed"], ["tool-a"])
        self.assertEqual(report["status"], "drift")
        self.install()
        self.assertFalse((target / "tool-a").is_symlink())
        self.assertEqual((target / "tool-a").read_text(), "#!/bin/sh\necho a\n")


class CohortSelectionTest(InstallTestCase):
    """`--cohort` restricts a run to part of the manifest."""

    def test_no_selection_means_every_cohort(self):
        config = load_config(self.source)
        for argument in (None, []):
            self.assertEqual(
                [cohort.name for cohort in select_cohorts(config, argument)],
                ["agents", "bin", "skills"],
            )

    def test_unknown_cohort_is_a_usage_error(self):
        with self.assertRaises(InstallError) as caught:
            select_cohorts(load_config(self.source), ["bin", "nope"])
        self.assertEqual(caught.exception.exit_code, EXIT_USAGE)
        self.assertIn("unknown cohort(s) nope", str(caught.exception))

    def test_selection_is_deduplicated_and_ordered(self):
        names = select_cohorts(load_config(self.source), ["skills", "bin", "bin"])
        self.assertEqual([cohort.name for cohort in names], ["bin", "skills"])

    def test_apply_touches_only_the_selected_cohorts(self):
        result = self.install(cohorts=["bin"])
        self.assertEqual(result["selected_cohorts"], ["bin"])
        self.assertEqual(sorted(result["cohorts"]), ["bin"])
        self.assertTrue((target_for("bin", self.home) / "tool-a").exists())
        self.assertFalse(target_for("skills", self.home).exists())
        self.assertFalse(target_for("agents", self.home).exists())

    def test_diff_reports_only_the_selected_cohorts(self):
        self.install(cohorts=["bin"])
        report = diff(self.source, home=self.home, cohorts=["bin"])
        self.assertEqual(report["selected_cohorts"], ["bin"])
        self.assertEqual(sorted(report["cohorts"]), ["bin"])
        self.assertEqual(report["status"], "in-sync")
        # A full diff still sees the two cohorts nobody has installed.
        self.assertEqual(self.report()["status"], "drift")

    def test_a_selected_run_leaves_the_other_targets_receipts_alone(self):
        self.install()
        before = read_receipt(target_for("skills", self.home))
        write(self.source / "bin1" / "tool-a", "#!/bin/sh\necho edited\n")
        self.commit_all()
        self.install(cohorts=["bin"])
        self.assertEqual(read_receipt(target_for("skills", self.home)), before)

    def test_dirt_outside_the_selected_cohorts_does_not_refuse(self):
        write(self.source / "kits" / "alpha" / "extra.md", "uncommitted\n")
        result = self.install(cohorts=["bin"])
        self.assertFalse(result["source_commit"].endswith("-dirty"))
        with self.assertRaisesRegex(InstallError, "uncommitted changes"):
            self.install(cohorts=["skills"])

    def test_the_overlap_refusal_still_covers_unselected_cohorts(self):
        # The fabricated HOME holds the skills and agents targets; selecting
        # only bin must not switch that refusal off.
        write(self.home / "install.json", json.dumps(self.manifest))
        for name in ("bin1", "bin2", "kits", "bots"):
            shutil.copytree(self.source / name, self.home / name)
        with self.assertRaises(InstallError) as caught:
            apply(self.home, home=self.home, cohorts=["bin"])
        self.assertEqual(caught.exception.exit_code, EXIT_REFUSED)


class DirtySourceTest(InstallTestCase):
    def test_dirty_source_refused_without_force(self):
        write(self.source / "bin1" / "tool-c", "#!/bin/sh\necho c\n")
        with self.assertRaises(InstallError) as caught:
            self.install()
        self.assertEqual(caught.exception.exit_code, EXIT_REFUSED)
        self.assertIn("uncommitted changes", str(caught.exception))
        self.assertFalse(target_for("bin", self.home).exists())

    def test_force_installs_and_stamps_dirty(self):
        write(self.source / "bin1" / "tool-c", "#!/bin/sh\necho c\n")
        result = self.install(force=True)
        self.assertTrue(result["source_commit"].endswith("-dirty"))
        record = read_receipt(target_for("bin", self.home))["sources"]["widget-kit"]
        self.assertTrue(record["source_commit"].endswith("-dirty"))

    def test_changes_outside_the_shipping_tree_do_not_count_as_dirty(self):
        write(self.source / "README.md", "not shipped\n")
        result = self.install()
        self.assertFalse(result["source_commit"].endswith("-dirty"))

    def test_non_git_source_counts_as_dirty(self):
        shutil.rmtree(self.source / ".git")
        with self.assertRaisesRegex(InstallError, "uncommitted changes"):
            self.install()
        result = self.install(force=True)
        self.assertEqual(result["source_commit"], "unknown-dirty")


class MultiSourceTest(InstallTestCase):
    """Two source repos shipping into one target: the receipt keying's whole
    reason for existing."""

    def setUp(self):
        super().setUp()
        self.other = self.tmp / "gadget-kit"
        self.other.mkdir()
        manifest = {
            "version": 1,
            "source_repo": "gadget-kit",
            "exclude": ["*_test.py"],
            "cohorts": {
                "bin": {"kind": "bin", "sources": ["tools"]},
                "skills": {"kind": "skills", "sources": ["kits"]},
            },
        }
        write(self.other / "install.json", json.dumps(manifest, indent=2) + "\n")
        write(self.other / "tools" / "tool-z", "#!/bin/sh\necho z\n", executable=True)
        write(self.other / "kits" / "gamma" / "SKILL.md", "gamma\n")
        self.commit_all(self.other)

    def test_second_repo_leaves_the_first_repos_files_alone(self):
        self.install()
        apply(self.other, home=self.home)
        binary = target_for("bin", self.home)
        self.assertTrue((binary / "tool-a").exists())
        self.assertTrue((binary / "tool-z").exists())
        skills = target_for("skills", self.home)
        self.assertTrue((skills / "alpha" / "SKILL.md").exists())
        self.assertTrue((skills / "gamma" / "SKILL.md").exists())

    def test_receipt_keeps_one_record_per_source_repo(self):
        self.install()
        apply(self.other, home=self.home)
        receipt = read_receipt(target_for("bin", self.home))
        self.assertEqual(sorted(receipt["sources"]), ["gadget-kit", "widget-kit"])
        self.assertEqual(sorted(receipt["sources"]["gadget-kit"]["files"]), ["tool-z"])

    def test_each_repo_diffs_only_its_own_files(self):
        self.install()
        apply(self.other, home=self.home)
        report = self.report()["cohorts"]["bin"]
        self.assertEqual(report["status"], "in-sync")
        self.assertEqual(report["foreign_files"], ["tool-z"])
        self.assertEqual(report["only_installed"], [])

    def test_a_repo_reinstalling_does_not_retire_the_other_repos_files(self):
        self.install()
        apply(self.other, home=self.home)
        self.install()
        self.assertTrue((target_for("bin", self.home) / "tool-z").exists())

    def test_shipping_a_path_another_repo_owns_is_refused(self):
        self.install()
        apply(self.other, home=self.home)
        write(self.source / "bin1" / "tool-z", "#!/bin/sh\necho clash\n")
        self.commit_all()
        with self.assertRaises(InstallError) as caught:
            self.install()
        self.assertEqual(caught.exception.exit_code, EXIT_REFUSED)
        self.assertIn("another source repo", str(caught.exception))

    def test_shipping_a_unit_another_repo_owns_is_refused(self):
        self.install()
        apply(self.other, home=self.home)
        write(self.source / "kits" / "gamma" / "SKILL.md", "clash\n")
        self.commit_all()
        with self.assertRaisesRegex(InstallError, "already\n?\\s*installed by another"):
            self.install()


class TwoSourceFixture(InstallTestCase):
    """A cohort mid-migration between source repos. No tests of its own.

    `gadget-kit` ships exactly the bytes `widget-kit` already installed -- two
    of the three `bin` files and one of the two skill units -- so it can adopt
    them, and `widget-kit` keeps the rest.
    """

    def setUp(self):
        super().setUp()
        self.other = self.tmp / "gadget-kit"
        self.other.mkdir()
        manifest = {
            "version": 1,
            "source_repo": "gadget-kit",
            "exclude": ["__pycache__", "*.pyc", ".DS_Store", "*_test.py"],
            "cohorts": {
                "bin": {"kind": "bin", "sources": ["tools"]},
                "skills": {"kind": "skills", "sources": ["kits"]},
            },
        }
        write(self.other / "install.json", json.dumps(manifest, indent=2) + "\n")
        write(self.other / "tools" / "tool-a", "#!/bin/sh\necho a\n", executable=True)
        write(self.other / "tools" / "lib" / "helper.py", "VALUE = 1\n")
        write(self.other / "kits" / "alpha" / "SKILL.md", "alpha\n")
        write(self.other / "kits" / "alpha" / "notes.md", "alpha notes\n")
        self.commit_all(self.other)

    def install_other(self, **kwargs):
        return apply(self.other, home=self.home, **kwargs)

    def supersede(self, repo="widget-kit", **kwargs):
        return apply(self.other, home=self.home, supersedes=repo, **kwargs)

    def inspect(self, **kwargs):
        return diff(self.other, home=self.home, **kwargs)


class OwnershipTransferTest(TwoSourceFixture):
    """`apply` adopting byte-identical collisions, and refusing the rest."""

    # -- apply, merge target ------------------------------------------------

    def test_adopts_byte_identical_files(self):
        self.install()
        outcome = self.install_other()["cohorts"]["bin"]
        self.assertEqual(outcome["adopted"], ["lib/helper.py", "tool-a"])
        self.assertEqual(outcome["retired"], [])
        self.assertEqual(outcome["preserved"], ["tool-b.sh"])
        binary = target_for("bin", self.home)
        self.assertEqual((binary / "tool-a").read_text(), "#!/bin/sh\necho a\n")
        self.assertEqual((binary / "lib" / "helper.py").read_text(), "VALUE = 1\n")
        self.assertTrue((binary / "tool-b.sh").exists())

    def test_adoption_moves_the_files_between_receipt_records(self):
        self.install()
        self.install_other()
        receipt = read_receipt(target_for("bin", self.home))
        self.assertEqual(
            sorted(receipt["sources"]["gadget-kit"]["files"]),
            ["lib/helper.py", "tool-a"],
        )
        self.assertEqual(
            sorted(receipt["sources"]["widget-kit"]["files"]), ["tool-b.sh"]
        )

    def test_a_file_whose_content_differs_refuses(self):
        self.install()
        write(self.other / "tools" / "tool-a", "#!/bin/sh\necho different\n")
        self.commit_all(self.other)
        with self.assertRaises(InstallError) as caught:
            self.install_other(cohorts=["bin"])
        self.assertEqual(caught.exception.exit_code, EXIT_REFUSED)
        self.assertIn("different content", str(caught.exception))
        self.assertIn("tool-a", str(caught.exception))
        receipt = read_receipt(target_for("bin", self.home))
        self.assertEqual(sorted(receipt["sources"]), ["widget-kit"])

    def test_a_claimed_path_absent_from_the_target_refuses(self):
        """No installed copy, no evidence the two sources agree."""
        self.install()
        (target_for("bin", self.home) / "tool-a").unlink()
        with self.assertRaises(InstallError) as caught:
            self.install_other(cohorts=["bin"])
        self.assertEqual(caught.exception.exit_code, EXIT_REFUSED)
        self.assertIn("tool-a", str(caught.exception))

    # -- apply, unit target -------------------------------------------------

    def test_adopts_a_byte_identical_unit(self):
        self.install()
        outcome = self.install_other()["cohorts"]["skills"]
        self.assertEqual(outcome["adopted"], ["alpha"])
        self.assertEqual(outcome["retired"], [])
        self.assertEqual(outcome["foreign_units"], ["beta"])
        skills = target_for("skills", self.home)
        self.assertEqual((skills / "alpha" / "notes.md").read_text(), "alpha notes\n")
        self.assertTrue((skills / "beta" / "SKILL.md").exists())
        receipt = read_receipt(skills)
        self.assertEqual(receipt["sources"]["gadget-kit"]["units"], ["alpha"])
        self.assertEqual(receipt["sources"]["widget-kit"]["units"], ["beta"])
        self.assertEqual(
            sorted(receipt["sources"]["widget-kit"]["files"]), ["beta/SKILL.md"]
        )

    def test_a_unit_whose_content_differs_refuses(self):
        self.install()
        write(self.other / "kits" / "alpha" / "SKILL.md", "not alpha\n")
        self.commit_all(self.other)
        with self.assertRaises(InstallError) as caught:
            self.install_other(cohorts=["skills"])
        self.assertEqual(caught.exception.exit_code, EXIT_REFUSED)
        self.assertIn("alpha", str(caught.exception))
        self.assertEqual(
            (target_for("skills", self.home) / "alpha" / "SKILL.md").read_text(),
            "alpha\n",
        )

    def test_a_unit_that_drops_an_installed_file_refuses(self):
        """Partial match is not a match: the unit swap is wholesale."""
        self.install()
        (self.other / "kits" / "alpha" / "notes.md").unlink()
        self.commit_all(self.other)
        with self.assertRaises(InstallError) as caught:
            self.install_other(cohorts=["skills"])
        self.assertEqual(caught.exception.exit_code, EXIT_REFUSED)
        self.assertTrue(
            (target_for("skills", self.home) / "alpha" / "notes.md").exists()
        )

    def test_an_unowned_file_inside_the_unit_refuses(self):
        """Adopting would destroy the hand-drop, so it is a conflict."""
        self.install()
        write(target_for("skills", self.home) / "alpha" / "scratch.md", "by hand\n")
        with self.assertRaises(InstallError) as caught:
            self.install_other(cohorts=["skills"])
        self.assertEqual(caught.exception.exit_code, EXIT_REFUSED)
        self.assertTrue(
            (target_for("skills", self.home) / "alpha" / "scratch.md").exists()
        )

    # -- the receipt after the transfer -------------------------------------

    def test_a_record_adoption_empties_is_dropped(self):
        self.install()
        write(self.other / "kits" / "beta" / "SKILL.md", "beta\n")
        self.commit_all(self.other)
        self.install_other(cohorts=["skills"])
        receipt = read_receipt(target_for("skills", self.home))
        self.assertEqual(sorted(receipt["sources"]), ["gadget-kit"])
        self.assertEqual(
            sorted(receipt["sources"]["gadget-kit"]["units"]), ["alpha", "beta"]
        )

    def test_the_old_source_neither_retires_nor_reclaims_what_it_gave_up(self):
        self.install()
        self.install_other()
        (self.source / "bin1" / "tool-a").unlink()
        (self.source / "bin1" / "lib" / "helper.py").unlink()
        shutil.rmtree(self.source / "kits" / "alpha")
        self.commit_all()
        result = self.install()

        binary, skills = target_for("bin", self.home), target_for("skills", self.home)
        self.assertEqual(result["cohorts"]["bin"]["retired"], [])
        self.assertEqual(result["cohorts"]["bin"]["adopted"], [])
        self.assertEqual(
            result["cohorts"]["bin"]["preserved"], ["lib/helper.py", "tool-a"]
        )
        self.assertEqual(result["cohorts"]["skills"]["retired"], [])
        self.assertEqual(result["cohorts"]["skills"]["adopted"], [])
        self.assertTrue((binary / "tool-a").exists())
        self.assertTrue((binary / "lib" / "helper.py").exists())
        self.assertTrue((skills / "alpha" / "SKILL.md").exists())
        self.assertEqual(
            sorted(read_receipt(binary)["sources"]["gadget-kit"]["files"]),
            ["lib/helper.py", "tool-a"],
        )
        self.assertEqual(
            sorted(read_receipt(binary)["sources"]["widget-kit"]["files"]),
            ["tool-b.sh"],
        )
        self.assertEqual(
            read_receipt(skills)["sources"]["widget-kit"]["units"], ["beta"]
        )

    def test_the_old_source_adopts_back_while_it_still_ships_them(self):
        """Ownership ping-pongs until the old source stops shipping the
        content; sequencing that is the migration's job, not the installer's."""
        self.install()
        self.install_other()
        report = self.report()["cohorts"]["bin"]
        self.assertEqual(report["adoptable"], ["lib/helper.py", "tool-a"])
        self.assertEqual(report["status"], "drift")

    # -- diff ---------------------------------------------------------------

    def test_diff_classifies_collisions_on_a_merge_target(self):
        self.install()
        report = self.inspect()["cohorts"]["bin"]
        self.assertEqual(report["adoptable"], ["lib/helper.py", "tool-a"])
        self.assertEqual(report["conflicting"], [])
        self.assertEqual(report["foreign_files"], ["tool-b.sh"])
        self.assertEqual(report["only_in_source"], [])
        self.assertEqual(report["changed"], [])
        self.assertEqual(report["status"], "drift")

    def test_diff_reports_a_conflicting_collision(self):
        self.install()
        write(self.other / "tools" / "tool-a", "#!/bin/sh\necho different\n")
        self.commit_all(self.other)
        report = self.inspect()["cohorts"]["bin"]
        self.assertEqual(report["adoptable"], ["lib/helper.py"])
        self.assertEqual(report["conflicting"], ["tool-a"])
        self.assertEqual(report["status"], "drift")

    def test_diff_classifies_collisions_on_a_unit_target(self):
        self.install()
        report = self.inspect()["cohorts"]["skills"]
        self.assertEqual(report["adoptable"], ["alpha"])
        self.assertEqual(report["conflicting"], [])
        self.assertEqual(report["foreign_units"], ["beta"])
        self.assertEqual(report["foreign_files"], ["beta/SKILL.md"])
        self.assertEqual(report["status"], "drift")

    def test_diff_is_in_sync_once_the_transfer_has_happened(self):
        self.install()
        self.install_other()
        report = self.inspect()["cohorts"]
        self.assertEqual(report["bin"]["status"], "in-sync")
        self.assertEqual(report["bin"]["adoptable"], [])
        self.assertEqual(report["skills"]["status"], "in-sync")

    # -- exit codes ---------------------------------------------------------

    def test_cli_diff_exits_1_on_an_adoptable_collision(self):
        self.install()
        result = self.run_cli("diff", str(self.other), "--cohort", "bin")
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)["cohorts"]["bin"]
        self.assertEqual(report["adoptable"], ["lib/helper.py", "tool-a"])

    def test_cli_apply_exits_4_on_a_conflicting_collision(self):
        self.install()
        write(self.other / "tools" / "tool-a", "#!/bin/sh\necho different\n")
        self.commit_all(self.other)
        result = self.run_cli("apply", str(self.other), "--cohort", "bin")
        self.assertEqual(result.returncode, 4)
        self.assertIn("different content", result.stderr)


class SupersedeTest(TwoSourceFixture):
    """`adopt`: the declared migration, where the new owner's content wins.

    The shape this exists for is a repo that rewrites content as it takes a
    cohort over, so byte-identity can never authorise the transfer.
    """

    def build_third(self) -> Path:
        """A third source repo, whose ownership `adopt widget-kit` may not take."""
        third = self.tmp / "sprocket-kit"
        third.mkdir()
        manifest = {
            "version": 1,
            "source_repo": "sprocket-kit",
            "exclude": ["__pycache__", "*.pyc", "*_test.py"],
            "cohorts": {"bin": {"kind": "bin", "sources": ["tools"]}},
        }
        write(third / "install.json", json.dumps(manifest, indent=2) + "\n")
        write(third / "tools" / "tool-s", "#!/bin/sh\necho sprocket\n")
        self.commit_all(third)
        return third

    # -- the transfer -------------------------------------------------------

    def test_adopts_a_superseded_file_whose_content_differs(self):
        self.install()
        write(self.other / "tools" / "tool-a", "#!/bin/sh\necho rewritten\n")
        self.commit_all(self.other)
        outcome = self.supersede(cohorts=["bin"])["cohorts"]["bin"]
        self.assertEqual(outcome["adopted"], ["lib/helper.py", "tool-a"])
        binary = target_for("bin", self.home)
        self.assertEqual((binary / "tool-a").read_text(), "#!/bin/sh\necho rewritten\n")
        self.assertTrue((binary / "tool-b.sh").exists())
        receipt = read_receipt(binary)
        self.assertEqual(
            sorted(receipt["sources"]["gadget-kit"]["files"]),
            ["lib/helper.py", "tool-a"],
        )
        self.assertEqual(
            sorted(receipt["sources"]["widget-kit"]["files"]), ["tool-b.sh"]
        )

    def test_adopts_a_superseded_unit_whose_content_differs(self):
        self.install()
        write(self.other / "kits" / "alpha" / "SKILL.md", "rewritten alpha\n")
        self.commit_all(self.other)
        outcome = self.supersede(cohorts=["skills"])["cohorts"]["skills"]
        self.assertEqual(outcome["adopted"], ["alpha"])
        skills = target_for("skills", self.home)
        self.assertEqual(
            (skills / "alpha" / "SKILL.md").read_text(), "rewritten alpha\n"
        )
        self.assertTrue((skills / "beta" / "SKILL.md").exists())
        receipt = read_receipt(skills)
        self.assertEqual(receipt["sources"]["gadget-kit"]["units"], ["alpha"])
        self.assertEqual(receipt["sources"]["widget-kit"]["units"], ["beta"])

    def test_a_superseded_unit_may_drop_a_file_the_target_holds(self):
        """The unit swap stays wholesale; the new owner's copy is the unit."""
        self.install()
        (self.other / "kits" / "alpha" / "notes.md").unlink()
        self.commit_all(self.other)
        self.supersede(cohorts=["skills"])
        skills = target_for("skills", self.home)
        self.assertTrue((skills / "alpha" / "SKILL.md").exists())
        self.assertFalse((skills / "alpha" / "notes.md").exists())

    def test_byte_identical_content_adopts_the_same_way(self):
        self.install()
        outcome = self.supersede()["cohorts"]
        self.assertEqual(outcome["bin"]["adopted"], ["lib/helper.py", "tool-a"])
        self.assertEqual(outcome["skills"]["adopted"], ["alpha"])
        self.assertEqual(
            (target_for("bin", self.home) / "tool-a").read_text(), "#!/bin/sh\necho a\n"
        )

    def test_a_second_adopt_is_a_converged_no_op(self):
        self.install()
        self.supersede()
        outcome = self.supersede()["cohorts"]
        self.assertEqual(outcome["bin"]["adopted"], [])
        self.assertEqual(outcome["skills"]["adopted"], [])
        self.assertTrue((target_for("bin", self.home) / "tool-a").exists())

    def test_the_result_names_the_superseded_repo(self):
        self.install()
        self.assertEqual(self.supersede(cohorts=["bin"])["supersedes"], "widget-kit")
        self.assertNotIn("supersedes", self.install())

    # -- what adopt still refuses -------------------------------------------

    def test_a_collision_with_an_unnamed_repo_still_refuses(self):
        self.install()
        apply(self.build_third(), home=self.home, cohorts=["bin"])
        write(self.other / "tools" / "tool-s", "#!/bin/sh\necho gadget\n")
        write(self.other / "tools" / "tool-a", "#!/bin/sh\necho rewritten\n")
        self.commit_all(self.other)
        with self.assertRaises(InstallError) as caught:
            self.supersede(cohorts=["bin"])
        self.assertEqual(caught.exception.exit_code, EXIT_REFUSED)
        self.assertIn("tool-s", str(caught.exception))
        self.assertNotIn("tool-a", str(caught.exception))
        self.assertIn("other than 'widget-kit'", str(caught.exception))
        binary = target_for("bin", self.home)
        self.assertEqual(
            (binary / "tool-s").read_text(), "#!/bin/sh\necho sprocket\n"
        )
        self.assertEqual(
            sorted(read_receipt(binary)["sources"]["sprocket-kit"]["files"]),
            ["tool-s"],
        )

    def test_an_unknown_superseded_repo_is_a_usage_error(self):
        self.install()
        with self.assertRaises(InstallError) as caught:
            self.supersede(repo="nonesuch", cohorts=["bin"])
        self.assertEqual(caught.exception.exit_code, EXIT_USAGE)
        self.assertIn("nonesuch", str(caught.exception))
        self.assertIn("widget-kit", str(caught.exception))

    def test_superseding_with_no_receipt_at_all_is_a_usage_error(self):
        with self.assertRaises(InstallError) as caught:
            self.supersede(cohorts=["bin"])
        self.assertEqual(caught.exception.exit_code, EXIT_USAGE)
        self.assertIn("no other source repo", str(caught.exception))

    def test_the_superseded_repo_must_appear_in_a_selected_target(self):
        """Scope is per run: a record in an unselected target does not count."""
        self.install(cohorts=["skills"])
        with self.assertRaises(InstallError) as caught:
            self.supersede(cohorts=["bin"])
        self.assertEqual(caught.exception.exit_code, EXIT_USAGE)

    def test_superseding_your_own_repo_is_a_usage_error(self):
        self.install()
        with self.assertRaises(InstallError) as caught:
            self.supersede(repo="gadget-kit", cohorts=["bin"])
        self.assertEqual(caught.exception.exit_code, EXIT_USAGE)
        self.assertIn("own repo label", str(caught.exception))

    def test_a_dirty_source_still_refuses_without_force(self):
        self.install()
        write(self.other / "tools" / "tool-a", "#!/bin/sh\necho uncommitted\n")
        with self.assertRaisesRegex(InstallError, "uncommitted changes"):
            self.supersede(cohorts=["bin"])
        result = self.supersede(cohorts=["bin"], force=True)
        self.assertTrue(result["source_commit"].endswith("-dirty"))
        self.assertEqual(result["cohorts"]["bin"]["adopted"], ["lib/helper.py", "tool-a"])

    # -- the receipt afterwards ---------------------------------------------

    def test_a_record_adopt_empties_is_dropped(self):
        self.install()
        write(self.other / "kits" / "alpha" / "SKILL.md", "rewritten alpha\n")
        write(self.other / "kits" / "beta" / "SKILL.md", "rewritten beta\n")
        self.commit_all(self.other)
        self.supersede(cohorts=["skills"])
        receipt = read_receipt(target_for("skills", self.home))
        self.assertEqual(sorted(receipt["sources"]), ["gadget-kit"])
        self.assertEqual(
            sorted(receipt["sources"]["gadget-kit"]["units"]), ["alpha", "beta"]
        )

    def test_the_old_source_neither_retires_nor_reclaims_after_adopt(self):
        self.install()
        write(self.other / "tools" / "tool-a", "#!/bin/sh\necho rewritten\n")
        write(self.other / "kits" / "alpha" / "SKILL.md", "rewritten alpha\n")
        self.commit_all(self.other)
        self.supersede()

        (self.source / "bin1" / "tool-a").unlink()
        (self.source / "bin1" / "lib" / "helper.py").unlink()
        shutil.rmtree(self.source / "kits" / "alpha")
        self.commit_all()
        result = self.install()

        binary, skills = target_for("bin", self.home), target_for("skills", self.home)
        self.assertEqual(result["cohorts"]["bin"]["retired"], [])
        self.assertEqual(result["cohorts"]["bin"]["adopted"], [])
        self.assertEqual(result["cohorts"]["skills"]["retired"], [])
        self.assertEqual(result["cohorts"]["skills"]["adopted"], [])
        self.assertEqual((binary / "tool-a").read_text(), "#!/bin/sh\necho rewritten\n")
        self.assertEqual(
            (skills / "alpha" / "SKILL.md").read_text(), "rewritten alpha\n"
        )
        self.assertEqual(
            sorted(read_receipt(binary)["sources"]["widget-kit"]["files"]),
            ["tool-b.sh"],
        )

    # -- diff as adopt's dry run --------------------------------------------

    def test_diff_separates_what_a_unit_swap_would_destroy(self):
        """Two kinds of casualty inside one adopted unit, plus a bystander.

        `gadget-kit` ships `alpha` without the `notes.md` that `widget-kit`
        put there, so the wholesale swap deletes a file the superseded record
        owns -- which `foreign_files` alone could not tell apart from a
        foreign file in a unit nobody is touching.
        """
        self.install()
        (self.other / "kits" / "alpha" / "notes.md").unlink()
        self.commit_all(self.other)
        write(target_for("skills", self.home) / "alpha" / "scratch.md", "by hand\n")

        report = self.inspect()["cohorts"]["skills"]
        self.assertEqual(report["foreign_replaced"], ["alpha/notes.md"])
        self.assertEqual(report["unowned_replaced"], ["alpha/scratch.md"])
        self.assertEqual(report["foreign_files"], ["beta/SKILL.md"])
        self.assertEqual(report["conflicting"], ["alpha"])
        self.assertEqual(report["status"], "drift")

    def test_adopt_destroys_exactly_what_diff_named(self):
        self.install()
        (self.other / "kits" / "alpha" / "notes.md").unlink()
        self.commit_all(self.other)
        skills = target_for("skills", self.home)
        write(skills / "alpha" / "scratch.md", "by hand\n")

        self.supersede(cohorts=["skills"])
        self.assertFalse((skills / "alpha" / "notes.md").exists())
        self.assertFalse((skills / "alpha" / "scratch.md").exists())
        self.assertTrue((skills / "alpha" / "SKILL.md").exists())
        self.assertTrue((skills / "beta" / "SKILL.md").exists())

    def test_an_untouched_unit_keeps_its_files_off_the_risk_lists(self):
        """The foreign categories partition; nothing is double-counted."""
        self.install()
        report = self.inspect()["cohorts"]["skills"]
        self.assertEqual(report["adoptable"], ["alpha"])
        self.assertEqual(report["foreign_replaced"], [])
        self.assertEqual(report["unowned_replaced"], [])
        self.assertEqual(report["foreign_files"], ["beta/SKILL.md"])

    def test_a_merge_cohort_reports_no_foreign_replaced(self):
        """Nothing is destroyed on a merge target: foreign files carry through."""
        self.install()
        self.assertNotIn("foreign_replaced", self.inspect()["cohorts"]["bin"])

    # -- the entry point ----------------------------------------------------

    def test_cli_adopt_transfers_differing_content(self):
        self.install()
        write(self.other / "tools" / "tool-a", "#!/bin/sh\necho rewritten\n")
        self.commit_all(self.other)
        result = self.run_cli("adopt", str(self.other), "widget-kit", "--cohort", "bin")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["action"], "applied")
        self.assertEqual(payload["supersedes"], "widget-kit")
        self.assertEqual(
            payload["cohorts"]["bin"]["adopted"], ["lib/helper.py", "tool-a"]
        )

    def test_cli_adopt_without_a_superseded_repo_is_a_usage_error(self):
        result = self.run_cli("adopt", str(self.other))
        self.assertEqual(result.returncode, 2)
        self.assertIn("supersedes", result.stderr)

    def test_cli_adopt_rejects_an_option_where_the_repo_belongs(self):
        result = self.run_cli("adopt", str(self.other), "--cohort", "bin")
        self.assertEqual(result.returncode, 2)

    def test_cli_adopt_exits_2_on_an_unknown_superseded_repo(self):
        self.install()
        result = self.run_cli("adopt", str(self.other), "nonesuch", "--cohort", "bin")
        self.assertEqual(result.returncode, 2)
        self.assertIn("nonesuch", result.stderr)


class RecoveryTest(InstallTestCase):
    """The two-rename swap is not atomic; a crash between the renames leaves
    the target missing and a retired copy beside it."""

    def crash(self, target: Path, pid: int = 9999) -> Path:
        retired = target.parent / f"{target.name}.retired-{pid}"
        target.rename(retired)
        return retired

    def test_restores_a_target_a_crash_left_missing(self):
        self.install()
        target = target_for("bin", self.home)
        retired = self.crash(target)
        actions = recover(target.parent, {target.name})
        self.assertTrue(target.is_dir())
        self.assertFalse(retired.exists())
        self.assertEqual(actions[0]["restored"], str(target))

    def test_discards_a_retired_copy_when_the_target_is_present(self):
        self.install()
        target = target_for("bin", self.home)
        retired = target.parent / f"{target.name}.retired-9999"
        shutil.copytree(target, retired)
        actions = recover(target.parent, {target.name})
        self.assertFalse(retired.exists())
        self.assertTrue(target.is_dir())
        self.assertEqual(actions, [{"discarded": retired.name}])

    def test_discards_abandoned_staging_directories(self):
        self.install()
        target = target_for("bin", self.home)
        staging = target.parent / f"{target.name}.new-9999"
        staging.mkdir()
        recover(target.parent, {target.name})
        self.assertFalse(staging.exists())

    def test_two_retired_copies_are_a_human_decision(self):
        self.install()
        target = target_for("bin", self.home)
        self.crash(target, 9999)
        shutil.copytree(
            target.parent / f"{target.name}.retired-9999",
            target.parent / f"{target.name}.retired-8888",
        )
        with self.assertRaises(InstallError) as caught:
            recover(target.parent, {target.name})
        self.assertEqual(caught.exception.exit_code, EXIT_REFUSED)
        self.assertIn("a human must pick", str(caught.exception))

    def test_apply_recovers_before_installing(self):
        self.install()
        target = target_for("bin", self.home)
        self.crash(target)
        result = self.install()
        self.assertTrue((target / "tool-a").exists())
        self.assertEqual(result["recovered"][0]["restored"], str(target))
        self.assertEqual(self.report()["status"], "in-sync")

    def test_apply_recovers_a_crashed_skill_unit(self):
        self.install()
        unit = target_for("skills", self.home) / "alpha"
        self.crash(unit)
        result = self.install()
        self.assertTrue((unit / "SKILL.md").exists())
        self.assertEqual(result["recovered"][0]["restored"], str(unit))

    def test_diff_reports_a_pending_recovery_without_performing_it(self):
        self.install()
        target = target_for("bin", self.home)
        retired = self.crash(target)
        report = self.report()
        self.assertIn(retired.name, report["recovery_pending"])
        self.assertTrue(retired.is_dir())
        self.assertFalse(target.exists())


class CommandLineTest(InstallTestCase):
    """The entry point's argument handling and exit-code contract."""

    def test_diff_exits_1_when_nothing_is_installed(self):
        result = self.run_cli("diff", str(self.source))
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "drift")
        self.assertEqual(report["source_repo"], "widget-kit")

    def test_diff_exits_0_once_in_sync(self):
        self.install()
        result = self.run_cli("diff", str(self.source))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "in-sync")

    def test_apply_emits_an_applied_plan(self):
        result = self.run_cli("apply", str(self.source))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["action"], "applied")

    def test_missing_source_argument_is_a_usage_error(self):
        result = self.run_cli("diff")
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_unknown_command_is_a_usage_error(self):
        result = self.run_cli("install", str(self.source))
        self.assertEqual(result.returncode, 2)

    def test_cohort_flag_restricts_the_run(self):
        result = self.run_cli("apply", str(self.source), "--cohort", "bin")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["selected_cohorts"], ["bin"])
        self.assertFalse(target_for("skills", self.home).exists())

    def test_repeated_cohort_flags_accumulate(self):
        result = self.run_cli(
            "apply", str(self.source), "--cohort", "skills", "--cohort=agents"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout)["selected_cohorts"], ["agents", "skills"]
        )

    def test_diff_of_one_installed_cohort_exits_0_while_the_rest_are_missing(self):
        self.run_cli("apply", str(self.source), "--cohort", "bin")
        result = self.run_cli("diff", str(self.source), "--cohort", "bin")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "in-sync")
        self.assertEqual(self.run_cli("diff", str(self.source)).returncode, 1)

    def test_unknown_cohort_exits_2(self):
        result = self.run_cli("diff", str(self.source), "--cohort", "nope")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("unknown cohort(s) nope", result.stderr)

    def test_cohort_without_a_name_is_a_usage_error(self):
        result = self.run_cli("diff", str(self.source), "--cohort")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--cohort needs a cohort name", result.stderr)

    def test_force_on_diff_is_a_usage_error(self):
        result = self.run_cli("diff", str(self.source), "--force")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--force applies to apply", result.stderr)

    def test_nonexistent_source_is_a_usage_error(self):
        result = self.run_cli("diff", str(self.tmp / "nowhere"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("is not a directory", result.stderr)

    def test_source_containing_a_target_is_refused_with_4(self):
        write(self.home / "install.json", json.dumps(self.manifest))
        for name in ("bin1", "bin2", "kits", "bots"):
            shutil.copytree(self.source / name, self.home / name)
        result = self.run_cli("diff", str(self.home))
        self.assertEqual(result.returncode, EXIT_REFUSED, result.stdout)
        self.assertIn("sits inside it", result.stderr)

    def test_help_exits_0(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("tooling-install", result.stdout)


if __name__ == "__main__":
    unittest.main()
