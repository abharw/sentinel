#[tokio::test]
async fn test_keyword_filter_api() {
    let client = reqwest::Client::new();
    let url = "http://localhost:8080/evaluate/keyword_filter";
    let request_body = serde_json::json!({
        "input_text": "This message contains hate.",
        "expected_output": "content without banned keywords",
        "actual_output": "This message contains hate.",
        "metadata": {
            "check_type": "keywords",
            "keyword_threshold": 0.1
        }
    });

    let response = client
        .post(url)
        .json(&request_body)
        .send()
        .await
        .expect("Failed to send request");
    assert!(response.status().is_success(), "API did not return success");
    let json: serde_json::Value = response.json().await.expect("Invalid JSON");
    assert_eq!(json["passed"], false, "Should not pass with banned keyword");
    assert!(json["details"]["found_keywords"]
        .as_array()
        .unwrap()
        .contains(&serde_json::Value::String("hate".to_string())));
}   