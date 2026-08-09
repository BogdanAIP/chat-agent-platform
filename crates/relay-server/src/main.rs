use std::net::SocketAddr;
use std::path::PathBuf;
use std::process::ExitCode;

use clap::Parser;
use relay_server::{RelayServerConfig, serve};

#[derive(Debug, Parser)]
#[command(
    name = "relay-server",
    version,
    about = "Provider-neutral HTTPS relay backend for agent-platform"
)]
struct Cli {
    #[arg(long, env = "RELAY_BIND", default_value = "127.0.0.1:8787")]
    bind: SocketAddr,

    #[arg(long, env = "RELAY_PROJECT_ID")]
    project_id: String,

    #[arg(long, env = "RELAY_MCP_TOKEN", hide_env_values = true)]
    mcp_token: String,

    #[arg(long, env = "RELAY_AGENT_TOKEN", hide_env_values = true)]
    agent_token: String,

    #[arg(
        long,
        env = "RELAY_DATABASE",
        default_value = "/var/lib/agent-platform-relay/relay.sqlite3"
    )]
    database: PathBuf,
}

#[tokio::main]
async fn main() -> ExitCode {
    let cli = Cli::parse();
    let config = match RelayServerConfig::new(
        cli.project_id,
        cli.mcp_token,
        cli.agent_token,
        cli.database,
    ) {
        Ok(value) => value,
        Err(error) => {
            eprintln!("{error}");
            return ExitCode::FAILURE;
        }
    };
    match serve(config, cli.bind).await {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("{error}");
            ExitCode::FAILURE
        }
    }
}
