"""
Project management routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from ..models import (
    ProjectCreate,
    ProjectResponse,
    ProjectStatus,
    Platform,
)
from ..services.file_storage import (
    get_file_storage,
    get_project_files,
    delete_project_files,
    ProjectFiles,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])

# In-memory storage for local development
# Will be replaced with Supabase in production
_projects_db: dict = {}


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[ProjectStatus] = None,
    platform: Optional[Platform] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List all projects with optional filtering.

    - **status**: Filter by project status
    - **platform**: Filter by target platform
    - **limit**: Maximum number of results (default 50)
    - **offset**: Number of results to skip (default 0)
    """
    projects = list(_projects_db.values())

    # Apply filters
    if status:
        projects = [p for p in projects if p["status"] == status.value]
    if platform:
        projects = [p for p in projects if p["platform"] == platform.value]

    # Sort by created_at descending
    projects.sort(key=lambda p: p["created_at"], reverse=True)

    # Apply pagination
    projects = projects[offset:offset + limit]

    return projects


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate):
    """
    Create a new project.

    The project will be created in 'idle' status, ready for code generation.
    """
    project_id = str(uuid.uuid4())
    now = datetime.now()

    project_data = {
        "id": project_id,
        "user_id": "local-dev-user",  # Will be replaced with auth in production
        "name": project.name,
        "description": project.description,
        "platform": project.platform.value,
        "status": ProjectStatus.IDLE.value,
        "created_at": now,
        "updated_at": now,
    }

    _projects_db[project_id] = project_data

    return project_data


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get a project by ID"""
    if project_id not in _projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    return _projects_db[project_id]


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[ProjectStatus] = None
):
    """Update a project's details"""
    if project_id not in _projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    project = _projects_db[project_id]

    if name is not None:
        project["name"] = name
    if description is not None:
        project["description"] = description
    if status is not None:
        project["status"] = status.value

    project["updated_at"] = datetime.now()

    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str):
    """Delete a project"""
    if project_id not in _projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    del _projects_db[project_id]
    return None


@router.get("/{project_id}/files")
async def get_files_for_project(project_id: str):
    """
    Get all generated files for a project.

    Returns file metadata and content from storage.
    """
    if project_id not in _projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        project_files: ProjectFiles = await get_project_files(project_id)

        # Convert to response format
        files_dict = {}
        for path, stored_file in project_files.files.items():
            files_dict[path] = {
                "content": stored_file.content,
                "language": stored_file.language,
                "size_bytes": stored_file.size_bytes,
            }

        return {
            "project_id": project_id,
            "files": files_dict,
            "file_count": project_files.file_count,
            "total_size_bytes": project_files.total_size_bytes,
        }

    except Exception as e:
        logger.error(f"Failed to get files for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve files: {str(e)}")


@router.get("/{project_id}/files/{file_path:path}")
async def get_single_file(project_id: str, file_path: str):
    """
    Get a single file from a project.

    Args:
        project_id: Project ID
        file_path: Path to the file within the project
    """
    if project_id not in _projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        storage = get_file_storage()
        stored_file = await storage.get_file(project_id, file_path)

        if stored_file is None:
            raise HTTPException(status_code=404, detail="File not found")

        return {
            "path": stored_file.path,
            "content": stored_file.content,
            "language": stored_file.language,
            "size_bytes": stored_file.size_bytes,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file {file_path} for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve file: {str(e)}")


@router.delete("/{project_id}/files")
async def delete_files_for_project(project_id: str):
    """
    Delete all generated files for a project.
    """
    if project_id not in _projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        success = await delete_project_files(project_id)

        if success:
            return {"message": "Files deleted successfully", "project_id": project_id}
        else:
            return {"message": "No files to delete", "project_id": project_id}

    except Exception as e:
        logger.error(f"Failed to delete files for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete files: {str(e)}")
