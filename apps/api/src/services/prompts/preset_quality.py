"""
Preset Quality Evaluation & Enhancement

This module enables agents to:
1. Score preset quality based on multiple signals
2. Identify problems in presets (missing data, bad structure)
3. Auto-enhance weak presets by learning from successful ones
4. Merge best patterns from high-performing presets

Quality Signals:
- Completeness: Are all required fields present?
- Consistency: Do entities/actions align with pages/data?
- Validation: Did it pass code validation?
- User feedback: Did users like the output?
- Engagement: Did users interact with the preview?
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# Custom exceptions for better error handling
class PresetQualityError(Exception):
    """Base exception for quality system"""
    pass


class EnhancementError(PresetQualityError):
    """Enhancement failed"""
    pass


class EvaluationError(PresetQualityError):
    """Quality evaluation failed"""
    pass


class PatternParsingError(PresetQualityError):
    """Failed to parse pattern from description"""
    pass


class QualityIssue(Enum):
    """Types of quality issues in presets"""
    MISSING_DATA_SOURCE = "missing_data_source"
    ORPHAN_PAGE = "orphan_page"  # Page with no useful sections
    EMPTY_SECTIONS = "empty_sections"
    NO_STAT_CARDS = "no_stat_cards"
    GENERIC_TERMINOLOGY = "generic_terminology"  # Using "user" instead of domain term
    MISSING_PRIMARY_ACTION = "missing_primary_action"
    LOW_ENTITY_COVERAGE = "low_entity_coverage"  # Detected entities not reflected in pages
    INCONSISTENT_METRICS = "inconsistent_metrics"  # Stats don't match architecture
    VALIDATION_FAILURES = "validation_failures"
    USER_NEGATIVE_FEEDBACK = "user_negative_feedback"


@dataclass
class QualityScore:
    """Quality assessment for a preset"""
    overall_score: float = 0.0  # 0-1

    # Component scores
    completeness_score: float = 0.0
    consistency_score: float = 0.0
    structure_score: float = 0.0

    # Issues found
    issues: List[Tuple[QualityIssue, str]] = field(default_factory=list)

    # Suggestions for improvement
    suggestions: List[str] = field(default_factory=list)

    # Can this preset be auto-enhanced?
    can_enhance: bool = False
    enhancement_priority: int = 0  # Higher = more urgent


@dataclass
class EnhancementResult:
    """Result of auto-enhancing a preset"""
    enhanced: bool = False
    changes_made: List[str] = field(default_factory=list)
    new_domain: Optional[Dict[str, Any]] = None
    new_architecture: Optional[Dict[str, Any]] = None
    new_mock_data: Optional[Dict[str, Any]] = None


class PresetQualityEvaluator:
    """
    Evaluates preset quality and identifies problems.

    This is like a QA agent that reviews generated presets
    before they're shown to users.
    """

    def evaluate(
        self,
        domain: Dict[str, Any],
        architecture: Dict[str, Any],
        mock_data: Dict[str, Any],
        concepts: Optional[Any] = None,  # ExtractedConcepts
        validation_result: Optional[Any] = None,
    ) -> QualityScore:
        """
        Evaluate preset quality across multiple dimensions.

        Returns a QualityScore with issues and suggestions.
        """
        score = QualityScore()

        # 1. Check completeness
        completeness_issues = self._check_completeness(domain, architecture, mock_data)
        score.issues.extend(completeness_issues)
        score.completeness_score = 1.0 - (len(completeness_issues) * 0.1)

        # 2. Check consistency
        consistency_issues = self._check_consistency(domain, architecture, mock_data, concepts)
        score.issues.extend(consistency_issues)
        score.consistency_score = 1.0 - (len(consistency_issues) * 0.15)

        # 3. Check structure quality
        structure_issues = self._check_structure(architecture)
        score.issues.extend(structure_issues)
        score.structure_score = 1.0 - (len(structure_issues) * 0.1)

        # 4. Add validation issues if provided
        if validation_result and hasattr(validation_result, 'errors'):
            for error in validation_result.errors:
                score.issues.append((QualityIssue.VALIDATION_FAILURES, error))

        # Calculate overall score
        score.overall_score = (
            score.completeness_score * 0.3 +
            score.consistency_score * 0.4 +
            score.structure_score * 0.3
        )
        score.overall_score = max(0.0, min(1.0, score.overall_score))

        # Generate suggestions
        score.suggestions = self._generate_suggestions(score.issues)

        # Determine if enhancement is possible
        score.can_enhance = score.overall_score < 0.8 and score.overall_score > 0.3
        score.enhancement_priority = int((1.0 - score.overall_score) * 10)

        return score

    def _check_completeness(
        self,
        domain: Dict[str, Any],
        architecture: Dict[str, Any],
        mock_data: Dict[str, Any]
    ) -> List[Tuple[QualityIssue, str]]:
        """Check if all required fields are present"""
        issues = []

        # Check domain completeness
        required_domain_fields = ["industry", "key_entities", "terminology"]
        for field in required_domain_fields:
            if not domain.get(field):
                issues.append((QualityIssue.MISSING_DATA_SOURCE, f"Domain missing '{field}'"))

        # Check architecture completeness
        if not architecture.get("pages"):
            issues.append((QualityIssue.EMPTY_SECTIONS, "No pages defined"))
        if not architecture.get("stat_cards"):
            issues.append((QualityIssue.NO_STAT_CARDS, "No stat cards defined"))
        if not architecture.get("primary_action"):
            issues.append((QualityIssue.MISSING_PRIMARY_ACTION, "No primary action defined"))

        # Check mock data completeness
        if not mock_data.get("stats"):
            issues.append((QualityIssue.MISSING_DATA_SOURCE, "Mock data missing 'stats'"))

        # Check that all data sources in architecture exist in mock data
        for page in architecture.get("pages", []):
            for section in page.get("sections", []):
                source = section.get("data_source")
                if source and source not in mock_data:
                    issues.append((
                        QualityIssue.MISSING_DATA_SOURCE,
                        f"Data source '{source}' referenced in page '{page.get('title')}' but not in mock data"
                    ))

        return issues

    def _check_consistency(
        self,
        domain: Dict[str, Any],
        architecture: Dict[str, Any],
        mock_data: Dict[str, Any],
        concepts: Optional[Any]
    ) -> List[Tuple[QualityIssue, str]]:
        """Check if components are consistent with each other"""
        issues = []

        # Check if terminology is actually used
        terminology = domain.get("terminology", {})
        if terminology:
            # Check if we're still using generic terms instead of domain-specific
            for page in architecture.get("pages", []):
                title = page.get("title", "").lower()
                for generic in ["user", "item", "order"]:
                    specific = terminology.get(generic, "")
                    if generic in title and specific and generic != specific:
                        issues.append((
                            QualityIssue.GENERIC_TERMINOLOGY,
                            f"Page '{page.get('title')}' uses generic term '{generic}' instead of '{specific}'"
                        ))

        # Check entity coverage (if concepts provided)
        if concepts and hasattr(concepts, 'entities'):
            detected_entities = set(concepts.entities)
            page_paths = {p.get("path", "") for p in architecture.get("pages", [])}

            # Map entities to expected pages
            entity_pages = {
                "proposal": "/governance",
                "vote": "/voting",
                "order": "/orders",
                "booking": "/bookings",
                "product": "/products",
                "user": "/users",
                "member": "/members",
            }

            for entity in detected_entities:
                expected_path = entity_pages.get(entity)
                if expected_path and expected_path not in page_paths:
                    issues.append((
                        QualityIssue.LOW_ENTITY_COVERAGE,
                        f"Detected entity '{entity}' but no corresponding page (expected '{expected_path}')"
                    ))

        # Check stat card metrics match mock data stats
        for stat_card in architecture.get("stat_cards", []):
            data_key = stat_card.get("data_key")
            if data_key and data_key not in mock_data.get("stats", {}):
                issues.append((
                    QualityIssue.INCONSISTENT_METRICS,
                    f"Stat card '{stat_card.get('title')}' references '{data_key}' not in mock data"
                ))

        return issues

    def _check_structure(
        self,
        architecture: Dict[str, Any]
    ) -> List[Tuple[QualityIssue, str]]:
        """Check structural quality of architecture"""
        issues = []

        pages = architecture.get("pages", [])

        # Check for orphan pages (no sections or all empty sections)
        for page in pages:
            sections = page.get("sections", [])
            if not sections:
                issues.append((
                    QualityIssue.ORPHAN_PAGE,
                    f"Page '{page.get('title')}' has no sections"
                ))
            elif all(not s.get("data_source") for s in sections):
                issues.append((
                    QualityIssue.EMPTY_SECTIONS,
                    f"Page '{page.get('title')}' has sections but no data sources"
                ))

        # Check for duplicate pages
        paths = [p.get("path") for p in pages]
        if len(paths) != len(set(paths)):
            issues.append((
                QualityIssue.ORPHAN_PAGE,
                "Duplicate page paths detected"
            ))

        # Check for minimum viable structure
        if len(pages) < 2:
            issues.append((
                QualityIssue.EMPTY_SECTIONS,
                "Architecture has fewer than 2 pages - too minimal"
            ))

        return issues

    def _generate_suggestions(
        self,
        issues: List[Tuple[QualityIssue, str]]
    ) -> List[str]:
        """Generate actionable suggestions based on issues"""
        suggestions = []
        issue_types = {issue[0] for issue in issues}

        if QualityIssue.MISSING_DATA_SOURCE in issue_types:
            suggestions.append("Add missing data sources to mock data or remove references")

        if QualityIssue.GENERIC_TERMINOLOGY in issue_types:
            suggestions.append("Replace generic terms with domain-specific terminology")

        if QualityIssue.LOW_ENTITY_COVERAGE in issue_types:
            suggestions.append("Add pages for detected entities that are missing")

        if QualityIssue.NO_STAT_CARDS in issue_types:
            suggestions.append("Add stat cards for key metrics")

        if QualityIssue.INCONSISTENT_METRICS in issue_types:
            suggestions.append("Ensure stat card data_keys exist in mock data stats")

        if QualityIssue.EMPTY_SECTIONS in issue_types:
            suggestions.append("Add meaningful sections with data sources to pages")

        return suggestions


class PresetEnhancer:
    """
    Auto-enhances weak presets by learning from successful patterns.

    This is like a senior developer reviewing and improving junior code.
    Patterns are persisted to disk for learning across restarts.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.evaluator = PresetQualityEvaluator()
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data"

        # Patterns learned from successful presets (loaded from disk)
        self._successful_patterns = self._load_patterns()

    def _load_patterns(self) -> Dict[str, List[Dict]]:
        """Load learned patterns from disk"""
        default_patterns = {
            "entity_page_patterns": [],
            "stat_card_patterns": [],
            "section_patterns": [],
        }
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            patterns_file = self.data_dir / "learned_patterns.json"
            if patterns_file.exists():
                loaded = json.loads(patterns_file.read_text())
                logger.info(f"Loaded {sum(len(v) for v in loaded.values())} learned patterns")
                return loaded
        except Exception as e:
            logger.warning(f"Failed to load learned patterns: {e}")
        return default_patterns

    def _save_patterns(self) -> None:
        """Save learned patterns to disk"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            patterns_file = self.data_dir / "learned_patterns.json"
            patterns_file.write_text(json.dumps(self._successful_patterns, indent=2))
            logger.debug("Saved learned patterns to disk")
        except Exception as e:
            logger.warning(f"Failed to save learned patterns: {e}")

    def learn_from_success(
        self,
        domain: Dict[str, Any],
        architecture: Dict[str, Any],
        mock_data: Dict[str, Any],
        confidence: float
    ) -> None:
        """
        Learn patterns from a successful preset.

        Called when a preset has high confidence or positive feedback.
        """
        if confidence < 0.7:
            return  # Only learn from good presets

        # Extract patterns

        # 1. Entity -> Page patterns
        concepts_info = domain.get("_concepts", {})
        entities = concepts_info.get("entities", [])
        for page in architecture.get("pages", []):
            for entity in entities:
                if entity.lower() in page.get("path", "").lower():
                    self._successful_patterns["entity_page_patterns"].append({
                        "entity": entity,
                        "page_config": {
                            "path": page.get("path"),
                            "title": page.get("title"),
                            "icon": page.get("icon"),
                            "sections": page.get("sections", [])
                        }
                    })

        # 2. Metric -> Stat card patterns
        for stat_card in architecture.get("stat_cards", []):
            self._successful_patterns["stat_card_patterns"].append({
                "data_key": stat_card.get("data_key"),
                "title": stat_card.get("title"),
                "icon": stat_card.get("icon"),
                "color": stat_card.get("color"),
            })

        # Limit pattern storage
        for key in self._successful_patterns:
            self._successful_patterns[key] = self._successful_patterns[key][-50:]

        # Persist to disk
        self._save_patterns()

        logger.debug(f"Learned patterns from successful preset (confidence={confidence})")

    def enhance(
        self,
        domain: Dict[str, Any],
        architecture: Dict[str, Any],
        mock_data: Dict[str, Any],
        concepts: Optional[Any] = None
    ) -> EnhancementResult:
        """
        Attempt to enhance a weak preset.

        Returns EnhancementResult with changes made.
        """
        result = EnhancementResult()

        # First evaluate current quality
        score = self.evaluator.evaluate(domain, architecture, mock_data, concepts)

        if score.overall_score > 0.8:
            # Already good enough
            return result

        # Make copies to modify
        import copy
        new_domain = copy.deepcopy(domain)
        new_architecture = copy.deepcopy(architecture)
        new_mock_data = copy.deepcopy(mock_data)

        # Fix issues
        for issue, description in score.issues:
            fixed = self._fix_issue(
                issue, description,
                new_domain, new_architecture, new_mock_data,
                concepts
            )
            if fixed:
                result.changes_made.append(f"Fixed: {description}")

        # Apply learned patterns
        patterns_applied = self._apply_patterns(
            new_domain, new_architecture, new_mock_data, concepts
        )
        result.changes_made.extend(patterns_applied)

        if result.changes_made:
            result.enhanced = True
            result.new_domain = new_domain
            result.new_architecture = new_architecture
            result.new_mock_data = new_mock_data

        return result

    def _fix_issue(
        self,
        issue: QualityIssue,
        description: str,
        domain: Dict[str, Any],
        architecture: Dict[str, Any],
        mock_data: Dict[str, Any],
        concepts: Optional[Any]
    ) -> bool:
        """Attempt to fix a specific issue. Returns True if fixed."""
        try:
            if issue == QualityIssue.MISSING_DATA_SOURCE:
                # Defensive parsing - extract the missing source name
                source = self._extract_quoted_value(description)
                if source and source not in mock_data:
                    mock_data[source] = self._generate_placeholder_data(source)
                    return True

            elif issue == QualityIssue.NO_STAT_CARDS:
                # Add default stat cards based on domain metrics
                metrics = domain.get("metrics", ["total_items", "active_users", "growth_rate", "satisfaction"])
                colors = ["blue", "green", "purple", "amber"]
                icons = ["list", "users", "trending-up", "star"]

                architecture["stat_cards"] = [
                    {
                        "title": m.replace("_", " ").title(),
                        "data_key": m,
                        "icon": icons[i % len(icons)],
                        "color": colors[i % len(colors)]
                    }
                    for i, m in enumerate(metrics[:4])
                ]
                return True

            elif issue == QualityIssue.INCONSISTENT_METRICS:
                # Add missing metric to mock data
                # Stats is now an array of objects, not a dict
                stats_list = mock_data.get("stats", [])
                if not isinstance(stats_list, list):
                    stats_list = []
                    mock_data["stats"] = stats_list

                existing_titles = {s.get("title", "").lower() for s in stats_list if isinstance(s, dict)}

                for stat_card in architecture.get("stat_cards", []):
                    data_key = stat_card.get("data_key", "")
                    title = stat_card.get("title", data_key.replace("_", " ").title())

                    if title.lower() not in existing_titles:
                        change_value = f"+{(hash(data_key) % 15) + 5}%"
                        stats_list.append({
                            "title": title,
                            "value": str(self._generate_stat_value(data_key)),
                            "change": change_value,
                            "changeType": "increase" if change_value.startswith("+") else "decrease",
                            "icon": stat_card.get("icon", "TrendingUp")
                        })
                        existing_titles.add(title.lower())
                return True

            elif issue == QualityIssue.LOW_ENTITY_COVERAGE and concepts:
                # Add missing pages for entities
                entities = concepts.entities if hasattr(concepts, 'entities') else []
                existing_paths = {p.get("path") for p in architecture.get("pages", [])}

                entity_pages = {
                    "proposal": {"path": "/governance", "title": "Governance", "icon": "vote"},
                    "vote": {"path": "/voting", "title": "Voting", "icon": "check-square"},
                    "order": {"path": "/orders", "title": "Orders", "icon": "shopping-cart"},
                    "booking": {"path": "/bookings", "title": "Bookings", "icon": "calendar"},
                    "product": {"path": "/products", "title": "Products", "icon": "package"},
                }

                for entity in entities:
                    if entity in entity_pages:
                        config = entity_pages[entity]
                        if config["path"] not in existing_paths:
                            architecture.setdefault("pages", []).append({
                                "path": config["path"],
                                "title": config["title"],
                                "icon": config["icon"],
                                "sections": [{
                                    "id": f"{entity}-table",
                                    "title": f"All {config['title']}",
                                    "component_type": "table",
                                    "data_source": f"{entity}s",
                                    "colspan": 3
                                }]
                            })
                            return True

            elif issue == QualityIssue.MISSING_PRIMARY_ACTION:
                # Add primary action based on entities
                entities = domain.get("key_entities", [])
                if entities:
                    primary_entity = entities[0]
                    architecture["primary_action"] = f"New {primary_entity.title()}"
                else:
                    architecture["primary_action"] = "Create New"
                return True

        except Exception as e:
            logger.warning(f"Failed to fix issue {issue}: {e}")
            return False

        return False

    def _extract_quoted_value(self, text: str) -> Optional[str]:
        """Safely extract a quoted value from text (e.g., 'value' or "value")"""
        try:
            # Try single quotes first
            if "'" in text:
                parts = text.split("'")
                if len(parts) >= 2:
                    return parts[1]
            # Try double quotes
            if '"' in text:
                parts = text.split('"')
                if len(parts) >= 2:
                    return parts[1]
        except (IndexError, ValueError) as e:
            logger.warning(f"Failed to extract quoted value from: {text[:50]}...")
        return None

    def _apply_patterns(
        self,
        domain: Dict[str, Any],
        architecture: Dict[str, Any],
        mock_data: Dict[str, Any],
        concepts: Optional[Any]
    ) -> List[str]:
        """Apply learned patterns from successful presets"""
        changes = []

        # Apply entity->page patterns
        if concepts and hasattr(concepts, 'entities'):
            existing_paths = {p.get("path") for p in architecture.get("pages", [])}

            for entity in concepts.entities:
                for pattern in self._successful_patterns.get("entity_page_patterns", []):
                    if pattern["entity"] == entity:
                        page_config = pattern["page_config"]
                        if page_config["path"] not in existing_paths:
                            architecture.setdefault("pages", []).append(page_config)
                            changes.append(f"Added page pattern for '{entity}'")
                            break

        return changes

    def _generate_placeholder_data(self, source: str) -> List[Dict]:
        """Generate placeholder data for a missing source"""
        # Generic placeholder based on source name
        return [
            {"id": f"{source}-001", "name": f"{source.title()} Item 1", "status": "active"},
            {"id": f"{source}-002", "name": f"{source.title()} Item 2", "status": "pending"},
            {"id": f"{source}-003", "name": f"{source.title()} Item 3", "status": "completed"},
        ]

    def _generate_stat_value(self, key: str) -> Any:
        """Generate a realistic stat value"""
        key_lower = key.lower()
        if "rate" in key_lower or "percent" in key_lower:
            return f"{78 + hash(key) % 20}%"
        elif "revenue" in key_lower or "value" in key_lower:
            return f"${(hash(key) % 50 + 10) * 100:,}"
        elif "count" in key_lower or "total" in key_lower:
            return 100 + (hash(key) % 900)
        return hash(key) % 100 + 50


class PresetFeedbackAnalyzer:
    """
    Analyzes feedback to identify patterns in what makes presets good or bad.

    This enables the system to learn from user behavior, not just explicit feedback.
    Feedback data is persisted to disk for learning across restarts.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data"
        # Track correlations between features and outcomes (loaded from disk)
        self.feature_outcomes = self._load_data()

    def _load_data(self) -> Dict[str, Dict[str, int]]:
        """Load feedback data from disk"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            feedback_file = self.data_dir / "feedback_outcomes.json"
            if feedback_file.exists():
                loaded = json.loads(feedback_file.read_text())
                logger.info(f"Loaded feedback data for {len(loaded)} features")
                return loaded
        except Exception as e:
            logger.warning(f"Failed to load feedback data: {e}")
        return {}

    def _save_data(self) -> None:
        """Save feedback data to disk"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            feedback_file = self.data_dir / "feedback_outcomes.json"
            feedback_file.write_text(json.dumps(self.feature_outcomes, indent=2))
            logger.debug("Saved feedback data to disk")
        except Exception as e:
            logger.warning(f"Failed to save feedback data: {e}")

    def record_outcome(
        self,
        domain: Dict[str, Any],
        architecture: Dict[str, Any],
        positive: bool
    ) -> None:
        """
        Record the outcome of a preset to learn correlations.
        """
        outcome_key = "positive" if positive else "negative"

        # Extract features to track
        features = []

        # Industry
        industry = domain.get("industry", "unknown")
        features.append(f"industry:{industry}")

        # Number of pages
        page_count = len(architecture.get("pages", []))
        features.append(f"pages:{page_count}")

        # Entities present
        for entity in domain.get("key_entities", [])[:3]:
            features.append(f"entity:{entity}")

        # Stat card count
        stat_count = len(architecture.get("stat_cards", []))
        features.append(f"stat_cards:{stat_count}")

        # Record each feature
        for feature in features:
            if feature not in self.feature_outcomes:
                self.feature_outcomes[feature] = {"positive": 0, "negative": 0}
            self.feature_outcomes[feature][outcome_key] += 1

        # Persist to disk
        self._save_data()

    def get_insights(self) -> Dict[str, Any]:
        """
        Get insights about what features correlate with success.
        """
        insights = {
            "positive_features": [],
            "negative_features": [],
            "uncertain_features": [],
        }

        for feature, outcomes in self.feature_outcomes.items():
            total = outcomes["positive"] + outcomes["negative"]
            if total < 3:
                continue  # Not enough data

            positive_rate = outcomes["positive"] / total

            if positive_rate > 0.7:
                insights["positive_features"].append({
                    "feature": feature,
                    "positive_rate": round(positive_rate, 2),
                    "sample_size": total
                })
            elif positive_rate < 0.3:
                insights["negative_features"].append({
                    "feature": feature,
                    "positive_rate": round(positive_rate, 2),
                    "sample_size": total
                })
            else:
                insights["uncertain_features"].append({
                    "feature": feature,
                    "positive_rate": round(positive_rate, 2),
                    "sample_size": total
                })

        # Sort by strength of signal
        insights["positive_features"].sort(key=lambda x: -x["positive_rate"])
        insights["negative_features"].sort(key=lambda x: x["positive_rate"])

        return insights

    def should_avoid(self, feature: str) -> bool:
        """Check if a feature should be avoided based on historical data"""
        if feature in self.feature_outcomes:
            outcomes = self.feature_outcomes[feature]
            total = outcomes["positive"] + outcomes["negative"]
            if total >= 5:
                positive_rate = outcomes["positive"] / total
                return positive_rate < 0.3
        return False


# Singleton instances
_evaluator: Optional[PresetQualityEvaluator] = None
_enhancer: Optional[PresetEnhancer] = None
_feedback_analyzer: Optional[PresetFeedbackAnalyzer] = None


def get_evaluator() -> PresetQualityEvaluator:
    global _evaluator
    if _evaluator is None:
        _evaluator = PresetQualityEvaluator()
    return _evaluator


def get_enhancer() -> PresetEnhancer:
    global _enhancer
    if _enhancer is None:
        _enhancer = PresetEnhancer()
    return _enhancer


def get_feedback_analyzer() -> PresetFeedbackAnalyzer:
    global _feedback_analyzer
    if _feedback_analyzer is None:
        _feedback_analyzer = PresetFeedbackAnalyzer()
    return _feedback_analyzer


def evaluate_preset(
    domain: Dict[str, Any],
    architecture: Dict[str, Any],
    mock_data: Dict[str, Any],
    concepts: Optional[Any] = None
) -> QualityScore:
    """Convenience function to evaluate preset quality"""
    return get_evaluator().evaluate(domain, architecture, mock_data, concepts)


def enhance_preset(
    domain: Dict[str, Any],
    architecture: Dict[str, Any],
    mock_data: Dict[str, Any],
    concepts: Optional[Any] = None
) -> EnhancementResult:
    """Convenience function to enhance a weak preset"""
    return get_enhancer().enhance(domain, architecture, mock_data, concepts)
