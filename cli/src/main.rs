use clap::{command, Parser, Subcommand};
use colored::*;
use serde::{Deserialize, Serialize};
use std::fmt;
use std::fs;
use std::path::PathBuf;
use tabled::{Table, Tabled};
use uuid::Uuid;

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

#[derive(Debug, Serialize, Deserialize, Tabled)]
struct Policy {
    id: String,
    name: String,
    description: String,
    severity: String,
    enabled: bool,
    #[tabled(skip)]
    conditions: serde_json::Value,
    #[tabled(skip)]
    actions: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
struct PolicyFile {
    name: String,
    description: String,
    severity: String,
    enabled: bool,
    conditions: serde_json::Value,
    actions: serde_json::Value,
}

#[derive(Debug, Deserialize, Serialize)]
struct HealthResponse {
    status: String,
    evaluators: Option<serde_json::Value>,
    system_info: Option<serde_json::Value>,
    timestamp: Option<f64>,
}
impl fmt::Display for HealthResponse {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Status: {}\nEvaluators: {}\nSystem Info: {}\nTimestamp: {}",
            self.status,
            serde_json::to_string_pretty(&self.evaluators).unwrap_or_else(|_| "N/A".to_string()),
            serde_json::to_string_pretty(&self.system_info).unwrap_or_else(|_| "N/A".to_string()),
            self.timestamp.unwrap_or(0.0)
        )
    }
}

struct SentinelClient {
    client: reqwest::Client,
    base_url: String,
}

impl SentinelClient {
    fn new(base_url: String) -> Self {
        Self {
            client: reqwest::Client::new(),
            base_url,
        }
    }

    async fn health_check(&self) -> anyhow::Result<()> {
        let response = self
            .client
            .get(&format!("{}/health", self.base_url))
            .send()
            .await?;
        if response.status().is_success() {
            let health: HealthResponse = response.json().await?;

            println!("{}", "✓ Sentinel API is healthy".green());
            println!("{}", health);
        } else {
            println!("{}", "✗ Sentinel API is not healthy".red());
        }
        Ok(())
    }

    async fn list_policies(&self) -> anyhow::Result<()> {
        let response = self
            .client
            .get(&format!("{}/policies", self.base_url))
            .send()
            .await?;

        if response.status().is_success() {
            let policies: Vec<Policy> = response.json().await?;
            if policies.is_empty() {
                println!("{}", "No policies found".yellow());
            } else {
                println!(
                    "{}",
                    format!("Found {} policies", policies.len()).bold().green()
                );
                let table = Table::new(policies);
                println!("{}", table);
            }
        } else {
            println!("{}", "Failed to fetch policies".red());
            println!("Status: {}", response.status());
        }
        Ok(())
    }

    async fn create_policy(&self, file: PathBuf) -> anyhow::Result<()> {
        let policy_content = fs::read_to_string(file)?;
        let policy_file: PolicyFile = serde_yaml::from_str(&policy_content)?;
        let policy = Policy {
            id: Uuid::new_v4().to_string(),
            name: policy_file.name,
            description: policy_file.description,
            severity: policy_file.severity,
            enabled: policy_file.enabled,
            conditions: policy_file.conditions,
            actions: policy_file.actions,
        };

        let response = self
            .client
            .post(&format!("{}/policies", self.base_url))
            .json(&policy)
            .send()
            .await?;

        if response.status().is_success() {
            println!("{}", format!("✓ Policy created successfully").green());
            println!("{}", format!("Policy ID: {}", policy.id).bold().green());
            println!("{}", format!("Name: {}", policy.name).bold().green());
        } else {
            println!(
                "{}",
                format!(
                    "Failed to create policy {}: {}",
                    policy.id,
                    response.status()
                )
                .red()
            );
        }
        Ok(())
    }

    async fn get_policy(&self, id: &str) -> anyhow::Result<()> {
        let response = self
            .client
            .get(&format!("{}/policies/{}", self.base_url, id))
            .send()
            .await?;

        match response.status().as_u16() {
            200 => {
                let policy: Policy = response.json().await?;
                println!("{}", "Policy details:".green());
                println!("  ID: {}", policy.id);
                println!("  Name: {}", policy.name);
                println!("  Description: {}", policy.description);
                println!("  Severity: {}", policy.severity);
                println!("  Enabled: {}", policy.enabled);
                println!(
                    "  Conditions: {}",
                    serde_json::to_string_pretty(&policy.conditions)?
                );
                println!(
                    "  Actions: {}",
                    serde_json::to_string_pretty(&policy.actions)?
                );
            }
            404 => {
                println!("{}", format!("Policy with ID {} not found", id).red());
            }
            _ => {
                println!(
                    "{}",
                    format!("Failed to fetch policy {}: {}", id, response.status()).red()
                );
            }
        }
        Ok(())
    }

    async fn delete(&self, id: &str) -> anyhow::Result<()> {
        let response = self
            .client
            .delete(&format!("{}/policies/{}", self.base_url, id))
            .send()
            .await?;

        match response.status().as_u16() {
            200 => {
                println!("{}", "✓ Policy deleted successfully".green());
            }
            404 => {
                println!("{}", "Policy not found".red());
            }
            _ => {
                println!("{}", "Failed to delete policy".red());
            }
        }
        Ok(())
    }
}

fn validate_policy_file(file_path: &PathBuf) -> anyhow::Result<()> {
    let policy_content = fs::read_to_string(file_path)?;
    let policy: PolicyFile = serde_yaml::from_str(&policy_content)?;

    println!("{}", "✓ Policy file is valid".green());
    println!("  Name: {}", policy.name);
    println!("  Description: {}", policy.description);
    println!("  Severity: {}", policy.severity);
    println!("  Enabled: {}", policy.enabled);

    Ok(())
}

async fn monitor_requests(live: bool) -> anyhow::Result<()> {
    if live {
        println!(
            "{}",
            " Starting live monitoring (Press Ctrl+C to stop)".cyan()
        );
        println!(
            "{}",
            "This would show real-time AI request monitoring...".yellow()
        );

        // In a real implementation, this would connect to a WebSocket or polling endpoint
        // and show real-time metrics, violations, and request flows
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;

        println!(
            "{}",
            "Real-time monitoring dashboard would appear here".blue()
        );
    } else {
        println!("{}", "Current monitoring stats:".cyan());
        println!("  Total requests: 1,234");
        println!("  Blocked requests: 56");
        println!("  Policy violations: 78");
        println!("  Average latency: 12.5ms");
    }

    Ok(())
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    let client = SentinelClient::new(cli.server_url);

    match cli.command {
        Commands::Health => {
            client.health_check().await?;
        }
        Commands::Policy { action } => match action {
            PolicyAction::List => {
                client.list_policies().await?;
            }
            PolicyAction::Create { file } => {
                client.create_policy(file).await?;
            }
            PolicyAction::Get { id } => {
                client.get_policy(&id).await?;
            }
            PolicyAction::Update { id, file } => {
                println!("{}", "Update policy not implemented yet".yellow());
            }
            PolicyAction::Delete { id } => {
                client.delete(&id).await?;
            }
        },
        Commands::Monitor { live } => {
            monitor_requests(live).await?;
        }
        Commands::Validate { file } => {
            validate_policy_file(&file)?;
        }
    }
    Ok(())
}
