use std::fs::{self, File};
use std::io::Read;
use std::path::{Path, PathBuf};

use serde_json::{Map, Value, json};
use sha2::{Digest, Sha256};
use uuid::Uuid;

use crate::artifact::{Artifact, ArtifactStore};
use crate::audio_analysis::{MasteringDecision, decide_mastering};
use crate::binding::{ProjectBinding, resolve_project};
use crate::capability::{CapabilityRegistry, required_quality};
use crate::contracts;
use crate::error::{PlatformError, io_error};
use crate::job::{JobRecord, JobStore};
use crate::media::{MediaInspection, convert_audio, inspect_media, normalize_loudness};
use crate::policy::{PolicyDecision, PolicyEnforcementPoint};

const CAPABILITY: &str = "audio.mastering_produce";
const FINAL_CHECKPOINT: &str = "master_qc_complete";

struct AuthorizedWorkflow {
    binding: ProjectBinding,
    store: ArtifactStore,
    jobs: JobStore,
    request_id: String,
    policy: PolicyDecision,
    executor: String,
}

struct TempOutput {
    path: PathBuf,
}

impl TempOutput {
    fn wav() -> Self {
        Self {
            path: std::env::temp_dir().join(format!(
                "agent-platform-master-{}.wav",
                Uuid::new_v4().simple()
            )),
        }
    }
}

impl Drop for TempOutput {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.path);
    }
}

pub fn produce_mastering_file(
    repo_root: &Path,
    file_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
    profile: &str,
) -> Result<Value, PlatformError> {
    let source_sha256 = sha256_file(file_path)?;
    let idempotency_key = format!("master-v1:{source_sha256}:{profile}:{data_class}");
    let auth = authorize(
        repo_root,
        file_path,
        project_id,
        data_class,
        requested_risk_hint,
        profile,
        &source_sha256,
    )?;
    let existing = auth.jobs.begin(CAPABILITY, &idempotency_key)?;

    if existing.status == "succeeded" {
        return completed_response(&auth, &existing);
    }

    let running = auth.jobs.resume(&existing.job_id)?;
    if running
        .checkpoint
        .as_ref()
        .is_some_and(|checkpoint| checkpoint.name == FINAL_CHECKPOINT)
    {
        let result = checkpoint_result(&running)?;
        let completed = auth.jobs.succeed(&running.job_id, result)?;
        return completed_response(&auth, &completed);
    }

    match execute_workflow(&auth, &running, file_path, data_class, profile) {
        Ok(result) => Ok(result),
        Err(error) => {
            if auth
                .jobs
                .get(&running.job_id)
                .is_ok_and(|job| job.status == "running")
            {
                let _ = auth.jobs.fail(&running.job_id, error_map(&error));
            }
            Err(error)
        }
    }
}

fn execute_workflow(
    auth: &AuthorizedWorkflow,
    job: &JobRecord,
    file_path: &Path,
    data_class: &str,
    profile: &str,
) -> Result<Value, PlatformError> {
    let source = source_artifact(auth, job, file_path, data_class)?;
    let input_inspection = inspect_media(Path::new(&source.path))?;
    let decision = decide_mastering(&input_inspection, profile)?;

    auth.jobs.checkpoint(
        &job.job_id,
        "analysis_complete",
        object(json!({
            "source_artifact_id": source.artifact_id,
            "source_sha256": source.sha256,
            "decision": decision
        }))?,
    )?;

    if decision.requires_review || !decision.auto_mastering_allowed {
        auth.jobs.fail(
            &job.job_id,
            object(json!({
                "code": "MASTERING_REVIEW_REQUIRED",
                "message": "source is outside the validated automatic mastering envelope",
                "retryable": false,
                "quality_flags": decision.quality_flags,
                "reasons": decision.reasons
            }))?,
        )?;
        return Err(PlatformError::Validation(format!(
            "automatic mastering requires review; job_id={}",
            job.job_id
        )));
    }

    let output = TempOutput::wav();
    let applied_action = match decision.action.as_str() {
        "preserve" => {
            convert_audio(Path::new(&source.path), &output.path, "wav")?;
            "preserve"
        }
        "normalize_loudness" => {
            normalize_loudness(
                Path::new(&source.path),
                &output.path,
                decision.target.target_lufs,
                decision.target.target_true_peak_dbtp,
            )?;
            "normalize_loudness"
        }
        other => {
            return Err(PlatformError::Validation(format!(
                "unsupported automatic mastering action from decision layer: {other}"
            )));
        }
    };

    let final_inspection = inspect_media(&output.path)?;
    verify_final_quality(&input_inspection, &final_inspection, &decision, profile)?;
    let final_decision = decide_mastering(&final_inspection, profile)?;

    let master = auth
        .store
        .import_file(&output.path, CAPABILITY, data_class)?;
    let mut metadata = Map::new();
    metadata.insert(
        "workflow".into(),
        Value::String("technical-master-v1".into()),
    );
    metadata.insert("job_id".into(), Value::String(job.job_id.clone()));
    metadata.insert("profile".into(), Value::String(profile.into()));
    metadata.insert(
        "applied_action".into(),
        Value::String(applied_action.into()),
    );
    metadata.insert(
        "input_decision".into(),
        serde_json::to_value(&decision).map_err(serialization_error)?,
    );
    metadata.insert(
        "final_inspection".into(),
        serde_json::to_value(&final_inspection).map_err(serialization_error)?,
    );
    let master = auth.store.update_metadata(&master.artifact_id, metadata)?;

    let result = object(json!({
        "job_id": job.job_id,
        "workflow_status": "succeeded",
        "workflow": "technical-master-v1",
        "profile": profile,
        "applied_action": applied_action,
        "source_artifact": artifact_ref(&source),
        "master_artifact": artifact_ref(&master),
        "input_decision": decision,
        "final_decision": final_decision,
        "final_inspection": final_inspection
    }))?;

    auth.jobs.checkpoint(
        &job.job_id,
        FINAL_CHECKPOINT,
        object(json!({"result": Value::Object(result.clone())}))?,
    )?;
    let completed = auth.jobs.succeed(&job.job_id, result)?;
    completed_response(auth, &completed)
}

fn source_artifact(
    auth: &AuthorizedWorkflow,
    job: &JobRecord,
    file_path: &Path,
    data_class: &str,
) -> Result<Artifact, PlatformError> {
    if let Some(artifact_id) = job
        .checkpoint
        .as_ref()
        .and_then(|checkpoint| checkpoint.data.get("source_artifact_id"))
        .and_then(Value::as_str)
    {
        return auth.store.get(artifact_id);
    }

    let source = auth.store.import_file(file_path, CAPABILITY, data_class)?;
    auth.jobs.checkpoint(
        &job.job_id,
        "source_registered",
        object(json!({
            "source_artifact_id": source.artifact_id,
            "source_sha256": source.sha256
        }))?,
    )?;
    Ok(source)
}

fn verify_final_quality(
    input: &MediaInspection,
    output: &MediaInspection,
    input_decision: &MasteringDecision,
    profile: &str,
) -> Result<(), PlatformError> {
    if output.sample_rate_hz < 44_100 {
        return Err(PlatformError::Validation(format!(
            "master output sample rate is below delivery floor: {} Hz",
            output.sample_rate_hz
        )));
    }
    if output.channels == 0 || output.channels > 2 {
        return Err(PlatformError::Validation(format!(
            "master output channel count is outside validated mono/stereo range: {}",
            output.channels
        )));
    }
    if (output.duration_seconds - input.duration_seconds).abs() > 0.1 {
        return Err(PlatformError::Validation(format!(
            "master output duration drift exceeds 100 ms: input={:.3}s output={:.3}s",
            input.duration_seconds, output.duration_seconds
        )));
    }
    let final_decision = decide_mastering(output, profile)?;
    if final_decision.requires_review || !final_decision.auto_mastering_allowed {
        return Err(PlatformError::Validation(
            "master output failed the final safe-auto quality envelope".into(),
        ));
    }
    if final_decision.action != "preserve" {
        return Err(PlatformError::Validation(format!(
            "master output is still outside target tolerance: {}",
            final_decision.action
        )));
    }
    let peak = output.true_peak_dbtp.ok_or_else(|| {
        PlatformError::Validation("master output true peak is unmeasurable".into())
    })?;
    if peak > input_decision.target.target_true_peak_dbtp + 0.1 {
        return Err(PlatformError::Validation(format!(
            "master output true peak {peak:.2} dBTP exceeds target ceiling {:.2} dBTP",
            input_decision.target.target_true_peak_dbtp
        )));
    }
    Ok(())
}

fn authorize(
    repo_root: &Path,
    file_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
    profile: &str,
    source_sha256: &str,
) -> Result<AuthorizedWorkflow, PlatformError> {
    let request_id = format!("req_{}", Uuid::new_v4().simple());
    let parameters = json!({
        "source_name": file_path
            .file_name()
            .map_or_else(String::new, |value| value.to_string_lossy().into_owned()),
        "source_sha256": source_sha256,
        "data_class": data_class,
        "profile": profile,
        "workflow": "technical-master-v1"
    });
    let request = json!({
        "contract_version": "tool-v1",
        "request_id": request_id,
        "capability": CAPABILITY,
        "idempotency_key": format!("master-v1:{source_sha256}:{profile}:{data_class}"),
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
            .ok_or_else(|| PlatformError::Validation("mastering parameters are missing".into()))?,
        data_class,
        requested_risk_hint,
        selection.base_risk(),
    )?;
    contracts::validate(
        &serde_json::to_value(&policy).map_err(serialization_error)?,
        "policy-decision-v1.schema.json",
    )?;
    let store = ArtifactStore::new(&binding.artifact_root)?;
    let jobs = JobStore::for_binding(&binding)?;
    Ok(AuthorizedWorkflow {
        binding,
        store,
        jobs,
        request_id,
        policy,
        executor: selection.executor().to_owned(),
    })
}

fn completed_response(auth: &AuthorizedWorkflow, job: &JobRecord) -> Result<Value, PlatformError> {
    if job.status != "succeeded" {
        return Err(PlatformError::Validation(format!(
            "job is not complete: {} ({})",
            job.job_id, job.status
        )));
    }
    let result = job.result.clone().ok_or_else(|| {
        PlatformError::Validation(format!("succeeded job has no result: {}", job.job_id))
    })?;
    let master_id = result
        .get("master_artifact")
        .and_then(Value::as_object)
        .and_then(|value| value.get("artifact_id"))
        .and_then(Value::as_str)
        .ok_or_else(|| PlatformError::Validation("master result has no artifact id".into()))?;
    let master = auth.store.get(master_id)?;
    let response = json!({
        "request_id": auth.request_id,
        "status": "success",
        "result": Value::Object(result),
        "artifact_refs": [artifact_ref(&master)],
        "provenance": {
            "capability": CAPABILITY,
            "executor": auth.executor,
            "project_id": auth.binding.project_id,
            "validated": true,
            "persistent_job": true
        },
        "policy_decision_id": auth.policy.decision_id,
        "error": null
    });
    contracts::validate(&response, "tool-v1.schema.json")?;
    Ok(response)
}

fn checkpoint_result(job: &JobRecord) -> Result<Map<String, Value>, PlatformError> {
    job.checkpoint
        .as_ref()
        .and_then(|checkpoint| checkpoint.data.get("result"))
        .and_then(Value::as_object)
        .cloned()
        .ok_or_else(|| {
            PlatformError::Validation(format!(
                "final checkpoint is missing persisted result: {}",
                job.job_id
            ))
        })
}

fn artifact_ref(artifact: &Artifact) -> Value {
    json!({
        "artifact_id": artifact.artifact_id,
        "sha256": artifact.sha256,
        "data_class": artifact.data_class,
        "mime": artifact.mime
    })
}

fn error_map(error: &PlatformError) -> Map<String, Value> {
    object(json!({
        "code": error.code(),
        "message": error.to_string(),
        "retryable": error.retryable(),
        "safe_to_retry": error.retryable()
    }))
    .unwrap_or_default()
}

fn object(value: Value) -> Result<Map<String, Value>, PlatformError> {
    value
        .as_object()
        .cloned()
        .ok_or_else(|| PlatformError::Validation("expected JSON object".into()))
}

fn sha256_file(path: &Path) -> Result<String, PlatformError> {
    let mut file = File::open(path).map_err(|error| {
        io_error(
            format!("cannot open mastering source {}", path.display()),
            error,
        )
    })?;
    let mut hasher = Sha256::new();
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let read = file
            .read(&mut buffer)
            .map_err(|error| io_error("cannot hash mastering source", error))?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    let digest = hasher.finalize();
    Ok(format!("{digest:x}"))
}

fn serialization_error(error: serde_json::Error) -> PlatformError {
    PlatformError::Validation(format!("cannot serialize mastering workflow data: {error}"))
}
