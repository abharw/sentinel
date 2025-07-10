from typing import Any, Dict, Optional
from pydantic import BaseModel

class PolicyCreate(BaseModel):
    id: str
    name: str
    description: str
    severity: str
    enabled: bool
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    provider: str

class PolicyResponse(BaseModel):
    id: str
    name: str
    description: str
    severity: str
    enabled: bool
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    provider: str
    created_at: str
    updated_at: str
    
class PolicyCheckRequest(BaseModel):
    input_text: str
    expected_output: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PolicyCheckResponse(BaseModel):
    decision: str  # "allow", "block", "warn"
    violations: list
    metadata: Dict[str, Any]