// use crate::client::SentinelClient;
use crate::models::policy::{Policy, PolicyAction, PolicyCondition};
use crate::policy::action::ActionRunner;
use crate::policy::condition::ConditionRunner;
use colored::*;
use serde_yaml;
use std::fs::File;
use std::path::PathBuf;

pub struct PolicyRunner {
    policy_path: PathBuf,
    pub parsed_policy: Policy,
}

impl PolicyRunner {
    pub fn new(policy_path: PathBuf) -> Result<Self, Box<dyn std::error::Error>> {
        let policy_file = File::open(&policy_path)?;
        let parsed_policy: Policy = serde_yaml::from_reader(policy_file)?;
        Ok(Self {
            policy_path,
            parsed_policy,
        })
    }

    pub async fn run(&self, content: &str) -> Result<(), Box<dyn std::error::Error>> {
        // For now, we can just validate that the policy can be parsed
        let _policy_runner = PolicyRunner::new(self.policy_path.clone())?;
        println!("Policy validation successful");
        if self.parsed_policy.enabled {
            if self.parsed_policy.conditions.is_null() {
                println!("{}", "Policy has no conditions".yellow());
                return Ok(());
            } else {
                println!(
                    "{}",
                    format!(
                        "Policy has {} conditions",
                        self.parsed_policy.conditions.as_object().unwrap().len()
                    )
                    .green()
                );
                self.run_conditions(content).await?;
            }
            if self.parsed_policy.actions.is_null() {
                println!("{}", "Policy has no actions".yellow());
                return Ok(());
            } else {
                println!(
                    "{}",
                    format!(
                        "Policy has {} actions",
                        self.parsed_policy.actions.as_object().unwrap().len()
                    )
                    .green()
                );
                self.run_actions().await?;
            }
        } else {
            println!("{}", "Policy is disabled".yellow());
            return Ok(());
        }
        Ok(())
    }

    async fn run_conditions(&self, content: &str) -> Result<(), Box<dyn std::error::Error>> {
        for (condition_name, condition_value) in self.parsed_policy.conditions.as_object().unwrap()
        {
            println!(
                "{}",
                format!("Running condition: {}", condition_name).green()
            );
            let condition = PolicyCondition {
                name: condition_name.clone(),
                parameters: condition_value.clone(),
            };
            let condition_runner = ConditionRunner::new(condition);
            condition_runner.run(content).await?;
        }
        Ok(())
    }

    async fn run_actions(&self) -> Result<(), Box<dyn std::error::Error>> {
        for (action_name, action_value) in self.parsed_policy.actions.as_object().unwrap() {
            println!("{}", format!("Running action: {}", action_name).green());
            let action = PolicyAction {
                name: action_name.clone(),
                parameters: action_value.clone(),
            };
            let action_runner = ActionRunner::new(action);
            action_runner.run()?;
        }
        Ok(())
    }
}
