from __future__ import annotations

from unittest import mock
import unittest

from runtime.agent_sessions import chatgpt_temporary_authenticated_controller as controller
from runtime.control_plane.delegation_state import DelegationStateError


class _TransientBusyState:
    def __init__(self, busy_calls: int) -> None:
        self.busy_calls = busy_calls
        self.calls = 0

    def status(self) -> dict[str, object]:
        self.calls += 1
        if self.calls <= self.busy_calls:
            raise BlockingIOError("task_already_running")
        return {"schema_version": 1, "status": "ready"}


class TemporaryStatusLockRetryTests(unittest.TestCase):
    def test_transient_busy_status_is_retried_then_succeeds(self) -> None:
        state = _TransientBusyState(busy_calls=2)
        with mock.patch.object(controller.time, "sleep") as sleep:
            result = controller._status_with_transient_lock_retry(state)

        self.assertEqual("ready", result["status"])
        self.assertEqual(3, state.calls)
        self.assertEqual(2, sleep.call_count)
        sleep.assert_called_with(controller.STATUS_LOCK_RETRY_DELAY_SECONDS)

    def test_persistent_busy_status_becomes_compact_controller_error(self) -> None:
        state = _TransientBusyState(busy_calls=controller.STATUS_LOCK_RETRY_ATTEMPTS + 2)
        with mock.patch.object(controller.time, "sleep") as sleep:
            with self.assertRaisesRegex(DelegationStateError, "delegation status temporarily busy"):
                controller._status_with_transient_lock_retry(state)

        self.assertEqual(controller.STATUS_LOCK_RETRY_ATTEMPTS, state.calls)
        self.assertEqual(controller.STATUS_LOCK_RETRY_ATTEMPTS - 1, sleep.call_count)


if __name__ == "__main__":
    unittest.main()
