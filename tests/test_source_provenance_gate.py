from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "source-provenance-gate.py"


@unittest.skipUnless(shutil.which("git"), "git is required")
class SourceProvenanceGateTests(unittest.TestCase):
    def git(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def make_repo(self, root: Path) -> tuple[Path, str]:
        repo = root / "repo"
        repo.mkdir()
        self.git(repo, "init")
        self.git(repo, "config", "user.email", "qualification@example.invalid")
        self.git(repo, "config", "user.name", "Qualification Test")
        (repo / "critical.txt").write_text("critical-v1\n", encoding="utf-8")
        (repo / "lock.json").write_text('{"version":1}\n', encoding="utf-8")
        self.git(repo, "add", "critical.txt", "lock.json")
        self.git(repo, "commit", "-m", "fixture")
        return repo, self.git(repo, "rev-parse", "HEAD").stdout.strip()

    def run_gate(self, root: Path, repo: Path, head: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        output = root / "evidence" / "source-provenance.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(GATE),
                "--repo-root",
                str(repo),
                "--expected-head",
                head,
                "--output",
                str(output),
                "--asset",
                "critical.txt",
                "--lockfile",
                "lock.json",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return completed, json.loads(output.read_text(encoding="utf-8"))

    def test_clean_exact_head_binds_git_blob_and_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, head = self.make_repo(root)
            completed, result = self.run_gate(root, repo, head)

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["actual_head"], head)
            self.assertTrue(result["working_tree_clean"])
            self.assertTrue(result["tracked_diff_empty"])
            self.assertTrue(result["untracked_empty"])
            record = result["critical_assets"]["critical.txt"]
            self.assertTrue(record["matches_expected_blob"])
            self.assertEqual(len(record["sha256"]), 64)
            self.assertEqual(result["lockfiles"]["lock.json"]["matches_expected_blob"], True)

    def test_tracked_modification_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, head = self.make_repo(root)
            (repo / "critical.txt").write_text("tampered\n", encoding="utf-8")
            completed, result = self.run_gate(root, repo, head)

            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(result["status"], "fail")
            self.assertFalse(result["working_tree_clean"])
            self.assertFalse(result["tracked_diff_empty"])
            self.assertFalse(result["critical_assets"]["critical.txt"]["matches_expected_blob"])

    def test_untracked_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, head = self.make_repo(root)
            (repo / "untracked-helper.py").write_text("print('unexpected')\n", encoding="utf-8")
            completed, result = self.run_gate(root, repo, head)

            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(result["status"], "fail")
            self.assertFalse(result["working_tree_clean"])
            self.assertFalse(result["untracked_empty"])
            self.assertTrue(any(line.startswith("?? ") for line in result["status_porcelain"]))

    def test_output_inside_repo_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, head = self.make_repo(root)
            output = repo / "provenance.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(GATE),
                    "--repo-root",
                    str(repo),
                    "--expected-head",
                    head,
                    "--output",
                    str(output),
                    "--asset",
                    "critical.txt",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertNotEqual(completed.returncode, 0)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "fail")
            self.assertIn("outside the repository", result["error"])


if __name__ == "__main__":
    unittest.main()
