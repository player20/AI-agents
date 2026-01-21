"""
Quality System Configuration

Centralized configuration for all quality evaluation and enhancement thresholds.
This allows tuning the system without changing code.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class QualityConfig:
    """Centralized configuration for quality system"""

    # Score weights (must sum to 1.0)
    completeness_weight: float = 0.3
    consistency_weight: float = 0.4
    structure_weight: float = 0.3

    # Enhancement thresholds
    min_enhance_score: float = 0.3  # Below this = too broken to fix
    max_enhance_score: float = 0.8  # Above this = good enough

    # Cache settings
    similarity_threshold: float = 0.4  # Min similarity to use cached preset
    min_confidence: float = 0.5  # Min confidence for cached preset
    max_patterns_per_category: int = 50  # Pattern storage limit

    # Learning thresholds
    learn_from_score: float = 0.7  # Only learn from presets scoring above this
    min_feedback_samples: int = 3  # Minimum samples before trusting feedback
    positive_rate_threshold: float = 0.7  # Rate above this = positive feature
    negative_rate_threshold: float = 0.3  # Rate below this = negative feature

    # Required fields (can be customized per domain)
    required_domain_fields: List[str] = field(
        default_factory=lambda: ["industry", "key_entities", "terminology"]
    )

    # Default metrics fallback
    default_metrics: List[str] = field(
        default_factory=lambda: ["total_items", "active_users", "growth_rate", "satisfaction"]
    )

    # Confidence decay (for pattern aging)
    confidence_decay_factor: float = 0.95  # Applied to old patterns

    def validate(self) -> bool:
        """Validate configuration values"""
        # Check weights sum to 1.0
        total_weight = (
            self.completeness_weight +
            self.consistency_weight +
            self.structure_weight
        )
        if abs(total_weight - 1.0) > 0.001:
            logger.warning(f"Score weights sum to {total_weight}, not 1.0")
            return False

        # Check threshold ordering
        if self.min_enhance_score >= self.max_enhance_score:
            logger.warning("min_enhance_score must be less than max_enhance_score")
            return False

        if self.negative_rate_threshold >= self.positive_rate_threshold:
            logger.warning("negative_rate_threshold must be less than positive_rate_threshold")
            return False

        return True


# Global config instance
_config: Optional[QualityConfig] = None


def get_quality_config() -> QualityConfig:
    """Get the current quality configuration"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_quality_config(config: QualityConfig) -> None:
    """Set a new quality configuration"""
    global _config
    if config.validate():
        _config = config
        logger.info("Quality config updated")
    else:
        raise ValueError("Invalid quality configuration")


def load_config(config_path: Optional[Path] = None) -> QualityConfig:
    """
    Load quality configuration from file or return defaults.

    Config file location: data/quality_config.json
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "data" / "quality_config.json"

    try:
        if config_path.exists():
            data = json.loads(config_path.read_text())
            config = QualityConfig(**data)
            if config.validate():
                logger.info(f"Loaded quality config from {config_path}")
                return config
            else:
                logger.warning("Config file invalid, using defaults")
    except Exception as e:
        logger.warning(f"Failed to load quality config: {e}")

    return QualityConfig()


def save_config(config: QualityConfig, config_path: Optional[Path] = None) -> bool:
    """Save quality configuration to file"""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "data" / "quality_config.json"

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "completeness_weight": config.completeness_weight,
            "consistency_weight": config.consistency_weight,
            "structure_weight": config.structure_weight,
            "min_enhance_score": config.min_enhance_score,
            "max_enhance_score": config.max_enhance_score,
            "similarity_threshold": config.similarity_threshold,
            "min_confidence": config.min_confidence,
            "max_patterns_per_category": config.max_patterns_per_category,
            "learn_from_score": config.learn_from_score,
            "min_feedback_samples": config.min_feedback_samples,
            "positive_rate_threshold": config.positive_rate_threshold,
            "negative_rate_threshold": config.negative_rate_threshold,
            "required_domain_fields": config.required_domain_fields,
            "default_metrics": config.default_metrics,
            "confidence_decay_factor": config.confidence_decay_factor,
        }

        config_path.write_text(json.dumps(data, indent=2))
        logger.info(f"Saved quality config to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save quality config: {e}")
        return False
