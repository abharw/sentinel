use crate::client::SentinelClient;

pub async fn execute(client: &SentinelClient) -> anyhow::Result<()> {
    client.health_check().await
}
