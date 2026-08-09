mod http;
mod ingress;
mod lifecycle;
mod protocol;

use std::env;
use std::path::Path;

use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value, json};
use zeroize::Zeroize;

use crate::binding::{ProjectBinding, resolve_project};
use crate::capability::{CapabilityRegistry, CapabilitySelection, required_quality};
use crate::contracts;
use crate::error::PlatformError;
use crate::policy::{PolicyDecision, PolicyEnforcementPoint};
use crate::secret::SecretStore;
use crate::service::self_test;

pub use ingress::{
    DEFAULT_PORT as DEFAULT_INGRESS_PORT, DEFAULT_SECRET_REF as DEFAULT_INGRESS_SECRET_REF,
    remove_ingress_token, serve_local_ingress, store_ingress_token_from_env,
};
pub use lifecycle::{relay_status, run_relay_worker, start_relay_worker, stop_relay_worker};

const RELAY_CAPABILITY: &str = "transport.relay_connect";
pub const DEFAULT_SECRET_REF: &str = "secret://relay/agent_token";
pub const DEFAULT_LONG_POLL_SECONDS: u64 = 25;
pub(super) const MAX_LONG_POLL_SECONDS: u64 = 30;
pub(super) const MAX_PING_MESSAGE_BYTES: usize = 1024;

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

pub fn configure_relay(
    repo_root: &Path,
    project_id: Option<&str>,
    endpoint: &str,
    env_name: &str,
    secret_ref: &str,
) -> Result<Value, PlatformError> {
    validate_endpoint(endpoint)?;
    let token = store_relay_token_from_env(repo_root, project_id, env_name, secret_ref)?;
    match lifecycle::write_relay_config(repo_root, project_id, endpoint, secret_ref) {
        Ok(config) => Ok(json!({
            "status": "configured",
            "relay": config,
            "credential": token,
            "enabled": false
        })),
        Err(error) => {
            let _ = remove_relay_token(repo_root, project_id, secret_ref);
            Err(error)
        }
    }
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
    validate_token(&value)?;
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
    lifecycle::remove_relay_config(repo_root, project_id)?;
    Ok(json!({
        "status": "success",
        "secret_ref": secret_ref,
        "consumer": selection.executor(),
        "policy_decision_id": policy.decision_id,
        "configured": false
    }))
}

#[must_use]
pub fn dispatch_request(
    repo_root: &Path,
    project_id: &str,
    request: RelayRequest,
) -> RelayResponse {
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
    dispatch_operation(
        repo_root,
        project_id,
        &request.operation,
        &request.parameters,
    )
}

pub(super) fn dispatch_operation(
    repo_root: &Path,
    project_id: &str,
    operation: &str,
    parameters: &Value,
) -> Result<Value, PlatformError> {
    let parameters = parameters.as_object().ok_or_else(|| {
        PlatformError::Validation("remote operation parameters must be an object".into())
    })?;
    match operation {
        "local_ping" => dispatch_local_ping(project_id, parameters),
        "runtime_self_test" => {
            require_no_parameters("runtime_self_test", parameters)?;
            self_test(repo_root, Some(project_id))
        }
        other => Err(PlatformError::PolicyDenied(format!(
            "remote operation is not allowlisted: {other}"
        ))),
    }
}

fn dispatch_local_ping(
    project_id: &str,
    parameters: &Map<String, Value>,
) -> Result<Value, PlatformError> {
    if parameters.keys().any(|key| key != "message") {
        return Err(PlatformError::Validation(
            "local_ping accepts only the optional message parameter".into(),
        ));
    }
    let message = match parameters.get("message") {
        Some(Value::String(value)) => value.as_str(),
        Some(_) => {
            return Err(PlatformError::Validation(
                "local_ping message must be a string".into(),
            ));
        }
        None => "ping",
    };
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

fn require_no_parameters(
    operation: &str,
    parameters: &Map<String, Value>,
) -> Result<(), PlatformError> {
    if parameters.is_empty() {
        Ok(())
    } else {
        Err(PlatformError::Validation(format!(
            "{operation} does not accept parameters"
        )))
    }
}

pub(super) fn authorize_transport(
    repo_root: &Path,
    project_id: Option<&str>,
    parameters: Value,
) -> Result<(ProjectBinding, CapabilitySelection, PolicyDecision), PlatformError> {
    authorize_transport_capability(repo_root, project_id, RELAY_CAPABILITY, parameters)
}

pub(super) fn authorize_transport_capability(
    repo_root: &Path,
    project_id: Option<&str>,
    capability: &str,
    parameters: Value,
) -> Result<(ProjectBinding, CapabilitySelection, PolicyDecision), PlatformError> {
    let binding = resolve_project(repo_root, project_id)?;
    let quality = required_quality(&binding.repo_root, capability)?;
    let selection =
        CapabilityRegistry::load(&binding.repo_root)?.select(capability, &quality, 0)?;
    let data_class = parameters
        .get("data_class")
        .and_then(Value::as_str)
        .unwrap_or("project");
    let policy = PolicyEnforcementPoint::load(&binding.policy_path)?.evaluate(
        capability,
        &parameters,
        data_class,
        None,
        selection.base_risk(),
    )?;
    Ok((binding, selection, policy))
}

pub(super) fn validate_endpoint(endpoint: &str) -> Result<(), PlatformError> {
    if endpoint.chars().any(char::is_control) {
        return Err(PlatformError::Validation(
            "relay endpoint contains control characters".into(),
        ));
    }
    let secure = endpoint.starts_with("https://");
    let local = endpoint.starts_with("http://127.0.0.1:")
        || endpoint.starts_with("http://localhost:")
        || endpoint == "http://localhost"
        || endpoint == "http://127.0.0.1";
    if secure || local {
        Ok(())
    } else {
        Err(PlatformError::Validation(
            "relay endpoint must use https://; http:// is allowed only for localhost tests".into(),
        ))
    }
}

pub(super) fn validate_token(token: &str) -> Result<(), PlatformError> {
    if !(24..=256).contains(&token.len())
        || !token
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.' | b'~'))
    {
        return Err(PlatformError::Validation(
            "transport token must be 24-256 URL-safe ASCII characters".into(),
        ));
    }
    Ok(())
}

pub(super) fn validate_request_id(value: &str) -> Result<(), PlatformError> {
    if value.len() != 36
        || !value.starts_with("rly_")
        || !value[4..].bytes().all(|byte| byte.is_ascii_hexdigit())
    {
        return Err(PlatformError::Validation(format!(
            "invalid relay request id: {value}"
        )));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use uuid::Uuid;

    #[test]
    fn public_plaintext_endpoint_is_rejected() {
        assert!(validate_endpoint("http://example.com/agent").is_err());
        assert!(validate_endpoint("https://relay.example.com/agent").is_ok());
        assert!(validate_endpoint("http://127.0.0.1:8787/agent").is_ok());
    }

    #[test]
    fn token_must_be_url_safe_and_long_enough() {
        assert!(validate_token("short").is_err());
        assert!(validate_token("abcdefghijklmnopqrstuvwx").is_ok());
        assert!(validate_token("abcdefghijklmnopqrstuvw\n").is_err());
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

    #[test]
    fn contract_rejects_unknown_operation() {
        let request = RelayRequest {
            contract_version: "relay-request-v1".into(),
            request_id: format!("rly_{}", Uuid::new_v4().simple()),
            operation: "shell.run_arbitrary".into(),
            parameters: json!({}),
            deadline_unix_ms: Utc::now().timestamp_millis() + 10_000,
        };
        let response = dispatch_request(Path::new("."), "demo", request);
        assert_eq!(response.status, "error");
        assert_eq!(response.error["code"], "VALIDATION_FAILED");
    }

    #[test]
    fn allowlisted_operations_reject_extra_parameters() {
        let ping = RelayRequest {
            contract_version: "relay-request-v1".into(),
            request_id: format!("rly_{}", Uuid::new_v4().simple()),
            operation: "local_ping".into(),
            parameters: json!({"message": "ok", "unexpected": true}),
            deadline_unix_ms: Utc::now().timestamp_millis() + 10_000,
        };
        let ping_response = dispatch_request(Path::new("."), "demo", ping);
        assert_eq!(ping_response.status, "error");

        let self_test = RelayRequest {
            contract_version: "relay-request-v1".into(),
            request_id: format!("rly_{}", Uuid::new_v4().simple()),
            operation: "runtime_self_test".into(),
            parameters: json!({"unexpected": true}),
            deadline_unix_ms: Utc::now().timestamp_millis() + 10_000,
        };
        let self_test_response = dispatch_request(Path::new("."), "demo", self_test);
        assert_eq!(self_test_response.status, "error");
    }
}
