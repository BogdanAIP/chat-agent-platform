use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};

use agent_platform::service::write_runtime_profile;
use serde_json::{Value, json};
use tempfile::tempdir;

fn source_repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root must resolve")
}

fn make_test_repo(root: &Path) {
    let source_config = source_repo_root().join("config");
    let config = root.join("config");
    fs::create_dir_all(&config).expect("test config directory");
    for file in [
        "tools.yaml",
        "tool-lock.yaml",
        "capability-requirements.yaml",
        "policy.yaml",
    ] {
        fs::copy(source_config.join(file), config.join(file)).expect("copy test config");
    }
    fs::write(
        config.join("projects.yaml"),
        serde_json::to_string_pretty(&json!({
            "contract_version": "projects-v1",
            "active_project_id": "profile-test",
            "projects": [{
                "project_id": "profile-test",
                "repo_root": "..",
                "local_root": "..",
                "artifact_root": "../artifacts",
                "policy": "policy.yaml"
            }]
        }))
        .expect("serialize projects config"),
    )
    .expect("write projects config");
}

#[test]
fn runtime_profile_is_derived_from_every_locked_capability() {
    let temporary = tempdir().expect("temp directory");
    make_test_repo(temporary.path());

    let (path, profile) =
        write_runtime_profile(temporary.path(), Some("profile-test")).expect("runtime profile");
    assert!(
        path.is_file(),
        "runtime capability profile must be persisted"
    );
    assert_eq!(profile["contract_version"], "runtime-capability-profile-v1");
    assert!(
        profile["rust"]["compiler"]
            .as_str()
            .is_some_and(|value| value.starts_with("rustc ")),
        "profile must report the compiler that built the binary"
    );
    assert!(
        profile["rust"]["msrv"]
            .as_str()
            .is_some_and(|value| !value.is_empty()),
        "profile must retain the package MSRV separately"
    );

    let lock: Value = serde_json::from_str(
        &fs::read_to_string(temporary.path().join("config/tool-lock.yaml"))
            .expect("tool lock text"),
    )
    .expect("tool lock JSON");
    let locked = lock["selected"]
        .as_object()
        .expect("selected tool lock map")
        .keys()
        .cloned()
        .collect::<BTreeSet<_>>();
    let profiled = profile["capabilities"]
        .as_object()
        .expect("profile capability map")
        .keys()
        .cloned()
        .collect::<BTreeSet<_>>();
    assert_eq!(
        profiled, locked,
        "runtime profile must not omit locked capabilities"
    );

    for capability in locked {
        let entry = &profile["capabilities"][&capability];
        assert!(entry["executor"].is_string(), "{capability} executor");
        assert!(
            entry["execution_path"].is_string(),
            "{capability} execution path"
        );
        assert!(entry["required"].is_boolean(), "{capability} required flag");
        assert!(
            matches!(entry["status"].as_str(), Some("available" | "unavailable")),
            "{capability} runtime status"
        );
        assert!(
            entry["acceptance_evidence"].is_array(),
            "{capability} acceptance evidence"
        );
    }

    let persisted: Value = serde_json::from_str(
        &fs::read_to_string(path).expect("persisted runtime capability profile"),
    )
    .expect("persisted profile JSON");
    assert_eq!(persisted, profile);
}
