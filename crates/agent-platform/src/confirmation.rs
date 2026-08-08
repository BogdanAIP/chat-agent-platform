use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

use atomic_write_file::AtomicWriteFile;
use chrono::{DateTime, Duration, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use uuid::Uuid;

use crate::binding::ProjectBinding;
use crate::contracts;
use crate::error::{PlatformError, io_error};
use crate::policy::PolicyDecision;

const DEFAULT_TTL_SECONDS: i64 = 600;
const MIN_TTL_SECONDS: i64 = 30;
const MAX_TTL_SECONDS: i64 = 900;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfirmationRecord {
    pub contract_version: String,
    pub confirmation_id: String,
    pub project_id: String,
    pub decision_id: String,
    pub capability: String,
    pub confirmation_binding: String,
    pub effective_risk: String,
    pub status: String,
    pub created_at: String,
    pub expires_at: String,
    pub consumed_at: Option<String>,
}

pub struct ConfirmationStore {
    root: PathBuf,
    project_id: String,
}

impl ConfirmationStore {
    pub fn for_binding(binding: &ProjectBinding) -> Result<Self, PlatformError> {
        let root = binding
            .local_root
            .join("runtime")
            .join("confirmations")
            .join(&binding.project_id);
        Self::new(&root, &binding.project_id)
    }

    pub fn new(root: &Path, project_id: &str) -> Result<Self, PlatformError> {
        validate_nonempty("project id", project_id)?;
        fs::create_dir_all(root)
            .map_err(|error| io_error("cannot create confirmation store", error))?;
        let root = fs::canonicalize(root)
            .map_err(|error| io_error("cannot resolve confirmation store", error))?;
        Ok(Self {
            root,
            project_id: project_id.to_owned(),
        })
    }

    pub fn prepare(&self, decision: &PolicyDecision) -> Result<ConfirmationRecord, PlatformError> {
        self.prepare_with_ttl(decision, DEFAULT_TTL_SECONDS)
    }

    pub fn prepare_with_ttl(
        &self,
        decision: &PolicyDecision,
        ttl_seconds: i64,
    ) -> Result<ConfirmationRecord, PlatformError> {
        if decision.decision != "guarded" {
            return Err(PlatformError::Validation(
                "only guarded policy decisions may create confirmations".into(),
            ));
        }
        if !(MIN_TTL_SECONDS..=MAX_TTL_SECONDS).contains(&ttl_seconds) {
            return Err(PlatformError::Validation(format!(
                "confirmation TTL must be between {MIN_TTL_SECONDS} and {MAX_TTL_SECONDS} seconds"
            )));
        }
        let binding = decision.confirmation_binding.as_deref().ok_or_else(|| {
            PlatformError::Validation("guarded policy decision has no confirmation binding".into())
        })?;
        validate_binding(binding)?;
        validate_nonempty("capability", &decision.capability)?;
        validate_nonempty("effective risk", &decision.effective_risk)?;

        self.with_lock(|| {
            let now = Utc::now();
            let record = ConfirmationRecord {
                contract_version: "confirmation-v1".into(),
                confirmation_id: format!("cfm_{}", Uuid::new_v4().simple()),
                project_id: self.project_id.clone(),
                decision_id: decision.decision_id.clone(),
                capability: decision.capability.clone(),
                confirmation_binding: binding.to_owned(),
                effective_risk: decision.effective_risk.clone(),
                status: "prepared".into(),
                created_at: now.to_rfc3339(),
                expires_at: (now + Duration::seconds(ttl_seconds)).to_rfc3339(),
                consumed_at: None,
            };
            self.write_locked(&record)?;
            Ok(record)
        })
    }

    pub fn get(&self, confirmation_id: &str) -> Result<ConfirmationRecord, PlatformError> {
        validate_confirmation_id(confirmation_id)?;
        self.with_lock(|| self.read_locked(confirmation_id))
    }

    pub fn consume_for_decision(
        &self,
        confirmation_id: &str,
        decision: &PolicyDecision,
    ) -> Result<ConfirmationRecord, PlatformError> {
        validate_confirmation_id(confirmation_id)?;
        if decision.decision != "guarded" {
            return Err(PlatformError::Validation(
                "confirmation may only authorize a fresh guarded policy decision".into(),
            ));
        }
        let expected_binding = decision.confirmation_binding.as_deref().ok_or_else(|| {
            PlatformError::Validation("fresh guarded decision has no confirmation binding".into())
        })?;
        validate_binding(expected_binding)?;

        self.with_lock(|| {
            let mut record = self.read_locked(confirmation_id)?;
            if record.status != "prepared" {
                return Err(PlatformError::PolicyDenied(format!(
                    "confirmation {confirmation_id} has already been consumed"
                )));
            }
            if record.project_id != self.project_id {
                return Err(PlatformError::PolicyDenied(
                    "confirmation belongs to another project".into(),
                ));
            }
            if record.capability != decision.capability {
                return Err(PlatformError::PolicyDenied(
                    "confirmation capability does not match the requested action".into(),
                ));
            }
            if record.effective_risk != decision.effective_risk {
                return Err(PlatformError::PolicyDenied(
                    "confirmation risk does not match the fresh policy decision".into(),
                ));
            }
            if record.confirmation_binding != expected_binding {
                return Err(PlatformError::PolicyDenied(
                    "confirmation binding does not match the requested action".into(),
                ));
            }
            let expires_at = parse_timestamp("expires_at", &record.expires_at)?;
            let now = Utc::now();
            if now > expires_at {
                return Err(PlatformError::PolicyDenied(format!(
                    "confirmation {confirmation_id} has expired"
                )));
            }
            record.status = "consumed".into();
            record.consumed_at = Some(now.to_rfc3339());
            self.write_locked(&record)?;
            Ok(record)
        })
    }

    fn read_locked(&self, confirmation_id: &str) -> Result<ConfirmationRecord, PlatformError> {
        let path = self.root.join(format!("{confirmation_id}.json"));
        if !path.starts_with(&self.root) || !path.is_file() {
            return Err(PlatformError::Validation(format!(
                "confirmation is not registered: {confirmation_id}"
            )));
        }
        let text = fs::read_to_string(&path)
            .map_err(|error| io_error("cannot read confirmation record", error))?;
        let value: Value = serde_json::from_str(&text).map_err(|error| {
            PlatformError::Validation(format!(
                "persisted confirmation state is corrupt at {}: {error}",
                path.display()
            ))
        })?;
        contracts::validate(&value, "confirmation-v1.schema.json")?;
        let record: ConfirmationRecord = serde_json::from_value(value).map_err(|error| {
            PlatformError::Validation(format!("cannot decode confirmation record: {error}"))
        })?;
        if record.confirmation_id != confirmation_id {
            return Err(PlatformError::Validation(
                "confirmation identity does not match persisted filename".into(),
            ));
        }
        if record.project_id != self.project_id {
            return Err(PlatformError::PolicyDenied(
                "confirmation record belongs to another project".into(),
            ));
        }
        Ok(record)
    }

    fn write_locked(&self, record: &ConfirmationRecord) -> Result<(), PlatformError> {
        validate_confirmation_id(&record.confirmation_id)?;
        let value = serde_json::to_value(record).map_err(serialization_error)?;
        contracts::validate(&value, "confirmation-v1.schema.json")?;
        let path = self.root.join(format!("{}.json", record.confirmation_id));
        if !path.starts_with(&self.root) {
            return Err(PlatformError::Validation(
                "confirmation path escapes the confirmation store".into(),
            ));
        }
        let text = serde_json::to_string_pretty(record).map_err(serialization_error)?;
        let mut file = AtomicWriteFile::open(&path)
            .map_err(|error| io_error("cannot open atomic confirmation state", error))?;
        file.write_all(text.as_bytes())
            .map_err(|error| io_error("cannot write atomic confirmation state", error))?;
        file.commit()
            .map_err(|error| io_error("cannot commit atomic confirmation state", error))
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
            .open(self.root.join(".confirmations.lock"))
            .map_err(|error| io_error("cannot open confirmation store lock", error))?;
        lock.lock()
            .map_err(|error| io_error("cannot lock confirmation store", error))?;
        let result = operation();
        let unlock_result = lock
            .unlock()
            .map_err(|error| io_error("cannot unlock confirmation store", error));
        match (result, unlock_result) {
            (Err(error), _) | (Ok(_), Err(error)) => Err(error),
            (Ok(value), Ok(())) => Ok(value),
        }
    }
}

fn validate_confirmation_id(value: &str) -> Result<(), PlatformError> {
    if value.len() == 36
        && value.starts_with("cfm_")
        && value
            .bytes()
            .skip(4)
            .all(|byte| byte.is_ascii_hexdigit())
    {
        Ok(())
    } else {
        Err(PlatformError::Validation(format!(
            "invalid confirmation id: {value}"
        )))
    }
}

fn validate_binding(value: &str) -> Result<(), PlatformError> {
    if value.len() == 72
        && value.starts_with("confirm_")
        && value
            .bytes()
            .skip(8)
            .all(|byte| byte.is_ascii_hexdigit())
    {
        Ok(())
    } else {
        Err(PlatformError::Validation(
            "invalid confirmation binding".into(),
        ))
    }
}

fn validate_nonempty(label: &str, value: &str) -> Result<(), PlatformError> {
    if value.trim().is_empty() {
        Err(PlatformError::Validation(format!(
            "{label} must not be empty"
        )))
    } else {
        Ok(())
    }
}

fn parse_timestamp(label: &str, value: &str) -> Result<DateTime<Utc>, PlatformError> {
    DateTime::parse_from_rfc3339(value)
        .map(|value| value.with_timezone(&Utc))
        .map_err(|error| PlatformError::Validation(format!("invalid {label}: {error}")))
}

fn serialization_error(error: serde_json::Error) -> PlatformError {
    PlatformError::Validation(format!("cannot serialize confirmation contract: {error}"))
}
