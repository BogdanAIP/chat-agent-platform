from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import mock
import unittest

from runtime.control_plane import independent_review_state as review_state


BASE_SHA = "1" * 40
HEAD_SHA = "2" * 40


def identity_dict() -> dict[str, object]:
    return {
        "repository": "BogdanAIP/chat-agent-platform",
        "pr_number": 141,
        "base_sha": BASE_SHA,
        "head_sha": HEAD_SHA,
        "review_skill": "code-review",
        "review_skill_version": "1.1",
    }


def automatic_result(review_run_id: str, *, suffix: str = "") -> str:
    lines = [
        "REVIEW_RESULT_V1",
        "repository=BogdanAIP/chat-agent-platform",
        "pr_number=141",
        f"base_sha={BASE_SHA}",
        f"head_sha={HEAD_SHA}",
        f"review_policy_ref={BASE_SHA}",
        "review_skill=code-review",
        "review_skill_version=1.1",
        "review_context=ordinary_chat_fresh",
        "status=PASS",
        "review_validity=CURRENT",
        "reported_findings=0",
        "rejected_candidates=3",
        "reviewed_at=2026-08-31T08:30:48+00:00",
        f"review_run_id={review_run_id}",
    ]
    if suffix:
        lines.extend(["", suffix])
    return "\n".join(lines)


class IndependentReviewStateSizeBoundsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.state_root = Path(self.temp.name) / "procedure-state"
        self.identity = review_state.parse_review_identity(identity_dict())
        self.operation_key = review_state.review_operation_key(self.identity)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _dispatch(self) -> review_state.PreparedReviewOperation:
        prepared = review_state.prepare_review_operation(
            identity_dict(),
            state_root=self.state_root,
        )
        review_state.mark_dispatch_attempted(identity_dict(), state_root=self.state_root)
        return prepared

    def _state_path(self) -> Path:
        root = review_state._review_root(self.state_root)
        return review_state._state_path(root, self.operation_key)

    def test_json_expansion_round_trips_within_result_bound(self) -> None:
        prepared = self._dispatch()
        payload = automatic_result(prepared.review_run_id, suffix="\x01" * 120_000)
        self.assertLess(len(payload.encode("utf-8")), review_state.MAX_RESULT_BYTES)

        recorded = review_state.submit_independent_review_result(
            {"review_run_id": prepared.review_run_id, "result": payload},
            state_root=self.state_root,
        )
        self.assertEqual("recorded", recorded["status"])

        # The old loader limit (MAX_RESULT_BYTES + 32 KiB) rejected this valid
        # checkpoint after JSON escaping expanded the control-byte-heavy body.
        self.assertGreater(
            self._state_path().stat().st_size,
            review_state.MAX_RESULT_BYTES + 32_768,
        )
        self.assertLessEqual(self._state_path().stat().st_size, review_state.MAX_STATE_BYTES)

        reconciled = review_state.reconcile_independent_review_result(
            identity_dict(),
            state_root=self.state_root,
        )
        self.assertEqual("recorded", reconciled["status"])
        self.assertEqual(payload, reconciled["result"])

    def test_encoded_state_bound_is_checked_before_canonical_replace(self) -> None:
        prepared = self._dispatch()
        canonical = self._state_path()
        before = canonical.read_bytes()
        payload = automatic_result(prepared.review_run_id, suffix="x" * 20_000)

        with mock.patch.object(review_state, "MAX_STATE_BYTES", len(before)):
            with self.assertRaisesRegex(
                review_state.ReviewStateError,
                "encoded bound",
            ):
                review_state.submit_independent_review_result(
                    {"review_run_id": prepared.review_run_id, "result": payload},
                    state_root=self.state_root,
                )

        self.assertEqual(before, canonical.read_bytes())
        pending = review_state.reconcile_independent_review_result(
            identity_dict(),
            state_root=self.state_root,
        )
        self.assertEqual("pending", pending["status"])
        self.assertEqual("open", pending["result_state"])


if __name__ == "__main__":
    unittest.main()
