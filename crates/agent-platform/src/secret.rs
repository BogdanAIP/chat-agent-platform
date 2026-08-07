use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};

use crate::contracts;
use crate::error::PlatformError;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SecretMetadata {
    contract_version: String,
    secret_ref: String,
    allowed_consumers: Vec<String>,
    credential_target: String,
}

pub struct SecretValue {
    bytes: Vec<u8>,
}

impl SecretValue {
    #[must_use]
    pub fn as_bytes(&self) -> &[u8] {
        &self.bytes
    }
}

impl Drop for SecretValue {
    fn drop(&mut self) {
        self.bytes.fill(0);
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
        let contract = json!({
            "contract_version": "secret-ref-v1",
            "secret_ref": secret_ref,
            "allowed_consumers": allowed_consumers
        });
        contracts::validate(&contract, "secret-ref-v1.schema.json")?;
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
            credential_target,
        };
        let bytes = serde_json::to_vec_pretty(&metadata).map_err(|error| {
            PlatformError::Validation(format!("cannot serialize secret metadata: {error}"))
        })?;
        fs::write(self.metadata_path(secret_ref), bytes)
            .map_err(|error| crate::error::io_error("cannot write secret metadata", error))?;
        Ok(())
    }

    pub fn resolve(
        &self,
        secret_ref: &str,
        consumer: &str,
    ) -> Result<SecretValue, PlatformError> {
        let metadata = self.load_metadata(secret_ref)?;
        if !metadata
            .allowed_consumers
            .iter()
            .any(|allowed| allowed == consumer)
        {
            return Err(PlatformError::SecretDenied(format!(
                "consumer {consumer} is not allowed to resolve {secret_ref}"
            )));
        }
        let bytes = read_credential(&metadata.credential_target)?;
        Ok(SecretValue { bytes })
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
        let contract = json!({
            "contract_version": metadata.contract_version,
            "secret_ref": metadata.secret_ref,
            "allowed_consumers": metadata.allowed_consumers
        });
        contracts::validate(&contract, "secret-ref-v1.schema.json")?;
        Ok(metadata)
    }

    fn metadata_path(&self, secret_ref: &str) -> PathBuf {
        self.metadata_root
            .join(format!("{}.json", stable_id(secret_ref)))
    }
}

fn credential_target(secret_ref: &str) -> String {
    format!("chat-agent-platform:{}", stable_id(secret_ref))
}

fn stable_id(value: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(value.as_bytes());
    let digest = hasher.finalize();
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}

#[cfg(windows)]
fn write_credential(target: &str, value: &[u8]) -> Result<(), PlatformError> {
    use windows::Win32::Security::Credentials::{
        CREDENTIALW, CRED_PERSIST_LOCAL_MACHINE, CRED_TYPE_GENERIC, CredWriteW,
    };
    use windows::core::PWSTR;

    let mut target_wide: Vec<u16> = target.encode_utf16().chain(std::iter::once(0)).collect();
    let blob_size = u32::try_from(value.len())
        .map_err(|_| PlatformError::Validation("secret is too large".into()))?;
    let mut credential = CREDENTIALW {
        Type: CRED_TYPE_GENERIC,
        TargetName: PWSTR(target_wide.as_mut_ptr()),
        CredentialBlobSize: blob_size,
        CredentialBlob: value.as_ptr().cast_mut(),
        Persist: CRED_PERSIST_LOCAL_MACHINE,
        ..Default::default()
    };
    unsafe { CredWriteW(&mut credential, 0) }.map_err(|error| {
        PlatformError::Validation(format!("Windows Credential Manager write failed: {error}"))
    })
}

#[cfg(windows)]
fn read_credential(target: &str) -> Result<Vec<u8>, PlatformError> {
    use std::ffi::c_void;
    use std::ptr::null_mut;
    use std::slice;

    use windows::Win32::Security::Credentials::{
        CREDENTIALW, CRED_TYPE_GENERIC, CredFree, CredReadW,
    };
    use windows::core::PCWSTR;

    let target_wide: Vec<u16> = target.encode_utf16().chain(std::iter::once(0)).collect();
    let mut credential: *mut CREDENTIALW = null_mut();
    unsafe {
        CredReadW(
            PCWSTR(target_wide.as_ptr()),
            CRED_TYPE_GENERIC,
            None,
            &mut credential,
        )
    }
    .map_err(|error| {
        PlatformError::Validation(format!("Windows Credential Manager read failed: {error}"))
    })?;
    if credential.is_null() {
        return Err(PlatformError::Validation(
            "Windows Credential Manager returned a null credential".into(),
        ));
    }
    let bytes = unsafe {
        let item = &*credential;
        slice::from_raw_parts(item.CredentialBlob, item.CredentialBlobSize as usize).to_vec()
    };
    unsafe { CredFree(credential.cast::<c_void>()) };
    Ok(bytes)
}

#[cfg(windows)]
fn delete_credential(target: &str) -> Result<(), PlatformError> {
    use windows::Win32::Security::Credentials::{CRED_TYPE_GENERIC, CredDeleteW};
    use windows::core::PCWSTR;

    let target_wide: Vec<u16> = target.encode_utf16().chain(std::iter::once(0)).collect();
    unsafe { CredDeleteW(PCWSTR(target_wide.as_ptr()), CRED_TYPE_GENERIC, None) }.map_err(|error| {
        PlatformError::Validation(format!("Windows Credential Manager delete failed: {error}"))
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
