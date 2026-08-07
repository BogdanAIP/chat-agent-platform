use std::path::{Path, PathBuf};
use std::process::Command;

use agent_platform::error::PlatformError;
use agent_platform::media_ops::{
    convert_audio_file, extract_audio_file, mux_media_files, normalize_audio_file,
    validate_media_file,
};
use tempfile::tempdir;

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root must resolve")
}

fn make_tone(path: &Path) {
    let status = Command::new("ffmpeg")
        .args([
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=997:sample_rate=48000:duration=2",
            "-ac",
            "2",
            path.to_str().expect("UTF-8 tone path"),
        ])
        .status()
        .expect("ffmpeg tone generator must start");
    assert!(status.success());
}

fn make_video(path: &Path) {
    let status = Command::new("ffmpeg")
        .args([
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=160x120:r=25",
            "-t",
            "2",
            "-an",
            "-c:v",
            "mpeg4",
            "-pix_fmt",
            "yuv420p",
            path.to_str().expect("UTF-8 video path"),
        ])
        .status()
        .expect("ffmpeg video generator must start");
    assert!(status.success());
}

#[test]
fn stage11_audio_operations_are_typed_and_technically_validated() {
    let temporary = tempdir().expect("temp directory");
    let tone = temporary.path().join("tone.wav");
    make_tone(&tone);
    let root = repo_root();

    let validation = validate_media_file(&root, &tone, Some("demo"), "project", None)
        .expect("media validation must pass");
    assert_eq!(validation["status"], "success");
    assert_eq!(validation["result"]["validation"]["audio_streams"], 1);

    let converted = convert_audio_file(
        &root,
        &tone,
        Some("demo"),
        "project",
        None,
        "flac",
    )
    .expect("lossless conversion must pass");
    assert_eq!(converted["status"], "success");
    assert_eq!(converted["result"]["format"], "flac");
    assert_eq!(converted["artifact_refs"][0]["mime"], "audio/flac");

    let extracted = extract_audio_file(&root, &tone, Some("demo"), "project", None)
        .expect("audio extraction must pass");
    assert_eq!(extracted["status"], "success");
    assert_eq!(extracted["artifact_refs"][0]["mime"], "audio/wav");

    let normalized = normalize_audio_file(
        &root,
        &tone,
        Some("demo"),
        "project",
        None,
        -18.0,
        -1.0,
    )
    .expect("two-pass loudness normalization must pass");
    let measured = normalized["result"]["inspection"]["integrated_lufs"]
        .as_f64()
        .expect("normalized LUFS must be measured");
    assert!((measured + 18.0).abs() <= 0.7);
    let peak = normalized["result"]["inspection"]["true_peak_dbtp"]
        .as_f64()
        .expect("normalized true peak must be measured");
    assert!(peak <= -0.8);
}

#[test]
fn stage11_mux_requires_and_produces_audio_and_video_streams() {
    let temporary = tempdir().expect("temp directory");
    let tone = temporary.path().join("tone.wav");
    let video = temporary.path().join("video.mp4");
    make_tone(&tone);
    make_video(&video);

    let result = mux_media_files(
        &repo_root(),
        &video,
        &tone,
        Some("demo"),
        "project",
        None,
    )
    .expect("typed mux must pass");
    assert_eq!(result["status"], "success");
    assert_eq!(result["result"]["validation"]["audio_streams"], 1);
    assert_eq!(result["result"]["validation"]["video_streams"], 1);
    assert_eq!(result["result"]["container"], "matroska");
}

#[test]
fn stage11_rejects_unapproved_conversion_format_before_execution() {
    let temporary = tempdir().expect("temp directory");
    let tone = temporary.path().join("tone.wav");
    make_tone(&tone);
    let error = convert_audio_file(
        &repo_root(),
        &tone,
        Some("demo"),
        "project",
        None,
        "aac",
    )
    .expect_err("unapproved format must be rejected");
    assert!(matches!(error, PlatformError::Validation(_)));
}
