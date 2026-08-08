use std::path::Path;
use std::{fs, path::PathBuf};

use chrono::Utc;
use serde_json::{Map, Value, json};
use uuid::Uuid;

use crate::artifact::{Artifact, ArtifactStore};
use crate::binding::{ProjectBinding, resolve_project};
use crate::capability::{CapabilityRegistry, CapabilitySelection, required_quality};
use crate::contracts;
use crate::error::PlatformError;
use crate::media::{inspect_media, tool_version};
use crate::policy::{PolicyDecision, PolicyEnforcementPoint};
use crate::reaper::discover_reaper;
use crate::reference_mastering::probe_matchering;

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
    let required = required_quality(&binding.repo_root, "media.inspect")?;
    let selection = CapabilityRegistry::load(&binding.repo_root)?.select(
        "media.inspect",
        &required,
        request
            .get("cost_limit")
            .and_then(Value::as_u64)
            .unwrap_or(0),
    )?;
    let parameters = request
        .get("parameters")
        .cloned()
        .unwrap_or_else(|| json!({}));
    let policy = PolicyEnforcementPoint::load(&binding.policy_path)?.evaluate(
        "media.inspect",
        &parameters,
        data_class,
        requested_risk_hint,
        selection.base_risk(),
    )?;
    let store = ArtifactStore::new(&binding.artifact_root)?;
    let artifact = store.import_file(file_path, "media.inspect", data_class)?;
    complete_inspection(
        &binding,
        &store,
        artifact,
        &request_id,
        policy,
        selection.executor(),
    )
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
    let required = required_quality(&binding.repo_root, "media.inspect")?;
    let selection = CapabilityRegistry::load(&binding.repo_root)?.select(
        "media.inspect",
        &required,
        request
            .get("cost_limit")
            .and_then(Value::as_u64)
            .unwrap_or(0),
    )?;
    let policy = PolicyEnforcementPoint::load(&binding.policy_path)?.evaluate(
        "media.inspect",
        request
            .get("parameters")
            .ok_or_else(|| PlatformError::Validation("inspection parameters are missing".into()))?,
        &artifact.data_class,
        requested_risk_hint,
        selection.base_risk(),
    )?;
    complete_inspection(
        &binding,
        &store,
        artifact,
        &request_id,
        policy,
        selection.executor(),
    )
}

fn complete_inspection(
    binding: &ProjectBinding,
    store: &ArtifactStore,
    artifact: Artifact,
    request_id: &str,
    policy: PolicyDecision,
    executor: &str,
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
    let artifact = store.update_metadata(&artifact.artifact_id, metadata)?;
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
            "executor": executor,
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
        "rust": env!("AGENT_PLATFORM_RUSTC_VERSION"),
        "rust_msrv": env!("CARGO_PKG_RUST_VERSION"),
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
    let registry = CapabilityRegistry::load(&binding.repo_root)?;
    let selections = registry.locked_selections()?;
    let mut capabilities = Map::new();
    for selection in &selections {
        capabilities.insert(
            selection.capability().to_owned(),
            runtime_capability_entry(&binding.repo_root, selection),
        );
    }
    let required_unavailable = capabilities
        .values()
        .filter(|entry| {
            entry.get("required").and_then(Value::as_bool) == Some(true)
                && entry.get("status").and_then(Value::as_str) == Some("unavailable")
        })
        .count();
    let profile = json!({
        "contract_version": "runtime-capability-profile-v1",
        "verified_at": Utc::now().to_rfc3339(),
        "status": if required_unavailable == 0 { "available" } else { "degraded" },
        "required_unavailable": required_unavailable,
        "surface": "local_windows_rust",
        "project_id": binding.project_id,
        "system": std::env::consts::OS,
        "rust": {
            "compiler": env!("AGENT_PLATFORM_RUSTC_VERSION"),
            "msrv": env!("CARGO_PKG_RUST_VERSION")
        },
        "tools": {
            "ffmpeg": {"available": true, "version": ffmpeg},
            "ffprobe": {"available": true, "version": ffprobe}
        },
        "selection_source": {
            "manifest": "config/tools.yaml",
            "lock": "config/tool-lock.yaml",
            "requirements": "config/capability-requirements.yaml"
        },
        "capabilities": Value::Object(capabilities),
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

fn runtime_capability_entry(repo_root: &Path, selection: &CapabilitySelection) -> Value {
    let (status, health) = match selection.executor() {
        "edge.python.matchering" => match probe_matchering(repo_root) {
            Ok(probe) => ("available", probe),
            Err(error) => (
                "unavailable",
                json!({"code": error.code(), "message": error.to_string()}),
            ),
        },
        "rust.local.reaper" => match discover_reaper() {
            Ok(path) => (
                "available",
                json!({"executable": path.to_string_lossy().into_owned()}),
            ),
            Err(error) => (
                "unavailable",
                json!({"code": error.code(), "message": error.to_string()}),
            ),
        },
        _ => ("available", json!({"built_in_or_ffmpeg_backed": true})),
    };
    json!({
        "status": status,
        "required": selection.required(),
        "executor": selection.executor(),
        "execution_path": selection.execution_path(),
        "quality": selection.quality(),
        "reliability": selection.reliability(),
        "determinism": selection.determinism(),
        "base_risk": selection.base_risk(),
        "cost": selection.cost(),
        "fallbacks": selection.fallbacks(),
        "evidence": selection.evidence(),
        "acceptance_evidence": selection.acceptance_evidence(),
        "health": health
    })
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
    let required = required_quality(&binding.repo_root, "runtime.self_test")?;
    let selection = CapabilityRegistry::load(&binding.repo_root)?.select(
        "runtime.self_test",
        &required,
        request
            .get("cost_limit")
            .and_then(Value::as_u64)
            .unwrap_or(0),
    )?;
    let policy = PolicyEnforcementPoint::load(&binding.policy_path)?.evaluate(
        "runtime.self_test",
        request
            .get("parameters")
            .ok_or_else(|| PlatformError::Validation("self-test parameters are missing".into()))?,
        "project",
        None,
        selection.base_risk(),
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
            "rust": env!("AGENT_PLATFORM_RUSTC_VERSION"),
            "rust_msrv": env!("CARGO_PKG_RUST_VERSION"),
            "ffmpeg": tool_version("ffmpeg")?,
            "ffprobe": tool_version("ffprobe")?
        },
        "artifact_refs": [],
        "provenance": {
            "capability": "runtime.self_test",
            "executor": selection.executor(),
            "project_id": binding.project_id,
            "validated": true
        },
        "policy_decision_id": policy.decision_id,
        "error": null
    });
    contracts::validate(&result, "tool-v1.schema.json")?;
    Ok(result)
}
