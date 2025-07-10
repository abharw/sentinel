use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tabled::Tabled;

#[derive(Debug, Serialize, Deserialize, Tabled)]
pub struct Policy {
    pub id: String,
    pub name: String,
    pub description: String,
    pub severity: String,
    pub enabled: bool,
    #[tabled(skip)]
    pub conditions: serde_json::Value,
    #[tabled(skip)]
    pub actions: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PolicyFile {
    pub id: String,
    pub name: String,
    pub description: String,
    pub severity: String,
    pub enabled: bool,
    pub conditions: serde_json::Value,
    pub actions: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PolicyResult {
    pub policy_id: String,
    pub policy_name: String,
    pub policy_description: String,
    pub policy_conditions: Vec<String>,
    pub policy_actions: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct PolicyContext {
    pub user_id: String,
    pub organization: String,
    pub policy_version: String,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PolicyCondition {
    pub name: String,
    pub parameters: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PolicyAction {
    pub name: String,
    pub parameters: serde_json::Value,
}
