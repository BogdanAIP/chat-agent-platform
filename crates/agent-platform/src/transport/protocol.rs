use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use atomic_write_file::AtomicWriteFile;
use serde_json::{Value, json};

use super::http::post_json;
use super::{
    DEFAULT_LONG_POLL_SECONDS, RelayRequest, RelayResponse, dispatch_request, validate_request_id,
};
use crate::binding::ProjectBinding;
use crate::contracts;
use crate::error::{PlatformError, io_error};

pub(super) fn poll_once(
    binding: &ProjectBinding,
    cache_root: &Path,
    http_root: &Path,
    endpoint: &str,
    token: &str,
) -> Result<Option<String>, PlatformError> {
    let response = post_json(
        http_root,
        endpoint,
        token,
        &json!({
            "agent_action": "poll",
            "wait_seconds": DEFAULT_LONG_POLL_SECONDS,
            "project_id": binding.project_id,
            "agent_version": env!("CARGO_PKG_VERSION"),
            "operations": ["local_ping", "runtime_self_test"]
        }),
        DEFAULT_LONG_POLL_SECONDS + 10,
    )?;
    if response.get("ok").and_then(Value::as_bool) != Some(true) {
        return Err(PlatformError::ToolUnavailable(
            response
                .get("error")
                .and_then(Value::as_str)
                .unwrap_or("relay gateway rejected poll")
                .to_owned(),
        ));
    }
    let Some(task) = response.get("task").filter(|value| !value.is_null()) else {
        return Ok(None);
    };
    let request: RelayRequest = serde_json::from_value(task.clone()).map_err(|error| {
        PlatformError::Validation(format!("gateway returned invalid relay task: {error}"))
    })?;
    let task_id = request.request_id.clone();
    let relay_response = if let Some(cached) = read_cached_response(cache_root, &task_id)? {
        cached
    } else {
        let response = dispatch_request(&binding.repo_root, &binding.project_id, request);
        cache_response(cache_root, &task_id, &response)?;
        response
    };
    let ack = post_json(
        http_root,
        endpoint,
        token,
        &json!({
            "agent_action": "result",
            "task_id": task_id,
            "response": relay_response
        }),
        15,
    )?;
    if ack.get("ok").and_then(Value::as_bool) != Some(true) {
        return Err(PlatformError::ToolUnavailable(
            ack.get("error")
                .and_then(Value::as_str)
                .unwrap_or("relay gateway did not accept task result")
                .to_owned(),
        ));
    }
    Ok(Some(task_id))
}

pub(super) fn cleanup_old_cache(root: &Path) -> Result<(), PlatformError> {
    let cutoff = SystemTime::now()
        .checked_sub(Duration::from_hours(24))
        .unwrap_or(UNIX_EPOCH);
    for entry in
        fs::read_dir(root).map_err(|error| io_error("cannot scan relay response cache", error))?
    {
        let entry = entry.map_err(|error| io_error("cannot read relay cache entry", error))?;
        let metadata = entry
            .metadata()
            .map_err(|error| io_error("cannot read relay cache metadata", error))?;
        if metadata.is_file() && metadata.modified().is_ok_and(|modified| modified < cutoff) {
            let _ = fs::remove_file(entry.path());
        }
    }
    Ok(())
}

fn cache_response(
    root: &Path,
    task_id: &str,
    response: &RelayResponse,
) -> Result<(), PlatformError> {
    let path = response_cache_path(root, task_id)?;
    let value = serde_json::to_value(response).map_err(|error| {
        PlatformError::Validation(format!("cannot serialize relay response: {error}"))
    })?;
    contracts::validate(&value, "relay-response-v1.schema.json")?;
    let text = serde_json::to_string_pretty(response).map_err(|error| {
        PlatformError::Validation(format!("cannot serialize relay response: {error}"))
    })?;
    let mut file = AtomicWriteFile::open(&path)
        .map_err(|error| io_error("cannot open relay response cache", error))?;
    file.write_all(text.as_bytes())
        .map_err(|error| io_error("cannot write relay response cache", error))?;
    file.commit()
        .map_err(|error| io_error("cannot commit relay response cache", error))
}

fn read_cached_response(
    root: &Path,
    task_id: &str,
) -> Result<Option<RelayResponse>, PlatformError> {
    let path = response_cache_path(root, task_id)?;
    let text = match fs::read_to_string(&path) {
        Ok(value) => value,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(error) => return Err(io_error("cannot read relay response cache", error)),
    };
    let value: Value = serde_json::from_str(&text).map_err(|error| {
        PlatformError::Validation(format!("relay response cache is corrupt: {error}"))
    })?;
    contracts::validate(&value, "relay-response-v1.schema.json")?;
    serde_json::from_value(value).map(Some).map_err(|error| {
        PlatformError::Validation(format!("cannot decode cached relay response: {error}"))
    })
}

fn response_cache_path(root: &Path, task_id: &str) -> Result<PathBuf, PlatformError> {
    validate_request_id(task_id)?;
    Ok(root.join(format!("{task_id}.json")))
}
