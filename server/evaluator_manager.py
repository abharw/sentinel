import asyncio
import time 
from typing import Dict, Any, Optional, List, Type 
import logging 
from protocols import (
    MLEvaluatorProtocol,
    BaseEvaluatorProtocol,
    EvaluationRequest,
    EvaluationResult
)

from evaluators.semantic import SemanticEvaluator
from evaluators.performance import PerformanceEvaluator
from evaluators.content_safety import ContentSafetyEvaluator
from evaluators.keyword_filter import KeywordFilterEvaluator

logger = logging.getLogger(__name__)

class EvaluatorManager:
    def __init__(self):
        self.semantic_evaluator: Optional[SemanticEvaluator] = None
        self.performance_evaluator: Optional[PerformanceEvaluator] = None
        self.content_safety_evaluator: Optional[ContentSafetyEvaluator] = None
        self.keyword_filter_evaluator: Optional[KeywordFilterEvaluator] = None
        self.quality_evaluator: Optional[BaseEvaluatorProtocol] = None # TODO: Implement quality evaluator
        self.regression_evaluator: Optional[BaseEvaluatorProtocol] = None # TODO: Implement regression evaluator
        self._initialization_time_ms = 0.0
        self.is_loading = False
        
    async def load_all(self) -> None: 
        if self.is_loading:
            logger.info("Already loading evaluators, please wait...")
            return 
        self.is_loading = True
        start_time = time.time()
        
        try:
            logger.info("Starting to load evaluators...")
            self.semantic_evaluator = SemanticEvaluator()
            self.performance_evaluator = PerformanceEvaluator()
            self.content_safety_evaluator = ContentSafetyEvaluator()
            self.keyword_filter_evaluator = KeywordFilterEvaluator()
            # will be loaded in parallel
            tasks = [
                self.semantic_evaluator.load(),
                self.performance_evaluator.load(),
                self.content_safety_evaluator.load(),
                self.keyword_filter_evaluator.load()
                # add other evaluators here
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            self.initialization_time = time.time() - start_time
            logger.info(f"Evaluators loaded in {self.initialization_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error loading evaluators: {e}")
            raise
        finally:
            self.is_loading = False
            
    async def unload_all(self) -> None:
        logger.info("Unloading all evaluators...")
        
        tasks = []
        
        if self.semantic_evaluator and self.semantic_evaluator.loaded:
            tasks.append(self.semantic_evaluator.unload())
        
        if self.performance_evaluator and self.performance_evaluator.loaded:
            tasks.append(self.performance_evaluator.unload())
        
        if self.content_safety_evaluator and self.content_safety_evaluator.loaded:
            tasks.append(self.content_safety_evaluator.unload())
        
        if self.keyword_filter_evaluator and self.keyword_filter_evaluator.loaded:
            tasks.append(self.keyword_filter_evaluator.unload())
        
        if self.quality_evaluator and self.quality_evaluator.loaded:
            tasks.append(self.quality_evaluator.unload())
        
        if self.regression_evaluator and self.regression_evaluator.loaded:
            tasks.append(self.regression_evaluator.unload())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("All evaluators unloaded")
        
    async def health_check_all(self) -> Dict[str, bool]:
        results = {}
        
        if self.semantic_evaluator and self.semantic_evaluator.loaded:
            results["semantic"] = await self.semantic_evaluator.health_check()
            
        if self.performance_evaluator and self.performance_evaluator.loaded:
            results["performance"] = await self.performance_evaluator.health_check()
            
        if self.content_safety_evaluator and self.content_safety_evaluator.loaded:
            results["content_safety"] = await self.content_safety_evaluator.health_check()
            
        if self.keyword_filter_evaluator and self.keyword_filter_evaluator.loaded:
            results["keyword_filter"] = await self.keyword_filter_evaluator.health_check()
            
        if self.quality_evaluator and self.quality_evaluator.loaded:
            results["quality"] = await self.quality_evaluator.health_check()
            
        if self.regression_evaluator and self.regression_evaluator.loaded:
            results["regression"] = await self.regression_evaluator.health_check()
            
        return results
    
    async def evaluate_comprehensive(self, requests: List[EvaluationRequest], include_regression: bool = False, baseline_results: Optional[List[EvaluationResult]] = None) -> Dict[str, Any]:
        if not requests:
            raise ValueError("No evaluation requests provided")
        
        start_time = time.time()
        results = {
            "total_requests": len(requests),
            "evaluations": {},
            "summary": {},
            "timing": {}
        }
        
        try: 
            if self.semantic_evaluator and self.semantic_evaluator.loaded:
                eval_start = time.time()
                semantic_results = []
                
                for request in requests:
                    result = await self.semantic_evaluator.evaluate_semantic_match(request)
                    semantic_results.append(result)
            
                results["evaluations"]["semantic"] = [dict(r) for r in semantic_results]
                results["timing"]["semantic_ms"] = (time.time() - eval_start) * 1000
                
            if self.performance_evaluator and self.performance_evaluator.loaded:
                eval_start = time.time()
                performance_results = []
                
                for request in requests:
                    latency_ms = request.metadata.get("latency_ms", 100.0) if request.metadata else 100.0
                    result = await self.performance_evaluator.evaluate_efficiency(request)
                    performance_results.append(result)
                    
                results["evaluations"]["performance"] = [dict(r) for r in performance_results]
                results["timing"]["performance_ms"] = (time.time() - eval_start) * 1000
                
            # TODO: Add quality and regression evaluations
            if include_regression and baseline_results:
                results["regression"] = {"status": "not_implemented"}
                        
            
            results["summary"] = self._calculate_summary(results["evaluations"])
            results["timing"]["total_ms"] = (time.time() - start_time) * 1000
            
            
            logger.info(f"Evaluation completed in {results['timing']['total_ms']:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            results["error"] = str(e)
        
        return results
            
    def get_system_info(self) -> Dict[str, Any]:
        info = {
            "initialization_time": self._initialization_time_ms,
            "is_loading": self.is_loading,
            "evaluators": {}
        }
        if self.semantic_evaluator:
            info["evaluators"]["semantic"] = self.semantic_evaluator.get_model_info().__dict__
        
        if self.performance_evaluator:
            info["evaluators"]["performance"] = self.performance_evaluator.get_model_info().__dict__
        
        if self.content_safety_evaluator:
            info["evaluators"]["content_safety"] = self.content_safety_evaluator.get_model_info().__dict__
        
        if self.keyword_filter_evaluator:
            info["evaluators"]["keyword_filter"] = self.keyword_filter_evaluator.get_model_info().__dict__
        
        if self.quality_evaluator:
            info["evaluators"]["quality"] = self.quality_evaluator.get_model_info().__dict__
        
        if self.regression_evaluator:
            info["evaluators"]["regression"] = self.regression_evaluator.get_model_info().__dict__
        
        return info
    
    def _calculate_summary(self, evaluations: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        summary = {}
        
        for eval_type, results in evaluations.items():
            if not results:
                continue
            
            scores = [r.get("score", 0.0) for r in results]
            passed_count = sum(1 for r in results if r.get("passed", False))
            
            summary[eval_type] = {
                "total_tests": len(results),
                "passed_tests": passed_count,
                "pass_rate": passed_count / len(results),
                "avg_score": sum(scores) / len(scores) if scores else 0.0,
                "min_score": min(scores) if scores else 0.0,
                "max_score": max(scores) if scores else 0.0,
                "avg_latency_ms": sum(r.get("latency_ms", 0.0) for r in results) / len(results)
            }
        
        return summary


evaluator_manager = EvaluatorManager()