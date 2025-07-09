from fastapi import APIRouter, HTTPException
from evaluator_manager import evaluator_manager
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def root():
    return {
        "service": "Sentinel API",
        "version": "0.1.0",
        "status": "ok",
        "docs": "/docs"
    }

@router.get("/health")
async def health_check():
    try:
        health_status = await evaluator_manager.health_check_all()
        system_info = evaluator_manager.get_system_info()
        all_ok = all(health_status.values() if health_status else [])
        return {
            "status": "ok" if all_ok else "degraded",
            "evaluators": health_status,
            "system_info": system_info,
            "timestamp": system_info.get("initialization_time_s", 0),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 