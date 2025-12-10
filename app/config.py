"""
Configuration settings for Vertex AI Search RAG API
Loads environment variables using Pydantic Settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables

    Required variables:
    - GEMINI_API_KEY: Google Gemini API key
    - GCP_PROJECT_ID: Google Cloud Platform project ID
    - GCP_SERVICE_ACCOUNT_KEY: JSON service account key (minified, as string)
    - VERTEX_SEARCH_ENGINE_ID: Vertex AI Search engine ID

    Optional variables:
    - VERTEX_SEARCH_LOCATION: Vertex AI Search location (default: "global")
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
    )

    # Gemini AI Configuration
    GEMINI_API_KEY: str

    # Google Cloud Platform / Vertex AI Search Configuration
    GCP_PROJECT_ID: str
    GCP_SERVICE_ACCOUNT_KEY: str  # JSON string (minified)
    VERTEX_SEARCH_ENGINE_ID: str
    VERTEX_SEARCH_LOCATION: str = "global"

    # Properties for backward compatibility and cleaner access
    @property
    def gcp_project_id(self) -> str:
        return self.GCP_PROJECT_ID

    @property
    def gcp_service_account_key(self) -> str:
        return self.GCP_SERVICE_ACCOUNT_KEY

    @property
    def vertex_search_engine_id(self) -> str:
        return self.VERTEX_SEARCH_ENGINE_ID

    @property
    def vertex_search_location(self) -> str:
        return self.VERTEX_SEARCH_LOCATION

    @property
    def gemini_api_key(self) -> str:
        return self.GEMINI_API_KEY

    # Allowed Gemini models for streaming mode
    allowed_models: list[str] = [
        "gemini-2.0-flash",
        "gemini-2.5-flash",
    ]

    # API metadata
    api_title: str = "Vertex AI Search RAG API"
    api_version: str = "1.0.0"
    api_description: str = "Standalone Vertex AI Search with RAG and Gemini streaming"


# Initialize settings instance (singleton)
settings = Settings()
