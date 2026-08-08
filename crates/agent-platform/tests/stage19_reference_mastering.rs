use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use agent_platform::artifact::ArtifactStore;
use agent_platform::reference_mastering::{probe_matchering, reference_master_files};
use serde_json::{Value, json};
use tempfile::tempdir;

fn source_repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root must resolve")
}

fn make_test_repo(root: &Path) {
    let config = root.join("config");
    fs::create_dir_all(&config).expect("test config directory");
    fs::write(
        config.join("projects.yaml"),
        serde_json::to_string_pretty(&json!({
            "contract_version": "projects-v1",
            "active_project_id": "reference-test",
            "projects": [{
                "project_id": "reference-test",
                "repo_root": "..",
                "local_root": "..",
                "artifact_root": "../artifacts",
                "policy": "policy.yaml"
            }]
        }))
        .expect("projects config"),
    )
    .expect("write projects config");
    fs::write(
        config.join("tools.yaml"),
        serde_json::to_string_pretty(&json!({
            "contract_version": "tools-v1",
            "capabilities": [{
                "capability": "audio.reference_master",
                "executor": "edge.python.matchering",
                "enabled": true,
                "quality": "professional",
                "reliability": "high",
                "determinism": "high",
                "base_risk": "low",
                "cost": 0,
                "fallbacks": []
            }]
        }))
        .expect("tools config"),
    )
    .expect("write tools config");
    fs::write(
        config.join("tool-lock.yaml"),
        serde_json::to_string_pretty(&json!({
            "contract_version": "tool-lock-v1",
            "selected": {"audio.reference_master": "edge.python.matchering"}
        }))
        .expect("tool lock"),
    )
    .expect("write tool lock");
    fs::write(
        config.join("capability-requirements.yaml"),
        serde_json::to_string_pretty(&json!({
            "contract_version": "capability-requirements-v1",
            "requirements": [{
                "capability": "audio.reference_master",
                "required": true,
                "required_quality": "professional",
                "execution_paths": ["edge.python.matchering"],
                "fallbacks": [],
                "acceptance": ["reference_match", "technical_delivery_qc", "artifact_sha256"]
            }]
        }))
        .expect("requirements config"),
    )
    .expect("write requirements config");
    fs::write(
        config.join("policy.yaml"),
        serde_json::to_string_pretty(&json!({
            "contract_version": "policy-v1",
            "rules": {
                "audio.reference_master": {
                    "decision": "allow",
                    "enforced_by": "matchering_edge_adapter",
                    "allowed_data_classes": ["public", "project", "private", "sensitive"],
                    "external_side_effect": false,
                    "max_cost": 0
                }
            }
        }))
        .expect("policy config"),
    )
    .expect("write policy config");
    fs::create_dir_all(root.join("scripts")).expect("scripts directory");
    fs::copy(
        source_repo_root().join("scripts/matchering_adapter.py"),
        root.join("scripts/matchering_adapter.py"),
    )
    .expect("copy Matchering adapter");
}

fn make_program(path: &Path, low_gain: f64, high_gain: f64, sample_rate: u32) {
    let low = format!("sine=frequency=220:sample_rate={sample_rate}:duration=18");
    let high = format!("sine=frequency=4200:sample_rate={sample_rate}:duration=18");
    let filter = format!(
        "[0:a]volume={low_gain}[low];[1:a]volume={high_gain}[high];[low][high]amix=inputs=2:normalize=0,tremolo=f=0.27:d=0.35[out]"
    );
    let status = Command::new("ffmpeg")
        .args([
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            &low,
            "-f",
            "lavfi",
            "-i",
            &high,
            "-filter_complex",
            &filter,
            "-map",
            "[out]",
            "-ac",
            "2",
            "-c:a",
            "pcm_s24le",
            path.to_str().expect("UTF-8 fixture path"),
        ])
        .status()
        .expect("ffmpeg fixture generator must start");
    assert!(status.success(), "ffmpeg fixture generation failed");
}

fn manifest_count(root: &Path) -> usize {
    let manifest: Value = serde_json::from_str(
        &fs::read_to_string(root.join("artifacts/manifest.json")).expect("manifest"),
    )
    .expect("manifest JSON");
    manifest.as_object().expect("manifest object").len()
}

fn artifact_path(root: &Path, artifact_id: &str) -> PathBuf {
    let store = ArtifactStore::new(&root.join("artifacts")).expect("artifact store");
    PathBuf::from(store.get(artifact_id).expect("stored artifact").path)
}

fn filtered_mean_volume_db(path: &Path, filter: &str) -> f64 {
    let audio_filter = format!("{filter},volumedetect");
    let output = Command::new("ffmpeg")
        .args(["-hide_banner", "-nostats", "-i"])
        .arg(path)
        .args(["-af", &audio_filter, "-f", "null", "-"])
        .output()
        .expect("ffmpeg spectral benchmark must start");
    assert!(output.status.success(), "ffmpeg spectral benchmark failed");
    let stderr = String::from_utf8_lossy(&output.stderr);
    stderr
        .lines()
        .find_map(|line| {
            line.split("mean_volume: ")
                .nth(1)
                .and_then(|value| value.strip_suffix(" dB"))
                .and_then(|value| value.trim().parse::<f64>().ok())
        })
        .expect("volumedetect mean_volume")
}

fn tonal_balance_db(path: &Path) -> f64 {
    let low = filtered_mean_volume_db(path, "bandpass=f=220:width_type=h:w=80");
    let high = filtered_mean_volume_db(path, "bandpass=f=4200:width_type=h:w=500");
    high - low
}

#[test]
#[ignore = "requires pinned Matchering edge runtime"]
fn matchering_reference_master_is_real_qc_valid_and_idempotent() {
    let temporary = tempdir().expect("temp directory");
    make_test_repo(temporary.path());
    let target = temporary.path().join("target.wav");
    let reference = temporary.path().join("reference.wav");
    make_program(&target, 0.22, 0.035, 48_000);
    make_program(&reference, 0.10, 0.42, 48_000);

    let probe = probe_matchering(temporary.path()).expect("Matchering probe must pass");
    assert_eq!(probe["status"], "available");
    assert_eq!(probe["engine"], "matchering");

    let target_tonal_balance = tonal_balance_db(&target);
    let reference_tonal_balance = tonal_balance_db(&reference);
    let tonal_distance_before = (target_tonal_balance - reference_tonal_balance).abs();

    let first = reference_master_files(
        temporary.path(),
        &target,
        &reference,
        Some("reference-test"),
        "project",
        None,
        "music-balanced",
    )
    .expect("reference master must succeed");
    assert_eq!(first["status"], "success");
    assert_eq!(first["result"]["workflow_status"], "succeeded");
    assert_eq!(first["result"]["engine"], "matchering");
    assert_eq!(first["result"]["final_decision"]["action"], "preserve");
    assert_eq!(first["result"]["final_decision"]["requires_review"], false);
    assert_eq!(
        first["result"]["final_inspection"]["sample_rate_hz"],
        48_000
    );
    assert_eq!(first["result"]["final_inspection"]["channels"], 2);
    let final_lufs = first["result"]["final_inspection"]["integrated_lufs"]
        .as_f64()
        .expect("final LUFS");
    assert!(
        (final_lufs + 14.0).abs() <= 0.7,
        "unexpected final LUFS: {final_lufs}"
    );

    let before = first["result"]["reference_similarity"]["before_lu"]
        .as_f64()
        .expect("before reference distance");
    let after = first["result"]["reference_similarity"]["after_lu"]
        .as_f64()
        .expect("after reference distance");
    assert!(
        after < before,
        "Matchering did not improve loudness proximity: before={before}, after={after}"
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
        .expect("master SHA-256")
        .to_owned();

    let master_path = artifact_path(temporary.path(), &artifact_id);
    let master_tonal_balance = tonal_balance_db(&master_path);
    let tonal_distance_after = (master_tonal_balance - reference_tonal_balance).abs();
    assert!(
        tonal_distance_after < tonal_distance_before,
        "Matchering did not improve tonal balance proximity: before={tonal_distance_before:.2} dB, after={tonal_distance_after:.2} dB"
    );

    let count = manifest_count(temporary.path());
    let second = reference_master_files(
        temporary.path(),
        &target,
        &reference,
        Some("reference-test"),
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
    assert_eq!(manifest_count(temporary.path()), count);
}

#[test]
#[ignore = "requires pinned Matchering edge runtime"]
fn invalid_target_is_rejected_before_reference_processing() {
    let temporary = tempdir().expect("temp directory");
    make_test_repo(temporary.path());
    let target = temporary.path().join("low-rate-target.wav");
    let reference = temporary.path().join("reference.wav");
    make_program(&target, 0.2, 0.05, 32_000);
    make_program(&reference, 0.1, 0.4, 48_000);

    let error = reference_master_files(
        temporary.path(),
        &target,
        &reference,
        Some("reference-test"),
        "project",
        None,
        "music-balanced",
    )
    .expect_err("32 kHz target must fail the validated input gate");
    assert!(error.to_string().contains("44.1 kHz"));

    let jobs = fs::read_dir(temporary.path().join("runtime/jobs/reference-test"))
        .expect("job directory")
        .filter_map(Result::ok)
        .filter(|entry| entry.path().extension().and_then(|value| value.to_str()) == Some("json"))
        .collect::<Vec<_>>();
    assert_eq!(jobs.len(), 1);
    let job: Value = serde_json::from_str(&fs::read_to_string(jobs[0].path()).expect("failed job"))
        .expect("job JSON");
    assert_eq!(job["status"], "failed");
    assert_eq!(job["error"]["retryable"], false);
}
