use std::env;
use std::fmt::Write as _;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::thread;
use std::time::{Duration, Instant};

use serde::{Deserialize, Serialize};

use crate::artifact::ArtifactStore;
use crate::error::PlatformError;
use crate::media::{MediaValidation, validate_media};

const AUTHORING_TIMEOUT: Duration = Duration::from_secs(45);
const RENDER_TIMEOUT: Duration = Duration::from_secs(180);
const POLL_INTERVAL: Duration = Duration::from_millis(200);

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReaperTrackSpec {
    pub artifact_id: String,
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReaperMarkerSpec {
    pub position_seconds: f64,
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReaperSessionSpec {
    pub tracks: Vec<ReaperTrackSpec>,
    pub markers: Vec<ReaperMarkerSpec>,
    pub render_sample_rate_hz: u32,
}

#[derive(Debug, Clone, Serialize)]
pub struct ReaperDriverPack {
    pub script: String,
    pub script_path: PathBuf,
    pub project_path: PathBuf,
    pub render_path: PathBuf,
    pub completion_path: PathBuf,
}

pub fn discover_reaper() -> Result<PathBuf, PlatformError> {
    if let Some(explicit) = env::var_os("REAPER_EXE") {
        let path = PathBuf::from(explicit);
        if path.is_file() {
            return Ok(path);
        }
        return Err(PlatformError::ToolUnavailable(format!(
            "REAPER_EXE does not point to a file: {}",
            path.display()
        )));
    }

    let mut candidates = Vec::new();
    if let Some(program_files) = env::var_os("ProgramFiles") {
        let root = PathBuf::from(program_files);
        candidates.push(root.join("REAPER (x64)/reaper.exe"));
        candidates.push(root.join("REAPER/reaper.exe"));
    }
    if let Some(program_files_x86) = env::var_os("ProgramFiles(x86)") {
        candidates.push(PathBuf::from(program_files_x86).join("REAPER/reaper.exe"));
    }
    candidates
        .into_iter()
        .find(|path| path.is_file())
        .ok_or_else(|| {
            PlatformError::ToolUnavailable(
                "REAPER executable was not found; set REAPER_EXE or install REAPER in Program Files"
                    .into(),
            )
        })
}

pub fn build_driver_pack(
    store: &ArtifactStore,
    spec: &ReaperSessionSpec,
    workspace: &Path,
) -> Result<ReaperDriverPack, PlatformError> {
    validate_spec(spec)?;
    std::fs::create_dir_all(workspace)
        .map_err(|error| crate::error::io_error("cannot create REAPER workspace", error))?;
    let workspace = std::fs::canonicalize(workspace)
        .map_err(|error| crate::error::io_error("cannot resolve REAPER workspace", error))?;
    let script_path = workspace.join("driver.lua");
    let project_path = workspace.join("session.rpp");
    let render_path = workspace.join("master.wav");
    let completion_path = workspace.join("driver.complete");

    let mut script = String::from(
        "local project = 0\n\
reaper.PreventUIRefresh(1)\n\
while reaper.CountTracks(project) > 0 do\n\
  reaper.DeleteTrack(reaper.GetTrack(project, 0))\n\
end\n",
    );

    for (index, track_spec) in spec.tracks.iter().enumerate() {
        let artifact = store.get(&track_spec.artifact_id)?;
        if !artifact.mime.starts_with("audio/") {
            return Err(PlatformError::Validation(format!(
                "REAPER track source must be audio: {} is {}",
                artifact.artifact_id, artifact.mime
            )));
        }
        let validation = validate_media(Path::new(&artifact.path))?;
        if validation.audio_streams == 0 {
            return Err(PlatformError::Validation(format!(
                "REAPER track source has no audio stream: {}",
                artifact.artifact_id
            )));
        }
        let artifact_path = lua_string(&artifact.path);
        let track_name = lua_string(&track_spec.name);
        writeln!(
            script,
            "reaper.InsertTrackInProject(project, {index}, 0)\nlocal track_{index} = reaper.GetTrack(project, {index})\nif track_{index} == nil then error(\"track creation failed\") end\nreaper.GetSetMediaTrackInfo_String(track_{index}, \"P_NAME\", {track_name}, true)\nreaper.SetOnlyTrackSelected(track_{index})\nreaper.SetEditCurPos(0, false, false)\nif reaper.InsertMedia({artifact_path}, 0) <= 0 then error(\"media import failed\") end"
        )
        .expect("writing to String cannot fail");
    }

    for marker in &spec.markers {
        let marker_name = lua_string(&marker.name);
        writeln!(
            script,
            "if reaper.AddProjectMarker(project, false, {:.9}, 0, {marker_name}, -1) < 0 then error(\"marker creation failed\") end",
            marker.position_seconds
        )
        .expect("writing to String cannot fail");
    }

    let render_directory = lua_string(&workspace.to_string_lossy());
    let project_file = lua_string(&project_path.to_string_lossy());
    let completion_file = lua_string(&completion_path.to_string_lossy());
    writeln!(
        script,
        "reaper.GetSetProjectInfo(project, \"RENDER_SETTINGS\", 0, true)\nreaper.GetSetProjectInfo(project, \"RENDER_BOUNDSFLAG\", 1, true)\nreaper.GetSetProjectInfo(project, \"RENDER_CHANNELS\", 2, true)\nreaper.GetSetProjectInfo(project, \"RENDER_SRATE\", {}, true)\nreaper.GetSetProjectInfo_String(project, \"RENDER_FILE\", {render_directory}, true)\nreaper.GetSetProjectInfo_String(project, \"RENDER_PATTERN\", \"master\", true)\nreaper.GetSetProjectInfo_String(project, \"RENDER_FORMAT\", \"evaw\", true)\nreaper.GetSetProjectInfo_String(project, \"RENDER_FORMAT2\", \"\", true)\nreaper.Main_SaveProjectEx(project, {project_file}, 8)\nlocal completion = assert(io.open({completion_file}, \"w\"))\ncompletion:write(\"ok\\n\")\ncompletion:close()\nreaper.PreventUIRefresh(-1)\nreaper.UpdateArrange()",
        spec.render_sample_rate_hz
    )
    .expect("writing to String cannot fail");

    if script.contains("os.execute")
        || script.contains("io.popen")
        || script.contains("Main_OnCommand(")
    {
        return Err(PlatformError::Validation(
            "generated REAPER driver contains a forbidden execution primitive".into(),
        ));
    }

    Ok(ReaperDriverPack {
        script,
        script_path,
        project_path,
        render_path,
        completion_path,
    })
}

pub fn execute_driver_pack(
    executable: &Path,
    pack: &ReaperDriverPack,
) -> Result<MediaValidation, PlatformError> {
    std::fs::write(&pack.script_path, &pack.script)
        .map_err(|error| crate::error::io_error("cannot write REAPER driver", error))?;

    let authoring = authoring_command(executable, &pack.script_path);
    let mut authoring_process = spawn_plan(&authoring, "REAPER authoring")?;
    wait_for_marker_and_stop(
        &mut authoring_process,
        &pack.completion_path,
        AUTHORING_TIMEOUT,
        "REAPER authoring",
    )?;
    if !pack.project_path.is_file() {
        return Err(PlatformError::Validation(
            "REAPER authoring completed without saving the project".into(),
        ));
    }

    let rendering = render_command(executable, &pack.project_path);
    let mut render_process = spawn_plan(&rendering, "REAPER render")?;
    wait_for_render_and_stop(
        &mut render_process,
        &pack.render_path,
        RENDER_TIMEOUT,
        "REAPER render",
    )
}

#[must_use]
pub fn authoring_command(executable: &Path, script_path: &Path) -> Vec<String> {
    vec![
        executable.to_string_lossy().into_owned(),
        "-newinst".into(),
        "-nosplash".into(),
        script_path.to_string_lossy().into_owned(),
    ]
}

#[must_use]
pub fn render_command(executable: &Path, project_path: &Path) -> Vec<String> {
    vec![
        executable.to_string_lossy().into_owned(),
        "-newinst".into(),
        "-renderproject".into(),
        project_path.to_string_lossy().into_owned(),
    ]
}

fn spawn_plan(plan: &[String], context: &str) -> Result<Child, PlatformError> {
    let executable = plan
        .first()
        .ok_or_else(|| PlatformError::Validation(format!("{context} command is empty")))?;
    Command::new(executable)
        .args(&plan[1..])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|error| {
            if error.kind() == std::io::ErrorKind::NotFound {
                PlatformError::ToolUnavailable(format!(
                    "{context} executable is unavailable: {executable}"
                ))
            } else {
                PlatformError::Validation(format!("cannot start {context}: {error}"))
            }
        })
}

fn wait_for_marker_and_stop(
    child: &mut Child,
    marker: &Path,
    timeout: Duration,
    context: &str,
) -> Result<(), PlatformError> {
    let started = Instant::now();
    loop {
        if marker.is_file() {
            stop_child(child, context)?;
            return Ok(());
        }
        if let Some(status) = child
            .try_wait()
            .map_err(|error| PlatformError::Validation(format!("cannot poll {context}: {error}")))?
        {
            return Err(PlatformError::Validation(format!(
                "{context} exited before completion marker with status {status}"
            )));
        }
        if started.elapsed() >= timeout {
            stop_child(child, context)?;
            return Err(PlatformError::ToolTimeout(format!(
                "{context} exceeded the {} second execution limit",
                timeout.as_secs()
            )));
        }
        thread::sleep(POLL_INTERVAL);
    }
}

fn wait_for_render_and_stop(
    child: &mut Child,
    render_path: &Path,
    timeout: Duration,
    context: &str,
) -> Result<MediaValidation, PlatformError> {
    let started = Instant::now();
    let mut previous_size = None;
    let mut stable_observations = 0_u8;
    loop {
        if render_path.is_file() {
            let size = render_path
                .metadata()
                .map_err(|error| crate::error::io_error("cannot inspect REAPER render", error))?
                .len();
            if size > 0 && previous_size == Some(size) {
                stable_observations = stable_observations.saturating_add(1);
            } else {
                previous_size = Some(size);
                stable_observations = 0;
            }
            if stable_observations >= 4
                && let Ok(validation) = validate_media(render_path)
                && validation.audio_streams > 0
            {
                stop_child(child, context)?;
                return Ok(validation);
            }
        }

        if let Some(status) = child
            .try_wait()
            .map_err(|error| PlatformError::Validation(format!("cannot poll {context}: {error}")))?
        {
            if !status.success() {
                return Err(PlatformError::Validation(format!(
                    "{context} exited with status {status}"
                )));
            }
            let validation = validate_media(render_path).map_err(|error| {
                PlatformError::Validation(format!(
                    "{context} exited successfully but output validation failed: {error}"
                ))
            })?;
            if validation.audio_streams == 0 {
                return Err(PlatformError::Validation(
                    "REAPER render contains no audio stream".into(),
                ));
            }
            return Ok(validation);
        }

        if started.elapsed() >= timeout {
            stop_child(child, context)?;
            return Err(PlatformError::ToolTimeout(format!(
                "{context} exceeded the {} second execution limit",
                timeout.as_secs()
            )));
        }
        thread::sleep(POLL_INTERVAL);
    }
}

fn stop_child(child: &mut Child, context: &str) -> Result<(), PlatformError> {
    if child
        .try_wait()
        .map_err(|error| PlatformError::Validation(format!("cannot poll {context}: {error}")))?
        .is_some()
    {
        return Ok(());
    }
    if let Err(kill_error) = child.kill() {
        if child
            .try_wait()
            .map_err(|error| PlatformError::Validation(format!("cannot poll {context}: {error}")))?
            .is_none()
        {
            return Err(PlatformError::Validation(format!(
                "cannot stop {context}: {kill_error}"
            )));
        }
        return Ok(());
    }
    child
        .wait()
        .map_err(|error| PlatformError::Validation(format!("cannot reap {context}: {error}")))?;
    Ok(())
}

fn validate_spec(spec: &ReaperSessionSpec) -> Result<(), PlatformError> {
    if spec.tracks.is_empty() {
        return Err(PlatformError::Validation(
            "REAPER session requires at least one track".into(),
        ));
    }
    if !(8_000..=384_000).contains(&spec.render_sample_rate_hz) {
        return Err(PlatformError::Validation(
            "REAPER render sample rate must be between 8000 and 384000 Hz".into(),
        ));
    }
    for track in &spec.tracks {
        if track.name.trim().is_empty() || track.name.len() > 200 {
            return Err(PlatformError::Validation(
                "REAPER track name must contain 1..=200 characters".into(),
            ));
        }
    }
    for marker in &spec.markers {
        if !marker.position_seconds.is_finite() || marker.position_seconds < 0.0 {
            return Err(PlatformError::Validation(
                "REAPER marker position must be a finite non-negative number".into(),
            ));
        }
        if marker.name.trim().is_empty() || marker.name.len() > 200 {
            return Err(PlatformError::Validation(
                "REAPER marker name must contain 1..=200 characters".into(),
            ));
        }
    }
    Ok(())
}

fn lua_string(value: &str) -> String {
    let mut output = String::with_capacity(value.len() + 2);
    output.push('"');
    for character in value.chars() {
        match character {
            '\\' => output.push_str("\\\\"),
            '"' => output.push_str("\\\""),
            '\n' => output.push_str("\\n"),
            '\r' => output.push_str("\\r"),
            '\t' => output.push_str("\\t"),
            other if other.is_control() => {
                write!(&mut output, "\\x{:02x}", u32::from(other))
                    .expect("writing to String cannot fail");
            }
            other => output.push(other),
        }
    }
    output.push('"');
    output
}

#[cfg(all(test, windows))]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn completion_marker_stops_an_isolated_process() {
        let temporary = tempdir().expect("temp directory");
        let marker = temporary.path().join("complete.marker");
        let escaped = marker.to_string_lossy().replace("'", "''");
        let command = format!(
            "Start-Sleep -Milliseconds 100; Set-Content -LiteralPath '{escaped}' -Value ok; Start-Sleep -Seconds 5"
        );
        let mut child = Command::new("powershell")
            .args(["-NoProfile", "-Command", &command])
            .spawn()
            .expect("PowerShell must start");
        wait_for_marker_and_stop(&mut child, &marker, Duration::from_secs(2), "marker test")
            .expect("marker should terminate the isolated process");
        assert!(marker.is_file());
        assert!(
            child.try_wait().expect("process state").is_some(),
            "process must be stopped after completion marker"
        );
    }
}
