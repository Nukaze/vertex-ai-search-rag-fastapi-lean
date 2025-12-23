"""
GCS Feedback Service - Handles logging user feedback to Google Cloud Storage
Stores feedback as NDJSON (Newline Delimited JSON) with datetime-based filenames for sorting

Structure:
- chat-feedback/YYYY-MM-DD/positive_YYYYMMDD_HHMMSS_ms.json  (archive, thumbs up)
- chat-feedback/YYYY-MM-DD/negative_YYYYMMDD_HHMMSS_ms.json  (archive, thumbs down)
- chat-feedback/latest/positive_YYYYMMDD_HHMMSS_ms.json       (today only, cleared daily)
- chat-feedback/latest/negative_YYYYMMDD_HHMMSS_ms.json       (today only, cleared daily)
"""

import json
from datetime import datetime
from typing import Optional, Tuple
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

    def _get_bucket(self) -> storage.Bucket:
        """
        Get bucket reference (no API call, just returns bucket object)

        Returns:
            GCS Bucket object (lightweight reference, doesn't verify existence)
        """
        # Use bucket() instead of get_bucket() to avoid storage.buckets.get permission
        # This creates a bucket reference without making an API call
        bucket = self.storage_client.bucket(self.feedback_bucket_name)
        return bucket

    def _get_current_date(self) -> str:
        """
        Get current date in UTC for folder naming

        Returns:
            Date string in format YYYY-MM-DD
        """
        return datetime.utcnow().strftime("%Y-%m-%d")

    def _check_and_clear_latest_folder(self, current_date: str) -> None:
        """
        Check if it's a new day and clear the latest/ folder if needed

        Strategy:
        - Store last_cleared_date in a marker file: chat-feedback/latest/.last_cleared
        - If current date != last_cleared_date, delete all files in latest/ and update marker

        Args:
            current_date: Current date in YYYY-MM-DD format
        """
        try:
            bucket = self._get_bucket()
            marker_blob = bucket.blob("chat-feedback/latest/.last_cleared")

            # Check if marker exists and get last cleared date
            if marker_blob.exists():
                last_cleared = marker_blob.download_as_text().strip()

                if last_cleared == current_date:
                    # Already cleared today, no action needed
                    return

            # New day - clear all feedback files in latest/
            print(f"[GCS] New day detected ({current_date}), clearing chat-feedback/latest/ folder...")

            blobs = bucket.list_blobs(prefix="chat-feedback/latest/")
            deleted_count = 0

            for blob in blobs:
                # Don't delete the marker file itself during iteration
                if not blob.name.endswith(".last_cleared"):
                    blob.delete()
                    deleted_count += 1

            # Update marker file with current date
            marker_blob.upload_from_string(current_date, content_type="text/plain")

            print(f"[GCS] Cleared {deleted_count} files from chat-feedback/latest/")

        except Exception as e:
            # Don't fail feedback submission if cleanup fails
            print(f"[GCS] Warning: Failed to clear latest folder: {e}")

    def _generate_feedback_paths(self, timestamp_iso: str, feedback_type: str) -> Tuple[str, str, str]:
        """
        Generate both archive and latest paths for feedback with sentiment prefix

        Format:
        - Archive: chat-feedback/YYYY-MM-DD/positive_YYYYMMDD_HHMMSS_milliseconds.json
        - Latest: chat-feedback/latest/positive_YYYYMMDD_HHMMSS_milliseconds.json

        Args:
            timestamp_iso: ISO 8601 timestamp string
            feedback_type: "up" or "down"

        Returns:
            Tuple of (date_folder, archive_path, latest_path)
            Example:
                ("2025-01-22",
                 "chat-feedback/2025-01-22/negative_20250122_143025_456.json",
                 "chat-feedback/latest/negative_20250122_143025_456.json")
        """
        try:
            dt = datetime.fromisoformat(timestamp_iso.replace('Z', '+00:00'))
            # Date folder: YYYY-MM-DD
            date_folder = dt.strftime("%Y-%m-%d")
            # Filename prefix based on feedback type
            prefix = "positive" if feedback_type == "up" else "negative"
            # Timestamp: YYYYMMDD_HHMMSS_milliseconds
            time_part = dt.strftime("%Y%m%d_%H%M%S")
            milliseconds = dt.microsecond // 1000
            filename = f"{prefix}_{time_part}_{milliseconds:03d}.json"

            archive_path = f"chat-feedback/{date_folder}/{filename}"
            latest_path = f"chat-feedback/latest/{filename}"

            return date_folder, archive_path, latest_path

        except Exception as e:
            # Fallback: use current time if parsing fails
            print(f"[GCS] Warning: Failed to parse timestamp '{timestamp_iso}', using current time: {e}")
            now = datetime.utcnow()
            date_folder = now.strftime("%Y-%m-%d")
            prefix = "positive" if feedback_type == "up" else "negative"
            time_part = now.strftime("%Y%m%d_%H%M%S")
            milliseconds = now.microsecond // 1000
            filename = f"{prefix}_{time_part}_{milliseconds:03d}.json"

            archive_path = f"chat-feedback/{date_folder}/{filename}"
            latest_path = f"chat-feedback/latest/{filename}"

            return date_folder, archive_path, latest_path

    async def log_feedback(self, feedback: FeedbackRequest) -> dict:
        """
        Log feedback to GCS in both archive and latest locations

        Writes to:
        1. chat-feedback/YYYY-MM-DD/{positive|negative}_xxx.json (permanent archive)
        2. chat-feedback/latest/{positive|negative}_xxx.json (today's data, cleared daily)

        Args:
            feedback: FeedbackRequest object with user feedback data

        Returns:
            dict with:
                - success: bool
                - feedbackId: str (archive path)
                - storedAt: str (ISO timestamp)
                - error: Optional[str]
        """
        try:
            # Get bucket (assumes bucket already exists)
            bucket = self._get_bucket()

            # Generate server timestamp (single source of truth)
            created_at = datetime.utcnow().isoformat() + "Z"

            # Get current date and check if we need to clear latest folder
            current_date = self._get_current_date()
            self._check_and_clear_latest_folder(current_date)

            # Generate paths for both locations (with positive/negative prefix)
            date_folder, archive_path, latest_path = self._generate_feedback_paths(
                created_at,
                feedback.feedback
            )

            # Prepare feedback data as JSON
            feedback_data = {
                "messageId": feedback.messageId,
                "feedback": feedback.feedback,
                "reason": feedback.reason,
                "userQuestion": feedback.userQuestion,
                "aiAnswer": feedback.aiAnswer,
                "createdAt": created_at
            }

            # Convert to NDJSON (single line JSON)
            ndjson_content = json.dumps(feedback_data, ensure_ascii=False)

            # Upload to BOTH locations
            # 1. Archive (permanent, organized by date)
            archive_blob = bucket.blob(archive_path)
            archive_blob.upload_from_string(
                ndjson_content,
                content_type="application/x-ndjson"
            )

            # 2. Latest (today's data only, for easy consumption)
            latest_blob = bucket.blob(latest_path)
            latest_blob.upload_from_string(
                ndjson_content,
                content_type="application/x-ndjson"
            )

            print(f"[GCS] Feedback logged successfully:")
            print(f"  - Archive: {archive_path}")
            print(f"  - Latest: {latest_path}")

            return {
                "success": True,
                "feedbackId": archive_path,  # Return archive path as ID
                "storedAt": feedback_data["createdAt"],
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
