use std::env;
use std::fmt::Write as _;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::artifact::ArtifactStore;
use crate::error::PlatformError;

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
        project_path,
        render_path,
        completion_path,
    })
}

pub fn authoring_command(executable: &Path, script_path: &Path) -> Vec<String> {
    vec![
        executable.to_string_lossy().into_owned(),
        "-newinst".into(),
        "-nosplash".into(),
        script_path.to_string_lossy().into_owned(),
    ]
}

pub fn render_command(executable: &Path, project_path: &Path) -> Vec<String> {
    vec![
        executable.to_string_lossy().into_owned(),
        "-newinst".into(),
        "-renderproject".into(),
        project_path.to_string_lossy().into_owned(),
    ]
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
