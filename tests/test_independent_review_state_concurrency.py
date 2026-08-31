from __future__ import annotations

import tempfile
import threading
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


def result_text(*, review_run_id: str | None = None) -> str:
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
        "rejected_candidates=2",
        "reviewed_at=2026-08-31T13:00:00+00:00",
    ]
    if review_run_id is not None:
        lines.append(f"review_run_id={review_run_id}")
    return "\n".join(lines)


class IndependentReviewStateConcurrencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.state_root = Path(self.temp.name) / "procedure-state"
        self.identity = review_state.parse_review_identity(identity_dict())
        self.operation_key = review_state.review_operation_key(self.identity)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_concurrent_first_caller_cannot_create_second_nonce(self) -> None:
        entered_create = threading.Event()
        release_create = threading.Event()
        first_result: list[review_state.PreparedReviewOperation] = []
        first_error: list[BaseException] = []
        original_create = review_state._exclusive_create_file

        def blocking_create(path: Path, data: bytes) -> None:
            entered_create.set()
            if not release_create.wait(timeout=5):
                raise TimeoutError("test did not release genesis create")
            original_create(path, data)

        def first_prepare() -> None:
            try:
                first_result.append(
                    review_state.prepare_review_operation(
                        identity_dict(),
                        state_root=self.state_root,
                    )
                )
            except BaseException as exc:  # pragma: no cover - assertion reports it below
                first_error.append(exc)

        with mock.patch.object(review_state, "_exclusive_create_file", side_effect=blocking_create):
            worker = threading.Thread(target=first_prepare, daemon=True)
            worker.start()
            self.assertTrue(entered_create.wait(timeout=5), "first caller never reached genesis create")
            with self.assertRaisesRegex(BlockingIOError, "task_already_running"):
                review_state.prepare_review_operation(
                    identity_dict(),
                    state_root=self.state_root,
                )
            release_create.set()
            worker.join(timeout=5)

        self.assertFalse(worker.is_alive(), "first caller did not finish")
        self.assertEqual([], first_error)
        self.assertEqual(1, len(first_result))
        self.assertTrue(first_result[0].created)

        later = review_state.prepare_review_operation(
            identity_dict(),
            state_root=self.state_root,
        )
        self.assertFalse(later.created)
        self.assertEqual(first_result[0].review_run_id, later.review_run_id)
        self.assertEqual(first_result[0].operation_key, later.operation_key)

    def test_submit_and_reconcile_use_the_same_operation_lock(self) -> None:
        prepared = review_state.prepare_review_operation(
            identity_dict(),
            state_root=self.state_root,
        )
        review_state.mark_dispatch_attempted(identity_dict(), state_root=self.state_root)
        root = review_state._review_root(self.state_root)
        lock_id = review_state._lock_id(prepared.operation_key)

        with review_state._acquire_task_lock(root, lock_id):
            with self.assertRaisesRegex(BlockingIOError, "task_already_running"):
                review_state.submit_independent_review_result(
                    {
                        "review_run_id": prepared.review_run_id,
                        "result": result_text(review_run_id=prepared.review_run_id),
                    },
                    state_root=self.state_root,
                )
            with self.assertRaisesRegex(BlockingIOError, "task_already_running"):
                review_state.reconcile_independent_review_result(
                    {**identity_dict(), "manual_result": result_text()},
                    state_root=self.state_root,
                )

        pending = review_state.reconcile_independent_review_result(
            identity_dict(),
            state_root=self.state_root,
        )
        self.assertEqual("pending", pending["status"])
        self.assertEqual("open", pending["result_state"])


if __name__ == "__main__":
    unittest.main()
