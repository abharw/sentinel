use crate::models::policy::PolicyCondition;

pub struct ConditionRunner {
    condition: PolicyCondition,
}

impl ConditionRunner {
    pub fn new(condition: PolicyCondition) -> Self {
        Self { condition }
    }

    pub fn run(&self) -> Result<(), Box<dyn std::error::Error>> {
        Ok(())
    }
}