from typing import Dict, Any, Optional, List
import logging
import httpx
import asyncio
from datetime import datetime

from services.policy_runner import PolicyRunner, PolicyDecision
from models.pydantic.policy import PolicyResponse

logger = logging.getLogger(__name__)

class LLMProxyService:
    def __init__(self):
        self.policy_runner = PolicyRunner()
        self._loaded = False
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def load(self):
        """Load the policy runner"""
        if not self._loaded:
            await self.policy_runner.load()
            self._loaded = True
    
    async def process_request(
        self, 
        provider: str, 
        request_data: Dict[str, Any],
        policies: Optional[List[PolicyResponse]] = None
    ) -> Dict[str, Any]:
        """
        Process LLM request through policy checks
        
        Args:
            provider: LLM provider (e.g., "OpenAI", "Anthropic")
            request_data: Original LLM request data
            policies: Optional list of policies to check (if None, will fetch from DB)
        
        Returns:
            Dict containing either the LLM response or policy violation details
        """
        try:
            # Load policy runner if not loaded
            await self.load()
            
            # Get policies if not provided
            if policies is None:
                policies = await self._get_policies_for_provider(provider)
            
            # Extract text for policy evaluation
            input_text = self._extract_input_text(request_data)
            
            # Prepare evaluation data
            eval_data = {
                "input_text": input_text,
                "expected_output": request_data.get("expected_output", ""),
                "metadata": {
                    "provider": provider,
                    "model": request_data.get("model", ""),
                    "temperature": request_data.get("temperature", 0.7),
                    "max_tokens": request_data.get("max_tokens", 1000)
                }
            }
            
            # Evaluate policies
            result = await self.policy_runner.evaluate_policies(policies, eval_data)
            
            # Handle policy decision
            if result.decision == PolicyDecision.BLOCK:
                return self._create_blocked_response(result)
            elif result.decision == PolicyDecision.WARN:
                # Log warning but allow request
                logger.warning(f"Policy warning for provider {provider}: {result.violations}")
                return await self._forward_to_llm(provider, request_data, result)
            else:  # ALLOW
                return await self._forward_to_llm(provider, request_data, result)
                
        except Exception as e:
            logger.error(f"Error processing LLM request: {e}")
            return {
                "error": "Internal server error",
                "details": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_policies_for_provider(self, provider: str) -> List[PolicyResponse]:
        """Get all enabled policies for a provider"""
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        # Connect to MongoDB
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        client = AsyncIOMotorClient(mongodb_uri)
        db = client.sentinel
        policies_collection = db.policies
        
        # Query for enabled policies for this provider
        policies = []
        async for policy_doc in policies_collection.find({
            "enabled": True,
            "provider": provider
        }):
            policies.append(PolicyResponse(**policy_doc))
        
        return policies
    
    def _extract_input_text(self, request_data: Dict[str, Any]) -> str:
        """Extract input text from various LLM request formats"""
        # OpenAI format
        if "messages" in request_data:
            messages = request_data["messages"]
            if messages and isinstance(messages, list):
                # Get the last user message
                for message in reversed(messages):
                    if message.get("role") == "user":
                        return message.get("content", "")
        
        # Anthropic format
        if "prompt" in request_data:
            return request_data["prompt"]
        
        # Generic format
        if "input" in request_data:
            return request_data["input"]
        
        if "text" in request_data:
            return request_data["text"]
        
        # Fallback
        return str(request_data)
    
    def _create_blocked_response(self, result) -> Dict[str, Any]:
        """Create response for blocked requests"""
        violations = []
        for violation in result.violations:
            violations.append({
                "policy_id": violation.policy_id,
                "policy_name": violation.policy_name,
                "reason": violation.reason,
                "severity": violation.severity,
                "details": violation.details
            })
        
        return {
            "blocked": True,
            "reason": "Policy violation detected",
            "violations": violations,
            "timestamp": datetime.now().isoformat(),
            "metadata": result.metadata
        }
    
    async def _forward_to_llm(
        self, 
        provider: str, 
        request_data: Dict[str, Any], 
        policy_result
    ) -> Dict[str, Any]:
        """Forward request to actual LLM provider"""
        try:
            # Add policy evaluation metadata
            request_data["_policy_metadata"] = {
                "evaluated": True,
                "violations": len(policy_result.violations),
                "timestamp": datetime.now().isoformat()
            }
            
            # Route to appropriate provider
            if provider.lower() == "openai":
                return await self._call_openai(request_data)
            elif provider.lower() == "anthropic":
                return await self._call_anthropic(request_data)
            else:
                return {
                    "error": f"Unsupported provider: {provider}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error calling LLM provider {provider}: {e}")
            return {
                "error": f"LLM provider error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _call_openai(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call OpenAI API"""
        import os
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "OpenAI API key not configured"}
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Remove policy metadata before sending to OpenAI
        clean_request = {k: v for k, v in request_data.items() if not k.startswith("_")}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=clean_request
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "error": f"OpenAI API error: {response.status_code}",
                    "details": response.text,
                    "timestamp": datetime.now().isoformat()
                }
    
    async def _call_anthropic(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call Anthropic API"""
        import os
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"error": "Anthropic API key not configured"}
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Remove policy metadata before sending to Anthropic
        clean_request = {k: v for k, v in request_data.items() if not k.startswith("_")}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=clean_request
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "error": f"Anthropic API error: {response.status_code}",
                    "details": response.text,
                    "timestamp": datetime.now().isoformat()
                } 