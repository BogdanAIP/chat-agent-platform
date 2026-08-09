import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path

from gateway.yandex_function import index

TOKEN = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGH"
REMOTE_TOKEN = "remote-abcdefghijklmnopqrstuvwxyz0123456789"


def event(body, headers=None, method="POST"):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": json.dumps(body),
        "isBase64Encoded": False,
    }


def parsed(response):
    return json.loads(response["body"]) if response.get("body") else None


def remote_headers():
    return {"Authorization": f"Bearer {REMOTE_TOKEN}"}


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["RELAY_STATE_DIR"] = self.tmp.name
        os.environ["AGENT_TOKEN"] = TOKEN
        os.environ["MCP_TOKEN"] = REMOTE_TOKEN
        os.environ["PROJECT_ID"] = "demo"

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("RELAY_STATE_DIR", None)
        os.environ.pop("AGENT_TOKEN", None)
        os.environ.pop("MCP_TOKEN", None)
        os.environ.pop("PROJECT_ID", None)

    def test_agent_auth_is_required(self):
        response = index.handler(
            event(
                {
                    "agent_action": "poll",
                    "project_id": "demo",
                    "operations": ["local_ping"],
                }
            ),
            None,
        )
        self.assertEqual(response["statusCode"], 401)

    def test_agent_health_is_authenticated_and_side_effect_free(self):
        response = index.handler(
            event(
                {"agent_action": "health", "project_id": "demo"},
                {"X-Agent-Token": TOKEN},
            ),
            None,
        )
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(parsed(response), {"ok": True, "project_id": "demo"})
        self.assertFalse((Path(self.tmp.name) / "agents" / "demo.json").exists())

    def test_remote_auth_fails_closed_when_missing_or_unconfigured(self):
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        denied = index.handler(event(request), None)
        self.assertEqual(denied["statusCode"], 401)
        allowed = index.handler(event(request, remote_headers()), None)
        self.assertEqual(allowed["statusCode"], 200)
        self.assertIn("result", parsed(allowed))

        os.environ.pop("MCP_TOKEN")
        unconfigured = index.handler(
            event(request, {"Authorization": f"Bearer {REMOTE_TOKEN}"}),
            None,
        )
        self.assertEqual(unconfigured["statusCode"], 401)

    def test_offline_mcp_tool_fails_without_waiting_for_task_deadline(self):
        started = time.monotonic()
        response = index.handler(
            event(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "local_ping",
                        "arguments": {"message": "hello"},
                    },
                },
                remote_headers(),
            ),
            None,
        )
        elapsed = time.monotonic() - started
        payload = parsed(response)["result"]
        self.assertTrue(payload["isError"])
        self.assertEqual(payload["structuredContent"]["code"], "AGENT_OFFLINE")
        self.assertLess(elapsed, 1.0)

    def test_actions_surface_requires_bearer_and_mirrors_argument_allowlist(self):
        denied = index.handler(event({"action": "local_ping", "message": "hello"}), None)
        self.assertEqual(denied["statusCode"], 401)

        invalid = index.handler(
            event(
                {"action": "runtime_self_test", "message": "not allowed"},
                remote_headers(),
            ),
            None,
        )
        self.assertEqual(invalid["statusCode"], 200)
        payload = parsed(invalid)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error"]["code"], "VALIDATION_FAILED")

        unknown = index.handler(
            event({"action": "shell.run_arbitrary"}, remote_headers()),
            None,
        )
        self.assertEqual(parsed(unknown)["error"]["code"], "TOOL_NOT_FOUND")

    def test_authenticated_offline_overwrites_heartbeat_without_delete_permission(self):
        poll = index.handler(
            event(
                {
                    "agent_action": "poll",
                    "wait_seconds": 1,
                    "project_id": "demo",
                    "operations": ["local_ping", "runtime_self_test"],
                },
                {"X-Agent-Token": TOKEN},
            ),
            None,
        )
        self.assertEqual(poll["statusCode"], 200)
        heartbeat = Path(self.tmp.name) / "agents" / "demo.json"
        self.assertTrue(heartbeat.exists())
        offline = index.handler(
            event(
                {"agent_action": "offline", "project_id": "demo"},
                {"X-Agent-Token": TOKEN},
            ),
            None,
        )
        self.assertEqual(offline["statusCode"], 200)
        self.assertTrue(heartbeat.exists())
        heartbeat_value = json.loads(heartbeat.read_text(encoding="utf-8"))
        self.assertEqual(heartbeat_value["last_seen_unix_ms"], 0)
        self.assertEqual(heartbeat_value["operations"], [])
        self.assertFalse(parsed(offline)["agent_online"])
        public_health = parsed(index.handler(event({}, method="GET"), None))
        self.assertEqual(set(public_health), {"status", "contract_version"})
        health = parsed(index.handler(event({}, remote_headers(), method="GET"), None))
        self.assertFalse(health["agent_online"])
        self.assertEqual(health["project_id"], "demo")
        self.assertTrue(health["remote_auth_configured"])

    def test_actions_long_poll_rendezvous_result_and_duplicate_are_no_delete(self):
        holder = {}

        def agent():
            poll = index.handler(
                event(
                    {
                        "agent_action": "poll",
                        "wait_seconds": 3,
                        "project_id": "demo",
                        "operations": ["local_ping", "runtime_self_test"],
                    },
                    {"X-Agent-Token": TOKEN},
                ),
                None,
            )
            task = parsed(poll)["task"]
            holder["task"] = task
            result = {
                "contract_version": "relay-response-v1",
                "request_id": task["request_id"],
                "status": "success",
                "result": {
                    "pong": True,
                    "message": task["parameters"].get("message"),
                },
                "error": None,
            }
            holder["result"] = result
            ack = index.handler(
                event(
                    {
                        "agent_action": "result",
                        "task_id": task["request_id"],
                        "response": result,
                    },
                    {"X-Agent-Token": TOKEN},
                ),
                None,
            )
            holder["ack"] = parsed(ack)

        thread = threading.Thread(target=agent, daemon=True)
        thread.start()
        heartbeat = Path(self.tmp.name) / "agents" / "demo.json"
        for _ in range(40):
            if heartbeat.exists():
                break
            time.sleep(0.05)
        response = index.handler(
            event(
                {"action": "local_ping", "message": "stage4"},
                remote_headers(),
            ),
            None,
        )
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        payload = parsed(response)
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["result"]["pong"])
        self.assertEqual(payload["result"]["message"], "stage4")
        self.assertTrue(holder["ack"]["ok"])
        self.assertFalse(holder["ack"]["duplicate"])
        self.assertEqual(holder["task"]["operation"], "local_ping")

        task_id = holder["task"]["request_id"]
        task_path = Path(self.tmp.name) / "tasks" / f"{task_id}.json"
        result_path = Path(self.tmp.name) / "results" / f"{task_id}.json"
        self.assertTrue(task_path.exists())
        self.assertTrue(result_path.exists())
        stored_task = json.loads(task_path.read_text(encoding="utf-8"))
        self.assertNotIn("status", stored_task)
        self.assertEqual(stored_task["request_id"], task_id)

        duplicate = index.handler(
            event(
                {
                    "agent_action": "result",
                    "task_id": task_id,
                    "response": holder["result"],
                },
                {"X-Agent-Token": TOKEN},
            ),
            None,
        )
        self.assertTrue(parsed(duplicate)["duplicate"])
        self.assertTrue(task_path.exists())
        self.assertTrue(result_path.exists())

        second_poll = index.handler(
            event(
                {
                    "agent_action": "poll",
                    "wait_seconds": 1,
                    "project_id": "demo",
                    "operations": ["local_ping", "runtime_self_test"],
                },
                {"X-Agent-Token": TOKEN},
            ),
            None,
        )
        self.assertIsNone(parsed(second_poll)["task"])

    def test_gateway_runtime_source_has_no_object_delete_primitives(self):
        source = Path(index.__file__).read_text(encoding="utf-8")
        self.assertNotIn(".unlink(", source)
        self.assertNotIn("os.remove(", source)
        self.assertNotIn("os.unlink(", source)

    def test_actions_openapi_template_exports_only_the_two_stage4_operations(self):
        template = Path("gateway/actions-openapi.template.json")
        schema = json.loads(template.read_text(encoding="utf-8"))
        self.assertEqual(schema["openapi"], "3.1.0")
        action = schema["paths"]["/"]["post"]
        self.assertEqual(action["operationId"], "runLocalAgentTool")
        action_enum = action["requestBody"]["content"]["application/json"]["schema"]["properties"]["action"]["enum"]
        self.assertEqual(action_enum, ["local_ping", "runtime_self_test"])
        self.assertEqual(schema["servers"][0]["url"], "__GATEWAY_URL__")

    def test_yandex_api_gateway_forwards_get_and_post_to_the_cloud_function(self):
        template = Path("gateway/yandex-apigateway.template.json")
        schema = json.loads(template.read_text(encoding="utf-8"))
        self.assertEqual(schema["openapi"], "3.0.0")
        for method in ("get", "post"):
            integration = schema["paths"]["/"][method]["x-yc-apigateway-integration"]
            self.assertEqual(integration["type"], "cloud_functions")
            self.assertEqual(integration["function_id"], "__FUNCTION_ID__")
            self.assertEqual(integration["payload_format_version"], "0.1")

    def test_context_token_extracts_iam_access_token(self):
        self.assertEqual(
            index._context_token({"token": {"access_token": "iam-token", "token_type": "Bearer"}}),
            "iam-token",
        )

    def test_tools_list_exports_only_allowlisted_local_operations(self):
        response = index.handler(
            event(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {},
                },
                remote_headers(),
            ),
            None,
        )
        names = [item["name"] for item in parsed(response)["result"]["tools"]]
        self.assertEqual(names, ["local_ping", "runtime_self_test"])


if __name__ == "__main__":
    unittest.main()
