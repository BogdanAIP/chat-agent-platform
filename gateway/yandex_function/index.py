import base64
import hmac
import json
import os
import re
import time
import uuid
from pathlib import Path

CONTRACT = "yandex-relay-gateway-v1"
DEFAULT_STATE_DIR = "/function/storage/relay"
MAX_LONG_POLL_SECONDS = 30
DEFAULT_LONG_POLL_SECONDS = 25
HEARTBEAT_TTL_SECONDS = 40
HEARTBEAT_WRITE_SECONDS = 10
TASK_TTL_SECONDS = 60
RESULT_TTL_SECONDS = 300
POLL_SLICE_SECONDS = 1.0
REQUEST_ID = re.compile(r"^rly_[a-f0-9]{32}$")
ALLOWED_TOOLS = {
    "local_ping": {
        "name": "local_ping",
        "description": "Check that the explicitly enabled local Windows agent is reachable.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"message": {"type": "string", "maxLength": 1024}},
        },
    },
    "runtime_self_test": {
        "name": "runtime_self_test",
        "description": "Run the policy-gated local agent-platform runtime self-test.",
        "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
    },
}


def _now_ms():
    return int(time.time() * 1000)


def _state_root():
    return Path(os.environ.get("RELAY_STATE_DIR", DEFAULT_STATE_DIR)).resolve()


def _project_id():
    return os.environ.get("PROJECT_ID", "demo").strip() or "demo"


def _agent_token():
    return os.environ.get("AGENT_TOKEN", "")


def _mcp_token():
    return os.environ.get("MCP_TOKEN", "")


def _ensure_state():
    root = _state_root()
    for name in ("tasks", "results", "agents"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def _json_response(status_code, body, headers=None):
    merged = {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
    }
    if headers:
        merged.update(headers)
    return {
        "statusCode": status_code,
        "headers": merged,
        "isBase64Encoded": False,
        "body": json.dumps(body, ensure_ascii=False, separators=(",", ":")),
    }


def _empty_response(status_code=204):
    return {"statusCode": status_code, "headers": {"Cache-Control": "no-store"}, "body": ""}


def _headers(event):
    return {str(key).lower(): str(value) for key, value in (event.get("headers") or {}).items()}


def _body(event):
    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    return json.loads(raw)


def _authorized_agent(event):
    expected = _agent_token()
    supplied = _headers(event).get("x-agent-token", "")
    return bool(expected) and hmac.compare_digest(expected, supplied)


def _authorized_mcp(event):
    expected = _mcp_token()
    if not expected:
        return True
    headers = _headers(event)
    supplied = headers.get("x-mcp-token", "")
    if not supplied:
        authorization = headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            supplied = authorization[7:].strip()
    return hmac.compare_digest(expected, supplied)


def _safe_unlink(path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _cleanup(root):
    now = _now_ms()
    for path in (root / "tasks").glob("rly_*.json"):
        task = _read_json(path)
        if not task or int(task.get("deadline_unix_ms", 0)) < now:
            _safe_unlink(path)
    result_cutoff = time.time() - RESULT_TTL_SECONDS
    for path in (root / "results").glob("rly_*.json"):
        try:
            if path.stat().st_mtime < result_cutoff:
                _safe_unlink(path)
        except OSError:
            pass


def _heartbeat_path(root, project_id):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", project_id)
    return root / "agents" / f"{safe}.json"


def _write_heartbeat(root, project_id, operations):
    _write_json(
        _heartbeat_path(root, project_id),
        {
            "contract_version": CONTRACT,
            "project_id": project_id,
            "last_seen_unix_ms": _now_ms(),
            "operations": sorted(set(operations)),
        },
    )


def _agent_online(root, project_id):
    heartbeat = _read_json(_heartbeat_path(root, project_id))
    if not heartbeat:
        return False
    last_seen = int(heartbeat.get("last_seen_unix_ms", 0))
    return _now_ms() - last_seen <= HEARTBEAT_TTL_SECONDS * 1000


def _agent_poll(root, body):
    project_id = str(body.get("project_id") or "")
    if project_id != _project_id():
        return _json_response(403, {"ok": False, "error": "project_id is not allowed"})
    operations = [str(item) for item in (body.get("operations") or []) if str(item) in ALLOWED_TOOLS]
    if not operations:
        return _json_response(400, {"ok": False, "error": "no allowed operations advertised"})
    wait_seconds = body.get("wait_seconds", DEFAULT_LONG_POLL_SECONDS)
    try:
        wait_seconds = int(wait_seconds)
    except (TypeError, ValueError):
        wait_seconds = DEFAULT_LONG_POLL_SECONDS
    wait_seconds = max(1, min(wait_seconds, MAX_LONG_POLL_SECONDS))
    deadline = time.monotonic() + wait_seconds
    next_heartbeat = 0.0
    while True:
        now = time.monotonic()
        if now >= next_heartbeat:
            _write_heartbeat(root, project_id, operations)
            _cleanup(root)
            next_heartbeat = now + HEARTBEAT_WRITE_SECONDS
        for path in sorted((root / "tasks").glob("rly_*.json"), key=lambda item: item.name):
            task = _read_json(path)
            if not task or task.get("project_id") != project_id:
                continue
            if task.get("operation") not in operations:
                continue
            public_task = {
                key: task[key]
                for key in (
                    "contract_version",
                    "request_id",
                    "operation",
                    "parameters",
                    "deadline_unix_ms",
                )
            }
            return _json_response(200, {"ok": True, "task": public_task})
        if now >= deadline:
            return _json_response(200, {"ok": True, "task": None})
        time.sleep(min(POLL_SLICE_SECONDS, max(0.0, deadline - now)))


def _agent_result(root, body):
    task_id = str(body.get("task_id") or "")
    response = body.get("response")
    if not REQUEST_ID.fullmatch(task_id):
        return _json_response(400, {"ok": False, "error": "invalid task_id"})
    if not isinstance(response, dict) or response.get("request_id") != task_id:
        return _json_response(400, {"ok": False, "error": "response identity mismatch"})
    if response.get("contract_version") != "relay-response-v1":
        return _json_response(400, {"ok": False, "error": "unsupported response contract"})
    result_path = root / "results" / f"{task_id}.json"
    task_path = root / "tasks" / f"{task_id}.json"
    if result_path.exists():
        return _json_response(200, {"ok": True, "duplicate": True})
    if not task_path.exists():
        return _json_response(409, {"ok": False, "error": "task is no longer pending"})
    _write_json(result_path, response)
    _safe_unlink(task_path)
    return _json_response(200, {"ok": True, "duplicate": False})


def _mcp_result(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _mcp_error(request_id, code, message, data=None):
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _tool_result(payload, is_error=False):
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": payload,
        "isError": is_error,
    }


def _call_local_tool(root, name, arguments):
    project_id = _project_id()
    if name not in ALLOWED_TOOLS:
        return _tool_result({"code": "TOOL_NOT_FOUND", "message": f"unknown tool: {name}"}, True)
    if not isinstance(arguments, dict):
        return _tool_result(
            {"code": "VALIDATION_FAILED", "message": "tool arguments must be an object"}, True
        )
    if not _agent_online(root, project_id):
        return _tool_result(
            {
                "code": "AGENT_OFFLINE",
                "message": "Local agent is switched off or its heartbeat is stale. Enable relay locally and retry.",
                "retryable": True,
            },
            True,
        )
    task_id = f"rly_{uuid.uuid4().hex}"
    deadline_ms = _now_ms() + TASK_TTL_SECONDS * 1000
    task = {
        "contract_version": "relay-request-v1",
        "request_id": task_id,
        "operation": name,
        "parameters": arguments,
        "deadline_unix_ms": deadline_ms,
        "project_id": project_id,
        "created_unix_ms": _now_ms(),
    }
    task_path = root / "tasks" / f"{task_id}.json"
    result_path = root / "results" / f"{task_id}.json"
    _write_json(task_path, task)
    wait_deadline = time.monotonic() + TASK_TTL_SECONDS
    while time.monotonic() < wait_deadline:
        response = _read_json(result_path)
        if response:
            _safe_unlink(result_path)
            if response.get("status") == "success":
                return _tool_result(response.get("result") or {}, False)
            return _tool_result(
                response.get("error")
                or {"code": "LOCAL_ERROR", "message": "local execution failed"},
                True,
            )
        time.sleep(POLL_SLICE_SECONDS)
    _safe_unlink(task_path)
    return _tool_result(
        {
            "code": "LOCAL_TIMEOUT",
            "message": "Local agent did not return the task before its deadline.",
            "retryable": True,
        },
        True,
    )


def _handle_mcp(root, event, body):
    if not _authorized_mcp(event):
        return _json_response(401, _mcp_error(body.get("id"), -32001, "MCP authorization failed"))
    method = body.get("method")
    request_id = body.get("id")
    params = body.get("params") or {}
    if method == "notifications/initialized":
        return _empty_response()
    if method == "initialize":
        requested = params.get("protocolVersion")
        protocol = requested if isinstance(requested, str) and requested else "2025-06-18"
        return _json_response(
            200,
            _mcp_result(
                request_id,
                {
                    "protocolVersion": protocol,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "agent-platform-yandex-relay", "version": "1.0.0"},
                },
            ),
        )
    if method == "ping":
        return _json_response(200, _mcp_result(request_id, {}))
    if method == "tools/list":
        return _json_response(200, _mcp_result(request_id, {"tools": list(ALLOWED_TOOLS.values())}))
    if method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        return _json_response(200, _mcp_result(request_id, _call_local_tool(root, name, arguments)))
    return _json_response(200, _mcp_error(request_id, -32601, f"method not found: {method}"))


def handler(event, context):
    del context
    root = _ensure_state()
    method = str(event.get("httpMethod") or "POST").upper()
    if method == "GET":
        return _json_response(
            200,
            {
                "status": "ok",
                "contract_version": CONTRACT,
                "agent_online": _agent_online(root, _project_id()),
                "project_id": _project_id(),
            },
        )
    if method != "POST":
        return _json_response(405, {"error": "method not allowed"}, {"Allow": "GET, POST"})
    try:
        body = _body(event)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return _json_response(400, {"error": "invalid JSON body"})
    if body.get("agent_action"):
        if not _authorized_agent(event):
            return _json_response(401, {"ok": False, "error": "agent authorization failed"})
        action = body.get("agent_action")
        if action == "poll":
            return _agent_poll(root, body)
        if action == "result":
            return _agent_result(root, body)
        return _json_response(400, {"ok": False, "error": "unsupported agent_action"})
    return _handle_mcp(root, event, body)
