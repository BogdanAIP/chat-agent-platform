use std::path::{Path, PathBuf};
use std::process::Command;

use agent_platform::media_ops::analyze_mastering_file;
use tempfile::tempdir;

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root must resolve")
}

fn make_program(path: &Path, volume: f64, sample_rate: u32, channels: u32, duration: u32) {
    let source = format!("sine=frequency=997:sample_rate={sample_rate}:duration={duration}");
    let filter = format!("volume={volume},tremolo=f=0.25:d=0.55");
    let channels_text = channels.to_string();
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
            "-af",
            &filter,
            "-ac",
            &channels_text,
            "-c:a",
            "pcm_s24le",
            path.to_str().expect("UTF-8 fixture path"),
        ])
        .status()
        .expect("ffmpeg benchmark generator must start");
    assert!(status.success(), "ffmpeg benchmark generator failed");
}

fn has_flag(result: &serde_json::Value, expected: &str) -> bool {
    result["result"]["quality_flags"]
        .as_array()
        .expect("quality_flags must be an array")
        .iter()
        .any(|flag| flag.as_str() == Some(expected))
}

#[test]
fn stage13_benchmark_corpus_exercises_real_ebu_r128_analysis() {
    let temporary = tempdir().expect("temp directory");
    let root = repo_root();

    let cases = [
        ("quiet", 0.25, 48_000, 2, 12),
        ("nominal", 2.0, 48_000, 2, 12),
        ("hot", 7.0, 48_000, 2, 12),
        ("lowrate_mono", 1.0, 32_000, 1, 12),
    ];

    let mut results = Vec::new();
    for (name, volume, sample_rate, channels, duration) in cases {
        let fixture = temporary.path().join(format!("{name}.wav"));
        make_program(&fixture, volume, sample_rate, channels, duration);
        let result = analyze_mastering_file(
            &root,
            &fixture,
            Some("demo"),
            "project",
            None,
            "music-balanced",
        )
        .expect("mastering analysis must pass");
        assert_eq!(result["status"], "success");
        assert_eq!(result["result"]["target"]["profile"], "music-balanced");
        assert!(result["result"]["source"]["integrated_lufs"].is_number());
        assert!(result["result"]["source"]["true_peak_dbtp"].is_number());
        assert_eq!(result["artifact_refs"].as_array().map(Vec::len), Some(1));
        results.push((name, result));
    }

    let quiet = &results
        .iter()
        .find(|(name, _)| *name == "quiet")
        .expect("quiet result")
        .1;
    assert!(has_flag(quiet, "loudness_outside_target_tolerance"));

    let hot = &results
        .iter()
        .find(|(name, _)| *name == "hot")
        .expect("hot result")
        .1;
    assert!(has_flag(hot, "loudness_outside_target_tolerance"));

    let lowrate = &results
        .iter()
        .find(|(name, _)| *name == "lowrate_mono")
        .expect("low-rate result")
        .1;
    assert!(has_flag(lowrate, "sample_rate_below_delivery_floor"));
    assert_eq!(lowrate["result"]["requires_review"], true);
    assert_eq!(lowrate["result"]["auto_mastering_allowed"], false);
}

#[test]
fn stage13_profiles_change_target_without_changing_measured_source() {
    let temporary = tempdir().expect("temp directory");
    let fixture = temporary.path().join("profile.wav");
    make_program(&fixture, 1.5, 48_000, 2, 12);
    let root = repo_root();

    let balanced = analyze_mastering_file(
        &root,
        &fixture,
        Some("demo"),
        "project",
        None,
        "music-balanced",
    )
    .expect("balanced analysis");
    let loud = analyze_mastering_file(&root, &fixture, Some("demo"), "project", None, "music-loud")
        .expect("loud analysis");

    assert_eq!(
        balanced["result"]["source"]["integrated_lufs"],
        loud["result"]["source"]["integrated_lufs"]
    );
    assert_eq!(balanced["result"]["target"]["target_lufs"], -14.0);
    assert_eq!(loud["result"]["target"]["target_lufs"], -10.0);
}
