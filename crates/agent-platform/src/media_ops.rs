use std::fs;
use std::path::{Path, PathBuf};

use serde_json::{Map, Value, json};
use uuid::Uuid;

use crate::artifact::{Artifact, ArtifactStore};
use crate::audio_analysis::decide_mastering;
use crate::binding::{ProjectBinding, resolve_project};
use crate::capability::{CapabilityRegistry, required_quality};
use crate::contracts;
use crate::error::PlatformError;
use crate::media::{
    convert_audio, extract_audio, inspect_media, mux_audio_video, normalize_loudness,
    validate_media,
};
use crate::policy::{PolicyDecision, PolicyEnforcementPoint};

struct AuthorizedInput {
    binding: ProjectBinding,
    store: ArtifactStore,
    artifact: Artifact,
    request_id: String,
    policy: PolicyDecision,
    executor: String,
    capability: String,
}

struct TempOutput {
    path: PathBuf,
}

impl TempOutput {
    fn new(extension: &str) -> Self {
        Self {
            path: std::env::temp_dir().join(format!(
                "agent-platform-{}.{}",
                Uuid::new_v4().simple(),
                extension
            )),
        }
    }
}

impl Drop for TempOutput {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.path);
    }
}

pub fn validate_media_file(
    repo_root: &Path,
    file_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
) -> Result<Value, PlatformError> {
    let parameters = json!({
        "source_name": source_name(file_path),
        "data_class": data_class
    });
    let auth = authorize_file(
        repo_root,
        file_path,
        project_id,
        data_class,
        requested_risk_hint,
        "media.validate",
        parameters,
    )?;
    let validation = validate_media(Path::new(&auth.artifact.path))?;
    let artifact = update_output_metadata(
        &auth.store,
        &auth.artifact.artifact_id,
        "media.validate",
        &serde_json::to_value(&validation).map_err(serialization_error)?,
    )?;
    complete_response(&auth, json!({"validation": validation}), &[artifact])
}

pub fn analyze_mastering_file(
    repo_root: &Path,
    file_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
    profile: &str,
) -> Result<Value, PlatformError> {
    let parameters = json!({
        "source_name": source_name(file_path),
        "data_class": data_class,
        "profile": profile,
        "analysis_standard": "ebu_r128_plus_delivery_envelope"
    });
    let auth = authorize_file(
        repo_root,
        file_path,
        project_id,
        data_class,
        requested_risk_hint,
        "audio.mastering_analyze",
        parameters,
    )?;
    let inspection = inspect_media(Path::new(&auth.artifact.path))?;
    let decision = decide_mastering(&inspection, profile)?;
    let validation = serde_json::to_value(&decision).map_err(serialization_error)?;
    let artifact = update_output_metadata(
        &auth.store,
        &auth.artifact.artifact_id,
        "audio.mastering_analyze",
        &validation,
    )?;
    complete_response(&auth, validation, &[artifact])
}

pub fn convert_audio_file(
    repo_root: &Path,
    file_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
    format: &str,
) -> Result<Value, PlatformError> {
    validate_audio_format(format)?;
    let parameters = json!({
        "source_name": source_name(file_path),
        "data_class": data_class,
        "format": format
    });
    let auth = authorize_file(
        repo_root,
        file_path,
        project_id,
        data_class,
        requested_risk_hint,
        "media.convert",
        parameters,
    )?;
    let output = TempOutput::new(format);
    let inspection = convert_audio(Path::new(&auth.artifact.path), &output.path, format)?;
    let artifact = register_output(
        &auth,
        &output.path,
        "media.convert",
        &serde_json::to_value(&inspection).map_err(serialization_error)?,
    )?;
    complete_response(
        &auth,
        json!({"format": format, "inspection": inspection}),
        &[artifact],
    )
}

pub fn extract_audio_file(
    repo_root: &Path,
    file_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
) -> Result<Value, PlatformError> {
    let parameters = json!({
        "source_name": source_name(file_path),
        "data_class": data_class,
        "output_format": "wav"
    });
    let auth = authorize_file(
        repo_root,
        file_path,
        project_id,
        data_class,
        requested_risk_hint,
        "media.extract_audio",
        parameters,
    )?;
    let output = TempOutput::new("wav");
    let inspection = extract_audio(Path::new(&auth.artifact.path), &output.path)?;
    let artifact = register_output(
        &auth,
        &output.path,
        "media.extract_audio",
        &serde_json::to_value(&inspection).map_err(serialization_error)?,
    )?;
    complete_response(
        &auth,
        json!({"format": "wav", "inspection": inspection}),
        &[artifact],
    )
}

pub fn normalize_audio_file(
    repo_root: &Path,
    file_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
    target_lufs: f64,
    target_true_peak_dbtp: f64,
) -> Result<Value, PlatformError> {
    let parameters = json!({
        "source_name": source_name(file_path),
        "data_class": data_class,
        "target_lufs": target_lufs,
        "target_true_peak_dbtp": target_true_peak_dbtp,
        "algorithm": "ebu_r128_loudnorm_two_pass"
    });
    let auth = authorize_file(
        repo_root,
        file_path,
        project_id,
        data_class,
        requested_risk_hint,
        "media.normalize_loudness",
        parameters,
    )?;
    let output = TempOutput::new("wav");
    let normalization = normalize_loudness(
        Path::new(&auth.artifact.path),
        &output.path,
        target_lufs,
        target_true_peak_dbtp,
    )?;
    let artifact = register_output(
        &auth,
        &output.path,
        "media.normalize_loudness",
        &serde_json::to_value(&normalization).map_err(serialization_error)?,
    )?;
    complete_response(
        &auth,
        serde_json::to_value(&normalization).map_err(serialization_error)?,
        &[artifact],
    )
}

pub fn mux_media_files(
    repo_root: &Path,
    video_path: &Path,
    audio_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
) -> Result<Value, PlatformError> {
    let parameters = json!({
        "video_source_name": source_name(video_path),
        "audio_source_name": source_name(audio_path),
        "data_class": data_class,
        "container": "matroska",
        "video_mode": "stream_copy",
        "audio_codec": "flac"
    });
    let auth = authorize_file(
        repo_root,
        video_path,
        project_id,
        data_class,
        requested_risk_hint,
        "media.mux",
        parameters,
    )?;
    let audio_artifact = auth
        .store
        .import_file(audio_path, "media.mux", data_class)?;
    let output = TempOutput::new("mkv");
    let validation = mux_audio_video(
        Path::new(&auth.artifact.path),
        Path::new(&audio_artifact.path),
        &output.path,
    )?;
    let artifact = register_output(
        &auth,
        &output.path,
        "media.mux",
        &serde_json::to_value(&validation).map_err(serialization_error)?,
    )?;
    complete_response(
        &auth,
        json!({
            "container": "matroska",
            "validation": validation,
            "source_artifacts": [
                {"artifact_id": auth.artifact.artifact_id, "sha256": auth.artifact.sha256},
                {"artifact_id": audio_artifact.artifact_id, "sha256": audio_artifact.sha256}
            ]
        }),
        &[artifact],
    )
}

fn authorize_file(
    repo_root: &Path,
    file_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
    capability: &str,
    parameters: Value,
) -> Result<AuthorizedInput, PlatformError> {
    let request_id = format!("req_{}", Uuid::new_v4().simple());
    let request = json!({
        "contract_version": "tool-v1",
        "request_id": request_id,
        "capability": capability,
        "idempotency_key": null,
        "requested_risk_hint": requested_risk_hint,
        "cost_limit": 0,
        "artifact_refs": [],
        "parameters": parameters
    });
    contracts::validate(&request, "tool-request-v1.schema.json")?;
    let binding = resolve_project(repo_root, project_id)?;
    let required = required_quality(&binding.repo_root, capability)?;
    let selection =
        CapabilityRegistry::load(&binding.repo_root)?.select(capability, &required, 0)?;
    let policy = PolicyEnforcementPoint::load(&binding.policy_path)?.evaluate(
        capability,
        request
            .get("parameters")
            .ok_or_else(|| PlatformError::Validation("media parameters are missing".into()))?,
        data_class,
        requested_risk_hint,
        selection.base_risk(),
    )?;
    contracts::validate(
        &serde_json::to_value(&policy).map_err(serialization_error)?,
        "policy-decision-v1.schema.json",
    )?;
    let store = ArtifactStore::new(&binding.artifact_root)?;
    let artifact = store.import_file(file_path, capability, data_class)?;
    Ok(AuthorizedInput {
        binding,
        store,
        artifact,
        request_id,
        policy,
        executor: selection.executor().to_owned(),
        capability: capability.to_owned(),
    })
}

fn register_output(
    auth: &AuthorizedInput,
    path: &Path,
    operation: &str,
    validation: &Value,
) -> Result<Artifact, PlatformError> {
    let artifact = auth
        .store
        .import_file(path, operation, &auth.artifact.data_class)?;
    update_output_metadata(&auth.store, &artifact.artifact_id, operation, validation)
}

fn update_output_metadata(
    store: &ArtifactStore,
    artifact_id: &str,
    operation: &str,
    validation: &Value,
) -> Result<Artifact, PlatformError> {
    let mut metadata = Map::new();
    metadata.insert("operation".into(), Value::String(operation.to_owned()));
    metadata.insert("technical_validation".into(), validation.clone());
    store.update_metadata(artifact_id, metadata)
}

fn complete_response(
    auth: &AuthorizedInput,
    result: Value,
    artifacts: &[Artifact],
) -> Result<Value, PlatformError> {
    let artifact_refs: Vec<Value> = artifacts
        .iter()
        .map(|artifact| {
            json!({
                "artifact_id": artifact.artifact_id,
                "sha256": artifact.sha256,
                "data_class": artifact.data_class,
                "mime": artifact.mime
            })
        })
        .collect();
    let response = json!({
        "request_id": auth.request_id,
        "status": "success",
        "result": result,
        "artifact_refs": artifact_refs,
        "provenance": {
            "capability": auth.capability,
            "executor": auth.executor,
            "project_id": auth.binding.project_id,
            "validated": true
        },
        "policy_decision_id": auth.policy.decision_id,
        "error": null
    });
    contracts::validate(&response, "tool-v1.schema.json")?;
    Ok(response)
}

fn validate_audio_format(format: &str) -> Result<(), PlatformError> {
    match format {
        "wav" | "flac" => Ok(()),
        other => Err(PlatformError::Validation(format!(
            "unsupported professional audio conversion format: {other}"
        ))),
    }
}

fn source_name(path: &Path) -> String {
    path.file_name()
        .map_or_else(String::new, |value| value.to_string_lossy().into_owned())
}

fn serialization_error(error: serde_json::Error) -> PlatformError {
    PlatformError::Validation(format!("cannot serialize media operation result: {error}"))
}
