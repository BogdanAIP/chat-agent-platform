use std::path::Path;

use serde_json::{Map, Value};

use crate::binding::resolve_project;
use crate::error::PlatformError;
use crate::job::JobStore;

pub fn begin_job(
    repo_root: &Path,
    project_id: Option<&str>,
    capability: &str,
    idempotency_key: &str,
) -> Result<Value, PlatformError> {
    let store = store(repo_root, project_id)?;
    serialize(store.begin(capability, idempotency_key)?)
}

pub fn get_job(
    repo_root: &Path,
    project_id: Option<&str>,
    job_id: &str,
) -> Result<Value, PlatformError> {
    let store = store(repo_root, project_id)?;
    serialize(store.get(job_id)?)
}

pub fn resume_job(
    repo_root: &Path,
    project_id: Option<&str>,
    job_id: &str,
) -> Result<Value, PlatformError> {
    let store = store(repo_root, project_id)?;
    serialize(store.resume(job_id)?)
}

pub fn checkpoint_job(
    repo_root: &Path,
    project_id: Option<&str>,
    job_id: &str,
    name: &str,
    data_json: &str,
) -> Result<Value, PlatformError> {
    let store = store(repo_root, project_id)?;
    let data = parse_object(data_json, "checkpoint data")?;
    serialize(store.checkpoint(job_id, name, data)?)
}

pub fn succeed_job(
    repo_root: &Path,
    project_id: Option<&str>,
    job_id: &str,
    result_json: &str,
) -> Result<Value, PlatformError> {
    let store = store(repo_root, project_id)?;
    let result = parse_object(result_json, "job result")?;
    serialize(store.succeed(job_id, result)?)
}

pub fn fail_job(
    repo_root: &Path,
    project_id: Option<&str>,
    job_id: &str,
    error_json: &str,
) -> Result<Value, PlatformError> {
    let store = store(repo_root, project_id)?;
    let error = parse_object(error_json, "job error")?;
    serialize(store.fail(job_id, error)?)
}

pub fn cancel_job(
    repo_root: &Path,
    project_id: Option<&str>,
    job_id: &str,
) -> Result<Value, PlatformError> {
    let store = store(repo_root, project_id)?;
    serialize(store.cancel(job_id)?)
}

fn store(repo_root: &Path, project_id: Option<&str>) -> Result<JobStore, PlatformError> {
    let binding = resolve_project(repo_root, project_id)?;
    JobStore::for_binding(&binding)
}

fn parse_object(text: &str, label: &str) -> Result<Map<String, Value>, PlatformError> {
    let value: Value = serde_json::from_str(text)
        .map_err(|error| PlatformError::Validation(format!("invalid {label} JSON: {error}")))?;
    value
        .as_object()
        .cloned()
        .ok_or_else(|| PlatformError::Validation(format!("{label} must be a JSON object")))
}

fn serialize<T: serde::Serialize>(value: T) -> Result<Value, PlatformError> {
    serde_json::to_value(value)
        .map_err(|error| PlatformError::Validation(format!("cannot serialize job result: {error}")))
}
