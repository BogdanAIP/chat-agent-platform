use std::path::PathBuf;
use std::process::ExitCode;

use agent_platform::audit::write_capability_audit;
use agent_platform::bootstrap::build_context;
use agent_platform::service::{
    diagnose, inspect_artifact, inspect_file, self_test, write_runtime_profile,
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
enum Command {
    Diagnose {
        #[arg(long)]
        project_id: Option<String>,
    },
    Probe {
        #[arg(long)]
        project_id: Option<String>,
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
        Command::Bootstrap {
            project_id,
            capability,
        } => build_context(&cli.repo_root, project_id.as_deref(), capability),
        Command::Audit { project_id } => {
            write_capability_audit(&cli.repo_root, project_id.as_deref())
                .map(|output| json!({"status": "success", "output": output}))
        }
        Command::SelfTest { project_id } => self_test(&cli.repo_root, project_id.as_deref()),
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
