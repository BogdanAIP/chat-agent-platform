import ast
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "config" / "stage26-openadapt-lock.json"
HARNESS_PATH = ROOT / "scripts" / "stage26-openadapt-capture-qualification.ps1"
FIXTURE_PATH = ROOT / "scripts" / "stage26-windows-capture-fixture.ps1"
DRIVER_PATH = ROOT / "scripts" / "stage26-openadapt-capture-driver.py"


class Stage26OpenAdaptCaptureQualificationTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        self.harness = HARNESS_PATH.read_text(encoding="utf-8")
        self.fixture = FIXTURE_PATH.read_text(encoding="utf-8")
        self.driver = DRIVER_PATH.read_text(encoding="utf-8")

    def test_python_driver_parses(self):
        ast.parse(self.driver)

    def test_ffmpeg_asset_is_exact_and_bound_to_pinned_desktop_manifest(self):
        asset = self.lock["qualification_assets"]["ffmpeg_windows_x86_64"]
        desktop = self.lock["upstreams"]["openadapt_desktop"]
        self.assertEqual(asset["source_repository"], "OpenAdaptAI/openadapt-desktop")
        self.assertEqual(asset["source_commit"], desktop["commit"])
        self.assertEqual(asset["manifest_path"], "src-tauri/ffmpeg-runtime-manifest.json")
        self.assertEqual(asset["runtime_version"], "8.1.2-r1")
        self.assertEqual(asset["target"], "x86_64-pc-windows-msvc")
        self.assertEqual(asset["license"], "LGPL-2.1-or-later")
        for name in ("archive_sha256", "ffmpeg_sha256", "ffprobe_sha256"):
            self.assertRegex(asset[name], r"^[0-9a-f]{64}$", name)
        self.assertIn("--disable-network", asset["required_build_properties"])
        self.assertIn("encoder:mpeg4", asset["required_build_properties"])
        self.assertIn("encoder:png", asset["required_build_properties"])

    def test_harness_uses_lock_driven_exact_upstreams_and_ffmpeg_hashes(self):
        self.assertIn("stage26-openadapt-lock.json", self.harness)
        self.assertIn("openadapt-flow[windows]", self.harness)
        self.assertIn("direct_url.json", self.harness)
        self.assertIn("Invoke-WebRequest", self.harness)
        self.assertIn("Assert-FileSha256", self.harness)
        self.assertIn("ffmpeg_windows_x86_64", self.harness)
        self.assertIn("-buildconf", self.harness)
        self.assertIn("--disable-network", self.harness)
        for entry in self.lock["upstreams"].values():
            self.assertNotIn(entry["commit"], self.harness)
        ffmpeg_url = self.lock["qualification_assets"]["ffmpeg_windows_x86_64"]["url"]
        self.assertNotIn(ffmpeg_url, self.harness)

    def test_real_human_input_is_required_and_synthetic_input_is_absent(self):
        combined = "\n".join((self.harness, self.driver, self.fixture))
        for forbidden in (
            "pyautogui",
            "SendInput",
            "keybd_event",
            "mouse_event",
            "SetCursorPos",
        ):
            self.assertNotIn(forbidden.lower(), combined.lower())
        self.assertIn("physical-user-input path", self.driver)
        self.assertIn("OpenAdapt намеренно отбрасывает injected input", self.harness)

    def test_capture_is_window_scoped_structural_and_video_backed(self):
        for required in (
            "capture_video=True",
            "capture_audio=False",
            "capture_images=False",
            "capture_structural_observations=True",
            "capture_browser_events=False",
            "capture_full_video=False",
            "ffmpeg_path=str(ffmpeg_path)",
            "ffprobe_path=str(ffprobe_path)",
            'window={"owner": None, "title": window_title}',
        ):
            self.assertIn(required, self.driver)
        self.assertIn("CaptureSession.load(raw_dir)", self.driver)
        self.assertIn("foreign_structural_window_pass", self.driver)
        self.assertIn("raw_uia_evidence_pass", self.driver)
        self.assertIn("window_scope_pass", self.driver)
        self.assertIn("video_evidence_pass", self.driver)

    def test_expected_physical_sequence_is_explicit(self):
        self.assertIn('REQUIRED_FLOW_KINDS = {"click", "type", "key", "scroll"}', self.driver)
        self.assertIn('EXPECTED_TEXT = "CAPTURE_OK"', self.driver)
        self.assertIn('EXPECTED_KEY = "Enter"', self.driver)
        for state in (
            "start_clicked",
            "text_ok",
            "enter_pressed",
            "scroll_seen",
            "finish_clicked",
        ):
            self.assertIn(state, self.fixture)
        self.assertIn("$listBox.Focus()", self.fixture)

    def test_window_scoped_surface_contract_is_not_falsified(self):
        self.assertIn('EXPECTED_WINDOW_SCOPED_SURFACE = "rdp"', self.driver)
        self.assertIn("backend_kind=EXPECTED_WINDOW_SCOPED_SURFACE", self.driver)
        self.assertIn("surface_contract_pass", self.driver)
        self.assertNotIn('target_surface="windows"', self.driver)
        self.assertIn("native_windows_replay_claimed", self.driver)
        self.assertIn('"native_windows_replay_claimed": False', self.driver)

    def test_raw_uia_containment_uses_native_identity_not_form_text_only(self):
        # The first real target run proved WinForms UIA can expose AccessibleName
        # as the top-level title. Qualification must therefore bind evidence to
        # its owned process/HWND and fail closed on explicit mismatches rather
        # than treating a title alias as a foreign application.
        self.assertIn("_structural_identity_record", self.driver)
        self.assertIn("process_id", self.driver)
        self.assertIn("native_window_handle", self.driver)
        self.assertIn("captured_window_id", self.driver)
        self.assertIn("pid_match is False or handle_match is False", self.driver)
        self.assertNotIn("args.window_title.lower() not in title.lower()", self.driver)

    def test_raw_uia_is_required_but_explicit_rdp_conversion_suppresses_it(self):
        # Raw Capture on the local WinForms fixture must really observe UIA.
        self.assertIn('"raw_uia_evidence_pass": False', self.driver)
        self.assertIn('result["raw_structural_action_count"] > 0', self.driver)
        self.assertIn('result["uia_evidence_pass"] = result["raw_uia_evidence_pass"]', self.driver)
        # Pinned Flow suppresses local client-window UIA only when the live
        # orchestration explicitly identifies the replay substrate as rdp or
        # citrix. The real target run exposed that window scope alone is not
        # enough, so Stage 26.1B must pass backend_kind explicitly.
        self.assertIn("backend_kind=EXPECTED_WINDOW_SCOPED_SURFACE", self.driver)
        self.assertIn('"window_scoped_structural_suppression_pass": False', self.driver)
        self.assertIn('result["structural_event_count"] == 0', self.driver)
        self.assertIn('result["compiled_structural_count"] == 0', self.driver)
        self.assertIn("window_scoped_structural_suppression_pass", self.driver)

    def test_unaccepted_windows_executor_and_production_runtime_are_not_called(self):
        combined = "\n".join((self.harness, self.driver, self.fixture))
        for forbidden in (
            "/execute_windows",
            "allow-legacy-exec",
            "WindowsBackend(",
            "semantic-projection-runtime.ps1 -Action",
            "start-chat-profile.ps1",
            "stop-chat-profile.ps1",
            "start-semantic-profile.ps1",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertIn("SKIPPED_UNACCEPTED_WINDOWS_EXECUTOR", self.driver)
        self.assertIn('"bounded_replay_refusal": True', self.driver)

    def test_harness_does_not_manage_user_chrome_or_other_user_processes(self):
        self.assertIn("Get-Process chrome", self.harness)
        self.assertNotRegex(self.harness, re.compile(r"Stop-Process", re.I))
        self.assertNotRegex(self.harness, re.compile(r"taskkill", re.I))
        self.assertIn("ProcessStartInfo", self.harness)
        self.assertIn("ArgumentList.Add", self.harness)
        self.assertNotIn("Start-Process", self.harness)
        self.assertIn("$fixtureProcess.Kill($true)", self.harness)
        self.assertNotIn("Get-Process pwsh", self.harness)

    def test_raw_artifacts_stay_local_and_replay_remains_refused(self):
        self.assertIn("raw_artifact_containment_pass", self.harness)
        self.assertIn("$containmentRoot", self.harness)
        self.assertIn("SKIPPED_UNACCEPTED_WINDOWS_EXECUTOR", self.driver)
        self.assertIn("bounded_replay_refusal", self.driver)
        self.assertIn("fixture_cleanup_pass", self.harness)

    def test_harness_surfaces_raw_uia_and_structural_suppression_results(self):
        self.assertIn("raw_uia_evidence_pass", self.harness)
        self.assertIn("window_scoped_structural_suppression_pass", self.harness)
        self.assertIn("RAW_UIA_EVIDENCE_PASS", self.harness)
        self.assertIn("WINDOW_SCOPED_STRUCTURAL_SUPPRESSION_PASS", self.harness)


if __name__ == "__main__":
    unittest.main()
