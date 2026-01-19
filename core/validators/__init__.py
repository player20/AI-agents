"""
Universal Validators Package

Provides automated validation for any code project:
- Project type detection
- Static analysis
- Build validation
- Runtime validation
- UI/Visual validation
- Functional testing
"""

from .project_detector import ProjectDetector, ProjectType
from .static_analyzer import StaticAnalyzer
from .build_validator import BuildValidator
from .runtime_validator import RuntimeValidator
from .ui_validator import UIValidator
from .report_generator import ValidationReportGenerator

__all__ = [
    "ProjectDetector",
    "ProjectType",
    "StaticAnalyzer",
    "BuildValidator",
    "RuntimeValidator",
    "UIValidator",
    "ValidationReportGenerator",
]
