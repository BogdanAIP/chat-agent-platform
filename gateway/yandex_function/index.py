import base64
import fnmatch
import hmac
import json
import os
import re
import time
import uuid
from pathlib import Path
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest
from xml.etree import ElementTree

CONTRACT = "yandex-relay-gateway-v1"
DEFAULT_STATE_DIR = "/function/storage/relay"
MAX_LONG_POLL_SECONDS = 30
DEFAULT_LONG_POLL_SECONDS = 25
HEARTBEAT_TTL_SECONDS = 40
HEARTBEAT_WRITE_SECONDS = 10
TASK_TTL_SECONDS = 60
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


class _ObjectStorage:
    def __init__(self, bucket, token):
        self.bucket = bucket
        self.token = token

    def path(self, key=""):
        return _ObjectPath(self, key.strip("/"))

    def _url(self, key="", query=""):
        suffix = "/" + urlparse.quote(key, safe="/") if key else ""
        return f"https://storage.yandexcloud.net/{self.bucket}{suffix}{query}"

    def request(self, method, key="", body=None, query=""):
        headers = {"Authorization": f"Bearer {self.token}"}
        if body is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
        request = urlrequest.Request(self._url(key, query), data=body, headers=headers, method=method)
        try:
            return urlrequest.urlopen(request, timeout=15)
        except urlerror.HTTPError as error:
            if error.code == 404:
                raise FileNotFoundError(key) from error
            print(f"Object Storage {method} failed with HTTP {error.code}: key={key}", flush=True)
            raise OSError(f"Object Storage {method} failed with HTTP {error.code}") from error
        except urlerror.URLError as error:
            print(f"Object Storage {method} transport failed: key={key}", flush=True)
            raise OSError(f"Object Storage {method} failed") from error

    def list_keys(self, prefix):
        keys = []
        continuation = None
        while True:
            parameters = {"list-type": "2", "prefix": prefix}
            if continuation:
                parameters["continuation-token"] = continuation
            query = "?" + urlparse.urlencode(parameters)
            with self.request("GET", query=query) as response:
                root = ElementTree.fromstring(response.read())
            for element in root.iter():
                if element.tag.rsplit("}", 1)[-1] == "Key" and element.text:
                    keys.append(element.text)
            truncated = next(
                (element.text for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "IsTruncated"),
                "false",
            )
            if str(truncated).lower() != "true":
                break
            continuation = next(
                (
                    element.text
                    for element in root.iter()
                    if element.tag.rsplit("}", 1)[-1] == "NextContinuationToken"
                ),
                None,
            )
            if not continuation:
                break
        return keys


class _ObjectPath:
    def __init__(self, storage, key):
        self.storage = storage
        self.key = key.strip("/")

    def __truediv__(self, child):
        key = "/".join(part for part in (self.key, str(child).strip("/")) if part)
        return _ObjectPath(self.storage, key)

    @property
    def name(self):
        return self.key.rsplit("/", 1)[-1]

    @property
    def parent(self):
        return _ObjectPath(self.storage, self.key.rsplit("/", 1)[0] if "/" in self.key else "")

    def resolve(self):
        return self

    def mkdir(self, parents=False, exist_ok=False):
        del parents, exist_ok

    def read_text(self, encoding="utf-8"):
        with self.storage.request("GET", self.key) as response:
            return response.read().decode(encoding)

    def write_text(self, text, encoding="utf-8"):
        payload = text.encode(encoding)
        with self.storage.request("PUT", self.key, payload):
            return len(payload)

    def exists(self):
        try:
            with self.storage.request("HEAD", self.key):
                return True
        except FileNotFoundError:
            return False

    def glob(self, pattern):
        prefix = self.key + "/" if self.key else ""
        matches = []
        for key in self.storage.list_keys(prefix):
            remainder = key[len(prefix) :]
            if remainder and "/" not in remainder and fnmatch.fnmatch(remainder, pattern):
                matches.append(_ObjectPath(self.storage, key))
        return matches


def _context_token(context):
    if context is None:
        return ""
    if isinstance(context, dict):
        token_info = context.get("token")
    else:
        token_info = getattr(context, "token", None)
    if isinstance(token_info, dict):
        return str(token_info.get("access_token") or "")
    access_token = getattr(token_info, "access_token", None)
    if access_token:
        return str(access_token)
    return str(token_info or "")


def _state_root(context=None):
    bucket = os.environ.get("BUCKET_NAME", "").strip()
    token = _context_token(context)
    if bucket and token:
        return _ObjectStorage(bucket, token).path()
    return Path(os.environ.get("RELAY_STATE_DIR", DEFAULT_STATE_DIR)).resolve()


def _project_id():
    return os.environ.get("PROJECT_ID", "demo").strip() or "demo"


def _agent_token():
    return os.environ.get("AGENT_TOKEN", "")


def _remote_token():
    return os.environ.get("MCP_TOKEN", "")


def _ensure_state(context=None):
    root = _state_root(context)
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


def _authorized_remote(event):
    expected = _remote_token()
    if not expected:
        return False
    headers = _headers(event)
    supplied = headers.get("x-mcp-token", "")
    if not supplied:
        authorization = headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            supplied = authorization[7:].strip()
    return bool(supplied) and hmac.compare_digest(expected, supplied)


def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _heartbeat_path(root, project_id):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", project_id)
    return root / "agents" / f"{safe}.json"


def _write_heartbeat(root, project_id, operations, last_seen_unix_ms=None):
    _write_json(
        _heartbeat_path(root, project_id),
        {
            "contract_version": CONTRACT,
            "project_id": project_id,
            "last_seen_unix_ms": _now_ms() if last_seen_unix_ms is None else int(last_seen_unix_ms),
            "operations": sorted(set(operations)),
        },
    )


def _agent_online(root, project_id):
    heartbeat = _read_json(_heartbeat_path(root, project_id))
    if not heartbeat:
        return False
    last_seen = int(heartbeat.get("last_seen_unix_ms", 0))
    return last_seen > 0 and _now_ms() - last_seen <= HEARTBEAT_TTL_SECONDS * 1000


def _validate_agent_project(body):
    project_id = str(body.get("project_id") or "")
    if project_id != _project_id():
        return None, _json_response(403, {"ok": False, "error": "project_id is not allowed"})
    return project_id, None


def _task_is_pending(root, task):
    request_id = str(task.get("request_id") or "")
    if not REQUEST_ID.fullmatch(request_id):
        return False
    if int(task.get("deadline_unix_ms", 0)) < _now_ms():
        return False
    return not (root / "results" / f"{request_id}.json").exists()


def _agent_poll(root, body):
    project_id, error = _validate_agent_project(body)
    if error:
        return error
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
            next_heartbeat = now + HEARTBEAT_WRITE_SECONDS
        for path in sorted((root / "tasks").glob("rly_*.json"), key=lambda item: item.name):
            task = _read_json(path)
            if not task or task.get("project_id") != project_id:
                continue
            if task.get("operation") not in operations or not _task_is_pending(root, task):
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


def _agent_offline(root, body):
    project_id, error = _validate_agent_project(body)
    if error:
        return error
    _write_heartbeat(root, project_id, [], last_seen_unix_ms=0)
    return _json_response(200, {"ok": True, "agent_online": False})


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
    existing = _read_json(result_path)
    if existing:
        if existing != response:
            return _json_response(409, {"ok": False, "error": "result identity collision"})
        return _json_response(200, {"ok": True, "duplicate": True})
    task = _read_json(task_path)
    if not task or task.get("request_id") != task_id:
        return _json_response(409, {"ok": False, "error": "task is no longer pending"})
    if int(task.get("deadline_unix_ms", 0)) < _now_ms():
        return _json_response(409, {"ok": False, "error": "task deadline has expired"})
    _write_json(result_path, response)
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


def _tool_error(code, message, retryable=False):
    return _tool_result(
        {"code": code, "message": message, "retryable": bool(retryable)},
        True,
    )


def _validate_tool_arguments(name, arguments):
    if name not in ALLOWED_TOOLS:
        return None, _tool_error("TOOL_NOT_FOUND", f"unknown tool: {name}")
    if not isinstance(arguments, dict):
        return None, _tool_error("VALIDATION_FAILED", "tool arguments must be an object")
    if name == "runtime_self_test":
        if arguments:
            return None, _tool_error("VALIDATION_FAILED", "runtime_self_test does not accept parameters")
        return {}, None
    extra = set(arguments) - {"message"}
    if extra:
        return None, _tool_error("VALIDATION_FAILED", "local_ping accepts only the optional message parameter")
    message = arguments.get("message", "ping")
    if not isinstance(message, str):
        return None, _tool_error("VALIDATION_FAILED", "local_ping message must be a string")
    if len(message.encode("utf-8")) > 1024:
        return None, _tool_error("VALIDATION_FAILED", "local_ping message exceeds 1024 bytes")
    return {"message": message}, None


def _call_local_tool(root, name, arguments):
    arguments, error = _validate_tool_arguments(name, arguments)
    if error:
        return error
    project_id = _project_id()
    if not _agent_online(root, project_id):
        return _tool_error(
            "AGENT_OFFLINE",
            "Local agent is switched off or its heartbeat is stale. Enable relay locally and retry.",
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
            if response.get("status") == "success":
                return _tool_result(response.get("result") or {}, False)
            return _tool_result(
                response.get("error")
                or {"code": "LOCAL_ERROR", "message": "local execution failed"},
                True,
            )
        time.sleep(POLL_SLICE_SECONDS)
    return _tool_error(
        "LOCAL_TIMEOUT",
        "Local agent did not return the task before its deadline.",
        True,
    )


def _handle_mcp(root, event, body):
    if not _authorized_remote(event):
        return _json_response(401, _mcp_error(body.get("id"), -32001, "remote authorization failed"))
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


def _handle_action(root, event, body):
    if not _authorized_remote(event):
        return _json_response(401, {"status": "error", "error": {"code": "AUTH_FAILED", "message": "remote authorization failed"}})
    name = str(body.get("action") or "")
    arguments = {}
    if "message" in body:
        arguments["message"] = body.get("message")
    extra = set(body) - {"action", "message"}
    if extra:
        return _json_response(400, {"status": "error", "error": {"code": "VALIDATION_FAILED", "message": "unknown action request fields"}})
    result = _call_local_tool(root, name, arguments)
    if result["isError"]:
        return _json_response(200, {"status": "error", "error": result["structuredContent"]})
    return _json_response(200, {"status": "success", "result": result["structuredContent"]})


def _handle_request(root, event):
    method = str(event.get("httpMethod") or "POST").upper()
    if method == "GET":
        health = {"status": "ok", "contract_version": CONTRACT}
        if _authorized_remote(event):
            health.update(
                {
                    "agent_online": _agent_online(root, _project_id()),
                    "project_id": _project_id(),
                    "remote_auth_configured": bool(_remote_token()),
                }
            )
        return _json_response(200, health)
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
        if action == "health":
            return _json_response(200, {"ok": True, "project_id": _project_id()})
        if action == "poll":
            return _agent_poll(root, body)
        if action == "result":
            return _agent_result(root, body)
        if action == "offline":
            return _agent_offline(root, body)
        return _json_response(400, {"ok": False, "error": "unsupported agent_action"})
    if "action" in body:
        return _handle_action(root, event, body)
    return _handle_mcp(root, event, body)


def handler(event, context):
    root = _ensure_state(context)
    try:
        return _handle_request(root, event)
    except OSError as error:
        return _json_response(
            503,
            {
                "status": "error",
                "error": {"code": "STATE_BACKEND_UNAVAILABLE", "message": str(error)},
            },
        )
