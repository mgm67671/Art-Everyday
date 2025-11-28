"""
Cloud Storage integration for handling image uploads.
Supports both local file storage (development) and Google Cloud Storage (production).
"""

import os
from typing import Optional
from werkzeug.datastructures import FileStorage
from google.cloud import storage
from datetime import timedelta


class StorageHandler:
    """Handles file uploads to either local storage or Google Cloud Storage."""
    
    def __init__(self, gcs_bucket: Optional[str] = None):
        """
        Initialize storage handler.
        
        Args:
            gcs_bucket: GCS bucket name for production, None for local development
        """
        self.gcs_bucket = gcs_bucket
        self.use_gcs = gcs_bucket is not None
        
        if self.use_gcs:
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(gcs_bucket)
    
    def upload_file(self, file: FileStorage, filename: str, local_path: Optional[str] = None) -> str:
        """
        Upload a file to storage.
        
        Args:
            file: The file object to upload
            filename: The filename to save as
            local_path: Local directory path (used only in dev mode)
            
        Returns:
            The URL or path where the file can be accessed
        """
        if self.use_gcs:
            return self._upload_to_gcs(file, filename)
        else:
            return self._upload_to_local(file, filename, local_path)
    
    def _upload_to_gcs(self, file: FileStorage, filename: str) -> str:
        """Upload file to Google Cloud Storage."""
        blob = self.bucket.blob(f"submissions/{filename}")
        
        # Set content type based on file extension
        content_type = file.content_type or 'application/octet-stream'
        blob.upload_from_file(file, content_type=content_type)
        
        # Don't use blob.make_public() when uniform bucket-level access is enabled
        # The bucket already has public access configured at the bucket level
        
        return blob.public_url
    
    def _upload_to_local(self, file: FileStorage, filename: str, local_path: str) -> str:
        """Upload file to local filesystem."""
        os.makedirs(local_path, exist_ok=True)
        save_path = os.path.join(local_path, filename)
        file.save(save_path)
        return filename
    
    def get_file_url(self, filename: str, local_prefix: str = 'uploaded_images') -> str:
        """
        Get the URL for accessing a file.
        
        Args:
            filename: The filename
            local_prefix: Path prefix for local files
            
        Returns:
            Full URL for GCS, relative path for local
        """
        if self.use_gcs:
            blob = self.bucket.blob(f"submissions/{filename}")
            return blob.public_url
        else:
            return f"{local_prefix}/{filename}"
    
    def generate_signed_url(self, filename: str, expiration: int = 3600) -> str:
        """
        Generate a signed URL for temporary access (GCS only).
        
        Args:
            filename: The filename
            expiration: URL expiration time in seconds
            
        Returns:
            Signed URL or regular URL if not using GCS
        """
        if self.use_gcs:
            blob = self.bucket.blob(f"submissions/{filename}")
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expiration),
                method="GET"
            )
            return url
        else:
            return self.get_file_url(filename)
    
    def delete_file(self, filename: str, local_path: Optional[str] = None) -> bool:
        """
        Delete a file from storage.
        
        Args:
            filename: The filename to delete
            local_path: Local directory path (used only in dev mode)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_gcs:
                blob = self.bucket.blob(f"submissions/{filename}")
                blob.delete()
            else:
                if local_path:
                    file_path = os.path.join(local_path, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")
            return False
    
    def list_files(self, prefix: str = "submissions/") -> list:
        """
        List all files in storage.
        
        Args:
            prefix: Path prefix to filter files (GCS only)
            
        Returns:
            List of filenames
        """
        if self.use_gcs:
            blobs = self.bucket.list_blobs(prefix=prefix)
            return [blob.name.replace(prefix, "") for blob in blobs]
        else:
            # For local, would need to scan directory
            return []


def get_storage_handler() -> StorageHandler:
    """Get a configured storage handler instance."""
    from . import app
    gcs_bucket = app.config.get('GCS_BUCKET')
    return StorageHandler(gcs_bucket)
