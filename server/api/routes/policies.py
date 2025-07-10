from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

router = APIRouter()
logger = logging.getLogger(__name__)

import os

# MongoDB connection - use Atlas in production, local for development
# Will look for MONGODB_URI in environment variables (from shared/config/.env)
mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
print(f"Connecting to MongoDB: {mongodb_uri.split('@')[0]}@***")  # Hide password in logs
client = AsyncIOMotorClient(mongodb_uri)
db = client.sentinel
policies_collection = db.policies

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

@router.get("/policies", response_model=List[PolicyResponse])
async def list_policies():
    """List all policies"""
    try:
        policies = []
        async for policy_doc in policies_collection.find():
            policies.append(PolicyResponse(
                id=policy_doc["id"],
                name=policy_doc["name"],
                description=policy_doc["description"],
                severity=policy_doc["severity"],
                enabled=policy_doc["enabled"],
                conditions=policy_doc["conditions"],
                actions=policy_doc["actions"],
                created_at=policy_doc["created_at"],
                updated_at=policy_doc["updated_at"]
            ))
        return policies
    except Exception as e:
        logger.error(f"Failed to list policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/policies", response_model=PolicyResponse)
async def create_policy(policy: PolicyCreate):
    """Create a new policy"""
    try:
        now = datetime.utcnow().isoformat()
        policy_data = {
            "id": policy.id,
            "name": policy.name,
            "description": policy.description,
            "severity": policy.severity,
            "enabled": policy.enabled,
            "conditions": policy.conditions,
            "actions": policy.actions,
            "created_at": now,
            "updated_at": now
        }
        
        await policies_collection.insert_one(policy_data)
        
        logger.info(f"Created policy: {policy.id} - {policy.name}")
        
        return PolicyResponse(**policy_data)
    except Exception as e:
        logger.error(f"Failed to create policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str):
    """Get a specific policy by ID"""
    try:
        policy_doc = await policies_collection.find_one({"id": policy_id})
        if not policy_doc:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return PolicyResponse(**policy_doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(policy_id: str, policy: PolicyCreate):
    """Update an existing policy"""
    try:
        now = datetime.utcnow().isoformat()
        policy_data = {
            "id": policy.id,
            "name": policy.name,
            "description": policy.description,
            "severity": policy.severity,
            "enabled": policy.enabled,
            "conditions": policy.conditions,
            "actions": policy.actions,
            "updated_at": now
        }
        
        # Keep original creation time
        existing_policy = await policies_collection.find_one({"id": policy_id})
        if existing_policy:
            policy_data["created_at"] = existing_policy["created_at"]
        
        result = await policies_collection.replace_one(
            {"id": policy_id}, 
            policy_data
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        logger.info(f"Updated policy: {policy_id} - {policy.name}")
        
        return PolicyResponse(**policy_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str):
    """Delete a policy"""
    try:
        result = await policies_collection.delete_one({"id": policy_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        logger.info(f"Deleted policy: {policy_id}")
        
        return {"message": "Policy deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 