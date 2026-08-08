use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use agent_platform::mastering_workflow::produce_mastering_file;
use agent_platform::media::normalize_loudness;
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
            "active_project_id": "master-test",
            "projects": [{
                "project_id": "master-test",
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

fn make_dynamic_program(path: &Path, sample_rate: u32, channels: u32) {
    let source = format!("sine=frequency=997:sample_rate={sample_rate}:duration=5");
    let channels_text = channels.to_string();
    let filter = "[0:a]volume=0.25[a0];[1:a]volume=0.55[a1];[2:a]volume=0.35[a2];[3:a]volume=0.50[a3];[a0][a1][a2][a3]concat=n=4:v=0:a=1[out]";
    let status = Command::new("ffmpeg")
        .args([
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            &source,
            "-f",
            "lavfi",
            "-i",
            &source,
            "-f",
            "lavfi",
            "-i",
            &source,
            "-f",
            "lavfi",
            "-i",
            &source,
            "-filter_complex",
            filter,
            "-map",
            "[out]",
            "-ac",
            &channels_text,
            "-c:a",
            "pcm_s24le",
            path.to_str().expect("UTF-8 fixture path"),
        ])
        .status()
        .expect("ffmpeg fixture generator must start");
    assert!(status.success(), "ffmpeg fixture generator failed");
}

fn manifest_count(root: &Path) -> usize {
    let manifest: Value = serde_json::from_str(
        &fs::read_to_string(root.join("artifacts/manifest.json")).expect("artifact manifest"),
    )
    .expect("manifest JSON");
    manifest
        .as_object()
        .expect("artifact manifest must be object")
        .len()
}

fn persisted_job(root: &Path, job_id: &str) -> Value {
    serde_json::from_str(
        &fs::read_to_string(
            root.join("runtime/jobs/master-test")
                .join(format!("{job_id}.json")),
        )
        .expect("persisted job"),
    )
    .expect("persisted job JSON")
}

#[test]
fn quiet_dynamic_program_is_mastered_once_and_reused_idempotently() {
    let temporary = tempdir().expect("temp directory");
    make_test_repo(temporary.path());
    let source = temporary.path().join("quiet-dynamic.wav");
    make_dynamic_program(&source, 48_000, 2);

    let first = produce_mastering_file(
        temporary.path(),
        &source,
        Some("master-test"),
        "project",
        None,
        "music-balanced",
    )
    .expect("technical master must succeed");
    assert_eq!(first["status"], "success");
    assert_eq!(first["result"]["workflow_status"], "succeeded");
    assert_eq!(first["result"]["applied_action"], "normalize_loudness");
    assert_eq!(first["result"]["final_decision"]["action"], "preserve");
    let lufs = first["result"]["final_inspection"]["integrated_lufs"]
        .as_f64()
        .expect("final LUFS");
    let peak = first["result"]["final_inspection"]["true_peak_dbtp"]
        .as_f64()
        .expect("final true peak");
    assert!(
        (lufs + 14.0).abs() <= 0.7,
        "unexpected final LUFS: {lufs}"
    );
    assert!(
        peak <= -0.9,
        "true peak exceeds target tolerance: {peak}"
    );

    let job_id = first["result"]["job_id"]
        .as_str()
        .expect("job id")
        .to_owned();
    let artifact_id = first["result"]["master_artifact"]["artifact_id"]
        .as_str()
        .expect("master artifact id")
        .to_owned();
    let sha256 = first["result"]["master_artifact"]["sha256"]
        .as_str()
        .expect("master sha")
        .to_owned();
    let count_after_first = manifest_count(temporary.path());

    let second = produce_mastering_file(
        temporary.path(),
        &source,
        Some("master-test"),
        "project",
        None,
        "music-balanced",
    )
    .expect("idempotent repeat must succeed");
    assert_eq!(second["result"]["job_id"], job_id);
    assert_eq!(
        second["result"]["master_artifact"]["artifact_id"],
        artifact_id
    );
    assert_eq!(second["result"]["master_artifact"]["sha256"], sha256);
    assert_eq!(manifest_count(temporary.path()), count_after_first);

    let job = persisted_job(temporary.path(), &job_id);
    assert_eq!(job["status"], "succeeded");
    assert_eq!(job["attempt"], 1);
    assert_eq!(job["checkpoint"]["name"], "master_qc_complete");
}

#[test]
fn already_compliant_program_is_preserved_losslessly_without_level_change() {
    let temporary = tempdir().expect("temp directory");
    make_test_repo(temporary.path());
    let source = temporary.path().join("dynamic-source.wav");
    let compliant = temporary.path().join("already-mastered.wav");
    make_dynamic_program(&source, 48_000, 2);
    normalize_loudness(&source, &compliant, -14.0, -1.0).expect("prepare compliant fixture");

    let result = produce_mastering_file(
        temporary.path(),
        &compliant,
        Some("master-test"),
        "project",
        None,
        "music-balanced",
    )
    .expect("compliant source must pass");
    assert_eq!(result["status"], "success");
    assert_eq!(result["result"]["applied_action"], "preserve");
    assert_eq!(result["result"]["final_decision"]["action"], "preserve");
    assert_eq!(result["result"]["master_artifact"]["mime"], "audio/wav");
}

#[test]
fn unsafe_delivery_source_is_failed_for_review_without_master_artifact() {
    let temporary = tempdir().expect("temp directory");
    make_test_repo(temporary.path());
    let source = temporary.path().join("low-rate.wav");
    make_dynamic_program(&source, 32_000, 1);

    let error = produce_mastering_file(
        temporary.path(),
        &source,
        Some("master-test"),
        "project",
        None,
        "music-balanced",
    )
    .expect_err("32 kHz source must require review");
    assert!(error.to_string().contains("requires review"));

    let jobs = fs::read_dir(temporary.path().join("runtime/jobs/master-test"))
        .expect("job directory")
        .filter_map(Result::ok)
        .filter(|entry| entry.path().extension().and_then(|value| value.to_str()) == Some("json"))
        .collect::<Vec<_>>();
    assert_eq!(jobs.len(), 1);
    let job: Value =
        serde_json::from_str(&fs::read_to_string(jobs[0].path()).expect("failed job JSON"))
            .expect("failed job contract");
    assert_eq!(job["status"], "failed");
    assert_eq!(job["error"]["code"], "MASTERING_REVIEW_REQUIRED");
    assert_eq!(job["error"]["retryable"], false);

    let manifest: Value = serde_json::from_str(
        &fs::read_to_string(temporary.path().join("artifacts/manifest.json"))
            .expect("artifact manifest"),
    )
    .expect("manifest JSON");
    let artifacts = manifest.as_object().expect("artifact manifest object");
    assert_eq!(
        artifacts.len(),
        1,
        "review path should register only source"
    );
    assert!(artifacts.values().all(|artifact| {
        artifact
            .get("metadata")
            .and_then(Value::as_object)
            .and_then(|metadata| metadata.get("workflow"))
            .is_none()
    }));
}
