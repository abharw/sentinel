from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from services.llm_proxy import LLMProxyService

router = APIRouter()
logger = logging.getLogger(__name__)

class LLMRequest(BaseModel):
    provider: str
    request_data: Dict[str, Any]

class LLMResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    blocked: Optional[bool] = None
    violations: Optional[list] = None
    timestamp: str

@router.post("/llm/chat", response_model=LLMResponse)
async def chat_completion(request: LLMRequest):
    """Process LLM chat completion through policy checks"""
    try:
        proxy = LLMProxyService()
        result = await proxy.process_request(
            provider=request.provider,
            request_data=request.request_data
        )
        
        return LLMResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/llm/{provider}/chat", response_model=LLMResponse)
async def provider_chat_completion(provider: str, request_data: Dict[str, Any]):
    """Process LLM chat completion for specific provider"""
    try:
        proxy = LLMProxyService()
        result = await proxy.process_request(
            provider=provider,
            request_data=request_data
        )
        
        return LLMResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in {provider} chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 