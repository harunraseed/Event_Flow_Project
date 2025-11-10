#!/usr/bin/env python3
"""
Vercel Migration Helper Script
Prepares your Flask app for Vercel serverless deployment
"""

import os
import shutil
from pathlib import Path
import json

def clean_sqlite_references():
    """Remove SQLite database files and references"""
    print("🗄️  Cleaning SQLite References...")
    
    # Remove SQLite database files
    instance_dir = Path("instance")
    if instance_dir.exists():
        sqlite_files = list(instance_dir.glob("*.db")) + list(instance_dir.glob("*.sqlite*"))
        if sqlite_files:
            backup_dir = Path("backup/sqlite_removed")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"📦 Backing up {len(sqlite_files)} SQLite files...")
            for db_file in sqlite_files:
                backup_path = backup_dir / db_file.name
                shutil.move(str(db_file), str(backup_path))
                print(f"   Moved: {db_file.name} → backup/")
            
            # Remove instance directory if empty
            try:
                if not any(instance_dir.iterdir()):
                    instance_dir.rmdir()
                    print("   Removed empty instance/ directory")
            except:
                pass
        else:
            print("✅ No SQLite files found")
    
    print("✅ SQLite cleanup complete")

def backup_local_uploads():
    """Backup local upload files before cloud migration"""
    print("\n📤 Backing Up Local Upload Files...")
    
    upload_paths = ["uploads", "static/uploads"]
    backup_root = Path("backup/local_uploads_backup")
    
    for upload_path in upload_paths:
        source = Path(upload_path)
        if source.exists():
            files = list(source.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            
            if file_count > 0:
                dest = backup_root / upload_path
                dest.mkdir(parents=True, exist_ok=True)
                
                print(f"📁 Backing up {upload_path}/ ({file_count} files)...")
                shutil.copytree(source, dest, dirs_exist_ok=True)
                print(f"   ✅ Backed up to: backup/local_uploads_backup/{upload_path}/")
    
    print("✅ Upload files backed up")

def create_serverless_compatible_app():
    """Create serverless-compatible version of app.py"""
    print("\n🔧 Creating Serverless-Compatible App...")
    
    app_file = Path("app.py")
    if not app_file.exists():
        print("❌ app.py not found")
        return
    
    # Read current app.py
    try:
        content = app_file.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        content = app_file.read_text(encoding='latin-1')
    
    # Create backup
    backup_file = Path("app.py.backup")
    backup_file.write_text(content, encoding='utf-8')
    print("📦 Created backup: app.py.backup")
    
    # Modifications for serverless
    modifications = [
        # Remove app.run() calls
        ("app.run(", "# app.run("),
        ("if __name__ == '__main__':\n    app.run(", "# Serverless deployment - app.run() removed\n# if __name__ == '__main__':\n#     app.run("),
        
        # Update storage imports (if using old azure_storage)
        ("from azure_storage import storage", "from vercel_storage import storage"),
        ("import azure_storage", "import vercel_storage as azure_storage  # Compatibility alias"),
    ]
    
    modified = False
    for old, new in modifications:
        if old in content:
            content = content.replace(old, new)
            modified = True
            print(f"   ✅ Updated: {old[:30]}... → {new[:30]}...")
    
    if modified:
        app_file.write_text(content, encoding='utf-8')
        print("✅ app.py updated for serverless deployment")
    else:
        print("ℹ️  No serverless modifications needed")

def create_vercel_deployment_files():
    """Create additional files needed for Vercel"""
    print("\n📄 Creating Vercel Deployment Files...")
    
    # Create .vercelignore
    vercelignore_content = """# Vercel ignore file
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git/
.mypy_cache/
.pytest_cache/
.hypothesis/

# Local development
.env
.env.local
instance/
backup/

# Local uploads (use cloud storage)
uploads/
static/uploads/
*.sqlite
*.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db"""
    
    Path(".vercelignore").write_text(vercelignore_content)
    print("✅ Created .vercelignore")
    
    # Create runtime.txt for Python version
    runtime_content = "python-3.11"
    Path("runtime.txt").write_text(runtime_content)
    print("✅ Created runtime.txt")

def create_migration_guide():
    """Create step-by-step migration guide"""
    
    guide_content = """# 🚀 Vercel Deployment Guide - Your Event Ticketing App

## ✅ Completed Setup Steps:
- [x] Vercel configuration files created
- [x] Cloud storage service implemented  
- [x] SQLite files cleaned up
- [x] Local uploads backed up
- [x] Serverless compatibility updates

## 🔄 Next Steps for Deployment:

### 1. Setup Cloud Storage (Choose One):

#### Option A: Cloudinary (Recommended for Images) 🖼️
1. Sign up: https://cloudinary.com (Free: 25 credits/month)
2. Get credentials from Dashboard > Settings > Access Keys
3. Add to Vercel environment variables:
   ```
   STORAGE_PROVIDER=cloudinary
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret
   ```

#### Option B: Vercel Blob Storage 💾
1. In Vercel Dashboard: Storage > Create Database > Blob
2. Copy the token
3. Add to environment variables:
   ```
   STORAGE_PROVIDER=vercel-blob
   BLOB_READ_WRITE_TOKEN=your-token
   ```

### 2. Deploy to Vercel:

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Connect to Vercel:**
   - Visit https://vercel.com
   - Import your GitHub repository
   - Vercel will auto-detect Flask app

3. **Configure Environment Variables:**
   In Vercel Dashboard > Settings > Environment Variables, add:
   ```
   DATABASE_URL=your-supabase-url
   SECRET_KEY=your-secret-key
   STORAGE_PROVIDER=cloudinary  # or vercel-blob
   # Add storage credentials from step 1
   ```

4. **Deploy:**
   - Vercel deploys automatically on git push
   - Your app will be available at: https://your-app.vercel.app

### 3. Migrate Existing Files:

#### Upload Files to Cloud Storage:
1. Download backed up files from: `backup/local_uploads_backup/`
2. Upload manually through your app's upload interface
3. Or create a migration script to bulk upload

#### Test Everything:
- [ ] Event creation with logo upload
- [ ] Participant registration  
- [ ] Certificate generation
- [ ] Email sending
- [ ] Database operations (Supabase)

## 📁 File Backup Locations:
- SQLite databases: `backup/sqlite_removed/`
- Upload files: `backup/local_uploads_backup/`
- Original app.py: `app.py.backup`

## 🎯 Production Benefits:
✅ Automatic HTTPS and CDN
✅ Global edge deployment
✅ Zero-config scaling  
✅ Instant rollbacks
✅ Preview deployments
✅ Custom domains (free)

## 💰 Expected Costs:
- Vercel Hobby (Free): Up to 100GB bandwidth/month
- Cloudinary (Free): 25 credits/month (~500 images)  
- Supabase (Free): 500MB database, 2GB bandwidth
- **Total: $0/month for small-medium usage** 🎉

## 🆘 Need Help?
- Vercel docs: https://vercel.com/docs
- Cloudinary docs: https://cloudinary.com/documentation
- Your app is ready - just follow the steps above!
"""
    
    Path("VERCEL_DEPLOYMENT_STEPS.md").write_text(guide_content, encoding='utf-8')
    print("✅ Created deployment guide: VERCEL_DEPLOYMENT_STEPS.md")

def main():
    """Main migration function"""
    print("🚀 Vercel Migration Helper")
    print("=" * 40)
    
    # Ask for confirmation
    print("\nThis script will:")
    print("1. Clean up SQLite database files")
    print("2. Backup local upload files") 
    print("3. Update app.py for serverless compatibility")
    print("4. Create Vercel deployment files")
    print("5. Generate step-by-step deployment guide")
    
    response = input("\n🤔 Continue with migration? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Migration cancelled")
        return
    
    # Run migration steps
    clean_sqlite_references()
    backup_local_uploads()  
    create_serverless_compatible_app()
    create_vercel_deployment_files()
    create_migration_guide()
    
    print("\n🎉 Vercel migration preparation complete!")
    print("\n📖 Next steps: Read VERCEL_DEPLOYMENT_STEPS.md")
    print("🚀 Your app is ready for cloud deployment!")

if __name__ == "__main__":
    main()