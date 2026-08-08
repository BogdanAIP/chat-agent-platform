#![cfg(windows)]

use std::fs;
use std::path::{Path, PathBuf};

use agent_platform::binding::resolve_project;
use agent_platform::capability::{CapabilityRegistry, required_quality};
use agent_platform::secret::SecretStore;
use serde_json::json;
use tempfile::tempdir;
use uuid::Uuid;

const PROJECT_ID: &str = "relay-secret-test";
const TOKEN: &[u8] = b"abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGH";

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
            "active_project_id": PROJECT_ID,
            "projects": [{
                "project_id": PROJECT_ID,
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
fn locked_relay_executor_can_round_trip_its_credential() {
    let temporary = tempdir().expect("temp directory");
    make_test_repo(temporary.path());
    let binding = resolve_project(temporary.path(), Some(PROJECT_ID)).expect("project binding");
    let quality = required_quality(&binding.repo_root, "transport.relay_connect")
        .expect("relay quality requirement");
    let selection = CapabilityRegistry::load(&binding.repo_root)
        .expect("capability registry")
        .select("transport.relay_connect", &quality, 0)
        .expect("locked relay selection");
    assert_eq!(selection.executor(), "rust.local.relay");

    let secret_ref = format!("secret://relay/test/{}", Uuid::new_v4().simple());
    let store = SecretStore::new(&binding.repo_root).expect("secret store");
    store
        .put(&secret_ref, &[selection.executor().to_owned()], TOKEN)
        .expect("relay credential write");

    let mut observed = Vec::new();
    store
        .with_secret(&secret_ref, &selection, |secret| {
            observed.extend_from_slice(secret);
            Ok(())
        })
        .expect("relay credential ACL read");
    assert_eq!(observed, TOKEN);

    store.remove(&secret_ref).expect("relay credential cleanup");
}
