use sentinel::client::PolicyRunner;
use std::path::PathBuf;

#[test]
fn test_policy_runner() {
    let policy_runner = PolicyRunner::new(PathBuf::from("tests/policies/test.yaml"));
    match policy_runner {
        Ok(runner) => {
            println!("Policy runner created successfully");
            println!("Policy conditions: {:?}", runner.parsed_policy.conditions);
            println!("Policy actions: {:?}", runner.parsed_policy.actions);
        }
        Err(e) => {
            println!("Error creating policy runner: {}", e);
            panic!("Policy runner creation failed: {}", e);
        }
    }
}
