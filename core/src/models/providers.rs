use clap::ValueEnum;
use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug, Clone, ValueEnum, Serialize, Deserialize)]
pub enum Provider {
    OpenAI,
    Anthropic,
    Google,
    Azure,
    DeepSeek,
}

impl fmt::Display for Provider {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Provider::OpenAI => write!(f, "OpenAI"),
            Provider::Anthropic => write!(f, "Anthropic"),
            Provider::Google => write!(f, "Google"),
            Provider::Azure => write!(f, "Azure"),
            Provider::DeepSeek => write!(f, "DeepSeek"),
        }
    }
}
