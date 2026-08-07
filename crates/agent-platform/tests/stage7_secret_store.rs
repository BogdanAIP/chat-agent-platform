#[cfg(windows)]
use std::fs;

use agent_platform::error::PlatformError;
use agent_platform::secret::SecretStore;
use tempfile::tempdir;
use uuid::Uuid;

#[cfg(windows)]
#[test]
fn allowed_consumer_can_use_secret_but_ffmpeg_cannot() {
    let root = tempdir().expect("temp root");
    let store = SecretStore::new(root.path()).expect("secret store");
    let secret_ref = format!("secret://tests/{}", Uuid::new_v4().simple());
    let secret_value = format!("stage7-secret-{}", Uuid::new_v4().simple());
    let consumers = vec!["video.api".to_string()];

    store
        .put(&secret_ref, &consumers, secret_value.as_bytes())
        .expect("store secret");

    let metadata_dump = fs::read_dir(root.path().join("runtime/secrets"))
        .expect("metadata directory")
        .map(|entry| fs::read(entry.expect("metadata entry").path()).expect("metadata read"))
        .flatten()
        .collect::<Vec<_>>();
    assert!(
        !metadata_dump
            .windows(secret_value.len())
            .any(|window| window == secret_value.as_bytes()),
        "raw secret must never be present in metadata"
    );

    let mut observed = false;
    store
        .with_secret(&secret_ref, "video.api", |secret| {
            observed = secret == secret_value.as_bytes();
            Ok(())
        })
        .expect("allowed consumer must use secret");
    assert!(observed, "allowed consumer must receive the stored value");

    let denied = store
        .with_secret(&secret_ref, "ffmpeg", |_| Ok(()))
        .expect_err("FFmpeg must not resolve unrelated secret");
    assert!(matches!(denied, PlatformError::SecretDenied(_)));
    assert_eq!(denied.code(), "SECRET_ACCESS_DENIED");
    assert!(
        !denied.to_string().contains(&secret_value),
        "access errors must not disclose the raw secret"
    );

    store.remove(&secret_ref).expect("secret cleanup");
}

#[test]
fn secret_reference_contract_rejects_empty_acl() {
    let root = tempdir().expect("temp root");
    let store = SecretStore::new(root.path()).expect("secret store");
    let secret_ref = format!("secret://tests/{}", Uuid::new_v4().simple());
    let error = store
        .put(&secret_ref, &[], b"not-stored")
        .expect_err("empty ACL must be rejected before backend write");
    assert!(matches!(error, PlatformError::Validation(_)));
}
