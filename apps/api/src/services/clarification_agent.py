"""
Clarification Agent

Generates smart clarifying questions before prototype generation to understand
the user's unique business needs. Questions are targeted based on:

1. Low confidence areas in domain detection
2. Missing critical information (target market, pricing, services)
3. Ambiguous domain (could be B2B or B2C?)
4. Entity-specific questions based on detected entities

The goal is to transform a vague description into a rich DomainExpertise profile.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QuestionType(str, Enum):
    """Types of clarification questions"""
    DOMAIN_CONFIRMATION = "domain_confirmation"  # Confirm detected industry
    TARGET_MARKET = "target_market"  # Who are the customers?
    SERVICE_MODEL = "service_model"  # What services/products?
    PRICING_MODEL = "pricing_model"  # How do they charge?
    UNIQUE_VALUE = "unique_value"  # What makes them different?
    SCALE = "scale"  # Expected volume/size
    FEATURES = "features"  # Specific features needed
    ENTITY_SPECIFIC = "entity_specific"  # Based on detected entities


@dataclass
class ClarificationQuestion:
    """A single clarification question to ask the user"""
    id: str
    question: str
    question_type: QuestionType
    options: List[str] = field(default_factory=list)  # For multiple choice
    allow_custom: bool = True  # Allow free text answer
    priority: int = 1  # Higher = more important (1-5)
    context: str = ""  # Why this question matters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "type": self.question_type.value,
            "options": self.options,
            "allow_custom": self.allow_custom,
            "priority": self.priority,
            "context": self.context,
        }


@dataclass
class ClarificationResult:
    """Result of the clarification process"""
    questions: List[ClarificationQuestion]
    enriched_description: str = ""
    confidence_before: float = 0.0
    detected_industry: str = ""
    missing_info: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "questions": [q.to_dict() for q in self.questions],
            "enriched_description": self.enriched_description,
            "confidence_before": self.confidence_before,
            "detected_industry": self.detected_industry,
            "missing_info": self.missing_info,
        }


# Question templates by type
QUESTION_TEMPLATES = {
    QuestionType.DOMAIN_CONFIRMATION: {
        "template": "I detected this might be a {industry} business. Is that correct?",
        "options_generator": "secondary_industries",
        "priority": 5,
        "context": "Getting the right industry helps us use appropriate terminology and features",
    },
    QuestionType.TARGET_MARKET: {
        "template": "Who are your primary customers?",
        "default_options": [
            "Individual consumers (B2C)",
            "Small businesses (SMB)",
            "Enterprise companies (B2B)",
            "Both businesses and consumers",
        ],
        "priority": 4,
        "context": "Understanding your target market helps us design the right user experience",
    },
    QuestionType.SERVICE_MODEL: {
        "template": "What type of {entity_plural} do you offer?",
        "default_template": "What services or products do you offer?",
        "priority": 4,
        "context": "This helps us create realistic mock data and appropriate features",
    },
    QuestionType.PRICING_MODEL: {
        "template": "How do you charge customers?",
        "default_options": [
            "Per item/service",
            "Subscription/recurring",
            "Packages/bundles",
            "Custom quotes",
            "Free with premium options",
        ],
        "priority": 3,
        "context": "This affects the checkout flow and pricing displays",
    },
    QuestionType.UNIQUE_VALUE: {
        "template": "What makes your {industry_name} business different from competitors?",
        "default_template": "What makes your business unique?",
        "priority": 2,
        "context": "We'll highlight these differentiators in your dashboard",
    },
    QuestionType.SCALE: {
        "template": "What's your expected {metric} volume?",
        "default_template": "What scale are you expecting?",
        "default_options": [
            "Small (1-50 per day)",
            "Medium (50-500 per day)",
            "Large (500-5000 per day)",
            "Enterprise (5000+ per day)",
        ],
        "priority": 2,
        "context": "This helps us design appropriate data views and metrics",
    },
}

# Industry-specific question templates
INDUSTRY_QUESTIONS = {
    "pet-services": [
        ClarificationQuestion(
            id="pet_services",
            question="What pet services do you provide?",
            question_type=QuestionType.SERVICE_MODEL,
            options=["Grooming", "Boarding/Daycare", "Walking", "Veterinary care", "Training", "Pet supplies"],
            priority=5,
            context="Each service type has unique scheduling and tracking needs",
        ),
        ClarificationQuestion(
            id="pet_types",
            question="Which animals do you serve?",
            question_type=QuestionType.ENTITY_SPECIFIC,
            options=["Dogs only", "Cats only", "Dogs and cats", "All pets (including exotic)"],
            priority=4,
        ),
    ],
    "restaurant": [
        ClarificationQuestion(
            id="restaurant_type",
            question="What type of restaurant are you running?",
            question_type=QuestionType.SERVICE_MODEL,
            options=["Dine-in restaurant", "Fast casual", "Food truck", "Ghost kitchen/Delivery only", "Cafe/Coffee shop"],
            priority=5,
        ),
        ClarificationQuestion(
            id="ordering_method",
            question="How do customers typically order?",
            question_type=QuestionType.ENTITY_SPECIFIC,
            options=["In-person ordering", "Online ordering", "Phone orders", "All of the above"],
            priority=4,
        ),
    ],
    "healthcare": [
        ClarificationQuestion(
            id="healthcare_type",
            question="What type of healthcare practice is this?",
            question_type=QuestionType.SERVICE_MODEL,
            options=["General practice", "Specialty clinic", "Mental health", "Dental", "Physical therapy", "Telehealth"],
            priority=5,
        ),
        ClarificationQuestion(
            id="patient_type",
            question="Who are your patients?",
            question_type=QuestionType.TARGET_MARKET,
            options=["Adults", "Pediatric", "Geriatric", "All ages"],
            priority=4,
        ),
    ],
    "fitness": [
        ClarificationQuestion(
            id="fitness_type",
            question="What type of fitness business is this?",
            question_type=QuestionType.SERVICE_MODEL,
            options=["Gym/Fitness center", "Yoga/Pilates studio", "Personal training", "Online coaching", "CrossFit box"],
            priority=5,
        ),
        ClarificationQuestion(
            id="membership_model",
            question="How do members access your services?",
            question_type=QuestionType.PRICING_MODEL,
            options=["Monthly membership", "Class packs", "Drop-in rates", "Annual contracts", "Hybrid model"],
            priority=4,
        ),
    ],
    "ecommerce": [
        ClarificationQuestion(
            id="product_type",
            question="What type of products do you sell?",
            question_type=QuestionType.SERVICE_MODEL,
            options=["Physical products", "Digital products", "Services", "Mix of physical and digital"],
            priority=5,
        ),
        ClarificationQuestion(
            id="fulfillment",
            question="How do you handle fulfillment?",
            question_type=QuestionType.ENTITY_SPECIFIC,
            options=["Self-fulfilled", "Dropshipping", "Third-party logistics (3PL)", "Digital delivery"],
            priority=3,
        ),
    ],
    "saas": [
        ClarificationQuestion(
            id="saas_model",
            question="What type of SaaS product is this?",
            question_type=QuestionType.SERVICE_MODEL,
            options=["B2B tool", "B2C application", "Developer tool/API", "Marketplace", "Platform"],
            priority=5,
        ),
        ClarificationQuestion(
            id="pricing_tiers",
            question="What's your pricing model?",
            question_type=QuestionType.PRICING_MODEL,
            options=["Freemium", "Flat-rate subscription", "Usage-based", "Tiered plans", "Enterprise custom"],
            priority=4,
        ),
    ],
    "education": [
        ClarificationQuestion(
            id="education_type",
            question="What type of educational content do you provide?",
            question_type=QuestionType.SERVICE_MODEL,
            options=["Online courses", "Live classes", "Tutoring", "Corporate training", "K-12 curriculum"],
            priority=5,
        ),
        ClarificationQuestion(
            id="learner_type",
            question="Who are your learners?",
            question_type=QuestionType.TARGET_MARKET,
            options=["Students (K-12)", "College students", "Working professionals", "Enterprise teams", "Hobbyists"],
            priority=4,
        ),
    ],
    "news-media": [
        ClarificationQuestion(
            id="content_focus",
            question="What type of content do you focus on?",
            question_type=QuestionType.SERVICE_MODEL,
            options=["Breaking news", "Investigative journalism", "Opinion/Editorial", "Industry news", "Local news"],
            priority=5,
        ),
        ClarificationQuestion(
            id="monetization",
            question="How is the content monetized?",
            question_type=QuestionType.PRICING_MODEL,
            options=["Free with ads", "Paywall/Subscription", "Freemium (some free)", "Donations", "Sponsorships"],
            priority=4,
        ),
    ],
    "real-estate": [
        ClarificationQuestion(
            id="real_estate_type",
            question="What type of real estate do you deal with?",
            question_type=QuestionType.SERVICE_MODEL,
            options=["Residential sales", "Commercial properties", "Rentals/Property management", "Land/Development", "Mixed"],
            priority=5,
        ),
        ClarificationQuestion(
            id="client_type",
            question="Who are your primary clients?",
            question_type=QuestionType.TARGET_MARKET,
            options=["Home buyers", "Sellers", "Landlords", "Tenants", "Investors"],
            priority=4,
        ),
    ],
    "finance": [
        ClarificationQuestion(
            id="finance_type",
            question="What financial services do you provide?",
            question_type=QuestionType.SERVICE_MODEL,
            options=["Personal finance/Budgeting", "Investment management", "Accounting/Bookkeeping", "Lending", "Payments"],
            priority=5,
        ),
        ClarificationQuestion(
            id="compliance_level",
            question="What's your regulatory environment?",
            question_type=QuestionType.ENTITY_SPECIFIC,
            options=["Consumer fintech (light regulation)", "Registered investment advisor", "Banking/Heavy regulation", "Crypto/Emerging regulation"],
            priority=3,
        ),
    ],
}

# Keywords that indicate missing information
MISSING_INFO_INDICATORS = {
    "target_market": ["customer", "client", "user", "buyer", "audience", "market", "b2b", "b2c", "consumer"],
    "pricing": ["price", "pricing", "cost", "subscription", "fee", "charge", "pay", "payment", "tier"],
    "services": ["service", "product", "offering", "feature", "provide", "offer", "sell"],
    "scale": ["volume", "scale", "size", "capacity", "daily", "monthly", "users", "customers"],
}


class ClarificationAgent:
    """
    Generates smart clarifying questions based on detected domain uncertainty.

    The agent analyzes the user's description and ExtractedConcepts to determine
    what critical information is missing and generates targeted questions.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.7,
        max_questions: int = 4,
        min_questions: int = 2,
    ):
        """
        Initialize the clarification agent.

        Args:
            confidence_threshold: Below this score, ask domain confirmation
            max_questions: Maximum questions to ask (avoid overwhelming user)
            min_questions: Minimum questions to ensure we gather enough info
        """
        self.confidence_threshold = confidence_threshold
        self.max_questions = max_questions
        self.min_questions = min_questions

    def _detect_missing_info(
        self,
        description: str,
        entities: List[str],
        actions: List[str],
    ) -> List[str]:
        """Detect what critical information is missing from the description"""
        description_lower = description.lower()
        missing = []

        for info_type, indicators in MISSING_INFO_INDICATORS.items():
            has_indicator = any(ind in description_lower for ind in indicators)
            if not has_indicator:
                missing.append(info_type)

        # Additional checks based on entities/actions
        if not entities:
            missing.append("entities")
        if not actions:
            missing.append("actions")

        return missing

    def _get_industry_questions(self, industry: str) -> List[ClarificationQuestion]:
        """Get industry-specific questions"""
        return INDUSTRY_QUESTIONS.get(industry, [])

    def _generate_domain_confirmation_question(
        self,
        best_industry: str,
        best_score: float,
        secondary_industries: List[str],
    ) -> Optional[ClarificationQuestion]:
        """Generate a domain confirmation question if confidence is low"""
        if best_score >= self.confidence_threshold:
            return None

        # Build options from detected industries
        industry_display = best_industry.replace("-", " ").title()
        options = [f"{industry_display} (most likely)"]

        for secondary in secondary_industries[:3]:
            display = secondary.replace("-", " ").title()
            options.append(display)

        options.append("Something else (please specify)")

        return ClarificationQuestion(
            id="domain_confirmation",
            question=f"I detected this might be a {industry_display.lower()} business. Is that correct?",
            question_type=QuestionType.DOMAIN_CONFIRMATION,
            options=options,
            priority=5,
            context="Getting the right industry helps us use appropriate terminology and features",
        )

    def _generate_target_market_question(
        self,
        industry: str,
    ) -> ClarificationQuestion:
        """Generate target market question"""
        template = QUESTION_TEMPLATES[QuestionType.TARGET_MARKET]

        return ClarificationQuestion(
            id="target_market",
            question=template["template"],
            question_type=QuestionType.TARGET_MARKET,
            options=template["default_options"],
            priority=template["priority"],
            context=template["context"],
        )

    def _generate_pricing_question(
        self,
        industry: str,
        entities: List[str],
    ) -> ClarificationQuestion:
        """Generate pricing model question"""
        template = QUESTION_TEMPLATES[QuestionType.PRICING_MODEL]

        return ClarificationQuestion(
            id="pricing_model",
            question=template["template"],
            question_type=QuestionType.PRICING_MODEL,
            options=template["default_options"],
            priority=template["priority"],
            context=template["context"],
        )

    def _generate_scale_question(
        self,
        industry: str,
        entities: List[str],
    ) -> ClarificationQuestion:
        """Generate scale/volume question"""
        template = QUESTION_TEMPLATES[QuestionType.SCALE]

        # Customize metric based on entities
        if "order" in entities or "booking" in entities:
            metric = "order/booking"
        elif "user" in entities or "customer" in entities:
            metric = "customer"
        elif "appointment" in entities:
            metric = "appointment"
        else:
            metric = "transaction"

        return ClarificationQuestion(
            id="scale",
            question=f"What's your expected daily {metric} volume?",
            question_type=QuestionType.SCALE,
            options=template["default_options"],
            priority=template["priority"],
            context=template["context"],
        )

    def generate_questions(
        self,
        description: str,
        concepts: Any,  # ExtractedConcepts from smart_presets
    ) -> ClarificationResult:
        """
        Generate targeted clarification questions based on the description and concepts.

        Args:
            description: Original user description
            concepts: ExtractedConcepts from the smart preset system

        Returns:
            ClarificationResult with prioritized questions
        """
        questions: List[ClarificationQuestion] = []
        missing_info = self._detect_missing_info(
            description,
            concepts.entities,
            concepts.actions,
        )

        # 1. Domain confirmation if low confidence
        domain_q = self._generate_domain_confirmation_question(
            concepts.best_industry,
            concepts.best_score,
            concepts.secondary_industries,
        )
        if domain_q:
            questions.append(domain_q)

        # 2. Get industry-specific questions
        industry_questions = self._get_industry_questions(concepts.best_industry)
        questions.extend(industry_questions)

        # 3. Add generic questions for missing info
        if "target_market" in missing_info:
            questions.append(self._generate_target_market_question(concepts.best_industry))

        if "pricing" in missing_info:
            questions.append(self._generate_pricing_question(
                concepts.best_industry,
                concepts.entities,
            ))

        if "scale" in missing_info:
            questions.append(self._generate_scale_question(
                concepts.best_industry,
                concepts.entities,
            ))

        # 4. Sort by priority (higher first) and limit
        questions.sort(key=lambda q: q.priority, reverse=True)

        # Ensure we have at least min_questions but no more than max_questions
        if len(questions) > self.max_questions:
            questions = questions[:self.max_questions]

        logger.info(
            f"Generated {len(questions)} clarification questions for "
            f"'{concepts.best_industry}' (confidence={concepts.best_score:.2f})"
        )

        return ClarificationResult(
            questions=questions,
            enriched_description=description,
            confidence_before=concepts.best_score,
            detected_industry=concepts.best_industry,
            missing_info=missing_info,
        )

    def needs_clarification(
        self,
        concepts: Any,  # ExtractedConcepts
        description: str,
    ) -> bool:
        """
        Determine if clarification is needed.

        Returns True if:
        - Domain confidence is low (<threshold)
        - Critical information is missing
        - Description is too short (<50 chars)
        """
        # Short descriptions need clarification
        if len(description.strip()) < 50:
            return True

        # Low confidence needs clarification
        if concepts.best_score < self.confidence_threshold:
            return True

        # Check for missing critical info
        missing = self._detect_missing_info(
            description,
            concepts.entities,
            concepts.actions,
        )

        # If missing target market or services, ask
        if "target_market" in missing or "services" in missing:
            return True

        return False

    def enrich_description(
        self,
        original_description: str,
        responses: Dict[str, str],
    ) -> str:
        """
        Enrich the original description with user responses.

        Combines the original description with clarification responses
        to create a more detailed prompt for the agents.
        """
        enrichments = []

        for question_id, answer in responses.items():
            if not answer:
                continue

            # Map question IDs to enrichment text
            if question_id == "domain_confirmation":
                enrichments.append(f"Industry: {answer}")
            elif question_id == "target_market":
                enrichments.append(f"Target customers: {answer}")
            elif question_id in ("service_model", "pet_services", "restaurant_type",
                               "healthcare_type", "fitness_type", "product_type",
                               "saas_model", "education_type", "content_focus",
                               "real_estate_type", "finance_type"):
                enrichments.append(f"Services/products: {answer}")
            elif question_id in ("pricing_model", "membership_model", "pricing_tiers", "monetization"):
                enrichments.append(f"Pricing model: {answer}")
            elif question_id == "scale":
                enrichments.append(f"Expected scale: {answer}")
            elif question_id in ("unique_value",):
                enrichments.append(f"Differentiator: {answer}")
            else:
                # Generic enrichment
                enrichments.append(answer)

        if not enrichments:
            return original_description

        # Combine original description with enrichments
        enriched = f"{original_description}\n\nAdditional details:\n- " + "\n- ".join(enrichments)

        logger.info(f"Enriched description with {len(enrichments)} clarifications")

        return enriched


# Singleton instance
_clarification_agent: Optional[ClarificationAgent] = None


def get_clarification_agent() -> ClarificationAgent:
    """Get the singleton clarification agent"""
    global _clarification_agent
    if _clarification_agent is None:
        _clarification_agent = ClarificationAgent()
    return _clarification_agent
