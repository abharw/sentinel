import asyncio 
import time 
import statistics
from typing import Dict, Any, Optional, List

from protocols import (
    PerformanceEvaluatorProtocol,
    EvaluationRequest,
    EvaluationResult,
    ModelInfo
)

class PerformanceEvaluator(PerformanceEvaluatorProtocol):
    def __init__(self):
        self.name = "performance_evaluator"
        self.version = "1.0.0"
        self.loaded = False
        self._metrics_history: List[Dict[str, float]] = []
        
    async def load(self) -> None:
        if self.loaded:
            return 
        
        print(f"Loading {self.name}...")
        self.loaded = True
        print(f"{self.name} loaded successfully")
        
    async def unload(self) -> None:
        self.loaded = False
        self._metrics_history.clear()
    
    async def health_check(self) -> bool:
        return self.loaded
    
    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            name=self.name,
            version="1.0.0",
            size_mb=0.1,
            loaded=self.loaded,
            memory_usage_mb=10.0,
            metadata={
                "type": "heuristic_evaluator",
                "metrics": ["latency", "efficiency", "coherence"],
                "requires_gpu": False,
                "history_count": len(self._metrics_history)
            }
        )
        
    async def calculate_performance_score(self, input_text: str, output_text: str, latency_ms: float, token_count: Optional[int] = None) -> float:
        if not self.loaded:
            raise RuntimeError(f"{self.name} not loaded")
            
        scores = []
        
        # Latency score (lower is better, normalized to 5s max)
        latency_score = max(0, 1 - latency_ms / 5000)
        scores.append(latency_score)
        
        # Efficiency score (output quality vs input length)
        efficiency_score = self._calculate_efficiency_score(input_text, output_text)
        scores.append(efficiency_score)
        
        # Response completeness
        completeness_score = self._calculate_completeness_score(output_text)
        scores.append(completeness_score)
        
        # Token efficiency (if available)
        if token_count:
            token_efficiency = self._calculate_token_efficiency(input_text, output_text, token_count)
            scores.append(token_efficiency)
        
        overall_score = statistics.mean(scores)
        
        # Store metrics for trend analysis
        self._metrics_history.append({
            "timestamp": time.time(),
            "latency_ms": latency_ms,
            "efficiency": efficiency_score,
            "completeness": completeness_score,
            "overall": overall_score
        })
        
        # Keep history bounded
        if len(self._metrics_history) > 1000:
            self._metrics_history = self._metrics_history[-500:]
        
        return overall_score
    
    async def evaluate_latency(self, latency_ms: float, max_latency_ms: float) -> EvaluationResult:
            """Evaluate if latency meets requirements"""
            if not self.loaded:
                raise RuntimeError(f"{self.name} not loaded")
            
            passed = latency_ms <= max_latency_ms
            score = max(0, (max_latency_ms - latency_ms) / max_latency_ms)
            
            return EvaluationResult(
                score=score,
                passed=passed,
                latency_ms=0.1,  # This evaluation is very fast
                details={
                    "actual_latency_ms": latency_ms,
                    "max_latency_ms": max_latency_ms,
                    "latency_ratio": latency_ms / max_latency_ms,
                    "performance_category": self._categorize_latency(latency_ms)
                }
            )
    
    async def evaluate_efficiency(self, request: EvaluationRequest) -> EvaluationResult:
        """Evaluate token efficiency and response quality"""
        if not self.loaded:
            raise RuntimeError(f"{self.name} not loaded")
        
        start_time = time.time()
        
        try:
            input_text = request.input_text
            output_text = request.actual_output
            
            # Calculate various efficiency metrics
            length_ratio = len(output_text) / max(len(input_text), 1)
            word_ratio = len(output_text.split()) / max(len(input_text.split()), 1)
            
            # Quality indicators
            has_punctuation = any(p in output_text for p in '.!?')
            proper_capitalization = output_text and output_text[0].isupper()
            no_repetition = self._check_repetition(output_text)
            
            # Calculate efficiency score
            efficiency_score = self._calculate_efficiency_score(input_text, output_text)
            
            # Determine if efficient (reasonable length, good quality)
            passed = (
                0.5 <= length_ratio <= 5.0 and  # Reasonable length ratio
                efficiency_score >= 0.6 and     # Good efficiency
                has_punctuation and             # Proper formatting
                no_repetition                   # No excessive repetition
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return EvaluationResult(
                score=efficiency_score,
                passed=passed,
                latency_ms=elapsed_ms,
                details={
                    "length_ratio": length_ratio,
                    "word_ratio": word_ratio,
                    "has_punctuation": has_punctuation,
                    "proper_capitalization": proper_capitalization,
                    "no_repetition": no_repetition,
                    "input_length": len(input_text),
                    "output_length": len(output_text)
                }
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return EvaluationResult(
                score=0.0,
                passed=False,
                latency_ms=elapsed_ms,
                error=str(e),
                details={"error_type": type(e).__name__}
            )
    
    def _calculate_efficiency_score(self, input_text: str, output_text: str) -> float:
        """Calculate efficiency score based on input/output characteristics"""
        if not output_text:
            return 0.0
        
        scores = []
        
        # Length appropriateness (not too short, not too long)
        input_len = len(input_text)
        output_len = len(output_text)
        
        if input_len > 0:
            ratio = output_len / input_len
            # Optimal ratio is between 1-3 for most cases
            if 1 <= ratio <= 3:
                length_score = 1.0
            elif 0.5 <= ratio < 1 or 3 < ratio <= 5:
                length_score = 0.7
            else:
                length_score = max(0, 0.5 - abs(ratio - 2) * 0.1)
            scores.append(length_score)
        
        # Content quality indicators
        word_count = len(output_text.split())
        if word_count >= 3:  # At least a few words
            scores.append(0.8)
        elif word_count >= 1:
            scores.append(0.4)
        else:
            scores.append(0.0)
        
        # Structure indicators
        structure_score = 0.5  # Base score
        if any(p in output_text for p in '.!?'):
            structure_score += 0.2
        if output_text and output_text[0].isupper():
            structure_score += 0.1
        if self._check_repetition(output_text):
            structure_score += 0.2
        
        scores.append(min(structure_score, 1.0))
        
        return statistics.mean(scores) if scores else 0.0
    
    def _calculate_completeness_score(self, text: str) -> float:
        """Score text completeness"""
        if not text:
            return 0.0
        
        score = 0.5  # Base score
        
        # Ends with proper punctuation
        if text.rstrip().endswith(('.', '!', '?')):
            score += 0.3
        
        # Has reasonable length
        if 10 <= len(text) <= 500:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_token_efficiency(self, input_text: str, output_text: str, token_count: int) -> float:
        """Calculate token efficiency score"""
        if token_count <= 0:
            return 0.0
        
        # Rough estimate: 4 characters per token
        estimated_tokens = len(output_text) / 4
        efficiency = min(estimated_tokens / token_count, 1.0)
        
        return efficiency
    
    def _check_repetition(self, text: str) -> bool:
        """Check if text has excessive repetition"""
        words = text.lower().split()
        if len(words) < 2:
            return True
        
        unique_words = set(words)
        repetition_ratio = len(unique_words) / len(words)
        
        return repetition_ratio >= 0.6  # At least 60% unique words
    
    def _categorize_latency(self, latency_ms: float) -> str:
        """Categorize latency performance"""
        if latency_ms < 500:
            return "excellent"
        elif latency_ms < 1000:
            return "good"
        elif latency_ms < 2000:
            return "acceptable"
        elif latency_ms < 5000:
            return "slow"
        else:
            return "very_slow"