use std::path::Path;
use std::{fs, path::PathBuf};

use chrono::Utc;
use serde_json::{Map, Value, json};
use uuid::Uuid;

use crate::artifact::{Artifact, ArtifactStore};
use crate::binding::{ProjectBinding, resolve_project};
use crate::contracts;
use crate::error::PlatformError;
use crate::media::{inspect_media, tool_version};
use crate::policy::{PolicyDecision, PolicyEnforcementPoint};

pub fn inspect_file(
    repo_root: &Path,
    file_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
) -> Result<Value, PlatformError> {
    let request_id = format!("req_{}", Uuid::new_v4().simple());
    let request = json!({
        "contract_version": "tool-v1",
        "request_id": request_id,
        "capability": "media.inspect",
        "idempotency_key": null,
        "requested_risk_hint": requested_risk_hint,
        "cost_limit": 0,
        "artifact_refs": [],
        "parameters": {
            "source_name": file_path.file_name().map_or_else(String::new, |value| value.to_string_lossy().into_owned()),
            "data_class": data_class
        }
    });
    contracts::validate(&request, "tool-request-v1.schema.json")?;
    let binding = resolve_project(repo_root, project_id)?;
    let parameters = request
        .get("parameters")
        .cloned()
        .unwrap_or_else(|| json!({}));
    let policy = PolicyEnforcementPoint::load(&binding.policy_path)?.evaluate(
        "media.inspect",
        &parameters,
        data_class,
        requested_risk_hint,
    )?;
    let store = ArtifactStore::new(&binding.artifact_root)?;
    let artifact = store.import_file(file_path, "media.inspect", data_class)?;
    complete_inspection(&binding, &store, artifact, &request_id, policy)
}

pub fn inspect_artifact(
    repo_root: &Path,
    artifact_id: &str,
    project_id: Option<&str>,
    requested_risk_hint: Option<&str>,
) -> Result<Value, PlatformError> {
    let request_id = format!("req_{}", Uuid::new_v4().simple());
    let binding = resolve_project(repo_root, project_id)?;
    let store = ArtifactStore::new(&binding.artifact_root)?;
    let artifact = store.get(artifact_id)?;
    let request = json!({
        "contract_version": "tool-v1",
        "request_id": request_id,
        "capability": "media.inspect",
        "idempotency_key": null,
        "requested_risk_hint": requested_risk_hint,
        "cost_limit": 0,
        "artifact_refs": [{"artifact_id": artifact.artifact_id, "sha256": artifact.sha256}],
        "parameters": {"artifact_id": artifact_id, "data_class": artifact.data_class}
    });
    contracts::validate(&request, "tool-request-v1.schema.json")?;
    let policy = PolicyEnforcementPoint::load(&binding.policy_path)?.evaluate(
        "media.inspect",
        request
            .get("parameters")
            .ok_or_else(|| PlatformError::Validation("inspection parameters are missing".into()))?,
        &artifact.data_class,
        requested_risk_hint,
    )?;
    complete_inspection(&binding, &store, artifact, &request_id, policy)
}

fn complete_inspection(
    binding: &ProjectBinding,
    store: &ArtifactStore,
    mut artifact: Artifact,
    request_id: &str,
    policy: PolicyDecision,
) -> Result<Value, PlatformError> {
    contracts::validate(
        &serde_json::to_value(&policy).map_err(|error| {
            PlatformError::Validation(format!("cannot serialize policy decision: {error}"))
        })?,
        "policy-decision-v1.schema.json",
    )?;
    let inspection = inspect_media(Path::new(&artifact.path))?;
    let metadata: Map<String, Value> = serde_json::to_value(&inspection)
        .map_err(|error| {
            PlatformError::Validation(format!("cannot serialize inspection: {error}"))
        })?
        .as_object()
        .cloned()
        .ok_or_else(|| {
            PlatformError::Validation("inspection must serialize as an object".into())
        })?;
    store.update_metadata(&mut artifact, metadata)?;
    let result = json!({
        "request_id": request_id,
        "status": "success",
        "result": inspection,
        "artifact_refs": [{
            "artifact_id": artifact.artifact_id,
            "sha256": artifact.sha256,
            "data_class": artifact.data_class
        }],
        "provenance": {
            "capability": "media.inspect",
            "executor": "rust.local.ffmpeg",
            "project_id": binding.project_id,
            "validated": true
        },
        "policy_decision_id": policy.decision_id,
        "error": null
    });
    contracts::validate(&result, "tool-v1.schema.json")?;
    Ok(result)
}

pub fn diagnose(repo_root: &Path, project_id: Option<&str>) -> Result<Value, PlatformError> {
    let binding = resolve_project(repo_root, project_id)?;
    Ok(json!({
        "status": "available",
        "project_id": binding.project_id,
        "repo_root": binding.repo_root,
        "local_root": binding.local_root,
        "artifact_root": binding.artifact_root,
        "rust": env!("CARGO_PKG_RUST_VERSION"),
        "ffmpeg": tool_version("ffmpeg")?,
        "ffprobe": tool_version("ffprobe")?
    }))
}

pub fn write_runtime_profile(
    repo_root: &Path,
    project_id: Option<&str>,
) -> Result<(PathBuf, Value), PlatformError> {
    let binding = resolve_project(repo_root, project_id)?;
    let ffmpeg = tool_version("ffmpeg")?;
    let ffprobe = tool_version("ffprobe")?;
    let profile = json!({
        "contract_version": "runtime-capability-profile-v1",
        "verified_at": Utc::now().to_rfc3339(),
        "surface": "local_windows_rust",
        "project_id": binding.project_id,
        "system": std::env::consts::OS,
        "rust": env!("CARGO_PKG_RUST_VERSION"),
        "capabilities": {
            "media.inspect": {
                "status": "available",
                "execution_path": "rust.local.ffmpeg",
                "tools": {
                    "ffmpeg": {"available": true, "version": ffmpeg},
                    "ffprobe": {"available": true, "version": ffprobe}
                }
            }
        },
        "binding": {
            "repo_root": binding.repo_root,
            "local_root": binding.local_root,
            "artifact_root": binding.artifact_root
        }
    });
    let output = repo_root.join("runtime/capability-profile.json");
    if let Some(parent) = output.parent() {
        fs::create_dir_all(parent).map_err(|error| {
            crate::error::io_error("cannot create runtime profile directory", error)
        })?;
    }
    let text = serde_json::to_string_pretty(&profile).map_err(|error| {
        PlatformError::Validation(format!("cannot serialize runtime profile: {error}"))
    })?;
    fs::write(&output, text)
        .map_err(|error| crate::error::io_error("cannot write runtime profile", error))?;
    Ok((output, profile))
}

pub fn self_test(repo_root: &Path, project_id: Option<&str>) -> Result<Value, PlatformError> {
    let request_id = format!("req_{}", Uuid::new_v4().simple());
    let request = json!({
        "contract_version": "tool-v1",
        "request_id": request_id,
        "capability": "runtime.self_test",
        "idempotency_key": null,
        "requested_risk_hint": null,
        "cost_limit": 0,
        "artifact_refs": [],
        "parameters": {"target": "runtime.health", "data_class": "project"}
    });
    contracts::validate(&request, "tool-request-v1.schema.json")?;
    let binding = resolve_project(repo_root, project_id)?;
    let policy = PolicyEnforcementPoint::load(&binding.policy_path)?.evaluate(
        "runtime.self_test",
        request
            .get("parameters")
            .ok_or_else(|| PlatformError::Validation("self-test parameters are missing".into()))?,
        "project",
        None,
    )?;
    let health_root = repo_root.join("runtime/health");
    fs::create_dir_all(&health_root)
        .map_err(|error| crate::error::io_error("cannot create health directory", error))?;
    let test_path = health_root.join(format!("self-test-{}.tmp", Uuid::new_v4().simple()));
    let token = Uuid::new_v4().to_string();
    fs::write(&test_path, &token)
        .map_err(|error| crate::error::io_error("self-test write failed", error))?;
    let read_result = fs::read_to_string(&test_path)
        .map_err(|error| crate::error::io_error("self-test read failed", error));
    let cleanup_result = fs::remove_file(&test_path)
        .map_err(|error| crate::error::io_error("self-test cleanup failed", error));
    let read_back = read_result?;
    cleanup_result?;
    if read_back != token {
        return Err(PlatformError::Validation(
            "self-test read-back did not match written token".into(),
        ));
    }
    let result = json!({
        "request_id": request_id,
        "status": "success",
        "result": {
            "ping": "pong",
            "controlled_write_read": "passed",
            "cleanup": "passed",
            "ffmpeg": tool_version("ffmpeg")?,
            "ffprobe": tool_version("ffprobe")?
        },
        "artifact_refs": [],
        "provenance": {
            "capability": "runtime.self_test",
            "executor": "rust.local.core",
            "project_id": binding.project_id,
            "validated": true
        },
        "policy_decision_id": policy.decision_id,
        "error": null
    });
    contracts::validate(&result, "tool-v1.schema.json")?;
    Ok(result)
}
