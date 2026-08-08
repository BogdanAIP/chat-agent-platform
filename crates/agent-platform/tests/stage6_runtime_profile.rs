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
        .expect("projects config"),
    )
    .expect("write projects config");
}

fn capability_names(value: &Value) -> BTreeSet<String> {
    value
        .as_object()
        .expect("capability map")
        .keys()
        .cloned()
        .collect()
}

#[test]
fn runtime_profile_covers_every_configured_capability_and_execution_path() {
    let temporary = tempdir().expect("temp directory");
    make_test_repo(temporary.path());

    let (_, profile) = write_runtime_profile(temporary.path(), Some("profile-test"))
        .expect("runtime profile must be generated even when optional edge tools are absent");
    let tools: Value = serde_json::from_str(
        &fs::read_to_string(temporary.path().join("config/tools.yaml")).expect("tools config"),
    )
    .expect("tools JSON");
    let expected = tools["capabilities"]
        .as_array()
        .expect("capabilities array")
        .iter()
        .map(|item| {
            item["capability"]
                .as_str()
                .expect("capability name")
                .to_owned()
        })
        .collect::<BTreeSet<_>>();
    let actual = capability_names(&profile["capabilities"]);
    assert_eq!(actual, expected, "runtime profile must not lag tools.yaml");

    for capability in expected {
        let entry = &profile["capabilities"][&capability];
        assert!(
            matches!(entry["status"].as_str(), Some("available" | "unavailable")),
            "{capability} must have explicit runtime status"
        );
        assert!(entry["executor"].is_string(), "{capability} executor");
        assert!(
            entry["execution_path"].is_string(),
            "{capability} execution path"
        );
    }

    assert_eq!(profile["tools"]["ffmpeg"]["available"], true);
    assert_eq!(profile["tools"]["ffprobe"]["available"], true);
    assert!(profile["rust_minimum"].is_string());
}
