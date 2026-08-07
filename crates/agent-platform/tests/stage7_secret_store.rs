#[cfg(windows)]
use std::fs;

#[cfg(windows)]
use agent_platform::capability::CapabilityRegistry;
use agent_platform::error::PlatformError;
use agent_platform::secret::SecretStore;
#[cfg(windows)]
use serde_json::json;
use tempfile::tempdir;
use uuid::Uuid;

#[cfg(windows)]
#[test]
fn selected_executor_can_use_secret_but_ffmpeg_cannot() {
    let root = tempdir().expect("temp root");
    fs::create_dir_all(root.path().join("config")).expect("config dir");
    fs::write(
        root.path().join("config/tools.yaml"),
        serde_json::to_vec_pretty(&json!({
            "contract_version": "tools-v1",
            "capabilities": [
                {
                    "capability": "video.generate",
                    "executor": "video.api",
                    "enabled": true,
                    "quality": "professional",
                    "reliability": "high",
                    "determinism": "standard",
                    "base_risk": "medium",
                    "cost": 0,
                    "fallbacks": []
                },
                {
                    "capability": "media.inspect",
                    "executor": "rust.local.ffmpeg",
                    "enabled": true,
                    "quality": "professional",
                    "reliability": "high",
                    "determinism": "high",
                    "base_risk": "low",
                    "cost": 0,
                    "fallbacks": []
                }
            ]
        }))
        .expect("manifest JSON"),
    )
    .expect("manifest write");
    fs::write(
        root.path().join("config/tool-lock.yaml"),
        serde_json::to_vec_pretty(&json!({
            "contract_version": "tool-lock-v1",
            "selected": {
                "video.generate": "video.api",
                "media.inspect": "rust.local.ffmpeg"
            }
        }))
        .expect("lock JSON"),
    )
    .expect("lock write");

    let registry = CapabilityRegistry::load(root.path()).expect("registry");
    let video = registry
        .select("video.generate", "professional", 0)
        .expect("video selection");
    let ffmpeg = registry
        .select("media.inspect", "professional", 0)
        .expect("ffmpeg selection");

    let store = SecretStore::new(root.path()).expect("secret store");
    let secret_ref = format!("secret://tests/{}", Uuid::new_v4().simple());
    let secret_value = format!("stage7-secret-{}", Uuid::new_v4().simple());
    let consumers = vec![video.executor.clone()];

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
        .with_secret(&secret_ref, &video, |secret| {
            observed = secret == secret_value.as_bytes();
            Ok(())
        })
        .expect("selected consumer must use secret");
    assert!(observed, "selected consumer must receive the stored value");

    let denied = store
        .with_secret(&secret_ref, &ffmpeg, |_| Ok(()))
        .expect_err("FFmpeg selection must not resolve unrelated secret");
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
