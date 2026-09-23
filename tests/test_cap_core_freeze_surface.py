from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def _section(source: str, start: str, end: str) -> str:
    start_index = source.index(start)
    end_index = source.index(end, start_index + len(start))
    return source[start_index:end_index]


class CapCoreFreezeSurfaceTests(unittest.TestCase):
    def test_workspace_new_effect_path_has_no_legacy_structural_authority(self) -> None:
        support = (
            ROOT / "runtime" / "control_plane" / "_verified_workspace_artifact_support.py"
        ).read_text(encoding="utf-8")
        active = (
            ROOT / "runtime" / "control_plane" / "verified_workspace_artifact.py"
        ).read_text(encoding="utf-8")

        guard = _section(
            support,
            "def _workspace_guard_decision(",
            "def _record_workspace_attempt(",
        )
        self.assertIn("_WORKSPACE_GUARD.evaluate_authorized(", guard)
        self.assertNotIn("_WORKSPACE_GUARD.evaluate(", guard)
        self.assertIn("concrete workspace grant required before mutation", guard)

        record = _section(
            support,
            "def _record_workspace_attempt(",
            "def _record_legacy_recovery_attempt(",
        )
        self.assertIn("state.record_authorized_attempt(", record)
        self.assertNotIn("state.record_attempt(", record)

        legacy = _section(
            support,
            "def _record_legacy_recovery_attempt(",
            "def _prepared_marker(",
        )
        self.assertEqual(1, legacy.count("state.record_attempt("))
        self.assertIn("already-prepared schema-2 attempt", legacy)

        self.assertNotIn("state.record_attempt(", active)
        recovery = _section(
            active,
            "def _recover_prepared_intent(",
            "def _reconcile_exceptional_delivery(",
        )
        self.assertIn("_record_legacy_recovery_attempt(", recovery)

    def test_windows_case_new_effects_use_only_authorized_core_path(self) -> None:
        source = (
            ROOT / "runtime" / "control_plane" / "windows_case_update.py"
        ).read_text(encoding="utf-8")

        self.assertIn("_WINDOWS_GUARD.evaluate_authorized(", source)
        self.assertIn("state.record_authorized_attempt(", source)
        self.assertNotIn("_WINDOWS_GUARD.evaluate(", source)
        self.assertNotIn("state.record_attempt(", source)

    def test_direct_workspace_write_authorizes_before_provider_and_verifies_after(self) -> None:
        source = (
            ROOT
            / "runtime"
            / "semantic-projection"
            / "bin"
            / "semantic-projection.mjs"
        ).read_text(encoding="utf-8")
        section = _section(
            source,
            "server.registerTool('workspace_write'",
            "server.registerTool('web_open'",
        )

        prepare = section.index("prepareSemanticWorkspaceWrite(")
        authorized = section.index("prepared?.status !== 'authorized'")
        delivery = section.index("providers.callFilesystem('write_file'")
        verification = section.index("verifySemanticWorkspaceWrite(")
        pass_check = section.index("verified.status === 'pass'")
        self.assertLess(prepare, authorized)
        self.assertLess(authorized, delivery)
        self.assertLess(delivery, verification)
        self.assertLess(verification, pass_check)
        self.assertIn("verification_runtime_unavailable", section)

    def test_direct_browser_effects_authorize_before_delivery_and_verify_after(self) -> None:
        source = (
            ROOT
            / "runtime"
            / "semantic-projection"
            / "bin"
            / "semantic-projection.mjs"
        ).read_text(encoding="utf-8")

        web_open = _section(
            source,
            "server.registerTool('web_open'",
            "server.registerTool('web_observe'",
        )
        self.assertLess(
            web_open.index("authorizeSemanticBrowserMutation("),
            web_open.index("providers.callBrowser('browser_navigate'"),
        )
        self.assertLess(
            web_open.index("providers.callBrowser('browser_navigate'"),
            web_open.index("verifyPlaywrightNavigation("),
        )

        interact = _section(
            source,
            "server.registerTool('web_interact'",
            "void serveStdio",
        )
        authorization = interact.index("authorizeSemanticBrowserMutation(")
        visual_delivery = interact.index("router.click(")
        click_delivery = interact.index("providers.callBrowser('browser_click'")
        type_delivery = interact.index("providers.callBrowser('browser_type'")
        verification = interact.index("verifyPlaywrightInteraction(")
        for delivery in (visual_delivery, click_delivery, type_delivery):
            self.assertLess(authorization, delivery)
            self.assertLess(delivery, verification)

    def test_provider_seam_cannot_own_core_authority_or_completion(self) -> None:
        source = (
            ROOT
            / "runtime"
            / "semantic-projection"
            / "lib"
            / "semantic-provider-bindings.mjs"
        ).read_text(encoding="utf-8")

        for forbidden in (
            "CapabilityGrant",
            "AuthorizationRequest",
            "WorkingState",
            "record_authorized_attempt",
            "evaluate_finish_gate",
            "candidate_done",
            "reconciliation",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_core_manifest_freezes_new_effect_authorization_rule(self) -> None:
        manifest = json.loads(
            (ROOT / "runtime" / "control_plane" / "core_v1_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("freeze-candidate", manifest["status"])
        self.assertTrue(
            any(
                "New consequence-bearing delivery must have exact authorization before the effect"
                in rule
                for rule in manifest["rules"]
            )
        )


if __name__ == "__main__":
    unittest.main()
