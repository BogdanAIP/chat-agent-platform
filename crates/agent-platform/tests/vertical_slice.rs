use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::Arc;
use std::thread;

use agent_platform::artifact::ArtifactStore;
use agent_platform::binding::resolve_project;
use agent_platform::bootstrap::build_context;
use agent_platform::contracts;
use agent_platform::error::PlatformError;
use agent_platform::policy::PolicyEnforcementPoint;
use agent_platform::service::{inspect_artifact, inspect_file, self_test};
use serde_json::json;
use tempfile::tempdir;

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root must resolve")
}

#[test]
fn real_wav_flows_through_rust_core_and_ffmpeg() {
    let temporary = tempdir().expect("temp directory");
    let source = temporary.path().join("tone.wav");
    let status = Command::new("ffmpeg")
        .args([
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:sample_rate=48000:duration=1",
            "-ac",
            "2",
            source.to_str().expect("UTF-8 temp path"),
        ])
        .status()
        .expect("ffmpeg must start");
    assert!(status.success());

    let result = inspect_file(&repo_root(), &source, Some("demo"), "project", Some("low"))
        .expect("Rust vertical slice must succeed");
    assert_eq!(result["status"], "success");
    assert_eq!(result["result"]["sample_rate_hz"], 48_000);
    assert_eq!(result["result"]["channels"], 2);
    assert_eq!(result["provenance"]["validated"], true);
    assert!(result["result"]["true_peak_dbtp"].as_f64().is_some());
    assert_eq!(result["result"]["true_peak_status"], "measured");
    assert!(
        result["artifact_refs"][0]["artifact_id"]
            .as_str()
            .is_some_and(|value| value.starts_with("art_"))
    );
    let artifact_id = result["artifact_refs"][0]["artifact_id"]
        .as_str()
        .expect("artifact id");
    let repeated = inspect_artifact(&repo_root(), artifact_id, Some("demo"), None)
        .expect("registered artifact inspection");
    assert_eq!(repeated["result"], result["result"]);
    assert_eq!(
        repeated["artifact_refs"][0]["sha256"],
        result["artifact_refs"][0]["sha256"]
    );
}

#[test]
fn unknown_project_is_not_guessed() {
    let error = resolve_project(&repo_root(), Some("neighbor-project"))
        .expect_err("unknown project must fail");
    assert!(matches!(error, PlatformError::Binding(_)));
}

#[test]
fn low_risk_hint_cannot_bypass_deny() {
    let binding = resolve_project(&repo_root(), Some("demo")).expect("demo binding");
    let policy = PolicyEnforcementPoint::load(&binding.policy_path).expect("policy config");
    let error = policy
        .evaluate(
            "shell.run_arbitrary",
            &json!({}),
            "project",
            Some("low"),
            "critical",
        )
        .expect_err("denied capability must remain denied");
    assert!(matches!(error, PlatformError::PolicyDenied(_)));
}

#[test]
fn bootstrap_loads_only_minimal_context() {
    let result = build_context(&repo_root(), Some("demo"), "media.inspect")
        .expect("bootstrap context must load");
    let keys = result["minimal_context"]
        .as_object()
        .expect("minimal context must be an object");
    assert_eq!(keys.len(), 3);
    assert!(keys.contains_key("CURRENT_STATE.md"));
    assert!(keys.contains_key("ARCHITECTURE.md"));
    assert!(keys.contains_key("CONSTRAINTS.md"));
}

#[test]
fn shared_contract_fixtures_have_expected_outcomes() {
    let root = repo_root();
    let cases = [
        (
            "tool-request-v1.schema.json",
            "tool-request.valid.json",
            "tool-request.invalid-missing-id.json",
        ),
        (
            "tool-v1.schema.json",
            "tool-result.valid.json",
            "tool-result.invalid-status.json",
        ),
        (
            "artifact-v1.schema.json",
            "artifact.valid.json",
            "artifact.invalid-hash.json",
        ),
        (
            "policy-decision-v1.schema.json",
            "policy-decision.valid.json",
            "policy-decision.invalid-risk.json",
        ),
        (
            "secret-ref-v1.schema.json",
            "secret-ref.valid.json",
            "secret-ref.invalid-empty-acl.json",
        ),
        (
            "job-v1.schema.json",
            "job.valid.json",
            "job.invalid-status.json",
        ),
    ];
    for (schema, valid_name, invalid_name) in cases {
        let load = |name: &str| -> serde_json::Value {
            serde_json::from_str(
                &std::fs::read_to_string(root.join("contracts/fixtures").join(name))
                    .expect("fixture must load"),
            )
            .expect("fixture JSON")
        };
        assert!(
            contracts::validate(&load(valid_name), schema).is_ok(),
            "{valid_name}"
        );
        assert!(
            contracts::validate(&load(invalid_name), schema).is_err(),
            "{invalid_name}"
        );
    }
}

#[test]
fn local_self_test_checks_write_read_cleanup_and_tools() {
    let result = self_test(&repo_root(), Some("demo")).expect("self-test must pass");
    assert_eq!(result["status"], "success");
    assert_eq!(result["result"]["ping"], "pong");
    assert_eq!(result["result"]["controlled_write_read"], "passed");
    assert_eq!(result["result"]["cleanup"], "passed");
    assert_eq!(result["provenance"]["validated"], true);
}

#[test]
fn artifact_manifest_preserves_concurrent_imports() {
    let temporary = tempdir().expect("temp directory");
    let source = temporary.path().join("fixture.wav");
    std::fs::write(&source, b"fixture bytes").expect("fixture write");
    let store =
        Arc::new(ArtifactStore::new(&temporary.path().join("artifacts")).expect("artifact store"));
    let handles: Vec<_> = (0..12)
        .map(|_| {
            let store = Arc::clone(&store);
            let source = source.clone();
            thread::spawn(move || {
                store
                    .import_file(&source, "concurrency-test", "project")
                    .expect("concurrent import")
            })
        })
        .collect();
    for handle in handles {
        handle.join().expect("import thread");
    }
    let manifest: serde_json::Value = serde_json::from_str(
        &std::fs::read_to_string(temporary.path().join("artifacts/manifest.json"))
            .expect("manifest read"),
    )
    .expect("manifest JSON");
    assert_eq!(manifest.as_object().map(serde_json::Map::len), Some(12));
}

#[test]
fn artifact_lookup_rejects_tampered_content() {
    let temporary = tempdir().expect("temp directory");
    let source = temporary.path().join("fixture.wav");
    std::fs::write(&source, b"original bytes").expect("fixture write");
    let store = ArtifactStore::new(&temporary.path().join("artifacts")).expect("artifact store");
    let artifact = store
        .import_file(&source, "tamper-test", "project")
        .expect("artifact import");
    std::fs::write(&artifact.path, b"changed bytes").expect("tamper write");
    let error = store
        .get(&artifact.artifact_id)
        .expect_err("tampered artifact must fail");
    assert!(matches!(error, PlatformError::Validation(_)));
}
