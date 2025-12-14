"""
Vertex AI Search service - handles GCP authentication and API calls
Equivalent to server/api/vertex-search.post.ts in Nuxt
"""

import json
import time
import re
from typing import AsyncGenerator
from datetime import datetime, timedelta
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import httpx
import google.generativeai as genai
from app.models.vertex_search import FormattedCitation, StreamChunk


class VertexAIService:
    """Service for interacting with Vertex AI Search and Gemini"""

    def __init__(
        self,
        gcp_project_id: str,
        gcp_service_account_key: str,
        vertex_search_engine_id: str,
        vertex_search_location: str = "global",
        gemini_api_key: str = None
    ):
        self.gcp_project_id = gcp_project_id
        self.vertex_search_engine_id = vertex_search_engine_id
        self.vertex_search_location = vertex_search_location
        self.gemini_api_key = gemini_api_key

        # Parse service account credentials
        try:
            service_account_info = json.loads(gcp_service_account_key)
            self.credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid GCP service account key format: {e}")

    def _get_access_token(self) -> str:
        """
        Get OAuth2 access token for GCP API calls with automatic refresh

        Refreshes token proactively if:
        - Token is expired (credentials.valid = False)
        - Token expires within 5 minutes (safety buffer)
        """
        needs_refresh = False

        # Check if token is already invalid
        if not self.credentials.valid:
            needs_refresh = True
            print("[Token] Token is invalid, refreshing...")

        # Check if token expires soon (within 5 minutes)
        elif self.credentials.expiry:
            time_until_expiry = self.credentials.expiry - datetime.now(self.credentials.expiry.tzinfo)
            if time_until_expiry < timedelta(minutes=5):
                needs_refresh = True
                print(f"[Token] Token expires in {time_until_expiry.total_seconds():.0f}s, refreshing proactively...")

        # Refresh if needed
        if needs_refresh:
            try:
                self.credentials.refresh(Request())
                if self.credentials.expiry:
                    time_until_expiry = self.credentials.expiry - datetime.now(self.credentials.expiry.tzinfo)
                    print(f"[Token] Refreshed successfully. New token valid for {time_until_expiry.total_seconds() / 60:.1f} minutes")
            except Exception as e:
                print(f"[Token] Refresh failed: {e}")
                raise ValueError(f"Failed to refresh GCP access token: {e}")

        return self.credentials.token

    def _parse_source_metadata(self, title: str, uri: str | None) -> dict:
        """
        Extract source metadata from title and URI for client-friendly display

        Returns dict with:
        - id: Clean ID from title (e.g., "ai-faqs" -> "ai-faqs")
        - title: Human-readable title
        - source_type: Category (faq, course, about, etc.)
        - url: Public URL if applicable
        """
        # Extract ID from title (often in format like [ai-faqs])
        title_clean = title.strip()
        source_id = None
        source_type = "unknown"

        # Check if title is in format [id]
        if title_clean.startswith("[") and title_clean.endswith("]"):
            source_id = title_clean[1:-1]
            title_clean = source_id.replace("-", " ").title()
        # Check if URI contains hints about source type
        elif uri and "/json/" in uri:
            # Extract from URI: .../json/ai-faqs.json
            import re
            match = re.search(r'/json/([^/]+)\.json', uri)
            if match:
                source_id = match.group(1)
                # Make title readable
                title_clean = source_id.replace("-", " ").title()

        # Determine source type from ID
        if source_id:
            if "faq" in source_id.lower():
                source_type = "faq"
                title_clean = "คำถามที่พบบ่อย"
            elif "course" in source_id.lower():
                source_type = "course"
                title_clean = "หลักสูตรอบรม"
            elif "about" in source_id.lower():
                source_type = "about"
                title_clean = "เกี่ยวกับเรา"
            elif "promotion" in source_id.lower():
                source_type = "promotion"
                title_clean = "โปรโมชั่น"
            elif "online" in source_id.lower():
                source_type = "course"
                title_clean = "คอร์สออนไลน์"
            elif "public" in source_id.lower():
                source_type = "course"
                title_clean = "คอร์สสาธารณะ"
            else:
                source_type = "info"

        # Don't expose internal gs:// URIs - replace with public URL if needed
        public_url = None
        if uri and not uri.startswith("gs://"):
            public_url = uri

        return {
            "id": source_id,
            "title": title_clean,
            "source_type": source_type,
            "url": public_url
        }

    def _clean_snippet(self, raw_snippet: str, max_length: int = 200) -> str:
        """
        Clean up raw snippet text for display
        - Removes JSON formatting artifacts
        - Strips HTML tags
        - Limits length
        - Extracts readable content
        """
        if not raw_snippet:
            return ""

        # Remove common JSON artifacts
        text = raw_snippet
        text = re.sub(r'^_"', '', text)  # Remove leading _"
        text = re.sub(r'"_$', '', text)  # Remove trailing "_
        text = re.sub(r'\\"', '"', text)  # Unescape quotes
        text = re.sub(r'\\n', ' ', text)  # Replace \n with space

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove JSON key-value patterns like "key": "value",
        text = re.sub(r'"[\w_]+"\s*:\s*"', '', text)
        text = re.sub(r'",\s*"', ' ', text)

        # Remove special characters and extra whitespace
        text = re.sub(r'[{}[\]"]', '', text)
        text = re.sub(r'\s+', ' ', text)

        # Trim and limit length
        text = text.strip()
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'

        return text

    def _build_vertex_endpoint(self) -> str:
        """Construct Vertex AI Search API endpoint URL"""
        return (
            f"https://discoveryengine.googleapis.com/v1alpha/"
            f"projects/{self.gcp_project_id}/"
            f"locations/{self.vertex_search_location}/"
            f"collections/default_collection/"
            f"engines/{self.vertex_search_engine_id}/"
            f"servingConfigs/default_search:search"
        )

    async def search_extractive(self, query: str, page_size: int = 5) -> tuple[str, list[FormattedCitation]]:
        """
        Get RAG data from Vertex AI (extractive content only, no summary)
        Returns: (context_text, citations)
        """
        endpoint = self._build_vertex_endpoint()
        access_token = self._get_access_token()

        payload = {
            "query": query,
            "pageSize": page_size,
            "queryExpansionSpec": {"condition": "AUTO"},
            "spellCorrectionSpec": {"mode": "AUTO"},
            "contentSearchSpec": {
                "extractiveContentSpec": {
                    "maxExtractiveAnswerCount": 5,
                    "maxExtractiveSegmentCount": 1
                }
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30.0
            )

            response.raise_for_status()
            data = response.json()

        # Extract context and citations
        context = ""
        citations = []

        results = data.get("results", [])
        for result in results:
            doc = result.get("document", {})
            derived_data = doc.get("derivedStructData", {})

            # Extract text content
            snippets = derived_data.get("snippets", [])
            for snippet_obj in snippets:
                snippet_text = snippet_obj.get("snippet")
                if snippet_text:
                    context += snippet_text + "\n\n"

            # Extract extractive answers
            extractive_answers = derived_data.get("extractive_answers", [])
            for answer in extractive_answers:
                content = answer.get("content")
                if content:
                    context += content + "\n\n"

            # Build citation with cleaned snippet and metadata
            raw_snippet = (snippets[0].get("snippet") if snippets else
                          extractive_answers[0].get("content") if extractive_answers else None)

            title = derived_data.get("title") or doc.get("name") or doc.get("id", "Untitled")
            uri = derived_data.get("link") or doc.get("uri")

            # Parse metadata for client-friendly fields
            metadata = self._parse_source_metadata(title, uri)

            citations.append(FormattedCitation(
                id=metadata["id"],
                title=metadata["title"],
                source_type=metadata["source_type"],
                url=metadata["url"],
                snippet=self._clean_snippet(raw_snippet) if raw_snippet else None,
                relevance_score=None  # Vertex AI doesn't provide this in extractive mode
            ))

        return context.strip(), citations

    async def search_with_summary(
        self,
        query: str,
        page_size: int = 5,
        # Query enhancement
        query_expansion: str = "AUTO",
        spell_correction: str = "AUTO",
        # Filtering
        filter_expr: str = None,
        canonical_filter: str = None,
        # Boosting
        boost_spec: dict = None,
        # Facets
        facet_specs: list = None,
        # Relevance
        relevance_threshold: str = None,
        # Summary customization
        custom_system_prompt: str = None,
        use_semantic_chunks: bool = True,
        summary_result_count: int = 5,
        language_code: str = "th",
        summary_model_version: str = "stable",  # NEW: Model version control
        # Advanced
        return_relevance_score: bool = False,
        safe_search: bool = False
    ) -> dict:
        """
        Get AI summary directly from Vertex AI Search - ENHANCED
        Returns: dict with summary, citations, totalResults, facets
        """
        endpoint = self._build_vertex_endpoint()
        access_token = self._get_access_token()

        # Build base payload
        payload = {
            "query": query,
            "pageSize": page_size,
            "queryExpansionSpec": {"condition": query_expansion},
            "spellCorrectionSpec": {"mode": spell_correction},
        }

        # Add filters if provided
        if filter_expr:
            payload["filter"] = filter_expr
        if canonical_filter:
            payload["canonicalFilter"] = canonical_filter

        # Add boosting if provided
        if boost_spec:
            payload["boostSpec"] = boost_spec

        # Add facets if provided
        if facet_specs:
            payload["facetSpecs"] = facet_specs

        # Add relevance threshold if provided
        if relevance_threshold:
            payload["relevanceThreshold"] = relevance_threshold

        # Add safe search if enabled
        if safe_search:
            payload["safeSearch"] = True

        # Build summary spec
        summary_spec = {
            "summaryResultCount": summary_result_count,
            "includeCitations": True,
            "ignoreAdversarialQuery": True,
            "ignoreJailBreakingQuery": True,  # Filter prompt injections
            "modelSpec": {"version": summary_model_version}  # Use configurable model version
        }

        # Add semantic chunks if enabled
        if use_semantic_chunks:
            summary_spec["useSemanticChunks"] = True

        # Add custom system prompt if provided
        if custom_system_prompt:
            summary_spec["modelPromptSpec"] = {
                "preamble": custom_system_prompt
            }

        # Add language code
        if language_code:
            summary_spec["languageCode"] = language_code

        # Add content search spec
        payload["contentSearchSpec"] = {
            "summarySpec": summary_spec
        }

        # Add snippet spec for better previews
        payload["contentSearchSpec"]["snippetSpec"] = {
            "returnSnippet": True
        }

        # Add relevance score if requested
        if return_relevance_score:
            payload["relevanceScoreSpec"] = {
                "returnRelevanceScore": True
            }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30.0
            )

            response.raise_for_status()
            data = response.json()

        # Extract summary and citations
        citations = []
        summary_data = data.get("summary", {})

        # Try to get citations from summary metadata
        summary_with_metadata = summary_data.get("summaryWithMetadata", {})
        references = summary_with_metadata.get("references", [])

        for ref in references:
            chunk_contents = ref.get("chunkContents", [])
            raw_snippet = chunk_contents[0].get("content") if chunk_contents else None

            title = ref.get("title", "Untitled")
            uri = ref.get("uri")

            # Parse metadata for client-friendly fields
            metadata = self._parse_source_metadata(title, uri)

            citations.append(FormattedCitation(
                id=metadata["id"],
                title=metadata["title"],
                source_type=metadata["source_type"],
                url=metadata["url"],
                snippet=self._clean_snippet(raw_snippet) if raw_snippet else None,
                relevance_score=None
            ))

        # Fallback: extract from search results if no summary citations
        if not citations:
            results = data.get("results", [])
            for result in results[:5]:
                doc = result.get("document", {})
                derived_data = doc.get("derivedStructData", {})

                snippets = derived_data.get("snippets", [])
                extractive_answers = derived_data.get("extractive_answers", [])

                raw_snippet = (snippets[0].get("snippet") if snippets else
                              extractive_answers[0].get("content") if extractive_answers else None)

                title = derived_data.get("title") or doc.get("name") or doc.get("id", "Untitled")
                uri = derived_data.get("link") or doc.get("uri")

                # Parse metadata for client-friendly fields
                metadata = self._parse_source_metadata(title, uri)

                citations.append(FormattedCitation(
                    id=metadata["id"],
                    title=metadata["title"],
                    source_type=metadata["source_type"],
                    url=metadata["url"],
                    snippet=self._clean_snippet(raw_snippet) if raw_snippet else None,
                    relevance_score=None
                ))

        # Extract facets if present
        facets = []
        facet_results = data.get("facets", [])
        for facet_result in facet_results:
            facet_key = facet_result.get("key")
            facet_values_raw = facet_result.get("values", [])

            facet_values = [
                {"value": fv.get("value"), "count": fv.get("count", 0)}
                for fv in facet_values_raw
            ]

            if facet_key and facet_values:
                facets.append({
                    "key": facet_key,
                    "values": facet_values
                })

        return {
            "summary": summary_with_metadata.get("summary") or summary_data.get("summary"),
            "citations": citations,
            "facets": facets if facets else None,
            "totalResults": data.get("totalSize")
        }

    async def generate_streaming_response(
        self,
        context: str,
        query: str,
        citations: list[FormattedCitation],
        model: str = "gemini-2.0-flash",
        # Generation config parameters
        temperature: float = None,
        top_k: int = None,
        top_p: float = None,
        max_output_tokens: int = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response using Gemini with RAG context - ENHANCED
        Yields SSE-formatted chunks

        Args:
            context: RAG context from Vertex AI Search
            query: User query
            citations: List of citations
            model: Gemini model name
            temperature: Sampling temperature (0.0-2.0)
            top_k: Top-K sampling (1-40)
            top_p: Top-P nucleus sampling (0.0-1.0)
            max_output_tokens: Maximum output tokens (1-8192)
        """
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY required for streaming mode")

        # Configure Gemini
        genai.configure(api_key=self.gemini_api_key)

        # Build generation config
        generation_config = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if top_k is not None:
            generation_config["top_k"] = top_k
        if top_p is not None:
            generation_config["top_p"] = top_p
        if max_output_tokens is not None:
            generation_config["max_output_tokens"] = max_output_tokens

        # Create model with optional generation config
        gemini_model = genai.GenerativeModel(
            model,
            generation_config=generation_config if generation_config else None
        )

        # Build prompt with context
        prompt = f"""คุณเป็นผู้ช่วย AI ของ 9Expert Training ซึ่งเป็นศูนย์ฝึกอบรมด้าน Data Analytics, Business Intelligence และ AI

โปรดใช้ข้อมูลต่อไปนี้เป็นบริบทในการตอบคำถาม:

<context>
{context}
</context>

คำถามจากผู้ใช้: {query}

โปรดตอบคำถามเป็นภาษาไทย โดย:
1. ตอบตรงประเด็น ชัดเจน กระชับ
2. ใช้ข้อมูลจาก context ที่ให้มาเท่านั้น
3. ถ้าข้อมูลไม่เพียงพอ บอกได้ว่าไม่มีข้อมูลในส่วนนั้น
4. จัดรูปแบบให้อ่านง่าย ใช้ bullet points ถ้าเหมาะสม

คำตอบ:"""

        # Generate streaming response
        start_time = time.time()
        response = gemini_model.generate_content(prompt, stream=True)

        for chunk in response:
            if chunk.text:
                # Yield SSE chunk
                chunk_data = StreamChunk(
                    chunk=chunk.text,
                    done=False
                )
                yield f"data: {chunk_data.model_dump_json()}\n\n"

        # Yield final chunk with citations
        response_time = time.time() - start_time
        final_chunk = StreamChunk(
            chunk="",
            done=True,
            citations=citations[:5],  # Limit to top 5
            responseTime=round(response_time, 2)
        )
        yield f"data: {final_chunk.model_dump_json()}\n\n"
