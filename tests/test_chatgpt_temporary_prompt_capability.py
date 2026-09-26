from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
import unittest

from runtime.agent_sessions import (
    chatgpt_temporary,
    chatgpt_temporary_controller,
    source_attestation,
)
from runtime.control_plane.delegation_state import WORKER_PROFILE


PRIVATE_REVIEW_NONCE = "9" * 64
EXPECTED_HEAD = "8" * 40
LAUNCH_HANDLE = "7" * 64
EXECUTION_GENERATION = "6" * 64


def _task() -> str:
    return "\n".join(
        [
            "REVIEW_REQUEST_V1",
            "repository=BogdanAIP/chat-agent-platform",
            "pr_number=159",
            f"review_run_id={PRIVATE_REVIEW_NONCE}",
        ]
    )


def _identity(task: str) -> dict[str, str]:
    return {
        "parent_task_id": "review-capability-url-regression",
        "subgoal_id": "pr-159-capability-url-regression",
        "worker_kind": "code-review",
        "worker_profile": WORKER_PROFILE,
        "task_sha256": chatgpt_temporary.task_sha256(task),
        "result_contract_id": "review_result_v1",
    }


def _runtime_attestation() -> dict[str, object]:
    assets = {
        name: f"{index + 1:x}".rjust(64, "0")
        for index, name in enumerate(source_attestation.RUNTIME_ASSETS)
    }
    return {
        "schema_version": 1,
        "adapter_id": source_attestation.ADAPTER_ID,
        "execution_generation": EXECUTION_GENERATION,
        "assets": assets,
    }


def _expected_runtime_attestation() -> dict[str, object]:
    value = _runtime_attestation()
    return {
        "schema_version": value["schema_version"],
        "adapter_id": value["adapter_id"],
        "expected_head": EXPECTED_HEAD,
        "execution_generation": value["execution_generation"],
        "assets": value["assets"],
    }


class ChatGPTTemporaryPromptCapabilityTests(unittest.TestCase):
    def assert_capability_free_task_url(self, url: str, prompt: str) -> None:
        parsed = urlsplit(url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        self.assertEqual("https", parsed.scheme)
        self.assertEqual("chatgpt.com", parsed.netloc)
        self.assertNotIn("prompt", query)
        self.assertNotIn(PRIVATE_REVIEW_NONCE, unquote(url))
        self.assertNotIn(prompt, unquote(url))

    def test_generic_launch_url_never_contains_capability_bearing_prompt(self) -> None:
        task = _task()
        identity = _identity(task)
        with tempfile.TemporaryDirectory() as temp_dir:
            launch = chatgpt_temporary.prepare_temporary_session(
                identity,
                task=task,
                launch_handle=LAUNCH_HANDLE,
                state_root=Path(temp_dir),
            )

        prompt = chatgpt_temporary.build_worker_prompt(
            launch.identity,
            delegation_id=launch.delegation_id,
            delivery_id=launch.delivery_id,
            task=task,
        )
        self.assertIn(PRIVATE_REVIEW_NONCE, prompt)
        self.assert_capability_free_task_url(launch.launch_url, prompt)

    def test_authenticated_preflight_hands_prompt_in_body_not_navigation_url(self) -> None:
        task = _task()
        identity = _identity(task)
        expected = _expected_runtime_attestation()
        runtime_report = _runtime_attestation()

        with tempfile.TemporaryDirectory() as state_dir, tempfile.TemporaryDirectory() as output_dir:
            runtime = chatgpt_temporary_controller.TemporaryControllerRuntime(
                identity_value=identity,
                task=task,
                expected_runtime_attestation_value=expected,
                state_root=Path(state_dir),
                output_dir=Path(output_dir),
            )
            self.assertIsNotNone(runtime.preflight_id)
            preflight_projection = json.loads(runtime.preflight_path.read_text(encoding="utf-8"))
            self.assertNotIn(PRIVATE_REVIEW_NONCE, json.dumps(preflight_projection, sort_keys=True))
            self.assertNotIn("prompt", preflight_projection)
            response = runtime.prepare_live_handoff(
                {
                    "schema_version": 1,
                    "preflight_id": runtime.preflight_id,
                    "execution_generation": EXECUTION_GENERATION,
                    "runtime_attestation": runtime_report,
                }
            )

        prompt = response["prompt"]
        self.assertIsInstance(prompt, str)
        self.assertIn(PRIVATE_REVIEW_NONCE, prompt)
        self.assertEqual(
            response["prompt_sha256"],
            hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        )
        self.assert_capability_free_task_url(response["launch_url"], prompt)


if __name__ == "__main__":
    unittest.main()
