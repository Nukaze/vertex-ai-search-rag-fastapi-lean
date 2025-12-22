"""
Vertex AI Search RAG API - Main FastAPI application
Standalone service for Vertex AI Search with RAG and Gemini streaming
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import vertex_search, feedback

# Run with: uvicorn app.main:app --reload --port 8000

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
)

# Add CORS middleware for cross-origin requests
# Allows requests from:
# - Localhost (development)
# - Vercel deployments (production)
# - Any custom domains (if needed later)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:3000|http://127\.0\.0\.1:3000|https://.*\.9expert\.com",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register Vertex Search router
app.include_router(vertex_search.router, prefix="/api", tags=["vertex-search"])

# Register Feedback router
app.include_router(feedback.router, prefix="/api", tags=["feedback"])


@app.get("/")
async def root():
    """
    Health check endpoint
    Returns API status and service information
    """
    return {
        "status": "ok",
        "service": settings.api_title,
        "version": settings.api_version,
        "endpoints": {
            "vertex_search": "/api/vertex-search",
            "feedback": "/api/feedback",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "service": settings.api_title
    }
