"""Tests for lib.git.repo: workspace verification and read primitives,
against real throwaway repos (offline; file-path remotes only).

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import gitw_test_support
from lib import plan
from lib.git import repo, run
from lib.git.roster import Entry


class _FixtureTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp, ignore_errors=True)
        self.base = Path(temp).resolve()
        self.remote, self.seed, self.clone = (
            gitw_test_support.make_remote_and_clone(self.base)
        )
        self.entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            default_branch="main",
        )


class ResolveWorkspaceTest(_FixtureTest):
    def test_cwd_in_checkout_resolves_in_repo(self):
        workspace = repo.resolve_workspace(self.entry, self.clone)
        self.assertTrue(workspace.in_repo)
        self.assertEqual(workspace.root, self.clone.resolve())

    def test_cwd_in_subdirectory_resolves_to_toplevel(self):
        subdirectory = self.clone / "nested" / "deeper"
        subdirectory.mkdir(parents=True)
        workspace = repo.resolve_workspace(self.entry, subdirectory)
        self.assertEqual(workspace.root, self.clone.resolve())

    def test_cwd_in_linked_worktree_resolves_via_common_dir(self):
        gitw_test_support.git(
            self.clone, "worktree", "add", str(self.base / "wt"), "-b", "fix/wt"
        )
        workspace = repo.resolve_workspace(self.entry, self.base / "wt")
        self.assertTrue(workspace.in_repo)
        self.assertEqual(workspace.root, (self.base / "wt").resolve())

    def test_unregistered_clone_is_refused_despite_matching_url(self):
        gitw_test_support.git(self.base, "clone", str(self.remote), "rogue")
        with self.assertRaises(repo.RefusalError) as caught:
            repo.resolve_workspace(self.entry, self.base / "rogue")
        self.assertIn("not inside the registered checkout", str(caught.exception))

    def test_cwd_outside_any_repo_is_refused(self):
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        with self.assertRaises(repo.RefusalError):
            repo.resolve_workspace(self.entry, elsewhere)

    def test_operable_from_admits_foreign_cwd_as_out_of_repo(self):
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            operable_from=(elsewhere,),
        )
        workspace = repo.resolve_workspace(entry, elsewhere)
        self.assertFalse(workspace.in_repo)
        self.assertEqual(workspace.root, self.clone.resolve())


class VerifyRemoteTest(_FixtureTest):
    def test_matching_remote_passes(self):
        workspace = repo.resolve_workspace(self.entry, self.clone)
        repo.verify_remote(workspace)  # must not raise

    def test_url_mismatch_is_refused(self):
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url="ssh://forge.example.com/own/other.git",
            remote="origin",
        )
        workspace = repo.resolve_workspace(entry, self.clone)
        with self.assertRaises(repo.RefusalError) as caught:
            repo.verify_remote(workspace)
        self.assertIn("not the blessed one", str(caught.exception))

    def test_git_suffix_and_trailing_slash_normalize(self):
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote)[: -len(".git")] + "/",
            remote="origin",
        )
        workspace = repo.resolve_workspace(entry, self.clone)
        repo.verify_remote(workspace)  # must not raise

    def test_missing_remote_name_is_refused(self):
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="upstream",
        )
        workspace = repo.resolve_workspace(entry, self.clone)
        with self.assertRaises(repo.RefusalError) as caught:
            repo.verify_remote(workspace)
        self.assertIn("'upstream'", str(caught.exception))

    def test_stale_roster_checkout_is_a_deployment_error(self):
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        stale = self.base / "gone"
        stale.mkdir()
        entry = Entry(
            label="proj", checkout=stale, operable_from=(elsewhere,)
        )
        workspace = repo.resolve_workspace(entry, elsewhere)
        with self.assertRaises(run.GitError) as caught:
            repo.verify_remote(workspace)
        self.assertEqual(caught.exception.exit_code, plan.EXIT_AUTH)


class ReadPrimitivesTest(_FixtureTest):
    def test_branch_commit_and_upstream(self):
        self.assertEqual(repo.current_branch(self.clone), "main")
        self.assertEqual(repo.upstream_of(self.clone, "main"), "origin/main")
        commit = repo.head_commit(self.clone)
        self.assertIsNotNone(commit)
        self.assertEqual(len(commit), 40)

    def test_detached_head_has_no_branch(self):
        gitw_test_support.git(self.clone, "switch", "--detach")
        self.assertIsNone(repo.current_branch(self.clone))
        self.assertIsNotNone(repo.head_commit(self.clone))

    def test_ahead_behind_counts(self):
        gitw_test_support.commit_on(
            self.clone, "local.txt", "local\n", "local commit"
        )
        gitw_test_support.advance_remote(self.seed)
        gitw_test_support.git(self.clone, "fetch", "origin")
        self.assertEqual(
            repo.ahead_behind(self.clone, "HEAD", "refs/remotes/origin/main"),
            (1, 1),
        )

    def test_ahead_behind_with_missing_base_is_none(self):
        self.assertIsNone(
            repo.ahead_behind(self.clone, "HEAD", "refs/heads/nope")
        )

    def test_status_counts_tally_each_class(self):
        (self.clone / "untracked.txt").write_text("u\n")
        (self.clone / "README.md").write_text("modified\n")
        (self.clone / "staged.txt").write_text("s\n")
        gitw_test_support.git(self.clone, "add", "staged.txt")
        self.assertEqual(
            repo.status_counts(self.clone),
            {"staged": 1, "unstaged": 1, "untracked": 1},
        )

    def test_status_counts_handle_renames(self):
        gitw_test_support.git(self.clone, "mv", "README.md", "RENAMED.md")
        counts = repo.status_counts(self.clone)
        self.assertEqual(counts["staged"], 1)
        self.assertEqual(counts["untracked"], 0)

    def test_status_counts_handle_worktree_side_renames(self):
        # ` R new\0old\0`: the rename marker in the *worktree* column,
        # index column a space -- the origin-path field must still be
        # consumed or it miscounts as a record of its own.
        gitw_test_support.commit_on(
            self.clone, "old.txt",
            "same content that is long enough to match\n", "add old",
        )
        (self.clone / "old.txt").rename(self.clone / "new.txt")
        gitw_test_support.git(self.clone, "add", "-N", "new.txt")
        self.assertEqual(
            repo.status_counts(self.clone),
            {"staged": 0, "unstaged": 1, "untracked": 0},
        )

    def test_clean_tree_is_all_zero(self):
        self.assertEqual(
            repo.status_counts(self.clone),
            {"staged": 0, "unstaged": 0, "untracked": 0},
        )

    def test_worktree_holding_branch(self):
        gitw_test_support.git(
            self.clone, "worktree", "add", str(self.base / "wt"), "-b", "fix/wt"
        )
        holder = repo.worktree_holding_branch(self.clone, "fix/wt")
        self.assertEqual(holder, (self.base / "wt").resolve())
        self.assertIsNone(repo.worktree_holding_branch(self.clone, "fix/other"))

    def test_status_entries_limit_to_pathspecs(self):
        (self.clone / "one.txt").write_text("1\n")
        (self.clone / "two.txt").write_text("2\n")
        entries = repo.status_entries(self.clone, ("one.txt",))
        self.assertEqual([path for _, _, path in entries], ["one.txt"])

    def test_status_entries_list_nested_untracked_files_individually(self):
        nested = self.clone / "nest"
        nested.mkdir()
        (nested / "hidden.txt").write_text("h\n")
        entries = repo.status_entries(self.clone)
        self.assertEqual(
            [path for _, _, path in entries], ["nest/hidden.txt"]
        )

    def test_require_prefixed_branch(self):
        gitw_test_support.git(self.clone, "switch", "-c", "fix/topic")
        self.assertEqual(
            repo.require_prefixed_branch(self.clone, "fix/", "proj", "main"),
            "fix/topic",
        )
        with self.assertRaises(repo.RefusalError):
            repo.require_prefixed_branch(self.clone, "docs/", "proj", "main")
        gitw_test_support.git(self.clone, "switch", "--detach")
        with self.assertRaises(repo.RefusalError):
            repo.require_prefixed_branch(self.clone, "fix/", "proj", "main")

    def test_prefix_alone_is_not_a_matching_branch(self):
        # A branch literally named like the prefix minus the slash must
        # not pass; nor would an empty tail.
        gitw_test_support.git(self.clone, "switch", "-c", "fixation")
        with self.assertRaises(repo.RefusalError):
            repo.require_prefixed_branch(self.clone, "fix/", "proj", "main")

    def test_bare_slash_admits_any_branch_but_the_default(self):
        gitw_test_support.git(self.clone, "switch", "-c", "foo-bar")
        self.assertEqual(
            repo.require_prefixed_branch(self.clone, "/", "proj", "main"),
            "foo-bar",
        )
        gitw_test_support.git(self.clone, "switch", "main")
        with self.assertRaisesRegex(repo.RefusalError, "default branch"):
            repo.require_prefixed_branch(self.clone, "/", "proj", "main")

    def test_bare_slash_refuses_a_case_variant_of_the_default(self):
        # On a case-insensitive filesystem 'Main' is the same ref as
        # 'main'; the guard must not depend on the filesystem.
        with self.assertRaisesRegex(repo.RefusalError, "default branch"):
            repo.require_branch_in_scope("Main", "/", "proj", "main")

    def test_current_branch_ignores_a_tag_named_like_the_branch(self):
        # `symbolic-ref --short` would answer 'heads/main' here.
        gitw_test_support.git(self.clone, "tag", "main")
        self.assertEqual(repo.current_branch(self.clone), "main")
        with self.assertRaisesRegex(repo.RefusalError, "default branch"):
            repo.require_prefixed_branch(self.clone, "/", "proj", "main")

    def test_names_shadowing_the_remote_are_refused(self):
        # Judged on the full name, however the prefix token was spelled.
        for branch in ("origin/main", "Origin/topic"):
            with self.subTest(branch=branch):
                with self.assertRaisesRegex(repo.RefusalError, "shadow"):
                    repo.refuse_remote_shadowing(branch, "origin")
        repo.refuse_remote_shadowing("origin", "origin")
        repo.refuse_remote_shadowing("originals/x", "origin")

    def test_a_machine_local_repo_has_no_remote_to_shadow(self):
        repo.refuse_remote_shadowing("origin/x", None)

    def test_a_real_prefix_also_refuses_a_slashed_default(self):
        # A real prefix can match a default like 'release/main'; the
        # refusal is prefix-independent.
        gitw_test_support.git(self.clone, "switch", "-c", "release/main")
        with self.assertRaisesRegex(repo.RefusalError, "default branch"):
            repo.require_prefixed_branch(
                self.clone, "release/", "proj", "release/main"
            )

    def test_no_rebase_in_progress_reports_none(self):
        self.assertIsNone(repo.rebase_head_branch(self.clone))
        self.assertEqual(repo.conflicted_paths(self.clone), [])
        self.assertIsNone(repo.pending_operation(self.clone))

    def test_describe_dirty_names_all_three_tallies(self):
        self.assertEqual(
            repo.describe_dirty({"staged": 1, "unstaged": 2, "untracked": 3}),
            "staged 1, unstaged 2, untracked 3",
        )

    def test_authoritative_ref_shapes(self):
        self.assertEqual(
            repo.authoritative_ref(self.entry),
            ("origin/main", "refs/remotes/origin/main"),
        )
        local = Entry(label="scratch", checkout=self.clone)
        self.assertEqual(
            repo.authoritative_ref(local), ("main", "refs/heads/main")
        )


if __name__ == "__main__":
    unittest.main()
