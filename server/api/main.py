from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
import uvicorn 
import logging 
from pydantic import BaseModel

from evaluator_manager import evaluator_manager
from protocols import EvaluationRequest as EvalReq, EvaluationResult as EvalRes
from api.routes.system import router as system_router
from api.routes.evaluation import router as evaluation_router
from api.routes.chat import router as chat_router
from api.routes.policies import router as policies_router
from api.routes.llm_proxy import router as llm_proxy_router
from models.pydantic.evaluation import (
    EvaluationRequest, SimilarityRequest, SimilarityResponse, BatchSimilarityRequest,
    EvaluationResponse, ComprehensiveEvaluationRequest
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Sentinel API...")
    try:
        await evaluator_manager.load_all()
        logger.info("Sentinel API ready")
    except Exception as e:
        logger.error(f"Failed to load evaluators: {e}")
        raise
    yield
    logger.info("Shutting down Sentinel API...")
    try:
        await evaluator_manager.unload_all()
        logger.info("Sentinel API shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        raise

app = FastAPI(
    lifespan=lifespan,
    title="Sentinel API",
    description="API for Sentinel",
    version="0.1.0",
)

app.include_router(system_router)
app.include_router(evaluation_router)
app.include_router(chat_router)
app.include_router(policies_router)
app.include_router(llm_proxy_router)

# Development server entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="info"
    )


    