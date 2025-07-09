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

@app.get("/")
async def root():
    return {
        "service": "Sentinel API",
        "version": "0.1.0",
        "status": "ok",
        "docs": "/docs" # TODO: Add docs with Swagger UI
    }

@app.get("/health")
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
    
    
@app.post("/similarity", response_model=Dict[str, float])
async def calculate_similarity(request: SimilarityRequest):
    """Calculate semantic similarity between two texts"""
    try:
        if not evaluator_manager.semantic_evaluator or not evaluator_manager.semantic_evaluator.loaded:
            raise HTTPException(status_code=503, detail="Semantic model not loaded")
        
        similarity = await evaluator_manager.semantic_evaluator.calculate_similarity(
            request.text1, 
            request.text2
        )
        
        return {"similarity": similarity}
        
    except Exception as e:
        logger.error(f"Similarity calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/similarity/batch", response_model=Dict[str, List[float]])
async def calculate_batch_similarity(request: BatchSimilarityRequest):
    try:
        if not evaluator_manager.semantic_evaluator or not evaluator_manager.semantic_evaluator.loaded:
            raise HTTPException(status_code=503, detail="Semantic model not loaded")
        
        similarities = await evaluator_manager.semantic_evaluator.batch_similarity(
            request.reference_text,
            request.candidate_texts
        )
        
        return {"similarities": similarities}
        
    except Exception as e:
        logger.error(f"Batch similarity calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate/semantic", response_model=EvaluationResponse)
async def evaluate_semantic(request: EvaluationRequest):
    try:
        if not evaluator_manager.semantic_evaluator or not evaluator_manager.semantic_evaluator.loaded:
            raise HTTPException(status_code=503, detail="Semantic model not loaded")
        
        eval_request = EvalReq(
            input_text=request.input_text,
            expected_output=request.expected_output,
            actual_output=request.actual_output,
            metadata=request.metadata or {}
        )
        
        result = await evaluator_manager.semantic_evaluator.evaluate_semantic_match(eval_request)
        
        return EvaluationResponse(
            score=result.score,
            passed=result.passed,
            details=result.details,
            latency_ms=result.latency_ms,
            error=result.error
        )
        
    except Exception as e:
        logger.error(f"Semantic evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate/performance", response_model=EvaluationResponse)
async def evaluate_performance(request: EvaluationRequest):
    try:
        if not evaluator_manager.performance_evaluator or not evaluator_manager.performance_evaluator.loaded:
            raise HTTPException(status_code=503, detail="Performance model not loaded")
        
        # Convert to internal format
        eval_request = EvalReq(
            input_text=request.input_text,
            expected_output=request.expected_output,
            actual_output=request.actual_output,
            metadata=request.metadata or {}
        )
        
        result = await evaluator_manager.performance_evaluator.evaluate_efficiency(eval_request)
        
        return EvaluationResponse(
            score=result.score,
            passed=result.passed,
            details=result.details,
            latency_ms=result.latency_ms,
            error=result.error
        )
        
    except Exception as e:
        logger.error(f"Performance evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate/comprehensive")
async def evaluate_comprehensive(request: ComprehensiveEvaluationRequest):
    try:
        eval_requests = [
            EvalReq(
                input_text=req.input_text,
                expected_output=req.expected_output,
                actual_output=req.actual_output,
                metadata=req.metadata or {}
            )
            for req in request.requests
        ]
        
        # TODO: Convert baseline_results if provided
        baseline_results = None
        if request.baseline_results:
            # would need proper conversion from dict to EvaluationResult
            pass
        
        results = await evaluator_manager.evaluate_comprehensive(
            eval_requests,
            include_regression=request.include_regression,
            baseline_results=baseline_results
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Comprehensive evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/info")
async def get_models_info():
    try:
        return evaluator_manager.get_system_info()
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/reload")
async def reload_models(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(_reload_models_task)
        return {"message": "Model reload initiated in background"}
    except Exception as e:
        logger.error(f"Failed to initiate model reload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _reload_models_task():
    try:
        logger.info("Reloading models...")
        await evaluator_manager.unload_all()
        await evaluator_manager.load_all()
        logger.info("Models reloaded successfully")
    except Exception as e:
        logger.error(f"Model reload failed: {e}")

# Development server entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="info"
    )


    