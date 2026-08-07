use std::fs::{self, OpenOptions};
use std::path::Path;

use agent_platform::artifact::ArtifactStore;
use agent_platform::capability::CapabilityRegistry;
use agent_platform::error::PlatformError;
use serde_json::json;
use tempfile::tempdir;

fn registry(root: &Path) -> CapabilityRegistry {
    fs::create_dir_all(root.join("config")).expect("config directory");
    fs::write(
        root.join("config/tools.yaml"),
        serde_json::to_vec_pretty(&json!({
            "contract_version": "tools-v1",
            "capabilities": [
                {
                    "capability": "external.stage",
                    "executor": "cloud.api",
                    "enabled": true,
                    "quality": "professional",
                    "reliability": "high",
                    "determinism": "high",
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
        root.join("config/tool-lock.yaml"),
        serde_json::to_vec_pretty(&json!({
            "contract_version": "tool-lock-v1",
            "selected": {
                "external.stage": "cloud.api",
                "media.inspect": "rust.local.ffmpeg"
            }
        }))
        .expect("lock JSON"),
    )
    .expect("lock write");
    CapabilityRegistry::load(root).expect("capability registry")
}

#[test]
fn staging_requires_allowlisted_selection_and_always_cleans_copy() {
    let temporary = tempdir().expect("temporary root");
    let source = temporary.path().join("fixture.wav");
    fs::write(&source, b"stage-eight-fixture").expect("fixture write");
    let store = ArtifactStore::new(&temporary.path().join("artifacts")).expect("artifact store");
    let artifact = store
        .import_file(&source, "stage8-test", "project")
        .expect("artifact import");
    let registry = registry(temporary.path());
    let cloud = registry
        .select("external.stage", "professional", 0)
        .expect("cloud selection");
    let ffmpeg = registry
        .select("media.inspect", "professional", 0)
        .expect("ffmpeg selection");
    store
        .allow_external_staging(&artifact.artifact_id, std::slice::from_ref(&cloud))
        .expect("allow cloud staging");

    let staging_root = temporary.path().join("external-staging");
    store
        .with_staged_copy(&artifact.artifact_id, &cloud, &staging_root, |path| {
            assert_eq!(
                fs::read(path).expect("read staged copy"),
                b"stage-eight-fixture"
            );
            Ok(())
        })
        .expect("allowlisted consumer must stage artifact");
    assert_eq!(
        fs::read_dir(&staging_root)
            .expect("staging root")
            .count(),
        0,
        "temporary staging directory must be removed after success"
    );

    let callback_error = store
        .with_staged_copy(&artifact.artifact_id, &cloud, &staging_root, |_| {
            Err(PlatformError::Validation("consumer failed".into()))
        })
        .expect_err("consumer error must be returned");
    assert!(matches!(callback_error, PlatformError::Validation(_)));
    assert_eq!(
        fs::read_dir(&staging_root)
            .expect("staging root")
            .count(),
        0,
        "temporary staging directory must be removed after consumer failure"
    );

    let denied = store
        .with_staged_copy(&artifact.artifact_id, &ffmpeg, &staging_root, |_| Ok(()))
        .expect_err("unlisted executor must not stage artifact");
    assert!(matches!(denied, PlatformError::PolicyDenied(_)));
    assert_eq!(
        fs::read_dir(&staging_root)
            .expect("staging root")
            .count(),
        0,
        "denied staging must not leave temporary files"
    );

    store
        .disable_external_staging(&artifact.artifact_id)
        .expect("disable staging");
    let disabled = store
        .with_staged_copy(&artifact.artifact_id, &cloud, &staging_root, |_| Ok(()))
        .expect_err("disabled staging must be enforced");
    assert!(matches!(disabled, PlatformError::PolicyDenied(_)));
}

#[test]
fn private_artifact_cannot_enable_external_staging() {
    let temporary = tempdir().expect("temporary root");
    let source = temporary.path().join("private.wav");
    fs::write(&source, b"private-data").expect("fixture write");
    let store = ArtifactStore::new(&temporary.path().join("artifacts")).expect("artifact store");
    let artifact = store
        .import_file(&source, "stage8-test", "private")
        .expect("artifact import");
    let registry = registry(temporary.path());
    let cloud = registry
        .select("external.stage", "professional", 0)
        .expect("cloud selection");

    let denied = store
        .allow_external_staging(&artifact.artifact_id, &[cloud])
        .expect_err("private artifact must not be externally stageable");
    assert!(matches!(denied, PlatformError::PolicyDenied(_)));
}

#[test]
fn tampered_artifact_is_rejected_before_external_copy() {
    let temporary = tempdir().expect("temporary root");
    let source = temporary.path().join("fixture.wav");
    fs::write(&source, b"original-data").expect("fixture write");
    let store = ArtifactStore::new(&temporary.path().join("artifacts")).expect("artifact store");
    let artifact = store
        .import_file(&source, "stage8-test", "project")
        .expect("artifact import");
    let registry = registry(temporary.path());
    let cloud = registry
        .select("external.stage", "professional", 0)
        .expect("cloud selection");
    store
        .allow_external_staging(&artifact.artifact_id, std::slice::from_ref(&cloud))
        .expect("allow cloud staging");
    fs::write(&artifact.path, b"tampered-data").expect("tamper artifact");

    let staging_root = temporary.path().join("external-staging");
    let error = store
        .with_staged_copy(&artifact.artifact_id, &cloud, &staging_root, |_| Ok(()))
        .expect_err("checksum mismatch must stop staging");
    assert!(matches!(error, PlatformError::Validation(_)));
    assert!(
        !staging_root.exists(),
        "checksum rejection must happen before staging root is created"
    );
}

#[test]
fn recovery_removes_abandoned_state_but_skips_active_pending_import() {
    let temporary = tempdir().expect("temporary root");
    let artifact_root = temporary.path().join("artifacts");
    let source = temporary.path().join("fixture.wav");
    fs::write(&source, b"registered-data").expect("fixture write");
    let store = ArtifactStore::new(&artifact_root).expect("artifact store");
    let registered = store
        .import_file(&source, "stage8-test", "project")
        .expect("artifact import");

    let orphan = artifact_root.join("art_deadbeef");
    fs::create_dir(&orphan).expect("orphan directory");
    fs::write(orphan.join("orphan.bin"), b"orphan").expect("orphan file");

    let abandoned = artifact_root.join(".pending-art_cafebabe");
    fs::create_dir(&abandoned).expect("abandoned pending directory");
    fs::write(abandoned.join("copy.bin"), b"pending").expect("pending file");
    fs::write(artifact_root.join(".pending-art_cafebabe.lock"), b"").expect("pending lock");

    let active = artifact_root.join(".pending-art_feedface");
    fs::create_dir(&active).expect("active pending directory");
    fs::write(active.join("copy.bin"), b"active").expect("active pending file");
    let active_lock_path = artifact_root.join(".pending-art_feedface.lock");
    let active_lock = OpenOptions::new()
        .create(true)
        .truncate(false)
        .read(true)
        .write(true)
        .open(&active_lock_path)
        .expect("active lock file");
    active_lock.lock().expect("hold active pending lock");

    let report = store.recover_orphans().expect("artifact recovery");
    assert_eq!(report.removed_unregistered, 1);
    assert_eq!(report.removed_pending, 1);
    assert_eq!(report.skipped_active_pending, 1);
    assert!(Path::new(&registered.path).exists());
    assert!(!orphan.exists());
    assert!(!abandoned.exists());
    assert!(active.exists());

    active_lock.unlock().expect("release active pending lock");
    drop(active_lock);
    let second = store.recover_orphans().expect("second recovery");
    assert_eq!(second.removed_pending, 1);
    assert!(!active.exists());
    assert!(!active_lock_path.exists());
}
