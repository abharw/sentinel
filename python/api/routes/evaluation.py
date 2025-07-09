from fastapi import APIRouter, HTTPException
from models.pydantic.evaluation import (
    SimilarityRequest, BatchSimilarityRequest, EvaluationRequest, EvaluationResponse, ComprehensiveEvaluationRequest
)
from evaluator_manager import evaluator_manager
from protocols import EvaluationRequest as EvalReq
import logging
from typing import Dict, List

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/similarity", response_model=Dict[str, float])
async def calculate_similarity(request: SimilarityRequest):
    try:
        if not evaluator_manager.semantic_evaluator or not evaluator_manager.semantic_evaluator.loaded:
            raise HTTPException(status_code=503, detail="Semantic model not loaded")
        similarity = await evaluator_manager.semantic_evaluator.calculate_similarity(
            request.text1, request.text2
        )
        return {"similarity": similarity}
    except Exception as e:
        logger.error(f"Similarity calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/similarity/batch", response_model=Dict[str, List[float]])
async def calculate_batch_similarity(request: BatchSimilarityRequest):
    try:
        if not evaluator_manager.semantic_evaluator or not evaluator_manager.semantic_evaluator.loaded:
            raise HTTPException(status_code=503, detail="Semantic model not loaded")
        similarities = await evaluator_manager.semantic_evaluator.batch_similarity(
            request.reference_text, request.candidate_texts
        )
        return {"similarities": similarities}
    except Exception as e:
        logger.error(f"Batch similarity calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/semantic", response_model=EvaluationResponse)
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

@router.post("/evaluate/performance", response_model=EvaluationResponse)
async def evaluate_performance(request: EvaluationRequest):
    try:
        if not evaluator_manager.performance_evaluator or not evaluator_manager.performance_evaluator.loaded:
            raise HTTPException(status_code=503, detail="Performance model not loaded")
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

@router.post("/evaluate/comprehensive")
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
        # Placeholder for actual comprehensive evaluation logic
        return {"status": "not_implemented"}
    except Exception as e:
        logger.error(f"Comprehensive evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 