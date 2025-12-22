"""
GCS Feedback Service - Handles logging user feedback to Google Cloud Storage
Stores feedback as NDJSON (Newline Delimited JSON) with datetime-based filenames for sorting
"""

import json
from datetime import datetime
from typing import Optional
from google.cloud import storage
from google.oauth2 import service_account
from app.models.feedback import FeedbackRequest


class GCSFeedbackService:
    """Service for logging feedback to Google Cloud Storage"""

    def __init__(
        self,
        gcp_service_account_key: str,
        gcp_project_id: str,
        feedback_bucket_name: str = "9expert-feedback-storage"
    ):
        """
        Initialize GCS client with service account credentials

        Args:
            gcp_service_account_key: JSON string of service account credentials
            gcp_project_id: GCP project ID
            feedback_bucket_name: GCS bucket name for feedback storage
        """
        self.gcp_project_id = gcp_project_id
        self.feedback_bucket_name = feedback_bucket_name

        # Parse service account credentials
        try:
            service_account_info = json.loads(gcp_service_account_key)
            self.credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid GCP service account key format: {e}")

        # Initialize GCS client
        self.storage_client = storage.Client(
            project=self.gcp_project_id,
            credentials=self.credentials
        )

    def _ensure_bucket_exists(self) -> storage.Bucket:
        """
        Ensure feedback bucket exists, create if not

        Returns:
            GCS Bucket object
        """
        try:
            bucket = self.storage_client.get_bucket(self.feedback_bucket_name)
            return bucket
        except Exception:
            # Bucket doesn't exist, create it
            print(f"[GCS] Bucket '{self.feedback_bucket_name}' not found, creating...")
            bucket = self.storage_client.create_bucket(
                self.feedback_bucket_name,
                location="ASIA-SOUTHEAST1"  # Bangkok region
            )
            print(f"[GCS] Bucket '{self.feedback_bucket_name}' created successfully")
            return bucket

    def _generate_feedback_id(self, timestamp_iso: str) -> str:
        """
        Generate unique feedback ID based on timestamp for sorting

        Format: feedback_YYYYMMDD_HHMMSS_milliseconds.json
        Example: feedback_20250122_143025_456.json

        This format ensures:
        - Files are automatically sorted by datetime in GCS
        - Easy to filter by date range
        - Collision-resistant (millisecond precision)

        Args:
            timestamp_iso: ISO 8601 timestamp string

        Returns:
            Unique feedback filename
        """
        try:
            dt = datetime.fromisoformat(timestamp_iso.replace('Z', '+00:00'))
            # Format: YYYYMMDD_HHMMSS_milliseconds
            date_part = dt.strftime("%Y%m%d_%H%M%S")
            milliseconds = dt.microsecond // 1000
            return f"feedback_{date_part}_{milliseconds:03d}.json"
        except Exception as e:
            # Fallback: use current time if parsing fails
            print(f"[GCS] Warning: Failed to parse timestamp '{timestamp_iso}', using current time: {e}")
            now = datetime.utcnow()
            date_part = now.strftime("%Y%m%d_%H%M%S")
            milliseconds = now.microsecond // 1000
            return f"feedback_{date_part}_{milliseconds:03d}.json"

    async def log_feedback(self, feedback: FeedbackRequest) -> dict:
        """
        Log feedback to GCS as NDJSON

        Args:
            feedback: FeedbackRequest object with user feedback data

        Returns:
            dict with:
                - success: bool
                - feedbackId: str (filename)
                - storedAt: str (ISO timestamp)
                - error: Optional[str]
        """
        try:
            # Ensure bucket exists
            bucket = self._ensure_bucket_exists()

            # Generate unique feedback ID (filename)
            feedback_id = self._generate_feedback_id(feedback.timestamp)

            # Prepare feedback data as JSON
            feedback_data = {
                "messageId": feedback.messageId,
                "feedback": feedback.feedback,
                "reason": feedback.reason,
                "timestamp": feedback.timestamp,
                "messageContent": feedback.messageContent,
                "storedAt": datetime.utcnow().isoformat() + "Z"
            }

            # Convert to NDJSON (single line JSON)
            ndjson_content = json.dumps(feedback_data, ensure_ascii=False)

            # Upload to GCS
            blob = bucket.blob(f"feedback/{feedback_id}")
            blob.upload_from_string(
                ndjson_content,
                content_type="application/x-ndjson"
            )

            print(f"[GCS] Feedback logged successfully: {feedback_id}")

            return {
                "success": True,
                "feedbackId": feedback_id,
                "storedAt": feedback_data["storedAt"],
                "error": None
            }

        except Exception as e:
            error_msg = f"Failed to log feedback to GCS: {str(e)}"
            print(f"[GCS] Error: {error_msg}")
            return {
                "success": False,
                "feedbackId": None,
                "storedAt": None,
                "error": error_msg
            }
