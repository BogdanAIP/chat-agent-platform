mod model;
mod store;

use std::collections::BTreeSet;
use std::net::SocketAddr;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use axum::extract::{DefaultBodyLimit, State};
use axum::http::header::{AUTHORIZATION, CACHE_CONTROL, CONTENT_TYPE};
use axum::http::{HeaderMap, HeaderName, HeaderValue, StatusCode};
use axum::response::{IntoResponse, Response};
use axum::routing::get;
use axum::{Json, Router};
use serde_json::{Map, Value, json};
use thiserror::Error;
use tokio::net::TcpListener;
use tokio::sync::Notify;
use tokio::time::{Instant, sleep};
use uuid::Uuid;
use zeroize::Zeroizing;

use model::{RelayResponse, RelayTask, StoredTask};
use store::{SaveResultOutcome, Store, StoreError};

const CONTRACT: &str = "relay-server-v1";
const DEFAULT_LONG_POLL_SECONDS: u64 = 25;
const MAX_LONG_POLL_SECONDS: u64 = 30;
const HEARTBEAT_TTL_MS: i64 = 40_000;
const HEARTBEAT_WRITE_MS: i64 = 10_000;
const TASK_TTL_MS: i64 = 60_000;
const TASK_LEASE_MS: i64 = 10_000;
const RETENTION_MS: i64 = 24 * 60 * 60 * 1_000;
const MAX_BODY_BYTES: usize = 64 * 1024;
const MAX_PING_MESSAGE_BYTES: usize = 1_024;
const RESULT_POLL_INTERVAL: Duration = Duration::from_millis(200);
const AGENT_POLL_FALLBACK_INTERVAL: Duration = Duration::from_secs(1);

static MCP_TOKEN_HEADER: HeaderName = HeaderName::from_static("x-mcp-token");
static AGENT_TOKEN_HEADER: HeaderName = HeaderName::from_static("x-agent-token");
static CONTENT_TYPE_OPTIONS: HeaderName = HeaderName::from_static("x-content-type-options");

#[derive(Debug, Error)]
pub enum RelayServerError {
    #[error("relay server configuration is invalid: {0}")]
    InvalidConfig(String),
    #[error("relay server state failed: {0}")]
    Store(#[from] StoreError),
    #[error("relay server I/O failed: {0}")]
    Io(#[from] std::io::Error),
}

pub struct RelayServerConfig {
    project_id: String,
    mcp_token: Zeroizing<String>,
    agent_token: Zeroizing<String>,
    database_path: PathBuf,
}

impl RelayServerConfig {
    pub fn new(
        project_id: String,
        mcp_token: String,
        agent_token: String,
        database_path: PathBuf,
    ) -> Result<Self, RelayServerError> {
        validate_project_id(&project_id)?;
        validate_token("RELAY_MCP_TOKEN", &mcp_token)?;
        validate_token("RELAY_AGENT_TOKEN", &agent_token)?;
        if mcp_token == agent_token {
            return Err(RelayServerError::InvalidConfig(
                "remote and local-agent tokens must be different".to_owned(),
            ));
        }
        Ok(Self {
            project_id,
            mcp_token: Zeroizing::new(mcp_token),
            agent_token: Zeroizing::new(agent_token),
            database_path,
        })
    }

    #[must_use]
    pub fn project_id(&self) -> &str {
        &self.project_id
    }

    #[must_use]
    pub fn database_path(&self) -> &Path {
        &self.database_path
    }
}

struct AppState {
    config: RelayServerConfig,
    store: Store,
    task_notify: Notify,
    result_notify: Notify,
}

impl AppState {
    fn new(config: RelayServerConfig, store: Store) -> Self {
        Self {
            config,
            store,
            task_notify: Notify::new(),
            result_notify: Notify::new(),
        }
    }
}

#[derive(Debug)]
struct LocalToolOutcome {
    payload: Value,
    is_error: bool,
}

impl LocalToolOutcome {
    fn success(payload: Value) -> Self {
        Self {
            payload,
            is_error: false,
        }
    }

    fn error(code: &str, message: &str, retryable: bool) -> Self {
        Self {
            payload: json!({
                "code": code,
                "message": message,
                "retryable": retryable
            }),
            is_error: true,
        }
    }
}

pub async fn serve(config: RelayServerConfig, bind: SocketAddr) -> Result<(), RelayServerError> {
    let store = Store::open(config.database_path())?;
    let now = now_unix_ms();
    store.cleanup(now.saturating_sub(RETENTION_MS))?;
    let project_id = config.project_id().to_owned();
    let state = Arc::new(AppState::new(config, store));
    let app = router(state);
    let listener = TcpListener::bind(bind).await?;
    eprintln!("relay-server listening on {bind} for project {project_id}");
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;
    Ok(())
}

fn router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/", get(root_get).post(root_post))
        .route("/healthz", get(healthz))
        .fallback(not_found)
        .layer(DefaultBodyLimit::max(MAX_BODY_BYTES))
        .with_state(state)
}

async fn shutdown_signal() {
    #[cfg(unix)]
    {
        use tokio::signal::unix::{SignalKind, signal};

        match signal(SignalKind::terminate()) {
            Ok(mut terminate) => {
                tokio::select! {
                    _ = tokio::signal::ctrl_c() => {},
                    _ = terminate.recv() => {},
                }
            }
            Err(_) => {
                let _ = tokio::signal::ctrl_c().await;
            }
        }
    }

    #[cfg(not(unix))]
    {
        let _ = tokio::signal::ctrl_c().await;
    }
}

async fn healthz() -> Response {
    json_response(
        StatusCode::OK,
        json!({"status": "ok", "contract_version": CONTRACT}),
    )
}

async fn not_found() -> Response {
    json_response(StatusCode::NOT_FOUND, json!({"error": "not found"}))
}

async fn root_get(State(state): State<Arc<AppState>>, headers: HeaderMap) -> Response {
    let mut health = json!({"status": "ok", "contract_version": CONTRACT});
    if authorized_remote(&state, &headers) {
        let now = now_unix_ms();
        let online = match state.store.agent_status(state.config.project_id()) {
            Ok(status) => status.is_some_and(|value| {
                value.last_seen_unix_ms > 0
                    && now.saturating_sub(value.last_seen_unix_ms) <= HEARTBEAT_TTL_MS
            }),
            Err(error) => return state_backend_error(&error),
        };
        if let Some(object) = health.as_object_mut() {
            object.insert("agent_online".to_owned(), Value::Bool(online));
            object.insert(
                "project_id".to_owned(),
                Value::String(state.config.project_id().to_owned()),
            );
            object.insert("remote_auth_configured".to_owned(), Value::Bool(true));
        }
    }
    json_response(StatusCode::OK, health)
}

async fn root_post(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    Json(body): Json<Value>,
) -> Response {
    let Some(object) = body.as_object() else {
        return json_response(StatusCode::BAD_REQUEST, json!({"error": "JSON body must be an object"}));
    };
    if object.contains_key("agent_action") {
        return handle_agent(state, &headers, object).await;
    }
    if object.contains_key("action") {
        return handle_action(state, &headers, object).await;
    }
    handle_mcp(state, &headers, object).await
}

async fn handle_agent(
    state: Arc<AppState>,
    headers: &HeaderMap,
    body: &Map<String, Value>,
) -> Response {
    if !authorized_agent(&state, headers) {
        return json_response(
            StatusCode::UNAUTHORIZED,
            json!({"ok": false, "error": "agent authorization failed"}),
        );
    }
    let action = body
        .get("agent_action")
        .and_then(Value::as_str)
        .unwrap_or_default();
    match action {
        "health" => json_response(
            StatusCode::OK,
            json!({"ok": true, "project_id": state.config.project_id()}),
        ),
        "poll" => agent_poll(state, body).await,
        "result" => agent_result(state, body),
        "offline" => agent_offline(state, body),
        _ => json_response(
            StatusCode::BAD_REQUEST,
            json!({"ok": false, "error": "unsupported agent_action"}),
        ),
    }
}

async fn agent_poll(state: Arc<AppState>, body: &Map<String, Value>) -> Response {
    if let Some(response) = validate_agent_project(&state, body) {
        return response;
    }
    let operations = allowed_operations_from_poll(body);
    if operations.is_empty() {
        return json_response(
            StatusCode::BAD_REQUEST,
            json!({"ok": false, "error": "no allowed operations advertised"}),
        );
    }
    let wait_seconds = body
        .get("wait_seconds")
        .and_then(Value::as_u64)
        .unwrap_or(DEFAULT_LONG_POLL_SECONDS)
        .clamp(1, MAX_LONG_POLL_SECONDS);
    let deadline = Instant::now() + Duration::from_secs(wait_seconds);
    let mut next_heartbeat_ms = 0_i64;

    loop {
        let notified = state.task_notify.notified();
        let now_ms = now_unix_ms();
        if now_ms >= next_heartbeat_ms {
            if let Err(error) = state
                .store
                .upsert_heartbeat(state.config.project_id(), &operations, now_ms)
            {
                return state_backend_error(&error);
            }
            next_heartbeat_ms = now_ms.saturating_add(HEARTBEAT_WRITE_MS);
        }
        match state.store.lease_next_task(
            state.config.project_id(),
            &operations,
            now_ms,
            now_ms.saturating_add(TASK_LEASE_MS),
        ) {
            Ok(Some(task)) => {
                return json_response(StatusCode::OK, json!({"ok": true, "task": task}));
            }
            Ok(None) => {}
            Err(error) => return state_backend_error(&error),
        }
        let now = Instant::now();
        if now >= deadline {
            return json_response(StatusCode::OK, json!({"ok": true, "task": null}));
        }
        let remaining = deadline.saturating_duration_since(now);
        let wait = remaining.min(AGENT_POLL_FALLBACK_INTERVAL);
        tokio::select! {
            _ = notified => {},
            () = sleep(wait) => {},
        }
    }
}

fn agent_result(state: Arc<AppState>, body: &Map<String, Value>) -> Response {
    let task_id = body
        .get("task_id")
        .and_then(Value::as_str)
        .unwrap_or_default();
    if !valid_request_id(task_id) {
        return json_response(
            StatusCode::BAD_REQUEST,
            json!({"ok": false, "error": "invalid task_id"}),
        );
    }
    let Some(response_value) = body.get("response") else {
        return json_response(
            StatusCode::BAD_REQUEST,
            json!({"ok": false, "error": "response is required"}),
        );
    };
    let response: RelayResponse = match serde_json::from_value(response_value.clone()) {
        Ok(value) => value,
        Err(_) => {
            return json_response(
                StatusCode::BAD_REQUEST,
                json!({"ok": false, "error": "invalid relay response"}),
            );
        }
    };
    if response.request_id != task_id {
        return json_response(
            StatusCode::BAD_REQUEST,
            json!({"ok": false, "error": "response identity mismatch"}),
        );
    }
    if response.contract_version != "relay-response-v1" {
        return json_response(
            StatusCode::BAD_REQUEST,
            json!({"ok": false, "error": "unsupported response contract"}),
        );
    }
    match state.store.save_result(task_id, &response, now_unix_ms()) {
        Ok(SaveResultOutcome::Stored) => {
            state.result_notify.notify_waiters();
            json_response(StatusCode::OK, json!({"ok": true, "duplicate": false}))
        }
        Ok(SaveResultOutcome::Duplicate) => {
            state.result_notify.notify_waiters();
            json_response(StatusCode::OK, json!({"ok": true, "duplicate": true}))
        }
        Err(StoreError::ResultCollision) => json_response(
            StatusCode::CONFLICT,
            json!({"ok": false, "error": "result identity collision"}),
        ),
        Err(StoreError::TaskMissing) => json_response(
            StatusCode::CONFLICT,
            json!({"ok": false, "error": "task is no longer pending"}),
        ),
        Err(StoreError::TaskExpired) => json_response(
            StatusCode::CONFLICT,
            json!({"ok": false, "error": "task deadline has expired"}),
        ),
        Err(error) => state_backend_error(&error),
    }
}

fn agent_offline(state: Arc<AppState>, body: &Map<String, Value>) -> Response {
    if let Some(response) = validate_agent_project(&state, body) {
        return response;
    }
    match state.store.mark_offline(state.config.project_id()) {
        Ok(()) => json_response(
            StatusCode::OK,
            json!({"ok": true, "agent_online": false}),
        ),
        Err(error) => state_backend_error(&error),
    }
}

fn validate_agent_project(state: &AppState, body: &Map<String, Value>) -> Option<Response> {
    let project_id = body
        .get("project_id")
        .and_then(Value::as_str)
        .unwrap_or_default();
    (project_id != state.config.project_id()).then(|| {
        json_response(
            StatusCode::FORBIDDEN,
            json!({"ok": false, "error": "project_id is not allowed"}),
        )
    })
}

async fn handle_action(
    state: Arc<AppState>,
    headers: &HeaderMap,
    body: &Map<String, Value>,
) -> Response {
    if !authorized_remote(&state, headers) {
        return json_response(
            StatusCode::UNAUTHORIZED,
            json!({
                "status": "error",
                "error": {"code": "AUTH_FAILED", "message": "remote authorization failed"}
            }),
        );
    }
    let allowed_fields = BTreeSet::from(["action", "message"]);
    if body.keys().any(|key| !allowed_fields.contains(key.as_str())) {
        return json_response(
            StatusCode::BAD_REQUEST,
            json!({
                "status": "error",
                "error": {"code": "VALIDATION_FAILED", "message": "unknown action request fields"}
            }),
        );
    }
    let name = body
        .get("action")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let mut arguments = Map::new();
    if let Some(message) = body.get("message") {
        arguments.insert("message".to_owned(), message.clone());
    }
    let outcome = call_local_tool(state, name, Value::Object(arguments)).await;
    if outcome.is_error {
        json_response(
            StatusCode::OK,
            json!({"status": "error", "error": outcome.payload}),
        )
    } else {
        json_response(
            StatusCode::OK,
            json!({"status": "success", "result": outcome.payload}),
        )
    }
}

async fn handle_mcp(
    state: Arc<AppState>,
    headers: &HeaderMap,
    body: &Map<String, Value>,
) -> Response {
    let request_id = body.get("id").cloned().unwrap_or(Value::Null);
    if !authorized_remote(&state, headers) {
        return json_response(
            StatusCode::UNAUTHORIZED,
            mcp_error(request_id, -32_001, "remote authorization failed"),
        );
    }
    let method = body
        .get("method")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let params = body
        .get("params")
        .and_then(Value::as_object)
        .cloned()
        .unwrap_or_default();
    match method {
        "notifications/initialized" => empty_response(StatusCode::NO_CONTENT),
        "initialize" => {
            let protocol = params
                .get("protocolVersion")
                .and_then(Value::as_str)
                .filter(|value| !value.is_empty())
                .unwrap_or("2025-06-18");
            json_response(
                StatusCode::OK,
                mcp_result(
                    request_id,
                    json!({
                        "protocolVersion": protocol,
                        "capabilities": {"tools": {"listChanged": false}},
                        "serverInfo": {
                            "name": "agent-platform-relay-server",
                            "version": env!("CARGO_PKG_VERSION")
                        }
                    }),
                ),
            )
        }
        "ping" => json_response(StatusCode::OK, mcp_result(request_id, json!({}))),
        "tools/list" => json_response(
            StatusCode::OK,
            mcp_result(request_id, json!({"tools": tool_definitions()})),
        ),
        "tools/call" => {
            let name = params
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or_default();
            let arguments = params.get("arguments").cloned().unwrap_or_else(|| json!({}));
            let outcome = call_local_tool(state, name, arguments).await;
            json_response(
                StatusCode::OK,
                mcp_result(request_id, mcp_tool_result(outcome)),
            )
        }
        _ => json_response(
            StatusCode::OK,
            mcp_error(request_id, -32_601, &format!("method not found: {method}")),
        ),
    }
}

async fn call_local_tool(state: Arc<AppState>, name: &str, arguments: Value) -> LocalToolOutcome {
    let arguments = match validate_tool_arguments(name, arguments) {
        Ok(value) => value,
        Err(outcome) => return outcome,
    };
    let now = now_unix_ms();
    let status = match state.store.agent_status(state.config.project_id()) {
        Ok(value) => value,
        Err(error) => return backend_tool_error(&error),
    };
    let Some(status) = status else {
        return LocalToolOutcome::error(
            "AGENT_OFFLINE",
            "Local agent is switched off or its heartbeat is stale. Enable relay locally and retry.",
            true,
        );
    };
    if status.last_seen_unix_ms <= 0
        || now.saturating_sub(status.last_seen_unix_ms) > HEARTBEAT_TTL_MS
    {
        return LocalToolOutcome::error(
            "AGENT_OFFLINE",
            "Local agent is switched off or its heartbeat is stale. Enable relay locally and retry.",
            true,
        );
    }
    if !status.operations.iter().any(|operation| operation == name) {
        return LocalToolOutcome::error(
            "AGENT_CAPABILITY_UNAVAILABLE",
            "Local agent is online but did not advertise the requested operation.",
            true,
        );
    }

    let request_id = format!("rly_{}", Uuid::new_v4().simple());
    let deadline_unix_ms = now.saturating_add(TASK_TTL_MS);
    let task = StoredTask {
        task: RelayTask {
            contract_version: "relay-request-v1".to_owned(),
            request_id: request_id.clone(),
            operation: name.to_owned(),
            parameters: arguments,
            deadline_unix_ms,
        },
        project_id: state.config.project_id().to_owned(),
        created_unix_ms: now,
    };
    if let Err(error) = state.store.insert_task(&task) {
        return backend_tool_error(&error);
    }
    state.task_notify.notify_waiters();

    let deadline = Instant::now() + Duration::from_millis(TASK_TTL_MS.unsigned_abs());
    loop {
        let notified = state.result_notify.notified();
        match state.store.read_result(&request_id) {
            Ok(Some(response)) => return relay_response_to_outcome(response),
            Ok(None) => {}
            Err(error) => return backend_tool_error(&error),
        }
        let now_instant = Instant::now();
        if now_instant >= deadline {
            return LocalToolOutcome::error(
                "LOCAL_TIMEOUT",
                "Local agent did not return the task before its deadline.",
                true,
            );
        }
        let remaining = deadline.saturating_duration_since(now_instant);
        tokio::select! {
            _ = notified => {},
            () = sleep(remaining.min(RESULT_POLL_INTERVAL)) => {},
        }
    }
}

fn validate_tool_arguments(name: &str, arguments: Value) -> Result<Value, LocalToolOutcome> {
    let Some(object) = arguments.as_object() else {
        return Err(LocalToolOutcome::error(
            "VALIDATION_FAILED",
            "tool arguments must be an object",
            false,
        ));
    };
    match name {
        "runtime_self_test" => {
            if object.is_empty() {
                Ok(json!({}))
            } else {
                Err(LocalToolOutcome::error(
                    "VALIDATION_FAILED",
                    "runtime_self_test does not accept parameters",
                    false,
                ))
            }
        }
        "local_ping" => {
            if object.keys().any(|key| key != "message") {
                return Err(LocalToolOutcome::error(
                    "VALIDATION_FAILED",
                    "local_ping accepts only the optional message parameter",
                    false,
                ));
            }
            let message = match object.get("message") {
                Some(Value::String(value)) => value.clone(),
                Some(_) => {
                    return Err(LocalToolOutcome::error(
                        "VALIDATION_FAILED",
                        "local_ping message must be a string",
                        false,
                    ));
                }
                None => "ping".to_owned(),
            };
            if message.len() > MAX_PING_MESSAGE_BYTES {
                return Err(LocalToolOutcome::error(
                    "VALIDATION_FAILED",
                    "local_ping message exceeds 1024 bytes",
                    false,
                ));
            }
            Ok(json!({"message": message}))
        }
        _ => Err(LocalToolOutcome::error(
            "TOOL_NOT_FOUND",
            &format!("unknown tool: {name}"),
            false,
        )),
    }
}

fn relay_response_to_outcome(response: RelayResponse) -> LocalToolOutcome {
    if response.status == "success" {
        LocalToolOutcome::success(response.result)
    } else {
        LocalToolOutcome {
            payload: if response.error.is_null() {
                json!({"code": "LOCAL_ERROR", "message": "local execution failed"})
            } else {
                response.error
            },
            is_error: true,
        }
    }
}

fn backend_tool_error(error: &StoreError) -> LocalToolOutcome {
    eprintln!("relay state error: {error}");
    LocalToolOutcome::error(
        "STATE_BACKEND_UNAVAILABLE",
        "Relay state backend is unavailable.",
        true,
    )
}

fn state_backend_error(error: &StoreError) -> Response {
    eprintln!("relay state error: {error}");
    json_response(
        StatusCode::SERVICE_UNAVAILABLE,
        json!({
            "status": "error",
            "error": {
                "code": "STATE_BACKEND_UNAVAILABLE",
                "message": "Relay state backend is unavailable."
            }
        }),
    )
}

fn allowed_operations_from_poll(body: &Map<String, Value>) -> Vec<String> {
    let mut operations = BTreeSet::new();
    if let Some(values) = body.get("operations").and_then(Value::as_array) {
        for value in values {
            if let Some(operation) = value.as_str()
                && matches!(operation, "local_ping" | "runtime_self_test")
            {
                operations.insert(operation.to_owned());
            }
        }
    }
    operations.into_iter().collect()
}

fn authorized_agent(state: &AppState, headers: &HeaderMap) -> bool {
    header_value(headers, &AGENT_TOKEN_HEADER)
        .is_some_and(|supplied| constant_time_eq(state.config.agent_token.as_bytes(), supplied.as_bytes()))
}

fn authorized_remote(state: &AppState, headers: &HeaderMap) -> bool {
    let supplied = header_value(headers, &MCP_TOKEN_HEADER).or_else(|| {
        headers
            .get(AUTHORIZATION)
            .and_then(|value| value.to_str().ok())
            .and_then(|value| {
                value
                    .strip_prefix("Bearer ")
                    .or_else(|| value.strip_prefix("bearer "))
            })
            .map(str::trim)
    });
    supplied.is_some_and(|value| constant_time_eq(state.config.mcp_token.as_bytes(), value.as_bytes()))
}

fn header_value<'a>(headers: &'a HeaderMap, name: &HeaderName) -> Option<&'a str> {
    headers.get(name).and_then(|value| value.to_str().ok())
}

fn constant_time_eq(expected: &[u8], supplied: &[u8]) -> bool {
    if expected.len() != supplied.len() {
        return false;
    }
    let mut difference = 0_u8;
    for (&left, &right) in expected.iter().zip(supplied) {
        difference |= left ^ right;
    }
    difference == 0
}

fn validate_project_id(project_id: &str) -> Result<(), RelayServerError> {
    if project_id.is_empty()
        || project_id.len() > 128
        || !project_id
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.'))
    {
        return Err(RelayServerError::InvalidConfig(
            "RELAY_PROJECT_ID must be 1-128 URL-safe identifier characters".to_owned(),
        ));
    }
    Ok(())
}

fn validate_token(name: &str, token: &str) -> Result<(), RelayServerError> {
    if !(24..=256).contains(&token.len())
        || !token
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.' | b'~'))
    {
        return Err(RelayServerError::InvalidConfig(format!(
            "{name} must be 24-256 URL-safe ASCII characters"
        )));
    }
    Ok(())
}

fn valid_request_id(value: &str) -> bool {
    value.len() == 36
        && value.starts_with("rly_")
        && value[4..]
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn now_unix_ms() -> i64 {
    let millis = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    i64::try_from(millis).unwrap_or(i64::MAX)
}

fn tool_definitions() -> Vec<Value> {
    vec![
        json!({
            "name": "local_ping",
            "description": "Check that the explicitly enabled local Windows agent is reachable.",
            "inputSchema": {
                "type": "object",
                "additionalProperties": false,
                "properties": {"message": {"type": "string", "maxLength": 1024}}
            }
        }),
        json!({
            "name": "runtime_self_test",
            "description": "Run the policy-gated local agent-platform runtime self-test.",
            "inputSchema": {"type": "object", "additionalProperties": false, "properties": {}}
        }),
    ]
}

fn mcp_tool_result(outcome: LocalToolOutcome) -> Value {
    let text = serde_json::to_string(&outcome.payload)
        .unwrap_or_else(|_| "{\"code\":\"SERIALIZATION_FAILED\"}".to_owned());
    json!({
        "content": [{"type": "text", "text": text}],
        "structuredContent": outcome.payload,
        "isError": outcome.is_error
    })
}

fn mcp_result(request_id: Value, result: Value) -> Value {
    json!({"jsonrpc": "2.0", "id": request_id, "result": result})
}

fn mcp_error(request_id: Value, code: i64, message: &str) -> Value {
    json!({
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message}
    })
}

fn json_response(status: StatusCode, body: Value) -> Response {
    let mut response = (status, Json(body)).into_response();
    let headers = response.headers_mut();
    headers.insert(CACHE_CONTROL, HeaderValue::from_static("no-store"));
    headers.insert(CONTENT_TYPE_OPTIONS, HeaderValue::from_static("nosniff"));
    response
        .headers_mut()
        .insert(CONTENT_TYPE, HeaderValue::from_static("application/json; charset=utf-8"));
    response
}

fn empty_response(status: StatusCode) -> Response {
    let mut response = status.into_response();
    response
        .headers_mut()
        .insert(CACHE_CONTROL, HeaderValue::from_static("no-store"));
    response
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_config() -> RelayServerConfig {
        RelayServerConfig::new(
            "chat-agent-platform".to_owned(),
            "remote-token-abcdefghijklmnopqrstuvwxyz".to_owned(),
            "agent-token-abcdefghijklmnopqrstuvwxyz0".to_owned(),
            PathBuf::from("ignored.sqlite3"),
        )
        .expect("config")
    }

    #[test]
    fn tokens_are_separate_and_url_safe() {
        assert!(RelayServerConfig::new(
            "project".to_owned(),
            "same-token-abcdefghijklmnopqrstuvwxyz".to_owned(),
            "same-token-abcdefghijklmnopqrstuvwxyz".to_owned(),
            PathBuf::from("relay.sqlite3")
        )
        .is_err());
        assert!(RelayServerConfig::new(
            "project".to_owned(),
            "bad token with spaces but long enough".to_owned(),
            "agent-token-abcdefghijklmnopqrstuvwxyz0".to_owned(),
            PathBuf::from("relay.sqlite3")
        )
        .is_err());
    }

    #[test]
    fn arbitrary_request_id_header_is_irrelevant_to_auth() {
        let state = AppState::new(test_config(), Store::open_in_memory().expect("store"));
        let mut headers = HeaderMap::new();
        headers.insert(
            MCP_TOKEN_HEADER.clone(),
            HeaderValue::from_static("remote-token-abcdefghijklmnopqrstuvwxyz"),
        );
        headers.insert(
            HeaderName::from_static("x-request-id"),
            HeaderValue::from_static("eca27359-989e-4d83-a24d-3592998fe7f5/probe"),
        );
        assert!(authorized_remote(&state, &headers));
    }

    #[test]
    fn request_id_contract_is_strict() {
        assert!(valid_request_id("rly_0123456789abcdef0123456789abcdef"));
        assert!(!valid_request_id("rly_0123456789ABCDEF0123456789ABCDEF"));
        assert!(!valid_request_id("eca27359-989e-4d83-a24d-3592998fe7f5/probe"));
    }

    #[test]
    fn tool_validation_matches_local_allowlist() {
        assert!(validate_tool_arguments("runtime_self_test", json!({})).is_ok());
        assert!(validate_tool_arguments("runtime_self_test", json!({"x": 1})).is_err());
        assert!(validate_tool_arguments("local_ping", json!({"message": "hello"})).is_ok());
        assert!(validate_tool_arguments("shell.run", json!({})).is_err());
    }
}
