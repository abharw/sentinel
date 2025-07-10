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
use models::providers::Provider;

#[derive(Parser)]
#[command(name = "sentinel")]
#[command(about = "AI Governance CLI - Manage policies and validate content")]
#[command(version = "1.0.0")]
#[command(propagate_version = true)]
struct Cli {
    /// URL of the Sentinel API server
    #[arg(long, default_value = "http://localhost:8080")]
    server_url: String,

    /// Enable verbose logging
    #[arg(short, long)]
    verbose: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Validate policy files for syntax and structure
    Validate {
        /// Path to the policy file to validate
        file: PathBuf,
    },

    /// Manage policies (create, list, update, delete)
    Policy {
        #[command(subcommand)]
        action: PolicyAction,
    },

    /// Monitor system health and status
    Monitor {
        /// Enable live monitoring mode
        #[arg(long)]
        live: bool,
    },

    /// Check system health
    Health,
}

#[derive(Subcommand)]
enum PolicyAction {
    /// List all policies
    List,

    /// Create a new policy from file
    Create {
        /// Path to the policy file
        file: PathBuf,
    },

    /// Get details of a specific policy
    Get {
        /// Policy ID
        id: String,
    },

    /// Update an existing policy
    Update {
        /// Policy ID
        id: String,
        /// Path to the updated policy file
        file: PathBuf,
    },

    /// Delete a policy
    Delete {
        /// Policy ID
        id: String,
    },

    /// Validate content against a policy
    Guard {
        /// Path to the policy file
        policy: PathBuf,
        /// Provider to use for the policy engine
        provider: Provider,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    let client = SentinelClient::new(cli.server_url);

    match cli.command {
        Commands::Validate { file } => {
            validate::execute(&file)?;
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
            PolicyAction::Guard { policy, provider } => {
                policy::guard(&client, policy, provider).await?;
            }
        },
        Commands::Monitor { live } => {
            monitor::execute(live).await?;
        }
        Commands::Health => {
            health::execute(&client).await?;
        }
    }
    Ok(())
}
