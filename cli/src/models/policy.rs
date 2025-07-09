use serde::{Deserialize, Serialize};
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