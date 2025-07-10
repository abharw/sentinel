use crate::models::policy::PolicyCondition;
use crate::config::CONFIG;
use colored::*;
use anyhow::{Result, Context};
use serde_json::{json, Value};

pub struct ConditionRunner {
    condition: PolicyCondition,
}

impl ConditionRunner {
    pub fn new(condition: PolicyCondition) -> Self {
        Self { condition }
    }

    pub async fn run(&self, content: &str) -> Result<bool> {
        println!("{}", format!("Running condition: {}", self.condition.name).green());
        
        match self.condition.name.as_str() {
            "content_analysis" => {
                println!("{}", "Content analysis condition".green());
                self.check_toxicity(content).await
            }
            "keywords" => {
                println!("{}", "Keywords condition".green());
                self.check_keywords(content).await
            }
            _ => {
                println!("{}", "Unknown condition".red());
                Ok(false)
            }
        }
    }

    async fn check_toxicity(&self, content: &str) -> Result<bool> {
        let client = reqwest::Client::new();
        
        let request_body = json!({
            "input_text": content,
            "expected_output": "non-toxic content",
            "actual_output": content,
            "metadata": {
                "check_type": "toxicity",
                "toxicity_threshold": 0.5
            }
        });

        let response = client
            .post(&format!("{}/evaluate/content_safety", CONFIG.server.api_url))
            .json(&request_body)
            .send()
            .await
            .with_context(|| "Failed to send toxicity check request to FastAPI")?;

        if response.status().is_success() {
            let result: Value = response.json().await.with_context(|| "Failed to parse toxicity check response JSON")?;
            let score = result["score"].as_f64().unwrap_or(0.0);
            let passed = result["passed"].as_bool().unwrap_or(false);
            
            println!("Toxicity check - Score: {:.2}, Passed: {}", score, passed);
            Ok(passed)
        } else {
            let status = response.status();
            let text = response.text().await.unwrap_or_default();
            Err(anyhow::anyhow!("Toxicity check failed: {} - {}", status, text))
        }
    }

    async fn check_keywords(&self, content: &str) -> Result<bool> {
        let client = reqwest::Client::new();
        
        let request_body = json!({
            "input_text": content,
            "expected_output": "content without banned keywords",
            "actual_output": content,
            "metadata": {
                "check_type": "keywords",
                "keyword_threshold": 0.1
            }
        });

        let response = client
            .post(&format!("{}/evaluate/keyword_filter", CONFIG.server.api_url))
            .json(&request_body)
            .send()
            .await
            .with_context(|| "Failed to send keyword filter request to FastAPI")?;

        if response.status().is_success() {
            let result: Value = response.
                json()
                .await
                .with_context(|| "Failed to parse keyword filter response JSON")?;
            let passed = result["passed"]
                .as_bool()
                .unwrap_or(false);
            
            println!("Keyword check - Passed: {}", passed);
            Ok(passed)
        } else {
            let status = response.status();
            let text = response
                .text()
                .await
                .unwrap_or_default();
            Err(anyhow::anyhow!("Keyword check failed: {} - {}", status, text))
        }
    }
}