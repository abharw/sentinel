use crate::models::policy::PolicyAction;

pub struct ActionRunner {
    action: PolicyAction,
}

impl ActionRunner {
    pub fn new(action: PolicyAction) -> Self {
        Self { action }
    }

    pub fn run(&self) -> Result<(), Box<dyn std::error::Error>> {
        Ok(())
    }
}