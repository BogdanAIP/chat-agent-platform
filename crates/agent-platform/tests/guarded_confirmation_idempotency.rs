use agent_platform::confirmation::ConfirmationStore;
use agent_platform::policy::PolicyDecision;
use chrono::DateTime;
use tempfile::tempdir;

fn guarded(decision_id: &str) -> PolicyDecision {
    PolicyDecision {
        decision_id: decision_id.into(),
        capability: "distribution.publish".into(),
        decision: "guarded".into(),
        effective_risk: "high".into(),
        enforced_by: "policy_enforcement_point".into(),
        reasons: Vec::new(),
        confirmation_binding: Some(format!("confirm_{}", "a".repeat(64))),
    }
}

#[test]
fn repeated_prepare_reuses_one_active_confirmation_without_extending_ttl() {
    let temporary = tempdir().expect("temp root");
    let store = ConfirmationStore::new(&temporary.path().join("confirmations"), "demo")
        .expect("confirmation store");

    let first = store
        .prepare_with_ttl(&guarded("pol_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"), 600)
        .expect("first prepare");
    let repeated = store
        .prepare_with_ttl(&guarded("pol_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"), 900)
        .expect("idempotent retry");
    assert_eq!(first.confirmation_id, repeated.confirmation_id);
    assert_eq!(
        first.expires_at, repeated.expires_at,
        "retry with a longer TTL must never extend an existing confirmation"
    );

    let shortened = store
        .prepare_with_ttl(&guarded("pol_cccccccccccccccccccccccccccccccc"), 30)
        .expect("shorter retry");
    assert_eq!(first.confirmation_id, shortened.confirmation_id);
    let original_expiry = DateTime::parse_from_rfc3339(&first.expires_at).expect("first expiry");
    let shortened_expiry =
        DateTime::parse_from_rfc3339(&shortened.expires_at).expect("shortened expiry");
    assert!(
        shortened_expiry < original_expiry,
        "retry may only tighten, never expand, the confirmation window"
    );

    let fresh_decision = guarded("pol_dddddddddddddddddddddddddddddddd");
    store
        .consume_for_decision(&first.confirmation_id, &fresh_decision)
        .expect("consume active confirmation");
    let next = store
        .prepare(&guarded("pol_eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"))
        .expect("new confirmation after consume");
    assert_ne!(first.confirmation_id, next.confirmation_id);
}
