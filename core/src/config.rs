use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub openai: OpenAIConfig,
    pub server: ServerConfig,
    pub policy: PolicyConfig,
    pub logging: LoggingConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OpenAIConfig {
    pub api_key: String,
    pub org_id: Option<String>,
    pub timeout_secs: u64,
    pub pool_idle_timeout_secs: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub default_org: String,
    pub database_url: Option<String>,
    pub redis_url: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicyConfig {
    pub version: String,
    pub default_policy_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoggingConfig {
    pub level: String,
}

impl Config {
    pub fn from_env() -> Result<Self> {
        // Load .env from shared/config directory
        Self::load_env_file()?;

        Ok(Self {
            openai: OpenAIConfig::from_env()?,
            server: ServerConfig::from_env()?,
            policy: PolicyConfig::from_env()?,
            logging: LoggingConfig::from_env()?,
        })
    }

    fn load_env_file() -> Result<()> {
        // Try multiple possible locations for the .env file
        let possible_paths = vec![
            PathBuf::from("shared/config/.env"),
            PathBuf::from("../shared/config/.env"),
            PathBuf::from("../../shared/config/.env"),
            PathBuf::from(".env"), // Fallback to local .env
        ];

        for path in possible_paths {
            if path.exists() {
                println!("Loading environment from: {:?}", path);
                dotenv::from_path(path)?;
                return Ok(());
            }
        }

        // If no .env file found, continue with system environment variables
        println!("No .env file found, using system environment variables");
        Ok(())
    }
}

impl OpenAIConfig {
    fn from_env() -> Result<Self> {
        Ok(Self {
            api_key: std::env::var("OPENAI_API_KEY")
                .map_err(|_| anyhow::anyhow!("OPENAI_API_KEY must be set"))?,
            org_id: std::env::var("OPENAI_ORG_ID").ok(),
            timeout_secs: std::env::var("OPENAI_TIMEOUT_SECS")
                .unwrap_or_else(|_| "30".to_string())
                .parse::<u64>()
                .unwrap_or(30),
            pool_idle_timeout_secs: std::env::var("OPENAI_POOL_IDLE_TIMEOUT_SECS")
                .unwrap_or_else(|_| "90".to_string())
                .parse::<u64>()
                .unwrap_or(90),
        })
    }
}

impl ServerConfig {
    fn from_env() -> Result<Self> {
        Ok(Self {
            default_org: std::env::var("DEFAULT_ORG").unwrap_or_else(|_| "default".to_string()),
            database_url: std::env::var("SENTINEL_DATABASE_URL").ok(),
            redis_url: std::env::var("SENTINEL_REDIS_URL").ok(),
        })
    }
}

impl PolicyConfig {
    fn from_env() -> Result<Self> {
        Ok(Self {
            version: std::env::var("POLICY_VERSION").unwrap_or_else(|_| "1.0.0".to_string()),
            default_policy_path: std::env::var("DEFAULT_POLICY_PATH")
                .unwrap_or_else(|_| "./shared/policies/default.yaml".to_string()),
        })
    }
}

impl LoggingConfig {
    fn from_env() -> Result<Self> {
        Ok(Self {
            level: std::env::var("LOG_LEVEL").unwrap_or_else(|_| "INFO".to_string()),
        })
    }
}

// Global config instance
lazy_static::lazy_static! {
    pub static ref CONFIG: Config = Config::from_env()
        .expect("Failed to load configuration from environment");
}
