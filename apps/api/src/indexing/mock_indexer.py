"""
Mock Indexer for local development and testing

Provides a simple in-memory implementation that doesn't require
external services or API keys.
"""
from typing import List, Dict, Optional
import logging
import asyncio

from .codebase_indexer import BaseIndexer, SearchResult

logger = logging.getLogger(__name__)


class MockIndexer(BaseIndexer):
    """
    Mock indexer for testing and local development.

    Uses simple in-memory storage with keyword matching.
    No external dependencies required.
    """

    def __init__(self):
        self._storage: Dict[str, Dict[str, str]] = {}

    async def index_directory(
        self,
        path: str,
        project_id: str,
        extensions: Optional[List[str]] = None
    ) -> int:
        """Mock directory indexing"""
        # Simulate some delay
        await asyncio.sleep(0.1)

        # Store a mock indicator
        self._storage[project_id] = {
            "_mock_directory": path,
            "_indexed": "true"
        }

        logger.info(f"Mock indexed directory: {path} for project {project_id}")
        return 1

    async def index_files(
        self,
        files: Dict[str, str],
        project_id: str
    ) -> int:
        """Store files in memory"""
        await asyncio.sleep(0.1)

        self._storage[project_id] = files.copy()

        logger.info(f"Mock indexed {len(files)} files for project {project_id}")
        return len(files)

    async def search(
        self,
        query: str,
        project_id: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """Simple keyword search"""
        if project_id not in self._storage:
            return []

        files = self._storage[project_id]
        query_lower = query.lower()
        results = []

        for file_path, content in files.items():
            if file_path.startswith("_"):
                continue

            # Simple relevance: count query word occurrences
            content_lower = content.lower()
            score = sum(
                content_lower.count(word)
                for word in query_lower.split()
            ) / max(1, len(content.split()))

            if score > 0:
                results.append(SearchResult(
                    content=content[:500],  # Truncate for preview
                    file_path=file_path,
                    score=min(score, 1.0),
                    language=self._detect_language(file_path)
                ))

        # Sort by score and limit
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    async def get_context(
        self,
        query: str,
        project_id: str,
        max_tokens: int = 2000
    ) -> str:
        """Get mock context"""
        results = await self.search(query, project_id, top_k=3)

        if not results:
            return "No relevant code found in the project."

        context_parts = ["Mock context from project files:\n"]

        for result in results:
            context_parts.append(f"\n--- {result.file_path} (score: {result.score:.2f}) ---\n")
            context_parts.append(result.content[:500])
            context_parts.append("\n")

        return "".join(context_parts)

    async def clear_index(self, project_id: str) -> bool:
        """Clear mock index"""
        if project_id in self._storage:
            del self._storage[project_id]
            return True
        return False

    def _detect_language(self, file_path: str) -> str:
        """Detect language from file extension"""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".md": "markdown",
        }
        ext = "." + file_path.split(".")[-1] if "." in file_path else ""
        return ext_map.get(ext.lower(), "text")
