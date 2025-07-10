from typing import Any, Dict
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