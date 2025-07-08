from typing import Protocol, Dict, Any, Optional, List, Union
from dataclasses import dataclass, field

@dataclass
class EvaluationRequest:
    input_text: str
    expected_output: str
    actual_output: str
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
@dataclass
class EvaluationResult:
    score: float
    passed: bool 
    details: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class ModelInfo:
    name: str
    version: str
    size_mb: float
    loaded: bool
    memory_usage_mb: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
            
class BaseEvaluatorProtocol(Protocol):
    name: str
    loaded: bool
    version: str
    
        
    async def load(self) -> None:
        ...
    
    async def unload(self) -> None:
        ...
    
    async def health_check(self) -> bool:
        ...
    
    def get_model_info(self) -> ModelInfo:
        ...
        
class SemanticEvaluatorProtocol(BaseEvaluatorProtocol, Protocol):
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        ...
    
    async def batch_similarity(self, reference: str, candidates: List[str]) -> List[float]:
        """Calculate similarity between reference and multiple candidates"""
        ...
    
    async def evaluate_semantic_match(self, request: EvaluationRequest) -> EvaluationResult:
        ...

class PerformanceEvaluatorProtocol(BaseEvaluatorProtocol, Protocol):
    
    async def calculate_performance_score(
        self, 
        input_text: str, 
        output_text: str,
        latency_ms: float,
        token_count: Optional[int] = None
    ) -> float:
        """Calculate overall performance score (0.0 to 1.0)"""
        ...
    
    async def evaluate_latency(self, latency_ms: float, max_latency_ms: float) -> EvaluationResult:
        ...
    
    async def evaluate_efficiency(self, request: EvaluationRequest) -> EvaluationResult:
        ...

class QualityEvaluatorProtocol(BaseEvaluatorProtocol, Protocol):
    
    async def evaluate_coherence(self, text: str) -> float:
        """Evaluate text coherence (0.0 to 1.0)"""
        ...
    
    async def evaluate_sentiment(self, text: str, expected_sentiment: str) -> EvaluationResult:
        ...
    
    async def evaluate_toxicity(self, text: str, max_toxicity: float = 0.1) -> EvaluationResult:
        """Evaluate if text toxicity is below threshold"""
        ...
    
    async def evaluate_language(self, text: str, expected_language: str = "en") -> EvaluationResult:
        ...

class RegressionDetectorProtocol(BaseEvaluatorProtocol, Protocol):
    
    async def detect_regression(
        self, 
        current_results: List[EvaluationResult],
        baseline_results: List[EvaluationResult],
        significance_level: float = 0.05
    ) -> Dict[str, Any]:
        ...
    
    async def calculate_trend(self, results: List[EvaluationResult]) -> Dict[str, float]:
        ...

class MLEvaluatorProtocol(Protocol):
    
    semantic: SemanticEvaluatorProtocol
    performance: PerformanceEvaluatorProtocol
    quality: QualityEvaluatorProtocol
    regression: RegressionDetectorProtocol
    
    async def load_all(self) -> None:
        """Load all evaluator models"""
        ...
    
    async def unload_all(self) -> None:
        """Unload all evaluator models"""
        ...
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all evaluators"""
        ...
    
    async def evaluate_comprehensive(
        self, 
        requests: List[EvaluationRequest],
        include_regression: bool = False,
        baseline_results: Optional[List[EvaluationResult]] = None
    ) -> Dict[str, Any]:
        """Run comprehensive evaluation across all evaluators"""
        ...
