use std::fs;
use std::path::{Path, PathBuf};

use serde_json::{Map, Value, json};
use uuid::Uuid;

use crate::artifact::{Artifact, ArtifactStore};
use crate::binding::{ProjectBinding, resolve_project};
use crate::capability::{CapabilityRegistry, required_quality};
use crate::contracts;
use crate::error::PlatformError;
use crate::media::inspect_media;
use crate::policy::{PolicyDecision, PolicyEnforcementPoint};
use crate::reaper::{
    ReaperMarkerSpec, ReaperSessionSpec, ReaperTrackSpec, build_driver_pack, discover_reaper,
    execute_driver_pack,
};

const CAPABILITY: &str = "audio.reaper_render";

#[derive(Debug, Clone, Copy)]
pub struct ReaperRenderOptions<'a> {
    pub data_class: &'a str,
    pub requested_risk_hint: Option<&'a str>,
    pub track_name: &'a str,
    pub marker_name: &'a str,
    pub marker_seconds: f64,
    pub render_sample_rate_hz: u32,
}

struct AuthorizedInput {
    binding: ProjectBinding,
    store: ArtifactStore,
    artifact: Artifact,
    request_id: String,
    policy: PolicyDecision,
    executor: String,
}

struct WorkspaceGuard {
    path: PathBuf,
}

impl WorkspaceGuard {
    fn new(repo_root: &Path, request_id: &str) -> Result<Self, PlatformError> {
        let parent = repo_root.join("runtime/reaper");
        fs::create_dir_all(&parent)
            .map_err(|error| crate::error::io_error("cannot create REAPER runtime root", error))?;
        let path = parent.join(request_id);
        if path.exists() {
            return Err(PlatformError::Validation(format!(
                "REAPER workspace already exists: {}",
                path.display()
            )));
        }
        fs::create_dir(&path)
            .map_err(|error| crate::error::io_error("cannot create REAPER workspace", error))?;
        Ok(Self { path })
    }
}

impl Drop for WorkspaceGuard {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

pub fn render_reaper_file(
    repo_root: &Path,
    file_path: &Path,
    project_id: Option<&str>,
    options: ReaperRenderOptions<'_>,
) -> Result<Value, PlatformError> {
    let parameters = json!({
        "source_name": source_name(file_path),
        "data_class": options.data_class,
        "track_name": options.track_name,
        "marker_name": options.marker_name,
        "marker_seconds": options.marker_seconds,
        "render_sample_rate_hz": options.render_sample_rate_hz,
        "render_format": "wav",
        "isolation": "new_reaper_instance"
    });
    let auth = authorize_file(
        repo_root,
        file_path,
        project_id,
        options.data_class,
        options.requested_risk_hint,
        parameters,
    )?;
    let workspace = WorkspaceGuard::new(&auth.binding.repo_root, &auth.request_id)?;
    let spec = ReaperSessionSpec {
        tracks: vec![ReaperTrackSpec {
            artifact_id: auth.artifact.artifact_id.clone(),
            name: options.track_name.to_owned(),
        }],
        markers: vec![ReaperMarkerSpec {
            position_seconds: options.marker_seconds,
            name: options.marker_name.to_owned(),
        }],
        render_sample_rate_hz: options.render_sample_rate_hz,
    };
    let pack = build_driver_pack(&auth.store, &spec, &workspace.path)?;
    let executable = discover_reaper()?;
    let validation = execute_driver_pack(&executable, &pack)?;
    let inspection = inspect_media(&pack.render_path)?;
    if inspection.sample_rate_hz != options.render_sample_rate_hz {
        return Err(PlatformError::Validation(format!(
            "REAPER render sample rate mismatch: expected {}, got {}",
            options.render_sample_rate_hz, inspection.sample_rate_hz
        )));
    }

    let project = auth
        .store
        .import_file(&pack.project_path, CAPABILITY, options.data_class)?;
    let render = auth
        .store
        .import_file(&pack.render_path, CAPABILITY, options.data_class)?;
    let project = add_metadata(
        &auth.store,
        &project.artifact_id,
        json!({
            "operation": CAPABILITY,
            "role": "reaper_project",
            "source_artifact_id": auth.artifact.artifact_id,
            "render_sample_rate_hz": options.render_sample_rate_hz
        }),
    )?;
    let render = add_metadata(
        &auth.store,
        &render.artifact_id,
        json!({
            "operation": CAPABILITY,
            "role": "rendered_master",
            "source_artifact_id": auth.artifact.artifact_id,
            "technical_validation": validation,
            "inspection": inspection
        }),
    )?;

    let result = json!({
        "request_id": auth.request_id,
        "status": "success",
        "result": {
            "source_artifact": artifact_ref(&auth.artifact),
            "project_artifact": artifact_ref(&project),
            "render_artifact": artifact_ref(&render),
            "render_validation": validation,
            "render_inspection": inspection
        },
        "artifact_refs": [artifact_ref(&project), artifact_ref(&render)],
        "provenance": {
            "capability": CAPABILITY,
            "executor": auth.executor,
            "project_id": auth.binding.project_id,
            "validated": true
        },
        "policy_decision_id": auth.policy.decision_id,
        "error": null
    });
    contracts::validate(&result, "tool-v1.schema.json")?;
    Ok(result)
}

fn authorize_file(
    repo_root: &Path,
    file_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
    parameters: Value,
) -> Result<AuthorizedInput, PlatformError> {
    let request_id = format!("req_{}", Uuid::new_v4().simple());
    let request = json!({
        "contract_version": "tool-v1",
        "request_id": request_id,
        "capability": CAPABILITY,
        "idempotency_key": null,
        "requested_risk_hint": requested_risk_hint,
        "cost_limit": 0,
        "artifact_refs": [],
        "parameters": parameters
    });
    contracts::validate(&request, "tool-request-v1.schema.json")?;
    let binding = resolve_project(repo_root, project_id)?;
    let required = required_quality(&binding.repo_root, CAPABILITY)?;
    let selection =
        CapabilityRegistry::load(&binding.repo_root)?.select(CAPABILITY, &required, 0)?;
    let policy = PolicyEnforcementPoint::load(&binding.policy_path)?.evaluate(
        CAPABILITY,
        request
            .get("parameters")
            .ok_or_else(|| PlatformError::Validation("REAPER parameters are missing".into()))?,
        data_class,
        requested_risk_hint,
        selection.base_risk(),
    )?;
    contracts::validate(
        &serde_json::to_value(&policy).map_err(serialization_error)?,
        "policy-decision-v1.schema.json",
    )?;
    let store = ArtifactStore::new(&binding.artifact_root)?;
    let artifact = store.import_file(file_path, CAPABILITY, data_class)?;
    Ok(AuthorizedInput {
        binding,
        store,
        artifact,
        request_id,
        policy,
        executor: selection.executor().to_owned(),
    })
}

fn add_metadata(
    store: &ArtifactStore,
    artifact_id: &str,
    metadata: Value,
) -> Result<Artifact, PlatformError> {
    let map: Map<String, Value> = metadata.as_object().cloned().ok_or_else(|| {
        PlatformError::Validation("REAPER artifact metadata must be an object".into())
    })?;
    store.update_metadata(artifact_id, map)
}

fn artifact_ref(artifact: &Artifact) -> Value {
    json!({
        "artifact_id": artifact.artifact_id,
        "sha256": artifact.sha256,
        "data_class": artifact.data_class,
        "mime": artifact.mime
    })
}

fn source_name(path: &Path) -> String {
    path.file_name()
        .map_or_else(String::new, |value| value.to_string_lossy().into_owned())
}

fn serialization_error(error: serde_json::Error) -> PlatformError {
    PlatformError::Validation(format!("cannot serialize REAPER operation result: {error}"))
}
