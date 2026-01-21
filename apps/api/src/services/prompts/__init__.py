"""
Creative Prototype Prompts

Specialized prompts for the 5-agent creative pipeline that transforms
generic templates into domain-specific prototypes.

Agents:
1. DomainAnalyst - Understands the client's business domain
2. Architect - Plans domain-specific sections and pages
3. ContentGenerator - Creates realistic mock data
4. Quality Analyst - Evaluates and enhances presets
5. UIComposer - Generates components with domain content
6. Validator - Pre-WebContainer validation checks

Smart Preset System:
- Learns from usage patterns
- Weighted keyword extraction (TF-IDF style)
- Composite preset generation
- Caching with similarity matching

Quality System:
- 3-dimension scoring (completeness, consistency, structure)
- Auto-enhancement with learned patterns
- Feedback-driven learning
- Configurable thresholds

Audit Trail:
- JSONL append-only logging
- Quality trends over time
- Failure debugging
"""

from .domain_analyst import DOMAIN_ANALYST_PROMPT, DomainAnalysis
from .architect import ARCHITECT_PROMPT, PrototypeArchitecture
from .content_generator import CONTENT_GENERATOR_PROMPT, MockDataSchema
from .smart_presets import (
    SmartPresetSystem,
    ExtractedConcepts,
    KeywordExtractor,
    PresetComposer,
    PresetCache,
    CachedPreset,
    get_smart_preset_system,
    get_smart_preset,
    extract_concepts,
)
from .preset_quality import (
    QualityScore,
    QualityIssue,
    EnhancementResult,
    PresetQualityEvaluator,
    PresetEnhancer,
    PresetFeedbackAnalyzer,
    PresetQualityError,
    EnhancementError,
    EvaluationError,
    PatternParsingError,
    evaluate_preset,
    enhance_preset,
    get_enhancer,
    get_feedback_analyzer,
)
from .quality_config import (
    QualityConfig,
    get_quality_config,
    set_quality_config,
    load_config,
    save_config,
)
from .generation_audit import (
    GenerationEvent,
    GenerationAuditLog,
    get_audit_log,
)

__all__ = [
    # Original prompts
    "DOMAIN_ANALYST_PROMPT",
    "DomainAnalysis",
    "ARCHITECT_PROMPT",
    "PrototypeArchitecture",
    "CONTENT_GENERATOR_PROMPT",
    "MockDataSchema",
    # Smart preset system
    "SmartPresetSystem",
    "ExtractedConcepts",
    "KeywordExtractor",
    "PresetComposer",
    "PresetCache",
    "CachedPreset",
    "get_smart_preset_system",
    "get_smart_preset",
    "extract_concepts",
    # Quality evaluation
    "QualityScore",
    "QualityIssue",
    "EnhancementResult",
    "PresetQualityEvaluator",
    "PresetEnhancer",
    "PresetFeedbackAnalyzer",
    "PresetQualityError",
    "EnhancementError",
    "EvaluationError",
    "PatternParsingError",
    "evaluate_preset",
    "enhance_preset",
    "get_enhancer",
    "get_feedback_analyzer",
    # Quality configuration
    "QualityConfig",
    "get_quality_config",
    "set_quality_config",
    "load_config",
    "save_config",
    # Audit trail
    "GenerationEvent",
    "GenerationAuditLog",
    "get_audit_log",
]
