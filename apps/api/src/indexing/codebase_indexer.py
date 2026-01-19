"""
Codebase Indexer using LlamaIndex

Provides semantic search and understanding of codebases for:
- Audit mode (understanding existing code)
- Code generation (learning from existing patterns)
- Documentation generation
- Bug analysis
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """A chunk of code with metadata"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """A search result from the code index"""
    content: str
    file_path: str
    score: float
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    language: Optional[str] = None
    context: Optional[str] = None


class BaseIndexer(ABC):
    """Abstract base class for codebase indexers"""

    @abstractmethod
    async def index_directory(
        self,
        path: str,
        project_id: str,
        extensions: Optional[List[str]] = None
    ) -> int:
        """Index all files in a directory"""
        pass

    @abstractmethod
    async def index_files(
        self,
        files: Dict[str, str],
        project_id: str
    ) -> int:
        """Index a dictionary of files (path -> content)"""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        project_id: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """Search the index with a natural language query"""
        pass

    @abstractmethod
    async def get_context(
        self,
        query: str,
        project_id: str,
        max_tokens: int = 2000
    ) -> str:
        """Get relevant context for a query as a formatted string"""
        pass

    @abstractmethod
    async def clear_index(self, project_id: str) -> bool:
        """Clear all indexed data for a project"""
        pass


class CodebaseIndexer(BaseIndexer):
    """
    LlamaIndex-based codebase indexer for semantic search.

    Features:
    - Automatic file type detection
    - Code-aware chunking
    - Vector embeddings for semantic search
    - Context retrieval for LLM prompts

    Note: Requires LlamaIndex and OpenAI/Anthropic API key for embeddings.
    Falls back to MockIndexer if not available.
    """

    # File extensions to index by default
    DEFAULT_EXTENSIONS = {
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".java", ".kt", ".swift", ".go", ".rs",
        ".cpp", ".c", ".h", ".hpp",
        ".html", ".css", ".scss", ".sass",
        ".json", ".yaml", ".yml", ".toml",
        ".md", ".txt", ".sql"
    }

    # Directories to skip
    SKIP_DIRS = {
        "node_modules", "venv", ".venv", "__pycache__",
        ".git", ".svn", "dist", "build", ".next",
        "target", "vendor", ".idea", ".vscode"
    }

    def __init__(
        self,
        embedding_model: str = "text-embedding-3-small",
        chunk_size: int = 1024,
        chunk_overlap: int = 128
    ):
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Storage for indexed documents (in-memory for local dev)
        # In production, use vector database (Supabase pgvector, Pinecone, etc.)
        self._indexes: Dict[str, Any] = {}

        self._llama_available = self._check_llama_index()

    def _check_llama_index(self) -> bool:
        """Check if LlamaIndex is available"""
        try:
            from llama_index.core import VectorStoreIndex, Document
            return True
        except ImportError:
            logger.warning(
                "LlamaIndex not installed. Using mock indexer. "
                "Install with: pip install llama-index"
            )
            return False

    async def index_directory(
        self,
        path: str,
        project_id: str,
        extensions: Optional[List[str]] = None
    ) -> int:
        """
        Index all files in a directory.

        Args:
            path: Path to the directory
            project_id: Unique identifier for this project
            extensions: Optional list of file extensions to include

        Returns:
            Number of files indexed
        """
        allowed_extensions = set(extensions) if extensions else self.DEFAULT_EXTENSIONS
        files_indexed = 0

        path_obj = Path(path)
        if not path_obj.exists():
            logger.error(f"Path does not exist: {path}")
            return 0

        # Collect all files
        files_to_index: Dict[str, str] = {}

        for file_path in path_obj.rglob("*"):
            # Skip directories in SKIP_DIRS
            if any(skip in file_path.parts for skip in self.SKIP_DIRS):
                continue

            # Skip non-files
            if not file_path.is_file():
                continue

            # Check extension
            if file_path.suffix.lower() not in allowed_extensions:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                relative_path = str(file_path.relative_to(path_obj))
                files_to_index[relative_path] = content
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")

        return await self.index_files(files_to_index, project_id)

    async def index_files(
        self,
        files: Dict[str, str],
        project_id: str
    ) -> int:
        """
        Index a dictionary of files.

        Args:
            files: Dictionary mapping file paths to content
            project_id: Unique identifier for this project

        Returns:
            Number of files indexed
        """
        if not self._llama_available:
            # Use simple in-memory storage
            self._indexes[project_id] = {
                "files": files,
                "chunks": self._simple_chunk_files(files)
            }
            logger.info(f"Indexed {len(files)} files for project {project_id} (simple mode)")
            return len(files)

        try:
            from llama_index.core import VectorStoreIndex, Document
            from llama_index.core.node_parser import CodeSplitter

            documents = []
            for file_path, content in files.items():
                language = self._detect_language(file_path)
                doc = Document(
                    text=content,
                    metadata={
                        "file_path": file_path,
                        "language": language,
                        "project_id": project_id
                    }
                )
                documents.append(doc)

            # Create index
            index = VectorStoreIndex.from_documents(documents)
            self._indexes[project_id] = index

            logger.info(f"Indexed {len(files)} files for project {project_id}")
            return len(files)

        except Exception as e:
            logger.error(f"Error indexing with LlamaIndex: {e}")
            # Fallback to simple storage
            self._indexes[project_id] = {
                "files": files,
                "chunks": self._simple_chunk_files(files)
            }
            return len(files)

    async def search(
        self,
        query: str,
        project_id: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Search the index with a natural language query.

        Args:
            query: Natural language query
            project_id: Project to search
            top_k: Number of results to return

        Returns:
            List of search results
        """
        if project_id not in self._indexes:
            logger.warning(f"No index found for project {project_id}")
            return []

        index_data = self._indexes[project_id]

        # Check if it's a LlamaIndex index or simple storage
        if isinstance(index_data, dict):
            # Simple keyword search fallback
            return self._simple_search(query, index_data, top_k)

        try:
            # LlamaIndex query
            query_engine = index_data.as_query_engine(similarity_top_k=top_k)
            response = query_engine.query(query)

            results = []
            for node in response.source_nodes:
                results.append(SearchResult(
                    content=node.text,
                    file_path=node.metadata.get("file_path", "unknown"),
                    score=node.score or 0.0,
                    language=node.metadata.get("language")
                ))

            return results

        except Exception as e:
            logger.error(f"Error searching with LlamaIndex: {e}")
            return []

    async def get_context(
        self,
        query: str,
        project_id: str,
        max_tokens: int = 2000
    ) -> str:
        """
        Get relevant context for a query as a formatted string.

        Useful for providing context to LLMs during code generation.

        Args:
            query: The query or task description
            project_id: Project to search
            max_tokens: Approximate max tokens in response

        Returns:
            Formatted context string
        """
        results = await self.search(query, project_id, top_k=5)

        if not results:
            return "No relevant code found in the project."

        context_parts = ["Relevant code from the project:\n"]
        current_tokens = 50  # Header estimate

        for result in results:
            # Rough token estimate (4 chars per token)
            result_tokens = len(result.content) // 4

            if current_tokens + result_tokens > max_tokens:
                break

            context_parts.append(f"\n--- {result.file_path} ---\n")
            context_parts.append(f"```{result.language or ''}\n")
            context_parts.append(result.content)
            context_parts.append("\n```\n")

            current_tokens += result_tokens + 20

        return "".join(context_parts)

    async def clear_index(self, project_id: str) -> bool:
        """Clear all indexed data for a project"""
        if project_id in self._indexes:
            del self._indexes[project_id]
            logger.info(f"Cleared index for project {project_id}")
            return True
        return False

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".kt": "kotlin",
            ".swift": "swift",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".sql": "sql",
        }
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, "text")

    def _simple_chunk_files(
        self,
        files: Dict[str, str]
    ) -> List[CodeChunk]:
        """Simple chunking for fallback mode"""
        chunks = []

        for file_path, content in files.items():
            language = self._detect_language(file_path)
            lines = content.split("\n")

            # Chunk by line groups
            chunk_lines = self.chunk_size // 50  # Rough estimate

            for i in range(0, len(lines), chunk_lines):
                chunk_content = "\n".join(lines[i:i + chunk_lines])
                if chunk_content.strip():
                    chunks.append(CodeChunk(
                        content=chunk_content,
                        file_path=file_path,
                        start_line=i + 1,
                        end_line=min(i + chunk_lines, len(lines)),
                        language=language
                    ))

        return chunks

    def _simple_search(
        self,
        query: str,
        index_data: Dict,
        top_k: int
    ) -> List[SearchResult]:
        """Simple keyword search fallback"""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_chunks = []

        for chunk in index_data.get("chunks", []):
            content_lower = chunk.content.lower()

            # Simple scoring: count matching words
            score = sum(1 for word in query_words if word in content_lower)

            if score > 0:
                scored_chunks.append((chunk, score))

        # Sort by score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        results = []
        for chunk, score in scored_chunks[:top_k]:
            results.append(SearchResult(
                content=chunk.content,
                file_path=chunk.file_path,
                score=float(score) / len(query_words),
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                language=chunk.language
            ))

        return results


# Global indexer instance
_indexer: Optional[CodebaseIndexer] = None


def get_indexer() -> CodebaseIndexer:
    """Get or create the global indexer instance"""
    global _indexer

    if _indexer is None:
        _indexer = CodebaseIndexer()

    return _indexer
