# Azure Storage Service for Event Ticketing App

import os
from azure.storage.blob import BlobServiceClient
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

class AzureStorageService:
    """
    Azure Blob Storage service for handling file uploads in cloud deployment
    Falls back to local storage for development
    """
    
    def __init__(self):
        self.use_azure = os.getenv('USE_AZURE_STORAGE', 'false').lower() == 'true'
        self.local_upload_folder = 'uploads'
        self.local_static_folder = 'static/uploads'
        
        if self.use_azure:
            try:
                connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                if not connection_string:
                    raise ValueError("AZURE_STORAGE_CONNECTION_STRING not found")
                
                self.blob_service = BlobServiceClient.from_connection_string(connection_string)
                self.account_name = self.blob_service.account_name
                logger.info("Azure Blob Storage initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize Azure Storage: {e}")
                logger.info("Falling back to local storage")
                self.use_azure = False
    
    def save_logo(self, file, filename=None):
        """Save event logo file"""
        if not filename:
            filename = secure_filename(file.filename)
        
        container = 'logos'
        return self._save_file(file, container, filename)
    
    def save_certificate_asset(self, file, filename=None):
        """Save certificate assets (logos, signatures, etc.)"""
        if not filename:
            filename = secure_filename(file.filename)
            
        container = 'certificates'
        return self._save_file(file, container, filename)
    
    def save_uploaded_file(self, file, subfolder='general', filename=None):
        """Save any uploaded file to specified subfolder"""
        if not filename:
            filename = secure_filename(file.filename)
            
        container = f'uploads/{subfolder}' if subfolder else 'uploads'
        return self._save_file(file, container, filename)
    
    def _save_file(self, file, container, filename):
        """Internal method to save file to Azure or local storage"""
        try:
            if self.use_azure:
                return self._save_to_azure(file, container, filename)
            else:
                return self._save_locally(file, container, filename)
                
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            # Fallback to local if Azure fails
            if self.use_azure:
                logger.info("Azure save failed, falling back to local storage")
                return self._save_locally(file, container, filename)
            raise
    
    def _save_to_azure(self, file, container, filename):
        """Save file to Azure Blob Storage"""
        try:
            # Create container if it doesn't exist
            container_client = self.blob_service.get_container_client(container)
            try:
                container_client.get_container_properties()
            except:
                container_client.create_container(public_access='blob')
                logger.info(f"Created container: {container}")
            
            # Upload file
            blob_client = self.blob_service.get_blob_client(
                container=container, 
                blob=filename
            )
            
            # Reset file pointer to beginning
            file.seek(0)
            blob_client.upload_blob(file, overwrite=True)
            
            # Return URL for accessing the file
            blob_url = f"https://{self.account_name}.blob.core.windows.net/{container}/{filename}"
            logger.info(f"File uploaded to Azure: {blob_url}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Azure upload failed for {filename}: {e}")
            raise
    
    def _save_locally(self, file, container, filename):
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
        file.save(file_path)
        
        # Return relative URL for Flask
        if container == 'logos':
            return f'/static/uploads/logos/{filename}'
        else:
            return f'/uploads/{container}/{filename}'
    
    def get_file_url(self, filename, container='uploads'):
        """Get URL for accessing a file"""
        if self.use_azure:
            return f"https://{self.account_name}.blob.core.windows.net/{container}/{filename}"
        else:
            if container == 'logos':
                return f'/static/uploads/logos/{filename}'
            else:
                return f'/uploads/{container}/{filename}'
    
    def delete_file(self, filename, container='uploads'):
        """Delete a file from storage"""
        try:
            if self.use_azure:
                blob_client = self.blob_service.get_blob_client(
                    container=container, 
                    blob=filename
                )
                blob_client.delete_blob()
                logger.info(f"Deleted from Azure: {container}/{filename}")
            else:
                # Local deletion
                if container == 'logos':
                    file_path = os.path.join(self.local_static_folder, 'logos', filename)
                else:
                    file_path = os.path.join(self.local_upload_folder, container, filename)
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted local file: {file_path}")
                    
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
    
    def list_files(self, container='uploads'):
        """List files in a container"""
        try:
            if self.use_azure:
                container_client = self.blob_service.get_container_client(container)
                blobs = container_client.list_blobs()
                return [blob.name for blob in blobs]
            else:
                # Local listing
                if container == 'logos':
                    local_path = os.path.join(self.local_static_folder, 'logos')
                else:
                    local_path = os.path.join(self.local_upload_folder, container)
                
                if os.path.exists(local_path):
                    return os.listdir(local_path)
                return []
                
        except Exception as e:
            logger.error(f"Error listing files in {container}: {e}")
            return []

# Global storage instance
storage = AzureStorageService()