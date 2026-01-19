"""
File Storage Service

Provides abstraction for storing and retrieving generated project files.
Supports local filesystem (development) and Supabase Storage (production).
"""

from typing import Dict, List, Optional, Any, Protocol
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
import os
import json
import logging
import aiofiles
import aiofiles.os

logger = logging.getLogger(__name__)


# ===========================================
# File Models
# ===========================================

class StoredFile(BaseModel):
    """Metadata for a stored file"""
    path: str = Field(description="File path relative to project")
    content: str = Field(description="File content")
    language: Optional[str] = None
    size_bytes: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    checksum: Optional[str] = None


class ProjectFiles(BaseModel):
    """Collection of files for a project"""
    project_id: str
    files: Dict[str, StoredFile] = Field(default_factory=dict)
    total_size_bytes: int = 0
    file_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# Storage Backend Protocol
# ===========================================

class FileStorageBackend(ABC):
    """Abstract base class for file storage backends"""

    @abstractmethod
    async def save_file(
        self,
        project_id: str,
        file_path: str,
        content: str,
        language: Optional[str] = None,
    ) -> StoredFile:
        """Save a single file"""
        pass

    @abstractmethod
    async def save_files(
        self,
        project_id: str,
        files: Dict[str, str],
    ) -> Dict[str, StoredFile]:
        """Save multiple files at once"""
        pass

    @abstractmethod
    async def get_file(
        self,
        project_id: str,
        file_path: str,
    ) -> Optional[StoredFile]:
        """Get a single file"""
        pass

    @abstractmethod
    async def get_files(
        self,
        project_id: str,
    ) -> ProjectFiles:
        """Get all files for a project"""
        pass

    @abstractmethod
    async def delete_file(
        self,
        project_id: str,
        file_path: str,
    ) -> bool:
        """Delete a single file"""
        pass

    @abstractmethod
    async def delete_files(
        self,
        project_id: str,
    ) -> bool:
        """Delete all files for a project"""
        pass

    @abstractmethod
    async def list_projects(self) -> List[str]:
        """List all project IDs with stored files"""
        pass


# ===========================================
# Local File Storage (Development)
# ===========================================

class LocalFileStorage(FileStorageBackend):
    """
    File storage using local filesystem.

    Stores files in a configurable directory structure:
    base_path/
    └── {project_id}/
        ├── files/
        │   └── {file_path}
        └── metadata.json
    """

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or self._default_path())
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalFileStorage initialized at: {self.base_path}")

    def _default_path(self) -> str:
        """Get default storage path"""
        # apps/api/generated_projects/
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "generated_projects")

    def _project_path(self, project_id: str) -> Path:
        """Get path for a project"""
        return self.base_path / project_id

    def _files_path(self, project_id: str) -> Path:
        """Get files directory for a project"""
        return self._project_path(project_id) / "files"

    def _metadata_path(self, project_id: str) -> Path:
        """Get metadata file path for a project"""
        return self._project_path(project_id) / "metadata.json"

    def _calculate_checksum(self, content: str) -> str:
        """Calculate MD5 checksum of content"""
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()

    async def _load_metadata(self, project_id: str) -> Dict[str, Any]:
        """Load project metadata"""
        meta_path = self._metadata_path(project_id)
        if meta_path.exists():
            async with aiofiles.open(meta_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        return {"files": {}, "created_at": datetime.utcnow().isoformat()}

    async def _save_metadata(self, project_id: str, metadata: Dict[str, Any]) -> None:
        """Save project metadata"""
        meta_path = self._metadata_path(project_id)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        metadata["updated_at"] = datetime.utcnow().isoformat()
        async with aiofiles.open(meta_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(metadata, indent=2, default=str))

    async def save_file(
        self,
        project_id: str,
        file_path: str,
        content: str,
        language: Optional[str] = None,
    ) -> StoredFile:
        """Save a single file to local storage"""
        files_dir = self._files_path(project_id)
        full_path = files_dir / file_path

        # Create directories
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
            await f.write(content)

        # Create stored file record
        now = datetime.utcnow()
        stored = StoredFile(
            path=file_path,
            content=content,
            language=language,
            size_bytes=len(content.encode()),
            created_at=now,
            updated_at=now,
            checksum=self._calculate_checksum(content),
        )

        # Update metadata
        metadata = await self._load_metadata(project_id)
        metadata["files"][file_path] = {
            "language": language,
            "size_bytes": stored.size_bytes,
            "checksum": stored.checksum,
            "updated_at": now.isoformat(),
        }
        await self._save_metadata(project_id, metadata)

        logger.debug(f"Saved file: {project_id}/{file_path}")
        return stored

    async def save_files(
        self,
        project_id: str,
        files: Dict[str, str],
    ) -> Dict[str, StoredFile]:
        """Save multiple files"""
        results = {}
        for file_path, content in files.items():
            # Infer language from extension
            ext = Path(file_path).suffix.lower()
            language = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".tsx": "typescript",
                ".jsx": "javascript",
                ".html": "html",
                ".css": "css",
                ".json": "json",
                ".yaml": "yaml",
                ".yml": "yaml",
                ".md": "markdown",
                ".sql": "sql",
                ".sh": "shell",
            }.get(ext)

            results[file_path] = await self.save_file(
                project_id, file_path, content, language
            )

        logger.info(f"Saved {len(results)} files for project {project_id}")
        return results

    async def get_file(
        self,
        project_id: str,
        file_path: str,
    ) -> Optional[StoredFile]:
        """Get a single file"""
        full_path = self._files_path(project_id) / file_path

        if not full_path.exists():
            return None

        async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
            content = await f.read()

        # Load metadata
        metadata = await self._load_metadata(project_id)
        file_meta = metadata.get("files", {}).get(file_path, {})

        return StoredFile(
            path=file_path,
            content=content,
            language=file_meta.get("language"),
            size_bytes=len(content.encode()),
            checksum=self._calculate_checksum(content),
        )

    async def get_files(
        self,
        project_id: str,
    ) -> ProjectFiles:
        """Get all files for a project"""
        files_dir = self._files_path(project_id)
        files = {}
        total_size = 0

        if files_dir.exists():
            for file_path in files_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(files_dir)).replace("\\", "/")
                    stored = await self.get_file(project_id, rel_path)
                    if stored:
                        files[rel_path] = stored
                        total_size += stored.size_bytes

        metadata = await self._load_metadata(project_id)

        return ProjectFiles(
            project_id=project_id,
            files=files,
            total_size_bytes=total_size,
            file_count=len(files),
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(metadata.get("updated_at", datetime.utcnow().isoformat())),
        )

    async def delete_file(
        self,
        project_id: str,
        file_path: str,
    ) -> bool:
        """Delete a single file"""
        full_path = self._files_path(project_id) / file_path

        if full_path.exists():
            await aiofiles.os.remove(full_path)

            # Update metadata
            metadata = await self._load_metadata(project_id)
            if file_path in metadata.get("files", {}):
                del metadata["files"][file_path]
                await self._save_metadata(project_id, metadata)

            logger.debug(f"Deleted file: {project_id}/{file_path}")
            return True

        return False

    async def delete_files(
        self,
        project_id: str,
    ) -> bool:
        """Delete all files for a project"""
        project_path = self._project_path(project_id)

        if project_path.exists():
            import shutil
            shutil.rmtree(project_path)
            logger.info(f"Deleted project: {project_id}")
            return True

        return False

    async def list_projects(self) -> List[str]:
        """List all project IDs"""
        projects = []
        if self.base_path.exists():
            for path in self.base_path.iterdir():
                if path.is_dir() and (path / "metadata.json").exists():
                    projects.append(path.name)
        return projects


# ===========================================
# Supabase Storage (Production)
# ===========================================

class SupabaseFileStorage(FileStorageBackend):
    """
    File storage using Supabase Storage.

    Stores files in a Supabase bucket with project-based prefixes.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        bucket_name: str = "generated-projects",
    ):
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_KEY")
        self.bucket_name = bucket_name
        self._client = None

        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not configured")

    def _get_client(self):
        """Get or create Supabase client"""
        if self._client is None:
            try:
                from supabase import create_client
                self._client = create_client(self.supabase_url, self.supabase_key)
            except ImportError:
                logger.error("supabase-py not installed")
                raise
        return self._client

    def _storage_path(self, project_id: str, file_path: str) -> str:
        """Get storage path for a file"""
        return f"{project_id}/{file_path}"

    async def save_file(
        self,
        project_id: str,
        file_path: str,
        content: str,
        language: Optional[str] = None,
    ) -> StoredFile:
        """Save file to Supabase Storage"""
        client = self._get_client()
        storage_path = self._storage_path(project_id, file_path)

        # Upload file
        result = client.storage.from_(self.bucket_name).upload(
            storage_path,
            content.encode(),
            {"content-type": "text/plain", "upsert": "true"},
        )

        now = datetime.utcnow()
        return StoredFile(
            path=file_path,
            content=content,
            language=language,
            size_bytes=len(content.encode()),
            created_at=now,
            updated_at=now,
        )

    async def save_files(
        self,
        project_id: str,
        files: Dict[str, str],
    ) -> Dict[str, StoredFile]:
        """Save multiple files to Supabase"""
        results = {}
        for file_path, content in files.items():
            ext = Path(file_path).suffix.lower()
            language = {".py": "python", ".js": "javascript", ".ts": "typescript"}.get(ext)
            results[file_path] = await self.save_file(project_id, file_path, content, language)
        return results

    async def get_file(
        self,
        project_id: str,
        file_path: str,
    ) -> Optional[StoredFile]:
        """Get file from Supabase Storage"""
        client = self._get_client()
        storage_path = self._storage_path(project_id, file_path)

        try:
            response = client.storage.from_(self.bucket_name).download(storage_path)
            content = response.decode()

            return StoredFile(
                path=file_path,
                content=content,
                size_bytes=len(content.encode()),
            )
        except Exception as e:
            logger.debug(f"File not found: {storage_path}: {e}")
            return None

    async def get_files(
        self,
        project_id: str,
    ) -> ProjectFiles:
        """Get all files for a project from Supabase"""
        client = self._get_client()

        # List files in project folder
        files_list = client.storage.from_(self.bucket_name).list(project_id)

        files = {}
        total_size = 0

        for file_info in files_list:
            file_path = file_info["name"]
            stored = await self.get_file(project_id, file_path)
            if stored:
                files[file_path] = stored
                total_size += stored.size_bytes

        return ProjectFiles(
            project_id=project_id,
            files=files,
            total_size_bytes=total_size,
            file_count=len(files),
        )

    async def delete_file(
        self,
        project_id: str,
        file_path: str,
    ) -> bool:
        """Delete file from Supabase Storage"""
        client = self._get_client()
        storage_path = self._storage_path(project_id, file_path)

        try:
            client.storage.from_(self.bucket_name).remove([storage_path])
            return True
        except Exception as e:
            logger.warning(f"Failed to delete {storage_path}: {e}")
            return False

    async def delete_files(
        self,
        project_id: str,
    ) -> bool:
        """Delete all files for a project from Supabase"""
        client = self._get_client()

        try:
            # List and delete all files
            files_list = client.storage.from_(self.bucket_name).list(project_id)
            paths = [f"{project_id}/{f['name']}" for f in files_list]
            if paths:
                client.storage.from_(self.bucket_name).remove(paths)
            return True
        except Exception as e:
            logger.warning(f"Failed to delete project {project_id}: {e}")
            return False

    async def list_projects(self) -> List[str]:
        """List all project IDs in Supabase"""
        client = self._get_client()

        try:
            # List top-level folders
            folders = client.storage.from_(self.bucket_name).list()
            return [f["name"] for f in folders if f.get("id") is None]  # Folders have no id
        except Exception as e:
            logger.warning(f"Failed to list projects: {e}")
            return []


# ===========================================
# Storage Factory
# ===========================================

_storage: Optional[FileStorageBackend] = None


def get_file_storage() -> FileStorageBackend:
    """
    Get the configured file storage backend.

    Uses Supabase in production, local filesystem in development.
    """
    global _storage

    if _storage is None:
        # Check for Supabase configuration
        if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"):
            try:
                _storage = SupabaseFileStorage()
                logger.info("Using Supabase file storage")
            except Exception as e:
                logger.warning(f"Supabase storage not available: {e}")
                _storage = LocalFileStorage()
        else:
            _storage = LocalFileStorage()
            logger.info("Using local file storage")

    return _storage


def set_file_storage(storage: FileStorageBackend) -> None:
    """Set the file storage backend (for testing)"""
    global _storage
    _storage = storage


# ===========================================
# Convenience Functions
# ===========================================

async def save_project_files(
    project_id: str,
    files: Dict[str, str],
) -> Dict[str, StoredFile]:
    """Save files for a project"""
    storage = get_file_storage()
    return await storage.save_files(project_id, files)


async def get_project_files(project_id: str) -> ProjectFiles:
    """Get all files for a project"""
    storage = get_file_storage()
    return await storage.get_files(project_id)


async def delete_project_files(project_id: str) -> bool:
    """Delete all files for a project"""
    storage = get_file_storage()
    return await storage.delete_files(project_id)
