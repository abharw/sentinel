import asyncio
import time
import re
from typing import Dict, Any, List, Optional, Set
from tqdm import tqdm

from protocols import (
    KeywordFilterEvaluatorProtocol,
    EvaluationRequest, 
    EvaluationResult, 
    ModelInfo
)

class KeywordFilterEvaluator(KeywordFilterEvaluatorProtocol):
    def __init__(self):
        self.name = "keyword_filter_evaluator"
        self.version = "0.1.0"
        self.loaded = False
        self._load_start_time = 0.0
        
        # Default banned keywords (can be loaded from config)
        self.banned_keywords: Set[str] = set()
        self.banned_patterns: List[str] = []
        
    async def load(self) -> None:
        if self.loaded:
            return 
        
        print(f"Loading {self.name}...")
        self._load_start_time = time.time()
        
        # Load banned keywords and patterns
        await self.load_banned_keywords()
        
        load_time = time.time() - self._load_start_time
        self.loaded = True
        print(f"Loaded {self.name} in {load_time:.2f} seconds")
        
    async def unload(self) -> None:
        if not self.loaded:
            return 
    
        self.banned_keywords.clear()
        self.banned_patterns.clear()
        self.loaded = False
        print(f"Unloaded {self.name}")
        
    async def health_check(self) -> bool:
        if not self.loaded:
            return False
        
        try:
            # Simple health check - try to check a benign text
            await self.check_keywords("This is a test message.")
            return True
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
        
    def get_model_info(self) -> ModelInfo:
        return ModelInfo(
            name=self.name,
            version=self.version,
            size_mb=0.1,  # Very small, just keyword lists
            loaded=self.loaded,
            memory_usage_mb=1.0,  # Minimal memory usage
            metadata={
                "model_type": "keyword_filter",
                "banned_keywords_count": len(self.banned_keywords),
                "banned_patterns_count": len(self.banned_patterns),
                "supports_languages": ["en"]
            }
        )
    
    async def load_banned_keywords(self) -> None:
        """Load banned keywords from configuration"""
        # Default banned keywords (in production, load from database/config)
        default_keywords = {
            # Profanity
            "fuck", "shit", "bitch", "asshole", "damn", "hell",
            # Hate speech
            "nazi", "racist", "bigot", "hate",
            # Violence
            "kill", "murder", "bomb", "terrorist", "attack",
            # Drugs
            "cocaine", "heroin", "meth", "drugs",
            # Other
            "spam", "scam", "phishing"
        }
        
        self.banned_keywords = default_keywords
        
        # Load custom keywords from environment or config file
        # TODO: Implement loading from shared/config/banned_keywords.txt
        print(f"Loaded {len(self.banned_keywords)} banned keywords")
        
    async def check_keywords(self, text: str) -> Dict[str, Any]:
        """Check for banned keywords in text"""
        if not self.loaded:
            raise RuntimeError(f"{self.name} is not loaded")
        
        start_time = time.time()
        
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Find banned keywords
        found_keywords = []
        for keyword in self.banned_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        # Check regex patterns
        found_patterns = []
        for pattern in self.banned_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found_patterns.append(pattern)
        
        # Calculate severity score
        severity_score = min(1.0, (len(found_keywords) + len(found_patterns)) * 0.3)
        
        elapsed_time_ms = (time.time() - start_time) * 1000
        print(f"Keyword check completed in {elapsed_time_ms:.1f}ms")
        
        return {
            "found_keywords": found_keywords,
            "found_patterns": found_patterns,
            "severity_score": severity_score,
            "total_violations": len(found_keywords) + len(found_patterns)
        }
    
    async def evaluate_keyword_filter(self, request: EvaluationRequest) -> EvaluationResult:
        start_time = time.time()
        try:
            # Check for banned keywords
            keyword_results = await self.check_keywords(request.input_text)
            
            # Get threshold from metadata or use default
            threshold = request.metadata.get("keyword_threshold", 0.1) if request.metadata else 0.1
            
            # Determine if content passes keyword filter
            passed = keyword_results["severity_score"] < threshold
            
            elapsed_time_ms = (time.time() - start_time) * 1000
            
            return EvaluationResult(
                score=1.0 - keyword_results["severity_score"],  # Safety score
                passed=passed,
                latency_ms=elapsed_time_ms,
                details={
                    "found_keywords": keyword_results["found_keywords"],
                    "found_patterns": keyword_results["found_patterns"],
                    "severity_score": keyword_results["severity_score"],
                    "threshold": threshold,
                    "method": "keyword_filtering",
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