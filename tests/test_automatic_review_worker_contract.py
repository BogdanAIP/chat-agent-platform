from __future__ import annotations

import ast
from pathlib import Path
import unittest

from runtime.control_plane.independent_review_delegation import build_review_worker_task
from runtime.control_plane.independent_review_state import ReviewIdentity


ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "runtime" / "control_plane" / "automatic_review_worker.py"
DELEGATION = ROOT / "runtime" / "control_plane" / "independent_review_delegation.py"
PROCEDURES = ROOT / "runtime" / "control_plane" / "independent_review_procedures.py"


class AutomaticReviewWorkerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.worker = WORKER.read_text(encoding="utf-8")
        self.delegation = DELEGATION.read_text(encoding="utf-8")
        self.procedures = PROCEDURES.read_text(encoding="utf-8")

    def test_new_python_modules_parse(self) -> None:
        ast.parse(self.worker)
        ast.parse(self.delegation)

    def test_review_task_exposes_public_read_only_evidence_routes(self) -> None:
        identity = ReviewIdentity(
            repository="BogdanAIP/chat-agent-platform",
            pr_number=159,
            base_sha="1" * 40,
            head_sha="2" * 40,
            review_skill="code-review",
            review_skill_version="1.1",
        )
        task = build_review_worker_task(identity, review_run_id="3" * 64)

        self.assertIn(
            "https://api.github.com/repos/BogdanAIP/chat-agent-platform/pulls/159",
            task,
        )
        self.assertIn(
            "https://api.github.com/repos/BogdanAIP/chat-agent-platform/contents/.agents/skills?ref="
            + "2" * 40,
            task,
        )
        self.assertIn(
            "https://raw.githubusercontent.com/BogdanAIP/chat-agent-platform/"
            + "1" * 40
            + "/AGENTS.md",
            task,
        )
        self.assertIn(
            "navigation hints only, not trusted evidence",
            task,
        )
        self.assertIn("prove live PR base.sha and head.sha exactly match this request", task)
        self.assertIn("enumerate every HEAD skill directory entry", task)

    def test_worker_uses_installed_main_receipt_and_fixed_app_root(self) -> None:
        self.assertIn("platform-update.json", self.delegation)
        self.assertIn("installed-version state is unavailable", self.delegation)
        self.assertIn("source_attestation.RUNTIME_ASSETS", self.delegation)
        self.assertIn('value["status"] not in {"current", "update_available"}', self.delegation)
        self.assertIn('value["repository"] != _REPOSITORY', self.delegation)
        self.assertIn('value["branch"] != _BRANCH', self.delegation)
        self.assertIn('"ChatAgentPlatform" / "app"', self.delegation)
        self.assertIn("validate_review_worker_runtime", self.worker)
        self.assertIn("app_root, expected_head =", self.worker)

    def test_worker_opens_only_neutral_preflight_and_never_accepts_url_or_command(self) -> None:
        self.assertIn("cap_agent_preflight=1#cap_preflight_id=", self.worker)
        self.assertIn("os.startfile(url)", self.worker)
        parser_block = self.worker.split("def _parser()", 1)[1]
        for forbidden in ("--url", "--command", "--provider", "--backend", "--python", "--prompt"):
            self.assertNotIn(forbidden, parser_block)

    def test_running_extension_must_attest_exact_installed_assets(self) -> None:
        self.assertIn("source_attestation.RUNTIME_ASSETS", self.delegation)
        self.assertIn("source_attestation.RUNTIME_ASSETS", self.worker)
        self.assertIn("expected-runtime-attestation.json", self.worker)
        self.assertIn("execution_generation.js", self.worker)
        self.assertIn("_sha256_file(path)", self.worker)
        self.assertIn("chatgpt_temporary_authenticated_controller", self.worker)

    def test_dispatch_is_consumed_only_after_installed_runtime_preflight(self) -> None:
        validate = self.procedures.index("validate_review_worker_runtime(")
        mark = self.procedures.index("mark_dispatch_attempted(")
        spawn = self.procedures.index("spawn_review_worker(")
        self.assertLess(validate, mark)
        self.assertLess(mark, spawn)
        self.assertNotIn("mark_dispatch_prepared", self.procedures)
        self.assertNotIn("automatic_relaunch", self.procedures)

    def test_reconcile_can_only_settle_existing_generic_result(self) -> None:
        self.assertIn("settle_review_from_delegation", self.procedures)
        self.assertIn('if "manual_result" in value:', self.procedures)
        self.assertIn(
            'return reconcile_independent_review_result(state_request, state_root=state_root)',
            self.procedures,
        )
        self.assertIn("load_delegation", self.delegation)
        self.assertIn("submit_independent_review_result", self.delegation)
        self.assertNotIn("mark_launch_attempted", self.delegation)
        self.assertNotIn("claim_delivery", self.delegation)


if __name__ == "__main__":
    unittest.main()
