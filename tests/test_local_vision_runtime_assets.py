from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "local-vision-runtime.json"
CONTROLLER = ROOT / "scripts" / "local-vision-runtime.ps1"
WATCHDOG = ROOT / "scripts" / "local-vision-runtime-watchdog.ps1"
ACCEPTANCE = ROOT / "scripts" / "test-local-vision-runtime.ps1"
WORKFLOW = ROOT / ".github" / "workflows" / "stage25-1-vision-runtime.yml"


class LocalVisionRuntimeAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.controller = CONTROLLER.read_text(encoding="utf-8")
        cls.watchdog = WATCHDOG.read_text(encoding="utf-8")
        cls.acceptance = ACCEPTANCE.read_text(encoding="utf-8")

    def test_reviewed_profile_is_exact_f16_target_baseline(self) -> None:
        self.assertEqual(self.config["schema_version"], 1)
        self.assertEqual(self.config["profile"], "lfm25-vl-450m-f16")
        self.assertEqual(self.config["runtime"]["command"], "llama-server")
        self.assertEqual(self.config["runtime"]["host"], "127.0.0.1")
        self.assertEqual(self.config["runtime"]["port"], 3068)
        self.assertEqual(
            self.config["runtime"]["required_version_markers"],
            ["build 10448", "ad1de39e0"],
        )

        model = self.config["artifacts"]["model"]
        mmproj = self.config["artifacts"]["mmproj"]
        self.assertEqual(model["bytes"], 711486624)
        self.assertEqual(
            model["sha256"],
            "f7d130500beadcbe66b78fb7b1222142ccdf4edcb2596026a7ee30b4bafe6989",
        )
        self.assertEqual(mmproj["bytes"], 189126080)
        self.assertEqual(
            mmproj["sha256"],
            "51b458cfdbc736982145a35f798ce37611af0aab639e58b33473ba0c7815fd99",
        )

    def test_reviewed_server_args_preserve_target_configuration(self) -> None:
        args = self.config["server_args"]
        text = " ".join(args)
        for marker in (
            "--device none",
            "--gpu-layers 0",
            "--no-mmproj-offload",
            "--no-op-offload",
            "--threads 8",
            "--threads-batch 8",
            "--fit off",
            "--ctx-size 2048",
            "--batch-size 128",
            "--ubatch-size 64",
            "--cache-type-k q8_0",
            "--cache-type-v q8_0",
            "--image-min-tokens 64",
            "--image-max-tokens 256",
            "--parallel 1",
            "--no-ui",
            "--offline",
        ):
            self.assertIn(marker, text)
        self.assertNotIn("--host", args)
        self.assertNotIn("--port", args)
        self.assertNotIn("--model", args)
        self.assertNotIn("--mmproj", args)

    def test_memory_policy_is_conservative_and_has_idle_unload(self) -> None:
        memory = self.config["memory"]
        self.assertGreaterEqual(memory["min_start_physical_gb"], 1.5)
        self.assertGreaterEqual(memory["min_start_virtual_gb"], 3.0)
        self.assertGreaterEqual(memory["min_run_physical_gb"], 0.5)
        self.assertGreaterEqual(memory["min_run_virtual_gb"], 1.5)
        self.assertGreaterEqual(self.config["idle_ttl_seconds"], 60)
        self.assertLessEqual(self.config["idle_ttl_seconds"], 600)
        self.assertLessEqual(
            self.config["watchdog_interval_seconds"],
            self.config["idle_ttl_seconds"],
        )

    def test_controller_is_owned_fail_closed_not_generic_model_admin(self) -> None:
        for marker in (
            "chat-agent-platform-vision-runtime",
            "Test-OwnedServerProcess",
            "process_start_time_utc",
            "ownership mismatch",
            "occupied by an unowned listener",
            "Confirm-Artifacts",
            "Confirm-RuntimeVersion",
            "Test-MemoryFloor",
            "idle-ttl",
            "resource-pressure",
            "127.0.0.1",
        ):
            self.assertIn(marker, self.controller)
        self.assertIn("CHAT_VISION_RUNTIME_TEST_MODE", self.controller)
        self.assertIn("override is available only", self.controller)
        self.assertNotIn("get-process chrome", self.controller.lower())
        self.assertNotIn("Stop-Process -Name", self.controller)
        self.assertNotIn("Invoke-Expression", self.controller)

    def test_watchdog_can_only_sweep_controller(self) -> None:
        self.assertIn("-Action Sweep", self.watchdog)
        self.assertNotIn("Stop-Process", self.watchdog)
        self.assertNotIn("llama-server", self.watchdog)
        self.assertNotIn("Invoke-Expression", self.watchdog)

    def test_synthetic_windows_acceptance_covers_lifecycle_safety(self) -> None:
        for marker in (
            "VISION_RUNTIME_DOCTOR=PASS",
            "VISION_RUNTIME_IDEMPOTENT_START=PASS",
            "VISION_RUNTIME_IDLE_TTL=PASS",
            "VISION_RUNTIME_EXPLICIT_STOP=PASS",
            "VISION_RUNTIME_ARTIFACT_TAMPER=PASS",
            "VISION_RUNTIME_FOREIGN_PORT=PASS",
            "VISION_RUNTIME_OWNERSHIP_FAIL_CLOSED=PASS",
            "VISION_RUNTIME_ACCEPTANCE=PASS",
        ):
            self.assertIn(marker, self.acceptance)

    def test_dedicated_workflow_exists(self) -> None:
        self.assertTrue(WORKFLOW.is_file())


if __name__ == "__main__":
    unittest.main()
