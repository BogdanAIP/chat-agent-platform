use std::fs;
use std::sync::Arc;
use std::thread;

use agent_platform::job::JobStore;
use serde_json::{Map, Value, json};
use tempfile::tempdir;

fn object(value: Value) -> Map<String, Value> {
    serde_json::from_value(value).expect("test object must decode")
}

#[test]
fn idempotency_reuses_one_job_and_rejects_capability_collision() {
    let temporary = tempdir().expect("temp directory");
    let store = JobStore::new(temporary.path()).expect("job store");

    let first = store
        .begin("audio.mastering_produce", "same-request")
        .expect("first job");
    let second = store
        .begin("audio.mastering_produce", "same-request")
        .expect("idempotent lookup");
    assert_eq!(first.job_id, second.job_id);
    assert_eq!(second.status, "queued");

    let collision = store
        .begin("media.mux", "same-request")
        .expect_err("same key must not bind to another capability");
    assert!(collision.to_string().contains("already bound"));
}

#[test]
fn concurrent_idempotent_begin_produces_one_job() {
    let temporary = tempdir().expect("temp directory");
    let store = Arc::new(JobStore::new(temporary.path()).expect("job store"));
    let mut workers = Vec::new();
    for _ in 0..8 {
        let store = Arc::clone(&store);
        workers.push(thread::spawn(move || {
            store
                .begin("audio.mastering_produce", "concurrent-request")
                .expect("idempotent concurrent begin")
                .job_id
        }));
    }
    let ids: Vec<String> = workers
        .into_iter()
        .map(|worker| worker.join().expect("worker must finish"))
        .collect();
    assert!(ids.iter().all(|job_id| job_id == &ids[0]));
    let persisted = fs::read_dir(temporary.path())
        .expect("job directory")
        .filter_map(Result::ok)
        .filter(|entry| entry.path().extension().and_then(|value| value.to_str()) == Some("json"))
        .count();
    assert_eq!(persisted, 1);
}

#[test]
fn checkpoint_retry_and_result_survive_new_store_instances() {
    let temporary = tempdir().expect("temp directory");
    let job_id = {
        let store = JobStore::new(temporary.path()).expect("job store");
        let queued = store
            .begin("audio.mastering_produce", "persistent-request")
            .expect("begin");
        let running = store.resume(&queued.job_id).expect("start queued job");
        assert_eq!(running.status, "running");
        let checkpointed = store
            .checkpoint(
                &queued.job_id,
                "analysis_complete",
                object(json!({"source_artifact": "art_deadbeef"})),
            )
            .expect("checkpoint");
        assert_eq!(
            checkpointed
                .checkpoint
                .as_ref()
                .map(|checkpoint| checkpoint.name.as_str()),
            Some("analysis_complete")
        );
        let failed = store
            .fail(
                &queued.job_id,
                object(json!({
                    "code": "TOOL_TIMEOUT",
                    "message": "transient renderer timeout",
                    "retryable": true
                })),
            )
            .expect("retryable failure");
        assert_eq!(failed.status, "failed");
        queued.job_id
    };

    let reopened = JobStore::new(temporary.path()).expect("reopened store");
    let persisted = reopened.get(&job_id).expect("persisted failed job");
    assert_eq!(persisted.attempt, 1);
    assert_eq!(
        persisted
            .checkpoint
            .as_ref()
            .map(|checkpoint| checkpoint.name.as_str()),
        Some("analysis_complete")
    );

    let retried = reopened.resume(&job_id).expect("retry persisted job");
    assert_eq!(retried.status, "running");
    assert_eq!(retried.attempt, 2);
    assert!(retried.error.is_none());
    assert_eq!(
        retried
            .checkpoint
            .as_ref()
            .map(|checkpoint| checkpoint.name.as_str()),
        Some("analysis_complete")
    );
    reopened
        .succeed(&job_id, object(json!({"render_artifact": "art_cafebabe"})))
        .expect("success");

    let final_store = JobStore::new(temporary.path()).expect("new session store");
    let completed = final_store.get(&job_id).expect("completed job");
    assert_eq!(completed.status, "succeeded");
    assert_eq!(completed.attempt, 2);
    assert_eq!(
        completed
            .result
            .as_ref()
            .and_then(|result| result.get("render_artifact"))
            .and_then(Value::as_str),
        Some("art_cafebabe")
    );
}

#[test]
fn terminal_and_non_retryable_transitions_are_denied() {
    let temporary = tempdir().expect("temp directory");
    let store = JobStore::new(temporary.path()).expect("job store");

    let completed = store
        .begin("audio.mastering_produce", "complete-request")
        .expect("begin");
    store.resume(&completed.job_id).expect("start");
    store
        .succeed(&completed.job_id, object(json!({"ok": true})))
        .expect("success");
    assert!(store.resume(&completed.job_id).is_err());
    assert!(store.cancel(&completed.job_id).is_err());

    let failed = store
        .begin("audio.mastering_produce", "fatal-request")
        .expect("begin fatal");
    store.resume(&failed.job_id).expect("start fatal");
    store
        .fail(
            &failed.job_id,
            object(json!({
                "code": "VALIDATION_FAILED",
                "message": "source is invalid",
                "retryable": false
            })),
        )
        .expect("fatal failure");
    assert!(store.resume(&failed.job_id).is_err());
}

#[test]
fn corrupt_persisted_state_fails_closed_and_is_preserved() {
    let temporary = tempdir().expect("temp directory");
    let corrupt = temporary.path().join("job_deadbeef.json");
    fs::write(&corrupt, "{ definitely-not-json").expect("corrupt test state must be written");
    let store = JobStore::new(temporary.path()).expect("job store");

    let error = store
        .begin("audio.mastering_produce", "new-request")
        .expect_err("corrupt state must stop idempotency scan");
    assert!(error.to_string().contains("corrupt"));
    assert!(corrupt.is_file(), "corrupt evidence must not be deleted");
}
