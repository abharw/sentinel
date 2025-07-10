use crate::models::health::HealthResponse;
use crate::models::policy::{Policy, PolicyFile};
use crate::models::providers::Provider;
use colored::*;
use serde_yaml;
use std::path::PathBuf;
use uuid::Uuid;

pub struct SentinelClient {
    client: reqwest::Client,
    base_url: String,
}

impl SentinelClient {
    pub fn new(base_url: String) -> Self {
        Self {
            client: reqwest::Client::new(),
            base_url,
        }
    }

    pub async fn health_check(&self) -> anyhow::Result<()> {
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

    pub async fn list_policies(&self) -> anyhow::Result<()> {
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
                let table = tabled::Table::new(policies);
                println!("{}", table);
            }
        } else {
            println!("{}", "Failed to fetch policies".red());
            println!("Status: {}", response.status());
        }
        Ok(())
    }

    pub async fn create_policy(&self, file: PathBuf) -> anyhow::Result<()> {
        let policy_content = std::fs::read_to_string(file)?;
        let policy_file: PolicyFile = serde_yaml::from_str(&policy_content)?;
        let policy = Policy {
            id: Uuid::new_v4().to_string(),
            name: policy_file.name,
            description: policy_file.description,
            severity: policy_file.severity,
            enabled: policy_file.enabled,
            conditions: policy_file.conditions,
            actions: policy_file.actions,
            provider: policy_file.provider,
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

    pub async fn get_policy(&self, id: &str) -> anyhow::Result<()> {
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

    pub async fn delete_policy(&self, id: &str) -> anyhow::Result<()> {

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

    pub async fn check_policy(&self, policy: PathBuf, provider: Provider) -> anyhow::Result<()> {
        let policy_content = std::fs::read_to_string(policy)?;
        let policy_file: PolicyFile = serde_yaml::from_str(&policy_content)?;
        let policy = Policy {
            id: Uuid::new_v4().to_string(),
            name: policy_file.name,
            description: policy_file.description,
            severity: policy_file.severity,
            enabled: policy_file.enabled,
            provider: provider,
            conditions: policy_file.conditions,
            actions: policy_file.actions,
        };

        let response = self
            .client
            .post(&format!("{}/policies/guard", self.base_url))
            .json(&policy)
            .send()
            .await?;

        if response.status().is_success() {
            println!("{}", "✓ Policy checked successfully".green());
        } else {
            println!("{}", "Failed to check policy".red());
        }

        Ok(())
    }
}
