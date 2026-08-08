use std::env;
use std::ffi::OsString;
use std::fmt::Write as _;
use std::fs::{self, File};
use std::io::Read;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::Duration;

use serde_json::{Map, Value, json};
use sha2::{Digest, Sha256};
use uuid::Uuid;
use wait_timeout::ChildExt;

use crate::artifact::{Artifact, ArtifactStore};
use crate::audio_analysis::{decide_mastering, mastering_target};
use crate::binding::{ProjectBinding, resolve_project};
use crate::capability::{CapabilityRegistry, required_quality};
use crate::contracts;
use crate::error::{PlatformError, io_error};
use crate::job::{JobRecord, JobStore};
use crate::media::{MediaInspection, inspect_media, normalize_loudness};
use crate::policy::{PolicyDecision, PolicyEnforcementPoint};

const CAPABILITY: &str = "audio.reference_master";
const WORKFLOW_VERSION: &str = "reference-master-v1";
const FINAL_CHECKPOINT: &str = "reference_master_qc_complete";
const PROBE_TIMEOUT: Duration = Duration::from_secs(20);
const PROCESS_TIMEOUT: Duration = Duration::from_mins(10);

#[derive(Debug, Clone)]
struct PythonRuntime {
    program: OsString,
    display: String,
}

struct AuthorizedWorkflow {
    binding: ProjectBinding,
    store: ArtifactStore,
    jobs: JobStore,
    request_id: String,
    policy: PolicyDecision,
    executor: String,
}

struct Workspace {
    root: PathBuf,
}

impl Workspace {
    fn new(binding: &ProjectBinding) -> Result<Self, PlatformError> {
        let root = binding
            .local_root
            .join("runtime")
            .join("reference-mastering")
            .join(format!("req_{}", Uuid::new_v4().simple()));
        fs::create_dir_all(&root)
            .map_err(|error| io_error("cannot create reference mastering workspace", error))?;
        let root = fs::canonicalize(&root)
            .map_err(|error| io_error("cannot resolve reference mastering workspace", error))?;
        if !root.starts_with(&binding.local_root) {
            return Err(PlatformError::Validation(
                "reference mastering workspace escapes bound local root".into(),
            ));
        }
        Ok(Self { root })
    }

    fn matched(&self) -> PathBuf {
        self.root.join("matched.wav")
    }

    fn delivered(&self) -> PathBuf {
        self.root.join("master.wav")
    }
}

impl Drop for Workspace {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

pub fn probe_matchering(repo_root: &Path) -> Result<Value, PlatformError> {
    let runtime = discover_python()?;
    let script = adapter_script(repo_root)?;
    let output = run_probe(&runtime, &script)?;
    let mut value: Value = serde_json::from_slice(&output).map_err(|error| {
        PlatformError::Validation(format!("Matchering probe returned invalid JSON: {error}"))
    })?;
    let object = value.as_object_mut().ok_or_else(|| {
        PlatformError::Validation("Matchering probe must return a JSON object".into())
    })?;
    if object.get("status").and_then(Value::as_str) != Some("available") {
        return Err(PlatformError::ToolUnavailable(
            "Matchering probe did not report available status".into(),
        ));
    }
    object.insert("python".into(), Value::String(runtime.display));
    object.insert(
        "execution_path".into(),
        Value::String("edge.python.matchering".into()),
    );
    Ok(value)
}

pub fn reference_master_files(
    repo_root: &Path,
    target_path: &Path,
    reference_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
    profile: &str,
) -> Result<Value, PlatformError> {
    let target_sha = sha256_file(target_path)?;
    let reference_sha = sha256_file(reference_path)?;
    let idempotency_key =
        format!("{WORKFLOW_VERSION}:{target_sha}:{reference_sha}:{profile}:{data_class}");
    let auth = authorize(
        repo_root,
        target_path,
        reference_path,
        project_id,
        data_class,
        requested_risk_hint,
        profile,
        &target_sha,
        &reference_sha,
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

    match execute_workflow(
        repo_root,
        &auth,
        &running,
        target_path,
        reference_path,
        data_class,
        profile,
    ) {
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

#[allow(clippy::too_many_arguments)]
fn execute_workflow(
    repo_root: &Path,
    auth: &AuthorizedWorkflow,
    job: &JobRecord,
    target_path: &Path,
    reference_path: &Path,
    data_class: &str,
    profile: &str,
) -> Result<Value, PlatformError> {
    let (target, reference) = input_artifacts(auth, job, target_path, reference_path, data_class)?;
    let target_inspection = inspect_media(Path::new(&target.path))?;
    let reference_inspection = inspect_media(Path::new(&reference.path))?;
    validate_input("target", &target_inspection)?;
    validate_input("reference", &reference_inspection)?;

    let runtime = discover_python()?;
    let script = adapter_script(repo_root)?;
    run_probe(&runtime, &script)?;

    let workspace = Workspace::new(&auth.binding)?;
    run_matchering(
        &runtime,
        &script,
        Path::new(&target.path),
        Path::new(&reference.path),
        &workspace.matched(),
    )?;
    let matched_inspection = inspect_media(&workspace.matched())?;
    validate_matchering_output(&target_inspection, &matched_inspection)?;

    let target_profile = mastering_target(profile)?;
    normalize_loudness(
        &workspace.matched(),
        &workspace.delivered(),
        target_profile.target_lufs,
        target_profile.target_true_peak_dbtp,
    )?;
    let final_inspection = inspect_media(&workspace.delivered())?;
    validate_final_output(&target_inspection, &final_inspection, profile)?;
    let final_decision = decide_mastering(&final_inspection, profile)?;

    let master = auth
        .store
        .import_file(&workspace.delivered(), CAPABILITY, data_class)?;
    let similarity = loudness_similarity(
        &target_inspection,
        &reference_inspection,
        &matched_inspection,
    );
    let mut metadata = Map::new();
    metadata.insert("workflow".into(), Value::String(WORKFLOW_VERSION.into()));
    metadata.insert("job_id".into(), Value::String(job.job_id.clone()));
    metadata.insert("profile".into(), Value::String(profile.into()));
    metadata.insert(
        "reference_artifact_id".into(),
        Value::String(reference.artifact_id.clone()),
    );
    metadata.insert(
        "matchering_inspection".into(),
        serde_json::to_value(&matched_inspection).map_err(serialization_error)?,
    );
    metadata.insert(
        "final_inspection".into(),
        serde_json::to_value(&final_inspection).map_err(serialization_error)?,
    );
    metadata.insert("reference_similarity".into(), similarity.clone());
    let master = auth.store.update_metadata(&master.artifact_id, metadata)?;

    let result = object(json!({
        "job_id": job.job_id,
        "workflow_status": "succeeded",
        "workflow": WORKFLOW_VERSION,
        "profile": profile,
        "engine": "matchering",
        "target_artifact": artifact_ref(&target),
        "reference_artifact": artifact_ref(&reference),
        "master_artifact": artifact_ref(&master),
        "target_inspection": target_inspection,
        "reference_inspection": reference_inspection,
        "matched_inspection": matched_inspection,
        "reference_similarity": similarity,
        "final_inspection": final_inspection,
        "final_decision": final_decision
    }))?;

    auth.jobs.checkpoint(
        &job.job_id,
        FINAL_CHECKPOINT,
        object(json!({"result": Value::Object(result.clone())}))?,
    )?;
    let completed = auth.jobs.succeed(&job.job_id, result)?;
    completed_response(auth, &completed)
}

fn input_artifacts(
    auth: &AuthorizedWorkflow,
    job: &JobRecord,
    target_path: &Path,
    reference_path: &Path,
    data_class: &str,
) -> Result<(Artifact, Artifact), PlatformError> {
    if let Some(checkpoint) = &job.checkpoint
        && checkpoint.name == "inputs_registered"
    {
        let target_id = checkpoint
            .data
            .get("target_artifact_id")
            .and_then(Value::as_str)
            .ok_or_else(|| {
                PlatformError::Validation("target artifact checkpoint is missing".into())
            })?;
        let reference_id = checkpoint
            .data
            .get("reference_artifact_id")
            .and_then(Value::as_str)
            .ok_or_else(|| {
                PlatformError::Validation("reference artifact checkpoint is missing".into())
            })?;
        return Ok((auth.store.get(target_id)?, auth.store.get(reference_id)?));
    }

    let target = auth
        .store
        .import_file(target_path, CAPABILITY, data_class)?;
    let reference = auth
        .store
        .import_file(reference_path, CAPABILITY, data_class)?;
    auth.jobs.checkpoint(
        &job.job_id,
        "inputs_registered",
        object(json!({
            "target_artifact_id": target.artifact_id,
            "target_sha256": target.sha256,
            "reference_artifact_id": reference.artifact_id,
            "reference_sha256": reference.sha256
        }))?,
    )?;
    Ok((target, reference))
}

fn validate_input(label: &str, inspection: &MediaInspection) -> Result<(), PlatformError> {
    if inspection.sample_rate_hz < 44_100 {
        return Err(PlatformError::Validation(format!(
            "{label} sample rate is below the 44.1 kHz reference-mastering floor"
        )));
    }
    if inspection.channels == 0 || inspection.channels > 2 {
        return Err(PlatformError::Validation(format!(
            "{label} channel count is outside the validated mono/stereo path"
        )));
    }
    if inspection.duration_seconds < 5.0 {
        return Err(PlatformError::Validation(format!(
            "{label} is shorter than the 5 second reference-mastering floor"
        )));
    }
    if inspection.integrated_lufs.is_none() || inspection.true_peak_dbtp.is_none() {
        return Err(PlatformError::Validation(format!(
            "{label} loudness/true-peak metrics are not measurable"
        )));
    }
    Ok(())
}

fn validate_matchering_output(
    target: &MediaInspection,
    output: &MediaInspection,
) -> Result<(), PlatformError> {
    if output.codec != "pcm_s24le" {
        return Err(PlatformError::Validation(format!(
            "Matchering output must be PCM 24-bit WAV, got {}",
            output.codec
        )));
    }
    if output.channels == 0 || output.channels > 2 {
        return Err(PlatformError::Validation(
            "Matchering output is outside the validated mono/stereo path".into(),
        ));
    }
    if (output.duration_seconds - target.duration_seconds).abs() > 0.25 {
        return Err(PlatformError::Validation(format!(
            "Matchering output duration drift exceeds 250 ms: target={:.3}s output={:.3}s",
            target.duration_seconds, output.duration_seconds
        )));
    }
    if output.integrated_lufs.is_none() || output.true_peak_dbtp.is_none() {
        return Err(PlatformError::Validation(
            "Matchering output loudness/true-peak metrics are not measurable".into(),
        ));
    }
    Ok(())
}

fn validate_final_output(
    target: &MediaInspection,
    output: &MediaInspection,
    profile: &str,
) -> Result<(), PlatformError> {
    if output.sample_rate_hz < 44_100 || output.channels == 0 || output.channels > 2 {
        return Err(PlatformError::Validation(
            "reference master failed final delivery format validation".into(),
        ));
    }
    if (output.duration_seconds - target.duration_seconds).abs() > 0.25 {
        return Err(PlatformError::Validation(
            "reference master failed final duration integrity".into(),
        ));
    }
    let decision = decide_mastering(output, profile)?;
    if decision.requires_review || !decision.auto_mastering_allowed || decision.action != "preserve"
    {
        return Err(PlatformError::Validation(format!(
            "reference master failed final Stage 13 delivery gate: action={}, flags={}, lra={:.2} LU, lufs={:?}, peak={:?}",
            decision.action,
            decision.quality_flags.join(","),
            output.loudness_range_lu,
            output.integrated_lufs,
            output.true_peak_dbtp
        )));
    }
    Ok(())
}

fn loudness_similarity(
    target: &MediaInspection,
    reference: &MediaInspection,
    matched: &MediaInspection,
) -> Value {
    let target_lufs = target.integrated_lufs;
    let reference_lufs = reference.integrated_lufs;
    let matched_lufs = matched.integrated_lufs;
    let before = target_lufs.zip(reference_lufs).map(|(a, b)| (a - b).abs());
    let after = matched_lufs.zip(reference_lufs).map(|(a, b)| (a - b).abs());
    json!({
        "metric": "integrated_lufs_distance",
        "before_lu": before,
        "after_lu": after,
        "improved": before.zip(after).map(|(before, after)| after < before)
    })
}

#[allow(clippy::too_many_arguments)]
fn authorize(
    repo_root: &Path,
    target_path: &Path,
    reference_path: &Path,
    project_id: Option<&str>,
    data_class: &str,
    requested_risk_hint: Option<&str>,
    profile: &str,
    target_sha: &str,
    reference_sha: &str,
) -> Result<AuthorizedWorkflow, PlatformError> {
    let request_id = format!("req_{}", Uuid::new_v4().simple());
    let parameters = json!({
        "target_name": file_name(target_path),
        "reference_name": file_name(reference_path),
        "target_sha256": target_sha,
        "reference_sha256": reference_sha,
        "data_class": data_class,
        "profile": profile,
        "engine": "matchering",
        "workflow": WORKFLOW_VERSION
    });
    let request = json!({
        "contract_version": "tool-v1",
        "request_id": request_id,
        "capability": CAPABILITY,
        "idempotency_key": format!("{WORKFLOW_VERSION}:{target_sha}:{reference_sha}:{profile}:{data_class}"),
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
        request.get("parameters").ok_or_else(|| {
            PlatformError::Validation("reference mastering parameters are missing".into())
        })?,
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

fn discover_python() -> Result<PythonRuntime, PlatformError> {
    if let Some(explicit) = env::var_os("MATCHERING_PYTHON") {
        let path = PathBuf::from(&explicit);
        if !path.is_file() {
            return Err(PlatformError::ToolUnavailable(format!(
                "MATCHERING_PYTHON does not point to a file: {}",
                path.display()
            )));
        }
        return Ok(PythonRuntime {
            program: explicit,
            display: path.to_string_lossy().into_owned(),
        });
    }
    Ok(PythonRuntime {
        program: OsString::from("python"),
        display: "python (PATH)".into(),
    })
}

fn adapter_script(repo_root: &Path) -> Result<PathBuf, PlatformError> {
    let path = repo_root.join("scripts/matchering_adapter.py");
    if !path.is_file() {
        return Err(PlatformError::ToolUnavailable(format!(
            "Matchering adapter script is unavailable: {}",
            path.display()
        )));
    }
    fs::canonicalize(&path)
        .map_err(|error| io_error("cannot resolve Matchering adapter script", error))
}

fn run_probe(runtime: &PythonRuntime, script: &Path) -> Result<Vec<u8>, PlatformError> {
    let mut child = Command::new(&runtime.program)
        .arg(script)
        .arg("probe")
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|error| {
            PlatformError::ToolUnavailable(format!(
                "cannot start Matchering Python runtime {}: {error}",
                runtime.display
            ))
        })?;
    let status = child
        .wait_timeout(PROBE_TIMEOUT)
        .map_err(|error| io_error("cannot wait for Matchering probe", error))?;
    let Some(status) = status else {
        let _ = child.kill();
        let _ = child.wait();
        return Err(PlatformError::ToolTimeout(
            "Matchering probe exceeded 20 seconds".into(),
        ));
    };
    let mut output = Vec::new();
    if let Some(mut stdout) = child.stdout.take() {
        stdout
            .read_to_end(&mut output)
            .map_err(|error| io_error("cannot read Matchering probe output", error))?;
    }
    if !status.success() {
        return Err(PlatformError::ToolUnavailable(
            "Matchering is not importable in the selected Python runtime".into(),
        ));
    }
    Ok(output)
}

fn run_matchering(
    runtime: &PythonRuntime,
    script: &Path,
    target: &Path,
    reference: &Path,
    output: &Path,
) -> Result<(), PlatformError> {
    let mut child = Command::new(&runtime.program)
        .arg(script)
        .arg("process")
        .arg("--target")
        .arg(target)
        .arg("--reference")
        .arg(reference)
        .arg("--output")
        .arg(output)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|error| {
            PlatformError::ToolUnavailable(format!(
                "cannot start Matchering process with {}: {error}",
                runtime.display
            ))
        })?;
    let status = child
        .wait_timeout(PROCESS_TIMEOUT)
        .map_err(|error| io_error("cannot wait for Matchering process", error))?;
    let Some(status) = status else {
        let _ = child.kill();
        let _ = child.wait();
        return Err(PlatformError::ToolTimeout(
            "Matchering processing exceeded 10 minutes".into(),
        ));
    };
    if !status.success() {
        return Err(PlatformError::Validation(
            "Matchering process failed; no reference master was accepted".into(),
        ));
    }
    if !output.is_file() || !output.metadata().is_ok_and(|metadata| metadata.len() > 0) {
        return Err(PlatformError::Validation(
            "Matchering did not create a non-empty output WAV".into(),
        ));
    }
    Ok(())
}

fn completed_response(auth: &AuthorizedWorkflow, job: &JobRecord) -> Result<Value, PlatformError> {
    if job.status != "succeeded" {
        return Err(PlatformError::Validation(format!(
            "reference mastering job is not complete: {} ({})",
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
        .ok_or_else(|| {
            PlatformError::Validation("reference master result has no artifact id".into())
        })?;
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
            "persistent_job": true,
            "external_engine": "matchering"
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
                "final reference-mastering checkpoint is missing result: {}",
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

fn file_name(path: &Path) -> String {
    path.file_name()
        .map_or_else(String::new, |value| value.to_string_lossy().into_owned())
}

fn sha256_file(path: &Path) -> Result<String, PlatformError> {
    let mut file = File::open(path)
        .map_err(|error| io_error(format!("cannot open {}", path.display()), error))?;
    let mut hasher = Sha256::new();
    let mut buffer = vec![0_u8; 64 * 1024];
    loop {
        let read = file
            .read(&mut buffer)
            .map_err(|error| io_error("cannot hash reference-mastering input", error))?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    let digest = hasher.finalize();
    let mut hex = String::with_capacity(digest.len() * 2);
    for byte in digest {
        write!(&mut hex, "{byte:02x}").expect("writing SHA-256 to String cannot fail");
    }
    Ok(hex)
}

fn serialization_error(error: serde_json::Error) -> PlatformError {
    PlatformError::Validation(format!(
        "cannot serialize reference-mastering data: {error}"
    ))
}
