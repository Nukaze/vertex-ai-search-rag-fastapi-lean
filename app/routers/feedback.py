"""
Feedback Router - Provides POST /api/feedback endpoint
Handles user feedback on AI responses (thumbs up/down with optional reason)
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.feedback import FeedbackRequest, FeedbackResponse
from app.services.gcs_feedback_service import GCSFeedbackService
from app.config import settings


router = APIRouter()

# Singleton instance - reuse GCS client across requests
_feedback_service_instance: GCSFeedbackService | None = None


def get_feedback_service() -> GCSFeedbackService:
    """
    Dependency: Get or create GCS feedback service singleton instance

    Uses singleton pattern to:
    - Reuse GCS credentials across requests
    - Avoid redundant service account parsing
    - Maintain connection pool
    """
    global _feedback_service_instance

    if _feedback_service_instance is None:
        print("[Service] Initializing GCSFeedbackService singleton...")
        _feedback_service_instance = GCSFeedbackService(
            gcp_service_account_key=settings.gcp_service_account_key,
            gcp_project_id=settings.gcp_project_id,
            feedback_bucket_name="9expert-feedback-storage"  # TODO: Move to config
        )

    return _feedback_service_instance


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackRequest,
    feedback_service: GCSFeedbackService = Depends(get_feedback_service)
):
    """
    Submit user feedback on AI responses

    Request body:
        - messageId: Unique message ID from chat session
        - feedback: "up" or "down"
        - reason: Optional reason for thumbs down (max 500 chars)
        - timestamp: ISO 8601 timestamp when feedback was given
        - messageContent: First 200 chars of AI message for context

    Response:
        - success: Whether feedback was logged successfully
        - message: Human-readable status message
        - feedbackId: Unique ID for this feedback entry (filename in GCS)
        - storedAt: ISO timestamp when feedback was stored
        - error: Error message if success=False

    Stores feedback in GCS as NDJSON with datetime-sorted filenames:
        - Bucket: 9expert-feedback-storage
        - Path: feedback/feedback_YYYYMMDD_HHMMSS_milliseconds.json
        - Format: Single-line JSON (NDJSON)
    """
    try:
        # Log feedback to GCS
        result = await feedback_service.log_feedback(feedback)

        if result["success"]:
            return FeedbackResponse(
                success=True,
                message="ขอบคุณสำหรับคำติชมครับ! เราจะนำไปปรับปรุง AI ให้ดีขึ้น",
                feedbackId=result["feedbackId"],
                storedAt=result["storedAt"],
                error=None
            )
        else:
            # GCS logging failed, but don't expose internal error to user
            print(f"[Feedback] GCS logging failed: {result['error']}")
            raise HTTPException(
                status_code=500,
                detail="ขออภัย ไม่สามารถบันทึกคำติชมได้ กรุณาลองใหม่อีกครั้ง"
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        # Unexpected errors
        print(f"[Feedback] Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="ขออภัย เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง"
        )
