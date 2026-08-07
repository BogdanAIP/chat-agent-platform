use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};

use atomic_write_file::AtomicWriteFile;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};
use uuid::Uuid;

use crate::contracts;
use crate::error::{PlatformError, io_error};

const DATA_CLASSES: [&str; 4] = ["public", "project", "private", "sensitive"];
const HEX: &[u8; 16] = b"0123456789abcdef";

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
        Ok(Self {
            manifest_path: root.join("manifest.json"),
            root,
        })
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
        let artifact_dir = self.root.join(&artifact_id);
        fs::create_dir(&artifact_dir)
            .map_err(|error| io_error("cannot create artifact directory", error))?;
        let destination = artifact_dir.join(filename);
        if !destination.starts_with(&self.root) {
            return Err(PlatformError::Validation(
                "resolved artifact path escapes artifact store".into(),
            ));
        }
        fs::copy(&source, &destination)
            .map_err(|error| io_error("cannot copy source into artifact store", error))?;
        let mime = mime_for(&destination);
        let artifact = Artifact {
            artifact_id,
            artifact_type: mime
                .split_once('/')
                .map_or("binary", |parts| parts.0)
                .into(),
            path: destination.to_string_lossy().into_owned(),
            mime,
            size_bytes: destination
                .metadata()
                .map_err(|error| io_error("cannot read artifact metadata", error))?
                .len(),
            sha256: sha256(&destination)?,
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
        self.upsert(&artifact)?;
        Ok(artifact)
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
        if !artifact_id.starts_with("art_")
            || !artifact_id
                .chars()
                .skip(4)
                .all(|character| character.is_ascii_hexdigit())
        {
            return Err(PlatformError::Validation(format!(
                "invalid artifact id: {artifact_id}"
            )));
        }
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
        let mut manifest = if self.manifest_path.exists() {
            let text = fs::read_to_string(&self.manifest_path)
                .map_err(|error| io_error("cannot read artifact manifest", error))?;
            serde_json::from_str::<Map<String, Value>>(&text).map_err(|error| {
                PlatformError::Validation(format!("artifact manifest is corrupt: {error}"))
            })?
        } else {
            Map::new()
        };
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
        let text = fs::read_to_string(&self.manifest_path)
            .map_err(|error| io_error("cannot read artifact manifest", error))?;
        let manifest: Map<String, Value> = serde_json::from_str(&text).map_err(|error| {
            PlatformError::Validation(format!("artifact manifest is corrupt: {error}"))
        })?;
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
