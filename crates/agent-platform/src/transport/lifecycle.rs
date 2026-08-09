use std::env;
use std::fs::{self, File, OpenOptions, TryLockError};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;

use atomic_write_file::AtomicWriteFile;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

use super::protocol::{cleanup_old_cache, notify_offline, poll_once};
use super::{
    DEFAULT_SECRET_REF, MAX_LONG_POLL_SECONDS, authorize_transport, validate_endpoint,
    validate_token,
};
use crate::binding::{ProjectBinding, resolve_project};
use crate::error::{PlatformError, io_error};
use crate::secret::SecretStore;

const STATUS_STALE_SECONDS: i64 = 90;
const WORKER_LOCK_PROTOCOL: &str = "worker-lock-v1";

#[derive(Debug, Clone, Serialize, Deserialize)]
struct RelayConfig {
    contract_version: String,
    endpoint: String,
    secret_ref: String,
    configured_at: String,
}

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
    #[serde(default, skip_serializing_if = "Option::is_none")]
    liveness_protocol: Option<String>,
}

struct RelayPaths {
    config: PathBuf,
    status: PathBuf,
    stop: PathBuf,
    worker_lock: PathBuf,
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
            config: root.join("config.json"),
            status: root.join("status.json"),
            stop: root.join("stop.request"),
            worker_lock: root.join("worker.lock"),
            cache,
            http,
        })
    }
}

pub(super) fn write_relay_config(
    repo_root: &Path,
    project_id: Option<&str>,
    endpoint: &str,
    secret_ref: &str,
) -> Result<Value, PlatformError> {
    validate_endpoint(endpoint)?;
    if secret_ref.trim().is_empty() {
        return Err(PlatformError::Validation(
            "relay secret reference must not be empty".into(),
        ));
    }
    let binding = resolve_project(repo_root, project_id)?;
    let paths = RelayPaths::for_binding(&binding)?;
    let config = RelayConfig {
        contract_version: "relay-config-v1".into(),
        endpoint: endpoint.into(),
        secret_ref: secret_ref.into(),
        configured_at: Utc::now().to_rfc3339(),
    };
    write_config(&paths.config, &config)?;
    Ok(json!({
        "contract_version": config.contract_version,
        "endpoint": config.endpoint,
        "secret_ref": config.secret_ref,
        "configured_at": config.configured_at
    }))
}

pub(super) fn remove_relay_config(
    repo_root: &Path,
    project_id: Option<&str>,
) -> Result<(), PlatformError> {
    let binding = resolve_project(repo_root, project_id)?;
    let paths = RelayPaths::for_binding(&binding)?;
    remove_if_exists(&paths.config)
}

pub fn relay_status(repo_root: &Path, project_id: Option<&str>) -> Result<Value, PlatformError> {
    let binding = resolve_project(repo_root, project_id)?;
    let paths = RelayPaths::for_binding(&binding)?;
    let config = read_config(&paths.config)?;
    let status = read_status(&paths.status)?;
    let worker_lock_held = worker_lock_is_held(&paths.worker_lock)?;
    Ok(status_value(
        status.as_ref(),
        config.as_ref(),
        worker_lock_held,
    ))
}

pub fn start_relay_worker(
    repo_root: &Path,
    project_id: Option<&str>,
    endpoint_override: Option<&str>,
    secret_ref_override: Option<&str>,
) -> Result<Value, PlatformError> {
    let binding = resolve_project(repo_root, project_id)?;
    let paths = RelayPaths::for_binding(&binding)?;
    let config = read_config(&paths.config)?;
    let endpoint = endpoint_override
        .or_else(|| config.as_ref().map(|item| item.endpoint.as_str()))
        .ok_or_else(|| {
            PlatformError::Validation(
                "relay is not configured; run `relay configure --endpoint <https-url>` first"
                    .into(),
            )
        })?;
    let secret_ref = secret_ref_override
        .or_else(|| config.as_ref().map(|item| item.secret_ref.as_str()))
        .unwrap_or(DEFAULT_SECRET_REF);
    validate_endpoint(endpoint)?;
    let (authorized_binding, selection, policy) = authorize_transport(
        repo_root,
        Some(&binding.project_id),
        json!({
            "action": "start",
            "external_destination": endpoint,
            "data_class": "project"
        }),
    )?;
    SecretStore::new(&authorized_binding.repo_root)?
        .with_secret(secret_ref, &selection, |_| Ok(()))?;
    let worker_lock_held = worker_lock_is_held(&paths.worker_lock)?;
    if let Some(existing) = read_status(&paths.status)?
        && status_is_live(&existing, worker_lock_held)
    {
        return Ok(json!({
            "status": "already_running",
            "relay": status_value(Some(&existing), config.as_ref(), worker_lock_held),
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
            liveness_protocol: None,
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
            let worker_lock_held = worker_lock_is_held(&paths.worker_lock)?;
            return Ok(json!({
                "status": if current.state == "running" { "started" } else { "error" },
                "relay": status_value(Some(&current), config.as_ref(), worker_lock_held),
                "policy_decision_id": policy.decision_id
            }));
        }
    }
    let current = read_status(&paths.status)?;
    let worker_lock_held = worker_lock_is_held(&paths.worker_lock)?;
    Ok(json!({
        "status": "starting",
        "relay": status_value(current.as_ref(), config.as_ref(), worker_lock_held),
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
    let config = read_config(&paths.config)?;
    let Some(mut status) = read_status(&paths.status)? else {
        return Ok(json!({
            "status": "stopped",
            "already_stopped": true,
            "relay": status_value(None, config.as_ref(), false),
            "policy_decision_id": policy.decision_id
        }));
    };
    let worker_lock_held = worker_lock_is_held(&paths.worker_lock)?;
    if !status_is_live(&status, worker_lock_held) || status.state == "stopped" {
        status.state = "stopped".into();
        status.updated_at = Utc::now().to_rfc3339();
        status.message = Some("worker was not live when stop was requested".into());
        write_status(&paths.status, &status)?;
        remove_if_exists(&paths.stop)?;
        return Ok(json!({
            "status": "stopped",
            "already_stopped": true,
            "relay": status_value(Some(&status), config.as_ref(), false),
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
        let worker_lock_held = worker_lock_is_held(&paths.worker_lock)?;
        if current.as_ref().is_none_or(|item| item.state == "stopped") {
            remove_if_exists(&paths.stop)?;
            return Ok(json!({
                "status": "stopped",
                "relay": status_value(current.as_ref(), config.as_ref(), worker_lock_held),
                "policy_decision_id": policy.decision_id
            }));
        }
        if let Some(mut item) = current
            && item.liveness_protocol.as_deref() == Some(WORKER_LOCK_PROTOCOL)
            && !worker_lock_held
        {
            item.state = "stopped".into();
            item.updated_at = Utc::now().to_rfc3339();
            item.message = Some("worker process exited before final status update".into());
            write_status(&paths.status, &item)?;
            remove_if_exists(&paths.stop)?;
            return Ok(json!({
                "status": "stopped",
                "relay": status_value(Some(&item), config.as_ref(), false),
                "policy_decision_id": policy.decision_id
            }));
        }
    }
    let current = read_status(&paths.status)?;
    let worker_lock_held = worker_lock_is_held(&paths.worker_lock)?;
    Ok(json!({
        "status": "stopping",
        "relay": status_value(current.as_ref(), config.as_ref(), worker_lock_held),
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
    let _worker_lock = acquire_worker_lock(&paths.worker_lock)?;
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
        liveness_protocol: Some(WORKER_LOCK_PROTOCOL.into()),
    };
    write_status(&paths.status, &status)?;

    let store = SecretStore::new(&binding.repo_root)?;
    let mut completed = 0_u64;
    let mut backoff = Duration::from_secs(1);
    let execution = loop {
        if paths.stop.exists() {
            break Ok(());
        }
        let mut processed = None;
        let polled = store.with_secret(secret_ref, &selection, |secret| {
            let token = std::str::from_utf8(secret)
                .map_err(|_| PlatformError::SecretStore("relay token is not UTF-8".into()))?;
            validate_token(token)?;
            processed = poll_once(&binding, &paths.cache, &paths.http, endpoint, token)?;
            Ok(())
        });
        match polled {
            Ok(()) => {
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
                    break Ok(());
                }
            }
            Err(error) if error.retryable() || matches!(error, PlatformError::Io { .. }) => {
                status.updated_at = Utc::now().to_rfc3339();
                status.consecutive_errors = status.consecutive_errors.saturating_add(1);
                status.message = Some(format!("retryable transport error: {}", error.code()));
                write_status(&paths.status, &status)?;
                if once {
                    break Err(error);
                }
                sleep_interruptible(&paths.stop, backoff);
                backoff = (backoff * 2).min(Duration::from_secs(15));
            }
            Err(error) => break Err(error),
        }
    };
    let _ = store.with_secret(secret_ref, &selection, |secret| {
        let token = std::str::from_utf8(secret)
            .map_err(|_| PlatformError::SecretStore("relay token is not UTF-8".into()))?;
        validate_token(token)?;
        notify_offline(&binding, &paths.http, endpoint, token)
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

fn read_config(path: &Path) -> Result<Option<RelayConfig>, PlatformError> {
    let text = match fs::read_to_string(path) {
        Ok(value) => value,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(error) => return Err(io_error("cannot read relay config", error)),
    };
    let config: RelayConfig = serde_json::from_str(&text)
        .map_err(|error| PlatformError::Validation(format!("relay config is corrupt: {error}")))?;
    if config.contract_version != "relay-config-v1" {
        return Err(PlatformError::Validation(
            "unsupported relay config contract".into(),
        ));
    }
    validate_endpoint(&config.endpoint)?;
    if config.secret_ref.trim().is_empty() {
        return Err(PlatformError::Validation(
            "relay config secret reference is empty".into(),
        ));
    }
    Ok(Some(config))
}

fn write_config(path: &Path, config: &RelayConfig) -> Result<(), PlatformError> {
    let text = serde_json::to_string_pretty(config).map_err(|error| {
        PlatformError::Validation(format!("cannot serialize relay config: {error}"))
    })?;
    let mut file = AtomicWriteFile::open(path)
        .map_err(|error| io_error("cannot open atomic relay config", error))?;
    file.write_all(text.as_bytes())
        .map_err(|error| io_error("cannot write atomic relay config", error))?;
    file.commit()
        .map_err(|error| io_error("cannot commit atomic relay config", error))
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

fn status_value(
    status: Option<&WorkerStatus>,
    config: Option<&RelayConfig>,
    worker_lock_held: bool,
) -> Value {
    let Some(status) = status else {
        return json!({
            "contract_version": "relay-worker-status-v1",
            "state": "stopped",
            "enabled": false,
            "configured": config.is_some(),
            "endpoint": config.map(|item| item.endpoint.as_str())
        });
    };
    let heartbeat_stale = !heartbeat_is_fresh(status);
    let live = status_is_live(status, worker_lock_held);
    json!({
        "contract_version": status.contract_version,
        "state": if live { status.state.as_str() } else { "stopped" },
        "enabled": live && matches!(status.state.as_str(), "starting" | "running" | "stopping"),
        "configured": config.is_some(),
        "pid": status.pid,
        "project_id": status.project_id,
        "endpoint": status.endpoint,
        "started_at": status.started_at,
        "updated_at": status.updated_at,
        "last_poll_at": status.last_poll_at,
        "last_task_id": status.last_task_id,
        "consecutive_errors": status.consecutive_errors,
        "liveness_protocol": status.liveness_protocol,
        "worker_lock_held": status.liveness_protocol.as_deref() == Some(WORKER_LOCK_PROTOCOL) && worker_lock_held,
        "heartbeat_stale": heartbeat_stale,
        "message": if live {
            status.message.clone()
        } else {
            Some("worker liveness evidence is stale; relay is treated as stopped".into())
        }
    })
}

fn status_is_live(status: &WorkerStatus, worker_lock_held: bool) -> bool {
    if !matches!(status.state.as_str(), "starting" | "running" | "stopping") {
        return false;
    }
    if status.liveness_protocol.as_deref() == Some(WORKER_LOCK_PROTOCOL) {
        return worker_lock_held;
    }
    heartbeat_is_fresh(status)
}

fn heartbeat_is_fresh(status: &WorkerStatus) -> bool {
    chrono::DateTime::parse_from_rfc3339(&status.updated_at).is_ok_and(|value| {
        Utc::now()
            .timestamp_millis()
            .saturating_sub(value.timestamp_millis())
            <= STATUS_STALE_SECONDS * 1000
    })
}

fn acquire_worker_lock(path: &Path) -> Result<File, PlatformError> {
    let file = open_worker_lock(path)?;
    match file.try_lock() {
        Ok(()) => Ok(file),
        Err(TryLockError::WouldBlock) => Err(PlatformError::Validation(
            "relay worker lock is already held by another process".into(),
        )),
        Err(TryLockError::Error(error)) => {
            Err(io_error("cannot acquire relay worker lock", error))
        }
    }
}

fn worker_lock_is_held(path: &Path) -> Result<bool, PlatformError> {
    let file = open_worker_lock(path)?;
    match file.try_lock() {
        Ok(()) => {
            file.unlock()
                .map_err(|error| io_error("cannot release relay worker probe lock", error))?;
            Ok(false)
        }
        Err(TryLockError::WouldBlock) => Ok(true),
        Err(TryLockError::Error(error)) => {
            Err(io_error("cannot probe relay worker lock", error))
        }
    }
}

fn open_worker_lock(path: &Path) -> Result<File, PlatformError> {
    OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .open(path)
        .map_err(|error| io_error("cannot open relay worker lock", error))
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

#[cfg(test)]
mod tests {
    use super::*;

    fn status(updated_at: String, last_poll_at: Option<String>) -> WorkerStatus {
        WorkerStatus {
            contract_version: "relay-worker-status-v1".into(),
            state: "running".into(),
            pid: 123,
            project_id: "test".into(),
            endpoint: "https://example.invalid".into(),
            started_at: updated_at.clone(),
            updated_at,
            last_poll_at,
            last_task_id: None,
            consecutive_errors: 10,
            message: Some("retryable transport error".into()),
            liveness_protocol: None,
        }
    }

    #[test]
    fn legacy_retry_heartbeat_uses_updated_at_not_last_successful_poll() {
        let old_poll = (Utc::now() - chrono::Duration::minutes(10)).to_rfc3339();
        let current = status(Utc::now().to_rfc3339(), Some(old_poll));
        assert!(status_is_live(&current, false));
    }

    #[test]
    fn worker_lock_is_authoritative_for_new_worker_liveness() {
        let temporary = tempfile::tempdir().expect("temporary relay directory");
        let lock_path = temporary.path().join("worker.lock");
        let _lock = acquire_worker_lock(&lock_path).expect("acquire worker lock");
        assert!(worker_lock_is_held(&lock_path).expect("probe held worker lock"));

        let mut current = status(
            (Utc::now() - chrono::Duration::minutes(10)).to_rfc3339(),
            None,
        );
        current.liveness_protocol = Some(WORKER_LOCK_PROTOCOL.into());
        assert!(status_is_live(&current, true));
        assert!(!status_is_live(&current, false));
    }
}
