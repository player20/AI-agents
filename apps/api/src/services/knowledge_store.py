"""
Knowledge Store

Vector-based storage for domain patterns learned from successful generations.

This module provides:
1. Pattern storage - Save successful generation patterns
2. Pattern retrieval - Find similar patterns for new queries
3. Learning - Improve patterns based on user feedback
4. Pruning - Remove low-performing patterns

Uses ChromaDB for local vector storage with embedding-based similarity search.
"""

import logging
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class DomainPattern:
    """
    A learned pattern from a successful generation.

    Stores the key elements that made a generation successful,
    so similar future queries can benefit from this knowledge.
    """
    pattern_id: str
    industry: str
    description_keywords: List[str]

    # Domain analysis elements
    terminology: Dict[str, str] = field(default_factory=dict)
    key_entities: List[str] = field(default_factory=list)
    key_metrics: List[str] = field(default_factory=list)
    suggested_sections: List[str] = field(default_factory=list)

    # Architecture elements
    page_structure: List[str] = field(default_factory=list)
    stat_cards: List[str] = field(default_factory=list)

    # Quality metrics
    user_rating: float = 0.0  # 0-5 stars
    success_count: int = 1
    failure_count: int = 0

    # Metadata
    created_at: str = ""
    last_used_at: str = ""

    @property
    def confidence(self) -> float:
        """Calculate confidence based on usage and ratings"""
        if self.success_count + self.failure_count == 0:
            return 0.5

        success_rate = self.success_count / (self.success_count + self.failure_count)
        rating_factor = self.user_rating / 5.0 if self.user_rating > 0 else 0.5
        usage_factor = min(1.0, (self.success_count + self.failure_count) / 10)

        return (success_rate * 0.5) + (rating_factor * 0.3) + (usage_factor * 0.2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainPattern":
        return cls(**data)


@dataclass
class PatternMatch:
    """Result of a pattern similarity search"""
    pattern: DomainPattern
    similarity: float
    relevance_score: float  # Combined similarity + confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern.to_dict(),
            "similarity": self.similarity,
            "relevance_score": self.relevance_score,
        }


class DomainKnowledgeStore:
    """
    Vector store for domain patterns and successful generations.

    Uses ChromaDB for embedding-based similarity search.
    Falls back to simple keyword matching if ChromaDB unavailable.
    """

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        collection_name: str = "domain_patterns",
    ):
        """
        Initialize the knowledge store.

        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the ChromaDB collection
        """
        self.persist_dir = persist_directory or Path(__file__).parent.parent / "data" / "knowledge_store"
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._fallback_patterns: Dict[str, DomainPattern] = {}
        self._use_chromadb = True

        self._init_store()

    def _init_store(self) -> None:
        """Initialize ChromaDB or fallback storage"""
        try:
            import chromadb
            from chromadb.config import Settings

            self.persist_dir.mkdir(parents=True, exist_ok=True)

            self._client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.persist_dir),
                anonymized_telemetry=False,
            ))

            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Domain patterns from successful generations"},
            )

            logger.info(f"ChromaDB initialized with {self._collection.count()} patterns")

        except ImportError:
            logger.warning("chromadb not installed. Using fallback storage. Run: pip install chromadb")
            self._use_chromadb = False
            self._load_fallback_patterns()
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}. Using fallback storage.")
            self._use_chromadb = False
            self._load_fallback_patterns()

    def _load_fallback_patterns(self) -> None:
        """Load patterns from JSON fallback storage"""
        try:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            fallback_file = self.persist_dir / "patterns_fallback.json"

            if fallback_file.exists():
                data = json.loads(fallback_file.read_text())
                for pattern_id, pattern_data in data.items():
                    self._fallback_patterns[pattern_id] = DomainPattern.from_dict(pattern_data)
                logger.info(f"Loaded {len(self._fallback_patterns)} patterns from fallback storage")
        except Exception as e:
            logger.warning(f"Failed to load fallback patterns: {e}")

    def _save_fallback_patterns(self) -> None:
        """Save patterns to JSON fallback storage"""
        try:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            fallback_file = self.persist_dir / "patterns_fallback.json"

            data = {pid: p.to_dict() for pid, p in self._fallback_patterns.items()}
            fallback_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save fallback patterns: {e}")

    def _generate_pattern_id(self, industry: str, keywords: List[str]) -> str:
        """Generate unique pattern ID"""
        content = f"{industry}:{':'.join(sorted(keywords[:10]))}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _create_document(self, pattern: DomainPattern) -> str:
        """Create a searchable document from pattern"""
        parts = [
            f"Industry: {pattern.industry}",
            f"Keywords: {', '.join(pattern.description_keywords)}",
            f"Entities: {', '.join(pattern.key_entities)}",
            f"Metrics: {', '.join(pattern.key_metrics)}",
            f"Sections: {', '.join(pattern.suggested_sections)}",
        ]
        return " | ".join(parts)

    async def store_pattern(
        self,
        industry: str,
        description_keywords: List[str],
        domain_analysis: Dict[str, Any],
        architecture: Dict[str, Any],
        user_rating: float = 0.0,
    ) -> str:
        """
        Store a new pattern from a successful generation.

        Args:
            industry: Industry classification
            description_keywords: Keywords from the user's description
            domain_analysis: Domain analysis result from Agent 1
            architecture: Architecture result from Agent 2
            user_rating: Optional user rating (0-5)

        Returns:
            Pattern ID
        """
        pattern_id = self._generate_pattern_id(industry, description_keywords)

        pattern = DomainPattern(
            pattern_id=pattern_id,
            industry=industry,
            description_keywords=description_keywords,
            terminology=domain_analysis.get("terminology", {}),
            key_entities=domain_analysis.get("key_entities", []),
            key_metrics=domain_analysis.get("metrics", []),
            suggested_sections=domain_analysis.get("suggested_sections", []),
            page_structure=[p.get("title", "") for p in architecture.get("pages", [])],
            stat_cards=[s.get("title", "") for s in architecture.get("stat_cards", [])],
            user_rating=user_rating,
            created_at=datetime.utcnow().isoformat(),
            last_used_at=datetime.utcnow().isoformat(),
        )

        if self._use_chromadb and self._collection:
            # Store in ChromaDB
            document = self._create_document(pattern)

            self._collection.upsert(
                ids=[pattern_id],
                documents=[document],
                metadatas=[{
                    "industry": industry,
                    "confidence": pattern.confidence,
                    "success_count": pattern.success_count,
                    "user_rating": user_rating,
                    "created_at": pattern.created_at,
                }],
            )

            # Also store full pattern data
            self._fallback_patterns[pattern_id] = pattern
            self._save_fallback_patterns()
        else:
            # Fallback storage
            self._fallback_patterns[pattern_id] = pattern
            self._save_fallback_patterns()

        logger.info(f"Stored pattern {pattern_id} for industry '{industry}'")
        return pattern_id

    async def find_similar_patterns(
        self,
        description: str,
        industry: str,
        top_k: int = 3,
        min_confidence: float = 0.3,
    ) -> List[PatternMatch]:
        """
        Find similar patterns based on description and industry.

        Args:
            description: User's project description
            industry: Detected industry
            top_k: Maximum patterns to return
            min_confidence: Minimum confidence threshold

        Returns:
            List of PatternMatch objects sorted by relevance
        """
        matches = []

        if self._use_chromadb and self._collection:
            try:
                results = self._collection.query(
                    query_texts=[f"{industry} {description}"],
                    n_results=top_k * 2,  # Get more to filter by confidence
                    where={"industry": industry} if industry != "universal" else None,
                )

                if results and results.get("ids"):
                    for i, pattern_id in enumerate(results["ids"][0]):
                        # Get full pattern from fallback storage
                        if pattern_id in self._fallback_patterns:
                            pattern = self._fallback_patterns[pattern_id]

                            if pattern.confidence >= min_confidence:
                                # Calculate similarity from distance
                                distance = results["distances"][0][i] if results.get("distances") else 0.5
                                similarity = 1.0 - min(1.0, distance)

                                # Combine similarity with confidence
                                relevance = (similarity * 0.6) + (pattern.confidence * 0.4)

                                matches.append(PatternMatch(
                                    pattern=pattern,
                                    similarity=similarity,
                                    relevance_score=relevance,
                                ))

            except Exception as e:
                logger.warning(f"ChromaDB query failed: {e}. Using fallback.")

        # Fallback: simple keyword matching
        if not matches:
            desc_words = set(description.lower().split())

            for pattern in self._fallback_patterns.values():
                if pattern.confidence < min_confidence:
                    continue

                if industry != "universal" and pattern.industry != industry:
                    continue

                # Calculate keyword overlap
                pattern_words = set(w.lower() for w in pattern.description_keywords)
                overlap = len(desc_words & pattern_words)
                similarity = overlap / max(len(desc_words), 1)

                if similarity > 0.1:  # Some overlap required
                    relevance = (similarity * 0.6) + (pattern.confidence * 0.4)
                    matches.append(PatternMatch(
                        pattern=pattern,
                        similarity=similarity,
                        relevance_score=relevance,
                    ))

        # Sort by relevance and limit
        matches.sort(key=lambda m: m.relevance_score, reverse=True)
        return matches[:top_k]

    async def record_success(self, pattern_id: str) -> None:
        """Record a successful use of a pattern"""
        if pattern_id in self._fallback_patterns:
            pattern = self._fallback_patterns[pattern_id]
            pattern.success_count += 1
            pattern.last_used_at = datetime.utcnow().isoformat()
            self._save_fallback_patterns()

            # Update ChromaDB metadata
            if self._use_chromadb and self._collection:
                try:
                    self._collection.update(
                        ids=[pattern_id],
                        metadatas=[{
                            "confidence": pattern.confidence,
                            "success_count": pattern.success_count,
                        }],
                    )
                except Exception as e:
                    logger.warning(f"Failed to update ChromaDB: {e}")

    async def record_failure(self, pattern_id: str) -> None:
        """Record a failed use of a pattern"""
        if pattern_id in self._fallback_patterns:
            pattern = self._fallback_patterns[pattern_id]
            pattern.failure_count += 1
            self._save_fallback_patterns()

    async def record_feedback(self, pattern_id: str, rating: float) -> None:
        """Record user feedback (0-5 star rating)"""
        if pattern_id in self._fallback_patterns:
            pattern = self._fallback_patterns[pattern_id]
            # Weighted average with existing rating
            if pattern.user_rating > 0:
                pattern.user_rating = (pattern.user_rating * 0.7) + (rating * 0.3)
            else:
                pattern.user_rating = rating
            self._save_fallback_patterns()

    async def prune_low_performers(self, min_confidence: float = 0.2) -> int:
        """Remove patterns with consistently poor performance"""
        to_remove = []

        for pattern_id, pattern in self._fallback_patterns.items():
            # Only prune if we have enough data
            total_uses = pattern.success_count + pattern.failure_count
            if total_uses >= 5 and pattern.confidence < min_confidence:
                to_remove.append(pattern_id)

        for pattern_id in to_remove:
            del self._fallback_patterns[pattern_id]

            if self._use_chromadb and self._collection:
                try:
                    self._collection.delete(ids=[pattern_id])
                except Exception:
                    pass

        if to_remove:
            self._save_fallback_patterns()
            logger.info(f"Pruned {len(to_remove)} low-performing patterns")

        return len(to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge store"""
        if not self._fallback_patterns:
            return {"total_patterns": 0, "message": "Knowledge store is empty"}

        total = len(self._fallback_patterns)
        industries = {}
        total_success = 0
        total_failure = 0
        avg_rating = 0.0
        rated_count = 0

        for pattern in self._fallback_patterns.values():
            industries[pattern.industry] = industries.get(pattern.industry, 0) + 1
            total_success += pattern.success_count
            total_failure += pattern.failure_count
            if pattern.user_rating > 0:
                avg_rating += pattern.user_rating
                rated_count += 1

        return {
            "total_patterns": total,
            "industries": industries,
            "total_successful_uses": total_success,
            "total_failed_uses": total_failure,
            "success_rate": total_success / max(1, total_success + total_failure),
            "avg_user_rating": avg_rating / max(1, rated_count),
            "using_chromadb": self._use_chromadb,
        }


# Singleton instance
_knowledge_store: Optional[DomainKnowledgeStore] = None


def get_knowledge_store() -> DomainKnowledgeStore:
    """Get the singleton knowledge store"""
    global _knowledge_store
    if _knowledge_store is None:
        _knowledge_store = DomainKnowledgeStore()
    return _knowledge_store
