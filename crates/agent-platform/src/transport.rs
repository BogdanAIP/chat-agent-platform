use std::env;
use std::path::Path;
use std::thread;
use std::time::Duration;

use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use tungstenite::http::Request;
use tungstenite::{Message, connect};
use uuid::Uuid;
use zeroize::Zeroize;

use crate::binding::{ProjectBinding, resolve_project};
use crate::capability::{CapabilityRegistry, CapabilitySelection, required_quality};
use crate::contracts;
use crate::error::PlatformError;
use crate::policy::{PolicyDecision, PolicyEnforcementPoint};
use crate::secret::SecretStore;
use crate::service::self_test;

const CAPABILITY: &str = "transport.relay_connect";
pub const DEFAULT_SECRET_REF: &str = "relay.agent_token";
const MAX_PING_MESSAGE_BYTES: usize = 1024;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RelayRequest {
    pub contract_version: String,
    pub request_id: String,
    pub operation: String,
    pub parameters: Value,
    pub deadline_unix_ms: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RelayResponse {
    pub contract_version: String,
    pub request_id: String,
    pub status: String,
    pub result: Value,
    pub error: Value,
}

#[derive(Debug, Serialize)]
struct AgentHello<'a> {
    r#type: &'static str,
    contract_version: &'static str,
    agent_id: String,
    project_id: &'a str,
    operations: [&'static str; 2],
}

#[derive(Debug, Deserialize)]
struct RequestEnvelope {
    r#type: String,
    payload: RelayRequest,
}

#[derive(Debug, Serialize)]
struct ResponseEnvelope<'a> {
    r#type: &'static str,
    payload: &'a RelayResponse,
}

pub fn store_relay_token_from_env(
    repo_root: &Path,
    project_id: Option<&str>,
    env_name: &str,
    secret_ref: &str,
) -> Result<Value, PlatformError> {
    if env_name.trim().is_empty() {
        return Err(PlatformError::Validation(
            "relay token environment variable name must not be empty".into(),
        ));
    }
    let (binding, selection, policy) = authorize_transport(
        repo_root,
        project_id,
        json!({"action": "store_relay_token", "data_class": "sensitive"}),
    )?;
    let mut value = env::var(env_name).map_err(|_| {
        PlatformError::Validation(format!(
            "environment variable {env_name} is missing; relay token was not stored"
        ))
    })?;
    if value.len() < 24 {
        value.zeroize();
        return Err(PlatformError::Validation(
            "relay token must contain at least 24 bytes".into(),
        ));
    }
    let store = SecretStore::new(&binding.repo_root)?;
    let consumers = vec![selection.executor().to_owned()];
    let result = store.put(secret_ref, &consumers, value.as_bytes());
    value.zeroize();
    result?;
    Ok(json!({
        "status": "success",
        "secret_ref": secret_ref,
        "consumer": selection.executor(),
        "policy_decision_id": policy.decision_id,
        "raw_secret_returned": false
    }))
}

pub fn remove_relay_token(
    repo_root: &Path,
    project_id: Option<&str>,
    secret_ref: &str,
) -> Result<Value, PlatformError> {
    let (binding, selection, policy) = authorize_transport(
        repo_root,
        project_id,
        json!({"action": "remove_relay_token", "data_class": "sensitive"}),
    )?;
    SecretStore::new(&binding.repo_root)?.remove(secret_ref)?;
    Ok(json!({
        "status": "success",
        "secret_ref": secret_ref,
        "consumer": selection.executor(),
        "policy_decision_id": policy.decision_id
    }))
}

pub fn run_relay_worker(
    repo_root: &Path,
    project_id: Option<&str>,
    endpoint: &str,
    secret_ref: &str,
    once: bool,
) -> Result<Value, PlatformError> {
    validate_endpoint(endpoint)?;
    let (binding, selection, policy) = authorize_transport(
        repo_root,
        project_id,
        json!({
            "action": "connect",
            "external_destination": endpoint,
            "data_class": "project"
        }),
    )?;
    let store = SecretStore::new(&binding.repo_root)?;
    let mut completed = 0_u64;
    store.with_secret(secret_ref, &selection, |secret| {
        let token = std::str::from_utf8(secret)
            .map_err(|_| PlatformError::SecretStore("relay token is not UTF-8".into()))?;
        let mut backoff = Duration::from_secs(1);
        loop {
            match run_connection(&binding, endpoint, token, once) {
                Ok(count) => {
                    completed = completed.saturating_add(count);
                    if once {
                        return Ok(());
                    }
                    backoff = Duration::from_secs(1);
                }
                Err(error) if error.retryable() || matches!(error, PlatformError::Io { .. }) => {
                    if once {
                        return Err(error);
                    }
                    thread::sleep(backoff);
                    backoff = (backoff * 2).min(Duration::from_secs(30));
                }
                Err(error) => return Err(error),
            }
        }
    })?;
    Ok(json!({
        "status": "success",
        "execution_path": "yandex.relay.websocket",
        "project_id": binding.project_id,
        "completed_requests": completed,
        "once": once,
        "policy_decision_id": policy.decision_id
    }))
}

fn run_connection(
    binding: &ProjectBinding,
    endpoint: &str,
    token: &str,
    once: bool,
) -> Result<u64, PlatformError> {
    let request = Request::builder()
        .uri(endpoint)
        .header("Authorization", format!("Bearer {token}"))
        .header("User-Agent", "agent-platform-stage4")
        .body(())
        .map_err(|error| PlatformError::Validation(format!("invalid relay endpoint: {error}")))?;
    let (mut socket, _) = connect(request).map_err(|error| {
        PlatformError::ToolUnavailable(format!("cannot connect to relay endpoint: {error}"))
    })?;
    let hello = AgentHello {
        r#type: "hello",
        contract_version: "relay-agent-v1",
        agent_id: format!("agt_{}", Uuid::new_v4().simple()),
        project_id: &binding.project_id,
        operations: ["local_ping", "runtime_self_test"],
    };
    send_json(&mut socket, &hello)?;

    let mut completed = 0_u64;
    loop {
        let message = socket.read().map_err(|error| {
            PlatformError::ToolUnavailable(format!("relay connection closed: {error}"))
        })?;
        match message {
            Message::Text(text) => {
                let envelope: RequestEnvelope = serde_json::from_str(text.as_str()).map_err(|error| {
                    PlatformError::Validation(format!("invalid relay request envelope: {error}"))
                })?;
                if envelope.r#type != "request" {
                    return Err(PlatformError::Validation(
                        "relay sent unsupported envelope type".into(),
                    ));
                }
                let response = dispatch_request(&binding.repo_root, &binding.project_id, envelope.payload);
                send_json(
                    &mut socket,
                    &ResponseEnvelope {
                        r#type: "response",
                        payload: &response,
                    },
                )?;
                completed = completed.saturating_add(1);
                if once {
                    let _ = socket.close(None);
                    return Ok(completed);
                }
            }
            Message::Ping(payload) => socket.send(Message::Pong(payload)).map_err(|error| {
                PlatformError::ToolUnavailable(format!("relay pong failed: {error}"))
            })?,
            Message::Close(_) => return Ok(completed),
            Message::Binary(_) | Message::Pong(_) | Message::Frame(_) => {}
        }
    }
}

fn send_json<S, T>(socket: &mut tungstenite::WebSocket<S>, value: &T) -> Result<(), PlatformError>
where
    S: std::io::Read + std::io::Write,
    T: Serialize,
{
    let text = serde_json::to_string(value)
        .map_err(|error| PlatformError::Validation(format!("cannot serialize relay message: {error}")))?;
    socket.send(Message::Text(text.into())).map_err(|error| {
        PlatformError::ToolUnavailable(format!("cannot send relay message: {error}"))
    })
}

pub fn dispatch_request(repo_root: &Path, project_id: &str, request: RelayRequest) -> RelayResponse {
    match dispatch_request_inner(repo_root, project_id, &request) {
        Ok(result) => RelayResponse {
            contract_version: "relay-response-v1".into(),
            request_id: request.request_id,
            status: "success".into(),
            result,
            error: Value::Null,
        },
        Err(error) => RelayResponse {
            contract_version: "relay-response-v1".into(),
            request_id: request.request_id,
            status: "error".into(),
            result: Value::Null,
            error: serde_json::to_value(error.payload()).unwrap_or_else(|_| {
                json!({
                    "code": "VALIDATION_FAILED",
                    "message": "cannot serialize local error",
                    "retryable": false,
                    "safe_to_retry": false
                })
            }),
        },
    }
}

fn dispatch_request_inner(
    repo_root: &Path,
    project_id: &str,
    request: &RelayRequest,
) -> Result<Value, PlatformError> {
    let value = serde_json::to_value(request).map_err(|error| {
        PlatformError::Validation(format!("cannot serialize relay request: {error}"))
    })?;
    contracts::validate(&value, "relay-request-v1.schema.json")?;
    if request.deadline_unix_ms < Utc::now().timestamp_millis() {
        return Err(PlatformError::Validation(
            "relay request deadline has expired".into(),
        ));
    }
    match request.operation.as_str() {
        "local_ping" => {
            let message = request
                .parameters
                .get("message")
                .and_then(Value::as_str)
                .unwrap_or("ping");
            if message.len() > MAX_PING_MESSAGE_BYTES {
                return Err(PlatformError::Validation(
                    "local_ping message exceeds 1024 bytes".into(),
                ));
            }
            Ok(json!({
                "status": "success",
                "pong": true,
                "message": message,
                "project_id": project_id,
                "executed_locally": true
            }))
        }
        "runtime_self_test" => self_test(repo_root, Some(project_id)),
        other => Err(PlatformError::PolicyDenied(format!(
            "relay operation is not allowlisted: {other}"
        ))),
    }
}

fn authorize_transport(
    repo_root: &Path,
    project_id: Option<&str>,
    parameters: Value,
) -> Result<(ProjectBinding, CapabilitySelection, PolicyDecision), PlatformError> {
    let binding = resolve_project(repo_root, project_id)?;
    let quality = required_quality(&binding.repo_root, CAPABILITY)?;
    let selection = CapabilityRegistry::load(&binding.repo_root)?.select(CAPABILITY, &quality, 0)?;
    let data_class = parameters
        .get("data_class")
        .and_then(Value::as_str)
        .unwrap_or("project");
    let policy = PolicyEnforcementPoint::load(&binding.policy_path)?.evaluate(
        CAPABILITY,
        &parameters,
        data_class,
        None,
        selection.base_risk(),
    )?;
    Ok((binding, selection, policy))
}

fn validate_endpoint(endpoint: &str) -> Result<(), PlatformError> {
    let secure = endpoint.starts_with("wss://");
    let local = endpoint.starts_with("ws://127.0.0.1:") || endpoint.starts_with("ws://localhost:");
    if secure || local {
        Ok(())
    } else {
        Err(PlatformError::Validation(
            "relay endpoint must use wss://; ws:// is allowed only for localhost tests".into(),
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn public_plaintext_websocket_is_rejected() {
        assert!(validate_endpoint("ws://example.com/agent").is_err());
        assert!(validate_endpoint("wss://relay.example.com/agent").is_ok());
        assert!(validate_endpoint("ws://127.0.0.1:8787/agent").is_ok());
    }

    #[test]
    fn expired_request_is_rejected_before_dispatch() {
        let request = RelayRequest {
            contract_version: "relay-request-v1".into(),
            request_id: format!("rly_{}", Uuid::new_v4().simple()),
            operation: "local_ping".into(),
            parameters: json!({"message": "hello"}),
            deadline_unix_ms: 1,
        };
        let response = dispatch_request(Path::new("."), "demo", request);
        assert_eq!(response.status, "error");
        assert_eq!(response.error["code"], "VALIDATION_FAILED");
    }
}
