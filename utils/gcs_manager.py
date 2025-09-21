"""
Google Cloud Storage manager for handling media uploads and downloads
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from google.cloud import storage
from google.cloud.exceptions import NotFound
import requests
from PIL import Image
import io

from config.settings import Config
from utils.logger import setup_logger

class GCSManager:
    """Manager for Google Cloud Storage operations"""
    
    def __init__(self):
        self.logger = setup_logger("GCSManager")
        self.bucket_name = Config.GCS_BUCKET_NAME
        
        # Initialize GCS client
        if Config.GCS_CREDENTIALS_PATH:
            self.client = storage.Client.from_service_account_json(Config.GCS_CREDENTIALS_PATH)
        else:
            # Use default credentials (for production environments)
            self.client = storage.Client()
        
        self.bucket = self.client.bucket(self.bucket_name)
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the GCS bucket exists"""
        try:
            self.bucket.reload()
            self.logger.info(f"Connected to GCS bucket: {self.bucket_name}")
        except NotFound:
            self.logger.error(f"GCS bucket '{self.bucket_name}' not found")
            raise ValueError(f"GCS bucket '{self.bucket_name}' does not exist")
    
    def upload_image(self, image_data: bytes, filename: str, content_type: str = "image/png") -> Dict[str, str]:
        """Upload image to GCS and return URLs"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"images/{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
            
            # Create blob and upload
            blob = self.bucket.blob(unique_filename)
            blob.upload_from_string(image_data, content_type=content_type)
            
            # Make blob publicly readable
            blob.make_public()
            
            # Generate URLs
            public_url = blob.public_url
            gcs_path = f"gs://{self.bucket_name}/{unique_filename}"
            
            self.logger.info(f"Successfully uploaded image: {unique_filename}")
            
            return {
                "public_url": public_url,
                "gcs_path": gcs_path,
                "filename": unique_filename,
                "size": len(image_data)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to upload image: {str(e)}")
            raise
    
    def upload_video(self, video_data: bytes, filename: str, content_type: str = "video/mp4") -> Dict[str, str]:
        """Upload video to GCS and return URLs"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"videos/{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
            
            # Create blob and upload
            blob = self.bucket.blob(unique_filename)
            blob.upload_from_string(video_data, content_type=content_type)
            
            # Make blob publicly readable
            blob.make_public()
            
            # Generate URLs
            public_url = blob.public_url
            gcs_path = f"gs://{self.bucket_name}/{unique_filename}"
            
            self.logger.info(f"Successfully uploaded video: {unique_filename}")
            
            return {
                "public_url": public_url,
                "gcs_path": gcs_path,
                "filename": unique_filename,
                "size": len(video_data)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to upload video: {str(e)}")
            raise
    
    def download_file(self, gcs_path: str) -> bytes:
        """Download file from GCS"""
        try:
            # Extract blob name from GCS path
            blob_name = gcs_path.replace(f"gs://{self.bucket_name}/", "")
            blob = self.bucket.blob(blob_name)
            
            return blob.download_as_bytes()
            
        except Exception as e:
            self.logger.error(f"Failed to download file from {gcs_path}: {str(e)}")
            raise
    
    def delete_file(self, gcs_path: str) -> bool:
        """Delete file from GCS"""
        try:
            blob_name = gcs_path.replace(f"gs://{self.bucket_name}/", "")
            blob = self.bucket.blob(blob_name)
            blob.delete()
            
            self.logger.info(f"Successfully deleted file: {gcs_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete file {gcs_path}: {str(e)}")
            return False
    
    def list_files(self, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List files in GCS bucket"""
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix, max_results=limit)
            
            files = []
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "created": blob.time_created.isoformat() if blob.time_created else None,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                    "public_url": blob.public_url,
                    "gcs_path": f"gs://{self.bucket_name}/{blob.name}"
                })
            
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to list files: {str(e)}")
            raise
    
    def generate_signed_url(self, gcs_path: str, expiration_hours: int = 24) -> str:
        """Generate signed URL for private access"""
        try:
            blob_name = gcs_path.replace(f"gs://{self.bucket_name}/", "")
            blob = self.bucket.blob(blob_name)
            
            expiration = datetime.utcnow() + timedelta(hours=expiration_hours)
            
            signed_url = blob.generate_signed_url(
                expiration=expiration,
                method='GET'
            )
            
            return signed_url
            
        except Exception as e:
            self.logger.error(f"Failed to generate signed URL for {gcs_path}: {str(e)}")
            raise
