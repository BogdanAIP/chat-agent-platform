use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use serde_json::Value;
use uuid::Uuid;
use zeroize::Zeroize;

use super::{MAX_LONG_POLL_SECONDS, validate_endpoint, validate_token};
use crate::error::{PlatformError, io_error};

const CURL_CONNECT_TIMEOUT_SECONDS: u64 = 10;
const MAX_GATEWAY_RESPONSE_BYTES: usize = 256 * 1024;

pub(super) fn post_json(
    http_root: &Path,
    endpoint: &str,
    token: &str,
    payload: &Value,
    max_time_seconds: u64,
) -> Result<Value, PlatformError> {
    validate_endpoint(endpoint)?;
    validate_token(token)?;
    let body = serde_json::to_vec(payload)
        .map_err(|error| PlatformError::Validation(format!("cannot encode relay JSON: {error}")))?;
    let body_path = http_root.join(format!("req_{}.json", Uuid::new_v4().simple()));
    fs::write(&body_path, body).map_err(|error| io_error("cannot write relay request body", error))?;
    let cleanup = HttpBodyCleanup(body_path.clone());

    let curl = if cfg!(windows) { "curl.exe" } else { "curl" };
    let mut child = Command::new(curl)
        .arg("--config")
        .arg("-")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|error| {
            PlatformError::ToolUnavailable(format!("cannot start {curl} for relay HTTPS: {error}"))
        })?;

    let mut config = curl_config(endpoint, token, &body_path, max_time_seconds)?;
    let mut stdin = child
        .stdin
        .take()
        .ok_or_else(|| PlatformError::Validation("curl stdin is unavailable".into()))?;
    let write_result = stdin.write_all(config.as_bytes());
    config.zeroize();
    write_result.map_err(|error| io_error("cannot send relay curl configuration", error))?;
    drop(stdin);

    let output = child
        .wait_with_output()
        .map_err(|error| io_error("cannot wait for relay curl process", error))?;
    drop(cleanup);
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let stdout = String::from_utf8_lossy(&output.stdout);
        return Err(PlatformError::ToolUnavailable(format!(
            "relay HTTPS request failed: {}",
            truncate_text(
                if stderr.trim().is_empty() {
                    &stdout
                } else {
                    &stderr
                },
                700
            )
        )));
    }
    if output.stdout.len() > MAX_GATEWAY_RESPONSE_BYTES {
        return Err(PlatformError::Validation(
            "relay gateway response exceeds 256 KiB".into(),
        ));
    }
    serde_json::from_slice(&output.stdout).map_err(|error| {
        PlatformError::Validation(format!("relay gateway returned invalid JSON: {error}"))
    })
}

fn curl_config(
    endpoint: &str,
    token: &str,
    body_path: &Path,
    max_time_seconds: u64,
) -> Result<String, PlatformError> {
    let endpoint = escape_curl_config(endpoint)?;
    let path = escape_curl_config(&body_path.to_string_lossy())?;
    Ok(format!(
        "url = \"{endpoint}\"\nrequest = \"POST\"\nheader = \"Content-Type: application/json; charset=utf-8\"\nheader = \"Accept: application/json\"\nheader = \"X-Agent-Token: {token}\"\nheader = \"User-Agent: agent-platform/{}\"\nheader = \"Connection: close\"\ndata-binary = \"@{path}\"\nipv4\nnoproxy = \"*\"\ntlsv1.2\nconnect-timeout = {CURL_CONNECT_TIMEOUT_SECONDS}\nmax-time = {}\nsilent\nshow-error\nfail-with-body\n",
        env!("CARGO_PKG_VERSION"),
        max_time_seconds.clamp(10, MAX_LONG_POLL_SECONDS + 15)
    ))
}

fn escape_curl_config(value: &str) -> Result<String, PlatformError> {
    if value.chars().any(char::is_control) {
        return Err(PlatformError::Validation(
            "relay curl configuration values must not contain control characters".into(),
        ));
    }
    Ok(value.replace('\\', "\\\\").replace('"', "\\\""))
}

struct HttpBodyCleanup(PathBuf);

impl Drop for HttpBodyCleanup {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.0);
    }
}

fn truncate_text(value: &str, max_chars: usize) -> String {
    value.chars().take(max_chars).collect()
}
