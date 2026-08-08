use std::fs;
use std::sync::{Arc, Barrier};
use std::thread;

use agent_platform::confirmation::ConfirmationStore;
use agent_platform::error::PlatformError;
use agent_platform::policy::{PolicyDecision, PolicyEnforcementPoint};
use chrono::{Duration, Utc};
use serde_json::{Value, json};
use tempfile::tempdir;

fn guarded_policy(root: &std::path::Path) -> PolicyEnforcementPoint {
    let path = root.join("policy.yaml");
    fs::write(
        &path,
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
    PolicyEnforcementPoint::load(&path).expect("policy")
}

fn decision(pep: &PolicyEnforcementPoint, sha: &str, destination: &str) -> PolicyDecision {
    pep.evaluate(
        "distribution.publish",
        &json!({
            "artifact_id": "art_demo",
            "artifact_sha256": sha,
            "external_destination": destination,
            "cost": 1
        }),
        "project",
        None,
        "medium",
    )
    .expect("guarded decision")
}

fn confirmation_path(root: &std::path::Path, confirmation_id: &str) -> std::path::PathBuf {
    root.join(format!("{confirmation_id}.json"))
}

#[test]
fn exact_fresh_policy_binding_is_required_and_replay_is_denied() {
    let temporary = tempdir().expect("temp root");
    let pep = guarded_policy(temporary.path());
    let store_root = temporary.path().join("confirmations");
    let store = ConfirmationStore::new(&store_root, "demo").expect("confirmation store");
    let original = decision(
        &pep,
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "example-channel",
    );
    let prepared = store.prepare(&original).expect("prepare confirmation");
    assert_eq!(prepared.status, "prepared");

    let changed_artifact = decision(
        &pep,
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "example-channel",
    );
    let error = store
        .consume_for_decision(&prepared.confirmation_id, &changed_artifact)
        .expect_err("changed artifact hash must invalidate confirmation");
    assert!(matches!(error, PlatformError::PolicyDenied(_)));
    assert_eq!(
        store
            .get(&prepared.confirmation_id)
            .expect("confirmation after denied consume")
            .status,
        "prepared",
        "binding mismatch must not burn a valid confirmation"
    );

    let changed_destination = decision(
        &pep,
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "another-channel",
    );
    assert!(
        store
            .consume_for_decision(&prepared.confirmation_id, &changed_destination)
            .is_err(),
        "destination change must invalidate confirmation"
    );

    let fresh_same_action = decision(
        &pep,
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "example-channel",
    );
    assert_ne!(
        original.decision_id, fresh_same_action.decision_id,
        "policy decisions are fresh audit records"
    );
    assert_eq!(
        original.confirmation_binding,
        fresh_same_action.confirmation_binding,
        "stable action binding must survive fresh policy evaluation"
    );
    let consumed = store
        .consume_for_decision(&prepared.confirmation_id, &fresh_same_action)
        .expect("exact fresh action may consume confirmation");
    assert_eq!(consumed.status, "consumed");
    assert!(consumed.consumed_at.is_some());

    let replay = store
        .consume_for_decision(&prepared.confirmation_id, &fresh_same_action)
        .expect_err("confirmation is one-shot");
    assert!(matches!(replay, PlatformError::PolicyDenied(_)));
    assert!(replay.to_string().contains("already been consumed"));
}

#[test]
fn expired_confirmation_fails_closed_without_becoming_consumed() {
    let temporary = tempdir().expect("temp root");
    let pep = guarded_policy(temporary.path());
    let store_root = temporary.path().join("confirmations");
    let store = ConfirmationStore::new(&store_root, "demo").expect("confirmation store");
    let action = decision(
        &pep,
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "example-channel",
    );
    let prepared = store
        .prepare_with_ttl(&action, 30)
        .expect("prepare confirmation");

    let path = confirmation_path(&store_root, &prepared.confirmation_id);
    let mut persisted: Value = serde_json::from_str(
        &fs::read_to_string(&path).expect("persisted confirmation"),
    )
    .expect("confirmation JSON");
    persisted["expires_at"] = Value::String((Utc::now() - Duration::seconds(1)).to_rfc3339());
    fs::write(
        &path,
        serde_json::to_string_pretty(&persisted).expect("expired confirmation JSON"),
    )
    .expect("rewrite expiration for deterministic test");

    let fresh = decision(
        &pep,
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "example-channel",
    );
    let error = store
        .consume_for_decision(&prepared.confirmation_id, &fresh)
        .expect_err("expired confirmation must fail closed");
    assert!(matches!(error, PlatformError::PolicyDenied(_)));
    assert!(error.to_string().contains("expired"));
    assert_eq!(
        store
            .get(&prepared.confirmation_id)
            .expect("expired record remains auditable")
            .status,
        "prepared"
    );
}

#[test]
fn concurrent_consumers_cannot_execute_one_confirmation_twice() {
    let temporary = tempdir().expect("temp root");
    let pep = guarded_policy(temporary.path());
    let store_root = temporary.path().join("confirmations");
    let store = ConfirmationStore::new(&store_root, "demo").expect("confirmation store");
    let action = decision(
        &pep,
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "example-channel",
    );
    let prepared = store.prepare(&action).expect("prepare confirmation");
    let binding = action
        .confirmation_binding
        .clone()
        .expect("confirmation binding");

    let barrier = Arc::new(Barrier::new(3));
    let mut workers = Vec::new();
    for index in 0..2 {
        let root = store_root.clone();
        let confirmation_id = prepared.confirmation_id.clone();
        let barrier = Arc::clone(&barrier);
        let binding = binding.clone();
        workers.push(thread::spawn(move || {
            let store = ConfirmationStore::new(&root, "demo").expect("worker store");
            let decision = PolicyDecision {
                decision_id: format!("pol_{:032x}", index + 1),
                capability: "distribution.publish".into(),
                decision: "guarded".into(),
                effective_risk: "high".into(),
                enforced_by: "policy_enforcement_point".into(),
                reasons: Vec::new(),
                confirmation_binding: Some(binding),
            };
            barrier.wait();
            store.consume_for_decision(&confirmation_id, &decision)
        }));
    }
    barrier.wait();
    let results = workers
        .into_iter()
        .map(|worker| worker.join().expect("worker finished"))
        .collect::<Vec<_>>();
    assert_eq!(
        results.iter().filter(|result| result.is_ok()).count(),
        1,
        "exactly one consumer may atomically consume the confirmation"
    );
    assert_eq!(
        results.iter().filter(|result| result.is_err()).count(),
        1,
        "the second consumer must be rejected as replay"
    );
    assert_eq!(
        store
            .get(&prepared.confirmation_id)
            .expect("final confirmation")
            .status,
        "consumed"
    );
}

#[test]
fn non_guarded_decisions_and_invalid_ttl_are_rejected() {
    let temporary = tempdir().expect("temp root");
    let store = ConfirmationStore::new(&temporary.path().join("confirmations"), "demo")
        .expect("confirmation store");
    let allowed = PolicyDecision {
        decision_id: "pol_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa".into(),
        capability: "media.inspect".into(),
        decision: "allow".into(),
        effective_risk: "low".into(),
        enforced_by: "policy_enforcement_point".into(),
        reasons: Vec::new(),
        confirmation_binding: None,
    };
    assert!(store.prepare(&allowed).is_err());

    let guarded = PolicyDecision {
        decision_id: "pol_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb".into(),
        capability: "distribution.publish".into(),
        decision: "guarded".into(),
        effective_risk: "high".into(),
        enforced_by: "policy_enforcement_point".into(),
        reasons: Vec::new(),
        confirmation_binding: Some(format!("confirm_{}", "a".repeat(64))),
    };
    assert!(store.prepare_with_ttl(&guarded, 29).is_err());
    assert!(store.prepare_with_ttl(&guarded, 901).is_err());
}
