use std::path::PathBuf;
use std::process::ExitCode;

use agent_platform::audit::write_capability_audit;
use agent_platform::bootstrap::build_context;
use agent_platform::job_ops::{
    begin_job, cancel_job, checkpoint_job, fail_job, get_job, resume_job, succeed_job,
};
use agent_platform::mastering_workflow::produce_mastering_file;
use agent_platform::media_ops::{
    analyze_mastering_file, convert_audio_file, extract_audio_file, mux_media_files,
    normalize_audio_file, validate_media_file,
};
use agent_platform::reaper::discover_reaper;
use agent_platform::reaper_ops::{ReaperRenderOptions, render_reaper_file};
use agent_platform::reference_mastering::{probe_matchering, reference_master_files};
use agent_platform::service::{
    diagnose, inspect_artifact, inspect_file, self_test, write_runtime_profile,
};
use agent_platform::transport::{
    configure_relay, relay_status, remove_ingress_token, remove_relay_token, run_relay_worker,
    serve_local_ingress, start_relay_worker, stop_relay_worker, store_ingress_token_from_env,
};
use clap::{Parser, Subcommand};
use serde_json::json;

#[derive(Debug, Parser)]
#[command(
    name = "agent-platform",
    version,
    about = "Rust-first local agent platform core"
)]
struct Cli {
    #[arg(long, global = true, default_value = ".")]
    repo_root: PathBuf,
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum IngressCommand {
    ConfigureToken {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long, default_value = "AGENT_PLATFORM_INGRESS_TOKEN")]
        env_name: String,
        #[arg(long, default_value = "secret://ingress/caller_token")]
        secret_ref: String,
    },
    Serve {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long, default_value_t = 8787)]
        port: u16,
        #[arg(long, default_value = "secret://ingress/caller_token")]
        secret_ref: String,
    },
    RemoveToken {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long, default_value = "secret://ingress/caller_token")]
        secret_ref: String,
    },
}

#[derive(Debug, Subcommand)]
enum RelayCommand {
    Configure {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        endpoint: String,
        #[arg(long, default_value = "AGENT_PLATFORM_RELAY_TOKEN")]
        env_name: String,
        #[arg(long, default_value = "secret://relay/agent_token")]
        secret_ref: String,
    },
    Start {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        endpoint: Option<String>,
        #[arg(long)]
        secret_ref: Option<String>,
    },
    Status {
        #[arg(long)]
        project_id: Option<String>,
    },
    Stop {
        #[arg(long)]
        project_id: Option<String>,
    },
    RemoveToken {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long, default_value = "secret://relay/agent_token")]
        secret_ref: String,
    },
}

#[derive(Debug, Subcommand)]
enum Command {
    Diagnose {
        #[arg(long)]
        project_id: Option<String>,
    },
    Probe {
        #[arg(long)]
        project_id: Option<String>,
    },
    Ingress {
        #[command(subcommand)]
        command: IngressCommand,
    },
    Relay {
        #[command(subcommand)]
        command: RelayCommand,
    },
    #[command(hide = true)]
    RelayWorker {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        endpoint: String,
        #[arg(long, default_value = "secret://relay/agent_token")]
        secret_ref: String,
        #[arg(long, default_value_t = false)]
        once: bool,
    },
    ReaperProbe,
    MatcheringProbe,
    ReaperRender {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        file: PathBuf,
        #[arg(long, default_value = "Track 1")]
        track_name: String,
        #[arg(long, default_value = "Start")]
        marker_name: String,
        #[arg(long, default_value_t = 0.0)]
        marker_seconds: f64,
        #[arg(long, default_value_t = 48_000)]
        render_sample_rate_hz: u32,
        #[arg(long, default_value = "project")]
        data_class: String,
        #[arg(long)]
        requested_risk_hint: Option<String>,
    },
    ReferenceMaster {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        target: PathBuf,
        #[arg(long)]
        reference: PathBuf,
        #[arg(
            long,
            value_parser = ["music-balanced", "music-loud", "speech"],
            default_value = "music-balanced"
        )]
        profile: String,
        #[arg(long, default_value = "project")]
        data_class: String,
        #[arg(long)]
        requested_risk_hint: Option<String>,
    },
    Bootstrap {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        capability: String,
    },
    Audit {
        #[arg(long)]
        project_id: Option<String>,
    },
    SelfTest {
        #[arg(long)]
        project_id: Option<String>,
    },
    JobBegin {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        capability: String,
        #[arg(long)]
        idempotency_key: String,
    },
    JobGet {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        job_id: String,
    },
    JobResume {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        job_id: String,
    },
    JobCheckpoint {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        job_id: String,
        #[arg(long)]
        name: String,
        #[arg(long, default_value = "{}")]
        data_json: String,
    },
    JobSucceed {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        job_id: String,
        #[arg(long, default_value = "{}")]
        result_json: String,
    },
    JobFail {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        job_id: String,
        #[arg(long)]
        error_json: String,
    },
    JobCancel {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        job_id: String,
    },
    Inspect {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        file: PathBuf,
        #[arg(long, default_value = "project")]
        data_class: String,
        #[arg(long)]
        requested_risk_hint: Option<String>,
    },
    InspectArtifact {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        artifact_id: String,
        #[arg(long)]
        requested_risk_hint: Option<String>,
    },
    ValidateMedia {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        file: PathBuf,
        #[arg(long, default_value = "project")]
        data_class: String,
        #[arg(long)]
        requested_risk_hint: Option<String>,
    },
    AnalyzeMastering {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        file: PathBuf,
        #[arg(
            long,
            value_parser = ["music-balanced", "music-loud", "speech"],
            default_value = "music-balanced"
        )]
        profile: String,
        #[arg(long, default_value = "project")]
        data_class: String,
        #[arg(long)]
        requested_risk_hint: Option<String>,
    },
    ProduceMaster {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        file: PathBuf,
        #[arg(
            long,
            value_parser = ["music-balanced", "music-loud", "speech"],
            default_value = "music-balanced"
        )]
        profile: String,
        #[arg(long, default_value = "project")]
        data_class: String,
        #[arg(long)]
        requested_risk_hint: Option<String>,
    },
    ConvertAudio {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        file: PathBuf,
        #[arg(long, value_parser = ["wav", "flac"], default_value = "wav")]
        format: String,
        #[arg(long, default_value = "project")]
        data_class: String,
        #[arg(long)]
        requested_risk_hint: Option<String>,
    },
    ExtractAudio {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        file: PathBuf,
        #[arg(long, default_value = "project")]
        data_class: String,
        #[arg(long)]
        requested_risk_hint: Option<String>,
    },
    NormalizeAudio {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        file: PathBuf,
        #[arg(long, default_value_t = -14.0)]
        target_lufs: f64,
        #[arg(long, default_value_t = -1.0)]
        target_true_peak_dbtp: f64,
        #[arg(long, default_value = "project")]
        data_class: String,
        #[arg(long)]
        requested_risk_hint: Option<String>,
    },
    MuxMedia {
        #[arg(long)]
        project_id: Option<String>,
        #[arg(long)]
        video: PathBuf,
        #[arg(long)]
        audio: PathBuf,
        #[arg(long, default_value = "project")]
        data_class: String,
        #[arg(long)]
        requested_risk_hint: Option<String>,
    },
}

fn run_ingress_command(
    repo_root: &std::path::Path,
    command: &IngressCommand,
) -> Result<serde_json::Value, agent_platform::error::PlatformError> {
    match command {
        IngressCommand::ConfigureToken {
            project_id,
            env_name,
            secret_ref,
        } => store_ingress_token_from_env(
            repo_root,
            project_id.as_deref(),
            env_name,
            secret_ref,
        ),
        IngressCommand::Serve {
            project_id,
            port,
            secret_ref,
        } => serve_local_ingress(repo_root, project_id.as_deref(), *port, secret_ref),
        IngressCommand::RemoveToken {
            project_id,
            secret_ref,
        } => remove_ingress_token(repo_root, project_id.as_deref(), secret_ref),
    }
}

fn run_relay_command(
    repo_root: &std::path::Path,
    command: &RelayCommand,
) -> Result<serde_json::Value, agent_platform::error::PlatformError> {
    match command {
        RelayCommand::Configure {
            project_id,
            endpoint,
            env_name,
            secret_ref,
        } => configure_relay(
            repo_root,
            project_id.as_deref(),
            endpoint,
            env_name,
            secret_ref,
        ),
        RelayCommand::Start {
            project_id,
            endpoint,
            secret_ref,
        } => start_relay_worker(
            repo_root,
            project_id.as_deref(),
            endpoint.as_deref(),
            secret_ref.as_deref(),
        ),
        RelayCommand::Status { project_id } => relay_status(repo_root, project_id.as_deref()),
        RelayCommand::Stop { project_id } => stop_relay_worker(repo_root, project_id.as_deref()),
        RelayCommand::RemoveToken {
            project_id,
            secret_ref,
        } => remove_relay_token(repo_root, project_id.as_deref(), secret_ref),
    }
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let result = match &cli.command {
        Command::Diagnose { project_id } => diagnose(&cli.repo_root, project_id.as_deref()),
        Command::Probe { project_id } => write_runtime_profile(
            &cli.repo_root,
            project_id.as_deref(),
        )
        .map(
            |(output, profile)| json!({"status": "success", "output": output, "profile": profile}),
        ),
        Command::Ingress { command } => run_ingress_command(&cli.repo_root, command),
        Command::Relay { command } => run_relay_command(&cli.repo_root, command),
        Command::RelayWorker {
            project_id,
            endpoint,
            secret_ref,
            once,
        } => run_relay_worker(
            &cli.repo_root,
            project_id.as_deref(),
            endpoint,
            secret_ref,
            *once,
        ),
        Command::ReaperProbe => discover_reaper().map(|path| {
            json!({
                "status": "available",
                "execution_path": "reaper.cli.reascript",
                "executable": path
            })
        }),
        Command::MatcheringProbe => probe_matchering(&cli.repo_root),
        Command::ReaperRender {
            project_id,
            file,
            track_name,
            marker_name,
            marker_seconds,
            render_sample_rate_hz,
            data_class,
            requested_risk_hint,
        } => render_reaper_file(
            &cli.repo_root,
            file,
            project_id.as_deref(),
            ReaperRenderOptions {
                data_class,
                requested_risk_hint: requested_risk_hint.as_deref(),
                track_name,
                marker_name,
                marker_seconds: *marker_seconds,
                render_sample_rate_hz: *render_sample_rate_hz,
            },
        ),
        Command::ReferenceMaster {
            project_id,
            target,
            reference,
            profile,
            data_class,
            requested_risk_hint,
        } => reference_master_files(
            &cli.repo_root,
            target,
            reference,
            project_id.as_deref(),
            data_class,
            requested_risk_hint.as_deref(),
            profile,
        ),
        Command::Bootstrap {
            project_id,
            capability,
        } => build_context(&cli.repo_root, project_id.as_deref(), capability),
        Command::Audit { project_id } => {
            write_capability_audit(&cli.repo_root, project_id.as_deref())
                .map(|output| json!({"status": "success", "output": output}))
        }
        Command::SelfTest { project_id } => self_test(&cli.repo_root, project_id.as_deref()),
        Command::JobBegin {
            project_id,
            capability,
            idempotency_key,
        } => begin_job(
            &cli.repo_root,
            project_id.as_deref(),
            capability,
            idempotency_key,
        ),
        Command::JobGet { project_id, job_id } => {
            get_job(&cli.repo_root, project_id.as_deref(), job_id)
        }
        Command::JobResume { project_id, job_id } => {
            resume_job(&cli.repo_root, project_id.as_deref(), job_id)
        }
        Command::JobCheckpoint {
            project_id,
            job_id,
            name,
            data_json,
        } => checkpoint_job(
            &cli.repo_root,
            project_id.as_deref(),
            job_id,
            name,
            data_json,
        ),
        Command::JobSucceed {
            project_id,
            job_id,
            result_json,
        } => succeed_job(&cli.repo_root, project_id.as_deref(), job_id, result_json),
        Command::JobFail {
            project_id,
            job_id,
            error_json,
        } => fail_job(&cli.repo_root, project_id.as_deref(), job_id, error_json),
        Command::JobCancel { project_id, job_id } => {
            cancel_job(&cli.repo_root, project_id.as_deref(), job_id)
        }
        Command::Inspect {
            project_id,
            file,
            data_class,
            requested_risk_hint,
        } => inspect_file(
            &cli.repo_root,
            file,
            project_id.as_deref(),
            data_class,
            requested_risk_hint.as_deref(),
        ),
        Command::InspectArtifact {
            project_id,
            artifact_id,
            requested_risk_hint,
        } => inspect_artifact(
            &cli.repo_root,
            artifact_id,
            project_id.as_deref(),
            requested_risk_hint.as_deref(),
        ),
        Command::ValidateMedia {
            project_id,
            file,
            data_class,
            requested_risk_hint,
        } => validate_media_file(
            &cli.repo_root,
            file,
            project_id.as_deref(),
            data_class,
            requested_risk_hint.as_deref(),
        ),
        Command::AnalyzeMastering {
            project_id,
            file,
            profile,
            data_class,
            requested_risk_hint,
        } => analyze_mastering_file(
            &cli.repo_root,
            file,
            project_id.as_deref(),
            data_class,
            requested_risk_hint.as_deref(),
            profile,
        ),
        Command::ProduceMaster {
            project_id,
            file,
            profile,
            data_class,
            requested_risk_hint,
        } => produce_mastering_file(
            &cli.repo_root,
            file,
            project_id.as_deref(),
            data_class,
            requested_risk_hint.as_deref(),
            profile,
        ),
        Command::ConvertAudio {
            project_id,
            file,
            format,
            data_class,
            requested_risk_hint,
        } => convert_audio_file(
            &cli.repo_root,
            file,
            project_id.as_deref(),
            data_class,
            requested_risk_hint.as_deref(),
            format,
        ),
        Command::ExtractAudio {
            project_id,
            file,
            data_class,
            requested_risk_hint,
        } => extract_audio_file(
            &cli.repo_root,
            file,
            project_id.as_deref(),
            data_class,
            requested_risk_hint.as_deref(),
        ),
        Command::NormalizeAudio {
            project_id,
            file,
            target_lufs,
            target_true_peak_dbtp,
            data_class,
            requested_risk_hint,
        } => normalize_audio_file(
            &cli.repo_root,
            file,
            project_id.as_deref(),
            data_class,
            requested_risk_hint.as_deref(),
            *target_lufs,
            *target_true_peak_dbtp,
        ),
        Command::MuxMedia {
            project_id,
            video,
            audio,
            data_class,
            requested_risk_hint,
        } => mux_media_files(
            &cli.repo_root,
            video,
            audio,
            project_id.as_deref(),
            data_class,
            requested_risk_hint.as_deref(),
        ),
    };
    match result {
        Ok(value) => match serde_json::to_string_pretty(&value) {
            Ok(text) => {
                println!("{text}");
                ExitCode::SUCCESS
            }
            Err(error) => {
                eprintln!(
                    "{{\"status\":\"error\",\"error\":{{\"code\":\"VALIDATION_FAILED\",\"message\":{error:?}}}}}"
                );
                ExitCode::from(2)
            }
        },
        Err(error) => {
            let envelope = json!({"status": "error", "error": error.payload()});
            eprintln!(
                "{}",
                serde_json::to_string_pretty(&envelope)
                    .unwrap_or_else(|_| "{\"status\":\"error\"}".into())
            );
            ExitCode::from(2)
        }
    }
}
