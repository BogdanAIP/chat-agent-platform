use std::fs;
use std::path::Path;
use std::process::Command;

use serde_json::{Value, json};
use tempfile::tempdir;

fn make_bound_repo(root: &Path) {
    let config = root.join("config");
    fs::create_dir_all(&config).expect("config directory");
    let projects = json!({
        "contract_version": "projects-v1",
        "active_project_id": "process-test",
        "projects": [{
            "project_id": "process-test",
            "repo_root": "..",
            "local_root": "..",
            "artifact_root": "../artifacts",
            "policy": "policy.yaml"
        }]
    });
    fs::write(
        config.join("projects.yaml"),
        serde_json::to_string_pretty(&projects).expect("projects JSON"),
    )
    .expect("projects config");
}

fn run(root: &Path, args: &[&str]) -> Value {
    let output = Command::new(env!("CARGO_BIN_EXE_agent-platform"))
        .arg("--repo-root")
        .arg(root)
        .args(args)
        .output()
        .expect("agent-platform process must start");
    assert!(
        output.status.success(),
        "agent-platform failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    serde_json::from_slice(&output.stdout).expect("command must return JSON")
}

#[test]
fn job_state_survives_separate_binary_processes() {
    let temporary = tempdir().expect("temp directory");
    make_bound_repo(temporary.path());

    let begun = run(
        temporary.path(),
        &[
            "job-begin",
            "--project-id",
            "process-test",
            "--capability",
            "audio.mastering_produce",
            "--idempotency-key",
            "process-e2e",
        ],
    );
    let job_id = begun["job_id"].as_str().expect("job id").to_owned();
    assert_eq!(begun["status"], "queued");

    let duplicate = run(
        temporary.path(),
        &[
            "job-begin",
            "--project-id",
            "process-test",
            "--capability",
            "audio.mastering_produce",
            "--idempotency-key",
            "process-e2e",
        ],
    );
    assert_eq!(duplicate["job_id"], job_id);

    let running = run(
        temporary.path(),
        &["job-resume", "--project-id", "process-test", "--job-id", &job_id],
    );
    assert_eq!(running["status"], "running");

    run(
        temporary.path(),
        &[
            "job-checkpoint",
            "--project-id",
            "process-test",
            "--job-id",
            &job_id,
            "--name",
            "analysis_complete",
            "--data-json",
            r#"{"source":"art_deadbeef"}"#,
        ],
    );

    let reopened = run(
        temporary.path(),
        &["job-get", "--project-id", "process-test", "--job-id", &job_id],
    );
    assert_eq!(reopened["checkpoint"]["name"], "analysis_complete");
    assert_eq!(reopened["checkpoint"]["data"]["source"], "art_deadbeef");

    run(
        temporary.path(),
        &[
            "job-fail",
            "--project-id",
            "process-test",
            "--job-id",
            &job_id,
            "--error-json",
            r#"{"code":"TOOL_TIMEOUT","message":"retry","retryable":true}"#,
        ],
    );
    let retried = run(
        temporary.path(),
        &["job-resume", "--project-id", "process-test", "--job-id", &job_id],
    );
    assert_eq!(retried["status"], "running");
    assert_eq!(retried["attempt"], 2);
    assert_eq!(retried["checkpoint"]["name"], "analysis_complete");

    run(
        temporary.path(),
        &[
            "job-succeed",
            "--project-id",
            "process-test",
            "--job-id",
            &job_id,
            "--result-json",
            r#"{"artifact_id":"art_cafebabe"}"#,
        ],
    );
    let completed = run(
        temporary.path(),
        &["job-get", "--project-id", "process-test", "--job-id", &job_id],
    );
    assert_eq!(completed["status"], "succeeded");
    assert_eq!(completed["result"]["artifact_id"], "art_cafebabe");

    let persisted = temporary
        .path()
        .join("runtime/jobs/process-test")
        .join(format!("{job_id}.json"));
    assert!(persisted.is_file());
}
