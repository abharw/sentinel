use std::path::Path;
use std::process::Command;

#[test]
fn test_help_commands() {
    // Test main help
    let output = Command::new("cargo")
        .args(["run", "--", "--help"])
        .output()
        .expect("Failed to execute command");

    assert!(output.status.success(), "Help command should succeed");
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(
        stdout.contains("AI Governance CLI"),
        "Should show CLI description"
    );
    assert!(stdout.contains("validate"), "Should show validate command");
    assert!(stdout.contains("policy"), "Should show policy command");
}

#[test]
fn test_validate_help() {
    let output = Command::new("cargo")
        .args(["run", "--", "validate", "--help"])
        .output()
        .expect("Failed to execute command");

    assert!(output.status.success(), "Validate help should succeed");
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(
        stdout.contains("Validate policy files"),
        "Should show validate description"
    );
}

#[test]
fn test_policy_help() {
    let output = Command::new("cargo")
        .args(["run", "--", "policy", "--help"])
        .output()
        .expect("Failed to execute command");

    assert!(output.status.success(), "Policy help should succeed");
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(
        stdout.contains("Manage policies"),
        "Should show policy description"
    );
    assert!(stdout.contains("list"), "Should show list subcommand");
    assert!(stdout.contains("create"), "Should show create subcommand");
}

#[test]
fn test_validate_command() {
    // Test with a valid policy file
    let policy_file = "tests/policies/test.yaml";
    assert!(
        Path::new(policy_file).exists(),
        "Test policy file should exist"
    );

    let output = Command::new("cargo")
        .args(["run", "--", "validate", policy_file])
        .output()
        .expect("Failed to execute command");

    // Should succeed with valid policy file
    assert!(
        output.status.success(),
        "Validate should succeed with valid file"
    );
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(
        stdout.contains("Policy file is valid"),
        "Should show validation success"
    );
}

#[test]
fn test_validate_invalid_file() {
    let output = Command::new("cargo")
        .args(["run", "--", "validate", "nonexistent.yaml"])
        .output()
        .expect("Failed to execute command");

    // Should fail with invalid file
    assert!(
        !output.status.success(),
        "Validate should fail with invalid file"
    );
}
