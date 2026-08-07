use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};
use zeroize::Zeroize;

use crate::capability::CapabilitySelection;
use crate::contracts;
use crate::error::PlatformError;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SecretMetadata {
    contract_version: String,
    secret_ref: String,
    allowed_consumers: Vec<String>,
    credential_target: String,
}

struct SecretBuffer {
    bytes: Vec<u8>,
}

impl SecretBuffer {
    fn new(bytes: Vec<u8>) -> Self {
        Self { bytes }
    }

    fn as_bytes(&self) -> &[u8] {
        &self.bytes
    }
}

impl Drop for SecretBuffer {
    fn drop(&mut self) {
        self.bytes.zeroize();
    }
}

pub struct SecretStore {
    metadata_root: PathBuf,
}

impl SecretStore {
    pub fn new(repo_root: &Path) -> Result<Self, PlatformError> {
        let metadata_root = repo_root.join("runtime/secrets");
        fs::create_dir_all(&metadata_root)
            .map_err(|error| crate::error::io_error("cannot create secret metadata root", error))?;
        Ok(Self { metadata_root })
    }

    pub fn put(
        &self,
        secret_ref: &str,
        allowed_consumers: &[String],
        value: &[u8],
    ) -> Result<(), PlatformError> {
        validate_reference(secret_ref, allowed_consumers)?;
        if value.is_empty() {
            return Err(PlatformError::Validation(
                "secret value must not be empty".into(),
            ));
        }

        let credential_target = credential_target(secret_ref);
        write_credential(&credential_target, value)?;
        let metadata = SecretMetadata {
            contract_version: "secret-ref-v1".into(),
            secret_ref: secret_ref.into(),
            allowed_consumers: allowed_consumers.to_vec(),
            credential_target: credential_target.clone(),
        };
        let bytes = serde_json::to_vec_pretty(&metadata).map_err(|error| {
            PlatformError::Validation(format!("cannot serialize secret metadata: {error}"))
        })?;
        if let Err(error) = fs::write(self.metadata_path(secret_ref), bytes) {
            let _ = delete_credential(&credential_target);
            return Err(crate::error::io_error(
                "cannot write secret metadata",
                error,
            ));
        }
        Ok(())
    }

    pub fn with_secret<F>(
        &self,
        secret_ref: &str,
        selection: &CapabilitySelection,
        use_secret: F,
    ) -> Result<(), PlatformError>
    where
        F: FnOnce(&[u8]) -> Result<(), PlatformError>,
    {
        let metadata = self.load_metadata(secret_ref)?;
        if !metadata
            .allowed_consumers
            .iter()
            .any(|allowed| allowed == &selection.executor)
        {
            return Err(PlatformError::SecretDenied(format!(
                "executor {} is not allowed to resolve {secret_ref}",
                selection.executor
            )));
        }

        let secret = SecretBuffer::new(read_credential(&metadata.credential_target)?);
        use_secret(secret.as_bytes())
    }

    pub fn remove(&self, secret_ref: &str) -> Result<(), PlatformError> {
        let metadata = self.load_metadata(secret_ref)?;
        delete_credential(&metadata.credential_target)?;
        match fs::remove_file(self.metadata_path(secret_ref)) {
            Ok(()) => Ok(()),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
            Err(error) => Err(crate::error::io_error(
                "cannot delete secret metadata",
                error,
            )),
        }
    }

    fn load_metadata(&self, secret_ref: &str) -> Result<SecretMetadata, PlatformError> {
        let bytes = fs::read(self.metadata_path(secret_ref))
            .map_err(|error| crate::error::io_error("cannot read secret metadata", error))?;
        let metadata: SecretMetadata = serde_json::from_slice(&bytes).map_err(|error| {
            PlatformError::Validation(format!("invalid secret metadata: {error}"))
        })?;
        if metadata.secret_ref != secret_ref {
            return Err(PlatformError::Validation(
                "secret metadata reference mismatch".into(),
            ));
        }
        validate_reference(&metadata.secret_ref, &metadata.allowed_consumers)?;
        if metadata.credential_target != credential_target(secret_ref) {
            return Err(PlatformError::Validation(
                "secret credential target mismatch".into(),
            ));
        }
        Ok(metadata)
    }

    fn metadata_path(&self, secret_ref: &str) -> PathBuf {
        self.metadata_root
            .join(format!("{}.json", stable_id(secret_ref)))
    }
}

fn validate_reference(secret_ref: &str, allowed_consumers: &[String]) -> Result<(), PlatformError> {
    let contract = json!({
        "contract_version": "secret-ref-v1",
        "secret_ref": secret_ref,
        "allowed_consumers": allowed_consumers
    });
    contracts::validate(&contract, "secret-ref-v1.schema.json")
}

fn credential_target(secret_ref: &str) -> String {
    format!("BogdanAIP.chat-agent-platform:{}", stable_id(secret_ref))
}

fn stable_id(value: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(value.as_bytes());
    let digest = hasher.finalize();
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}

#[cfg(windows)]
fn credential_entry(target: &str) -> Result<keyring_core::Entry, PlatformError> {
    use std::collections::HashMap;

    use keyring_core::api::CredentialStoreApi;

    let store = windows_native_keyring_store::Store::new().map_err(|error| {
        PlatformError::SecretStore(format!(
            "cannot initialize Windows Credential Manager: {error}"
        ))
    })?;
    let mut modifiers = HashMap::new();
    modifiers.insert("target", target);
    modifiers.insert("persistence", "LocalMachine");
    store
        .build("chat-agent-platform", "secret", Some(&modifiers))
        .map_err(|error| {
            PlatformError::SecretStore(format!(
                "cannot create Windows Credential Manager entry: {error}"
            ))
        })
}

#[cfg(windows)]
fn write_credential(target: &str, value: &[u8]) -> Result<(), PlatformError> {
    credential_entry(target)?.set_secret(value).map_err(|error| {
        PlatformError::SecretStore(format!("Windows Credential Manager write failed: {error}"))
    })
}

#[cfg(windows)]
fn read_credential(target: &str) -> Result<Vec<u8>, PlatformError> {
    credential_entry(target)?.get_secret().map_err(|error| {
        PlatformError::SecretStore(format!("Windows Credential Manager read failed: {error}"))
    })
}

#[cfg(windows)]
fn delete_credential(target: &str) -> Result<(), PlatformError> {
    credential_entry(target)?
        .delete_credential()
        .map_err(|error| {
            PlatformError::SecretStore(format!("Windows Credential Manager delete failed: {error}"))
        })
}

#[cfg(not(windows))]
fn write_credential(_target: &str, _value: &[u8]) -> Result<(), PlatformError> {
    Err(PlatformError::ToolUnavailable(
        "Windows Credential Manager is only available on Windows".into(),
    ))
}

#[cfg(not(windows))]
fn read_credential(_target: &str) -> Result<Vec<u8>, PlatformError> {
    Err(PlatformError::ToolUnavailable(
        "Windows Credential Manager is only available on Windows".into(),
    ))
}

#[cfg(not(windows))]
fn delete_credential(_target: &str) -> Result<(), PlatformError> {
    Err(PlatformError::ToolUnavailable(
        "Windows Credential Manager is only available on Windows".into(),
    ))
}
