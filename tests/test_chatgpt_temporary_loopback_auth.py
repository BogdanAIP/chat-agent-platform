from __future__ import annotations

import hashlib
import http.client
import json
import threading
from http.server import ThreadingHTTPServer
import tempfile
from pathlib import Path
import unittest

from runtime.agent_sessions import chatgpt_temporary_authenticated_controller as authenticated
from runtime.agent_sessions.chatgpt_temporary_controller import TemporaryControllerRuntime
from tests.test_chatgpt_temporary_controller import (
    EXECUTION_GENERATION,
    TASK,
    expected_runtime_attestation,
    identity_dict,
    runtime_report,
)


def _json_bytes(value: dict[str, object]) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8")


def _headers(secret: str, method: str, path: str, nonce: str, body: bytes) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        authenticated.AUTH_VERSION_HEADER: authenticated.AUTH_VERSION,
        authenticated.AUTH_NONCE_HEADER: nonce,
        authenticated.AUTH_MAC_HEADER: authenticated._mac_hex(
            secret,
            authenticated._request_auth_input(method, path, nonce, body),
        ),
    }


def _verify_response(
    secret: str,
    method: str,
    path: str,
    nonce: str,
    response: http.client.HTTPResponse,
    body: bytes,
) -> None:
    assert response.getheader(authenticated.AUTH_VERSION_HEADER) == authenticated.AUTH_VERSION
    assert response.getheader(authenticated.AUTH_NONCE_HEADER) == nonce
    supplied = response.getheader(authenticated.AUTH_MAC_HEADER)
    assert supplied is not None
    expected = authenticated._mac_hex(
        secret,
        authenticated._response_auth_input(method, path, nonce, response.status, body),
    )
    assert supplied == expected


class AuthenticatedTemporaryControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.runtime = TemporaryControllerRuntime(
            identity_value=identity_dict(),
            task=TASK,
            expected_runtime_attestation_value=expected_runtime_attestation(),
            state_root=root / "private-state",
            output_dir=root / "output",
        )
        assert self.runtime.preflight_id is not None
        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            authenticated.make_authenticated_handler(self.runtime),
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    def request(
        self,
        method: str,
        path: str,
        *,
        secret: str,
        nonce: str,
        value: dict[str, object] | None = None,
        mac_secret: str | None = None,
    ) -> tuple[int, http.client.HTTPResponse, bytes]:
        body = b"" if value is None else _json_bytes(value)
        headers = _headers(mac_secret or secret, method, path, nonce, body)
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        connection.request(method, path, body=body if body else None, headers=headers)
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response.status, response, payload

    def preflight_body(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "execution_generation": EXECUTION_GENERATION,
            "runtime_attestation": runtime_report(),
        }

    def test_preflight_request_is_authenticated_without_raw_capability_and_response_is_signed(self) -> None:
        secret = self.runtime.preflight_id
        assert secret is not None
        nonce = "1" * 64
        body = self.preflight_body()
        self.assertNotIn("preflight_id", body)
        status, response, payload = self.request(
            "POST",
            "/preflight",
            secret=secret,
            nonce=nonce,
            value=body,
        )
        self.assertEqual(200, status, payload.decode("utf-8", errors="replace"))
        _verify_response(secret, "POST", "/preflight", nonce, response, payload)
        prepared = json.loads(payload.decode("utf-8"))
        self.assertEqual("handoff-prepared", prepared["status"])
        self.assertEqual(64, len(prepared["run_id"]))
        self.assertEqual(64, len(prepared["launch_handle"]))
        self.assertIsNotNone(self.runtime.pending_launch_handle)

    def test_wrong_mac_cannot_reach_preflight_operation(self) -> None:
        secret = self.runtime.preflight_id
        assert secret is not None
        self.assertIsNone(self.runtime.pending_launch_handle)
        status, response, payload = self.request(
            "POST",
            "/preflight",
            secret=secret,
            mac_secret="f" * 64,
            nonce="2" * 64,
            value=self.preflight_body(),
        )
        self.assertEqual(403, status)
        self.assertIsNone(response.getheader(authenticated.AUTH_MAC_HEADER))
        self.assertIsNone(self.runtime.pending_launch_handle)
        self.assertEqual("forbidden", json.loads(payload.decode("utf-8"))["status"])

    def test_replayed_authenticated_nonce_is_rejected_before_second_operation(self) -> None:
        secret = self.runtime.preflight_id
        assert secret is not None
        nonce = "3" * 64
        body = self.preflight_body()
        first_status, first_response, first_payload = self.request(
            "POST",
            "/preflight",
            secret=secret,
            nonce=nonce,
            value=body,
        )
        self.assertEqual(200, first_status)
        _verify_response(secret, "POST", "/preflight", nonce, first_response, first_payload)
        first_handle = self.runtime.pending_launch_handle
        second_status, second_response, _ = self.request(
            "POST",
            "/preflight",
            secret=secret,
            nonce=nonce,
            value=body,
        )
        self.assertEqual(403, second_status)
        self.assertIsNone(second_response.getheader(authenticated.AUTH_MAC_HEADER))
        self.assertEqual(first_handle, self.runtime.pending_launch_handle)

    def test_raw_preflight_capability_on_wire_is_rejected_even_with_valid_mac(self) -> None:
        secret = self.runtime.preflight_id
        assert secret is not None
        body = {**self.preflight_body(), "preflight_id": secret}
        status, response, payload = self.request(
            "POST",
            "/preflight",
            secret=secret,
            nonce="4" * 64,
            value=body,
        )
        self.assertEqual(409, status)
        _verify_response(secret, "POST", "/preflight", "4" * 64, response, payload)
        self.assertIn("private capability", json.loads(payload.decode("utf-8"))["reason"])
        self.assertIsNone(self.runtime.pending_launch_handle)

    def test_committed_status_uses_run_key_without_run_id_on_wire(self) -> None:
        preflight_secret = self.runtime.preflight_id
        assert preflight_secret is not None
        prepare_nonce = "5" * 64
        status, response, payload = self.request(
            "POST",
            "/preflight",
            secret=preflight_secret,
            nonce=prepare_nonce,
            value=self.preflight_body(),
        )
        self.assertEqual(200, status)
        _verify_response(preflight_secret, "POST", "/preflight", prepare_nonce, response, payload)
        prepared = json.loads(payload.decode("utf-8"))

        commit_body = {
            "schema_version": 1,
            "launch_handle": prepared["launch_handle"],
            "execution_generation": EXECUTION_GENERATION,
            "runtime_attestation": runtime_report(),
        }
        commit_nonce = "6" * 64
        status, response, payload = self.request(
            "POST",
            "/preflight-commit",
            secret=preflight_secret,
            nonce=commit_nonce,
            value=commit_body,
        )
        self.assertEqual(200, status, payload.decode("utf-8", errors="replace"))
        _verify_response(preflight_secret, "POST", "/preflight-commit", commit_nonce, response, payload)

        run_secret = prepared["run_id"]
        self.assertRegex(run_secret, r"^[0-9a-f]{64}$")
        status_nonce = "7" * 64
        status_code, status_response, status_payload = self.request(
            "GET",
            "/status",
            secret=run_secret,
            nonce=status_nonce,
        )
        self.assertEqual(200, status_code)
        _verify_response(run_secret, "GET", "/status", status_nonce, status_response, status_payload)
        status_value = json.loads(status_payload.decode("utf-8"))
        self.assertEqual("ready", status_value["status"])
        self.assertEqual(prepared["delegation_id"], status_value["delegation_id"])
        self.assertNotIn("run_id", status_value)

    def test_auth_input_binds_path_body_and_status(self) -> None:
        secret = "a" * 64
        nonce = "b" * 64
        body = b'{"schema_version":1}'
        request_mac = authenticated._mac_hex(
            secret,
            authenticated._request_auth_input("POST", "/preflight", nonce, body),
        )
        self.assertNotEqual(
            request_mac,
            authenticated._mac_hex(
                secret,
                authenticated._request_auth_input("POST", "/preflight-commit", nonce, body),
            ),
        )
        self.assertNotEqual(
            request_mac,
            authenticated._mac_hex(
                secret,
                authenticated._request_auth_input("POST", "/preflight", nonce, body + b" "),
            ),
        )
        response_200 = authenticated._mac_hex(
            secret,
            authenticated._response_auth_input("POST", "/preflight", nonce, 200, body),
        )
        response_409 = authenticated._mac_hex(
            secret,
            authenticated._response_auth_input("POST", "/preflight", nonce, 409, body),
        )
        self.assertNotEqual(response_200, response_409)
        self.assertEqual(64, len(hashlib.sha256(body).hexdigest()))


if __name__ == "__main__":
    unittest.main()
