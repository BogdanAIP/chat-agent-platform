use std::fmt::Write as _;
use std::fs::{self, File};
use std::io::Read;
use std::path::{Path, PathBuf};

use sha2::{Digest, Sha256};
use uuid::Uuid;

use crate::artifact::{Artifact, ArtifactStore};
use crate::error::{PlatformError, io_error};

struct CaptureGuard {
    root: PathBuf,
}

impl Drop for CaptureGuard {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

pub(crate) fn capture_expected_file(
    store: &ArtifactStore,
    source: &Path,
    expected_sha256: &str,
    created_by: &str,
    data_class: &str,
) -> Result<Artifact, PlatformError> {
    validate_sha256(expected_sha256)?;
    let source = fs::canonicalize(source).map_err(|error| {
        io_error(
            format!("cannot resolve workflow input {}", source.display()),
            error,
        )
    })?;
    if !source.is_file() {
        return Err(PlatformError::Validation(format!(
            "workflow input is not a file: {}",
            source.display()
        )));
    }
    let filename = source
        .file_name()
        .ok_or_else(|| PlatformError::Validation("workflow input has no filename".into()))?;
    let root = std::env::temp_dir().join(format!(
        "agent-platform-input-capture-{}",
        Uuid::new_v4().simple()
    ));
    fs::create_dir(&root)
        .map_err(|error| io_error("cannot create workflow input capture directory", error))?;
    let guard = CaptureGuard { root: root.clone() };
    let snapshot = root.join(filename);
    fs::copy(&source, &snapshot)
        .map_err(|error| io_error("cannot capture immutable workflow input", error))?;
    let captured_sha256 = sha256_file(&snapshot)?;
    if captured_sha256 != expected_sha256 {
        return Err(PlatformError::Validation(format!(
            "workflow input changed while it was being captured: expected SHA-256 {expected_sha256}, captured {captured_sha256}"
        )));
    }
    let artifact = store.import_file(&snapshot, created_by, data_class)?;
    if artifact.sha256 != expected_sha256 {
        return Err(PlatformError::Validation(format!(
            "artifact snapshot SHA-256 does not match workflow identity: expected {expected_sha256}, registered {}",
            artifact.sha256
        )));
    }
    drop(guard);
    Ok(artifact)
}

pub(crate) fn verify_artifact_identity(
    artifact: &Artifact,
    expected_sha256: &str,
    label: &str,
) -> Result<(), PlatformError> {
    validate_sha256(expected_sha256)?;
    if artifact.sha256 == expected_sha256 {
        return Ok(());
    }
    Err(PlatformError::Validation(format!(
        "{label} artifact SHA-256 does not match workflow identity: expected {expected_sha256}, registered {}",
        artifact.sha256
    )))
}

fn validate_sha256(value: &str) -> Result<(), PlatformError> {
    if value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        Ok(())
    } else {
        Err(PlatformError::Validation(
            "expected workflow SHA-256 must contain exactly 64 hexadecimal characters".into(),
        ))
    }
}

fn sha256_file(path: &Path) -> Result<String, PlatformError> {
    let mut file = File::open(path)
        .map_err(|error| io_error("cannot open captured workflow input", error))?;
    let mut hasher = Sha256::new();
    let mut buffer = vec![0_u8; 64 * 1024];
    loop {
        let read = file
            .read(&mut buffer)
            .map_err(|error| io_error("cannot hash captured workflow input", error))?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    let digest = hasher.finalize();
    let mut hex = String::with_capacity(digest.len() * 2);
    for byte in digest {
        write!(&mut hex, "{byte:02x}").expect("writing SHA-256 to String cannot fail");
    }
    Ok(hex)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn mismatched_expected_hash_is_rejected_before_artifact_publish() {
        let temporary = tempdir().expect("temporary root");
        let source = temporary.path().join("source.wav");
        fs::write(&source, b"immutable-source").expect("source write");
        let artifact_root = temporary.path().join("artifacts");
        let store = ArtifactStore::new(&artifact_root).expect("artifact store");

        let error = capture_expected_file(
            &store,
            &source,
            &"0".repeat(64),
            "test.capture",
            "project",
        )
        .expect_err("wrong expected hash must fail closed");
        assert!(error.to_string().contains("changed while it was being captured"));
        assert!(
            !artifact_root.join("manifest.json").exists(),
            "mismatched capture must not publish an artifact"
        );
        let published = fs::read_dir(&artifact_root)
            .expect("artifact root")
            .filter_map(Result::ok)
            .filter(|entry| {
                entry.file_type().is_ok_and(|kind| kind.is_dir())
                    && entry
                        .file_name()
                        .to_str()
                        .is_some_and(|name| name.starts_with("art_"))
            })
            .count();
        assert_eq!(published, 0);
    }
}
