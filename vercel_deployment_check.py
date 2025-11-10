#!/usr/bin/env python3
"""
Vercel Deployment Readiness Checker
Validates your event ticketing app for Vercel deployment
"""

import os
import json
from pathlib import Path

def check_vercel_config():
    """Check Vercel configuration files"""
    
    print("🔍 Checking Vercel Configuration...")
    
    # Check vercel.json
    vercel_config = Path("vercel.json")
    if vercel_config.exists():
        try:
            with open(vercel_config, 'r') as f:
                config = json.load(f)
            
            print("✅ vercel.json exists and is valid JSON")
            
            # Check key configurations
            if config.get("builds") and any(build.get("src") == "app.py" for build in config["builds"]):
                print("✅ Python build configuration found")
            else:
                print("⚠️  Python build configuration missing in vercel.json")
                
            if config.get("routes"):
                print("✅ Route configuration found")
            else:
                print("⚠️  Route configuration missing")
                
        except json.JSONDecodeError:
            print("❌ vercel.json exists but contains invalid JSON")
            
    else:
        print("❌ vercel.json not found")
        return False
    
    # Check environment template
    if Path("vercel.env.template").exists():
        print("✅ Vercel environment template exists")
    else:
        print("⚠️  Environment template missing")
    
    return True

def check_flask_app():
    """Check Flask app compatibility with Vercel"""
    
    print("\n🐍 Checking Flask App Compatibility...")
    
    app_file = Path("app.py")
    if not app_file.exists():
        print("❌ app.py not found")
        return False
    
    print("✅ app.py exists")
    
    # Check for Vercel handler pattern
    try:
        app_content = app_file.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        app_content = app_file.read_text(encoding='latin-1')
    
    # Look for common serverless patterns
    issues = []
    recommendations = []
    
    # Check for file system writes
    if "open(" in app_content and ("w" in app_content or "a" in app_content):
        issues.append("⚠️  File writes detected - may not work in serverless environment")
        recommendations.append("   Use cloud storage for persistent files")
    
    # Check for SQLite (should be migrated)
    if "sqlite" in app_content.lower():
        issues.append("⚠️  SQLite references found")
        recommendations.append("   Ensure all database operations use Supabase")
    
    # Check for app.run() in production
    if "app.run(" in app_content:
        recommendations.append("💡 Remove app.run() calls for production deployment")
    
    if not issues:
        print("✅ Flask app looks serverless-compatible")
    
    for issue in issues:
        print(f"  {issue}")
    
    for rec in recommendations:
        print(f"  {rec}")
    
    return len(issues) == 0

def check_dependencies():
    """Check Python dependencies"""
    
    print("\n📦 Checking Dependencies...")
    
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        requirements = req_file.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        requirements = req_file.read_text(encoding='latin-1')
    
    # Check for cloud storage dependencies
    cloud_storage = False
    if "cloudinary" in requirements:
        print("✅ Cloudinary SDK found")
        cloud_storage = True
    elif "boto3" in requirements:
        print("✅ AWS SDK found")
        cloud_storage = True
    elif "requests" in requirements:
        print("✅ HTTP requests library (for Vercel Blob)")
        cloud_storage = True
    
    if not cloud_storage:
        print("⚠️  No cloud storage SDK detected")
        print("   Consider adding Cloudinary or Vercel Blob support")
    
    # Check for database
    if "psycopg2" in requirements:
        print("✅ PostgreSQL driver found (Supabase compatible)")
    else:
        print("⚠️  PostgreSQL driver not found")
    
    # Check for potentially problematic dependencies
    problematic = ['sqlite3', 'azure-storage-blob']
    for dep in problematic:
        if dep in requirements:
            print(f"⚠️  {dep} found - may not be needed for Vercel")
    
    return True

def check_static_files():
    """Check static file configuration"""
    
    print("\n📁 Checking Static Files...")
    
    static_dir = Path("static")
    if static_dir.exists():
        print("✅ Static directory found")
        
        # Count files
        static_files = list(static_dir.rglob("*"))
        static_count = len([f for f in static_files if f.is_file()])
        static_size = sum(f.stat().st_size for f in static_files if f.is_file()) / 1024 / 1024
        
        print(f"   📊 {static_count} files, {static_size:.1f} MB total")
        
        if static_size > 50:  # Vercel has limits
            print("⚠️  Large static files detected")
            print("   Consider using CDN for large assets")
        
    else:
        print("ℹ️  No static directory found")
    
    return True

def check_uploads_migration():
    """Check if uploads are properly configured for cloud"""
    
    print("\n☁️  Checking Upload Configuration...")
    
    upload_dirs = ["uploads", "static/uploads"]
    local_files = []
    
    for upload_dir in upload_dirs:
        path = Path(upload_dir)
        if path.exists():
            files = list(path.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            if file_count > 0:
                local_files.append(f"{upload_dir}: {file_count} files")
    
    if local_files:
        print("⚠️  Local upload files found:")
        for files in local_files:
            print(f"   📁 {files}")
        print("   💡 Migrate these to cloud storage before production deployment")
    else:
        print("✅ No local upload files found")
    
    # Check for storage service
    if Path("vercel_storage.py").exists():
        print("✅ Vercel storage service created")
    elif Path("azure_storage.py").exists():
        print("⚠️  Azure storage service found - update for Vercel")
    else:
        print("⚠️  No cloud storage service found")
    
    return True

def generate_deployment_steps():
    """Generate next steps for deployment"""
    
    print("\n🚀 Vercel Deployment Steps:")
    print("=" * 50)
    
    steps = [
        "1. 📧 Sign up for Vercel account (free): https://vercel.com",
        "2. 🗄️  Choose storage provider:",
        "   • Cloudinary (recommended for images): https://cloudinary.com", 
        "   • Vercel Blob (simple files): In Vercel dashboard",
        "3. 🔧 Configure environment variables in Vercel dashboard",
        "4. 📁 Push code to GitHub repository",
        "5. 🔗 Connect repository to Vercel",
        "6. 🚀 Deploy automatically on git push",
        "7. 📤 Migrate existing files to cloud storage",
        "8. ✅ Test all functionality in production"
    ]
    
    for step in steps:
        print(step)

def main():
    """Main validation function"""
    
    print("🚀 Event Ticketing App - Vercel Deployment Checker")
    print("=" * 55)
    
    checks = [
        check_vercel_config(),
        check_flask_app(), 
        check_dependencies(),
        check_static_files(),
        check_uploads_migration()
    ]
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n📊 Summary: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 Your app is ready for Vercel deployment!")
    else:
        print("⚠️  Please resolve the issues above")
    
    generate_deployment_steps()

if __name__ == "__main__":
    main()