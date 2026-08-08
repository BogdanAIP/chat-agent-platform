import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path

from gateway.yandex_function import index

TOKEN = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGH"


def event(body, headers=None, method="POST"):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": json.dumps(body),
        "isBase64Encoded": False,
    }


def parsed(response):
    return json.loads(response["body"]) if response.get("body") else None


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["RELAY_STATE_DIR"] = self.tmp.name
        os.environ["AGENT_TOKEN"] = TOKEN
        os.environ["PROJECT_ID"] = "demo"
        os.environ.pop("MCP_TOKEN", None)

    def tearDown(self):
        self.tmp.cleanup()

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

    def test_offline_tool_fails_without_waiting_for_task_deadline(self):
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
                }
            ),
            None,
        )
        elapsed = time.monotonic() - started
        payload = parsed(response)["result"]
        self.assertTrue(payload["isError"])
        self.assertEqual(payload["structuredContent"]["code"], "AGENT_OFFLINE")
        self.assertLess(elapsed, 1.0)

    def test_long_poll_rendezvous_and_result(self):
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
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {
                        "name": "local_ping",
                        "arguments": {"message": "stage4"},
                    },
                }
            ),
            None,
        )
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        payload = parsed(response)["result"]
        self.assertFalse(payload["isError"])
        self.assertTrue(payload["structuredContent"]["pong"])
        self.assertEqual(payload["structuredContent"]["message"], "stage4")
        self.assertTrue(holder["ack"]["ok"])
        self.assertEqual(holder["task"]["operation"], "local_ping")

    def test_tools_list_exports_only_allowlisted_local_operations(self):
        response = index.handler(
            event(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {},
                }
            ),
            None,
        )
        names = [item["name"] for item in parsed(response)["result"]["tools"]]
        self.assertEqual(names, ["local_ping", "runtime_self_test"])


if __name__ == "__main__":
    unittest.main()
