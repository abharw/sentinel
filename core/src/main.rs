use clap::{command, Parser, Subcommand};
use std::path::PathBuf;

mod client;
mod commands;
mod models;
mod utils;

use client::SentinelClient;
use commands::health;
use commands::monitor;
use commands::policy;
use commands::validate;

#[derive(Parser)]
#[command(name = "sentinel")]
#[command(about = "AI Governance CLI")]
#[command(version = "1.0.0")]
struct Cli {
    #[arg(long, default_value = "http://localhost:8080")]
    server_url: String,
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Policy {
        #[command(subcommand)]
        action: PolicyAction,
    },
    Monitor {
        #[arg(long)]
        live: bool,
    },
    Validate {
        file: PathBuf,
    },
    Health,
}

#[derive(Subcommand)]
enum PolicyAction {
    List,
    Create { file: PathBuf },
    Get { id: String },
    Update { id: String, file: PathBuf },
    Delete { id: String },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    let client = SentinelClient::new(cli.server_url);

    match cli.command {
        Commands::Health => {
            health::execute(&client).await?;
        }
        Commands::Policy { action } => match action {
            PolicyAction::List => {
                policy::list(&client).await?;
            }
            PolicyAction::Create { file } => {
                policy::create(&client, file).await?;
            }
            PolicyAction::Get { id } => {
                policy::get(&client, &id).await?;
            }
            PolicyAction::Update { id, file } => {
                policy::update(&client, &id, file).await?;
            }
            PolicyAction::Delete { id } => {
                policy::delete(&client, &id).await?;
            }
        },
        Commands::Monitor { live } => {
            monitor::execute(live).await?;
        }
        Commands::Validate { file } => {
            validate::execute(&file)?;
        }
    }
    Ok(())
}
