"""
Cloudflare R2 Storage Utility
Handles file uploads, downloads, and signed URL generation
"""

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import hashlib
import uuid
from typing import Optional, BinaryIO
from datetime import datetime, timedelta
from app.core.config import settings


class StorageService:
    """Service for handling file storage operations with Cloudflare R2"""

    def __init__(self):
        """Initialize R2 client"""
        try:
            self.r2_client = boto3.client(
                's3',
                endpoint_url=settings.r2_endpoint_url,
                aws_access_key_id=settings.r2_access_key,
                aws_secret_access_key=settings.r2_secret_key,
                region_name=settings.r2_region,
                config=Config(signature_version='s3v4')
            )
            self.bucket_name = settings.r2_bucket_name
        except Exception as e:
            print(f"Warning: R2 client initialization failed: {e}")
            print("Document upload functionality will be limited until credentials are configured.")
            self.r2_client = None
            self.bucket_name = None

    def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder: str = "documents"
    ) -> dict:
        """
        Upload file to R2

        Args:
            file: File object to upload
            filename: Original filename
            content_type: MIME type of the file
            folder: Folder/prefix in bucket (default: "documents")

        Returns:
            dict: {
                'key': str,  # R2 object key
                'url': str,  # Full URL to object
                'checksum': str,  # SHA-256 checksum
                'size': int  # File size in bytes
            }

        Raises:
            Exception: If R2 is not configured or upload fails
        """
        if not self.r2_client or not self.bucket_name:
            raise Exception(
                "R2 storage is not configured. Please add credentials to .env file:\n"
                "R2_BUCKET_NAME, R2_ACCESS_KEY, R2_SECRET_KEY, R2_ENDPOINT_URL"
            )

        try:
            # Generate unique filename to prevent collisions
            file_extension = self._get_file_extension(filename)
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            object_key = f"{folder}/{unique_filename}"

            # Read file content for checksum and upload
            file_content = file.read()
            file.seek(0)  # Reset file pointer

            # Calculate SHA-256 checksum
            checksum = hashlib.sha256(file_content).hexdigest()

            # Upload to R2
            self.r2_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'original-filename': filename,
                    'checksum-sha256': checksum,
                    'uploaded-at': datetime.utcnow().isoformat()
                }
            )

            # Construct full URL
            file_url = f"{settings.r2_endpoint_url}/{self.bucket_name}/{object_key}"

            return {
                'key': object_key,
                'url': file_url,
                'checksum': checksum,
                'size': len(file_content)
            }

        except ClientError as e:
            raise Exception(f"Failed to upload file to R2: {str(e)}")

    def generate_signed_url(
        self,
        object_key: str,
        expiry_seconds: Optional[int] = None
    ) -> str:
        """
        Generate presigned URL for temporary file access

        Args:
            object_key: R2 object key (e.g., "documents/abc123.pdf")
            expiry_seconds: URL validity in seconds (default from config)

        Returns:
            str: Presigned URL

        Raises:
            Exception: If R2 is not configured or generation fails
        """
        if not self.r2_client or not self.bucket_name:
            raise Exception("R2 storage is not configured")

        if expiry_seconds is None:
            expiry_seconds = settings.signed_url_expiry_seconds

        try:
            signed_url = self.r2_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiry_seconds
            )
            return signed_url

        except ClientError as e:
            raise Exception(f"Failed to generate signed URL: {str(e)}")

    def delete_file(self, object_key: str) -> bool:
        """
        Delete file from R2

        Args:
            object_key: R2 object key to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            Exception: If R2 is not configured or deletion fails
        """
        if not self.r2_client or not self.bucket_name:
            raise Exception("R2 storage is not configured")

        try:
            self.r2_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True

        except ClientError as e:
            raise Exception(f"Failed to delete file from R2: {str(e)}")

    def file_exists(self, object_key: str) -> bool:
        """
        Check if file exists in R2

        Args:
            object_key: R2 object key to check

        Returns:
            bool: True if file exists
        """
        if not self.r2_client or not self.bucket_name:
            return False

        try:
            self.r2_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True

        except ClientError:
            return False

    def get_file_metadata(self, object_key: str) -> Optional[dict]:
        """
        Get file metadata from R2

        Args:
            object_key: R2 object key

        Returns:
            dict: File metadata or None if not found
        """
        if not self.r2_client or not self.bucket_name:
            return None

        try:
            response = self.r2_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )

            return {
                'size': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }

        except ClientError:
            return None

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        if '.' in filename:
            return f".{filename.rsplit('.', 1)[-1]}"
        return ""

    def validate_file_type(self, filename: str, allowed_types: list = None) -> bool:
        """
        Validate if file type is allowed

        Args:
            filename: Original filename
            allowed_types: List of allowed extensions (e.g., ['pdf', 'doc', 'docx'])

        Returns:
            bool: True if file type is allowed
        """
        if allowed_types is None:
            # Default allowed document types
            allowed_types = [
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                'jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov'
            ]

        extension = self._get_file_extension(filename).lower().lstrip('.')
        return extension in allowed_types

    def validate_file_size(self, file_size: int, max_size_mb: int = None) -> bool:
        """
        Validate if file size is within limits

        Args:
            file_size: File size in bytes
            max_size_mb: Maximum allowed size in MB (default from config)

        Returns:
            bool: True if file size is acceptable
        """
        if max_size_mb is None:
            max_size_mb = settings.max_document_size_mb

        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes


# Global storage service instance
storage_service = StorageService()
