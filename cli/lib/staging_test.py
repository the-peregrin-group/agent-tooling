"""Unit tests for staging.py (the staging-directory policy).

Run from the cli/ directory:
    python3 -m unittest discover -s . -p '*_test.py'
"""

from __future__ import annotations

import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

if __package__ in (None, ""):  # direct invocation: python3 lib/staging_test.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.staging import (
    StagingPathError,
    read_body,
    read_staged_body,
    resolve_staging_path,
    validate_staging_path,
)


class ValidateStagingPathTest(unittest.TestCase):
    def setUp(self):
        # Both policy roots are substituted with scratch directories under
        # /tmp/claude so the tests never touch the real ~/.claude/jobs tree.
        os.makedirs("/tmp/claude", exist_ok=True)
        self.scratch = Path(tempfile.mkdtemp(dir="/tmp/claude"))
        self.tmp_root = self.scratch / "tmp_root"
        self.jobs_root = self.scratch / "jobs_root"
        self.tmp_root.mkdir()
        self.jobs_root.mkdir()
        self.addCleanup(shutil.rmtree, self.scratch)

    def _validate(self, path: Path) -> Path:
        return validate_staging_path(
            str(path),
            tmp_root_for_testing=self.tmp_root,
            jobs_root_for_testing=self.jobs_root,
        )

    def _refuses(self, path: Path, why_fragment: str):
        with self.assertRaisesRegex(StagingPathError, why_fragment):
            self._validate(path)

    def test_accepts_file_in_tmp_root(self):
        body = self.tmp_root / "body.md"
        body.write_text("hello")
        self.assertEqual(self._validate(body), body.resolve())

    def test_accepts_file_nested_in_tmp_root(self):
        nested = self.tmp_root / "deeper" / "body.md"
        nested.parent.mkdir()
        nested.write_text("hello")
        self.assertEqual(self._validate(nested), nested.resolve())

    def test_accepts_file_in_job_tmp(self):
        body = self.jobs_root / "job-1" / "tmp" / "body.md"
        body.parent.mkdir(parents=True)
        body.write_text("hello")
        self.assertEqual(self._validate(body), body.resolve())

    def test_accepts_file_nested_in_job_tmp(self):
        body = self.jobs_root / "job-1" / "tmp" / "sub" / "body.md"
        body.parent.mkdir(parents=True)
        body.write_text("hello")
        self.assertEqual(self._validate(body), body.resolve())

    def test_refuses_missing_file(self):
        self._refuses(self.tmp_root / "absent.md", "does not exist")

    def test_refuses_directory(self):
        self._refuses(self.tmp_root, "not a regular file")

    def test_refuses_file_outside_staging(self):
        outsider = self.scratch / "outside.md"
        outsider.write_text("nope")
        self._refuses(outsider, "outside the staging directories")

    def test_refuses_job_file_outside_its_tmp(self):
        # A job's transcripts and other non-tmp/ contents are off-limits.
        stray = self.jobs_root / "job-1" / "transcript.md"
        stray.parent.mkdir()
        stray.write_text("nope")
        self._refuses(stray, "outside the staging directories")

    def test_refuses_file_directly_under_jobs_root(self):
        stray = self.jobs_root / "loose.md"
        stray.write_text("nope")
        self._refuses(stray, "outside the staging directories")

    def test_description_names_the_argument_in_refusals(self):
        # ghw-label-sync reads a schema file under the same policy; only the
        # wording changes.
        outsider = self.scratch / "outside.md"
        outsider.write_text("nope")
        with self.assertRaisesRegex(StagingPathError, "refusing schema file"):
            validate_staging_path(
                str(outsider),
                description="schema file",
                tmp_root_for_testing=self.tmp_root,
                jobs_root_for_testing=self.jobs_root,
            )

    def test_refuses_a_sibling_directory_sharing_the_prefix(self):
        # /tmp/claude-evil is not /tmp/claude: the check is a path-component
        # relationship, never a string prefix.
        sibling = Path(str(self.tmp_root) + "-evil")
        sibling.mkdir()
        stray = sibling / "body.md"
        stray.write_text("nope")
        self._refuses(stray, "outside the staging directories")

    def test_refuses_traversal_out_of_staging(self):
        outsider = self.scratch / "secret.md"
        outsider.write_text("secret")
        traversal = self.tmp_root / ".." / "secret.md"
        self._refuses(traversal, "outside the staging directories")

    def test_refuses_symlink_escaping_staging(self):
        # The literal path sits inside staging, but resolution escapes it.
        target = self.scratch / "secret.md"
        target.write_text("secret")
        link = self.tmp_root / "innocent.md"
        link.symlink_to(target)
        self._refuses(link, "outside the staging directories")


class ReadStagedBodyTest(unittest.TestCase):
    """Exercises the production roots: the scratch dir lives under the real
    /tmp/claude, so no *_for_testing substitution is involved."""

    def setUp(self):
        os.makedirs("/tmp/claude", exist_ok=True)
        self.scratch = Path(tempfile.mkdtemp(dir="/tmp/claude"))
        self.addCleanup(shutil.rmtree, self.scratch)

    def test_reads_utf8_body(self):
        body = self.scratch / "body.md"
        body.write_text("héllo", encoding="utf-8")
        self.assertEqual(read_staged_body(str(body)), "héllo")

    def test_refuses_non_utf8_body_with_exit_2(self):
        body = self.scratch / "binary.md"
        body.write_bytes(b"\xff\xfe not text")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            read_staged_body(str(body))
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("not valid UTF-8", stderr.getvalue())

    def test_read_body_reuses_a_resolved_path_without_revalidating(self):
        # For callers that need the path *and* the text (gitw-commit
        # passes the file to `git commit --file`).
        body = self.scratch / "body.md"
        body.write_text("héllo", encoding="utf-8")
        resolved = resolve_staging_path(str(body))
        self.assertEqual(read_body(resolved), "héllo")


if __name__ == "__main__":
    unittest.main()
