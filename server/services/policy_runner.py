from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import asyncio
from enum import Enum

from models.pydantic.policy import PolicyResponse
from evaluators.keyword_filter import KeywordFilterEvaluator
from evaluators.content_safety import ContentSafetyEvaluator
from evaluators.semantic import SemanticEvaluator
from evaluators.performance import PerformanceEvaluator

logger = logging.getLogger(__name__)

class PolicyDecision(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"

class PolicyViolation:
    def __init__(self, policy_id: str, policy_name: str, reason: str, severity: str, details: Dict[str, Any]):
        self.policy_id = policy_id
        self.policy_name = policy_name
        self.reason = reason
        self.severity = severity
        self.details = details
        self.timestamp = datetime.now().isoformat()

class PolicyEvaluationResult:
    def __init__(self, decision: PolicyDecision, violations: List[PolicyViolation], metadata: Dict[str, Any]):
        self.decision = decision
        self.violations = violations
        self.metadata = metadata
        self.timestamp = datetime.now().isoformat()

class PolicyRunner:
    def __init__(self):
        self.evaluators = {
            "keyword_filter": KeywordFilterEvaluator(),
            "content_safety": ContentSafetyEvaluator(),
            "semantic": SemanticEvaluator(),
            "performance": PerformanceEvaluator()
        }
        self._loaded = False
    
    async def load(self):
        """Load all evaluators"""
        if self._loaded:
            return
        
        logger.info("Loading policy runner evaluators...")
        for name, evaluator in self.evaluators.items():
            await evaluator.load()
        
        self._loaded = True
        logger.info("Policy runner loaded successfully")
    
    async def evaluate_policy(self, policy: PolicyResponse, request_data: Dict[str, Any]) -> PolicyEvaluationResult:
        """Evaluate a single policy against request data"""
        if not policy.enabled:
            return PolicyEvaluationResult(
                decision=PolicyDecision.ALLOW,
                violations=[],
                metadata={"reason": "Policy disabled"}
            )
        
        violations = []
        conditions = policy.conditions
        
        # Evaluate each condition type
        for condition_type, condition_config in conditions.items():
            if condition_type == "keyword_filter":
                result = await self._evaluate_keyword_filter(condition_config, request_data)
                if not result["passed"]:
                    violations.append(PolicyViolation(
                        policy_id=policy.id,
                        policy_name=policy.name,
                        reason=f"Keyword filter violation: {result.get('details', {}).get('found_keywords', [])}",
                        severity=policy.severity,
                        details=result.get("details", {})
                    ))
            
            elif condition_type == "content_safety":
                result = await self._evaluate_content_safety(condition_config, request_data)
                if not result["passed"]:
                    violations.append(PolicyViolation(
                        policy_id=policy.id,
                        policy_name=policy.name,
                        reason=f"Content safety violation: toxicity score {result.get('details', {}).get('max_toxicity', 0):.2f}",
                        severity=policy.severity,
                        details=result.get("details", {})
                    ))
            
            elif condition_type == "semantic":
                result = await self._evaluate_semantic(condition_config, request_data)
                if not result["passed"]:
                    violations.append(PolicyViolation(
                        policy_id=policy.id,
                        policy_name=policy.name,
                        reason="Semantic similarity violation",
                        severity=policy.severity,
                        details=result.get("details", {})
                    ))
        
        # Determine decision based on violations and policy actions
        decision = self._determine_decision(policy, violations)
        
        return PolicyEvaluationResult(
            decision=decision,
            violations=violations,
            metadata={
                "policy_id": policy.id,
                "policy_name": policy.name,
                "evaluation_time": datetime.now().isoformat()
            }
        )
    
    async def evaluate_policies(self, policies: List[PolicyResponse], request_data: Dict[str, Any]) -> PolicyEvaluationResult:
        """Evaluate multiple policies and return combined result"""
        all_violations = []
        
        for policy in policies:
            result = await self.evaluate_policy(policy, request_data)
            all_violations.extend(result.violations)
        
        # Determine overall decision based on all violations
        decision = self._determine_overall_decision(all_violations)
        
        return PolicyEvaluationResult(
            decision=decision,
            violations=all_violations,
            metadata={
                "total_policies": len(policies),
                "evaluation_time": datetime.now().isoformat()
            }
        )
    
    async def _evaluate_keyword_filter(self, config: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate keyword filter condition"""
        evaluator = self.evaluators["keyword_filter"]
        
        # Extract text from request data
        text = request_data.get("input_text", request_data.get("prompt", ""))
        if not text:
            return {"passed": True, "details": {"reason": "No text to evaluate"}}
        
        # Create evaluation request
        from protocols import EvaluationRequest
        request = EvaluationRequest(
            input_text=text,
            actual_output="",  # Not needed for keyword filtering
            expected_output="",  # Not needed for keyword filtering
            metadata=config.get("parameters", {})
        )
        
        result = await evaluator.evaluate_keyword_filter(request)
        return {
            "passed": result.passed,
            "details": result.details
        }
    
    async def _evaluate_content_safety(self, config: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate content safety condition"""
        evaluator = self.evaluators["content_safety"]
        
        text = request_data.get("input_text", request_data.get("prompt", ""))
        if not text:
            return {"passed": True, "details": {"reason": "No text to evaluate"}}
        
        from protocols import EvaluationRequest
        request = EvaluationRequest(
            input_text=text,
            actual_output="",
            expected_output="",
            metadata=config.get("parameters", {})
        )
        
        result = await evaluator.evaluate_content_safety(request)
        return {
            "passed": result.passed,
            "details": result.details
        }
    
    async def _evaluate_semantic(self, config: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate semantic similarity condition"""
        evaluator = self.evaluators["semantic"]
        
        input_text = request_data.get("input_text", request_data.get("prompt", ""))
        expected_output = request_data.get("expected_output", "")
        
        if not input_text or not expected_output:
            return {"passed": True, "details": {"reason": "Missing input or expected output"}}
        
        from protocols import EvaluationRequest
        request = EvaluationRequest(
            input_text=input_text,
            actual_output="",
            expected_output=expected_output,
            metadata=config.get("parameters", {})
        )
        
        result = await evaluator.evaluate_semantic_match(request)
        return {
            "passed": result.passed,
            "details": result.details
        }
    
    def _determine_decision(self, policy: PolicyResponse, violations: List[PolicyViolation]) -> PolicyDecision:
        """Determine decision based on policy actions and violations"""
        if not violations:
            return PolicyDecision.ALLOW
        
        actions = policy.actions
        action_type = actions.get("type", "block")
        
        if action_type == "block":
            return PolicyDecision.BLOCK
        elif action_type == "warn":
            return PolicyDecision.WARN
        else:
            # Default to block for safety
            return PolicyDecision.BLOCK
    
    def _determine_overall_decision(self, violations: List[PolicyViolation]) -> PolicyDecision:
        """Determine overall decision based on all violations"""
        if not violations:
            return PolicyDecision.ALLOW
        
        # If any critical violations, block
        critical_violations = [v for v in violations if v.severity.lower() == "critical"]
        if critical_violations:
            return PolicyDecision.BLOCK
        
        # If any violations, warn (unless all are low severity)
        low_severity_violations = [v for v in violations if v.severity.lower() == "low"]
        if len(low_severity_violations) == len(violations):
            return PolicyDecision.WARN
        
        return PolicyDecision.BLOCK 