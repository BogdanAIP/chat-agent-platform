use std::path::{Path, PathBuf};
use std::process::Command;

use agent_platform::artifact::ArtifactStore;
use agent_platform::error::PlatformError;
use agent_platform::reaper::{
    ReaperMarkerSpec, ReaperSessionSpec, ReaperTrackSpec, authoring_command, build_driver_pack,
    render_command,
};
use tempfile::tempdir;

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
            "sine=frequency=997:sample_rate=48000:duration=1",
            "-ac",
            "2",
            path.to_str().expect("UTF-8 tone path"),
        ])
        .status()
        .expect("ffmpeg tone generator must start");
    assert!(status.success());
}

fn store_audio(source: &Path, artifact_root: PathBuf) -> (ArtifactStore, String) {
    let store = ArtifactStore::new(&artifact_root).expect("artifact store");
    let artifact = store
        .import_file(source, "stage12-test", "project")
        .expect("artifact import");
    (store, artifact.artifact_id)
}

#[test]
fn stage12_driver_is_typed_and_contains_no_shell_escape_hatch() {
    let temporary = tempdir().expect("temp directory");
    let source = temporary.path().join("lead.wav");
    make_tone(&source);
    let (store, artifact_id) = store_audio(&source, temporary.path().join("artifacts"));
    let spec = ReaperSessionSpec {
        tracks: vec![ReaperTrackSpec {
            artifact_id,
            name: "Lead \"Vocal\"".into(),
        }],
        markers: vec![ReaperMarkerSpec {
            position_seconds: 12.5,
            name: "Verse 1".into(),
        }],
        render_sample_rate_hz: 48_000,
    };
    let pack =
        build_driver_pack(&store, &spec, &temporary.path().join("reaper")).expect("driver pack");

    assert!(pack.script.contains("reaper.InsertTrackInProject"));
    assert!(pack.script.contains("reaper.InsertMedia"));
    assert!(pack.script.contains("reaper.AddProjectMarker"));
    assert!(pack.script.contains("reaper.Main_SaveProjectEx"));
    assert!(pack.script.contains("RENDER_SRATE\", 48000"));
    assert!(pack.script.contains("Lead \\\"Vocal\\\""));
    assert!(!pack.script.contains("os.execute"));
    assert!(!pack.script.contains("io.popen"));
    assert!(!pack.script.contains("Main_OnCommand("));

    let executable = Path::new(r"C:\Program Files\REAPER (x64)\reaper.exe");
    let script = temporary.path().join("driver.lua");
    let authoring = authoring_command(executable, &script);
    assert_eq!(authoring[1], "-newinst");
    assert_eq!(authoring[2], "-nosplash");
    assert_eq!(authoring[3], script.to_string_lossy());
    let rendering = render_command(executable, &pack.project_path);
    assert_eq!(rendering[1], "-newinst");
    assert_eq!(rendering[2], "-renderproject");
    assert_eq!(rendering[3], pack.project_path.to_string_lossy());
}

#[test]
fn stage12_rejects_corrupt_audio_artifact_before_reaper_execution() {
    let temporary = tempdir().expect("temp directory");
    let source = temporary.path().join("corrupt.wav");
    std::fs::write(&source, b"not a real wav").expect("corrupt fixture write");
    let (store, artifact_id) = store_audio(&source, temporary.path().join("artifacts"));
    let spec = ReaperSessionSpec {
        tracks: vec![ReaperTrackSpec {
            artifact_id,
            name: "Corrupt".into(),
        }],
        markers: Vec::new(),
        render_sample_rate_hz: 48_000,
    };
    let error = build_driver_pack(&store, &spec, &temporary.path().join("reaper"))
        .expect_err("corrupt media must fail before REAPER execution");
    assert!(matches!(error, PlatformError::Validation(_)));
}

#[test]
fn stage12_rejects_invalid_session_before_driver_generation() {
    let temporary = tempdir().expect("temp directory");
    let store = ArtifactStore::new(&temporary.path().join("artifacts")).expect("artifact store");
    let spec = ReaperSessionSpec {
        tracks: Vec::new(),
        markers: vec![ReaperMarkerSpec {
            position_seconds: -1.0,
            name: "bad".into(),
        }],
        render_sample_rate_hz: 48_000,
    };
    let error = build_driver_pack(&store, &spec, &temporary.path().join("reaper"))
        .expect_err("empty track list must fail before REAPER execution");
    assert!(matches!(error, PlatformError::Validation(_)));
}
