use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug, Deserialize, Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub evaluators: Option<serde_json::Value>,
    pub system_info: Option<serde_json::Value>,
    pub timestamp: Option<f64>,
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
