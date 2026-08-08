use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

use atomic_write_file::AtomicWriteFile;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use uuid::Uuid;

use crate::binding::ProjectBinding;
use crate::contracts;
use crate::error::{PlatformError, io_error};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobCheckpoint {
    pub name: String,
    pub data: Map<String, Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobRecord {
    pub contract_version: String,
    pub job_id: String,
    pub capability: String,
    pub status: String,
    pub created_at: String,
    pub updated_at: String,
    pub result: Option<Map<String, Value>>,
    pub error: Option<Map<String, Value>>,
    pub idempotency_key: Option<String>,
    pub attempt: u32,
    pub checkpoint: Option<JobCheckpoint>,
}

pub struct JobStore {
    root: PathBuf,
}

impl JobStore {
    pub fn for_binding(binding: &ProjectBinding) -> Result<Self, PlatformError> {
        let root = binding
            .local_root
            .join("runtime")
            .join("jobs")
            .join(&binding.project_id);
        let store = Self::new(&root)?;
        if !store.root.starts_with(&binding.local_root) {
            return Err(PlatformError::Validation(
                "job store escapes the bound local root".into(),
            ));
        }
        Ok(store)
    }

    pub fn new(root: &Path) -> Result<Self, PlatformError> {
        fs::create_dir_all(root).map_err(|error| io_error("cannot create job store", error))?;
        let root =
            fs::canonicalize(root).map_err(|error| io_error("cannot resolve job store", error))?;
        Ok(Self { root })
    }

    pub fn begin(
        &self,
        capability: &str,
        idempotency_key: &str,
    ) -> Result<JobRecord, PlatformError> {
        validate_nonempty("capability", capability)?;
        validate_nonempty("idempotency key", idempotency_key)?;
        self.with_lock(|| {
            if let Some(existing) = self.find_by_idempotency_locked(idempotency_key)? {
                if existing.capability != capability {
                    return Err(PlatformError::Validation(format!(
                        "idempotency key is already bound to capability {}",
                        existing.capability
                    )));
                }
                return Ok(existing);
            }

            let now = Utc::now().to_rfc3339();
            let job = JobRecord {
                contract_version: "job-v1".into(),
                job_id: format!("job_{}", Uuid::new_v4().simple()),
                capability: capability.into(),
                status: "queued".into(),
                created_at: now.clone(),
                updated_at: now,
                result: None,
                error: None,
                idempotency_key: Some(idempotency_key.into()),
                attempt: 1,
                checkpoint: None,
            };
            self.write_locked(&job)?;
            Ok(job)
        })
    }

    pub fn get(&self, job_id: &str) -> Result<JobRecord, PlatformError> {
        validate_job_id(job_id)?;
        self.with_lock(|| self.read_locked(job_id))
    }

    pub fn resume(&self, job_id: &str) -> Result<JobRecord, PlatformError> {
        validate_job_id(job_id)?;
        self.with_lock(|| {
            let mut job = self.read_locked(job_id)?;
            match job.status.as_str() {
                "queued" => {
                    job.status = "running".into();
                    job.updated_at = Utc::now().to_rfc3339();
                    self.write_locked(&job)?;
                    Ok(job)
                }
                "running" => Ok(job),
                "failed" if is_retryable(&job) => {
                    job.status = "running".into();
                    job.attempt = job.attempt.checked_add(1).ok_or_else(|| {
                        PlatformError::Validation("job attempt counter overflow".into())
                    })?;
                    job.updated_at = Utc::now().to_rfc3339();
                    job.error = None;
                    job.result = None;
                    self.write_locked(&job)?;
                    Ok(job)
                }
                "failed" => Err(PlatformError::Validation(format!(
                    "job {job_id} failed with a non-retryable error"
                ))),
                "succeeded" | "cancelled" => Err(PlatformError::Validation(format!(
                    "terminal job cannot be resumed: {job_id} ({})",
                    job.status
                ))),
                other => Err(PlatformError::Validation(format!(
                    "unknown job status: {other}"
                ))),
            }
        })
    }

    pub fn checkpoint(
        &self,
        job_id: &str,
        name: &str,
        data: Map<String, Value>,
    ) -> Result<JobRecord, PlatformError> {
        validate_job_id(job_id)?;
        validate_nonempty("checkpoint name", name)?;
        self.with_lock(|| {
            let mut job = self.read_locked(job_id)?;
            require_status(&job, &["running"], "checkpoint")?;
            job.checkpoint = Some(JobCheckpoint {
                name: name.into(),
                data,
            });
            job.updated_at = Utc::now().to_rfc3339();
            self.write_locked(&job)?;
            Ok(job)
        })
    }

    pub fn succeed(
        &self,
        job_id: &str,
        result: Map<String, Value>,
    ) -> Result<JobRecord, PlatformError> {
        validate_job_id(job_id)?;
        self.with_lock(|| {
            let mut job = self.read_locked(job_id)?;
            require_status(&job, &["running"], "succeed")?;
            job.status = "succeeded".into();
            job.result = Some(result);
            job.error = None;
            job.updated_at = Utc::now().to_rfc3339();
            self.write_locked(&job)?;
            Ok(job)
        })
    }

    pub fn fail(
        &self,
        job_id: &str,
        error: Map<String, Value>,
    ) -> Result<JobRecord, PlatformError> {
        validate_job_id(job_id)?;
        self.with_lock(|| {
            let mut job = self.read_locked(job_id)?;
            require_status(&job, &["running"], "fail")?;
            job.status = "failed".into();
            job.result = None;
            job.error = Some(error);
            job.updated_at = Utc::now().to_rfc3339();
            self.write_locked(&job)?;
            Ok(job)
        })
    }

    pub fn cancel(&self, job_id: &str) -> Result<JobRecord, PlatformError> {
        validate_job_id(job_id)?;
        self.with_lock(|| {
            let mut job = self.read_locked(job_id)?;
            require_status(&job, &["queued", "running"], "cancel")?;
            job.status = "cancelled".into();
            job.result = None;
            job.error = None;
            job.updated_at = Utc::now().to_rfc3339();
            self.write_locked(&job)?;
            Ok(job)
        })
    }

    fn find_by_idempotency_locked(
        &self,
        idempotency_key: &str,
    ) -> Result<Option<JobRecord>, PlatformError> {
        for entry in
            fs::read_dir(&self.root).map_err(|error| io_error("cannot scan job store", error))?
        {
            let entry = entry.map_err(|error| io_error("cannot read job store entry", error))?;
            if !entry
                .file_type()
                .map_err(|error| io_error("cannot inspect job store entry", error))?
                .is_file()
            {
                continue;
            }
            let path = entry.path();
            if path.extension().and_then(|value| value.to_str()) != Some("json") {
                continue;
            }
            let job = Self::read_path_locked(&path)?;
            if job.idempotency_key.as_deref() == Some(idempotency_key) {
                return Ok(Some(job));
            }
        }
        Ok(None)
    }

    fn read_locked(&self, job_id: &str) -> Result<JobRecord, PlatformError> {
        let path = self.root.join(format!("{job_id}.json"));
        if !path.is_file() {
            return Err(PlatformError::Validation(format!(
                "job is not registered: {job_id}"
            )));
        }
        let job = Self::read_path_locked(&path)?;
        if job.job_id != job_id {
            return Err(PlatformError::Validation(format!(
                "job identity mismatch: expected {job_id}, got {}",
                job.job_id
            )));
        }
        Ok(job)
    }

    fn read_path_locked(path: &Path) -> Result<JobRecord, PlatformError> {
        let text = fs::read_to_string(path)
            .map_err(|error| io_error("cannot read persisted job", error))?;
        let value: Value = serde_json::from_str(&text).map_err(|error| {
            PlatformError::Validation(format!(
                "persisted job state is corrupt at {}: {error}",
                path.display()
            ))
        })?;
        contracts::validate(&value, "job-v1.schema.json")?;
        let job: JobRecord = serde_json::from_value(value).map_err(|error| {
            PlatformError::Validation(format!("cannot decode persisted job: {error}"))
        })?;
        validate_job_id(&job.job_id)?;
        let expected_name = format!("{}.json", job.job_id);
        if path.file_name().and_then(|value| value.to_str()) != Some(expected_name.as_str()) {
            return Err(PlatformError::Validation(format!(
                "persisted job filename does not match job id: {}",
                path.display()
            )));
        }
        Ok(job)
    }

    fn write_locked(&self, job: &JobRecord) -> Result<(), PlatformError> {
        let value = serde_json::to_value(job).map_err(serialization_error)?;
        contracts::validate(&value, "job-v1.schema.json")?;
        validate_job_id(&job.job_id)?;
        let path = self.root.join(format!("{}.json", job.job_id));
        if !path.starts_with(&self.root) {
            return Err(PlatformError::Validation(
                "job path escapes the job store".into(),
            ));
        }
        let text = serde_json::to_string_pretty(job).map_err(serialization_error)?;
        let mut file = AtomicWriteFile::open(&path)
            .map_err(|error| io_error("cannot open atomic job state", error))?;
        file.write_all(text.as_bytes())
            .map_err(|error| io_error("cannot write atomic job state", error))?;
        file.commit()
            .map_err(|error| io_error("cannot commit atomic job state", error))
    }

    fn with_lock<T, F>(&self, operation: F) -> Result<T, PlatformError>
    where
        F: FnOnce() -> Result<T, PlatformError>,
    {
        let lock = OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .open(self.root.join(".jobs.lock"))
            .map_err(|error| io_error("cannot open job store lock", error))?;
        lock.lock()
            .map_err(|error| io_error("cannot lock job store", error))?;
        let result = operation();
        let unlock_result = lock
            .unlock()
            .map_err(|error| io_error("cannot unlock job store", error));
        match (result, unlock_result) {
            (Err(error), _) | (Ok(_), Err(error)) => Err(error),
            (Ok(value), Ok(())) => Ok(value),
        }
    }
}

fn is_retryable(job: &JobRecord) -> bool {
    job.error
        .as_ref()
        .and_then(|error| error.get("retryable"))
        .and_then(Value::as_bool)
        == Some(true)
}

fn require_status(job: &JobRecord, allowed: &[&str], operation: &str) -> Result<(), PlatformError> {
    if allowed.contains(&job.status.as_str()) {
        return Ok(());
    }
    Err(PlatformError::Validation(format!(
        "cannot {operation} job {} from status {}",
        job.job_id, job.status
    )))
}

fn validate_job_id(job_id: &str) -> Result<(), PlatformError> {
    if !job_id.starts_with("job_")
        || job_id.len() == 4
        || !job_id
            .chars()
            .skip(4)
            .all(|character| character.is_ascii_hexdigit())
    {
        return Err(PlatformError::Validation(format!(
            "invalid job id: {job_id}"
        )));
    }
    Ok(())
}

fn validate_nonempty(label: &str, value: &str) -> Result<(), PlatformError> {
    if value.trim().is_empty() {
        return Err(PlatformError::Validation(format!(
            "{label} must not be empty"
        )));
    }
    Ok(())
}

fn serialization_error(error: serde_json::Error) -> PlatformError {
    PlatformError::Validation(format!("cannot serialize job contract: {error}"))
}
