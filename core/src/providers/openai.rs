use async_openai::{Client, config::OpenAIConfig, types::{CreateChatCompletionRequestArgs, ChatCompletionRequestMessage}};
use reqwest::ClientBuilder;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use anyhow::Result;
use crate::config::CONFIG;

#[derive(Debug, Clone)]
pub struct PolicyContext {
    pub user_id: String,
    pub organization: String,
    pub policy_version: String,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ChatCompletionRequest {
    pub messages: Vec<ChatCompletionRequestMessage>,
    pub model: String,
    pub max_tokens: Option<u32>,
    pub temperature: Option<f32>,
    pub metadata: Option<HashMap<String, String>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ChatCompletionResponse {
    pub id: String,
    pub choices: Vec<Choice>,
    pub usage: Usage,
    pub model: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Choice {
    pub index: u32,
    pub message: ChatCompletionRequestMessage,
    pub finish_reason: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Usage {
    pub prompt_tokens: u32,
    pub completion_tokens: u32,
    pub total_tokens: u32,
}

pub struct OpenAIProvider {
    client: Client,
}

impl OpenAIProvider {
    pub fn new() -> Result<Self> {
        // Use shared configuration
        let config = &CONFIG.openai;
        
        // Create HTTP client with config from shared config
        let http_client = ClientBuilder::new()
            .user_agent("sentinel-ai-governance/1.0.0")
            .timeout(std::time::Duration::from_secs(config.timeout_secs))
            .pool_idle_timeout(std::time::Duration::from_secs(config.pool_idle_timeout_secs))
            .build()
            .unwrap();

        let openai_config = OpenAIConfig::new()
            .with_api_key(&config.api_key)
            .with_org_id(config.org_id.as_deref());

        let client = Client::with_config(openai_config)
            .with_http_client(http_client);

        Ok(Self { client })
    }

    pub async fn chat_completions(
        &self,
        request: ChatCompletionRequest,
        policy_context: &PolicyContext,
    ) -> Result<ChatCompletionResponse> {
        // 1. Policy evaluation
        self.evaluate_policy(&request, policy_context)?;
        
        // 2. Forward to OpenAI
        let openai_request = CreateChatCompletionRequestArgs::default()
            .model(&request.model)
            .messages(request.messages.clone())
            .max_tokens(request.max_tokens)
            .temperature(request.temperature)
            .build()?;

        let response = self.client.chat().create(openai_request).await?;
        
        // 3. Content filtering
        self.filter_response(&response)?;
        
        // 4. Audit logging
        self.log_request(&request, &response, policy_context).await?;
        
        // 5. Convert to our response format
        let choices = response.choices.into_iter().map(|choice| Choice {
            index: choice.index,
            message: choice.message,
            finish_reason: choice.finish_reason,
        }).collect();

        let usage = Usage {
            prompt_tokens: response.usage.prompt_tokens,
            completion_tokens: response.usage.completion_tokens,
            total_tokens: response.usage.total_tokens,
        };

        Ok(ChatCompletionResponse {
            id: response.id,
            choices,
            usage,
            model: response.model,
        })
    }

    fn evaluate_policy(&self, request: &ChatCompletionRequest, context: &PolicyContext) -> Result<()> {
        // TODO: Implement policy evaluation logic
        // - Content safety checks
        // - Cost limits
        // - Usage quotas
        // - Model restrictions
        println!("Policy evaluation for user: {}, org: {}", context.user_id, context.organization);
        Ok(())
    }

    fn filter_response(&self, response: &async_openai::types::CreateChatCompletionResponse) -> Result<()> {
        // TODO: Implement content filtering
        // - Check for harmful content
        // - Apply content policies
        // - Log filtered content
        println!("Content filtering applied");
        Ok(())
    }

    async fn log_request(
        &self,
        request: &ChatCompletionRequest,
        response: &async_openai::types::CreateChatCompletionResponse,
        context: &PolicyContext,
    ) -> Result<()> {
        // TODO: Implement audit logging
        // - Log to database
        // - Track costs
        // - Record policy decisions
        println!("Audit log: Request from user {} to model {}", context.user_id, request.model);
        Ok(())
    }
}









