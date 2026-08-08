use std::fs;
use std::path::Path;

use agent_platform::capability::CapabilityRegistry;
use agent_platform::error::PlatformError;
use agent_platform::policy::PolicyEnforcementPoint;
use serde_json::{Map, Value, json};
use tempfile::tempdir;

fn write_registry(root: &Path, tools: Value, lock: Value, requirements: Value) {
    fs::create_dir_all(root.join("config")).expect("config dir");
    fs::write(
        root.join("config/tools.yaml"),
        serde_json::to_string_pretty(&tools).expect("manifest JSON"),
    )
    .expect("manifest write");
    fs::write(
        root.join("config/tool-lock.yaml"),
        serde_json::to_string_pretty(&lock).expect("lock JSON"),
    )
    .expect("lock write");
    fs::write(
        root.join("config/capability-requirements.yaml"),
        serde_json::to_string_pretty(&requirements).expect("requirements JSON"),
    )
    .expect("requirements write");
}

fn requirement(
    capability: &str,
    quality: &str,
    reliability: &str,
    determinism: &str,
    execution_path: &str,
) -> Value {
    json!({
        "contract_version": "capability-requirements-v1",
        "requirements": [{
            "capability": capability,
            "required": true,
            "required_quality": quality,
            "required_reliability": reliability,
            "required_determinism": determinism,
            "execution_paths": [execution_path],
            "fallbacks": [],
            "acceptance_evidence": []
        }]
    })
}

fn tool(
    capability: &str,
    executor: &str,
    path: &str,
    quality: &str,
    reliability: &str,
    determinism: &str,
    cost: u64,
) -> Value {
    json!({
        "contract_version": "tools-v1",
        "capabilities": [{
            "capability": capability,
            "executor": executor,
            "execution_path": path,
            "enabled": true,
            "quality": quality,
            "reliability": reliability,
            "determinism": determinism,
            "base_risk": "low",
            "cost": cost,
            "fallbacks": []
        }]
    })
}

fn lock(capability: &str, executor: &str) -> Value {
    let mut selected = Map::new();
    selected.insert(capability.to_owned(), Value::String(executor.to_owned()));
    json!({
        "contract_version": "tool-lock-v1",
        "selected": Value::Object(selected)
    })
}

#[test]
fn professional_requirement_rejects_basic_executor_before_ranking() {
    let root = tempdir().expect("temp root");
    write_registry(
        root.path(),
        tool(
            "media.inspect",
            "basic.fake",
            "local.fake",
            "basic",
            "high",
            "high",
            0,
        ),
        lock("media.inspect", "basic.fake"),
        requirement(
            "media.inspect",
            "professional",
            "high",
            "high",
            "local.fake",
        ),
    );

    let error = match CapabilityRegistry::load(root.path()) {
        Ok(_) => panic!("basic executor must be rejected while validating the locked selection"),
        Err(error) => error,
    };
    assert!(matches!(error, PlatformError::Validation(_)));
    assert!(error.to_string().contains("quality"));
}

#[test]
fn reliability_and_determinism_are_runtime_gates() {
    let root = tempdir().expect("temp root");
    write_registry(
        root.path(),
        tool(
            "media.inspect",
            "weak.fake",
            "local.fake",
            "professional",
            "standard",
            "standard",
            0,
        ),
        lock("media.inspect", "weak.fake"),
        requirement(
            "media.inspect",
            "professional",
            "high",
            "high",
            "local.fake",
        ),
    );

    let error = match CapabilityRegistry::load(root.path()) {
        Ok(_) => panic!("weak reliability must fail closed"),
        Err(error) => error,
    };
    assert!(error.to_string().contains("reliability"));
}

#[test]
fn locked_executor_must_use_an_allowed_execution_path() {
    let root = tempdir().expect("temp root");
    write_registry(
        root.path(),
        tool(
            "media.inspect",
            "wrong.path",
            "remote.unapproved",
            "professional",
            "high",
            "high",
            0,
        ),
        lock("media.inspect", "wrong.path"),
        requirement(
            "media.inspect",
            "professional",
            "high",
            "high",
            "local.ffmpeg",
        ),
    );

    let error = match CapabilityRegistry::load(root.path()) {
        Ok(_) => panic!("unapproved execution path must fail closed"),
        Err(error) => error,
    };
    assert!(error.to_string().contains("not allowed"));
}

#[test]
fn unknown_manifest_fields_are_rejected_instead_of_ignored() {
    let root = tempdir().expect("temp root");
    let mut tools = tool(
        "media.inspect",
        "rust.local.ffmpeg",
        "local.ffmpeg",
        "professional",
        "high",
        "high",
        0,
    );
    tools["capabilities"][0]["imaginary_security_gate"] = json!(true);
    write_registry(
        root.path(),
        tools,
        lock("media.inspect", "rust.local.ffmpeg"),
        requirement(
            "media.inspect",
            "professional",
            "high",
            "high",
            "local.ffmpeg",
        ),
    );

    let error = match CapabilityRegistry::load(root.path()) {
        Ok(_) => panic!("unknown manifest fields must fail closed"),
        Err(error) => error,
    };
    assert!(error.to_string().contains("imaginary_security_gate"));
}

#[test]
fn cost_gate_rejects_executor_before_execution() {
    let root = tempdir().expect("temp root");
    write_registry(
        root.path(),
        tool(
            "video.generate",
            "paid.api",
            "remote.paid.api",
            "professional",
            "high",
            "standard",
            5,
        ),
        lock("video.generate", "paid.api"),
        requirement(
            "video.generate",
            "professional",
            "high",
            "standard",
            "remote.paid.api",
        ),
    );

    let registry = CapabilityRegistry::load(root.path()).expect("registry");
    let error = registry
        .select("video.generate", "professional", 0)
        .expect_err("cost limit must be mandatory");
    assert!(matches!(error, PlatformError::PolicyDenied(_)));
}

#[test]
fn guarded_preview_is_immutable_and_parameter_bound() {
    let root = tempdir().expect("temp root");
    let policy_path = root.path().join("policy.yaml");
    fs::write(
        &policy_path,
        serde_json::to_string_pretty(&json!({
            "contract_version": "policy-v1",
            "rules": {
                "distribution.publish": {
                    "decision": "guarded",
                    "enforced_by": "policy_enforcement_point",
                    "allowed_data_classes": ["project"],
                    "external_side_effect": true,
                    "max_cost": 10
                }
            }
        }))
        .expect("policy JSON"),
    )
    .expect("policy write");
    let pep = PolicyEnforcementPoint::load(&policy_path).expect("policy");
    let parameters = json!({
        "artifact_id": "art_demo",
        "artifact_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "external_destination": "example-channel",
        "cost": 1
    });
    let first = pep
        .evaluate(
            "distribution.publish",
            &parameters,
            "project",
            Some("low"),
            "medium",
        )
        .expect("guarded preview");
    let repeated = pep
        .evaluate(
            "distribution.publish",
            &parameters,
            "project",
            Some("critical"),
            "medium",
        )
        .expect("same guarded preview");
    assert_eq!(first.decision, "guarded");
    assert_eq!(first.effective_risk, "high");
    assert_eq!(first.confirmation_binding, repeated.confirmation_binding);

    let changed = pep
        .evaluate(
            "distribution.publish",
            &json!({
                "artifact_id": "art_demo",
                "artifact_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "external_destination": "example-channel",
                "cost": 1
            }),
            "project",
            None,
            "medium",
        )
        .expect("changed preview");
    assert_ne!(first.confirmation_binding, changed.confirmation_binding);
}
