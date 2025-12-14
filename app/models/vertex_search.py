"""
Pydantic models for Vertex AI Search API
Equivalent to app/types/vertex-search.ts in Nuxt frontend
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Configuration Sub-Models
# ============================================================================

class ConditionBoostSpec(BaseModel):
    """Boost specification based on filter condition"""
    condition: str = Field(..., description="Filter expression (e.g., 'rating >= 4.5')")
    boost: float = Field(..., description="Boost amount (-1 to 1)", ge=-1.0, le=1.0)


class FreshnessBoostSpec(BaseModel):
    """Boost specification based on datetime freshness"""
    datetimeField: str = Field(..., description="Datetime field name (e.g., 'published_date')")
    freshnessDuration: str = Field(..., description="Duration (e.g., '30d' for 30 days)")
    boost: float = Field(..., description="Boost amount (-1 to 1)", ge=-1.0, le=1.0)


class BoostSpec(BaseModel):
    """Result boosting configuration"""
    conditionBoostSpecs: Optional[list[ConditionBoostSpec]] = Field(
        None, description="Condition-based boosts"
    )
    freshnessBoostSpecs: Optional[list[FreshnessBoostSpec]] = Field(
        None, description="Freshness-based boosts"
    )


class FacetKey(BaseModel):
    """Facet key configuration"""
    key: str = Field(..., description="Field name for faceting")
    restrictedValues: Optional[list[str]] = Field(None, description="Limit to specific values")


class FacetSpec(BaseModel):
    """Faceted search specification"""
    facetKey: FacetKey
    limit: Optional[int] = Field(20, description="Max facet values to return", ge=1, le=100)
    excludedFilterKeys: Optional[list[str]] = Field(None, description="Filter keys to exclude")
    enableDynamicPosition: Optional[bool] = Field(True, description="Enable dynamic positioning")


# ============================================================================
# Request Models
# ============================================================================

class VertexSearchRequest(BaseModel):
    """Request body for Vertex AI Search endpoint - ENHANCED with all major features"""

    # Core search parameters
    query: str = Field(..., description="Search query", min_length=1, max_length=500)
    mode: Literal["streaming", "direct"] = Field(
        default="streaming",
        description="Response mode: streaming (RAG→Gemini) or direct (Vertex summary)"
    )
    pageSize: Optional[int] = Field(
        default=5,
        description="Number of search results",
        ge=1,
        le=50  # Increased from 10 to 50 based on docs
    )
    model: Optional[str] = Field(
        default="gemini-2.0-flash",
        description="Gemini model for streaming mode"
    )

    # Query enhancement
    queryExpansion: Optional[Literal["AUTO", "DISABLED", "ALWAYS"]] = Field(
        default="AUTO",
        description="Query expansion mode"
    )
    spellCorrection: Optional[Literal["AUTO", "DISABLED", "SUGGESTION_ONLY"]] = Field(
        default="AUTO",
        description="Spell correction mode"
    )

    # Filtering
    filter: Optional[str] = Field(
        None,
        description="Filter expression (e.g., 'category: ANY(\"course\") AND price < 5000')"
    )
    canonicalFilter: Optional[str] = Field(
        None,
        description="Default filter applied with query expansion"
    )

    # Boosting
    boostSpec: Optional[BoostSpec] = Field(
        None,
        description="Result boosting configuration"
    )

    # Faceted search
    facetSpecs: Optional[list[FacetSpec]] = Field(
        None,
        description="Facet specifications (max 100)",
        max_length=100
    )

    # Relevance controls
    relevanceThreshold: Optional[Literal["LOWEST", "LOW", "MEDIUM", "HIGH", "HIGHEST"]] = Field(
        None,
        description="Minimum relevance threshold for results"
    )

    # Summary customization (direct mode)
    customSystemPrompt: Optional[str] = Field(
        None,
        description="Custom system prompt for AI summary (direct mode only)",
        max_length=2000
    )
    useSemanticChunks: Optional[bool] = Field(
        True,
        description="Use semantic chunking for better quality (direct mode)"
    )
    summaryResultCount: Optional[int] = Field(
        5,
        description="Number of results to use for summary",
        ge=1,
        le=10
    )
    languageCode: Optional[str] = Field(
        "th",
        description="BCP-47 language code for responses (e.g., 'th', 'en')"
    )

    # Advanced options
    returnRelevanceScore: Optional[bool] = Field(
        False,
        description="Include relevance scores in response"
    )
    safeSearch: Optional[bool] = Field(
        False,
        description="Enable safe search filtering"
    )

    # ========================================================================
    # MODEL GENERATION PARAMETERS (Streaming mode - Gemini)
    # ========================================================================
    temperature: Optional[float] = Field(
        None,
        description="Sampling temperature (0.0-2.0). Higher = more creative. Streaming mode only.",
        ge=0.0,
        le=2.0
    )
    topK: Optional[int] = Field(
        None,
        description="Top-K sampling (1-40). Limits to top K tokens. Streaming mode only.",
        ge=1,
        le=40
    )
    topP: Optional[float] = Field(
        None,
        description="Top-P nucleus sampling (0.0-1.0). Cumulative probability threshold. Streaming mode only.",
        ge=0.0,
        le=1.0
    )
    maxOutputTokens: Optional[int] = Field(
        None,
        description="Maximum output tokens (1-8192). Controls response length. Streaming mode only.",
        ge=1,
        le=8192
    )

    # ========================================================================
    # SUMMARY MODEL CONTROL (Direct mode - Vertex AI)
    # ========================================================================
    summaryModelVersion: Optional[Literal["stable", "preview"]] = Field(
        "stable",
        description="Vertex AI summary model version. 'stable' = production, 'preview' = latest. Direct mode only."
    )


# ============================================================================
# Response Models
# ============================================================================

class FormattedCitation(BaseModel):
    """Citation with source information - client-ready format"""
    id: Optional[str] = Field(None, description="Citation ID for tracking")
    title: str = Field(..., description="Human-readable source title")
    source_type: Optional[str] = Field(None, description="Type: faq, course, about, etc.")
    url: Optional[str] = Field(None, description="Public URL if available (not gs://)")
    snippet: Optional[str] = Field(None, description="Clean text preview (max 200 chars)")
    relevance_score: Optional[float] = Field(None, description="Relevance score 0-1", ge=0, le=1)

    # Keep original URI for debugging (not shown to end users)
    internal_uri: Optional[str] = Field(None, alias="uri", exclude=True)


class FacetValue(BaseModel):
    """Facet value with count"""
    value: str
    count: int


class Facet(BaseModel):
    """Facet result with values and counts"""
    key: str
    values: list[FacetValue]


class FormattedSearchResponse(BaseModel):
    """Formatted response for frontend"""
    success: bool
    mode: Literal["streaming", "direct"]
    query: str
    summary: Optional[str] = None
    citations: Optional[list[FormattedCitation]] = None
    facets: Optional[list[Facet]] = None  # NEW: Faceted search results
    totalResults: Optional[int] = None
    responseTime: float
    error: Optional[str] = None


# ============================================================================
# Streaming Models (for SSE)
# ============================================================================

class StreamChunk(BaseModel):
    """Single chunk in Server-Sent Events stream"""
    chunk: str
    done: bool
    citations: Optional[list[FormattedCitation]] = None
    responseTime: Optional[float] = None
