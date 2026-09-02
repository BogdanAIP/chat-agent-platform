from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts" / "chat-platform-update-core.ps1"
UPDATER = ROOT / "scripts" / "chat-platform-update.ps1"
UPDATE_UI = ROOT / "scripts" / "chat-platform-update-ui.ps1"
BOOTSTRAP = ROOT / "scripts" / "bootstrap-chat-platform.ps1"


def run(cmd: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {cmd!r}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    return result.stdout.strip()


def ps_quote(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


class ChatPlatformUpdateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.core = CORE.read_text(encoding="utf-8")
        cls.updater = UPDATER.read_text(encoding="utf-8")
        cls.ui = UPDATE_UI.read_text(encoding="utf-8")
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")

    def test_public_updater_is_fixed_to_official_main(self) -> None:
        self.assertIn("$script:CapUpdateRepository = 'BogdanAIP/chat-agent-platform'", self.core)
        self.assertIn(
            "$script:CapUpdateOfficialRemote = 'https://github.com/BogdanAIP/chat-agent-platform.git'",
            self.core,
        )
        self.assertIn("$script:CapUpdateBranch = 'main'", self.core)
        self.assertIn("$RemoteUrl = $script:CapUpdateOfficialRemote", self.updater)
        parameter_block = self.updater.split("Set-StrictMode", 1)[0]
        for forbidden in ("RemoteUrl", "Repository", "Branch", "Commit", "Ref", "Path"):
            self.assertNotIn(forbidden, parameter_block)

    def test_update_blocks_non_fast_forward_and_uses_exact_detached_worktree(self) -> None:
        for marker in (
            "merge-base', '--is-ancestor'",
            "'worktree', 'add', '--detach'",
            "'rev-parse', 'HEAD'",
            "'status', '--porcelain'",
            "'+refs/heads/main:refs/remotes/origin/main'",
            "--atomic",
        ):
            self.assertIn(marker, self.core)
        self.assertIn("remote_main_not_fast_forward", self.updater)

    def test_version_receipt_requires_clean_exact_origin_main(self) -> None:
        publish = self.core.split("function Publish-CapInstalledVersionFromSource", 1)[1]
        publish = publish.split("function Initialize-CapUpdateCacheRepository", 1)[0]
        for marker in (
            "remote', 'get-url', 'origin'",
            "refs/remotes/origin/main^{commit}",
            "if ($head -cne $originMain)",
            "'status', '--porcelain'",
            "Write-CapUpdateAtomicJson",
        ):
            self.assertIn(marker, publish)

    def test_bootstrap_ships_ui_and_records_version_after_smoke(self) -> None:
        for marker in (
            "chat-platform-update-core.ps1",
            "chat-platform-update.ps1",
            "chat-platform-update-ui.ps1",
            "Install-CapUpdateDesktopShortcut",
            "Обновить Chat Agent Platform.lnk",
            "Publish-CapInstalledVersionFromSource",
            "INSTALLED_VERSION_RECORDED=",
        ):
            self.assertIn(marker, self.bootstrap)
        self.assertLess(
            self.bootstrap.index("Invoke-ChatBootstrapSmokeTest"),
            self.bootstrap.index("Publish-CapInstalledVersionFromSource"),
        )

    def test_update_ui_has_explicit_check_and_confirmed_apply(self) -> None:
        for marker in (
            "Проверить обновление",
            "Обновить до $target",
            "MessageBoxButtons]::YesNo",
            "Start-UpdateOperation -Action Check",
            "Start-UpdateOperation -Action Update",
        ):
            self.assertIn(marker, self.ui)


@unittest.skipUnless(shutil.which("pwsh") and shutil.which("git"), "pwsh and git are required")
class ChatPlatformUpdateGitBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.remote = self.root / "remote.git"
        self.cache = self.root / "cache.git"
        self.worktrees = self.root / "worktrees"

        run(["git", "init", str(self.source)])
        run(["git", "config", "user.name", "CAP Update Test"], cwd=self.source)
        run(["git", "config", "user.email", "cap-update@example.invalid"], cwd=self.source)
        (self.source / "value.txt").write_text("one\n", encoding="utf-8")
        run(["git", "add", "value.txt"], cwd=self.source)
        run(["git", "commit", "-m", "one"], cwd=self.source)
        run(["git", "branch", "-M", "main"], cwd=self.source)
        self.first = run(["git", "rev-parse", "HEAD"], cwd=self.source)
        run(["git", "clone", "--bare", str(self.source), str(self.remote)])
        run(["git", "remote", "add", "origin", str(self.remote)], cwd=self.source)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def pwsh(self, body: str) -> str:
        command = f". {ps_quote(CORE)}; $ErrorActionPreference='Stop'; {body}"
        return run(["pwsh", "-NoLogo", "-NoProfile", "-Command", command])

    def sync(self) -> str:
        return self.pwsh(
            f"Sync-CapUpdateMain -CacheRepo {ps_quote(self.cache)} "
            f"-RemoteUrl {ps_quote(self.remote)}"
        ).splitlines()[-1].strip()

    def test_exact_fetch_fast_forward_rollback_block_and_worktree(self) -> None:
        self.assertEqual(self.sync(), self.first)

        (self.source / "value.txt").write_text("two\n", encoding="utf-8")
        run(["git", "add", "value.txt"], cwd=self.source)
        run(["git", "commit", "-m", "two"], cwd=self.source)
        second = run(["git", "rev-parse", "HEAD"], cwd=self.source)
        run(["git", "push", "origin", "main"], cwd=self.source)
        self.assertEqual(self.sync(), second)

        ff = self.pwsh(
            f"Test-CapUpdateFastForward -CacheRepo {ps_quote(self.cache)} "
            f"-InstalledCommitSha '{self.first}' -TargetCommitSha '{second}'"
        ).splitlines()[-1].strip()
        self.assertEqual(ff, "True")

        worktree = self.pwsh(
            f"New-CapUpdateWorktree -CacheRepo {ps_quote(self.cache)} "
            f"-WorktreeRoot {ps_quote(self.worktrees)} -TargetCommitSha '{second}'"
        ).splitlines()[-1].strip()
        self.assertEqual(run(["git", "rev-parse", "HEAD"], cwd=Path(worktree)), second)
        self.assertEqual(run(["git", "status", "--porcelain"], cwd=Path(worktree)), "")
        self.pwsh(
            f"Remove-CapUpdateWorktree -CacheRepo {ps_quote(self.cache)} "
            f"-WorktreePath {ps_quote(worktree)}"
        )

        run(["git", "reset", "--hard", self.first], cwd=self.source)
        run(["git", "push", "--force", "origin", "main"], cwd=self.source)
        self.assertEqual(self.sync(), self.first)

        rollback = self.pwsh(
            f"Test-CapUpdateFastForward -CacheRepo {ps_quote(self.cache)} "
            f"-InstalledCommitSha '{second}' -TargetCommitSha '{self.first}'"
        ).splitlines()[-1].strip()
        self.assertEqual(rollback, "False")

    def test_state_round_trip_is_strict(self) -> None:
        state_path = self.root / "state.json"
        body = (
            f"$s=New-CapUpdateState -InstalledCommitSha '{self.first}' -InstalledAt '2026-09-02T00:00:00Z' "
            f"-Status current -TargetCommitSha '{self.first}' -LastCheckedAt '2026-09-02T00:00:00Z'; "
            f"Write-CapUpdateAtomicJson -Path {ps_quote(state_path)} -Value $s; "
            f"$r=Read-CapUpdateState -Path {ps_quote(state_path)}; $r | ConvertTo-Json -Compress"
        )
        value = json.loads(self.pwsh(body).splitlines()[-1])
        self.assertEqual(value["installed_commit_sha"], self.first)
        self.assertEqual(value["status"], "current")


if __name__ == "__main__":
    unittest.main()
