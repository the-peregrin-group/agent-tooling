"""Tests for the gitw-commit executable.

Argument tests run the script as a subprocess with arguments that fail
before the roster is ever read. Behavior tests load the script as a module,
mock the roster seam, and run against throwaway file-path git fixtures --
fully offline, never touching the real roster or any real repo.

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ghw_test_support
import gitw_test_support
from lib.git.roster import Entry

_SCRIPT = Path(__file__).resolve().parent / "gitw-commit"
_MODULE = ghw_test_support.load_wrapper_module(_SCRIPT)
_MISSING_MESSAGE = "/tmp/claude/gitw-commit-test-missing-message.txt"


def _run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *arguments],
        capture_output=True, text=True, timeout=30,
    )


class GitwCommitArgumentsTest(unittest.TestCase):
    def test_wrong_argument_count_is_usage_error(self):
        for arguments in ((), ("proj",), ("proj", "fix/")):
            with self.subTest(arguments=arguments):
                result = _run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage: gitw-commit", result.stderr)

    def test_invalid_prefix_is_usage_error(self):
        result = _run("proj", "Fix/", _MISSING_MESSAGE)
        self.assertEqual(result.returncode, 2)
        self.assertIn("prefix", result.stderr)

    def test_empty_pathspec_is_usage_error(self):
        result = _run("proj", "fix/", _MISSING_MESSAGE, "a.txt", "  ")
        self.assertEqual(result.returncode, 2)
        self.assertIn("pathspecs must not be empty", result.stderr)

    def test_missing_message_file_is_refused_before_roster(self):
        result = _run("proj", "fix/", _MISSING_MESSAGE)
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing message file", result.stderr)

    def test_empty_message_file_is_usage_error(self):
        os.makedirs("/tmp/claude", exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w", dir="/tmp/claude", suffix=".txt", delete=False
        )
        handle.write("   \n")
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        result = _run("proj", "fix/", handle.name)
        self.assertEqual(result.returncode, 2)
        self.assertIn("empty", result.stderr)

    def test_help_prints_doc_and_exits_zero(self):
        result = _run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("gitw-commit <repo>", result.stdout)


class _CommitFixtureTest(unittest.TestCase):
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
        gitw_test_support.git(self.clone, "switch", "-c", "fix/topic")
        config = gitw_test_support.isolated_git_config()
        config.__enter__()
        self.addCleanup(config.__exit__, None, None, None)
        os.makedirs("/tmp/claude", exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode="w", dir="/tmp/claude", suffix=".txt", delete=False
        )
        handle.write("test commit\n\nbody line\n")
        handle.close()
        self.message_path = handle.name
        self.addCleanup(os.unlink, self.message_path)

    def commit(self, *arguments: str, cwd: Path | None = None,
               entries: dict | None = None) -> dict:
        entries = {"proj": self.entry} if entries is None else entries
        with mock.patch.object(_MODULE.roster, "load", return_value=entries), \
                gitw_test_support.chdir(cwd or self.clone), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            code = _MODULE.main(list(arguments))
        self.assertEqual(code, 0)
        return json.loads(stdout.getvalue())

    def commit_expecting_exit(self, code: int, *arguments: str,
                              cwd: Path | None = None,
                              entries: dict | None = None) -> str:
        entries = {"proj": self.entry} if entries is None else entries
        with mock.patch.object(_MODULE.roster, "load", return_value=entries), \
                gitw_test_support.chdir(cwd or self.clone), \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                _MODULE.main(list(arguments))
        self.assertEqual(caught.exception.code, code)
        return stderr.getvalue()


class GitwCommitAllTest(_CommitFixtureTest):
    def test_commit_all_takes_everything_and_leaves_the_tree_clean(self):
        (self.clone / "README.md").write_text("modified\n")
        (self.clone / "new.txt").write_text("new\n")
        payload = self.commit("proj", "fix/", self.message_path)
        self.assertEqual(payload["action"], "applied")
        self.assertEqual(payload["branch"], "fix/topic")
        self.assertEqual(payload["files"], 2)
        self.assertTrue(payload["clean"])
        self.assertEqual(
            payload["remaining"], {"staged": 0, "unstaged": 0, "untracked": 0}
        )
        body = gitw_test_support.git(
            self.clone, "log", "-1", "--format=%B"
        ).stdout
        # The message, then the Executed-By trailer block (the trailer's
        # value depends on the ambient session; GitwCommitExecutedByTest
        # pins it).
        self.assertTrue(
            body.startswith("test commit\n\nbody line\n\nExecuted-By: "),
            body,
        )

    def test_clean_tree_is_an_empty_commit_refusal(self):
        stderr = self.commit_expecting_exit(4, "proj", "fix/", self.message_path)
        self.assertIn("working tree is clean", stderr)

    def test_filesystem_rename_plus_commit_all_yields_a_rename_record(self):
        # The inventory's `git mv` note: rename detection is content-based,
        # so plain mv + commit-all preserves the R100 record --follow needs.
        (self.clone / "README.md").rename(self.clone / "RENAMED.md")
        self.commit("proj", "fix/", self.message_path)
        names = gitw_test_support.git(
            self.clone, "diff", "--name-status", "-M", "HEAD~1", "HEAD"
        ).stdout
        self.assertIn("R100", names)

    def test_prefix_mismatch_is_refused(self):
        gitw_test_support.git(self.clone, "switch", "main")
        (self.clone / "README.md").write_text("modified\n")
        stderr = self.commit_expecting_exit(4, "proj", "fix/", self.message_path)
        self.assertIn("does not match the pinned prefix", stderr)

    def test_detached_head_is_refused(self):
        gitw_test_support.git(self.clone, "switch", "--detach")
        (self.clone / "README.md").write_text("modified\n")
        stderr = self.commit_expecting_exit(4, "proj", "fix/", self.message_path)
        self.assertIn("detached HEAD", stderr)

    def test_operable_from_cwd_is_refused(self):
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=str(self.remote),
            remote="origin",
            operable_from=(elsewhere,),
        )
        stderr = self.commit_expecting_exit(
            4, "proj", "fix/", self.message_path,
            cwd=elsewhere, entries={"proj": entry},
        )
        self.assertIn("worktree at cwd", stderr)

    def test_machine_local_repo_commits_fine(self):
        local = self.base / "local"
        local.mkdir()
        gitw_test_support.git(local, "init", "--initial-branch=main", ".")
        gitw_test_support.commit_on(local, "a.txt", "a\n", "seed")
        gitw_test_support.git(local, "switch", "-c", "fix/topic")
        (local / "b.txt").write_text("b\n")
        entry = Entry(label="scratch", checkout=local)
        payload = self.commit(
            "scratch", "fix/", self.message_path,
            cwd=local, entries={"scratch": entry},
        )
        self.assertTrue(payload["clean"])

    def make_conflicted_merge(self):
        gitw_test_support.commit_on(
            self.clone, "conflict.txt", "ours\n", "our side"
        )
        gitw_test_support.git(self.clone, "switch", "-c", "fix/other", "main")
        gitw_test_support.commit_on(
            self.clone, "conflict.txt", "theirs\n", "their side"
        )
        gitw_test_support.git(self.clone, "switch", "fix/topic")
        merge = gitw_test_support.git(
            self.clone, "merge", "fix/other", check=False
        )
        self.assertNotEqual(merge.returncode, 0)  # conflicted on purpose

    def test_pending_merge_is_refused_even_when_fully_resolved(self):
        # A resolved-and-staged merge passes every dirty/conflict check,
        # but `git commit` would silently conclude it as a two-parent
        # merge commit while the JSON reports an ordinary commit.
        self.make_conflicted_merge()
        (self.clone / "conflict.txt").write_text("resolved\n")
        gitw_test_support.git(self.clone, "add", "conflict.txt")
        stderr = self.commit_expecting_exit(4, "proj", "fix/", self.message_path)
        self.assertIn("merge is in progress", stderr)

    def test_unresolved_conflicts_are_refused(self):
        self.make_conflicted_merge()
        # Drop the pending-merge state so the unmerged-entries refusal
        # itself is what fires (defense in depth for states no pending
        # operation explains).
        gitw_test_support.git(self.clone, "update-ref", "-d", "MERGE_HEAD")
        stderr = self.commit_expecting_exit(4, "proj", "fix/", self.message_path)
        self.assertIn("unresolved conflicts", stderr)
        self.assertIn("conflict.txt", stderr)


class GitwCommitSweepGuardTest(_CommitFixtureTest):
    def test_commit_all_refuses_to_sweep_settings_local_json(self):
        (self.clone / ".claude").mkdir()
        (self.clone / ".claude" / "settings.local.json").write_text("{}\n")
        (self.clone / "work.txt").write_text("w\n")
        stderr = self.commit_expecting_exit(4, "proj", "fix/", self.message_path)
        self.assertIn("settings.local.json", stderr)
        self.assertIn("local-only", stderr)

    def test_commit_all_refuses_to_sweep_env_files(self):
        (self.clone / ".env.local").write_text("SECRET=1\n")
        stderr = self.commit_expecting_exit(4, "proj", "fix/", self.message_path)
        self.assertIn(".env.local (matches .env*)", stderr)
        # The refusal is self-explanatory: policy, the one sanctioned
        # exception, and where authority lies.
        self.assertIn("never enter history", stderr)
        self.assertIn(".env.example", stderr)
        self.assertIn("user's call", stderr)

    def test_env_example_commits_in_both_modes(self):
        # The one sanctioned exception, anywhere in
        # the tree.
        (self.clone / ".env.example").write_text("EXAMPLE=fill-me\n")
        docs = self.clone / "docs"
        docs.mkdir()
        (docs / ".env.example").write_text("EXAMPLE=fill-me\n")
        payload = self.commit(
            "proj", "fix/", self.message_path, ".env.example"
        )
        self.assertEqual(payload["files"], 1)
        payload = self.commit("proj", "fix/", self.message_path)
        self.assertTrue(payload["clean"])

    def test_env_sample_and_template_still_refuse(self):
        # Deliberately narrow exemption: only .env.example is sanctioned.
        for name in (".env.sample", ".env.template"):
            with self.subTest(name=name):
                (self.clone / name).write_text("EXAMPLE=1\n")
                stderr = self.commit_expecting_exit(
                    4, "proj", "fix/", self.message_path
                )
                self.assertIn(name, stderr)
                (self.clone / name).unlink()

    def test_a_directory_named_like_a_pattern_does_not_bypass_the_guard(self):
        (self.clone / ".env").mkdir()
        (self.clone / ".env" / "creds.json").write_text("{}\n")
        stderr = self.commit_expecting_exit(4, "proj", "fix/", self.message_path)
        self.assertIn(".env/creds.json", stderr)

    def test_case_variants_do_not_bypass_the_guard(self):
        # The default APFS volume is case-insensitive: these ARE the
        # guarded files on disk.
        (self.clone / "Settings.Local.JSON").write_text("{}\n")
        stderr = self.commit_expecting_exit(4, "proj", "fix/", self.message_path)
        self.assertIn("Settings.Local.JSON", stderr)

    def test_dot_pathspec_does_not_bypass_the_guard(self):
        (self.clone / ".env").write_text("SECRET=1\n")
        (self.clone / "work.txt").write_text("w\n")
        stderr = self.commit_expecting_exit(
            4, "proj", "fix/", self.message_path, "."
        )
        self.assertIn(".env", stderr)

    def test_explicit_pathspec_around_the_guarded_file_commits(self):
        (self.clone / ".env").write_text("SECRET=1\n")
        (self.clone / "work.txt").write_text("w\n")
        payload = self.commit("proj", "fix/", self.message_path, "work.txt")
        self.assertEqual(payload["files"], 1)
        self.assertFalse(payload["clean"])
        self.assertEqual(payload["remaining"]["untracked"], 1)


class GitwCommitPathspecTest(_CommitFixtureTest):
    def test_pathspec_commits_exactly_and_reports_the_rest(self):
        (self.clone / "README.md").write_text("modified\n")
        (self.clone / "other.txt").write_text("o\n")
        payload = self.commit("proj", "fix/", self.message_path, "README.md")
        self.assertEqual(payload["files"], 1)
        self.assertEqual(payload["remaining"]["untracked"], 1)
        self.assertFalse(payload["clean"])
        names = gitw_test_support.git(
            self.clone, "diff", "--name-only", "HEAD~1", "HEAD"
        ).stdout.split()
        self.assertEqual(names, ["README.md"])

    def test_pathspec_matching_nothing_is_refused(self):
        stderr = self.commit_expecting_exit(
            4, "proj", "fix/", self.message_path, "nope.txt"
        )
        self.assertIn("match no changes", stderr)

    def test_staged_changes_outside_the_pathspecs_are_refused(self):
        (self.clone / "README.md").write_text("modified\n")
        (self.clone / "other.txt").write_text("o\n")
        gitw_test_support.git(self.clone, "add", "other.txt")
        stderr = self.commit_expecting_exit(
            4, "proj", "fix/", self.message_path, "README.md"
        )
        self.assertIn("outside the given pathspecs", stderr)
        self.assertIn("other.txt", stderr)


class GitwCommitExecutedByTest(_CommitFixtureTest):
    _JOB_ENVIRON = {"CLAUDE_JOB_DIR": "/Users/x/.claude/jobs/ae218998",
                    "USER": "dan"}

    def commit_with_environ(self, environ: dict, *arguments: str,
                            expecting_exit: int | None = None):
        """Commit with the session identity pinned to `environ` (the
        developer running the suite may well be inside a background job
        with CLAUDE_JOB_DIR set). Returns the JSON payload, or the stderr
        text when `expecting_exit` names the refusal code."""
        with mock.patch.dict(os.environ, environ):
            if "CLAUDE_JOB_DIR" not in environ:
                os.environ.pop("CLAUDE_JOB_DIR", None)
            if expecting_exit is not None:
                return self.commit_expecting_exit(expecting_exit, *arguments)
            return self.commit(*arguments)

    def head_message(self) -> str:
        return gitw_test_support.git(
            self.clone, "log", "-1", "--format=%B"
        ).stdout

    def head_trailers(self, key: str) -> list:
        output = gitw_test_support.git(
            self.clone, "log", "-1",
            f"--format=%(trailers:key={key},valueonly)",
        ).stdout
        return [line for line in output.splitlines() if line]

    def head_subject(self) -> str:
        return gitw_test_support.git(
            self.clone, "log", "-1", "--format=%s"
        ).stdout.rstrip("\n")

    def test_job_dir_actor_is_the_trailer(self):
        (self.clone / "new.txt").write_text("new\n")
        payload = self.commit_with_environ(
            self._JOB_ENVIRON, "proj", "fix/", self.message_path
        )
        self.assertEqual(
            self.head_message(),
            "test commit\n\nbody line\n\n"
            "Executed-By: claude-job-ae218998\n\n",
        )
        self.assertEqual(payload["executed_by"], "claude-job-ae218998")

    def test_attended_fallback_is_the_trailer(self):
        (self.clone / "new.txt").write_text("new\n")
        payload = self.commit_with_environ(
            {"USER": "dan"}, "proj", "fix/", self.message_path
        )
        self.assertEqual(self.head_trailers("Executed-By"), ["attended-dan"])
        self.assertEqual(payload["executed_by"], "attended-dan")

    def test_trailer_joins_an_existing_trailer_block(self):
        Path(self.message_path).write_text(
            "subject\n\nbody\n\nRefs: abc-1\n"
        )
        (self.clone / "new.txt").write_text("new\n")
        self.commit_with_environ(
            self._JOB_ENVIRON, "proj", "fix/", self.message_path
        )
        self.assertEqual(
            self.head_message(),
            "subject\n\nbody\n\nRefs: abc-1\n"
            "Executed-By: claude-job-ae218998\n\n",
        )

    def test_caller_executed_by_trailer_is_replaced(self):
        for index, key in enumerate(("Executed-By", "executed-by")):
            with self.subTest(key=key):
                Path(self.message_path).write_text(
                    f"subject\n\nbody\n\n{key}: someone-else\n"
                )
                (self.clone / f"new{index}.txt").write_text("new\n")
                self.commit_with_environ(
                    self._JOB_ENVIRON, "proj", "fix/", self.message_path
                )
                self.assertEqual(
                    self.head_trailers("Executed-By"),
                    ["claude-job-ae218998"],
                )
                self.assertNotIn("someone-else", self.head_message())

    def test_pathspec_commit_gets_the_trailer_and_reports_the_rest(self):
        (self.clone / "README.md").write_text("modified\n")
        (self.clone / "other.txt").write_text("o\n")
        payload = self.commit_with_environ(
            self._JOB_ENVIRON, "proj", "fix/", self.message_path, "README.md"
        )
        self.assertEqual(
            self.head_trailers("Executed-By"), ["claude-job-ae218998"]
        )
        self.assertEqual(payload["executed_by"], "claude-job-ae218998")
        self.assertEqual(payload["files"], 1)
        self.assertEqual(payload["remaining"]["untracked"], 1)
        self.assertFalse(payload["clean"])

    def test_several_caller_executed_by_trailers_are_refused(self):
        # git's replace deletes only one; refusing beats leaving a caller
        # value beside the derived one.
        Path(self.message_path).write_text(
            "subject\n\nExecuted-By: a\nRefs: x\nexecuted-by: b\n"
        )
        (self.clone / "new.txt").write_text("new\n")
        stderr = self.commit_with_environ(
            self._JOB_ENVIRON, "proj", "fix/", self.message_path,
            expecting_exit=4,
        )
        self.assertIn("2 Executed-By trailers", stderr)
        # Refused before staging: nothing was added to the index.
        staged = gitw_test_support.git(
            self.clone, "diff", "--cached", "--name-only"
        ).stdout
        self.assertEqual(staged, "")

    def test_message_without_final_newline_still_gets_a_trailer(self):
        # interpret-trailers glues a trailer onto an unterminated last
        # line; the wrapper must terminate the message first.
        cases = (
            ("subject\n\nbody",
             "subject\n\nbody\n\nExecuted-By: claude-job-ae218998\n\n"),
            ("subject",
             "subject\n\nExecuted-By: claude-job-ae218998\n\n"),
        )
        for index, (content, expected) in enumerate(cases):
            with self.subTest(content=content):
                Path(self.message_path).write_bytes(content.encode())
                (self.clone / f"new{index}.txt").write_text("new\n")
                self.commit_with_environ(
                    self._JOB_ENVIRON, "proj", "fix/", self.message_path
                )
                self.assertEqual(
                    self.head_trailers("Executed-By"),
                    ["claude-job-ae218998"],
                )
                self.assertEqual(self.head_subject(), "subject")
                self.assertEqual(self.head_message(), expected)
                self.assertEqual(
                    Path(self.message_path).read_bytes(), content.encode()
                )

    def test_message_file_on_disk_is_unchanged(self):
        before = Path(self.message_path).read_bytes()
        (self.clone / "new.txt").write_text("new\n")
        self.commit_with_environ(
            self._JOB_ENVIRON, "proj", "fix/", self.message_path
        )
        self.assertEqual(Path(self.message_path).read_bytes(), before)
        self.assertIn(
            "Executed-By: claude-job-ae218998", self.head_message()
        )


class GitwCommitBareSlashTest(_CommitFixtureTest):
    def test_commits_on_an_unprefixed_branch(self):
        gitw_test_support.git(self.clone, "switch", "-c", "foo-bar")
        (self.clone / "new.txt").write_text("new\n")
        payload = self.commit("proj", "/", self.message_path)
        self.assertEqual(payload["branch"], "foo-bar")

    def test_refuses_the_default_branch(self):
        gitw_test_support.git(self.clone, "switch", "main")
        (self.clone / "new.txt").write_text("new\n")
        stderr = self.commit_expecting_exit(4, "proj", "/", self.message_path)
        self.assertIn("default branch", stderr)
        self.assertEqual(
            gitw_test_support.git(
                self.clone, "status", "--porcelain"
            ).stdout.strip(),
            "?? new.txt",
        )


    def test_tag_named_like_the_default_does_not_hide_it(self):
        gitw_test_support.git(self.clone, "switch", "main")
        gitw_test_support.git(self.clone, "tag", "main")
        (self.clone / "new.txt").write_text("new\n")
        stderr = self.commit_expecting_exit(4, "proj", "/", self.message_path)
        self.assertIn("default branch", stderr)


    def test_real_prefix_refuses_a_slashed_default(self):
        self.entry = Entry(
            label="proj",
            checkout=self.clone,
            remote_url=self.entry.remote_url,
            remote="origin",
            default_branch="fix/topic",
        )
        (self.clone / "new.txt").write_text("new\n")
        stderr = self.commit_expecting_exit(4, "proj", "fix/", self.message_path)
        self.assertIn("default branch", stderr)


if __name__ == "__main__":
    unittest.main()
