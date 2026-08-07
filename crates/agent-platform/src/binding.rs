use std::fs;
use std::path::{Path, PathBuf};

use crate::config::load_json_yaml;
use crate::error::{PlatformError, io_error};

#[derive(Debug, Clone)]
pub struct ProjectBinding {
    pub project_id: String,
    pub repo_root: PathBuf,
    pub local_root: PathBuf,
    pub artifact_root: PathBuf,
    pub policy_path: PathBuf,
}

pub fn resolve_project(
    repo_root: &Path,
    project_id: Option<&str>,
) -> Result<ProjectBinding, PlatformError> {
    let repo_root = fs::canonicalize(repo_root)
        .map_err(|error| io_error("cannot resolve repository root", error))?;
    let config_path = repo_root.join("config/projects.yaml");
    let config = load_json_yaml(&config_path)?;
    let selected = project_id
        .map(ToOwned::to_owned)
        .or_else(|| {
            config
                .get("active_project_id")
                .and_then(|value| value.as_str())
                .map(ToOwned::to_owned)
        })
        .ok_or_else(|| PlatformError::Binding("no explicit or active project id".into()))?;

    let projects = config
        .get("projects")
        .and_then(|value| value.as_array())
        .ok_or_else(|| PlatformError::Binding("projects config must contain an array".into()))?;
    let matches: Vec<_> = projects
        .iter()
        .filter(|item| item.get("project_id").and_then(|value| value.as_str()) == Some(&selected))
        .collect();
    if matches.len() != 1 {
        return Err(PlatformError::Binding(format!(
            "project binding must resolve exactly once: {selected:?}; matches={}",
            matches.len()
        )));
    }
    let item = matches[0];
    let config_dir = config_path
        .parent()
        .ok_or_else(|| PlatformError::Binding("projects config has no parent".into()))?;
    let resolve = |field: &str| -> Result<PathBuf, PlatformError> {
        let relative = item
            .get(field)
            .and_then(|value| value.as_str())
            .ok_or_else(|| PlatformError::Binding(format!("binding is missing {field}")))?;
        fs::canonicalize(config_dir.join(relative))
            .map_err(|error| io_error(format!("cannot resolve binding field {field}"), error))
    };
    let bound_repo = resolve("repo_root")?;
    if bound_repo != repo_root {
        return Err(PlatformError::Binding(format!(
            "bound repository {} does not match active repository {}",
            bound_repo.display(),
            repo_root.display()
        )));
    }
    let artifact_relative = item
        .get("artifact_root")
        .and_then(|value| value.as_str())
        .ok_or_else(|| PlatformError::Binding("binding is missing artifact_root".into()))?;
    let artifact_root = config_dir.join(artifact_relative);
    fs::create_dir_all(&artifact_root)
        .map_err(|error| io_error("cannot create artifact root", error))?;
    let artifact_root = fs::canonicalize(artifact_root)
        .map_err(|error| io_error("cannot resolve artifact root", error))?;
    let policy_relative = item
        .get("policy")
        .and_then(|value| value.as_str())
        .ok_or_else(|| PlatformError::Binding("binding is missing policy".into()))?;

    Ok(ProjectBinding {
        project_id: selected,
        repo_root: bound_repo,
        local_root: resolve("local_root")?,
        artifact_root,
        policy_path: config_dir.join(policy_relative),
    })
}
