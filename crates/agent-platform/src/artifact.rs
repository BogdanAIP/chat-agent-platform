use std::fs::{self, OpenOptions};
use std::io::{ErrorKind, Read, Write};
use std::path::{Path, PathBuf};

use atomic_write_file::AtomicWriteFile;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};
use uuid::Uuid;

use crate::capability::CapabilitySelection;
use crate::contracts;
use crate::error::{PlatformError, io_error};

const DATA_CLASSES: [&str; 4] = ["public", "project", "private", "sensitive"];
const EXTERNALLY_STAGEABLE_CLASSES: [&str; 2] = ["public", "project"];
const HEX: &[u8; 16] = b"0123456789abcdef";
const PENDING_PREFIX: &str = ".pending-";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Artifact {
    pub artifact_id: String,
    #[serde(rename = "type")]
    pub artifact_type: String,
    pub path: String,
    pub mime: String,
    pub size_bytes: u64,
    pub sha256: String,
    pub created_by: String,
    pub created_at: String,
    pub status: String,
    pub data_class: String,
    pub metadata: Map<String, Value>,
    pub external_policy: ExternalPolicy,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExternalPolicy {
    pub staging_allowed: bool,
    pub allowed_executors: Vec<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct RecoveryReport {
    pub removed_pending: usize,
    pub removed_unregistered: usize,
    pub skipped_active_pending: usize,
}

struct PendingImportGuard {
    directory: PathBuf,
    lock_path: PathBuf,
    lock: Option<fs::File>,
}

impl PendingImportGuard {
    fn new(root: &Path, artifact_id: &str) -> Result<Self, PlatformError> {
        let directory = root.join(format!("{PENDING_PREFIX}{artifact_id}"));
        let lock_path = root.join(format!("{PENDING_PREFIX}{artifact_id}.lock"));
        let lock = OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .open(&lock_path)
            .map_err(|error| io_error("cannot open pending artifact lock", error))?;
        lock.lock()
            .map_err(|error| io_error("cannot lock pending artifact", error))?;
        fs::create_dir(&directory)
            .map_err(|error| io_error("cannot create pending artifact directory", error))?;
        Ok(Self {
            directory,
            lock_path,
            lock: Some(lock),
        })
    }
}

impl Drop for PendingImportGuard {
    fn drop(&mut self) {
        if let Some(lock) = self.lock.take() {
            let _ = lock.unlock();
            drop(lock);
        }
        let _ = fs::remove_dir_all(&self.directory);
        let _ = fs::remove_file(&self.lock_path);
    }
}

struct StagingGuard {
    directory: PathBuf,
}

impl Drop for StagingGuard {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.directory);
    }
}

pub struct ArtifactStore {
    root: PathBuf,
    manifest_path: PathBuf,
}

impl ArtifactStore {
    pub fn new(root: &Path) -> Result<Self, PlatformError> {
        fs::create_dir_all(root)
            .map_err(|error| io_error("cannot create artifact store", error))?;
        let root = fs::canonicalize(root)
            .map_err(|error| io_error("cannot resolve artifact store", error))?;
        let store = Self {
            manifest_path: root.join("manifest.json"),
            root,
        };
        store.recover_orphans()?;
        Ok(store)
    }

    pub fn import_file(
        &self,
        source: &Path,
        created_by: &str,
        data_class: &str,
    ) -> Result<Artifact, PlatformError> {
        if !DATA_CLASSES.contains(&data_class) {
            return Err(PlatformError::Validation(format!(
                "unknown data class: {data_class}"
            )));
        }
        let source = fs::canonicalize(source).map_err(|error| {
            io_error(format!("cannot resolve source {}", source.display()), error)
        })?;
        if !source.is_file() {
            return Err(PlatformError::Validation(format!(
                "artifact source is not a file: {}",
                source.display()
            )));
        }
        let filename = source
            .file_name()
            .ok_or_else(|| PlatformError::Validation("artifact source has no filename".into()))?;
        let artifact_id = format!("art_{}", Uuid::new_v4().simple());
        let pending = PendingImportGuard::new(&self.root, &artifact_id)?;
        let pending_destination = pending.directory.join(filename);
        fs::copy(&source, &pending_destination)
            .map_err(|error| io_error("cannot copy source into pending artifact", error))?;

        let artifact_dir = self.root.join(&artifact_id);
        let destination = artifact_dir.join(filename);
        if !destination.starts_with(&self.root) {
            return Err(PlatformError::Validation(
                "resolved artifact path escapes artifact store".into(),
            ));
        }
        let mime = mime_for(&pending_destination);
        let artifact = Artifact {
            artifact_id,
            artifact_type: mime
                .split_once('/')
                .map_or("binary", |parts| parts.0)
                .into(),
            path: destination.to_string_lossy().into_owned(),
            mime,
            size_bytes: pending_destination
                .metadata()
                .map_err(|error| io_error("cannot read artifact metadata", error))?
                .len(),
            sha256: sha256(&pending_destination)?,
            created_by: created_by.into(),
            created_at: Utc::now().to_rfc3339(),
            status: "ready".into(),
            data_class: data_class.into(),
            metadata: Map::new(),
            external_policy: ExternalPolicy {
                staging_allowed: false,
                allowed_executors: Vec::new(),
            },
        };
        contracts::validate(
            &serde_json::to_value(&artifact).map_err(serialization_error)?,
            "artifact-v1.schema.json",
        )?;

        let lock = self.open_manifest_lock()?;
        lock.lock()
            .map_err(|error| io_error("cannot lock artifact manifest", error))?;
        let publish_result = if artifact_dir.exists() {
            Err(PlatformError::Validation(format!(
                "artifact directory already exists: {}",
                artifact.artifact_id
            )))
        } else {
            fs::rename(&pending.directory, &artifact_dir)
                .map_err(|error| io_error("cannot publish artifact directory", error))
                .and_then(|()| self.upsert_locked(&artifact))
        };
        let unlock_result = lock
            .unlock()
            .map_err(|error| io_error("cannot unlock artifact manifest", error));
        match (publish_result, unlock_result) {
            (Err(error), _) | (Ok(()), Err(error)) => Err(error),
            (Ok(()), Ok(())) => Ok(artifact),
        }
    }

    pub fn update_metadata(
        &self,
        artifact: &mut Artifact,
        metadata: Map<String, Value>,
    ) -> Result<(), PlatformError> {
        if sha256(Path::new(&artifact.path))? != artifact.sha256 {
            return Err(PlatformError::Validation(format!(
                "artifact hash changed after import: {}",
                artifact.artifact_id
            )));
        }
        artifact.metadata.extend(metadata);
        contracts::validate(
            &serde_json::to_value(&artifact).map_err(serialization_error)?,
            "artifact-v1.schema.json",
        )?;
        self.upsert(artifact)
    }

    pub fn get(&self, artifact_id: &str) -> Result<Artifact, PlatformError> {
        validate_artifact_id(artifact_id)?;
        let lock = self.open_manifest_lock()?;
        lock.lock()
            .map_err(|error| io_error("cannot lock artifact manifest", error))?;
        let result = self.get_locked(artifact_id);
        let unlock_result = lock
            .unlock()
            .map_err(|error| io_error("cannot unlock artifact manifest", error));
        match (result, unlock_result) {
            (Err(error), _) | (Ok(_), Err(error)) => Err(error),
            (Ok(artifact), Ok(())) => Ok(artifact),
        }
    }

    pub fn allow_external_staging(
        &self,
        artifact_id: &str,
        consumers: &[CapabilitySelection],
    ) -> Result<Artifact, PlatformError> {
        if consumers.is_empty() {
            return Err(PlatformError::Validation(
                "external staging requires at least one selected consumer".into(),
            ));
        }
        validate_artifact_id(artifact_id)?;
        let lock = self.open_manifest_lock()?;
        lock.lock()
            .map_err(|error| io_error("cannot lock artifact manifest", error))?;
        let result = (|| {
            let mut artifact = self.get_locked(artifact_id)?;
            if !EXTERNALLY_STAGEABLE_CLASSES.contains(&artifact.data_class.as_str()) {
                return Err(PlatformError::PolicyDenied(format!(
                    "data class {} cannot be externally staged",
                    artifact.data_class
                )));
            }
            let mut allowed_executors = consumers
                .iter()
                .map(|selection| selection.executor.clone())
                .collect::<Vec<_>>();
            allowed_executors.sort_unstable();
            allowed_executors.dedup();
            artifact.external_policy = ExternalPolicy {
                staging_allowed: true,
                allowed_executors,
            };
            contracts::validate(
                &serde_json::to_value(&artifact).map_err(serialization_error)?,
                "artifact-v1.schema.json",
            )?;
            self.upsert_locked(&artifact)?;
            Ok(artifact)
        })();
        let unlock_result = lock
            .unlock()
            .map_err(|error| io_error("cannot unlock artifact manifest", error));
        match (result, unlock_result) {
            (Err(error), _) | (Ok(_), Err(error)) => Err(error),
            (Ok(artifact), Ok(())) => Ok(artifact),
        }
    }

    pub fn disable_external_staging(
        &self,
        artifact_id: &str,
    ) -> Result<Artifact, PlatformError> {
        validate_artifact_id(artifact_id)?;
        let lock = self.open_manifest_lock()?;
        lock.lock()
            .map_err(|error| io_error("cannot lock artifact manifest", error))?;
        let result = (|| {
            let mut artifact = self.get_locked(artifact_id)?;
            artifact.external_policy = ExternalPolicy {
                staging_allowed: false,
                allowed_executors: Vec::new(),
            };
            contracts::validate(
                &serde_json::to_value(&artifact).map_err(serialization_error)?,
                "artifact-v1.schema.json",
            )?;
            self.upsert_locked(&artifact)?;
            Ok(artifact)
        })();
        let unlock_result = lock
            .unlock()
            .map_err(|error| io_error("cannot unlock artifact manifest", error));
        match (result, unlock_result) {
            (Err(error), _) | (Ok(_), Err(error)) => Err(error),
            (Ok(artifact), Ok(())) => Ok(artifact),
        }
    }

    pub fn with_staged_copy<F>(
        &self,
        artifact_id: &str,
        consumer: &CapabilitySelection,
        staging_root: &Path,
        use_copy: F,
    ) -> Result<(), PlatformError>
    where
        F: FnOnce(&Path) -> Result<(), PlatformError>,
    {
        let artifact = self.get(artifact_id)?;
        if !EXTERNALLY_STAGEABLE_CLASSES.contains(&artifact.data_class.as_str()) {
            return Err(PlatformError::PolicyDenied(format!(
                "data class {} cannot be externally staged",
                artifact.data_class
            )));
        }
        if !artifact.external_policy.staging_allowed
            || !artifact
                .external_policy
                .allowed_executors
                .iter()
                .any(|executor| executor == &consumer.executor)
        {
            return Err(PlatformError::PolicyDenied(format!(
                "executor {} is not allowed to stage {artifact_id}",
                consumer.executor
            )));
        }

        fs::create_dir_all(staging_root)
            .map_err(|error| io_error("cannot create external staging root", error))?;
        let staging_root = fs::canonicalize(staging_root)
            .map_err(|error| io_error("cannot resolve external staging root", error))?;
        if staging_root.starts_with(&self.root) {
            return Err(PlatformError::Validation(
                "external staging root must be outside artifact store".into(),
            ));
        }
        let staging_directory = staging_root.join(format!(
            ".stage-{}-{}",
            artifact.artifact_id,
            Uuid::new_v4().simple()
        ));
        fs::create_dir(&staging_directory)
            .map_err(|error| io_error("cannot create staged artifact directory", error))?;
        let guard = StagingGuard {
            directory: staging_directory.clone(),
        };
        let filename = Path::new(&artifact.path)
            .file_name()
            .ok_or_else(|| PlatformError::Validation("artifact path has no filename".into()))?;
        let staged_path = staging_directory.join(filename);
        fs::copy(&artifact.path, &staged_path)
            .map_err(|error| io_error("cannot create staged artifact copy", error))?;
        if sha256(&staged_path)? != artifact.sha256 {
            return Err(PlatformError::Validation(format!(
                "staged artifact checksum mismatch: {artifact_id}"
            )));
        }
        let result = use_copy(&staged_path);
        drop(guard);
        result
    }

    pub fn recover_orphans(&self) -> Result<RecoveryReport, PlatformError> {
        let lock = self.open_manifest_lock()?;
        lock.lock()
            .map_err(|error| io_error("cannot lock artifact manifest", error))?;
        let result = self.recover_orphans_locked();
        let unlock_result = lock
            .unlock()
            .map_err(|error| io_error("cannot unlock artifact manifest", error));
        match (result, unlock_result) {
            (Err(error), _) | (Ok(_), Err(error)) => Err(error),
            (Ok(report), Ok(())) => Ok(report),
        }
    }

    fn recover_orphans_locked(&self) -> Result<RecoveryReport, PlatformError> {
        let manifest = self.read_manifest_locked()?;
        let mut report = RecoveryReport {
            removed_pending: 0,
            removed_unregistered: 0,
            skipped_active_pending: 0,
        };
        let entries = fs::read_dir(&self.root)
            .map_err(|error| io_error("cannot scan artifact store for recovery", error))?;
        for entry in entries {
            let entry = entry.map_err(|error| io_error("cannot read artifact entry", error))?;
            let path = entry.path();
            let Some(name) = entry.file_name().to_str().map(str::to_owned) else {
                continue;
            };
            if entry
                .file_type()
                .map_err(|error| io_error("cannot inspect artifact entry", error))?
                .is_dir()
            {
                if let Some(artifact_id) = name.strip_prefix(PENDING_PREFIX) {
                    let lock_path = self.root.join(format!("{PENDING_PREFIX}{artifact_id}.lock"));
                    match try_cleanup_pending(&path, &lock_path)? {
                        PendingCleanup::Removed => report.removed_pending += 1,
                        PendingCleanup::Active => report.skipped_active_pending += 1,
                    }
                } else if name.starts_with("art_")
                    && validate_artifact_id(&name).is_ok()
                    && !manifest.contains_key(&name)
                {
                    fs::remove_dir_all(&path).map_err(|error| {
                        io_error("cannot remove unregistered artifact directory", error)
                    })?;
                    report.removed_unregistered += 1;
                }
            } else if name.starts_with(PENDING_PREFIX) && name.ends_with(".lock") {
                let pending_name = name.trim_end_matches(".lock");
                if !self.root.join(pending_name).exists() {
                    cleanup_orphan_pending_lock(&path)?;
                }
            }
        }
        Ok(report)
    }

    fn upsert(&self, artifact: &Artifact) -> Result<(), PlatformError> {
        let lock = self.open_manifest_lock()?;
        lock.lock()
            .map_err(|error| io_error("cannot lock artifact manifest", error))?;
        let result = self.upsert_locked(artifact);
        let unlock_result = lock
            .unlock()
            .map_err(|error| io_error("cannot unlock artifact manifest", error));
        result.and(unlock_result)
    }

    fn upsert_locked(&self, artifact: &Artifact) -> Result<(), PlatformError> {
        let mut manifest = self.read_manifest_locked()?;
        manifest.insert(
            artifact.artifact_id.clone(),
            serde_json::to_value(artifact).map_err(serialization_error)?,
        );
        let text = serde_json::to_string_pretty(&manifest).map_err(serialization_error)?;
        let mut file = AtomicWriteFile::open(&self.manifest_path)
            .map_err(|error| io_error("cannot open atomic artifact manifest", error))?;
        file.write_all(text.as_bytes())
            .map_err(|error| io_error("cannot write atomic artifact manifest", error))?;
        file.commit()
            .map_err(|error| io_error("cannot commit atomic artifact manifest", error))
    }

    fn get_locked(&self, artifact_id: &str) -> Result<Artifact, PlatformError> {
        let manifest = self.read_manifest_locked()?;
        let value = manifest.get(artifact_id).ok_or_else(|| {
            PlatformError::Validation(format!("artifact is not registered: {artifact_id}"))
        })?;
        contracts::validate(value, "artifact-v1.schema.json")?;
        let artifact: Artifact = serde_json::from_value(value.clone()).map_err(|error| {
            PlatformError::Validation(format!("cannot decode artifact record: {error}"))
        })?;
        let artifact_path = fs::canonicalize(&artifact.path)
            .map_err(|error| io_error("cannot resolve registered artifact path", error))?;
        if !artifact_path.starts_with(&self.root) {
            return Err(PlatformError::Validation(format!(
                "registered artifact escapes artifact store: {artifact_id}"
            )));
        }
        if sha256(&artifact_path)? != artifact.sha256 {
            return Err(PlatformError::Validation(format!(
                "registered artifact hash mismatch: {artifact_id}"
            )));
        }
        Ok(artifact)
    }

    fn read_manifest_locked(&self) -> Result<Map<String, Value>, PlatformError> {
        if !self.manifest_path.exists() {
            return Ok(Map::new());
        }
        let text = fs::read_to_string(&self.manifest_path)
            .map_err(|error| io_error("cannot read artifact manifest", error))?;
        serde_json::from_str(&text).map_err(|error| {
            PlatformError::Validation(format!("artifact manifest is corrupt: {error}"))
        })
    }

    fn open_manifest_lock(&self) -> Result<fs::File, PlatformError> {
        OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .open(self.root.join(".manifest.lock"))
            .map_err(|error| io_error("cannot open artifact manifest lock", error))
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum PendingCleanup {
    Removed,
    Active,
}

fn try_cleanup_pending(directory: &Path, lock_path: &Path) -> Result<PendingCleanup, PlatformError> {
    let lock = OpenOptions::new()
        .create(true)
        .truncate(false)
        .read(true)
        .write(true)
        .open(lock_path)
        .map_err(|error| io_error("cannot open pending artifact recovery lock", error))?;
    match lock.try_lock() {
        Ok(()) => {
            fs::remove_dir_all(directory)
                .map_err(|error| io_error("cannot remove abandoned pending artifact", error))?;
            lock.unlock()
                .map_err(|error| io_error("cannot unlock pending artifact recovery", error))?;
            drop(lock);
            match fs::remove_file(lock_path) {
                Ok(()) => {}
                Err(error) if error.kind() == ErrorKind::NotFound => {}
                Err(error) => {
                    return Err(io_error("cannot remove pending artifact lock", error));
                }
            }
            Ok(PendingCleanup::Removed)
        }
        Err(error) if error.kind() == ErrorKind::WouldBlock => Ok(PendingCleanup::Active),
        Err(error) => Err(io_error("cannot probe pending artifact lock", error)),
    }
}

fn cleanup_orphan_pending_lock(lock_path: &Path) -> Result<(), PlatformError> {
    let lock = OpenOptions::new()
        .create(false)
        .read(true)
        .write(true)
        .open(lock_path)
        .map_err(|error| io_error("cannot open orphan pending lock", error))?;
    match lock.try_lock() {
        Ok(()) => {
            lock.unlock()
                .map_err(|error| io_error("cannot unlock orphan pending lock", error))?;
            drop(lock);
            fs::remove_file(lock_path)
                .map_err(|error| io_error("cannot remove orphan pending lock", error))
        }
        Err(error) if error.kind() == ErrorKind::WouldBlock => Ok(()),
        Err(error) => Err(io_error("cannot probe orphan pending lock", error)),
    }
}

fn validate_artifact_id(artifact_id: &str) -> Result<(), PlatformError> {
    if !artifact_id.starts_with("art_")
        || artifact_id.len() == 4
        || !artifact_id
            .chars()
            .skip(4)
            .all(|character| character.is_ascii_hexdigit())
    {
        return Err(PlatformError::Validation(format!(
            "invalid artifact id: {artifact_id}"
        )));
    }
    Ok(())
}

fn sha256(path: &Path) -> Result<String, PlatformError> {
    let mut file = fs::File::open(path).map_err(|error| io_error("cannot hash artifact", error))?;
    let mut digest = Sha256::new();
    let mut buffer = vec![0_u8; 1024 * 1024];
    loop {
        let count = file
            .read(&mut buffer)
            .map_err(|error| io_error("cannot read artifact while hashing", error))?;
        if count == 0 {
            break;
        }
        digest.update(&buffer[..count]);
    }
    let bytes = digest.finalize();
    let mut encoded = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        encoded.push(char::from(HEX[usize::from(byte >> 4)]));
        encoded.push(char::from(HEX[usize::from(byte & 0x0f)]));
    }
    Ok(encoded)
}

fn mime_for(path: &Path) -> String {
    match path
        .extension()
        .and_then(|value| value.to_str())
        .map(str::to_ascii_lowercase)
        .as_deref()
    {
        Some("wav") => "audio/wav",
        Some("mp3") => "audio/mpeg",
        Some("flac") => "audio/flac",
        Some("m4a" | "mp4") => "audio/mp4",
        _ => "application/octet-stream",
    }
    .into()
}

fn serialization_error(error: serde_json::Error) -> PlatformError {
    PlatformError::Validation(format!("cannot serialize artifact contract: {error}"))
}
