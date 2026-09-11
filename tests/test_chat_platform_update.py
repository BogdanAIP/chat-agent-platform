from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts" / "chat-platform-update-core.ps1"
UPDATER = ROOT / "scripts" / "chat-platform-update.ps1"
TRAY = ROOT / "scripts" / "chat-platform-tray.ps1"
TRAY_UPDATE = ROOT / "scripts" / "chat-platform-tray-update.ps1"
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
        cls.tray = TRAY.read_text(encoding="utf-8")
        cls.tray_update = TRAY_UPDATE.read_text(encoding="utf-8")
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

    def test_bootstrap_ships_tray_updater_and_records_version_after_smoke(self) -> None:
        for marker in (
            "chat-platform-tray-update.ps1",
            "chat-platform-update-core.ps1",
            "chat-platform-update.ps1",
            "MAIN_UPDATE_UI=tray-more-menu",
            "Publish-CapInstalledVersionFromSource",
            "INSTALLED_VERSION_RECORDED=",
        ):
            self.assertIn(marker, self.bootstrap)
        self.assertNotIn("chat-platform-update-ui.ps1", self.bootstrap)
        self.assertNotIn("Install-CapUpdateDesktopShortcut", self.bootstrap)
        self.assertNotIn("Обновить Chat Agent Platform.lnk", self.bootstrap)
        self.assertLess(
            self.bootstrap.index("Invoke-ChatBootstrapSmokeTest"),
            self.bootstrap.index("Publish-CapInstalledVersionFromSource"),
        )

    def test_tray_more_menu_has_one_click_update_only(self) -> None:
        for marker in (
            'chat-platform-tray-update.ps1',
            'Register-CapUpdateTrayMenu',
            '-MoreMenu $moreMenu',
            '-NotifyIcon $notify',
            'Test-CapUpdateTrayBusy',
            'Stop-CapUpdateTrayMenu',
        ):
            self.assertIn(marker, self.tray)

        for marker in (
            "$script:CapTrayUpdateItem.Text = 'Обновить'",
            "'-Action', 'Update'",
            "Обновление не требуется. Установлена последняя версия.",
            "Установлена версия $version.",
            "Обновление уже выполняется.",
            "Дождитесь завершения текущей операции платформы.",
        ):
            self.assertIn(marker, self.tray_update)

        self.assertNotIn("Проверить обновление", self.tray_update)
        self.assertNotIn("MessageBox", self.tray_update)
        self.assertNotIn("-Action', 'Check'", self.tray_update)

    def test_target_main_cannot_remove_the_updater_that_invoked_it(self) -> None:
        for marker in (
            "function Test-CapTargetSelfUpdateContract",
            "scripts\\bootstrap-chat-platform.ps1",
            "scripts\\chat-platform-tray.ps1",
            "scripts\\chat-platform-tray-update.ps1",
            "scripts\\chat-platform-update-core.ps1",
            "scripts\\chat-platform-update.ps1",
            "target_missing_self_update_contract",
        ):
            self.assertIn(marker, self.updater)

        gate = self.updater.index("Test-CapTargetSelfUpdateContract -WorktreePath $worktree")
        bootstrap = self.updater.index("Invoke-CapPwshProcess -ScriptPath $bootstrap")
        self.assertLess(gate, bootstrap)
        self.assertIn("-Status 'blocked'", self.updater)
        self.assertIn("-Reason $TargetContinuityBlockedReason", self.updater)
        self.assertIn("target_missing_self_update_contract", self.tray_update)
        self.assertIn(
            "Доступный main ещё не содержит встроенный обновлятор. Ничего не изменено.",
            self.tray_update,
        )

    def test_update_quiesces_running_platform_before_bootstrap_and_recovers_on_error(self) -> None:
        gate = self.updater.index("Test-CapTargetSelfUpdateContract -WorktreePath $worktree")
        stop_attempt = self.updater.index("$platformStopAttempted = $true", gate)
        stop_call = self.updater.index(
            "-Arguments @('-Action', 'Stop', '-NoNotify')",
            stop_attempt,
        )
        bootstrap = self.updater.index("Invoke-CapPwshProcess -ScriptPath $bootstrap", stop_call)
        self.assertLess(gate, stop_attempt)
        self.assertLess(stop_attempt, stop_call)
        self.assertLess(stop_call, bootstrap)

        catch = self.updater.index("\ncatch {", bootstrap)
        recovery = self.updater.index(
            "if ($platformStopAttempted -and $wasRunning -and -not $platformRestarted)",
            catch,
        )
        recovery_start = self.updater.index(
            "-Arguments @('-Action', 'Start', '-NoNotify')",
            recovery,
        )
        self.assertLess(catch, recovery)
        self.assertLess(recovery, recovery_start)
        self.assertIn("'pre-update-platform-stop'", self.updater)
        self.assertIn("'update-recovery-platform-start'", self.updater)
        self.assertIn("-Restarted:$platformRestarted", self.updater[catch:])

        target_contract = self.updater.split(
            "function Test-CapTargetSelfUpdateContract",
            1,
        )[1].split("function Save-CapDecisionState", 1)[0]
        self.assertIn("'pre-update-platform-stop'", target_contract)
        self.assertIn("'update-recovery-platform-start'", target_contract)

    def test_tray_update_completion_does_not_depend_on_inherited_pipes(self) -> None:
        self.assertIn("platform-update-result.json", self.updater)
        self.assertIn("Write-CapUpdateAtomicJson -Path $ResultPath -Value $result", self.updater)
        self.assertIn("-CaptureOutput:$false", self.updater)
        self.assertIn("$startInfo.RedirectStandardOutput = $CaptureOutput", self.updater)
        self.assertIn("$startInfo.RedirectStandardError = $CaptureOutput", self.updater)

        self.assertIn("platform-update-result.json", self.tray_update)
        self.assertIn("Read-CapUpdateTrayResult", self.tray_update)
        self.assertIn("$startInfo.RedirectStandardOutput = $false", self.tray_update)
        self.assertIn("$startInfo.RedirectStandardError = $false", self.tray_update)
        self.assertNotIn("ReadToEndAsync", self.tray_update)
        self.assertNotIn("CapTrayUpdateStdoutTask", self.tray_update)
        self.assertNotIn("CapTrayUpdateStderrTask", self.tray_update)

    def test_tray_rejects_stale_or_foreign_terminal_results(self) -> None:
        self.assertIn("process_id = $PID", self.updater)
        for marker in (
            "[int]$ExpectedProcessId",
            "[datetimeoffset]$StartedAt",
            "$result.process_id -ne $ExpectedProcessId",
            "[string]$result.action -cne 'update'",
            "[string]$result.completed_at",
            "$completedAt -lt $StartedAt.ToUniversalTime()",
            "Read-CapUpdateTrayResult -ExpectedProcessId $processId -StartedAt $startedAt",
        ):
            self.assertIn(marker, self.tray_update)

        read = self.tray_update.index(
            "Read-CapUpdateTrayResult -ExpectedProcessId $processId -StartedAt $startedAt"
        )
        clear = self.tray_update.index("Clear-CapUpdateTrayProcess", read)
        self.assertLess(read, clear)

        target_contract = self.updater.split(
            "function Test-CapTargetSelfUpdateContract",
            1,
        )[1].split("function Save-CapDecisionState", 1)[0]
        self.assertIn("'ExpectedProcessId'", target_contract)
        self.assertIn("'completed_at'", target_contract)
        self.assertIn("'process_id = $PID'", target_contract)

    def test_tray_does_not_kill_an_active_update(self) -> None:
        exit_handler = self.tray.split("$exitItem.add_Click({", 1)[1]
        exit_handler = exit_handler.split("Refresh-VisualState", 1)[0]
        self.assertIn("if (Test-CapUpdateTrayBusy)", exit_handler)
        self.assertIn("return", exit_handler)
        self.assertIn("Never kill an updater", self.tray_update)
        self.assertIn("tray only observes its terminal exit", self.tray_update)
        self.assertNotIn(".Kill(", self.tray_update)


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

    @unittest.skipUnless(os.name == "nt", "Windows updater orchestration requires Windows")
    def test_running_platform_is_quiesced_before_bootstrap_and_restarted_after_failure(self) -> None:
        scripts = self.source / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)

        action_log = self.root / "actions.log"
        tunnel_sentinel = self.root / "tunnel-running.txt"
        tunnel_sentinel.write_text("running\n", encoding="utf-8")
        local_appdata = self.root / "localappdata"
        state_dir = local_appdata / "ChatAgentPlatform" / "state"
        manager_dir = local_appdata / "ChatAgentPlatform" / "app" / "scripts"
        state_dir.mkdir(parents=True, exist_ok=True)
        manager_dir.mkdir(parents=True, exist_ok=True)

        desired_state = state_dir / "desired-state.json"
        desired_state.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "desired_state": "running",
                    "source": "user_action",
                    "updated_at": "2026-09-11T00:00:00Z",
                }
            ),
            encoding="utf-8",
        )
        update_state = state_dir / "platform-update.json"
        update_state.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "repository": "BogdanAIP/chat-agent-platform",
                    "branch": "main",
                    "installed_commit_sha": self.first,
                    "installed_at": "2026-09-11T00:00:00Z",
                    "status": "current",
                    "target_commit_sha": self.first,
                    "last_checked_at": "2026-09-11T00:00:00Z",
                    "last_error": None,
                }
            ),
            encoding="utf-8",
        )

        manager = manager_dir / "chat-platform.ps1"
        manager.write_text(
            """[CmdletBinding()]
param(
    [ValidateSet('Start', 'Stop')]
    [string]$Action,
    [switch]$NoNotify
)
$ErrorActionPreference = 'Stop'
Add-Content -LiteralPath $env:CAP_TEST_ACTION_LOG -Value $Action -Encoding utf8
if ($Action -eq 'Stop') {
    Remove-Item -LiteralPath $env:CAP_TEST_TUNNEL_SENTINEL -Force -ErrorAction SilentlyContinue
    '{"schema_version":1,"desired_state":"stopped","source":"user_action","updated_at":"2026-09-11T00:00:01Z"}' |
        Set-Content -LiteralPath $env:CAP_TEST_DESIRED_STATE -Encoding utf8
}
else {
    Set-Content -LiteralPath $env:CAP_TEST_TUNNEL_SENTINEL -Value 'running' -Encoding utf8
    '{"schema_version":1,"desired_state":"running","source":"user_action","updated_at":"2026-09-11T00:00:02Z"}' |
        Set-Content -LiteralPath $env:CAP_TEST_DESIRED_STATE -Encoding utf8
}
exit 0
""",
            encoding="utf-8",
        )

        (scripts / "bootstrap-chat-platform.ps1").write_text(
            """# chat-platform-tray-update.ps1
# chat-platform-update-core.ps1
# chat-platform-update.ps1
# MAIN_UPDATE_UI=tray-more-menu
# MAIN_UPDATER_INSTALLED=True
$ErrorActionPreference = 'Stop'
Add-Content -LiteralPath $env:CAP_TEST_ACTION_LOG -Value 'Bootstrap' -Encoding utf8
if (Test-Path -LiteralPath $env:CAP_TEST_TUNNEL_SENTINEL -PathType Leaf) {
    exit 90
}
exit 92
""",
            encoding="utf-8",
        )
        (scripts / "chat-platform-tray.ps1").write_text(
            "# chat-platform-tray-update.ps1 Register-CapUpdateTrayMenu\n",
            encoding="utf-8",
        )
        (scripts / "chat-platform-tray-update.ps1").write_text(
            "# Register-CapUpdateTrayMenu '-Action', 'Update' platform-update-result.json\n",
            encoding="utf-8",
        )
        (scripts / "chat-platform-update-core.ps1").write_text(
            "# CapUpdateOfficialRemote CapUpdateBranch Sync-CapUpdateMain\n",
            encoding="utf-8",
        )
        (scripts / "chat-platform-update.ps1").write_text(
            (
                "# CapUpdateOfficialRemote New-CapUpdateWorktree "
                "Publish-CapInstalledVersionFromSource "
                "pre-update-platform-stop update-recovery-platform-start\n"
            ),
            encoding="utf-8",
        )
        run(["git", "add", "scripts"], cwd=self.source)
        run(["git", "commit", "-m", "target with self-update contract"], cwd=self.source)
        target = run(["git", "rev-parse", "HEAD"], cwd=self.source)
        run(["git", "push", "origin", "main"], cwd=self.source)

        harness = self.root / "harness"
        harness.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CORE, harness / CORE.name)
        updater_text = UPDATER.read_text(encoding="utf-8")
        fixed_source = "$RemoteUrl = $script:CapUpdateOfficialRemote"
        self.assertEqual(updater_text.count(fixed_source), 1)
        updater_text = updater_text.replace(
            fixed_source,
            f"$RemoteUrl = {ps_quote(self.remote)}",
        )
        harness_updater = harness / UPDATER.name
        harness_updater.write_text(updater_text, encoding="utf-8")

        env = os.environ.copy()
        env["LOCALAPPDATA"] = str(local_appdata)
        env["CAP_TEST_ACTION_LOG"] = str(action_log)
        env["CAP_TEST_TUNNEL_SENTINEL"] = str(tunnel_sentinel)
        env["CAP_TEST_DESIRED_STATE"] = str(desired_state)
        result = subprocess.run(
            [
                shutil.which("pwsh") or "pwsh",
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(harness_updater),
                "-Action",
                "Update",
            ],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            1,
            msg=f"stdout={result.stdout}\nstderr={result.stderr}",
        )

        actions = action_log.read_text(encoding="utf-8-sig").splitlines()
        self.assertEqual(actions, ["Stop", "Bootstrap", "Start"])
        self.assertTrue(tunnel_sentinel.is_file())
        self.assertEqual(
            json.loads(desired_state.read_text(encoding="utf-8-sig"))["desired_state"],
            "running",
        )

        terminal = json.loads(
            (state_dir / "platform-update-result.json").read_text(encoding="utf-8-sig")
        )
        self.assertEqual(terminal["status"], "error")
        self.assertTrue(terminal["restarted"])
        self.assertIn("bootstrap-chat-platform failed with exit code 92", terminal["reason"])

        final_state = json.loads(update_state.read_text(encoding="utf-8-sig"))
        self.assertEqual(final_state["status"], "error")
        self.assertEqual(final_state["installed_commit_sha"], self.first)
        self.assertEqual(final_state["target_commit_sha"], target)

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
