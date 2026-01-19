"""
Project and Agent models for Code Weaver Pro
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from enum import Enum


class Platform(str, Enum):
    WEB = "web"
    IOS = "ios"
    ANDROID = "android"
    ALL = "all"


class ProjectStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    DESIGNING = "designing"
    GENERATING = "generating"
    TESTING = "testing"
    COMPLETE = "complete"
    ERROR = "error"


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


# Request Models
class ProjectCreate(BaseModel):
    """Request model for creating a new project"""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    platform: Platform = Platform.WEB


class AgentExecutionCreate(BaseModel):
    """Request model for creating an agent execution"""
    project_id: str
    agent_name: str
    agent_type: Optional[str] = None
    input: Optional[Dict[str, Any]] = None


class GenerationRequest(BaseModel):
    """Request model for code generation"""
    description: str = Field(..., min_length=1)
    platform: Platform = Platform.WEB
    project_id: Optional[str] = None


# Response Models
class ProjectResponse(BaseModel):
    """Response model for project data"""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    platform: Platform
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentExecutionResponse(BaseModel):
    """Response model for agent execution data"""
    id: str
    project_id: str
    agent_name: str
    agent_type: Optional[str] = None
    status: AgentStatus
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# WebSocket Event Models
class GenerationEvent(BaseModel):
    """Events sent over WebSocket during generation"""
    type: Literal["status", "agent_start", "agent_complete", "agent_error", "parallel_start", "files", "complete", "error"]
    message: Optional[str] = None
    agent: Optional[str] = None
    agent_type: Optional[str] = None
    agents: Optional[List[str]] = None  # For parallel_start events
    output: Optional[str] = None
    error: Optional[str] = None
    files: Optional[Dict[str, str]] = None
    progress: Optional[int] = None
    summary: Optional[Dict[str, Any]] = None
