"""
Vector Search Module using Chroma

Provides semantic search over code, documentation, and project context.
Enables agents to find relevant code snippets and context efficiently.

Features:
- Persistent vector storage
- Multi-collection support (code, docs, conversations)
- Hybrid search (semantic + keyword)
- Automatic chunking and embedding
- Metadata filtering
"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
import logging
import os

logger = logging.getLogger(__name__)


class CollectionType(str, Enum):
    """Types of vector collections"""
    CODE = "code"
    DOCUMENTATION = "documentation"
    CONVERSATIONS = "conversations"
    TEMPLATES = "templates"
    ERRORS = "errors"


@dataclass
class Document:
    """A document to be indexed"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


@dataclass
class SearchResult:
    """A search result"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeChunk:
    """A chunk of code for indexing"""
    file_path: str
    content: str
    language: str
    start_line: int
    end_line: int
    chunk_type: str  # function, class, module, etc.
    name: Optional[str] = None

    def to_document(self) -> Document:
        """Convert to indexable document"""
        doc_id = hashlib.md5(
            f"{self.file_path}:{self.start_line}:{self.end_line}".encode()
        ).hexdigest()

        return Document(
            id=doc_id,
            content=self.content,
            metadata={
                "file_path": self.file_path,
                "language": self.language,
                "start_line": self.start_line,
                "end_line": self.end_line,
                "chunk_type": self.chunk_type,
                "name": self.name or ""
            }
        )


class VectorStore:
    """
    Vector store using Chroma for semantic search.

    Example:
        store = VectorStore()

        # Index code files
        store.index_code_file("src/main.py", "python", code_content)

        # Search for relevant code
        results = store.search("authentication logic", collection=CollectionType.CODE)

        for result in results:
            print(f"{result.metadata['file_path']}: {result.score}")
            print(result.content[:200])
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.persist_directory = persist_directory or os.path.join(
            os.path.expanduser("~"), ".codeweaver", "chroma"
        )
        self.embedding_model = embedding_model
        self._client = None
        self._embedding_function = None
        self._collections: Dict[str, Any] = {}
        self._chroma_available = False
        self._init_chroma()

    def _init_chroma(self):
        """Initialize Chroma client and embeddings"""
        try:
            import chromadb
            from chromadb.config import Settings

            # Create persistent client
            self._client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))

            # Try to use sentence-transformers for embeddings
            try:
                from chromadb.utils import embedding_functions
                self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=self.embedding_model
                )
            except ImportError:
                logger.warning("sentence-transformers not available, using default embeddings")
                self._embedding_function = None

            self._chroma_available = True
            logger.info(f"Chroma initialized with persist directory: {self.persist_directory}")

        except ImportError as e:
            logger.warning(f"Chroma not available: {e}. Using in-memory fallback.")
            self._chroma_available = False
            self._fallback_store: Dict[str, List[Document]] = {}

    def _get_collection(self, collection_type: CollectionType):
        """Get or create a collection"""
        if not self._chroma_available:
            if collection_type.value not in self._fallback_store:
                self._fallback_store[collection_type.value] = []
            return None

        if collection_type.value not in self._collections:
            kwargs = {"name": collection_type.value}
            if self._embedding_function:
                kwargs["embedding_function"] = self._embedding_function

            self._collections[collection_type.value] = self._client.get_or_create_collection(
                **kwargs
            )

        return self._collections[collection_type.value]

    def add_documents(
        self,
        documents: List[Document],
        collection: CollectionType = CollectionType.CODE
    ) -> int:
        """
        Add documents to a collection.

        Args:
            documents: List of documents to add
            collection: Target collection

        Returns:
            Number of documents added
        """
        if not documents:
            return 0

        if not self._chroma_available:
            # Fallback: store in memory
            self._fallback_store.setdefault(collection.value, []).extend(documents)
            return len(documents)

        coll = self._get_collection(collection)

        # Prepare data for Chroma
        ids = [doc.id for doc in documents]
        contents = [doc.content for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        # Add in batches to avoid memory issues
        batch_size = 100
        added = 0

        for i in range(0, len(documents), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_contents = contents[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]

            try:
                coll.add(
                    ids=batch_ids,
                    documents=batch_contents,
                    metadatas=batch_metadatas
                )
                added += len(batch_ids)
            except Exception as e:
                logger.error(f"Error adding documents: {e}")

        return added

    def search(
        self,
        query: str,
        collection: CollectionType = CollectionType.CODE,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for documents.

        Args:
            query: Search query
            collection: Collection to search
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter

        Returns:
            List of search results
        """
        if not self._chroma_available:
            return self._fallback_search(query, collection, n_results)

        coll = self._get_collection(collection)

        try:
            results = coll.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"]
            )

            search_results = []
            if results and results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    # Convert distance to similarity score (1 - normalized distance)
                    distance = results['distances'][0][i] if results['distances'] else 0
                    score = 1 / (1 + distance)

                    search_results.append(SearchResult(
                        id=doc_id,
                        content=results['documents'][0][i] if results['documents'] else "",
                        score=score,
                        metadata=results['metadatas'][0][i] if results['metadatas'] else {}
                    ))

            return search_results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def _fallback_search(
        self,
        query: str,
        collection: CollectionType,
        n_results: int
    ) -> List[SearchResult]:
        """Simple keyword-based fallback search"""
        documents = self._fallback_store.get(collection.value, [])
        query_terms = query.lower().split()

        scored_docs = []
        for doc in documents:
            content_lower = doc.content.lower()
            # Simple term frequency scoring
            score = sum(content_lower.count(term) for term in query_terms)
            if score > 0:
                scored_docs.append((doc, score))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [
            SearchResult(
                id=doc.id,
                content=doc.content,
                score=score / max(1, len(doc.content.split())),  # Normalize
                metadata=doc.metadata
            )
            for doc, score in scored_docs[:n_results]
        ]

    def delete_documents(
        self,
        ids: List[str],
        collection: CollectionType = CollectionType.CODE
    ) -> int:
        """Delete documents by ID"""
        if not self._chroma_available:
            docs = self._fallback_store.get(collection.value, [])
            original_len = len(docs)
            self._fallback_store[collection.value] = [d for d in docs if d.id not in ids]
            return original_len - len(self._fallback_store[collection.value])

        coll = self._get_collection(collection)
        try:
            coll.delete(ids=ids)
            return len(ids)
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return 0

    def clear_collection(self, collection: CollectionType) -> bool:
        """Clear all documents from a collection"""
        if not self._chroma_available:
            self._fallback_store[collection.value] = []
            return True

        try:
            self._client.delete_collection(collection.value)
            if collection.value in self._collections:
                del self._collections[collection.value]
            return True
        except Exception as e:
            logger.error(f"Clear collection error: {e}")
            return False

    def get_collection_stats(self, collection: CollectionType) -> Dict[str, Any]:
        """Get statistics for a collection"""
        if not self._chroma_available:
            docs = self._fallback_store.get(collection.value, [])
            return {
                "count": len(docs),
                "backend": "in-memory"
            }

        coll = self._get_collection(collection)
        return {
            "count": coll.count(),
            "backend": "chroma"
        }


class CodeIndexer:
    """
    Index code files for semantic search.

    Example:
        indexer = CodeIndexer()

        # Index a project
        indexer.index_directory("./src", project_id="my-project")

        # Search for code
        results = indexer.search_code("user authentication")
    """

    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.store = vector_store or VectorStore()
        self._parser = None

    def _get_parser(self):
        """Lazy load code parser"""
        if self._parser is None:
            try:
                from .code_parser import CodeParser
                self._parser = CodeParser()
            except ImportError:
                self._parser = None
        return self._parser

    def index_code_file(
        self,
        file_path: str,
        language: str,
        content: str,
        project_id: Optional[str] = None
    ) -> int:
        """
        Index a single code file.

        Args:
            file_path: Path to the file
            language: Programming language
            content: File content
            project_id: Optional project identifier

        Returns:
            Number of chunks indexed
        """
        chunks = self._chunk_code(file_path, language, content)

        # Add project_id to metadata if provided
        if project_id:
            for chunk in chunks:
                chunk.metadata["project_id"] = project_id

        documents = [chunk.to_document() for chunk in chunks]
        return self.store.add_documents(documents, CollectionType.CODE)

    def index_directory(
        self,
        directory: str,
        project_id: Optional[str] = None,
        extensions: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Index all code files in a directory.

        Args:
            directory: Directory to index
            project_id: Optional project identifier
            extensions: File extensions to include

        Returns:
            Dict mapping file paths to chunks indexed
        """
        default_extensions = [
            '.py', '.js', '.ts', '.tsx', '.jsx',
            '.go', '.rs', '.java', '.cpp', '.c',
            '.rb', '.php', '.swift', '.kt'
        ]
        extensions = extensions or default_extensions

        results = {}
        path = Path(directory)

        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix not in extensions:
                continue
            if self._should_skip(file_path):
                continue

            try:
                content = file_path.read_text(encoding='utf-8')
                language = self._detect_language(file_path)
                count = self.index_code_file(
                    str(file_path),
                    language,
                    content,
                    project_id
                )
                results[str(file_path)] = count
            except Exception as e:
                logger.error(f"Error indexing {file_path}: {e}")
                results[str(file_path)] = 0

        return results

    def search_code(
        self,
        query: str,
        project_id: Optional[str] = None,
        language: Optional[str] = None,
        chunk_type: Optional[str] = None,
        n_results: int = 10
    ) -> List[SearchResult]:
        """
        Search for code snippets.

        Args:
            query: Search query
            project_id: Filter by project
            language: Filter by language
            chunk_type: Filter by chunk type (function, class, etc.)
            n_results: Number of results

        Returns:
            List of search results
        """
        # Build metadata filter
        where = {}
        if project_id:
            where["project_id"] = project_id
        if language:
            where["language"] = language
        if chunk_type:
            where["chunk_type"] = chunk_type

        return self.store.search(
            query=query,
            collection=CollectionType.CODE,
            n_results=n_results,
            where=where if where else None
        )

    def _chunk_code(self, file_path: str, language: str, content: str) -> List[CodeChunk]:
        """Split code into meaningful chunks"""
        chunks = []

        # Try to use tree-sitter parser for intelligent chunking
        parser = self._get_parser()
        if parser:
            try:
                from .code_parser import Language as ParserLanguage
                lang = ParserLanguage(language.lower())
                result = parser.parse(content, lang)

                # Create chunks for each function
                for func in result.functions:
                    func_content = self._extract_lines(
                        content,
                        func.location.start_line,
                        func.location.end_line
                    )
                    chunks.append(CodeChunk(
                        file_path=file_path,
                        content=func_content,
                        language=language,
                        start_line=func.location.start_line,
                        end_line=func.location.end_line,
                        chunk_type="function",
                        name=func.name
                    ))

                # Create chunks for each class
                for cls in result.classes:
                    cls_content = self._extract_lines(
                        content,
                        cls.location.start_line,
                        cls.location.end_line
                    )
                    chunks.append(CodeChunk(
                        file_path=file_path,
                        content=cls_content,
                        language=language,
                        start_line=cls.location.start_line,
                        end_line=cls.location.end_line,
                        chunk_type="class",
                        name=cls.name
                    ))

            except Exception as e:
                logger.debug(f"Parser chunking failed: {e}, using line-based chunking")

        # Fallback: line-based chunking
        if not chunks:
            chunks = self._chunk_by_lines(file_path, language, content)

        # Always include full file as a chunk
        chunks.append(CodeChunk(
            file_path=file_path,
            content=content[:5000],  # Limit to avoid huge embeddings
            language=language,
            start_line=1,
            end_line=content.count('\n') + 1,
            chunk_type="module",
            name=Path(file_path).stem
        ))

        return chunks

    def _chunk_by_lines(
        self,
        file_path: str,
        language: str,
        content: str,
        chunk_size: int = 50,
        overlap: int = 10
    ) -> List[CodeChunk]:
        """Chunk code by line count with overlap"""
        lines = content.split('\n')
        chunks = []

        for i in range(0, len(lines), chunk_size - overlap):
            chunk_lines = lines[i:i + chunk_size]
            if not chunk_lines:
                continue

            chunks.append(CodeChunk(
                file_path=file_path,
                content='\n'.join(chunk_lines),
                language=language,
                start_line=i + 1,
                end_line=i + len(chunk_lines),
                chunk_type="chunk"
            ))

        return chunks

    def _extract_lines(self, content: str, start: int, end: int) -> str:
        """Extract lines from content (1-indexed)"""
        lines = content.split('\n')
        return '\n'.join(lines[start - 1:end])

    def _detect_language(self, path: Path) -> str:
        """Detect language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'tsx',
            '.jsx': 'jsx',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
        }
        return ext_map.get(path.suffix.lower(), 'unknown')

    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped"""
        skip_dirs = {
            '.git', 'node_modules', '__pycache__', 'venv',
            '.venv', 'dist', 'build', '.next', '.nuxt'
        }
        skip_files = {'package-lock.json', 'yarn.lock', 'poetry.lock'}

        if any(d in path.parts for d in skip_dirs):
            return True
        if path.name in skip_files:
            return True

        return False


class DocumentationIndexer:
    """Index documentation for semantic search"""

    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.store = vector_store or VectorStore()

    def index_markdown(
        self,
        file_path: str,
        content: str,
        project_id: Optional[str] = None
    ) -> int:
        """Index a markdown file"""
        chunks = self._chunk_markdown(content)
        documents = []

        for i, (heading, text) in enumerate(chunks):
            doc_id = hashlib.md5(f"{file_path}:{i}".encode()).hexdigest()
            documents.append(Document(
                id=doc_id,
                content=text,
                metadata={
                    "file_path": file_path,
                    "heading": heading,
                    "project_id": project_id or ""
                }
            ))

        return self.store.add_documents(documents, CollectionType.DOCUMENTATION)

    def search_docs(
        self,
        query: str,
        project_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[SearchResult]:
        """Search documentation"""
        where = {"project_id": project_id} if project_id else None
        return self.store.search(
            query=query,
            collection=CollectionType.DOCUMENTATION,
            n_results=n_results,
            where=where
        )

    def _chunk_markdown(self, content: str) -> List[tuple]:
        """Split markdown by headings"""
        import re

        chunks = []
        current_heading = "Introduction"
        current_content = []

        for line in content.split('\n'):
            heading_match = re.match(r'^#{1,3}\s+(.+)$', line)
            if heading_match:
                # Save previous section
                if current_content:
                    chunks.append((current_heading, '\n'.join(current_content)))
                current_heading = heading_match.group(1)
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            chunks.append((current_heading, '\n'.join(current_content)))

        return chunks


# ===========================================
# Convenience Functions
# ===========================================

_default_store: Optional[VectorStore] = None
_default_code_indexer: Optional[CodeIndexer] = None
_default_doc_indexer: Optional[DocumentationIndexer] = None


def get_vector_store() -> VectorStore:
    """Get the default vector store"""
    global _default_store
    if _default_store is None:
        _default_store = VectorStore()
    return _default_store


def get_code_indexer() -> CodeIndexer:
    """Get the default code indexer"""
    global _default_code_indexer
    if _default_code_indexer is None:
        _default_code_indexer = CodeIndexer(get_vector_store())
    return _default_code_indexer


def get_doc_indexer() -> DocumentationIndexer:
    """Get the default documentation indexer"""
    global _default_doc_indexer
    if _default_doc_indexer is None:
        _default_doc_indexer = DocumentationIndexer(get_vector_store())
    return _default_doc_indexer


def search_code(query: str, **kwargs) -> List[SearchResult]:
    """Search code in the default store"""
    return get_code_indexer().search_code(query, **kwargs)


def search_docs(query: str, **kwargs) -> List[SearchResult]:
    """Search documentation in the default store"""
    return get_doc_indexer().search_docs(query, **kwargs)


def index_project(directory: str, project_id: str) -> Dict[str, Any]:
    """Index an entire project (code and docs)"""
    code_indexer = get_code_indexer()
    doc_indexer = get_doc_indexer()

    results = {
        "code_files": code_indexer.index_directory(directory, project_id),
        "doc_files": {}
    }

    # Index markdown files
    for md_file in Path(directory).rglob("*.md"):
        if code_indexer._should_skip(md_file):
            continue
        try:
            content = md_file.read_text(encoding='utf-8')
            count = doc_indexer.index_markdown(str(md_file), content, project_id)
            results["doc_files"][str(md_file)] = count
        except Exception as e:
            logger.error(f"Error indexing {md_file}: {e}")

    return results
