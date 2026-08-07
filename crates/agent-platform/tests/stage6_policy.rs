use std::fs;

use agent_platform::capability::CapabilityRegistry;
use agent_platform::error::PlatformError;
use agent_platform::policy::PolicyEnforcementPoint;
use serde_json::json;
use tempfile::tempdir;

#[test]
fn professional_requirement_rejects_basic_executor_before_ranking() {
    let root = tempdir().expect("temp root");
    fs::create_dir_all(root.path().join("config")).expect("config dir");
    fs::write(
        root.path().join("config/tools.yaml"),
        serde_json::to_string_pretty(&json!({
            "contract_version": "tools-v1",
            "capabilities": [{
                "capability": "media.inspect",
                "executor": "basic.fake",
                "enabled": true,
                "quality": "basic",
                "reliability": "high",
                "determinism": "high",
                "base_risk": "low",
                "cost": 0,
                "fallbacks": []
            }]
        }))
        .expect("manifest JSON"),
    )
    .expect("manifest write");
    fs::write(
        root.path().join("config/tool-lock.yaml"),
        serde_json::to_string_pretty(&json!({
            "contract_version": "tool-lock-v1",
            "selected": {"media.inspect": "basic.fake"}
        }))
        .expect("lock JSON"),
    )
    .expect("lock write");

    let registry = CapabilityRegistry::load(root.path()).expect("registry");
    let error = registry
        .select("media.inspect", "professional", 0)
        .expect_err("basic executor must be rejected");
    assert!(matches!(error, PlatformError::Validation(_)));
}

#[test]
fn cost_gate_rejects_executor_before_execution() {
    let root = tempdir().expect("temp root");
    fs::create_dir_all(root.path().join("config")).expect("config dir");
    fs::write(
        root.path().join("config/tools.yaml"),
        serde_json::to_string_pretty(&json!({
            "contract_version": "tools-v1",
            "capabilities": [{
                "capability": "video.generate",
                "executor": "paid.api",
                "enabled": true,
                "quality": "professional",
                "reliability": "high",
                "determinism": "standard",
                "base_risk": "medium",
                "cost": 5,
                "fallbacks": []
            }]
        }))
        .expect("manifest JSON"),
    )
    .expect("manifest write");
    fs::write(
        root.path().join("config/tool-lock.yaml"),
        serde_json::to_string_pretty(&json!({
            "contract_version": "tool-lock-v1",
            "selected": {"video.generate": "paid.api"}
        }))
        .expect("lock JSON"),
    )
    .expect("lock write");

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
