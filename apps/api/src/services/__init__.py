"""
Services for Code Weaver Pro API

Includes:
- WebSocket management for real-time updates
- Code generation with template-first approach
- Prototype orchestration with 5-agent creative pipeline
- Template loading and customization
- Code validation and auto-fixing
"""
from .websocket_manager import ConnectionManager, manager
from .generator import CodeGenerator
from .template_loader import TemplateLoader, get_template_loader
from .template_customizer import TemplateCustomizer, get_template_customizer, BrandProfile
from .code_validator import CodeValidator, validate_files, validate_and_fix
from .prototype_orchestrator import (
    PrototypeOrchestrator,
    PrototypeEvent,
    PrototypeResult,
    get_prototype_orchestrator,
    generate_prototype,
)

__all__ = [
    # WebSocket
    "ConnectionManager",
    "manager",
    # Generation
    "CodeGenerator",
    # Prototype Orchestration (5-agent pipeline)
    "PrototypeOrchestrator",
    "PrototypeEvent",
    "PrototypeResult",
    "get_prototype_orchestrator",
    "generate_prototype",
    # Templates
    "TemplateLoader",
    "get_template_loader",
    "TemplateCustomizer",
    "get_template_customizer",
    "BrandProfile",
    # Validation
    "CodeValidator",
    "validate_files",
    "validate_and_fix",
]
