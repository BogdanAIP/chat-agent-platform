use std::env;
use std::net::SocketAddr;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use axum::Json;
use axum::Router;
use axum::extract::rejection::JsonRejection;
use axum::extract::{DefaultBodyLimit, State};
use axum::http::header::CACHE_CONTROL;
use axum::http::{HeaderMap, HeaderName, HeaderValue, StatusCode};
use axum::response::{IntoResponse, Response};
use axum::routing::{get, post};
use serde::Deserialize;
use serde_json::{Value, json};
use tokio::net::TcpListener;
use tokio::sync::Semaphore;
use zeroize::{Zeroize, Zeroizing};

use super::{authorize_transport_capability, dispatch_operation, validate_token};
use crate::error::PlatformError;
use crate::secret::SecretStore;

const CAPABILITY: &str = "transport.local_ingress";
const CONTRACT: &str = "local-ingress-v1";
pub const DEFAULT_SECRET_REF: &str = "secret://ingress/caller_token";
pub const DEFAULT_PORT: u16 = 8787;
const MAX_BODY_BYTES: usize = 8 * 1024;
const MAX_IN_FLIGHT: usize = 4;

static MCP_TOKEN_HEADER: HeaderName = HeaderName::from_static("x-mcp-token");
static CONTENT_TYPE_OPTIONS: HeaderName = HeaderName::from_static("x-content-type-options");

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ActionRequest {
    action: String,
    #[serde(default)]
    message: Option<String>,
}

struct IngressState {
    repo_root: PathBuf,
    project_id: String,
    token: Zeroizing<Vec<u8>>,
    in_flight: Arc<Semaphore>,
}

pub fn store_ingress_token_from_env(
    repo_root: &Path,
    project_id: Option<&str>,
    env_name: &str,
    secret_ref: &str,
) -> Result<Value, PlatformError> {
    if env_name.trim().is_empty() {
        return Err(PlatformError::Validation(
            "ingress token environment variable name must not be empty".into(),
        ));
    }
    let (binding, selection, policy) = authorize_transport_capability(
        repo_root,
        project_id,
        CAPABILITY,
        json!({"action": "store_ingress_token", "data_class": "sensitive"}),
    )?;
    let mut value = env::var(env_name).map_err(|_| {
        PlatformError::Validation(format!(
            "environment variable {env_name} is missing; ingress token was not stored"
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

pub fn remove_ingress_token(
    repo_root: &Path,
    project_id: Option<&str>,
    secret_ref: &str,
) -> Result<Value, PlatformError> {
    let (binding, selection, policy) = authorize_transport_capability(
        repo_root,
        project_id,
        CAPABILITY,
        json!({"action": "remove_ingress_token", "data_class": "sensitive"}),
    )?;
    SecretStore::new(&binding.repo_root)?.remove(secret_ref)?;
    Ok(json!({
        "status": "success",
        "secret_ref": secret_ref,
        "consumer": selection.executor(),
        "policy_decision_id": policy.decision_id,
        "configured": false
    }))
}

pub fn serve_local_ingress(
    repo_root: &Path,
    project_id: Option<&str>,
    port: u16,
    secret_ref: &str,
) -> Result<Value, PlatformError> {
    if port == 0 {
        return Err(PlatformError::Validation(
            "ingress port must be between 1 and 65535".into(),
        ));
    }
    let (binding, selection, policy) = authorize_transport_capability(
        repo_root,
        project_id,
        CAPABILITY,
        json!({
            "action": "serve_local_ingress",
            "data_class": "sensitive",
            "bind": "127.0.0.1",
            "port": port
        }),
    )?;
    let mut token = Zeroizing::new(Vec::new());
    SecretStore::new(&binding.repo_root)?.with_secret(secret_ref, &selection, |secret| {
        token.extend_from_slice(secret);
        Ok(())
    })?;
    let token_text = std::str::from_utf8(&token)
        .map_err(|_| PlatformError::Validation("ingress token is not valid UTF-8".into()))?;
    validate_token(token_text)?;

    let address = SocketAddr::from(([127, 0, 0, 1], port));
    let state = Arc::new(IngressState {
        repo_root: binding.repo_root.clone(),
        project_id: binding.project_id.clone(),
        token,
        in_flight: Arc::new(Semaphore::new(MAX_IN_FLIGHT)),
    });
    let runtime = tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()
        .map_err(|error| {
            PlatformError::Validation(format!("cannot start ingress runtime: {error}"))
        })?;

    eprintln!(
        "agent-platform local ingress listening on http://{address} for project {}; publish this loopback endpoint only through a trusted HTTPS tunnel",
        binding.project_id
    );
    runtime.block_on(async move {
        let listener = TcpListener::bind(address)
            .await
            .map_err(|error| crate::error::io_error("cannot bind local ingress", error))?;
        axum::serve(listener, router(state))
            .with_graceful_shutdown(async {
                let _ = tokio::signal::ctrl_c().await;
            })
            .await
            .map_err(|error| crate::error::io_error("local ingress server failed", error))?;
        Ok::<(), PlatformError>(())
    })?;

    Ok(json!({
        "status": "stopped",
        "contract_version": CONTRACT,
        "bind": "127.0.0.1",
        "port": port,
        "policy_decision_id": policy.decision_id
    }))
}

fn router(state: Arc<IngressState>) -> Router {
    Router::new()
        .route("/healthz", get(healthz))
        .route("/gpt", post(handle_action))
        .fallback(not_found)
        .layer(DefaultBodyLimit::max(MAX_BODY_BYTES))
        .with_state(state)
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

async fn handle_action(
    State(state): State<Arc<IngressState>>,
    headers: HeaderMap,
    payload: Result<Json<ActionRequest>, JsonRejection>,
) -> Response {
    if !authorized(&headers, &state.token) {
        return json_response(
            StatusCode::UNAUTHORIZED,
            json!({"status": "error", "error": {"code": "UNAUTHORIZED", "message": "caller authentication failed", "retryable": false, "safe_to_retry": false}}),
        );
    }
    let Ok(Json(request)) = payload else {
        return json_response(
            StatusCode::BAD_REQUEST,
            json!({"status": "error", "error": {"code": "VALIDATION_FAILED", "message": "request body must match the local action schema", "retryable": false, "safe_to_retry": false}}),
        );
    };
    let (operation, parameters) = match action_parameters(request) {
        Ok(value) => value,
        Err(error) => return platform_error_response(StatusCode::OK, &error),
    };
    let Ok(permit) = Arc::clone(&state.in_flight).try_acquire_owned() else {
        return json_response(
            StatusCode::TOO_MANY_REQUESTS,
            json!({"status": "error", "error": {"code": "BUSY", "message": "local ingress concurrency limit reached", "retryable": true, "safe_to_retry": true}}),
        );
    };
    let repo_root = state.repo_root.clone();
    let project_id = state.project_id.clone();
    let result = tokio::task::spawn_blocking(move || {
        let _permit = permit;
        dispatch_operation(&repo_root, &project_id, &operation, &parameters)
    })
    .await;

    match result {
        Ok(Ok(value)) => json_response(
            StatusCode::OK,
            json!({"status": "success", "result": value, "error": Value::Null}),
        ),
        Ok(Err(error)) => platform_error_response(StatusCode::OK, &error),
        Err(_) => json_response(
            StatusCode::INTERNAL_SERVER_ERROR,
            json!({"status": "error", "error": {"code": "LOCAL_EXECUTION_FAILED", "message": "local execution worker failed", "retryable": true, "safe_to_retry": true}}),
        ),
    }
}

fn action_parameters(request: ActionRequest) -> Result<(String, Value), PlatformError> {
    match request.action.as_str() {
        "local_ping" => Ok((
            request.action,
            request
                .message
                .map_or_else(|| json!({}), |message| json!({"message": message})),
        )),
        "runtime_self_test" => {
            if request.message.is_some() {
                return Err(PlatformError::Validation(
                    "runtime_self_test does not accept message".into(),
                ));
            }
            Ok((request.action, json!({})))
        }
        other => Err(PlatformError::PolicyDenied(format!(
            "remote operation is not allowlisted: {other}"
        ))),
    }
}

fn authorized(headers: &HeaderMap, expected: &[u8]) -> bool {
    let Some(actual) = headers.get(&MCP_TOKEN_HEADER) else {
        return false;
    };
    let Ok(actual) = actual.to_str() else {
        return false;
    };
    constant_time_eq(actual.as_bytes(), expected)
}

fn constant_time_eq(left: &[u8], right: &[u8]) -> bool {
    if left.len() != right.len() {
        return false;
    }
    let mut difference = 0_u8;
    for (&left_byte, &right_byte) in left.iter().zip(right) {
        difference |= left_byte ^ right_byte;
    }
    difference == 0
}

fn platform_error_response(status: StatusCode, error: &PlatformError) -> Response {
    let payload = serde_json::to_value(error.payload()).unwrap_or_else(|_| {
        json!({
            "code": "VALIDATION_FAILED",
            "message": "cannot serialize local error",
            "retryable": false,
            "safe_to_retry": false
        })
    });
    json_response(
        status,
        json!({"status": "error", "result": Value::Null, "error": payload}),
    )
}

fn json_response(status: StatusCode, body: Value) -> Response {
    let mut response = (status, Json(body)).into_response();
    response
        .headers_mut()
        .insert(CACHE_CONTROL, HeaderValue::from_static("no-store"));
    response.headers_mut().insert(
        CONTENT_TYPE_OPTIONS.clone(),
        HeaderValue::from_static("nosniff"),
    );
    response
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn token_comparison_does_not_short_circuit_by_prefix() {
        assert!(constant_time_eq(
            b"abcdefghijklmnopqrstuvwxyz",
            b"abcdefghijklmnopqrstuvwxyz"
        ));
        assert!(!constant_time_eq(
            b"abcdefghijklmnopqrstuvwxy0",
            b"abcdefghijklmnopqrstuvwxyz"
        ));
        assert!(!constant_time_eq(b"short", b"abcdefghijklmnopqrstuvwxyz"));
    }

    #[test]
    fn action_translation_is_fail_closed() {
        let ping = action_parameters(ActionRequest {
            action: "local_ping".into(),
            message: Some("hello".into()),
        })
        .expect("ping should translate");
        assert_eq!(ping.0, "local_ping");
        assert_eq!(ping.1["message"], "hello");

        assert!(
            action_parameters(ActionRequest {
                action: "runtime_self_test".into(),
                message: Some("unexpected".into()),
            })
            .is_err()
        );
        assert!(
            action_parameters(ActionRequest {
                action: "shell.run_arbitrary".into(),
                message: None,
            })
            .is_err()
        );
    }

    #[tokio::test]
    async fn authenticated_ping_runs_local_dispatch() {
        let state = Arc::new(IngressState {
            repo_root: PathBuf::from("."),
            project_id: "demo".into(),
            token: Zeroizing::new(b"abcdefghijklmnopqrstuvwxyz".to_vec()),
            in_flight: Arc::new(Semaphore::new(1)),
        });
        let mut headers = HeaderMap::new();
        headers.insert(
            &MCP_TOKEN_HEADER,
            HeaderValue::from_static("abcdefghijklmnopqrstuvwxyz"),
        );
        let response = handle_action(
            State(state),
            headers,
            Ok(Json(ActionRequest {
                action: "local_ping".into(),
                message: Some("direct".into()),
            })),
        )
        .await;
        assert_eq!(response.status(), StatusCode::OK);
        let bytes = axum::body::to_bytes(response.into_body(), 4096)
            .await
            .expect("response body should be readable");
        let value: Value = serde_json::from_slice(&bytes).expect("response must be JSON");
        assert_eq!(value["status"], "success");
        assert_eq!(value["result"]["executed_locally"], true);
        assert_eq!(value["result"]["message"], "direct");
    }

    #[tokio::test]
    async fn missing_token_is_rejected_before_dispatch() {
        let state = Arc::new(IngressState {
            repo_root: PathBuf::from("."),
            project_id: "demo".into(),
            token: Zeroizing::new(b"abcdefghijklmnopqrstuvwxyz".to_vec()),
            in_flight: Arc::new(Semaphore::new(1)),
        });
        let response = handle_action(
            State(state),
            HeaderMap::new(),
            Ok(Json(ActionRequest {
                action: "local_ping".into(),
                message: None,
            })),
        )
        .await;
        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
    }
}
