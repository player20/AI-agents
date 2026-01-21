"""
News Prompts for Mira News

Contains Pydantic models and prompts for:
- Bias neutralization
- Fact extraction
- Perspective identification
- Topic summarization
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class VerifiedFact(BaseModel):
    """A fact that appears in multiple sources"""
    statement: str = Field(description="The factual statement")
    sources: List[str] = Field(description="Source names that report this fact")
    confidence: float = Field(
        ge=0, le=1,
        description="Confidence based on source agreement (0-1)"
    )


class Perspective(BaseModel):
    """A viewpoint on the issue from a particular group"""
    viewpoint: str = Field(
        description="The group or perspective (e.g., 'Environmental Groups', 'Industry Leaders', 'Government Officials')"
    )
    position: str = Field(
        description="Their stance or position on this issue"
    )
    source: str = Field(
        description="Which article/source this perspective came from"
    )


class BiasAnalysis(BaseModel):
    """Analysis of bias in the news coverage"""
    left_sources: List[str] = Field(
        default_factory=list,
        description="Sources with left-leaning bias"
    )
    center_sources: List[str] = Field(
        default_factory=list,
        description="Sources with center/neutral bias"
    )
    right_sources: List[str] = Field(
        default_factory=list,
        description="Sources with right-leaning bias"
    )
    coverage_balance: str = Field(
        description="Overall balance: 'balanced', 'left-leaning', 'right-leaning', or 'insufficient-data'"
    )
    missing_perspectives: List[str] = Field(
        default_factory=list,
        description="Important viewpoints not represented in the coverage"
    )
    charged_language_examples: List[str] = Field(
        default_factory=list,
        description="Examples of politically charged language found in sources"
    )


class PotentialOutcome(BaseModel):
    """A potential future outcome"""
    scenario: str = Field(description="Description of what might happen")
    likelihood: str = Field(
        description="Assessment: 'likely', 'possible', 'unlikely'"
    )
    timeframe: Optional[str] = Field(
        default=None,
        description="When this might occur (e.g., 'within weeks', 'next year')"
    )


class NeutralizedArticle(BaseModel):
    """
    Bias-neutralized article output.

    Represents a single news topic after processing through the bias
    neutralization pipeline. Contains only factual, verified information
    with clear separation between facts and analysis.
    """
    title: str = Field(
        description="Neutral, factual headline without sensationalism"
    )
    summary: str = Field(
        description="Neutral 2-3 sentence summary of the issue"
    )
    verified_facts: List[VerifiedFact] = Field(
        description="Facts verified across multiple sources"
    )
    unverified_claims: List[str] = Field(
        default_factory=list,
        description="Claims that appear in only one source (flagged as unverified)"
    )
    pros: List[str] = Field(
        description="Potential benefits or positive outcomes of this situation/decision"
    )
    cons: List[str] = Field(
        description="Potential challenges or negative outcomes"
    )
    potential_outcomes: List[PotentialOutcome] = Field(
        description="What might happen next (multiple scenarios)"
    )
    perspectives: List[Perspective] = Field(
        description="Different viewpoints on this issue"
    )
    bias_analysis: BiasAnalysis = Field(
        description="Analysis of bias in the coverage"
    )
    sources: List[dict] = Field(
        description="All sources used with their reliability scores"
    )
    category: str = Field(
        default="General",
        description="News category (Politics, Business, Technology, etc.)"
    )
    region: str = Field(
        default="",
        description="Geographic region this news pertains to"
    )


class TopicCluster(BaseModel):
    """A cluster of articles about the same topic"""
    topic_id: str = Field(description="Unique identifier for this topic")
    keywords: List[str] = Field(description="Key terms for this topic")
    article_count: int = Field(description="Number of articles in this cluster")
    importance_score: float = Field(
        ge=0, le=1,
        description="Importance score based on coverage volume and recency"
    )


# ============================================================================
# PROMPTS
# ============================================================================

BIAS_NEUTRALIZATION_PROMPT = """You are an expert journalist trained in neutral, fact-first reporting. Your goal is to synthesize news from multiple sources into an unbiased, factual summary.

## INPUT
You will receive articles about the same topic from different news sources. Each article includes:
- Source name and its political bias rating (left, center-left, center, center-right, right)
- Title and content

## YOUR TASK

### 1. EXTRACT VERIFIED FACTS
- Identify statements that appear in 2+ sources
- Rate confidence: 1.0 if all sources agree, lower if some disagree
- Only include objective, verifiable facts
- Exclude opinions, predictions, and editorial commentary

### 2. FLAG UNVERIFIED CLAIMS
- Note claims that appear in only one source
- These should be clearly labeled as unverified

### 3. IDENTIFY PERSPECTIVES
- Note how different groups view this issue
- Be fair to all viewpoints, even unpopular ones
- Include the source for each perspective

### 4. ANALYZE BIAS
- Categorize sources by their bias rating
- Note if coverage is balanced or skewed
- Identify missing perspectives
- Flag examples of charged/sensational language

### 5. CREATE NEUTRAL SUMMARY
Write a headline and summary that:
- Uses neutral, objective language
- Avoids loaded words (e.g., "slammed", "blasted", "radical")
- Presents facts without emotional framing
- Does not favor any political perspective

### 6. PROS & CONS
List potential benefits and challenges:
- Be balanced - both sides should have substance
- Focus on factual consequences, not partisan framing
- Include economic, social, and practical considerations

### 7. POTENTIAL OUTCOMES
Predict what might happen next:
- Include multiple scenarios (not just one narrative)
- Assess likelihood honestly
- Base predictions on historical precedent when possible

## IMPORTANT RULES
- NEVER copy sensational language from sources
- NEVER present opinion as fact
- ALWAYS attribute controversial claims to their source
- IF sources disagree on a fact, note the disagreement
- BE SKEPTICAL of claims without evidence

## ARTICLES TO ANALYZE

{articles}
"""


TOPIC_CLUSTERING_PROMPT = """Analyze these article titles and descriptions to identify the main topics being covered.

Group articles that are about the same underlying story or issue, even if they have different headlines or angles.

For each topic cluster, provide:
1. A neutral topic title
2. Key terms/keywords
3. Which article IDs belong to this cluster
4. An importance score (0-1) based on how much coverage it's getting

Articles:
{articles}
"""


FACT_VERIFICATION_PROMPT = """Cross-reference these claims from different sources to verify facts.

For each claim:
1. Check if it appears in multiple sources
2. Note any contradictions between sources
3. Identify the most reliable source for this claim
4. Rate confidence in the fact's accuracy

Claims to verify:
{claims}

Sources and their reliability ratings:
{sources}
"""


def format_articles_for_prompt(articles: list) -> str:
    """Format a list of RawArticle objects for the LLM prompt"""
    formatted = []

    for i, article in enumerate(articles, 1):
        formatted.append(f"""
---
ARTICLE {i}
Source: {article.source_name} (Bias: {article.source_bias})
Title: {article.title}
Content: {article.description or article.content or 'No content available'}
URL: {article.url}
Published: {article.published_at}
---
""")

    return "\n".join(formatted)


def get_bias_neutralization_prompt(articles: list) -> str:
    """Get the full bias neutralization prompt with articles inserted"""
    articles_text = format_articles_for_prompt(articles)
    return BIAS_NEUTRALIZATION_PROMPT.format(articles=articles_text)
