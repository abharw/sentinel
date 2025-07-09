use crate::client::SentinelClient;
use colored::*;
use std::path::PathBuf;

pub async fn list(client: &SentinelClient) -> anyhow::Result<()> {
    client.list_policies().await
}

pub async fn create(client: &SentinelClient, file: PathBuf) -> anyhow::Result<()> {
    client.create_policy(file).await
}

pub async fn get(client: &SentinelClient, id: &str) -> anyhow::Result<()> {
    client.get_policy(id).await
}

pub async fn update(client: &SentinelClient, id: &str, file: PathBuf) -> anyhow::Result<()> {
    println!("{}", "Update policy not implemented yet".yellow());
    Ok(())
}

pub async fn delete(client: &SentinelClient, id: &str) -> anyhow::Result<()> {
    client.delete_policy(id).await
}


