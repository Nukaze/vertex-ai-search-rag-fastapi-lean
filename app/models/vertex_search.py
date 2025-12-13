"""
Pydantic models for Vertex AI Search API
Equivalent to app/types/vertex-search.ts in Nuxt frontend
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Request Models
# ============================================================================

class VertexSearchRequest(BaseModel):
    """Request body for Vertex AI Search endpoint"""
    query: str = Field(..., description="Search query", min_length=1, max_length=500)
    mode: Literal["streaming", "direct"] = Field(
        default="streaming",
        description="Response mode: streaming (RAG→Gemini) or direct (Vertex summary)"
    )
    pageSize: Optional[int] = Field(
        default=5,
        description="Number of search results",
        ge=1,
        le=10
    )
    model: Optional[str] = Field(
        default="gemini-2.0-flash",
        description="Gemini model for streaming mode"
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


class FormattedSearchResponse(BaseModel):
    """Formatted response for frontend"""
    success: bool
    mode: Literal["streaming", "direct"]
    query: str
    summary: Optional[str] = None
    citations: Optional[list[FormattedCitation]] = None
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
