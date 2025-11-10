# Vercel Cloud Storage Service for Event Ticketing App

import os
import requests
import base64
from werkzeug.utils import secure_filename
import logging
from typing import Optional, Union
import json

logger = logging.getLogger(__name__)

class VercelStorageService:
    """
    Cloud storage service for Vercel deployment
    Supports multiple providers: Vercel Blob, Cloudinary, AWS S3
    Falls back to local storage for development
    """
    
    def __init__(self):
        self.is_production = os.getenv('VERCEL_ENV') == 'production'
        self.storage_provider = os.getenv('STORAGE_PROVIDER', 'local')  # local, vercel-blob, cloudinary
        
        # Vercel Blob configuration
        self.vercel_token = os.getenv('BLOB_READ_WRITE_TOKEN')
        
        # Cloudinary configuration  
        self.cloudinary_cloud = os.getenv('CLOUDINARY_CLOUD_NAME')
        self.cloudinary_key = os.getenv('CLOUDINARY_API_KEY')
        self.cloudinary_secret = os.getenv('CLOUDINARY_API_SECRET')
        
        # Local development paths
        self.local_upload_folder = 'uploads'
        self.local_static_folder = 'static/uploads'
        
        logger.info(f"Storage provider: {self.storage_provider}")
    
    def save_logo(self, file, filename=None) -> str:
        """Save event logo with image optimization"""
        if not filename:
            filename = secure_filename(file.filename)
        
        if self.storage_provider == 'cloudinary':
            return self._save_to_cloudinary(file, filename, 'logos')
        elif self.storage_provider == 'vercel-blob':
            return self._save_to_vercel_blob(file, f'logos/{filename}')
        else:
            return self._save_locally(file, 'logos', filename)
    
    def save_certificate_asset(self, file, filename=None) -> str:
        """Save certificate assets (signatures, organization logos)"""
        if not filename:
            filename = secure_filename(file.filename)
        
        if self.storage_provider == 'vercel-blob':
            return self._save_to_vercel_blob(file, f'certificates/{filename}')
        elif self.storage_provider == 'cloudinary':
            return self._save_to_cloudinary(file, filename, 'certificates')
        else:
            return self._save_locally(file, 'certificates', filename)
    
    def _save_to_vercel_blob(self, file, blob_path: str) -> str:
        """Save file to Vercel Blob Storage"""
        try:
            if not self.vercel_token:
                raise ValueError("BLOB_READ_WRITE_TOKEN not configured")
            
            # Vercel Blob API endpoint
            url = f"https://blob.vercel-storage.com/{blob_path}"
            
            # Prepare file data
            file.seek(0)
            file_data = file.read()
            
            headers = {
                'Authorization': f'Bearer {self.vercel_token}',
                'Content-Type': file.content_type or 'application/octet-stream'
            }
            
            # Upload to Vercel Blob
            response = requests.put(url, headers=headers, data=file_data)
            response.raise_for_status()
            
            # Get the public URL
            blob_url = f"https://blob.vercel-storage.com/{blob_path}"
            logger.info(f"File uploaded to Vercel Blob: {blob_url}")
            
            return blob_url
            
        except Exception as e:
            logger.error(f"Vercel Blob upload failed for {blob_path}: {e}")
            # Fallback to local storage
            return self._save_locally(file, 'uploads', os.path.basename(blob_path))
    
    def _save_to_cloudinary(self, file, filename: str, folder: str) -> str:
        """Save file to Cloudinary with image optimization"""
        try:
            if not all([self.cloudinary_cloud, self.cloudinary_key, self.cloudinary_secret]):
                raise ValueError("Cloudinary credentials not configured")
            
            # Prepare file for upload
            file.seek(0)
            file_data = file.read()
            file_b64 = base64.b64encode(file_data).decode('utf-8')
            
            # Cloudinary upload API
            upload_url = f"https://api.cloudinary.com/v1_1/{self.cloudinary_cloud}/image/upload"
            
            # Generate upload signature (simplified for demo)
            import time
            timestamp = int(time.time())
            
            data = {
                'file': f'data:{file.content_type};base64,{file_b64}',
                'folder': folder,
                'public_id': filename.rsplit('.', 1)[0],  # Remove extension
                'api_key': self.cloudinary_key,
                'timestamp': timestamp,
                # Add transformations for optimization
                'transformation': 'c_limit,w_1200,h_1200,q_auto,f_auto'
            }
            
            # Simple upload without signature for demo
            # In production, implement proper signature generation
            response = requests.post(upload_url, data=data)
            
            if response.status_code == 200:
                result = response.json()
                cloudinary_url = result.get('secure_url')
                logger.info(f"File uploaded to Cloudinary: {cloudinary_url}")
                return cloudinary_url
            else:
                raise Exception(f"Upload failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Cloudinary upload failed for {filename}: {e}")
            # Fallback to local storage
            return self._save_locally(file, folder, filename)
    
    def _save_locally(self, file, container: str, filename: str) -> str:
        """Save file to local filesystem (development)"""
        # Map containers to local paths
        if container == 'logos':
            local_path = os.path.join(self.local_static_folder, 'logos')
        elif container == 'certificates':
            local_path = os.path.join(self.local_upload_folder, 'certificates')
        else:
            local_path = os.path.join(self.local_upload_folder, container)
        
        # Create directory if it doesn't exist
        os.makedirs(local_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(local_path, filename)
        file.seek(0)  # Reset file pointer
        file.save(file_path)
        
        # Return relative URL for Flask
        if container == 'logos':
            return f'/static/uploads/logos/{filename}'
        else:
            return f'/uploads/{container}/{filename}'
    
    def get_file_url(self, filename: str, container: str = 'uploads') -> str:
        """Get URL for accessing a file"""
        if self.storage_provider in ['vercel-blob', 'cloudinary']:
            # For cloud storage, the filename should already be a full URL
            # if saved through this service
            if filename.startswith('http'):
                return filename
            else:
                # Construct URL for cloud storage
                if self.storage_provider == 'vercel-blob':
                    return f"https://blob.vercel-storage.com/{container}/{filename}"
                # Cloudinary URLs are returned during upload
                return filename
        else:
            # Local development URLs
            if container == 'logos':
                return f'/static/uploads/logos/{filename}'
            else:
                return f'/uploads/{container}/{filename}'
    
    def delete_file(self, file_identifier: str, container: str = 'uploads'):
        """Delete a file from storage"""
        try:
            if self.storage_provider == 'vercel-blob':
                if file_identifier.startswith('https://blob.vercel-storage.com/'):
                    headers = {'Authorization': f'Bearer {self.vercel_token}'}
                    response = requests.delete(file_identifier, headers=headers)
                    response.raise_for_status()
                    logger.info(f"Deleted from Vercel Blob: {file_identifier}")
                    
            elif self.storage_provider == 'cloudinary':
                # Cloudinary deletion requires the public_id
                # This would need to be extracted from the URL or stored separately
                pass
                
            else:
                # Local deletion
                if container == 'logos':
                    file_path = os.path.join(self.local_static_folder, 'logos', file_identifier)
                else:
                    file_path = os.path.join(self.local_upload_folder, container, file_identifier)
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted local file: {file_path}")
                    
        except Exception as e:
            logger.error(f"Error deleting file {file_identifier}: {e}")

# Global storage instance
storage = VercelStorageService()

# Compatibility alias for existing code
AzureStorageService = VercelStorageService