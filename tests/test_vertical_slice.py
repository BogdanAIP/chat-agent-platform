from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_platform.binding import resolve_project
from agent_platform.audit import render_capability_audit
from agent_platform.bootstrap import build_bootstrap_context
from agent_platform.contracts import load_schema, validate_contract
from agent_platform.errors import BindingError, PolicyDenied, ValidationError
from agent_platform.policy import PolicyEnforcementPoint
from agent_platform.service import build_runtime_profile, inspect_file


REPO_ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is required")
class VerticalSliceTests(unittest.TestCase):
    def test_real_wav_flows_through_artifact_policy_and_ffmpeg(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "tone.wav"
            subprocess.run(
                [
                    shutil.which("ffmpeg"),
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=1000:sample_rate=48000:duration=1",
                    "-ac",
                    "2",
                    str(source),
                ],
                check=True,
            )
            result = inspect_file(
                REPO_ROOT,
                source,
                project_id="demo",
                requested_risk_hint="low",
            )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"]["sample_rate_hz"], 48000)
        self.assertEqual(result["result"]["channels"], 2)
        self.assertGreater(result["result"]["duration_seconds"], 0)
        self.assertIsInstance(result["result"]["integrated_lufs"], float)
        self.assertIsInstance(result["result"]["true_peak_dbtp"], float)
        self.assertTrue(result["provenance"]["validated"])
        self.assertTrue(result["artifact_refs"][0]["artifact_id"].startswith("art_"))

    def test_project_binding_does_not_guess_unknown_project(self) -> None:
        with self.assertRaises(BindingError):
            resolve_project(REPO_ROOT, "neighbor-project")

    def test_low_risk_hint_cannot_bypass_denied_policy(self) -> None:
        binding = resolve_project(REPO_ROOT, "demo")
        pep = PolicyEnforcementPoint(binding.policy_path)
        with self.assertRaises(PolicyDenied):
            pep.evaluate(
                "shell.run_arbitrary",
                parameters={},
                data_class="project",
                requested_risk_hint="low",
            )

    def test_versioned_configs_are_json_compatible_yaml(self) -> None:
        for filename in (
            "projects.yaml",
            "capability-requirements.yaml",
            "policy.yaml",
            "contracts.yaml",
        ):
            value = json.loads((REPO_ROOT / "config" / filename).read_text(encoding="utf-8"))
            self.assertIn("contract_version", value)

    def test_silence_has_json_safe_loudness_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "silence.wav"
            subprocess.run(
                [
                    shutil.which("ffmpeg"),
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=sample_rate=48000:channel_layout=stereo",
                    "-t",
                    "0.5",
                    str(source),
                ],
                check=True,
            )
            result = inspect_file(REPO_ROOT, source, project_id="demo")
        self.assertIn(result["result"]["integrated_lufs_status"], {"measured", "below_measurement_floor"})
        value = result["result"]["integrated_lufs"]
        self.assertTrue(value is None or isinstance(value, float))
        peak = result["result"]["true_peak_dbtp"]
        self.assertTrue(peak is None or isinstance(peak, float))
        json.dumps(result, allow_nan=False)

    def test_bootstrap_loads_only_minimal_context_and_capability_slice(self) -> None:
        result = build_bootstrap_context(
            REPO_ROOT, project_id="demo", capability="media.inspect"
        )
        self.assertEqual(
            set(result["minimal_context"]),
            {"CURRENT_STATE.md", "ARCHITECTURE.md", "CONSTRAINTS.md"},
        )
        self.assertEqual(result["capability_requirement"]["capability"], "media.inspect")
        self.assertTrue(
            result["relevant_skill"].endswith("project-skills\\media-inspection\\SKILL.md")
        )

    def test_contract_schemas_are_valid_and_reject_bad_request(self) -> None:
        for filename in (
            "tool-request-v1.schema.json",
            "tool-v1.schema.json",
            "artifact-v1.schema.json",
            "policy-decision-v1.schema.json",
            "secret-ref-v1.schema.json",
            "job-v1.schema.json",
        ):
            self.assertEqual(
                load_schema(filename)["$schema"],
                "https://json-schema.org/draft/2020-12/schema",
            )
        with self.assertRaises(ValidationError):
            validate_contract({"contract_version": "tool-v1"}, "tool-request-v1.schema.json")
        fixtures = REPO_ROOT / "contracts" / "fixtures"
        valid = json.loads((fixtures / "tool-request.valid.json").read_text(encoding="utf-8"))
        invalid = json.loads(
            (fixtures / "tool-request.invalid-missing-id.json").read_text(encoding="utf-8")
        )
        validate_contract(valid, "tool-request-v1.schema.json")
        with self.assertRaises(ValidationError):
            validate_contract(invalid, "tool-request-v1.schema.json")
        cases = (
            ("tool-v1.schema.json", "tool-result.valid.json", "tool-result.invalid-status.json"),
            ("artifact-v1.schema.json", "artifact.valid.json", "artifact.invalid-hash.json"),
            ("policy-decision-v1.schema.json", "policy-decision.valid.json", "policy-decision.invalid-risk.json"),
            ("secret-ref-v1.schema.json", "secret-ref.valid.json", "secret-ref.invalid-empty-acl.json"),
            ("job-v1.schema.json", "job.valid.json", "job.invalid-status.json"),
        )
        for schema, valid_name, invalid_name in cases:
            validate_contract(json.loads((fixtures / valid_name).read_text(encoding="utf-8")), schema)
            with self.assertRaises(ValidationError):
                validate_contract(
                    json.loads((fixtures / invalid_name).read_text(encoding="utf-8")), schema
                )

    def test_generated_audit_keeps_requirements_and_runtime_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            isolated_root = Path(temp)
            shutil.copytree(REPO_ROOT / "config", isolated_root / "config")
            (isolated_root / "artifacts").mkdir()
            (isolated_root / "runtime").mkdir()
            profile = build_runtime_profile(isolated_root, project_id="demo")
            (isolated_root / "runtime" / "capability-profile.json").write_text(
                json.dumps(profile), encoding="utf-8"
            )
            audit = render_capability_audit(isolated_root, project_id="demo")
        self.assertIn("`media.inspect`", audit)
        self.assertIn("Runtime verified at:", audit)
        self.assertIn("Hosted Chat/MCP status: `unknown`", audit)
        self.assertIn("Do not edit this file manually", audit)


if __name__ == "__main__":
    unittest.main()
