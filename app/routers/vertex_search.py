"""
Vertex AI Search Router - Provides /api/vertex-search endpoint
Supports both streaming (RAG + Gemini) and direct (Vertex summary) modes
"""

import time
import httpx
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.models.vertex_search import (
    VertexSearchRequest,
    FormattedSearchResponse,
    FormattedCitation
)
from app.services.vertex_ai_service import VertexAIService
from app.config import Settings, settings


router = APIRouter()

# Singleton instance - reuse credentials across requests
_vertex_service_instance: VertexAIService | None = None


def get_vertex_service() -> VertexAIService:
    """
    Dependency: Get or create Vertex AI service singleton instance

    Uses singleton pattern to:
    - Reuse GCP credentials across requests
    - Avoid redundant service account parsing
    - Maintain token refresh state
    """
    global _vertex_service_instance

    if _vertex_service_instance is None:
        print("[Service] Initializing VertexAIService singleton...")
        _vertex_service_instance = VertexAIService(
            gcp_project_id=settings.gcp_project_id,
            gcp_service_account_key=settings.gcp_service_account_key,
            vertex_search_engine_id=settings.vertex_search_engine_id,
            vertex_search_location=settings.vertex_search_location,
            gemini_api_key=settings.gemini_api_key
        )

    return _vertex_service_instance


@router.post("/vertex-search")
async def vertex_search(
    request: VertexSearchRequest,
    vertex_service: VertexAIService = Depends(get_vertex_service)
):
    """
    Vertex AI Search endpoint with dual modes

    Modes:
    - streaming: Get RAG data from Vertex → Stream via Gemini (SSE)
    - direct: Get AI summary directly from Vertex (JSON response)
    """
    start_time = time.time()

    try:
        if request.mode == "streaming":
            # ===== STREAMING MODE =====
            # Get RAG data from Vertex AI
            context, citations = await vertex_service.search_extractive(
                query=request.query,
                page_size=request.pageSize
            )

            if not context:
                # No context found - return error response
                response_time = time.time() - start_time
                return FormattedSearchResponse(
                    success=False,
                    mode="streaming",
                    query=request.query,
                    error="No relevant information found in knowledge base",
                    responseTime=round(response_time, 2)
                )

            # Stream response using Gemini with generation config
            return StreamingResponse(
                vertex_service.generate_streaming_response(
                    context=context,
                    query=request.query,
                    citations=citations,
                    model=request.model,
                    temperature=request.temperature,
                    top_k=request.topK,
                    top_p=request.topP,
                    max_output_tokens=request.maxOutputTokens
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
                    "Access-Control-Allow-Origin": "*",  # CORS header for streaming
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type"
                }
            )

        else:  # mode == "direct"
            # ===== DIRECT MODE =====

            # Build boost spec if provided
            boost_spec_dict = None
            if request.boostSpec:
                boost_spec_dict = {}
                if request.boostSpec.conditionBoostSpecs:
                    boost_spec_dict["conditionBoostSpecs"] = [
                        {"condition": b.condition, "boost": b.boost}
                        for b in request.boostSpec.conditionBoostSpecs
                    ]
                if request.boostSpec.freshnessBoostSpecs:
                    boost_spec_dict["freshnessBoostSpecs"] = [
                        {
                            "datetimeField": b.datetimeField,
                            "freshnessDuration": b.freshnessDuration,
                            "boost": b.boost
                        }
                        for b in request.boostSpec.freshnessBoostSpecs
                    ]

            # Build facet specs if provided
            facet_specs_list = None
            if request.facetSpecs:
                facet_specs_list = [
                    {
                        "facetKey": {
                            "key": f.facetKey.key,
                            "restrictedValues": f.facetKey.restrictedValues
                        },
                        "limit": f.limit,
                        "excludedFilterKeys": f.excludedFilterKeys,
                        "enableDynamicPosition": f.enableDynamicPosition
                    }
                    for f in request.facetSpecs
                ]

            result = await vertex_service.search_with_summary(
                query=request.query,
                page_size=request.pageSize,
                query_expansion=request.queryExpansion,
                spell_correction=request.spellCorrection,
                filter_expr=request.filter,
                canonical_filter=request.canonicalFilter,
                boost_spec=boost_spec_dict,
                facet_specs=facet_specs_list,
                relevance_threshold=request.relevanceThreshold,
                custom_system_prompt=request.customSystemPrompt,
                use_semantic_chunks=request.useSemanticChunks,
                summary_result_count=request.summaryResultCount,
                language_code=request.languageCode,
                summary_model_version=request.summaryModelVersion,
                return_relevance_score=request.returnRelevanceScore,
                safe_search=request.safeSearch
            )

            response_time = time.time() - start_time

            return FormattedSearchResponse(
                success=True,
                mode="direct",
                query=request.query,
                summary=result["summary"] or "ไม่พบคำตอบที่เหมาะสมในฐานความรู้",
                citations=result["citations"],
                facets=result.get("facets"),
                totalResults=result["totalResults"],
                responseTime=round(response_time, 2)
            )

    except ValueError as e:
        # Configuration errors
        raise HTTPException(status_code=500, detail=str(e))

    except httpx.HTTPStatusError as e:
        # Vertex AI API errors
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Vertex AI Search API failed: {e.response.text}"
        )

    except Exception as e:
        # Unexpected errors
        response_time = time.time() - start_time
        return FormattedSearchResponse(
            success=False,
            mode=request.mode,
            query=request.query,
            error=str(e),
            responseTime=round(response_time, 2)
        )
