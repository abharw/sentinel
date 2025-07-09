from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class EvaluationRequest(BaseModel):
    input_text: str
    expected_output: str
    actual_output: str
    metadata: Optional[Dict[str, Any]] = None

class SimilarityRequest(BaseModel):
    text1: str
    text2: str

class SimilarityResponse(BaseModel):
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None

class BatchSimilarityRequest(BaseModel):
    reference_text: str
    candidate_texts: List[str]

class EvaluationResponse(BaseModel):
    score: float
    passed: bool
    details: Optional[Dict[str, Any]] = None
    latency_ms: float
    error: Optional[str] = None

class ComprehensiveEvaluationRequest(BaseModel):
    requests: List[EvaluationRequest]
    include_regression: bool = False
    baseline_results: Optional[List[EvaluationResponse]] = None 