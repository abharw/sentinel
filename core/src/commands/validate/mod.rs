use crate::models::policy::PolicyFile;
use colored::*;
use std::fs;
use std::path::PathBuf;

pub fn execute(file_path: &PathBuf) -> anyhow::Result<()> {
    let policy_content = fs::read_to_string(file_path)?;
    let policy: PolicyFile = serde_yaml::from_str(&policy_content)?;

    println!("{}", "✓ Policy file is valid".green());
    println!("  Name: {}", policy.name);
    println!("  Description: {}", policy.description);
    println!("  Severity: {}", policy.severity);
    println!("  Enabled: {}", policy.enabled);
    println!("  Provider: {}", policy.provider);

    Ok(())
}
