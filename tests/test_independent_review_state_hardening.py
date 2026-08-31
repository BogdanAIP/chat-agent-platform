from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from runtime.control_plane import independent_review_state as review_state
from runtime.control_plane import _verified_workspace_artifact_support as workspace_support


class IndependentReviewStateHardeningTests(unittest.TestCase):
    def identity(self, *, repository: str = "BogdanAIP/chat-agent-platform", version: str = "1.1") -> dict[str, object]:
        return {
            "repository": repository,
            "pr_number": 141,
            "base_sha": "1" * 40,
            "head_sha": "2" * 40,
            "review_skill": "code-review",
            "review_skill_version": version,
        }

    def test_repository_case_aliases_share_one_operation_identity(self) -> None:
        canonical = review_state.parse_review_identity(self.identity())
        alias = review_state.parse_review_identity(
            self.identity(repository="bogdanaip/CHAT-AGENT-PLATFORM")
        )
        self.assertEqual("bogdanaip/chat-agent-platform", canonical.repository)
        self.assertEqual(canonical, alias)
        self.assertEqual(
            review_state.review_operation_key(canonical),
            review_state.review_operation_key(alias),
        )

    def test_skill_version_rejects_noncanonical_numeric_aliases(self) -> None:
        for version in ("01.1", "1.01", "00.00"):
            with self.subTest(version=version):
                with self.assertRaisesRegex(
                    review_state.ReviewStateError,
                    "canonical major.minor",
                ):
                    review_state.parse_review_identity(self.identity(version=version))

    def test_private_nonce_is_not_present_in_prepared_operation_repr(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            prepared = review_state.prepare_review_operation(
                self.identity(),
                state_root=Path(temp) / "procedure-state",
            )
            self.assertNotIn(prepared.review_run_id, repr(prepared))

    def test_reviewer_genesis_uses_private_state_create_not_workspace_pinned_binding(self) -> None:
        # On Windows runtime/control_plane/__init__.py deliberately replaces the
        # workspace-artifact support symbol with a namespace-pinned consequence
        # primitive. Reviewer metadata must not inherit that workspace-only
        # binding merely because it reuses the same create/fsync mechanic.
        self.assertIsNot(
            review_state._exclusive_create_file,
            workspace_support._exclusive_create_file,
        )
        with tempfile.TemporaryDirectory() as temp:
            prepared = review_state.prepare_review_operation(
                self.identity(),
                state_root=Path(temp) / "procedure-state",
            )
            root = review_state._review_root(Path(temp) / "procedure-state")
            genesis_path = review_state._genesis_path(root, prepared.operation_key)
            value = json.loads(genesis_path.read_text(encoding="utf-8"))
            self.assertEqual(prepared.operation_key, value["operation_key"])
            self.assertEqual(prepared.review_run_id, value["review_run_id"])


if __name__ == "__main__":
    unittest.main()
