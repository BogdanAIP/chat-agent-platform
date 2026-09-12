import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from urllib.parse import parse_qs, urlparse


ROOT = pathlib.Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "launch-chatgpt-deeplink-autosend.ps1"
REGISTRAR = ROOT / "scripts" / "register-chatgpt-deeplink-autosend-probe.ps1"


@unittest.skipUnless(os.name == "nt", "target-Windows Task Scheduler probe")
class ChatGptDeepLinkSchedulerProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pwsh = shutil.which("pwsh.exe") or shutil.which("pwsh")
        if cls.pwsh is None:
            raise unittest.SkipTest("PowerShell 7 is required")

    def test_launcher_builds_bound_url_without_launching(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_path = pathlib.Path(temp_dir) / "probe.txt"
            prompt_path.write_text(
                "Use only Chat Local Bridge Test. Call workspace_read exactly once.",
                encoding="utf-8",
            )
            run_id = "autosend-test-20260829-001"
            result = self._run_json(
                LAUNCHER,
                "-PromptBodyPath",
                str(prompt_path),
                "-RunId",
                run_id,
                "-NoLaunch",
            )

        self.assertFalse(result["launched"])
        self.assertEqual(result["run_id"], run_id)
        parsed = urlparse(result["url"])
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "chatgpt.com")
        query = parse_qs(parsed.query)
        self.assertEqual(query["cap_autosend"], ["1"])
        self.assertEqual(query["cap_run_id"], [run_id])
        self.assertEqual(query["cap_plugin"], ["Chat Local Bridge Test"])
        prompt = query["prompt"][0]
        self.assertIn("@Chat Local Bridge Test DEEPLINK_AUTOSEND_WAKE", prompt)
        self.assertIn(f"CAP_AUTOSEND_RUN_ID={run_id}", prompt)
        self.assertIn("Call workspace_read exactly once.", prompt)

    def test_launcher_rejects_body_that_forges_run_id_sentinel(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_path = pathlib.Path(temp_dir) / "bad.txt"
            prompt_path.write_text(
                "CAP_AUTOSEND_RUN_ID=forged-run-id\nDo something.", encoding="utf-8"
            )
            completed = subprocess.run(
                [
                    self.pwsh,
                    "-NoLogo",
                    "-NoProfile",
                    "-File",
                    str(LAUNCHER),
                    "-PromptBodyPath",
                    str(prompt_path),
                    "-RunId",
                    "autosend-test-20260829-002",
                    "-NoLaunch",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("launcher owns the run-id sentinel", completed.stderr)

    def test_registrar_dry_run_is_one_shot_interactive_limited(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_path = pathlib.Path(temp_dir) / "probe.txt"
            prompt_path.write_text("Probe body", encoding="utf-8")
            at = (dt.datetime.now() + dt.timedelta(minutes=5)).isoformat()
            result = self._run_json(
                REGISTRAR,
                "-PromptBodyPath",
                str(prompt_path),
                "-At",
                at,
                "-TaskName",
                "CAP-Hosted-DryRun-Probe",
                "-NoRegister",
            )

        self.assertFalse(result["registered"])
        self.assertEqual(result["task_name"], "CAP-Hosted-DryRun-Probe")
        self.assertEqual(result["logon_type"], "Interactive")
        self.assertEqual(result["run_level"], "Limited")
        self.assertIn("launch-chatgpt-deeplink-autosend.ps1", result["arguments"])
        self.assertIn("-PromptBodyPath", result["arguments"])
        self.assertNotIn("-RunId", result["arguments"])
        self.assertNotIn("Daily", result["arguments"])
        self.assertNotIn("Repetition", result["arguments"])

    def test_registrar_source_has_one_once_trigger_and_no_recurring_trigger(self):
        source = REGISTRAR.read_text(encoding="utf-8")
        self.assertEqual(source.count("New-ScheduledTaskTrigger -Once"), 1)
        for forbidden in ("-Daily", "-Weekly", "RepetitionInterval", "AtStartup", "AtLogOn"):
            self.assertNotIn(forbidden, source)
        self.assertIn("-MultipleInstances IgnoreNew", source)
        self.assertIn("-LogonType Interactive", source)
        self.assertIn("-RunLevel Limited", source)

    def _run_json(self, script, *args):
        completed = subprocess.run(
            [self.pwsh, "-NoLogo", "-NoProfile", "-File", str(script), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)


if __name__ == "__main__":
    unittest.main()
