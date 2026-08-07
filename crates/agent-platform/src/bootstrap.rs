use std::fs;
use std::path::Path;

use serde_json::{Map, Value, json};

use crate::binding::resolve_project;
use crate::config::load_json_yaml;
use crate::error::{PlatformError, io_error};

const MINIMAL_CONTEXT: [&str; 3] = ["CURRENT_STATE.md", "ARCHITECTURE.md", "CONSTRAINTS.md"];

pub fn build_context(
    repo_root: &Path,
    project_id: Option<&str>,
    capability: &str,
) -> Result<Value, PlatformError> {
    let binding = resolve_project(repo_root, project_id)?;
    let requirements = load_json_yaml(&repo_root.join("config/capability-requirements.yaml"))?;
    let matches: Vec<_> = requirements
        .get("requirements")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|item| item.get("capability").and_then(Value::as_str) == Some(capability))
        .collect();
    if matches.len() != 1 {
        return Err(PlatformError::Validation(format!(
            "capability requirement must resolve exactly once: {capability:?}; matches={}",
            matches.len()
        )));
    }
    let mut context = Map::new();
    for filename in MINIMAL_CONTEXT {
        let path = repo_root.join("project-context").join(filename);
        let text = fs::read_to_string(&path).map_err(|error| {
            io_error(
                format!(
                    "required bootstrap context is unavailable: {}",
                    path.display()
                ),
                error,
            )
        })?;
        context.insert(filename.into(), Value::String(text));
    }
    let runtime_path = repo_root.join("runtime/capability-profile.json");
    let runtime = if runtime_path.exists() {
        let profile = load_json_yaml(&runtime_path)?;
        if profile.get("project_id").and_then(Value::as_str) == Some(&binding.project_id) {
            capability_from_profile(&profile, capability)
        } else {
            json!({"status": "unknown", "reason": "runtime profile belongs to another project"})
        }
    } else {
        json!({"status": "unknown", "reason": "runtime profile has not been generated"})
    };
    let skill_name = if capability == "media.inspect" {
        "media-inspection".to_owned()
    } else {
        capability.replace('.', "-")
    };
    let skill = repo_root
        .join("project-skills")
        .join(skill_name)
        .join("SKILL.md");
    Ok(json!({
        "contract_version": "bootstrap-v1",
        "project": {
            "project_id": binding.project_id,
            "repo_root": binding.repo_root,
            "artifact_root": binding.artifact_root
        },
        "capability_requirement": matches[0],
        "runtime_capability": runtime,
        "minimal_context": context,
        "relevant_skill": if skill.exists() { Some(skill) } else { None }
    }))
}

fn capability_from_profile(profile: &Value, capability: &str) -> Value {
    profile
        .get("capabilities")
        .and_then(|value| value.get(capability))
        .cloned()
        .unwrap_or_else(|| json!({"status": "unknown", "reason": "capability has not been probed"}))
}
