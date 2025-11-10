# Azure Web App File Storage Migration Guide

## Current Local Storage Dependencies

### 1. Upload Directories
- `/uploads/certificates/` - Certificate assets (logos, signatures)
- `/static/uploads/logos/` - Event logos  
- `/uploads/logos/` - Logo storage

### 2. Database Storage ✅ RESOLVED
- SQLite databases have been migrated to Supabase PostgreSQL

## Azure Cloud Storage Solutions

### Option 1: Azure Blob Storage (Recommended)
**Best for: Production deployments with high availability**

#### Benefits:
- ✅ Persistent, scalable storage
- ✅ CDN integration for fast global access
- ✅ Built-in backup and versioning
- ✅ Cost-effective for large files
- ✅ Direct browser uploads possible

#### Implementation:
```python
# Install: pip install azure-storage-blob
from azure.storage.blob import BlobServiceClient

# Upload file to blob storage
def upload_to_azure_blob(file, container, filename):
    blob_client = blob_service_client.get_blob_client(
        container=container, blob=filename
    )
    blob_client.upload_blob(file, overwrite=True)
    return blob_client.url
```

### Option 2: Azure Files (SMB Share)
**Best for: Simple migration with minimal code changes**

#### Benefits:
- ✅ Mount as network drive
- ✅ Minimal code changes needed
- ✅ Standard file operations work
- ⚠️ Slower than Blob Storage
- ⚠️ More expensive than Blob Storage

### Option 3: Hybrid Approach
**Best for: Gradual migration**

#### Strategy:
1. Keep current file structure for development
2. Add Azure Blob Storage for production
3. Use environment variables to switch storage backend

## Implementation Plan

### Step 1: Add Azure Storage Configuration
```bash
# Environment variables needed
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER_UPLOADS=uploads
AZURE_STORAGE_CONTAINER_LOGOS=logos
USE_AZURE_STORAGE=true  # false for local development
```

### Step 2: Create Storage Service
```python
# services/storage.py
import os
from azure.storage.blob import BlobServiceClient

class StorageService:
    def __init__(self):
        self.use_azure = os.getenv('USE_AZURE_STORAGE', 'false').lower() == 'true'
        if self.use_azure:
            self.blob_service = BlobServiceClient.from_connection_string(
                os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            )
    
    def save_file(self, file, container, filename):
        if self.use_azure:
            return self._save_to_blob(file, container, filename)
        else:
            return self._save_locally(file, container, filename)
```

### Step 3: Update File Upload Handlers
Replace direct file saves with storage service calls:

```python
# Before (local only):
file.save(os.path.join('uploads', 'logos', filename))

# After (cloud-ready):
storage = StorageService()
file_url = storage.save_file(file, 'logos', filename)
```

### Step 4: Update File Serving
```python
# Update URL generation for cloud files
def get_file_url(filename, container):
    if storage.use_azure:
        return f"https://{account}.blob.core.windows.net/{container}/{filename}"
    else:
        return url_for('static', filename=f'uploads/{container}/{filename}')
```

## Migration Steps for Your App

### Immediate (Pre-deployment):
1. ✅ Database migrated to Supabase
2. Add Azure Storage SDK to requirements.txt
3. Create storage service abstraction
4. Update file upload/serving code

### Post-deployment:
1. Create Azure Storage Account
2. Configure connection strings
3. Migrate existing files to blob storage
4. Update DNS/CDN if needed

## Cost Estimation (Azure Blob Storage)
- **Storage**: ~$0.02/GB/month
- **Transactions**: ~$0.004/10,000 operations
- **Bandwidth**: First 5GB free, then ~$0.08/GB

For typical small-medium app: **$5-20/month**

## Files That Need Migration

### Critical (Must migrate):
- Event logos in `/static/uploads/logos/`
- Certificate assets in `/uploads/certificates/`
- Signature images
- Organization logos

### Optional (Can regenerate):
- Temporary certificate PDFs
- CSV upload files (processed then deleted)

## Development vs Production

### Development (Local):
- Keep current file structure
- Use local directories
- SQLite for testing (optional)

### Production (Azure):
- Azure Blob Storage for files
- Supabase for database
- Environment-based configuration switching