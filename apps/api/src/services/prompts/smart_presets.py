"""
Smart Preset System v2

A learning system that generates domain presets by:
1. Pattern extraction with TF-IDF style weighting (rare words matter more)
2. Multi-signal matching (entities + actions + domain + patterns)
3. Composite preset generation from multiple partial matches
4. Learning from successful generations to improve over time

Key improvements over v1:
- Weighted keywords (distinctive terms matter more)
- Pattern templates for common phrases
- Composite scoring across multiple signals
- Actual learning: success rate tracking
- Stemming for better matching
"""

import re
import json
import hashlib
import logging
import math
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)


# Common words to ignore (high frequency = low signal)
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "i", "you", "he",
    "she", "it", "we", "they", "what", "which", "who", "when", "where", "why",
    "how", "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "just", "also", "now", "build", "create", "make", "want",
    "need", "like", "app", "application", "system", "tool", "thing", "way",
}

# Word stems for better matching
WORD_STEMS = {
    "voting": "vote", "votes": "vote", "voted": "vote", "voter": "vote",
    "booking": "book", "booked": "book", "books": "book",
    "tracking": "track", "tracked": "track", "tracks": "track", "tracker": "track",
    "managing": "manage", "managed": "manage", "manages": "manage", "management": "manage",
    "scheduling": "schedule", "scheduled": "schedule", "schedules": "schedule",
    "users": "user", "customers": "customer", "clients": "client",
    "orders": "order", "ordering": "order", "ordered": "order",
    "payments": "payment", "paying": "pay", "paid": "pay",
    "products": "product", "items": "item", "services": "service",
    "analytics": "analytic", "analysis": "analyze", "analyzing": "analyze",
    "dashboards": "dashboard", "platforms": "platform", "applications": "app",
}


@dataclass
class ExtractedConcepts:
    """
    Concepts extracted from a user description.

    Uses weighted scoring where distinctive keywords matter more.
    """
    # Weighted keywords (word -> importance score)
    weighted_keywords: Dict[str, float] = field(default_factory=dict)

    # Categorized extractions
    entities: List[str] = field(default_factory=list)  # What things exist
    actions: List[str] = field(default_factory=list)   # What can be done
    domain_signals: Dict[str, float] = field(default_factory=dict)  # domain -> confidence

    # Pattern matches
    matched_patterns: List[str] = field(default_factory=list)

    # Industry matching
    industry_scores: Dict[str, float] = field(default_factory=dict)
    best_industry: str = "universal"
    best_score: float = 0.0

    # Composite matching (combine multiple partial matches)
    secondary_industries: List[str] = field(default_factory=list)

    # Extracted names
    app_name: str = ""
    tagline: str = ""

    @property
    def top_keywords(self) -> List[str]:
        """Get top 10 keywords by weight"""
        sorted_kw = sorted(self.weighted_keywords.items(), key=lambda x: -x[1])
        return [k for k, _ in sorted_kw[:10]]


@dataclass
class CachedPreset:
    """
    A cached preset from a previous successful generation.

    Tracks usage and success for learning.
    """
    description_hash: str
    keywords: List[str]
    weighted_keywords: Dict[str, float]  # For better similarity matching
    preset: Dict[str, Any]
    created_at: str
    use_count: int = 1
    success_count: int = 1  # Times it worked
    failure_count: int = 0  # Times it failed
    user_feedback_score: float = 0.0  # -1 to 1, 0 = no feedback

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 1.0

    @property
    def confidence_score(self) -> float:
        """Confidence based on usage and success"""
        base_confidence = self.success_rate
        usage_boost = min(0.2, self.use_count * 0.02)  # Up to 20% boost for usage
        feedback_boost = self.user_feedback_score * 0.1  # Up to 10% for feedback
        return min(1.0, base_confidence + usage_boost + feedback_boost)


# Weighted keyword mappings for concept extraction
# Format: keyword -> (category, weight)
# Higher weight = more distinctive for that category

ENTITY_SIGNALS = {
    # People/Users (weight indicates distinctiveness)
    "user": ("user", 0.5), "users": ("user", 0.5),
    "account": ("user", 0.6), "accounts": ("user", 0.6),
    "profile": ("user", 0.7), "profiles": ("user", 0.7),
    "member": ("member", 0.8), "members": ("member", 0.8),
    "customer": ("customer", 0.8), "customers": ("customer", 0.8),
    "client": ("client", 0.8), "clients": ("client", 0.8),
    "patient": ("patient", 0.9), "patients": ("patient", 0.9),
    "student": ("student", 0.9), "students": ("student", 0.9),
    "employee": ("employee", 0.8), "employees": ("employee", 0.8),
    "admin": ("admin", 0.7), "administrator": ("admin", 0.8),
    "team": ("team", 0.7), "teams": ("team", 0.7),
    "organization": ("organization", 0.8), "company": ("organization", 0.7),
    "workspace": ("workspace", 0.8),

    # Content entities
    "item": ("item", 0.4), "items": ("item", 0.4),  # Low - too generic
    "product": ("product", 0.8), "products": ("product", 0.8),
    "listing": ("listing", 0.9), "listings": ("listing", 0.9),
    "post": ("post", 0.7), "posts": ("post", 0.7),
    "article": ("article", 0.9), "articles": ("article", 0.9),
    "document": ("document", 0.8), "documents": ("document", 0.8),
    "file": ("file", 0.6), "files": ("file", 0.6),
    "asset": ("asset", 0.7), "assets": ("asset", 0.7),

    # Transaction entities
    "order": ("order", 0.8), "orders": ("order", 0.8),
    "booking": ("booking", 0.9), "bookings": ("booking", 0.9),
    "reservation": ("reservation", 0.9), "reservations": ("reservation", 0.9),
    "appointment": ("appointment", 0.9), "appointments": ("appointment", 0.9),
    "transaction": ("transaction", 0.8), "transactions": ("transaction", 0.8),
    "purchase": ("purchase", 0.8), "purchases": ("purchase", 0.8),
    "invoice": ("invoice", 0.9), "invoices": ("invoice", 0.9),

    # Communication
    "message": ("message", 0.7), "messages": ("message", 0.7),
    "chat": ("chat", 0.8), "chats": ("chat", 0.8),
    "notification": ("notification", 0.7), "notifications": ("notification", 0.7),
    "email": ("email", 0.7), "emails": ("email", 0.7),

    # Governance
    "proposal": ("proposal", 0.95), "proposals": ("proposal", 0.95),
    "vote": ("vote", 0.9), "votes": ("vote", 0.9),
    "ballot": ("ballot", 0.95), "ballots": ("ballot", 0.95),
    "election": ("election", 0.95), "poll": ("poll", 0.9),
}

ACTION_SIGNALS = {
    "create": ("create", 0.5), "add": ("create", 0.4),
    "generate": ("create", 0.7), "compose": ("create", 0.7),
    "view": ("read", 0.4), "browse": ("read", 0.6),
    "search": ("search", 0.8), "find": ("search", 0.6), "discover": ("search", 0.8),
    "edit": ("update", 0.6), "update": ("update", 0.5), "modify": ("update", 0.6),
    "delete": ("delete", 0.6), "remove": ("delete", 0.5),
    "share": ("share", 0.7), "publish": ("share", 0.8), "export": ("share", 0.7),
    "collaborate": ("collaborate", 0.9),
    "track": ("track", 0.8), "monitor": ("track", 0.8),
    "analyze": ("analyze", 0.8), "measure": ("analyze", 0.7),
    "vote": ("vote", 0.95), "rate": ("rate", 0.7), "review": ("review", 0.8),
    "approve": ("approve", 0.8), "reject": ("reject", 0.8),
    "pay": ("pay", 0.8), "purchase": ("pay", 0.8), "subscribe": ("subscribe", 0.9),
    "checkout": ("pay", 0.9), "billing": ("pay", 0.85),
    "book": ("book", 0.85), "schedule": ("schedule", 0.85), "reserve": ("book", 0.85),
}

# Industry signals with weights (higher = more distinctive)
INDUSTRY_SIGNALS = {
    # Tech/SaaS
    "saas": [
        ("software", 0.7), ("platform", 0.6), ("api", 0.9), ("sdk", 0.95),
        ("cloud", 0.8), ("integration", 0.8), ("automation", 0.8),
        ("workflow", 0.75), ("dashboard", 0.6), ("analytics", 0.7),
        ("subscription", 0.8), ("saas", 1.0), ("b2b", 0.9), ("enterprise", 0.8),
    ],
    "blockchain": [
        ("blockchain", 1.0), ("crypto", 0.95), ("token", 0.9), ("nft", 0.95),
        ("dao", 1.0), ("defi", 1.0), ("web3", 1.0), ("wallet", 0.85),
        ("smart contract", 1.0), ("decentralized", 0.95), ("ethereum", 1.0),
        ("solana", 1.0), ("governance", 0.8),
    ],
    "ai": [
        ("ai", 0.9), ("ml", 0.95), ("machine learning", 1.0), ("neural", 0.95),
        ("gpt", 0.95), ("llm", 1.0), ("chatbot", 0.85), ("prediction", 0.7),
        ("model", 0.5), ("training", 0.6), ("inference", 0.9),
    ],

    # Healthcare
    "healthcare": [
        ("health", 0.7), ("medical", 0.9), ("patient", 0.95), ("doctor", 0.9),
        ("clinic", 0.95), ("hospital", 0.95), ("diagnosis", 0.95),
        ("treatment", 0.85), ("prescription", 0.95), ("telehealth", 1.0),
        ("ehr", 1.0), ("hipaa", 1.0), ("healthcare", 1.0),
    ],
    "fitness": [
        ("fitness", 0.95), ("gym", 0.95), ("workout", 0.95), ("exercise", 0.9),
        ("yoga", 0.95), ("pilates", 0.95), ("trainer", 0.8), ("class", 0.5),
        ("membership", 0.6), ("wellness", 0.8),
    ],

    # Commerce
    "ecommerce": [
        ("ecommerce", 1.0), ("e-commerce", 1.0), ("shop", 0.8), ("store", 0.7),
        ("cart", 0.9), ("checkout", 0.9), ("inventory", 0.85), ("sku", 0.95),
        ("shipping", 0.85), ("product", 0.6), ("catalog", 0.8), ("marketplace", 0.9),
        ("retail", 0.85), ("wholesale", 0.9),
    ],

    # Food/Restaurant
    "restaurant": [
        ("restaurant", 1.0), ("cafe", 0.95), ("bistro", 0.95), ("menu", 0.85),
        ("table", 0.6), ("reservation", 0.75), ("order", 0.5), ("kitchen", 0.85),
        ("chef", 0.9), ("dining", 0.9), ("food", 0.7), ("delivery", 0.7),
        ("pos", 0.8), ("recipe", 0.85),
    ],

    # Education
    "education": [
        ("education", 0.95), ("learning", 0.8), ("course", 0.85), ("lesson", 0.85),
        ("student", 0.8), ("teacher", 0.85), ("instructor", 0.85), ("curriculum", 0.95),
        ("lms", 1.0), ("quiz", 0.8), ("assignment", 0.85), ("grade", 0.8),
        ("school", 0.85), ("university", 0.9), ("training", 0.7),
    ],

    # News/Media
    "news-media": [
        ("news", 0.9), ("journalism", 0.95), ("article", 0.8), ("reporter", 0.95),
        ("editorial", 0.95), ("fact", 0.7), ("source", 0.6), ("breaking", 0.85),
        ("headline", 0.9), ("media", 0.7), ("press", 0.85), ("publication", 0.85),
    ],

    # Pet services
    "pet-services": [
        ("pet", 0.95), ("dog", 0.9), ("cat", 0.9), ("grooming", 0.95),
        ("veterinary", 1.0), ("vet", 0.95), ("animal", 0.8), ("kennel", 0.95),
        ("boarding", 0.8), ("walking", 0.7), ("sitting", 0.7),
    ],

    # Real estate
    "real-estate": [
        ("real estate", 1.0), ("property", 0.85), ("listing", 0.75), ("mls", 1.0),
        ("agent", 0.6), ("broker", 0.85), ("mortgage", 0.95), ("rental", 0.8),
        ("tenant", 0.85), ("landlord", 0.9), ("lease", 0.85), ("housing", 0.8),
    ],

    # Finance
    "finance": [
        ("finance", 0.9), ("banking", 0.95), ("investment", 0.9), ("portfolio", 0.85),
        ("stock", 0.9), ("trading", 0.9), ("budget", 0.8), ("expense", 0.8),
        ("accounting", 0.9), ("invoice", 0.8), ("payment", 0.7), ("fintech", 1.0),
    ],
}

# Pattern templates for common descriptions
# These help extract structure from natural language
DESCRIPTION_PATTERNS = [
    # "[App Name] for [Industry/Use case]"
    (r"(?:build|create|make)?\s*([A-Z][a-zA-Z]+(?:\s+[A-Z]?[a-zA-Z]+)*)\s*(?:,|-)?\s*(?:a|an)?\s*(.+?)(?:platform|app|tool|system|dashboard)?$", "name_for_usecase"),

    # "[Type] for [Target users]"
    (r"(?:a|an)?\s*(\w+(?:\s+\w+)?)\s+(?:platform|app|tool|system)\s+for\s+(.+)", "type_for_users"),

    # "[Industry] [Type]"
    (r"(?:a|an)?\s*(\w+)\s+(dashboard|platform|app|tool|system|portal|hub)", "industry_type"),

    # "manage/track [Entities]"
    (r"(?:manage|track|organize|handle)\s+(?:my|your|our)?\s*(.+)", "action_entities"),
]

# Map domains to base preset IDs
DOMAIN_TO_PRESET = {
    "saas": "saas",
    "blockchain": "saas",  # Use saas as base, customize with blockchain elements
    "ai": "saas",
    "healthcare": "healthcare",
    "fitness": "fitness",
    "ecommerce": "ecommerce",
    "restaurant": "restaurant",
    "education": "education",
    "news-media": "news-media",
    "pet-services": "pet-services",
    "real-estate": "real-estate",
    "finance": "saas",
}


class KeywordExtractor:
    """
    Extracts meaningful concepts from user descriptions using weighted scoring.

    Key features:
    - TF-IDF style weighting (rare, distinctive words score higher)
    - Stemming for better matching
    - Multi-signal combination (entities + actions + domain)
    - Pattern template matching
    """

    def __init__(self):
        # Pre-compute word frequency for IDF-like weighting
        self._word_frequency: Dict[str, int] = Counter()
        self._total_descriptions = 0

    def _stem(self, word: str) -> str:
        """Simple stemming - reduce word to base form"""
        return WORD_STEMS.get(word.lower(), word.lower())

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize and stem text, removing stop words"""
        words = re.findall(r'\b\w+\b', text.lower())
        return [self._stem(w) for w in words if w not in STOP_WORDS and len(w) > 2]

    def _calculate_word_weights(self, tokens: List[str]) -> Dict[str, float]:
        """
        Calculate TF-IDF style weights for tokens.

        Words that appear frequently in all descriptions (like "build", "app")
        get lower weights. Distinctive words get higher weights.
        """
        weights = {}

        # Term frequency in this description
        tf = Counter(tokens)
        max_tf = max(tf.values()) if tf else 1

        for token, count in tf.items():
            # Normalized term frequency
            norm_tf = 0.5 + 0.5 * (count / max_tf)

            # IDF-like boost for rare words (if we have history)
            if self._total_descriptions > 0:
                doc_freq = self._word_frequency.get(token, 0)
                idf = math.log(1 + self._total_descriptions / (1 + doc_freq))
            else:
                # Default: assume common words are frequent
                idf = 1.0 if token in STOP_WORDS else 2.0

            # Extra boost for very distinctive terms
            distinctiveness = 1.0
            for signals in INDUSTRY_SIGNALS.values():
                for word, weight in signals:
                    if word == token and weight > 0.85:
                        distinctiveness = 1.5
                        break

            weights[token] = norm_tf * idf * distinctiveness

        return weights

    def _extract_app_name(self, description: str) -> str:
        """Extract app/product name from description"""
        # Try quoted strings first
        quoted = re.search(r'"([^"]+)"|\'([^\']+)\'', description)
        if quoted:
            return quoted.group(1) or quoted.group(2)

        # Try capitalized phrases (likely proper nouns)
        caps = re.search(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\b', description)
        if caps and caps.group(1) not in ["Build", "Create", "Make", "I", "A", "An", "The"]:
            return caps.group(1)

        # Try pattern matching
        for pattern, pattern_type in DESCRIPTION_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match and pattern_type == "name_for_usecase":
                return match.group(1).strip()

        # Fallback: first significant words
        words = [w for w in description.split() if w[0].isupper() or len(w) > 4]
        return " ".join(words[:2]).title() if words else "My App"

    def _match_entities(self, tokens: List[str]) -> List[Tuple[str, float]]:
        """Match tokens to entity types with confidence scores"""
        matched = {}

        for token in tokens:
            if token in ENTITY_SIGNALS:
                entity_type, weight = ENTITY_SIGNALS[token]
                if entity_type not in matched or matched[entity_type] < weight:
                    matched[entity_type] = weight

        return sorted(matched.items(), key=lambda x: -x[1])

    def _match_actions(self, tokens: List[str]) -> List[Tuple[str, float]]:
        """Match tokens to action types with confidence scores"""
        matched = {}

        for token in tokens:
            if token in ACTION_SIGNALS:
                action_type, weight = ACTION_SIGNALS[token]
                if action_type not in matched or matched[action_type] < weight:
                    matched[action_type] = weight

        return sorted(matched.items(), key=lambda x: -x[1])

    def _score_industries(self, text: str, tokens: List[str], weights: Dict[str, float]) -> Dict[str, float]:
        """
        Score how well the description matches each industry.

        Uses weighted matching - distinctive terms contribute more.
        """
        scores = {}

        for industry, signals in INDUSTRY_SIGNALS.items():
            score = 0.0
            matches = 0

            for signal_word, signal_weight in signals:
                # Check for exact match or phrase match
                if signal_word in text or signal_word in tokens:
                    # Weight by signal importance and token weight
                    token_weight = weights.get(signal_word, 1.0)
                    score += signal_weight * token_weight
                    matches += 1

            # Normalize by number of signals (so industries with many signals don't auto-win)
            if matches > 0:
                # Bonus for multiple matches (indicates stronger signal)
                match_bonus = min(0.3, matches * 0.05)
                scores[industry] = (score / len(signals)) + match_bonus

        return scores

    def _match_patterns(self, description: str) -> List[Tuple[str, Dict[str, str]]]:
        """Match description against known patterns"""
        matches = []

        for pattern, pattern_type in DESCRIPTION_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                groups = match.groups()
                matches.append((pattern_type, {
                    "full": match.group(0),
                    "groups": groups,
                }))

        return matches

    def extract(self, description: str) -> ExtractedConcepts:
        """
        Extract concepts from a description with weighted scoring.

        Returns comprehensive concept extraction for preset generation.
        """
        text = description.lower()
        tokens = self._tokenize(text)

        # Update frequency tracking for future IDF calculations
        self._total_descriptions += 1
        self._word_frequency.update(set(tokens))

        concepts = ExtractedConcepts()

        # Calculate weighted keywords
        concepts.weighted_keywords = self._calculate_word_weights(tokens)

        # Extract app name
        concepts.app_name = self._extract_app_name(description)

        # Match entities and actions
        entity_matches = self._match_entities(tokens)
        concepts.entities = [e for e, _ in entity_matches]

        action_matches = self._match_actions(tokens)
        concepts.actions = [a for a, _ in action_matches]

        # Score industries
        concepts.industry_scores = self._score_industries(text, tokens, concepts.weighted_keywords)

        # Find best industry (and secondaries for composite matching)
        if concepts.industry_scores:
            sorted_industries = sorted(concepts.industry_scores.items(), key=lambda x: -x[1])
            concepts.best_industry = sorted_industries[0][0]
            concepts.best_score = sorted_industries[0][1]

            # Secondary industries (for composite presets) - those with >50% of best score
            threshold = concepts.best_score * 0.5
            concepts.secondary_industries = [
                ind for ind, score in sorted_industries[1:4]
                if score >= threshold
            ]
        else:
            concepts.best_industry = "universal"
            concepts.best_score = 0.0

        # Match patterns
        pattern_matches = self._match_patterns(description)
        concepts.matched_patterns = [p[0] for p in pattern_matches]

        # Generate domain signals summary
        for industry, score in concepts.industry_scores.items():
            if score > 0.1:  # Only include meaningful signals
                concepts.domain_signals[industry] = score

        # Generate tagline based on extractions
        if concepts.entities and concepts.actions:
            primary_entity = concepts.entities[0]
            primary_action = concepts.actions[0] if concepts.actions else "manage"

            # Make it sound good
            entity_plural = primary_entity + "s" if not primary_entity.endswith("s") else primary_entity
            concepts.tagline = f"Streamline your {entity_plural}"
        elif concepts.best_industry != "universal":
            concepts.tagline = f"Your {concepts.best_industry.replace('-', ' ')} solution"
        else:
            concepts.tagline = "Your all-in-one platform"

        logger.debug(
            f"Extracted: best_industry={concepts.best_industry} "
            f"(score={concepts.best_score:.2f}), "
            f"entities={concepts.entities[:3]}, "
            f"actions={concepts.actions[:3]}"
        )

        return concepts


class PresetComposer:
    """
    Composes new presets by intelligently combining elements from existing presets.

    Key improvements:
    - Composite presets: blend multiple industries when appropriate
    - Concept-driven: entities and actions drive structure, not just industry match
    - Adaptive: uses confidence scores to decide how much to customize
    """

    def __init__(self):
        pass

    def compose(
        self,
        concepts: ExtractedConcepts,
        domain_presets: Dict[str, Dict[str, Any]],
        arch_presets: Dict[str, Dict[str, Any]],
        mock_presets: Dict[str, Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Compose domain, architecture, and mock data presets from concepts.

        Uses weighted blending when multiple industries match.
        Returns: (domain_preset, architecture_preset, mock_data_preset)
        """
        # Map industry to preset key
        base_industry = DOMAIN_TO_PRESET.get(concepts.best_industry, "universal")

        # Get base presets
        base_domain = domain_presets.get(base_industry, domain_presets.get("universal", {}))

        # For composite matching, get secondary preset to blend
        secondary_domain = None
        if concepts.secondary_industries:
            secondary_key = DOMAIN_TO_PRESET.get(concepts.secondary_industries[0], None)
            if secondary_key and secondary_key != base_industry:
                secondary_domain = domain_presets.get(secondary_key)

        # Compose domain with potential blending
        domain = self._compose_domain(concepts, base_domain, secondary_domain)

        # Get architecture preset
        arch_key = self._find_arch_key(base_industry, arch_presets)
        base_arch = arch_presets.get(arch_key, arch_presets.get("universal-dashboard", {}))
        architecture = self._compose_architecture(concepts, base_arch, domain)

        # Get mock data preset
        mock_key = self._find_mock_key(base_industry, mock_presets)
        base_mock = mock_presets.get(mock_key, mock_presets.get("universal", {}))
        mock_data = self._compose_mock_data(concepts, base_mock, domain, architecture)

        return domain, architecture, mock_data

    def _find_arch_key(self, industry: str, presets: Dict[str, Any]) -> str:
        """Find best architecture preset key for industry"""
        direct = f"{industry}-dashboard"
        if direct in presets:
            return direct

        # Try variations
        for key in presets:
            if industry in key:
                return key

        return "universal-dashboard"

    def _find_mock_key(self, industry: str, presets: Dict[str, Any]) -> str:
        """Find best mock data preset key for industry"""
        # Try exact match
        if industry in presets:
            return industry

        # Try without suffixes
        base = industry.replace("-services", "").replace("-", "-")
        if base in presets:
            return base

        return "universal"

    def _compose_domain(
        self,
        concepts: ExtractedConcepts,
        base: Dict[str, Any],
        secondary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compose a domain preset with intelligent customization.

        If concepts.best_score is low, we customize more.
        If high, we trust the base preset more.
        """
        domain = self._deep_copy(base)

        # How much to customize vs trust base (inverse of match quality)
        customize_weight = 1.0 - min(0.8, concepts.best_score)

        # Always update display name
        if concepts.app_name:
            industry_name = domain.get("industry_display_name", "Application")
            # Keep industry context but add app name
            domain["industry_display_name"] = f"{concepts.app_name}"
            domain["app_name"] = concepts.app_name

        # Blend entities - add extracted ones that aren't already present
        base_entities = set(domain.get("key_entities", []))
        for entity in concepts.entities:
            if entity not in base_entities:
                domain.setdefault("key_entities", []).insert(0, entity)

        # Blend from secondary preset if available
        if secondary and customize_weight > 0.3:
            # Borrow some elements from secondary
            secondary_sections = secondary.get("suggested_sections", [])
            if secondary_sections:
                current_sections = domain.get("suggested_sections", [])
                # Add 1-2 sections from secondary
                for section in secondary_sections[:2]:
                    if section not in current_sections:
                        current_sections.append(section)
                domain["suggested_sections"] = current_sections

        # Build terminology from entities
        terminology = domain.get("terminology", {}).copy()
        entity_term_map = {
            "user": ("user", "user"),
            "customer": ("customer", "customer"),
            "member": ("user", "member"),
            "patient": ("user", "patient"),
            "student": ("user", "student"),
            "client": ("customer", "client"),
            "order": ("order", "order"),
            "booking": ("order", "booking"),
            "reservation": ("order", "reservation"),
            "appointment": ("order", "appointment"),
            "product": ("item", "product"),
            "listing": ("item", "listing"),
            "article": ("item", "article"),
            "proposal": ("item", "proposal"),
        }
        for entity in concepts.entities:
            if entity in entity_term_map:
                generic, specific = entity_term_map[entity]
                terminology[generic] = specific
        domain["terminology"] = terminology

        # Update suggested sections based on entities and actions
        sections = domain.get("suggested_sections", [])
        section_additions = []

        # Entity-driven sections
        entity_sections = {
            "proposal": "Governance & Proposals",
            "vote": "Voting Dashboard",
            "order": "Orders & Transactions",
            "booking": "Bookings & Reservations",
            "appointment": "Appointment Schedule",
            "product": "Product Catalog",
            "article": "Content Library",
            "message": "Messages & Notifications",
            "invoice": "Billing & Invoices",
        }
        for entity in concepts.entities:
            if entity in entity_sections:
                section = entity_sections[entity]
                if section not in sections:
                    section_additions.append(section)

        # Action-driven sections
        action_sections = {
            "track": "Analytics & Tracking",
            "vote": "Voting & Governance",
            "pay": "Payments & Billing",
            "analyze": "Insights & Reports",
            "collaborate": "Team Collaboration",
            "schedule": "Calendar & Scheduling",
        }
        for action in concepts.actions:
            if action in action_sections:
                section = action_sections[action]
                if section not in sections and section not in section_additions:
                    section_additions.append(section)

        domain["suggested_sections"] = section_additions + sections[:4]

        # Update metrics based on entities and actions
        metrics = domain.get("metrics", [])
        metric_additions = []

        # Entity-driven metrics
        entity_metrics = {
            "proposal": ["active_proposals", "participation_rate"],
            "vote": ["votes_cast", "voter_turnout"],
            "order": ["total_orders", "revenue", "avg_order_value"],
            "booking": ["bookings_today", "occupancy_rate"],
            "user": ["active_users", "user_growth"],
            "product": ["total_products", "inventory_value"],
        }
        for entity in concepts.entities:
            if entity in entity_metrics:
                for metric in entity_metrics[entity]:
                    if metric not in metrics and metric not in metric_additions:
                        metric_additions.append(metric)

        # Action-driven metrics
        action_metrics = {
            "track": ["conversion_rate", "engagement"],
            "vote": ["participation_rate", "quorum_reached"],
            "pay": ["revenue", "transaction_volume"],
        }
        for action in concepts.actions:
            if action in action_metrics:
                for metric in action_metrics[action]:
                    if metric not in metrics and metric not in metric_additions:
                        metric_additions.append(metric)

        domain["metrics"] = metric_additions[:3] + metrics[:4]

        return domain

    def _compose_architecture(
        self,
        concepts: ExtractedConcepts,
        base: Dict[str, Any],
        domain: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compose architecture preset driven by extracted concepts.

        Pages and structure adapt to what entities/actions were detected.
        """
        arch = self._deep_copy(base)

        # Update app name
        arch["app_name"] = concepts.app_name or domain.get("app_name", "Dashboard")
        arch["tagline"] = concepts.tagline

        # Get existing pages as starting point, or build from scratch
        if concepts.best_score > 0.6 and "pages" in base:
            # High confidence match - use base pages but customize labels
            pages = self._customize_existing_pages(base.get("pages", []), domain)
        else:
            # Build pages from concepts
            pages = self._build_pages_from_concepts(concepts, domain)

        arch["pages"] = pages
        arch["sidebar_items"] = [p["title"] for p in pages]

        # Generate stat cards from domain metrics
        metrics = domain.get("metrics", [])[:4]
        if not metrics:
            metrics = ["total_items", "active_users", "growth_rate", "satisfaction"]

        colors = ["blue", "green", "purple", "amber"]
        icons = self._select_icons_for_metrics(metrics, concepts)

        arch["stat_cards"] = [
            {
                "title": self._format_metric_title(m),
                "data_key": m,
                "icon": icons[i] if i < len(icons) else "activity",
                "color": colors[i % len(colors)]
            }
            for i, m in enumerate(metrics)
        ]

        # Primary action based on primary entity/action
        arch["primary_action"] = self._determine_primary_action(concepts, domain)
        arch["primary_action_icon"] = "plus"

        return arch

    def _customize_existing_pages(
        self,
        pages: List[Dict],
        domain: Dict[str, Any]
    ) -> List[Dict]:
        """Customize labels in existing pages using domain terminology"""
        customized = []
        terminology = domain.get("terminology", {})

        for page in pages:
            new_page = self._deep_copy(page)

            # Update title using terminology
            title = new_page.get("title", "")
            for generic, specific in terminology.items():
                if generic.lower() in title.lower():
                    title = title.replace(generic.title(), specific.title())
                    title = title.replace(generic, specific)
            new_page["title"] = title

            # Update section titles
            for section in new_page.get("sections", []):
                section_title = section.get("title", "")
                for generic, specific in terminology.items():
                    if generic.lower() in section_title.lower():
                        section_title = section_title.replace(generic.title(), specific.title())
                section["title"] = section_title

            customized.append(new_page)

        return customized

    def _build_pages_from_concepts(
        self,
        concepts: ExtractedConcepts,
        domain: Dict[str, Any]
    ) -> List[Dict]:
        """Build page structure from extracted concepts"""
        pages = []

        # Always have a dashboard home
        pages.append({
            "path": "/",
            "title": "Dashboard",
            "icon": "layout-dashboard",
            "is_default": True,
            "sections": [
                {"id": "stats", "title": "Overview", "component_type": "stats", "data_source": "stats", "colspan": 3},
                {"id": "main", "title": "Recent Activity", "component_type": "cards", "data_source": "items", "colspan": 2},
                {"id": "activity", "title": "Activity Feed", "component_type": "list", "data_source": "recent_activity", "colspan": 1}
            ]
        })

        # Entity-driven pages
        entity_pages = {
            "proposal": {"path": "/governance", "title": "Governance", "icon": "vote", "data": "proposals"},
            "vote": {"path": "/voting", "title": "Voting", "icon": "check-square", "data": "votes"},
            "order": {"path": "/orders", "title": "Orders", "icon": "shopping-cart", "data": "orders"},
            "booking": {"path": "/bookings", "title": "Bookings", "icon": "calendar", "data": "bookings"},
            "appointment": {"path": "/schedule", "title": "Schedule", "icon": "calendar", "data": "appointments"},
            "product": {"path": "/products", "title": "Products", "icon": "package", "data": "products"},
            "article": {"path": "/content", "title": "Content", "icon": "file-text", "data": "articles"},
            "user": {"path": "/users", "title": "Users", "icon": "users", "data": "users"},
            "customer": {"path": "/customers", "title": "Customers", "icon": "users", "data": "customers"},
            "member": {"path": "/members", "title": "Members", "icon": "users", "data": "members"},
        }

        added_paths = {"/"}
        for entity in concepts.entities[:4]:  # Max 4 entity pages
            if entity in entity_pages:
                page_config = entity_pages[entity]
                if page_config["path"] not in added_paths:
                    pages.append({
                        "path": page_config["path"],
                        "title": page_config["title"],
                        "icon": page_config["icon"],
                        "sections": [
                            {"id": f"{entity}-table", "title": f"All {page_config['title']}", "component_type": "table", "data_source": page_config["data"], "colspan": 3}
                        ]
                    })
                    added_paths.add(page_config["path"])

        # Always have analytics
        if "/analytics" not in added_paths:
            pages.append({
                "path": "/analytics",
                "title": "Analytics",
                "icon": "bar-chart-3",
                "sections": [
                    {"id": "trends", "title": "Trends", "component_type": "chart", "data_source": "activity_data", "colspan": 2},
                    {"id": "breakdown", "title": "Breakdown", "component_type": "chart", "data_source": "categories", "colspan": 1}
                ]
            })

        return pages

    def _select_icons_for_metrics(
        self,
        metrics: List[str],
        concepts: ExtractedConcepts
    ) -> List[str]:
        """Select appropriate icons for metrics"""
        icon_map = {
            "revenue": "dollar-sign",
            "orders": "shopping-cart",
            "users": "users",
            "active_users": "users",
            "proposals": "file-text",
            "active_proposals": "file-text",
            "votes": "check-square",
            "votes_cast": "check-square",
            "participation": "users",
            "bookings": "calendar",
            "appointments": "calendar",
            "products": "package",
            "growth": "trending-up",
            "conversion": "trending-up",
            "satisfaction": "star",
            "engagement": "activity",
        }

        icons = []
        default_icons = ["activity", "list", "trending-up", "star"]

        for i, metric in enumerate(metrics):
            matched = False
            for key, icon in icon_map.items():
                if key in metric:
                    icons.append(icon)
                    matched = True
                    break
            if not matched:
                icons.append(default_icons[i % len(default_icons)])

        return icons

    def _format_metric_title(self, metric: str) -> str:
        """Format metric key into display title"""
        # Replace underscores, capitalize words
        title = metric.replace("_", " ").title()
        # Shorten common patterns
        title = title.replace("Active ", "").replace("Total ", "")
        return title

    def _determine_primary_action(
        self,
        concepts: ExtractedConcepts,
        domain: Dict[str, Any]
    ) -> str:
        """Determine the primary action button text"""
        entity_actions = {
            "proposal": "New Proposal",
            "vote": "Cast Vote",
            "order": "New Order",
            "booking": "New Booking",
            "appointment": "New Appointment",
            "product": "Add Product",
            "article": "Create Article",
            "user": "Add User",
            "member": "Add Member",
            "customer": "Add Customer",
            "invoice": "Create Invoice",
        }

        for entity in concepts.entities:
            if entity in entity_actions:
                return entity_actions[entity]

        # Fall back to domain terminology
        terminology = domain.get("terminology", {})
        item_term = terminology.get("item", "Item")
        return f"New {item_term.title()}"

    def _compose_mock_data(
        self,
        concepts: ExtractedConcepts,
        base: Dict[str, Any],
        domain: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compose mock data that matches the architecture's data sources.

        Ensures every data_source referenced in architecture has data.
        """
        mock = self._deep_copy(base)

        # Gather all data sources needed
        needed_sources = {"stats", "recent_activity"}
        for page in architecture.get("pages", []):
            for section in page.get("sections", []):
                source = section.get("data_source")
                if source:
                    needed_sources.add(source)

        # Ensure stats has all needed metrics
        stats = mock.get("stats", {})
        for stat_card in architecture.get("stat_cards", []):
            key = stat_card.get("data_key")
            if key and key not in stats:
                stats[key] = self._generate_stat_value(key)
                stats[f"change_{key}"] = f"+{(hash(key) % 15) + 5}%"
        mock["stats"] = stats

        # Add entity-specific data if needed
        entity_data = {
            "proposals": [
                {"id": "prop-001", "title": "Proposal Alpha", "status": "active", "votes_for": 234, "votes_against": 45, "deadline": "3 days", "author": "Alice"},
                {"id": "prop-002", "title": "Proposal Beta", "status": "active", "votes_for": 156, "votes_against": 89, "deadline": "5 days", "author": "Bob"},
                {"id": "prop-003", "title": "Proposal Gamma", "status": "passed", "votes_for": 412, "votes_against": 34, "deadline": "Ended", "author": "Carol"},
            ],
            "votes": [
                {"id": "vote-001", "proposal": "Proposal Alpha", "vote": "For", "voter": "You", "time": "2 hours ago"},
                {"id": "vote-002", "proposal": "Proposal Beta", "vote": "Against", "voter": "You", "time": "1 day ago"},
            ],
            "orders": [
                {"id": "ord-001", "customer": "Alex Johnson", "items": 3, "total": "$127", "status": "processing", "time": "10 min ago"},
                {"id": "ord-002", "customer": "Sam Chen", "items": 1, "total": "$49", "status": "shipped", "time": "2 hours ago"},
                {"id": "ord-003", "customer": "Jordan Smith", "items": 5, "total": "$312", "status": "delivered", "time": "1 day ago"},
            ],
            "bookings": [
                {"id": "book-001", "customer": "Alex J.", "service": "Consultation", "time": "2:00 PM", "status": "confirmed"},
                {"id": "book-002", "customer": "Sam C.", "service": "Follow-up", "time": "3:30 PM", "status": "pending"},
                {"id": "book-003", "customer": "Jordan S.", "service": "Initial Visit", "time": "Tomorrow 10 AM", "status": "confirmed"},
            ],
            "appointments": [
                {"id": "apt-001", "client": "Alex Johnson", "type": "Meeting", "time": "2:00 PM", "duration": "1 hr", "status": "upcoming"},
                {"id": "apt-002", "client": "Sam Chen", "type": "Call", "time": "3:30 PM", "duration": "30 min", "status": "confirmed"},
            ],
            "products": [
                {"id": "prod-001", "name": "Product Alpha", "price": "$99", "stock": 145, "category": "Main"},
                {"id": "prod-002", "name": "Product Beta", "price": "$149", "stock": 89, "category": "Premium"},
                {"id": "prod-003", "name": "Product Gamma", "price": "$49", "stock": 234, "category": "Basic"},
            ],
            "customers": [
                {"id": "cust-001", "name": "Alex Johnson", "email": "alex@example.com", "orders": 12, "total_spent": "$1,247"},
                {"id": "cust-002", "name": "Sam Chen", "email": "sam@example.com", "orders": 8, "total_spent": "$892"},
                {"id": "cust-003", "name": "Jordan Smith", "email": "jordan@example.com", "orders": 24, "total_spent": "$2,456"},
            ],
            "members": [
                {"id": "mem-001", "name": "Alex Johnson", "role": "Admin", "joined": "Jan 2024", "status": "active"},
                {"id": "mem-002", "name": "Sam Chen", "role": "Member", "joined": "Feb 2024", "status": "active"},
                {"id": "mem-003", "name": "Jordan Smith", "role": "Member", "joined": "Mar 2024", "status": "active"},
            ],
        }

        for source in needed_sources:
            if source not in mock:
                # Try to find matching entity data
                if source in entity_data:
                    mock[source] = entity_data[source]
                elif source == "activity_data":
                    mock[source] = [
                        {"month": "Jan", "value": 4200},
                        {"month": "Feb", "value": 5100},
                        {"month": "Mar", "value": 4800},
                        {"month": "Apr", "value": 6200},
                        {"month": "May", "value": 7100},
                        {"month": "Jun", "value": 8400},
                    ]
                elif source == "categories":
                    mock[source] = [
                        {"name": "Category A", "value": 45},
                        {"name": "Category B", "value": 30},
                        {"name": "Category C", "value": 25},
                    ]

        # Ensure recent_activity exists
        if "recent_activity" not in mock:
            mock["recent_activity"] = [
                {"id": "act-001", "user": "Alex J.", "action": "created", "target": "new item", "time": "5 min ago"},
                {"id": "act-002", "user": "Sam C.", "action": "updated", "target": "settings", "time": "15 min ago"},
                {"id": "act-003", "user": "Jordan S.", "action": "completed", "target": "task", "time": "1 hour ago"},
            ]

        return mock

    def _generate_stat_value(self, key: str) -> Any:
        """Generate a realistic stat value based on the key name"""
        key_lower = key.lower()

        if "rate" in key_lower or "percent" in key_lower:
            return f"{78 + hash(key) % 20}%"
        elif "revenue" in key_lower or "spent" in key_lower or "value" in key_lower:
            return f"${(hash(key) % 50 + 10) * 100:,}"
        elif "count" in key_lower or "total" in key_lower:
            return 100 + (hash(key) % 900)
        elif "time" in key_lower:
            return f"{(hash(key) % 30) + 5} min"
        else:
            return hash(key) % 100 + 50

    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy a dict/list structure"""
        import copy
        return copy.deepcopy(obj)


class PresetCache:
    """
    Caches successful presets for future reuse with learning capabilities.

    Features:
    - Weighted keyword similarity (not just Jaccard)
    - Success/failure tracking
    - Confidence-based retrieval
    - Automatic pruning of low-performing presets
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path(__file__).parent.parent.parent / "data" / "preset_cache"
        self.cache: Dict[str, CachedPreset] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cached presets from disk"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self.cache_dir / "presets.json"
            if cache_file.exists():
                data = json.loads(cache_file.read_text())
                for key, value in data.items():
                    # Handle both old and new cache formats
                    if "weighted_keywords" not in value:
                        value["weighted_keywords"] = {k: 1.0 for k in value.get("keywords", [])}
                    if "success_count" not in value:
                        value["success_count"] = value.get("use_count", 1)
                    if "failure_count" not in value:
                        value["failure_count"] = 0
                    if "user_feedback_score" not in value:
                        value["user_feedback_score"] = 0.0
                    self.cache[key] = CachedPreset(**value)
                logger.info(f"Loaded {len(self.cache)} cached presets")
        except Exception as e:
            logger.warning(f"Failed to load preset cache: {e}")

    def _save_cache(self) -> None:
        """Save cache to disk"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self.cache_dir / "presets.json"
            data = {k: asdict(v) for k, v in self.cache.items()}
            cache_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save preset cache: {e}")

    def _hash_description(self, description: str) -> str:
        """Create a hash for the description"""
        normalized = " ".join(description.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    def _weighted_similarity(
        self,
        query_weights: Dict[str, float],
        cached_weights: Dict[str, float]
    ) -> float:
        """
        Calculate weighted cosine similarity between keyword sets.

        Better than Jaccard because it considers keyword importance.
        """
        if not query_weights or not cached_weights:
            return 0.0

        # Get all unique keywords
        all_keywords = set(query_weights.keys()) | set(cached_weights.keys())

        # Calculate dot product and magnitudes
        dot_product = 0.0
        query_magnitude = 0.0
        cached_magnitude = 0.0

        for kw in all_keywords:
            q_weight = query_weights.get(kw, 0.0)
            c_weight = cached_weights.get(kw, 0.0)

            dot_product += q_weight * c_weight
            query_magnitude += q_weight ** 2
            cached_magnitude += c_weight ** 2

        query_magnitude = math.sqrt(query_magnitude)
        cached_magnitude = math.sqrt(cached_magnitude)

        if query_magnitude == 0 or cached_magnitude == 0:
            return 0.0

        return dot_product / (query_magnitude * cached_magnitude)

    def get(self, description: str) -> Optional[Dict[str, Any]]:
        """Get a cached preset if available (exact match)"""
        hash_key = self._hash_description(description)
        if hash_key in self.cache:
            cached = self.cache[hash_key]
            cached.use_count += 1
            self._save_cache()
            logger.info(f"Cache hit (exact) for preset (used {cached.use_count} times, confidence={cached.confidence_score:.2f})")
            return cached.preset
        return None

    def find_similar(
        self,
        weighted_keywords: Dict[str, float],
        threshold: float = 0.4,
        min_confidence: float = 0.5
    ) -> Optional[Tuple[Dict[str, Any], float]]:
        """
        Find a similar preset based on weighted keyword similarity.

        Returns: (preset, similarity_score) or None
        """
        best_match = None
        best_score = 0.0
        best_confidence = 0.0

        for cached in self.cache.values():
            # Skip low-confidence presets
            if cached.confidence_score < min_confidence:
                continue

            # Calculate weighted similarity
            similarity = self._weighted_similarity(weighted_keywords, cached.weighted_keywords)

            # Combine similarity with confidence
            combined_score = similarity * (0.7 + 0.3 * cached.confidence_score)

            if combined_score > best_score and similarity >= threshold:
                best_score = combined_score
                best_match = cached.preset
                best_confidence = cached.confidence_score

        if best_match:
            logger.info(f"Found similar preset (similarity={best_score:.2f}, confidence={best_confidence:.2f})")
            return best_match, best_score

        return None

    def store(
        self,
        description: str,
        keywords: List[str],
        weighted_keywords: Dict[str, float],
        preset: Dict[str, Any]
    ) -> str:
        """Store a preset in the cache. Returns the cache key."""
        hash_key = self._hash_description(description)
        self.cache[hash_key] = CachedPreset(
            description_hash=hash_key,
            keywords=keywords,
            weighted_keywords=weighted_keywords,
            preset=preset,
            created_at=datetime.utcnow().isoformat(),
        )
        self._save_cache()
        logger.info(f"Cached new preset: {hash_key}")
        return hash_key

    def record_success(self, description: str) -> None:
        """Record that a preset was used successfully"""
        hash_key = self._hash_description(description)
        if hash_key in self.cache:
            self.cache[hash_key].success_count += 1
            self._save_cache()

    def record_failure(self, description: str) -> None:
        """Record that a preset failed"""
        hash_key = self._hash_description(description)
        if hash_key in self.cache:
            self.cache[hash_key].failure_count += 1
            self._save_cache()

    def record_feedback(self, description: str, score: float) -> None:
        """Record user feedback (-1 to 1)"""
        hash_key = self._hash_description(description)
        if hash_key in self.cache:
            # Weighted average with previous feedback
            old_score = self.cache[hash_key].user_feedback_score
            new_score = (old_score * 0.7) + (score * 0.3)
            self.cache[hash_key].user_feedback_score = max(-1, min(1, new_score))
            self._save_cache()

    def get_most_similar(
        self,
        description: str,
        min_similarity: float = 0.6
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most similar cached entry with full details for fallback.

        Returns a dict with:
        - domain, architecture, mock_data from the cached preset
        - similarity score
        - success_count for reliability checking

        Used by the fallback cascade to reuse similar successful generations.
        """
        # Tokenize the description to get weighted keywords
        words = description.lower().split()
        # Simple weighting for quick lookup
        query_weights = {w: 1.0 for w in words if len(w) > 2}

        best_match = None
        best_score = 0.0

        for cached in self.cache.values():
            # Only consider presets that have succeeded at least once
            if cached.success_count < 1:
                continue

            # Calculate similarity
            similarity = self._weighted_similarity(query_weights, cached.weighted_keywords)

            # Weight by confidence (success rate)
            combined = similarity * (0.6 + 0.4 * cached.confidence_score)

            if combined > best_score and similarity >= min_similarity:
                best_score = combined
                best_match = cached

        if best_match:
            preset = best_match.preset
            return {
                "domain": preset.get("domain", {}),
                "architecture": preset.get("architecture", {}),
                "mock_data": preset.get("mock_data", {}),
                "similarity": best_score,
                "success_count": best_match.success_count,
                "confidence": best_match.confidence_score,
            }

        return None

    def prune_low_performers(self, min_confidence: float = 0.3) -> int:
        """Remove presets with consistently poor performance"""
        to_remove = []
        for key, cached in self.cache.items():
            # Only prune if we have enough data
            if cached.use_count >= 5 and cached.confidence_score < min_confidence:
                to_remove.append(key)

        for key in to_remove:
            del self.cache[key]

        if to_remove:
            self._save_cache()
            logger.info(f"Pruned {len(to_remove)} low-performing presets")

        return len(to_remove)


class SmartPresetSystem:
    """
    Main entry point for smart preset generation.

    This system:
    1. Extracts concepts with weighted keyword scoring
    2. Checks cache for exact or similar matches
    3. Composes new presets when needed
    4. Caches results for future learning
    5. Tracks success/failure for continuous improvement

    The more it's used, the smarter it gets.
    """

    def __init__(self):
        self.extractor = KeywordExtractor()
        self.composer = PresetComposer()
        self.cache = PresetCache()

        # Lazy-load base presets
        self._domain_presets: Optional[Dict] = None
        self._arch_presets: Optional[Dict] = None
        self._mock_presets: Optional[Dict] = None

    def _load_base_presets(self) -> None:
        """Load base presets from existing preset files"""
        if self._domain_presets is not None:
            return

        try:
            from .domain_analyst import INDUSTRY_PRESETS
            from .architect import ARCHITECTURE_PRESETS
            from .content_generator import MOCK_DATA_PRESETS

            self._domain_presets = INDUSTRY_PRESETS
            self._arch_presets = ARCHITECTURE_PRESETS
            self._mock_presets = MOCK_DATA_PRESETS
            logger.info(f"Loaded base presets: {len(self._domain_presets)} domains, {len(self._arch_presets)} architectures")
        except ImportError as e:
            logger.warning(f"Failed to load base presets: {e}")
            self._domain_presets = {}
            self._arch_presets = {}
            self._mock_presets = {}

    def get_preset(
        self,
        description: str,
        use_cache: bool = True
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Get or generate presets for a description.

        Pipeline:
        1. Check for exact cache match
        2. Extract concepts from description
        3. Check for similar cached preset
        4. Compose new preset from concepts
        5. Cache for future use

        Returns: (domain_preset, architecture_preset, mock_data_preset)
        """
        self._load_base_presets()

        # 1. Check cache for exact match
        if use_cache:
            cached = self.cache.get(description)
            if cached:
                return (
                    cached.get("domain", {}),
                    cached.get("architecture", {}),
                    cached.get("mock_data", {})
                )

        # 2. Extract concepts
        concepts = self.extractor.extract(description)
        logger.info(
            f"Smart preset extraction: "
            f"industry={concepts.best_industry} (score={concepts.best_score:.2f}), "
            f"entities={concepts.entities[:3]}, "
            f"actions={concepts.actions[:3]}, "
            f"secondary={concepts.secondary_industries}"
        )

        # 3. Check for similar cached preset
        if use_cache and concepts.weighted_keywords:
            similar_result = self.cache.find_similar(concepts.weighted_keywords)
            if similar_result:
                similar_preset, similarity = similar_result
                logger.info(f"Using similar cached preset (similarity={similarity:.2f})")
                return (
                    similar_preset.get("domain", {}),
                    similar_preset.get("architecture", {}),
                    similar_preset.get("mock_data", {})
                )

        # 4. Compose new presets
        domain, architecture, mock_data = self.composer.compose(
            concepts,
            self._domain_presets,
            self._arch_presets,
            self._mock_presets,
        )

        # 5. Cache the result
        if use_cache:
            self.cache.store(
                description=description,
                keywords=concepts.top_keywords,
                weighted_keywords=concepts.weighted_keywords,
                preset={"domain": domain, "architecture": architecture, "mock_data": mock_data}
            )

        return domain, architecture, mock_data

    def get_concepts(self, description: str) -> ExtractedConcepts:
        """
        Get extracted concepts without generating presets.

        Useful for debugging or inspection.
        """
        return self.extractor.extract(description)

    def record_success(self, description: str) -> None:
        """Record that the preset worked well"""
        self.cache.record_success(description)

    def record_failure(self, description: str) -> None:
        """Record that the preset failed or produced poor results"""
        self.cache.record_failure(description)

    def record_feedback(self, description: str, positive: bool) -> None:
        """Record user feedback on a preset"""
        score = 1.0 if positive else -1.0
        self.cache.record_feedback(description, score)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache"""
        if not self.cache.cache:
            return {"total": 0, "message": "Cache is empty"}

        total = len(self.cache.cache)
        avg_confidence = sum(c.confidence_score for c in self.cache.cache.values()) / total
        total_uses = sum(c.use_count for c in self.cache.cache.values())

        # Find top performers
        sorted_by_confidence = sorted(
            self.cache.cache.values(),
            key=lambda c: c.confidence_score,
            reverse=True
        )
        top_presets = [
            {
                "hash": c.description_hash,
                "confidence": round(c.confidence_score, 2),
                "uses": c.use_count,
                "keywords": c.keywords[:5]
            }
            for c in sorted_by_confidence[:5]
        ]

        return {
            "total": total,
            "total_uses": total_uses,
            "avg_confidence": round(avg_confidence, 2),
            "top_presets": top_presets
        }


# Singleton instance
_smart_preset_system: Optional[SmartPresetSystem] = None


def get_smart_preset_system() -> SmartPresetSystem:
    """Get the singleton smart preset system"""
    global _smart_preset_system
    if _smart_preset_system is None:
        _smart_preset_system = SmartPresetSystem()
    return _smart_preset_system


def get_smart_preset(description: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Convenience function to get smart presets.

    Returns: (domain_preset, architecture_preset, mock_data_preset)
    """
    return get_smart_preset_system().get_preset(description)


def extract_concepts(description: str) -> ExtractedConcepts:
    """
    Convenience function to extract concepts from a description.

    Returns: ExtractedConcepts with weighted keywords, entities, actions, etc.
    """
    return get_smart_preset_system().get_concepts(description)
