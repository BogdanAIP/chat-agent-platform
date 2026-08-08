use std::env;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;

use atomic_write_file::AtomicWriteFile;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

use super::protocol::{cleanup_old_cache, poll_once};
use super::{MAX_LONG_POLL_SECONDS, authorize_transport, validate_endpoint, validate_token};
use crate::binding::{ProjectBinding, resolve_project};
use crate::error::{PlatformError, io_error};
use crate::secret::SecretStore;

const STATUS_STALE_SECONDS: i64 = 90;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct WorkerStatus {
    contract_version: String,
    state: String,
    pid: u32,
    project_id: String,
    endpoint: String,
    started_at: String,
    updated_at: String,
    last_poll_at: Option<String>,
    last_task_id: Option<String>,
    consecutive_errors: u32,
    message: Option<String>,
}

struct RelayPaths {
    status: PathBuf,
    stop: PathBuf,
    cache: PathBuf,
    http: PathBuf,
}

impl RelayPaths {
    fn for_binding(binding: &ProjectBinding) -> Result<Self, PlatformError> {
        let root = binding.local_root.join("runtime").join("relay");
        fs::create_dir_all(&root)
            .map_err(|error| io_error("cannot create relay runtime directory", error))?;
        let root = fs::canonicalize(&root)
            .map_err(|error| io_error("cannot resolve relay runtime directory", error))?;
        if !root.starts_with(&binding.local_root) {
            return Err(PlatformError::Validation(
                "relay runtime directory escapes bound local root".into(),
            ));
        }
        let cache = root.join("responses");
        let http = root.join("http");
        fs::create_dir_all(&cache)
            .map_err(|error| io_error("cannot create relay response cache", error))?;
        fs::create_dir_all(&http)
            .map_err(|error| io_error("cannot create relay HTTP workspace", error))?;
        Ok(Self {
            status: root.join("status.json"),
            stop: root.join("stop.request"),
            cache,
            http,
        })
    }
}

pub fn relay_status(repo_root: &Path, project_id: Option<&str>) -> Result<Value, PlatformError> {
    let binding = resolve_project(repo_root, project_id)?;
    let paths = RelayPaths::for_binding(&binding)?;
    let status = read_status(&paths.status)?;
    Ok(status_value(status.as_ref()))
}

pub fn start_relay_worker(
    repo_root: &Path,
    project_id: Option<&str>,
    endpoint: &str,
    secret_ref: &str,
) -> Result<Value, PlatformError> {
    validate_endpoint(endpoint)?;
    let (binding, selection, policy) = authorize_transport(
        repo_root,
        project_id,
        json!({
            "action": "start",
            "external_destination": endpoint,
            "data_class": "project"
        }),
    )?;
    SecretStore::new(&binding.repo_root)?.with_secret(secret_ref, &selection, |_| Ok(()))?;
    let paths = RelayPaths::for_binding(&binding)?;
    if let Some(existing) = read_status(&paths.status)?
        && status_is_live(&existing)
    {
        return Ok(json!({
            "status": "already_running",
            "relay": status_value(Some(&existing)),
            "policy_decision_id": policy.decision_id
        }));
    }
    remove_if_exists(&paths.stop)?;
    cleanup_old_cache(&paths.cache)?;

    let now = Utc::now().to_rfc3339();
    write_status(
        &paths.status,
        &WorkerStatus {
            contract_version: "relay-worker-status-v1".into(),
            state: "starting".into(),
            pid: 0,
            project_id: binding.project_id.clone(),
            endpoint: endpoint.into(),
            started_at: now.clone(),
            updated_at: now,
            last_poll_at: None,
            last_task_id: None,
            consecutive_errors: 0,
            message: Some("starting detached long-poll worker".into()),
        },
    )?;

    let executable = env::current_exe()
        .map_err(|error| io_error("cannot resolve current agent-platform executable", error))?;
    let canonical_repo = fs::canonicalize(repo_root)
        .map_err(|error| io_error("cannot resolve relay repository root", error))?;
    let mut command = Command::new(executable);
    command
        .arg("--repo-root")
        .arg(canonical_repo)
        .arg("relay-worker")
        .arg("--project-id")
        .arg(&binding.project_id)
        .arg("--endpoint")
        .arg(endpoint)
        .arg("--secret-ref")
        .arg(secret_ref)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    configure_detached(&mut command);
    let child = command
        .spawn()
        .map_err(|error| io_error("cannot start detached relay worker", error))?;
    if let Some(mut current) = read_status(&paths.status)?
        && current.state == "starting"
    {
        current.pid = child.id();
        current.updated_at = Utc::now().to_rfc3339();
        write_status(&paths.status, &current)?;
    }

    for _ in 0..30 {
        thread::sleep(Duration::from_millis(100));
        if let Some(current) = read_status(&paths.status)?
            && matches!(current.state.as_str(), "running" | "error")
        {
            return Ok(json!({
                "status": if current.state == "running" { "started" } else { "error" },
                "relay": status_value(Some(&current)),
                "policy_decision_id": policy.decision_id
            }));
        }
    }
    Ok(json!({
        "status": "starting",
        "relay": status_value(read_status(&paths.status)?.as_ref()),
        "policy_decision_id": policy.decision_id
    }))
}

pub fn stop_relay_worker(
    repo_root: &Path,
    project_id: Option<&str>,
) -> Result<Value, PlatformError> {
    let (binding, _selection, policy) = authorize_transport(
        repo_root,
        project_id,
        json!({"action": "stop", "data_class": "project"}),
    )?;
    let paths = RelayPaths::for_binding(&binding)?;
    let Some(mut status) = read_status(&paths.status)? else {
        return Ok(json!({
            "status": "stopped",
            "already_stopped": true,
            "policy_decision_id": policy.decision_id
        }));
    };
    if !status_is_live(&status) || status.state == "stopped" {
        status.state = "stopped".into();
        status.updated_at = Utc::now().to_rfc3339();
        status.message = Some("worker was not live when stop was requested".into());
        write_status(&paths.status, &status)?;
        remove_if_exists(&paths.stop)?;
        return Ok(json!({
            "status": "stopped",
            "already_stopped": true,
            "relay": status_value(Some(&status)),
            "policy_decision_id": policy.decision_id
        }));
    }

    fs::write(&paths.stop, b"stop")
        .map_err(|error| io_error("cannot write relay stop request", error))?;
    status.state = "stopping".into();
    status.updated_at = Utc::now().to_rfc3339();
    status.message = Some(format!(
        "stop requested; worker exits after the current long poll (<= {MAX_LONG_POLL_SECONDS}s)"
    ));
    write_status(&paths.status, &status)?;

    for _ in 0..(MAX_LONG_POLL_SECONDS * 10 + 30) {
        thread::sleep(Duration::from_millis(100));
        let current = read_status(&paths.status)?;
        if current.as_ref().is_none_or(|item| item.state == "stopped") {
            remove_if_exists(&paths.stop)?;
            return Ok(json!({
                "status": "stopped",
                "relay": status_value(current.as_ref()),
                "policy_decision_id": policy.decision_id
            }));
        }
    }
    Ok(json!({
        "status": "stopping",
        "relay": status_value(read_status(&paths.status)?.as_ref()),
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
    let paths = RelayPaths::for_binding(&binding)?;
    cleanup_old_cache(&paths.cache)?;
    let started_at = Utc::now().to_rfc3339();
    let mut status = WorkerStatus {
        contract_version: "relay-worker-status-v1".into(),
        state: "running".into(),
        pid: std::process::id(),
        project_id: binding.project_id.clone(),
        endpoint: endpoint.into(),
        started_at: started_at.clone(),
        updated_at: started_at,
        last_poll_at: None,
        last_task_id: None,
        consecutive_errors: 0,
        message: Some("long polling enabled".into()),
    };
    write_status(&paths.status, &status)?;

    let store = SecretStore::new(&binding.repo_root)?;
    let mut completed = 0_u64;
    let execution = store.with_secret(secret_ref, &selection, |secret| {
        let token = std::str::from_utf8(secret)
            .map_err(|_| PlatformError::SecretStore("relay token is not UTF-8".into()))?;
        validate_token(token)?;
        let mut backoff = Duration::from_secs(1);
        loop {
            if paths.stop.exists() {
                break;
            }
            match poll_once(&binding, &paths.cache, &paths.http, endpoint, token) {
                Ok(processed) => {
                    status.last_poll_at = Some(Utc::now().to_rfc3339());
                    status.updated_at = Utc::now().to_rfc3339();
                    status.consecutive_errors = 0;
                    status.message = Some("long poll completed".into());
                    if let Some(task_id) = processed {
                        completed = completed.saturating_add(1);
                        status.last_task_id = Some(task_id);
                    }
                    write_status(&paths.status, &status)?;
                    backoff = Duration::from_secs(1);
                    if once {
                        break;
                    }
                }
                Err(error) if error.retryable() || matches!(error, PlatformError::Io { .. }) => {
                    status.updated_at = Utc::now().to_rfc3339();
                    status.consecutive_errors = status.consecutive_errors.saturating_add(1);
                    status.message = Some(format!("retryable transport error: {}", error.code()));
                    write_status(&paths.status, &status)?;
                    if once {
                        return Err(error);
                    }
                    sleep_interruptible(&paths.stop, backoff);
                    backoff = (backoff * 2).min(Duration::from_secs(15));
                }
                Err(error) => return Err(error),
            }
        }
        Ok(())
    });

    status.state = if execution.is_ok() {
        "stopped"
    } else {
        "error"
    }
    .into();
    status.updated_at = Utc::now().to_rfc3339();
    status.message = Some(if execution.is_ok() {
        "long polling disabled".into()
    } else {
        "relay worker stopped on a non-retryable error".into()
    });
    let _ = write_status(&paths.status, &status);
    let _ = remove_if_exists(&paths.stop);
    execution?;

    Ok(json!({
        "status": "success",
        "execution_path": "yandex.function.long_poll",
        "project_id": binding.project_id,
        "completed_requests": completed,
        "once": once,
        "policy_decision_id": policy.decision_id
    }))
}

fn read_status(path: &Path) -> Result<Option<WorkerStatus>, PlatformError> {
    let text = match fs::read_to_string(path) {
        Ok(value) => value,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(error) => return Err(io_error("cannot read relay status", error)),
    };
    let status: WorkerStatus = serde_json::from_str(&text)
        .map_err(|error| PlatformError::Validation(format!("relay status is corrupt: {error}")))?;
    if status.contract_version != "relay-worker-status-v1" {
        return Err(PlatformError::Validation(
            "unsupported relay worker status contract".into(),
        ));
    }
    Ok(Some(status))
}

fn write_status(path: &Path, status: &WorkerStatus) -> Result<(), PlatformError> {
    let text = serde_json::to_string_pretty(status).map_err(|error| {
        PlatformError::Validation(format!("cannot serialize relay status: {error}"))
    })?;
    let mut file = AtomicWriteFile::open(path)
        .map_err(|error| io_error("cannot open atomic relay status", error))?;
    file.write_all(text.as_bytes())
        .map_err(|error| io_error("cannot write atomic relay status", error))?;
    file.commit()
        .map_err(|error| io_error("cannot commit atomic relay status", error))
}

fn status_value(status: Option<&WorkerStatus>) -> Value {
    let Some(status) = status else {
        return json!({
            "contract_version": "relay-worker-status-v1",
            "state": "stopped",
            "enabled": false,
            "configured": false
        });
    };
    let live = status_is_live(status);
    json!({
        "contract_version": status.contract_version,
        "state": if live { status.state.as_str() } else { "stopped" },
        "enabled": live && matches!(status.state.as_str(), "starting" | "running" | "stopping"),
        "configured": true,
        "pid": status.pid,
        "project_id": status.project_id,
        "endpoint": status.endpoint,
        "started_at": status.started_at,
        "updated_at": status.updated_at,
        "last_poll_at": status.last_poll_at,
        "last_task_id": status.last_task_id,
        "consecutive_errors": status.consecutive_errors,
        "message": if live {
            status.message.clone()
        } else {
            Some("worker heartbeat is stale; relay is treated as stopped".into())
        }
    })
}

fn status_is_live(status: &WorkerStatus) -> bool {
    if !matches!(status.state.as_str(), "starting" | "running" | "stopping") {
        return false;
    }
    let timestamp = status
        .last_poll_at
        .as_deref()
        .unwrap_or(status.updated_at.as_str());
    chrono::DateTime::parse_from_rfc3339(timestamp).is_ok_and(|value| {
        Utc::now()
            .timestamp_millis()
            .saturating_sub(value.timestamp_millis())
            <= STATUS_STALE_SECONDS * 1000
    })
}

fn remove_if_exists(path: &Path) -> Result<(), PlatformError> {
    match fs::remove_file(path) {
        Ok(()) => Ok(()),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(error) => Err(io_error("cannot remove relay control file", error)),
    }
}

fn sleep_interruptible(stop_path: &Path, duration: Duration) {
    let slices = duration.as_millis().div_ceil(100);
    for _ in 0..slices {
        if stop_path.exists() {
            break;
        }
        thread::sleep(Duration::from_millis(100));
    }
}

#[cfg(windows)]
fn configure_detached(command: &mut Command) {
    use std::os::windows::process::CommandExt;

    const DETACHED_PROCESS: u32 = 0x0000_0008;
    const CREATE_NEW_PROCESS_GROUP: u32 = 0x0000_0200;
    const CREATE_NO_WINDOW: u32 = 0x0800_0000;
    command.creation_flags(DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW);
}

#[cfg(not(windows))]
fn configure_detached(_command: &mut Command) {}
