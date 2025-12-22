"""
Pydantic models for Feedback API
Handles user feedback on AI responses (thumbs up/down with optional reason)
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class FeedbackRequest(BaseModel):
    """
    Request body for POST /api/feedback
    Sent from frontend when user provides feedback on AI response
    """

    messageId: str = Field(
        ...,
        description="Unique message ID from chat session",
        min_length=1,
        max_length=200
    )

    feedback: Literal["up", "down"] = Field(
        ...,
        description="Feedback type: thumbs up or down"
    )

    reason: Optional[str] = Field(
        None,
        description="Optional reason for thumbs down (max 500 chars)",
        max_length=500
    )

    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp when feedback was given"
    )

    messageContent: Optional[str] = Field(
        None,
        description="First 200 chars of the AI message for context",
        max_length=200
    )


class FeedbackResponse(BaseModel):
    """
    Response after successfully logging feedback to GCS
    """

    success: bool = Field(..., description="Whether feedback was logged successfully")

    message: str = Field(..., description="Human-readable status message")

    feedbackId: Optional[str] = Field(
        None,
        description="Unique ID for this feedback entry (filename in GCS)"
    )

    storedAt: Optional[str] = Field(
        None,
        description="ISO timestamp when feedback was stored"
    )

    error: Optional[str] = Field(
        None,
        description="Error message if success=False"
    )
