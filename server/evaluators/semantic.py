import asyncio
import time
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

from protocols import (
    SemanticEvaluatorProtocol, 
    EvaluationRequest, 
    EvaluationResult, 
    ModelInfo
)

class SemanticEvaluator(SemanticEvaluatorProtocol):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.name = "semantic_evaluator"
        self.version = "0.1.0"
        self.loaded = False
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self._load_start_time = 0.0
        
    async def load(self) -> None:
        if self.loaded:
            return 
        
        print(f"Loading {self.model_name}...")
        
        # Create a progress bar for model loading
        with tqdm(total=1, desc=f"Loading {self.model_name}", unit="model") as pbar:
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(None, SentenceTransformer, self.model_name)
            pbar.update(1)
        
        load_time = time.time() - self._load_start_time
        self.loaded = True
        print(f"Loaded {self.model_name} in {load_time:.2f} seconds")
        
    async def unload(self) -> None:
        if not self.loaded:
            return 
    
        if self.model:
            del self.model
            self.model = None
        self.loaded = False
        print(f"Unloaded {self.name}")
        
    async def health_check(self) -> bool:
        if not self.loaded or not self.model:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.model.encode(["health check"]))  # type: ignore
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
                "model_type": "sentence_transformer",
                "embedding_dim": 384,  # for MiniLM
                "max_seq_length": 256,
                "supports_languages": ["en"] if "multilingual" not in self.model_name else ["multi"]
            }
        )
    
    def estimate_model_size(self) -> float:
        """Estimate model size in MB based on model name"""
        if "MiniLM" in self.model_name:
            return 80.0  # Approximate size for MiniLM models
        elif "all-mpnet" in self.model_name:
            return 420.0  # Approximate size for MPNet models
        else:
            return 100.0  # Default estimate
    
    def estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB when model is loaded"""
        if not self.loaded:
            return 0.0
        return self.estimate_model_size() * 1.5  # Rough estimate including runtime overhead
                
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        if not self.loaded or not self.model:
            raise RuntimeError(f"{self.name} is not loaded")
        
        start_time = time.time()
        
        # Create a progress bar for similarity calculation
        with tqdm(total=2, desc="Calculating similarity", unit="step") as pbar:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, lambda: self.model.encode([text1, text2])) # type: ignore
            pbar.update(1)
            
            # Reshape embeddings to 2D arrays for cosine_similarity
            embedding1 = embeddings[0].reshape(1, -1)
            embedding2 = embeddings[1].reshape(1, -1)
            similarity = cosine_similarity(embedding1, embedding2)[0][0]
            pbar.update(1)
        
        elapsed_time_ms = (time.time() - start_time) * 1000
        print(f"Similarity calculated in {elapsed_time_ms:.1f}ms: {similarity:.3f}")
        return similarity
    
    async def batch_similarity(self, reference: str, candidates: List[str]) -> List[float]:
        if not self.loaded or not self.model:
            raise RuntimeError(f"{self.name} is not loaded")
        
        if not candidates:
            return [] 
        
        start_time = time.time()
        all_texts = [reference] + candidates
        
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, lambda: self.model.encode(all_texts)) # type: ignore
        
        # Get reference and candidate embeddings
        ref_embedding = embeddings[0:1]  # Already 2D
        candidate_embeddings = embeddings[1:]  # Already 2D
        
        # Calculate similarities
        similarities = cosine_similarity(ref_embedding, candidate_embeddings)[0]
        
        elapsed_time_ms = (time.time() - start_time) * 1000
        print(f"Batch similarity calculated in {elapsed_time_ms:.1f}ms")
        return similarities.tolist()
    
    async def evaluate_semantic_match(self, request: EvaluationRequest) -> EvaluationResult:
        start_time = time.time()
        try: 
            similarity = await self.calculate_similarity(request.expected_output, request.actual_output)

            thresholds = request.metadata.get("thresholds", 0.75) if request.metadata else 0.75
            
            passed = similarity >= thresholds
            elapsed_time_ms = (time.time() - start_time) * 1000
            
            return EvaluationResult(
                score=similarity,
                passed=passed,
                latency_ms=elapsed_time_ms,
                details={
                    "similarity_score": similarity,
                    "threshold": thresholds,
                    "method": "cosine_similarity",
                    "model": self.model_name,
                    "input_length": len(request.expected_output),
                    "output_length": len(request.actual_output),
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
    
    def _estimate_model_size(self) -> float:
        size_map = {
            "all-MiniLM-L6-v2": 80.0,
            "all-mpnet-base-v2": 420.0,
            "paraphrase-multilingual-MiniLM-L12-v2": 470.0,
            "all-distilroberta-v1": 290.0
        }
        return size_map.get(self.model_name, 100.0)
    
    def _estimate_memory_usage(self) -> float:

        if not self.loaded:
            return 0.0
        
        # Rough estimates - use actual memory profiling in production
        usage_map = {
            "all-MiniLM-L6-v2": 400.0,
            "all-mpnet-base-v2": 800.0,
            "paraphrase-multilingual-MiniLM-L12-v2": 900.0,
            "all-distilroberta-v1": 600.0
        }
        return usage_map.get(self.model_name, 500.0)