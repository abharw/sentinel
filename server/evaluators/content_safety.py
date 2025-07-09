import asyncio
import time
from typing import Dict, Any, List, Optional
from transformers.pipelines import pipeline
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from tqdm import tqdm

from protocols import (
    ContentSafetyEvaluatorProtocol,
    EvaluationRequest, 
    EvaluationResult, 
    ModelInfo
)

class ContentSafetyEvaluator(ContentSafetyEvaluatorProtocol):
    def __init__(self, model_name: str = "unitary/toxic-bert"):
        self.name = "content_safety_evaluator"
        self.version = "0.1.0"
        self.loaded = False
        self.model_name = model_name
        self.classifier: Optional[Any] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForSequenceClassification] = None
        self._load_start_time = 0.0
        
        # Toxicity labels
        self.toxicity_labels = [
            "toxic", "severe_toxic", "obscene", "threat", 
            "insult", "identity_hate"
        ]
        
    async def load(self) -> None:
        if self.loaded:
            return 
        
        print(f"Loading {self.model_name}...")
        self._load_start_time = time.time()
        
        # Create a progress bar for model loading
        with tqdm(total=1, desc=f"Loading {self.model_name}", unit="model") as pbar:
            loop = asyncio.get_event_loop()
            
            # Load tokenizer and model
            self.tokenizer = await loop.run_in_executor(
                None, AutoTokenizer.from_pretrained, self.model_name
            )
            self.model = await loop.run_in_executor(
                None, AutoModelForSequenceClassification.from_pretrained, self.model_name
            )
            
            # Create pipeline
            self.classifier = await loop.run_in_executor(
                None, lambda: pipeline("text-classification", model=self.model_name)
            )
            
            pbar.update(1)
        
        load_time = time.time() - self._load_start_time
        self.loaded = True
        print(f"Loaded {self.model_name} in {load_time:.2f} seconds")
        
    async def unload(self) -> None:
        if not self.loaded:
            return 
    
        if self.classifier:
            del self.classifier
            self.classifier = None
        if self.model:
            del self.model
            self.model = None
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None
        self.loaded = False
        print(f"Unloaded {self.name}")
        
    async def health_check(self) -> bool:
        if not self.loaded or not self.classifier:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            if self.classifier is not None:
                await loop.run_in_executor(None, lambda: self.classifier("health check")) # type: ignore
            return True
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
        
    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            name=self.name,
            version=self.version,
            size_mb=self.estimate_model_size(),
            loaded=self.loaded,
            memory_usage_mb=self.estimate_memory_usage(),
            metadata={
                "model_type": "toxicity_classifier",
                "labels": self.toxicity_labels,
                "max_seq_length": 512,
                "supports_languages": ["en"]
            }
        )
    
    def estimate_model_size(self) -> float:
        """Estimate model size in MB"""
        return 500.0  # Approximate size for toxic-bert
    
    def estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB when model is loaded"""
        if not self.loaded:
            return 0.0
        return self.estimate_model_size() * 2.0  # Rough estimate including runtime overhead
                
    async def check_toxicity(self, text: str) -> Dict[str, float]:
        """Check toxicity levels in text"""
        if not self.loaded or not self.classifier:
            raise RuntimeError(f"{self.name} is not loaded")
        
        start_time = time.time()
        
        loop = asyncio.get_event_loop()
        if self.classifier is not None:
            results = await loop.run_in_executor(None, lambda: self.classifier(text)) # type: ignore
        else:
            raise RuntimeError("Classifier not initialized")
        
        # Extract toxicity scores
        toxicity_scores = {}
        if results and len(results) > 0:
            for label_score in results[0]:
                label = label_score['label']
                score = label_score['score']
                toxicity_scores[label] = score
        
        elapsed_time_ms = (time.time() - start_time) * 1000
        print(f"Toxicity check completed in {elapsed_time_ms:.1f}ms")
        
        return toxicity_scores
    
    async def evaluate_content_safety(self, request: EvaluationRequest) -> EvaluationResult:
        start_time = time.time()
        try:
            # Get toxicity scores
            toxicity_scores = await self.check_toxicity(request.input_text)
            
            # Calculate overall toxicity score (max of all toxicity types)
            max_toxicity = max(toxicity_scores.values()) if toxicity_scores else 0.0
            
            # Get threshold from metadata or use default
            threshold = request.metadata.get("toxicity_threshold", 0.5) if request.metadata else 0.5
            
            # Determine if content is safe
            passed = max_toxicity < threshold
            
            elapsed_time_ms = (time.time() - start_time) * 1000
            
            return EvaluationResult(
                score=1.0 - max_toxicity,  # Safety score (inverse of toxicity)
                passed=passed,
                latency_ms=elapsed_time_ms,
                details={
                    "toxicity_scores": toxicity_scores,
                    "max_toxicity": max_toxicity,
                    "threshold": threshold,
                    "method": "toxicity_classification",
                    "model": self.model_name,
                    "text_length": len(request.input_text),
                }
            )
        except Exception as e:
            elapsed_time_ms = (time.time() - start_time) * 1000
            return EvaluationResult(
                score=0.0,
                passed=False,
                latency_ms=elapsed_time_ms,
                error=str(e),
                details={
                    "error": str(e),
                    "elapsed_time_ms": elapsed_time_ms
                }
            ) 